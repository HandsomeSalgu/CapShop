# SyncShopper AI Server

FastAPI-based AI server for SyncShopper.

The server exposes:

```text
GET  /health
POST /api/ai/analyze-frame
POST /api/ai/generate-commerce-query
```

## Run

Windows:

```bash
cd ai-server
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Mac/Linux:

```bash
cd ai-server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Environment

Create `.env` from `.env.example`.

```env
AI_DETECTION_PROVIDER=mock
GMS_OPENAI_API_KEY=YOUR_API_KEY
GMS_OPENAI_CHAT_COMPLETIONS_URL=https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions
GMS_OPENAI_MODEL=gpt-5.4-mini
GMS_OPENAI_QUERY_MODEL=gpt-5.4-mini
GMS_OPENAI_TIMEOUT_SEC=30
```

Use `AI_DETECTION_PROVIDER=mock` for mock image detection and `AI_DETECTION_PROVIDER=gpt` for GPT Vision detection. Commerce query generation always uses GPT and reads `GMS_OPENAI_QUERY_MODEL`; if that value is omitted, it falls back to `GMS_OPENAI_MODEL`.

Do not commit `.env`; it is ignored by Git.

## Health Check

```http
GET http://localhost:8000/health
```

Response:

```json
{
  "status": "ok",
  "service": "syncshopper-ai-server"
}
```

## Analyze Frame

```http
POST http://localhost:8000/api/ai/analyze-frame
```

Request example:

```json
{
  "video_id": "nike-video-001",
  "timestamp_sec": 135,
  "image_base64": "data:image/png;base64,iVBORw0KGgoAAA...",
  "subtitle_text": "Nike shoes"
}
```

Mock response example:

```json
{
  "target_name": "Nike sneakers",
  "category_name": "패션",
  "brand": "Nike",
  "model_name": "Air Force 1",
  "confidence": 0.91
}
```

Invalid `image_base64` values return HTTP 400:

```json
{
  "detail": "image_base64 must be a valid data:image base64 string"
}
```

## Generate Commerce Query

```http
POST http://localhost:8000/api/ai/generate-commerce-query
```

Request example:

```json
{
  "target_name": "Nike sneakers",
  "category_name": "패션",
  "brand": "Nike",
  "model_name": "Air Force 1",
  "confidence": 0.91,
  "subtitle_text": "Nike Air Force 1 shoes",
  "video_id": "nike-video-001",
  "timestamp_sec": 135
}
```

Response example:

```json
{
  "primary_query": "나이키 에어포스 1",
  "fallback_queries": [
    "Nike Air Force 1",
    "나이키 스니커즈",
    "나이키 운동화"
  ],
  "normalized_brand": "Nike",
  "normalized_model": "Air Force 1",
  "normalized_category": "운동화",
  "query_confidence": 0.92,
  "reason": "Detection result includes a clear brand and model, so the primary query uses both for shopping search."
}
```

If `GMS_OPENAI_API_KEY` is missing, the commerce query API returns HTTP 500:

```json
{
  "detail": "GMS_OPENAI_API_KEY is not configured"
}
```

GPT timeout returns HTTP 504. GPT request failures, API errors, unexpected response shapes, and JSON parse failures return HTTP 502.

## Swagger

After starting the server, open:

```text
http://localhost:8000/docs
```

Expected APIs:

```text
GET /health
POST /api/ai/analyze-frame
POST /api/ai/generate-commerce-query
```

## Spring Boot Integration

Expected flow:

```text
Chrome Extension
-> Spring Boot /api/detections/analyze
-> FastAPI /api/ai/analyze-frame
-> Spring Boot saves detection result
-> FastAPI /api/ai/generate-commerce-query
-> Spring Boot Commerce API searches with primary_query
-> fallback_queries are used if primary_query results are weak
```
