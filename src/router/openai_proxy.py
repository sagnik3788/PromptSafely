from typing import Optional

import uuid
import logging

from fastapi import APIRouter, Request, Header, HTTPException
from fastapi.responses import JSONResponse
import httpx

from src.schema.openai import ChatRequest

logger = logging.getLogger("openai_proxy")

router = APIRouter()

UPSTREAM_URL = "https://api.openai.com/v1/chat/completions"


@router.post("/chat/completions")
async def proxy_chat_completions(
    request: Request,
    x_request_id: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
):
    body = await request.body()

    req_id = x_request_id or str(uuid.uuid4())

    try:
        ChatRequest.model_validate_json(body)
    except Exception as e:
        logger.debug("Invalid chat request: %s", e)
        raise HTTPException(status_code=400, detail="invalid request payload")

    headers = {
        "Content-Type": "application/json",
        "X-Request-Id": req_id,
    }

    if authorization:
        headers["Authorization"] = authorization

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(UPSTREAM_URL, content=body, headers=headers)
        except httpx.RequestError as e:
            logger.exception("Upstream request failed: %s", e)
            raise HTTPException(status_code=502, detail="upstream unavailable")

    try:
        return JSONResponse(status_code=resp.status_code, content=resp.json())
    except Exception:
        return JSONResponse(
            status_code=resp.status_code,
            content={"detail": "Upstream service returned an invalid response."},
        )
