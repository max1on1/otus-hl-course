from __future__ import annotations

import os
from uuid import UUID

import httpx


BASE_URL = os.getenv("COUNTER_SERVICE_URL", "http://counter-service:8002")


async def unread_total(token: str, x_request_id: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    if x_request_id:
        headers["x-request-id"] = x_request_id
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=5.0) as client:
        resp = await client.get("/api/v1/counters/unread/total", headers=headers)
        resp.raise_for_status()
        return resp.json()


async def unread_with_peer(token: str, peer_id: UUID, x_request_id: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    if x_request_id:
        headers["x-request-id"] = x_request_id
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=5.0) as client:
        resp = await client.get(f"/api/v1/counters/unread/{peer_id}", headers=headers)
        resp.raise_for_status()
        return resp.json()


async def reset_unread(token: str, peer_id: UUID, x_request_id: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    if x_request_id:
        headers["x-request-id"] = x_request_id
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=5.0) as client:
        resp = await client.post(f"/api/v1/counters/unread/{peer_id}/reset", headers=headers)
        resp.raise_for_status()
        return resp.json()

