"""Tray.io API client: static Bearer token against https://api.tray.io/core/v1,
429/5xx bounded retry with jitter (tasks #2356/#2359 pattern, same as Pipedream)."""
from __future__ import annotations

import asyncio
import random
from typing import Any

import httpx

BASE = "https://api.tray.io/core/v1"

# App-declared structured error codes (V32)
TR_AUTH_FAILED = "TR_AUTH_FAILED"
TR_FORBIDDEN = "TR_FORBIDDEN"
TR_NOT_FOUND = "TR_NOT_FOUND"
TR_RATE_LIMITED = "TR_RATE_LIMITED"
TR_UPSTREAM = "TR_UPSTREAM"
TR_VALIDATION = "TR_VALIDATION"
TR_NO_CONNECTION = "TR_NO_CONNECTION"
TR_UNEXPECTED = "TR_UNEXPECTED"

_MAX_ATTEMPTS = 4
_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class TrayError(Exception):
    """Typed upstream failure; handlers convert it to ActionResult.error."""

    def __init__(self, code: str, message: str, status: int = 0) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status

    @property
    def payload(self) -> dict:
        return {"code": self.code, "message": self.message}


ClientFail = TrayError  # alias matching other connectors' handlers


def _err(code: str, message: str, status: int = 0) -> TrayError:
    return TrayError(code, message, status)


def _code_for(status: int) -> str:
    if status == 401:
        return TR_AUTH_FAILED
    if status == 403:
        return TR_FORBIDDEN
    if status == 404:
        return TR_NOT_FOUND
    if status == 429:
        return TR_RATE_LIMITED
    if status >= 500:
        return TR_UPSTREAM
    return TR_VALIDATION


def _message_from(body: Any, status: int) -> str:
    if isinstance(body, dict):
        for key in ("message", "error", "detail", "error_description"):
            val = body.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    return f"Tray API returned HTTP {status}"


async def request(
    conn: dict,
    method: str,
    path: str,
    *,
    params: dict | None = None,
    json_body: dict | None = None,
) -> Any:
    """Authenticated JSON request against /core/v1 with bounded 429/5xx retry."""
    token = conn.get("token") or ""
    if not token:
        raise _err(TR_NO_CONNECTION, "saved connection has no token")
    url = f"{BASE}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    attempt = 0
    last_status = 0
    async with httpx.AsyncClient(timeout=_TIMEOUT) as http:
        while True:
            attempt += 1
            try:
                resp = await http.request(
                    method, url, headers=headers,
                    params={k: v for k, v in (params or {}).items() if v not in (None, "")},
                    json=json_body,
                )
            except httpx.HTTPError as exc:
                if attempt >= _MAX_ATTEMPTS:
                    raise _err(TR_UPSTREAM, f"network error reaching Tray: {exc}") from exc
                await asyncio.sleep(min(2 ** attempt, 8) + random.random())
                continue
            last_status = resp.status_code
            if resp.status_code in (429,) or resp.status_code >= 500:
                if attempt < _MAX_ATTEMPTS:
                    retry_after = resp.headers.get("retry-after")
                    try:
                        delay = float(retry_after) if retry_after else min(2 ** attempt, 8)
                    except ValueError:
                        delay = min(2 ** attempt, 8)
                    await asyncio.sleep(delay + random.random())
                    continue
                raise _err(_code_for(resp.status_code), _message_from(resp.json() if resp.content else {}, resp.status_code), resp.status_code)
            break
    if last_status >= 400:
        try:
            body = resp.json() if resp.content else {}
        except ValueError:
            body = {}
        raise _err(_code_for(last_status), _message_from(body, last_status), last_status)
    if not resp.content:
        return {}
    try:
        return resp.json()
    except ValueError as exc:
        raise _err(TR_UNEXPECTED, "non-JSON response from Tray API", last_status) from exc
