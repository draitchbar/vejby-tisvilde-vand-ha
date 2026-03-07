"""HTTP client abstraction for Vejby Tisvilde Vand integration."""
from typing import Any, Protocol

import aiohttp
import async_timeout

from .const import API_TIMEOUT


class HttpError(Exception):
    """Raised when an HTTP request returns a non-2xx status."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class HttpClient(Protocol):
    """Protocol for HTTP clients."""

    async def get(self, url: str, headers: dict, params: dict) -> Any: ...
    async def post(self, url: str, json: dict, headers: dict) -> Any: ...


class AioHttpClient:
    """HTTP client backed by aiohttp.ClientSession."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def get(self, url: str, headers: dict | None = None, params: dict | None = None) -> Any:
        async with async_timeout.timeout(API_TIMEOUT):
            response = await self._session.get(url, headers=headers or {}, params=params or {})
            if not response.ok:
                raise HttpError(response.status, f"GET {url} returned {response.status}")
            return await response.json()

    async def post(self, url: str, json: dict | None = None, headers: dict | None = None) -> Any:
        async with async_timeout.timeout(API_TIMEOUT):
            response = await self._session.post(url, json=json or {}, headers=headers or {})
            if not response.ok:
                raise HttpError(response.status, f"POST {url} returned {response.status}")
            return await response.json()
