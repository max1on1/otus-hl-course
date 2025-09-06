from __future__ import annotations

import os
from typing import List
from uuid import UUID

import httpx


BASE_URL = os.getenv("DIALOG_SERVICE_URL", "http://dialog-service:8001")


async def send_message(
    current_user_token: str,
    recipient_id: UUID,
    text: str,
    x_request_id: str | None = None,
) -> None:
    headers = {"Authorization": f"Bearer {current_user_token}"}
    if x_request_id:
        headers["x-request-id"] = x_request_id
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        resp = await client.post(f"/api/v1/dialog/{recipient_id}/send", json={"text": text}, headers=headers)
        resp.raise_for_status()


async def list_dialog(
    current_user_token: str,
    user_id: UUID,
    x_request_id: str | None = None,
) -> List[dict]:
    headers = {"Authorization": f"Bearer {current_user_token}"}
    if x_request_id:
        headers["x-request-id"] = x_request_id
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        resp = await client.get(f"/api/v1/dialog/{user_id}/list", headers=headers)
        resp.raise_for_status()
        return resp.json()

