import json
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings


def call_chat_completion(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    temperature: float = 0.1,
) -> str:
    if not settings.gms_openai_api_key:
        raise HTTPException(
            status_code=500,
            detail="GMS_OPENAI_API_KEY is not configured",
        )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.gms_openai_api_key}",
    }
    payload = {
        "model": model or settings.gms_openai_model,
        "messages": messages,
        "temperature": temperature,
    }

    try:
        with httpx.Client(timeout=settings.gms_openai_timeout_sec) as client:
            response = client.post(
                settings.gms_openai_chat_completions_url,
                headers=headers,
                json=payload,
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="GMS OpenAI request timed out",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"GMS OpenAI request failed: {str(exc)}",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=(
                f"GMS OpenAI API error: {response.status_code} "
                f"url={settings.gms_openai_chat_completions_url} "
                f"model={payload['model']} {_truncate(response.text)}"
            ),
        )

    try:
        response_json = response.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"GMS OpenAI API returned non-JSON response: {_truncate(response.text)}",
        ) from exc

    try:
        content = response_json["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected GMS OpenAI response format: {_truncate(json.dumps(response_json, ensure_ascii=False))}",
        ) from exc

    return str(content)


def extract_json_object(content: str) -> dict[str, Any]:
    cleaned = content.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(cleaned)
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


def _truncate(value: str, max_length: int = 500) -> str:
    if len(value) <= max_length:
        return value

    return f"{value[:max_length]}..."
