"""Cổ phiếu Việt Nam (HOSE, HNX, UPCoM) từ API công khai của VNDirect.

- Danh sách mã:   finfo-api /v4/stocks
- Giá trong ngày: finfo-api /v4/stock_prices
- Nến:            dchart-api /dchart/history (định dạng TradingView UDF)

Giá từ VNDirect tính theo nghìn đồng (VD 128.4 = 128.400 đ); provider đổi sang đồng.
"""
from __future__ import annotations

import statistics
import time
from datetime import date, timedelta
from typing import Any

import httpx

from .. import config
from ..models import AssetInfo, AssetSummary, Candle, InfoField
from .base import NotFound, Provider, ProviderError, clean_candles

FLOORS = ("HOSE", "HNX", "UPCOM")
TIMEFRAMES = ["1m", "5m", "15m", "1h", "1d", "1w"]

# khung -> (resolution của dchart, số ngày lùi lại)
TF_MAP = {
    "1m": ("1", 5),
    "5m": ("5", 20),
    "15m": ("15", 45),
    "1h": ("60", 120),
    "1d": ("D", 5 * 365),
    "1w": ("W", 15 * 365),
}


def to_vnd(value: Any, scale: int = 1000) -> float | None:
    try:
        return round(float(value) * scale, 2)
    except (TypeError, ValueError):
        return None


def detect_scale(closes: list[float]) -> int:
    """Giá cổ phiếu VN tính bằng đồng luôn lớn hơn nhiều so với 1.000,
    nên nếu giá giữa < 1.000 thì dữ liệu đang tính theo nghìn đồng."""
    valid = [c for c in closes if c]
    if not valid:
        return 1000
    return 1000 if statistics.median(valid) < 1000 else 1


class VNDirectProvider(Provider):
    category = "vn"
    label = "CK Việt Nam"
    timeframes = TIMEFRAMES

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        finfo_url: str | None = None,
        chart_url: str | None = None,
    ):
        super().__init__(client)
        self.finfo = finfo_url or config.VNDIRECT_FINFO_URL
        self.chart_url = chart_url or config.VNDIRECT_CHART_URL

    # ---------- danh sách mã ----------
    async def _stocks(self) -> dict[str, dict]:
        data = await self.get_json(
            f"{self.finfo}/stocks",
            {
                "q": "type:STOCK~status:LISTED",
                "fields": "code,companyName,companyNameEng,shortName,floor,listedDate",
                "size": 5000,
            },
            ttl=12 * 3600,
        )
        return {
            s["code"]: s
            for s in data.get("data", [])
            if s.get("code") and str(s.get("floor", "")).upper() in FLOORS
        }

    async def _latest_date(self) -> str:
        """Ngày giao dịch gần nhất, dò bằng một mã thanh khoản cao."""
        since = (date.today() - timedelta(days=14)).isoformat()
        data = await self.get_json(
            f"{self.finfo}/stock_prices",
            {"q": f"code:VNM~date:gte:{since}", "size": 20},
            ttl=60,
        )
        dates = [r["date"] for r in data.get("data", []) if r.get("date")]
        if not dates:
            raise ProviderError("VNDirect không trả về ngày giao dịch gần nhất")
        return max(dates)

    async def _snapshot(self) -> dict[str, dict]:
        """Giá phiên gần nhất của toàn bộ mã."""
        day = await self._latest_date()
        data = await self.get_json(
            f"{self.finfo}/stock_prices", {"q": f"date:{day}", "size": 5000}, ttl=30
        )
        return {r["code"]: r for r in data.get("data", []) if r.get("code")}

    async def list_assets(self) -> list[AssetSummary]:
        stocks = await self._stocks()
        try:
            prices = await self._snapshot()
        except ProviderError:
            prices = {}  # vẫn hiện danh sách mã nếu không lấy được giá
        out = []
        for code, s in stocks.items():
            p = prices.get(code, {})
            out.append(
                AssetSummary(
                    category=self.category,
                    symbol=code,
                    display=code,
                    name=s.get("companyName") or s.get("shortName") or code,
                    exchange=str(s.get("floor", "")).upper(),
                    price=_row_price(p, "close"),
                    change_pct=_f(p.get("pctChange")),
                    volume=_f(p.get("nmVolume")),
                )
            )
        out.sort(key=lambda a: (a.volume or 0) * (a.price or 0), reverse=True)
        return out

    # ---------- nến ----------
    async def candles(self, symbol: str, timeframe: str, limit: int = 500) -> list[Candle]:
        if timeframe not in TF_MAP:
            raise ProviderError(f"Khung thời gian không hỗ trợ cho CK Việt Nam: {timeframe}")
        resolution, days = TF_MAP[timeframe]
        now = int(time.time())
        data = await self.get_json(
            self.chart_url,
            {
                "resolution": resolution,
                "symbol": symbol.upper(),
                "from": now - days * 86400,
                "to": now,
            },
            ttl=15 if resolution.isdigit() else 120,
        )
        status = data.get("s")
        if status == "no_data":
            return []
        if status != "ok":
            raise ProviderError(f"VNDirect chart lỗi: {data.get('errmsg') or status}")
        closes = data.get("c") or []
        scale = detect_scale(closes)
        candles = [
            Candle(int(t), o * scale, h * scale, lo * scale, c * scale, float(v or 0))
            for t, o, h, lo, c, v in zip(
                data.get("t", []), data.get("o", []), data.get("h", []),
                data.get("l", []), closes, data.get("v", []),
            )
            if None not in (o, h, lo, c)
        ]
        return clean_candles(candles)[-limit:]

    # ---------- thông tin cơ bản ----------
    async def info(self, symbol: str) -> AssetInfo:
        code = symbol.upper()
        s = (await self._stocks()).get(code)
        if not s:
            raise NotFound(f"Không tìm thấy mã cổ phiếu {code}")

        since = (date.today() - timedelta(days=14)).isoformat()
        rows = (
            await self.get_json(
                f"{self.finfo}/stock_prices", {"q": f"code:{code}~date:gte:{since}", "size": 20}, ttl=30
            )
        ).get("data", [])
        p = max(rows, key=lambda r: r.get("date", "")) if rows else {}

        try:
            year = await self.candles(code, "1d", limit=260)
        except ProviderError:
            year = []

        price = _row_price(p, "close")
        fields = [
            InfoField("Giá tham chiếu", _row_price(p, "basicPrice"), "price"),
            InfoField("Giá trần", _row_price(p, "ceilingPrice"), "price"),
            InfoField("Giá sàn", _row_price(p, "floorPrice"), "price"),
            InfoField("Mở cửa", _row_price(p, "open"), "price"),
            InfoField("Cao nhất", _row_price(p, "high"), "price"),
            InfoField("Thấp nhất", _row_price(p, "low"), "price"),
            InfoField("KL khớp lệnh", _f(p.get("nmVolume")), "volume"),
            InfoField("Đỉnh 52 tuần", max((c.high for c in year), default=None), "price"),
            InfoField("Đáy 52 tuần", min((c.low for c in year), default=None), "price"),
            InfoField("Sàn niêm yết", str(s.get("floor", "")).upper(), "text"),
            InfoField("Ngày niêm yết", s.get("listedDate"), "date"),
            InfoField("Tên tiếng Anh", s.get("companyNameEng"), "text"),
            InfoField("Phiên gần nhất", p.get("date"), "date"),
        ]
        return AssetInfo(
            category=self.category,
            symbol=code,
            display=code,
            name=s.get("companyName") or code,
            exchange=str(s.get("floor", "")).upper(),
            currency="VND",
            price=price,
            change=_row_price(p, "change"),
            change_pct=_f(p.get("pctChange")),
            fields=[f for f in fields if f.value not in (None, "")],
        )


def _f(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _row_price(row: dict, key: str) -> float | None:
    """Giá trong /stock_prices tính theo nghìn đồng."""
    return to_vnd(row.get(key)) if row.get(key) is not None else None
