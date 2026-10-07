"""Giao diện chung cho mọi nguồn dữ liệu và các tiện ích HTTP."""
from __future__ import annotations

import asyncio
import time
import unicodedata
from abc import ABC, abstractmethod
from typing import Any

import httpx

from .. import config
from ..models import AssetInfo, AssetSummary, Candle

USER_AGENT = "Mozilla/5.0 (compatible; quant-invest/0.1)"


class ProviderError(Exception):
    """Lỗi khi lấy dữ liệu từ nguồn bên ngoài."""


class NotFound(ProviderError):
    """Không tìm thấy mã tài sản."""


class TTLCache:
    """Cache trong bộ nhớ, tránh gọi API miễn phí quá nhiều."""

    def __init__(self) -> None:
        self._data: dict[Any, tuple[float, Any]] = {}

    def get(self, key: Any) -> Any | None:
        hit = self._data.get(key)
        if hit and hit[0] > time.monotonic():
            return hit[1]
        return None

    def set(self, key: Any, value: Any, ttl: float) -> None:
        self._data[key] = (time.monotonic() + ttl, value)


def make_client(transport: httpx.AsyncBaseTransport | None = None) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=config.HTTP_TIMEOUT,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        follow_redirects=True,
        transport=transport,
    )


class Provider(ABC):
    category: str = ""
    label: str = ""
    timeframes: list[str] = []

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client or make_client()
        self.cache = TTLCache()
        self._locks: dict[Any, asyncio.Lock] = {}

    async def get_json(self, url: str, params: dict[str, Any] | None = None, ttl: float = 30) -> Any:
        key = (url, tuple(sorted((params or {}).items())))
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        # Gộp các request trùng nhau đang chạy song song thành một.
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            cached = self.cache.get(key)
            if cached is not None:
                return cached
            try:
                resp = await self.client.get(url, params=params)
            except httpx.HTTPError as exc:
                raise ProviderError(f"Không kết nối được {httpx.URL(url).host}: {exc}") from exc
            if resp.status_code >= 400:
                raise ProviderError(
                    f"{httpx.URL(url).host} trả về lỗi {resp.status_code}: {resp.text[:200]}"
                )
            try:
                data = resp.json()
            except ValueError as exc:
                raise ProviderError(f"{httpx.URL(url).host} trả về dữ liệu không hợp lệ") from exc
            self.cache.set(key, data, ttl)
            return data

    @abstractmethod
    async def list_assets(self) -> list[AssetSummary]:
        """Toàn bộ tài sản của danh mục, kèm giá mới nhất nếu có."""

    @abstractmethod
    async def candles(self, symbol: str, timeframe: str, limit: int = 500) -> list[Candle]: ...

    @abstractmethod
    async def info(self, symbol: str) -> AssetInfo: ...

    async def search(self, query: str, limit: int = 20) -> list[AssetSummary]:
        return rank_search(await self.list_assets(), query, limit)


def fold(text: str) -> str:
    """Bỏ dấu tiếng Việt và viết thường để tìm kiếm: 'Hòa Phát' -> 'hoa phat'."""
    text = text.replace("đ", "d").replace("Đ", "D")
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def rank_search(items: list[AssetSummary], query: str, limit: int) -> list[AssetSummary]:
    q = fold(query.strip()).replace("/", "").replace("-", "").replace(" ", "")
    qwords = fold(query.strip())
    if not q:
        return []
    scored: list[tuple[int, float, AssetSummary]] = []
    for a in items:
        sym = fold(a.symbol)
        disp = fold(a.display).replace("/", "")
        base = fold(a.display.split("/")[0])
        name = fold(a.name)
        if q in (sym, base, disp):
            score = 0
        elif sym.startswith(q) or base.startswith(q):
            score = 1
        elif qwords in name:
            score = 2 if name.startswith(qwords) else 3
        else:
            continue
        # Cùng điểm thì ưu tiên mã giao dịch nhiều hơn.
        scored.append((score, -(a.volume or 0) * (a.price or 0), a))
    scored.sort(key=lambda x: (x[0], x[1]))
    return [a for _, _, a in scored[:limit]]


def clean_candles(candles: list[Candle]) -> list[Candle]:
    """Bỏ nến thiếu giá, sắp xếp và loại thời gian trùng."""
    out: list[Candle] = []
    for c in sorted(candles, key=lambda x: x.time):
        if None in (c.open, c.high, c.low, c.close):
            continue
        if out and c.time == out[-1].time:
            out[-1] = c
            continue
        out.append(c)
    return out
