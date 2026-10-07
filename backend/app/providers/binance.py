"""Crypto từ sàn Binance (API công khai, không cần key).

Chỉ lấy các cặp giao dịch spot với USDT đang hoạt động.
"""
from __future__ import annotations

from typing import Any

import httpx

from .. import config
from ..models import AssetInfo, AssetSummary, Candle, InfoField
from .base import NotFound, Provider, ProviderError

QUOTE = "USDT"
# Stablecoin neo giá USD/EUR: giá gần như đứng yên nên không đưa vào danh sách.
STABLECOINS = {"USDC", "FDUSD", "TUSD", "USDP", "DAI", "BUSD", "USDE", "PYUSD", "USD1", "EUR", "EURI", "AEUR", "XUSD", "BFUSD", "RLUSD", "USDS"}
TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]


class BinanceProvider(Provider):
    category = "crypto"
    label = "Crypto"
    timeframes = TIMEFRAMES

    def __init__(self, client: httpx.AsyncClient | None = None, base_urls: list[str] | None = None):
        super().__init__(client)
        self.base_urls = base_urls or config.BINANCE_BASE_URLS

    async def _get(self, path: str, params: dict[str, Any] | None = None, ttl: float = 15) -> Any:
        """Gọi lần lượt các domain Binance cho tới khi có một domain trả lời."""
        errors = []
        for base in self.base_urls:
            try:
                return await self.get_json(f"{base}/api/v3/{path}", params, ttl)
            except ProviderError as exc:
                # Mã không tồn tại thì domain nào cũng trả lỗi như nhau, không cần thử tiếp.
                if "Invalid symbol" in str(exc):
                    raise NotFound(f"Không tìm thấy mã {params and params.get('symbol')}") from exc
                errors.append(str(exc))
        raise ProviderError("Không lấy được dữ liệu Binance. " + " | ".join(errors))

    async def _symbols(self) -> dict[str, dict]:
        data = await self._get("exchangeInfo", {"permissions": "SPOT"}, ttl=6 * 3600)
        return {
            s["symbol"]: s
            for s in data.get("symbols", [])
            if s.get("status") == "TRADING"
            and s.get("quoteAsset") == QUOTE
            and s.get("baseAsset") not in STABLECOINS
        }

    async def list_assets(self) -> list[AssetSummary]:
        symbols = await self._symbols()
        tickers = await self._get("ticker/24hr", ttl=15)
        by_symbol = {t["symbol"]: t for t in tickers}
        out = []
        for sym, meta in symbols.items():
            t = by_symbol.get(sym, {})
            out.append(
                AssetSummary(
                    category=self.category,
                    symbol=sym,
                    display=f"{meta['baseAsset']}/{QUOTE}",
                    name=meta["baseAsset"],
                    exchange="Binance",
                    price=_f(t.get("lastPrice")),
                    change_pct=_f(t.get("priceChangePercent")),
                    volume=_f(t.get("quoteVolume")),
                )
            )
        # Mặc định sắp theo giá trị giao dịch 24h giảm dần.
        out.sort(key=lambda a: a.volume or 0, reverse=True)
        return out

    async def candles(self, symbol: str, timeframe: str, limit: int = 500) -> list[Candle]:
        if timeframe not in TIMEFRAMES:
            raise ProviderError(f"Khung thời gian không hỗ trợ: {timeframe}")
        rows = await self._get(
            "klines",
            {"symbol": symbol.upper(), "interval": timeframe, "limit": min(limit, 1000)},
            ttl=10,
        )
        return [
            Candle(int(r[0]) // 1000, float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5]))
            for r in rows
        ]

    async def info(self, symbol: str) -> AssetInfo:
        symbol = symbol.upper()
        meta = (await self._symbols()).get(symbol)
        if not meta:
            raise NotFound(f"Không tìm thấy mã {symbol} trên Binance")
        t = await self._get("ticker/24hr", {"symbol": symbol}, ttl=10)
        base = meta["baseAsset"]
        return AssetInfo(
            category=self.category,
            symbol=symbol,
            display=f"{base}/{QUOTE}",
            name=base,
            exchange="Binance",
            currency=QUOTE,
            price=_f(t.get("lastPrice")),
            change=_f(t.get("priceChange")),
            change_pct=_f(t.get("priceChangePercent")),
            fields=[
                InfoField("Mở cửa 24h", _f(t.get("openPrice")), "price"),
                InfoField("Cao nhất 24h", _f(t.get("highPrice")), "price"),
                InfoField("Thấp nhất 24h", _f(t.get("lowPrice")), "price"),
                InfoField("Giá TB 24h", _f(t.get("weightedAvgPrice")), "price"),
                InfoField(f"Khối lượng 24h ({base})", _f(t.get("volume")), "volume"),
                InfoField(f"Giá trị 24h ({QUOTE})", _f(t.get("quoteVolume")), "volume"),
                InfoField("Số lệnh khớp 24h", t.get("count"), "number"),
                InfoField("Sàn", "Binance Spot", "text"),
            ],
        )


def _f(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
