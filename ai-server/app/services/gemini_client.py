import base64
import json
import mimetypes
import re
from typing import Any
from urllib.parse import quote, urlparse

import httpx
from fastapi import HTTPException

from app.core.config import settings


DATA_IMAGE_PATTERN = re.compile(r"^data:(image/[a-zA-Z0-9.+-]+);base64,(.+)$", re.DOTALL)
MAX_REMOTE_IMAGE_BYTES = 5 * 1024 * 1024


def call_chat_completion(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    temperature: float = 0.1,
    timeout_sec: float | None = None,
) -> str:
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not configured",
        )

    resolved_model = model or settings.gemini_model
    payload = _build_generate_content_payload(messages, temperature=temperature)
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": settings.gemini_api_key,
    }

    try:
        with httpx.Client(timeout=timeout_sec or settings.gemini_timeout_sec) as client:
            response = client.post(
                _generate_content_url(resolved_model),
                headers=headers,
                json=payload,
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="Gemini API request timed out",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini API request failed: {str(exc)}",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Gemini API error: {response.status_code} "
                f"url={_generate_content_url(resolved_model)} "
                f"model={resolved_model} {_response_error_detail(response)}"
            ),
        )

    try:
        response_json = response.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini API returned non-JSON response: {_truncate(response.text)}",
        ) from exc

    return _extract_response_text(response_json)


def extract_json_object(content: str) -> dict[str, Any]:
    cleaned = content.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to parse AI response as JSON: {_truncate(content)}",
            )

        try:
            parsed = json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to parse AI response as JSON: {_truncate(content)}",
            ) from exc

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=502,
            detail="AI response JSON must be an object",
        )

    return parsed


def _build_generate_content_payload(
    messages: list[dict[str, Any]],
    *,
    temperature: float,
) -> dict[str, Any]:
    system_parts: list[dict[str, Any]] = []
    contents: list[dict[str, Any]] = []

    for message in messages:
        role = str(message.get("role") or "user").lower()
        parts = _content_to_parts(message.get("content"))
        if not parts:
            continue

        if role in {"system", "developer"}:
            system_parts.extend(parts)
            continue

        contents.append({
            "role": "model" if role == "assistant" else "user",
            "parts": parts,
        })

    if not contents:
        contents.append({
            "role": "user",
            "parts": [{"text": "Return only valid JSON."}],
        })

    payload: dict[str, Any] = {
        "contents": contents,
        "generation_config": {
            "temperature": temperature,
        },
    }
    if system_parts:
        payload["system_instruction"] = {"parts": system_parts}

    return payload


def _content_to_parts(content: Any) -> list[dict[str, Any]]:
    if isinstance(content, str):
        return [{"text": content}]

    if not isinstance(content, list):
        return [{"text": str(content)}] if content is not None else []

    parts: list[dict[str, Any]] = []
    for item in content:
        if not isinstance(item, dict):
            if item is not None:
                parts.append({"text": str(item)})
            continue

        content_type = item.get("type")
        if content_type == "text":
            text = item.get("text")
            if text is not None:
                parts.append({"text": str(text)})
        elif content_type == "image_url":
            image_url = item.get("image_url") or {}
            url = image_url.get("url") if isinstance(image_url, dict) else None
            if url:
                parts.append(_image_url_to_part(str(url)))

    return parts


def _image_url_to_part(url: str) -> dict[str, Any]:
    normalized = url.strip()
    data_match = DATA_IMAGE_PATTERN.match(normalized)
    if data_match:
        return {
            "inline_data": {
                "mime_type": data_match.group(1),
                "data": re.sub(r"\s+", "", data_match.group(2)),
            },
        }

    parsed = urlparse(normalized)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        raise HTTPException(
            status_code=400,
            detail="invalid_image_url: Gemini image input must be data:image base64 or https URL",
        )

    return _remote_image_to_inline_part(normalized)


def _remote_image_to_inline_part(url: str) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=settings.http_timeout_sec, follow_redirects=True) as client:
            response = client.get(url)
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail=f"invalid_image_url: Gemini candidate image download timed out: {_truncate(url, 160)}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"invalid_image_url: Gemini candidate image download failed: {str(exc)}",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"invalid_image_url: Gemini candidate image returned {response.status_code}: {_truncate(url, 160)}",
        )

    if len(response.content) > MAX_REMOTE_IMAGE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"invalid_image_url: Gemini candidate image exceeds {MAX_REMOTE_IMAGE_BYTES} bytes",
        )

    mime_type = _image_mime_type(response, url)
    return {
        "inline_data": {
            "mime_type": mime_type,
            "data": base64.b64encode(response.content).decode("ascii"),
        },
    }


def _image_mime_type(response: httpx.Response, url: str) -> str:
    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type.startswith("image/"):
        return content_type

    guessed_type, _ = mimetypes.guess_type(url)
    if guessed_type and guessed_type.startswith("image/"):
        return guessed_type

    raise HTTPException(
        status_code=415,
        detail=f"invalid_image_url: Gemini candidate URL did not return an image: {_truncate(url, 160)}",
    )


def _extract_response_text(response_json: dict[str, Any]) -> str:
    candidates = response_json.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected Gemini response format: {_truncate(json.dumps(response_json, ensure_ascii=False))}",
        )

    first_candidate = candidates[0]
    if not isinstance(first_candidate, dict):
        raise HTTPException(status_code=502, detail="Unexpected Gemini response candidate format")

    content = first_candidate.get("content")
    parts = content.get("parts") if isinstance(content, dict) else None
    if isinstance(parts, list):
        texts = [
            part.get("text")
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ]
        if texts:
            return "\n".join(texts).strip()

    finish_reason = str(first_candidate.get("finishReason") or "").strip()
    raise HTTPException(
        status_code=502,
        detail=(
            "Unexpected Gemini response format"
            + (f" finish_reason={finish_reason}" if finish_reason else "")
            + f": {_truncate(json.dumps(response_json, ensure_ascii=False))}"
        ),
    )


def _generate_content_url(model: str) -> str:
    normalized_model = model.strip().removeprefix("models/")
    template = settings.gemini_generate_content_url_template
    if "{model}" not in template:
        return template

    return template.format(model=quote(normalized_model, safe=""))


def _response_error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return _truncate(response.text)

    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = str(error.get("message") or "").strip()
            status = str(error.get("status") or "").strip()
            parts = [part for part in [status, message] if part]
            if parts:
                return _truncate(" | ".join(parts))

    return _truncate(response.text)


def _truncate(value: str, max_length: int = 500) -> str:
    if len(value) <= max_length:
        return value

    return f"{value[:max_length]}..."
