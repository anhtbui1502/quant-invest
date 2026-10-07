"""Dữ liệu giả lập để chạy thử giao diện khi không có mạng (DEMO_MODE=1).

Giá được sinh ngẫu nhiên nhưng cố định theo mã, KHÔNG phải giá thật.
"""
from __future__ import annotations

import random
import time

from ..models import AssetInfo, AssetSummary, Candle, InfoField
from .base import NotFound, Provider
from .binance import TIMEFRAMES as CRYPTO_TF
from .vndirect import TIMEFRAMES as VN_TF

TF_SECONDS = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400, "1w": 604800}

VN_STOCKS = [
    ("FPT", "Công ty Cổ phần FPT", "HOSE", 128.4),
    ("VNM", "Công ty Cổ phần Sữa Việt Nam", "HOSE", 61.2),
    ("HPG", "Công ty Cổ phần Tập đoàn Hòa Phát", "HOSE", 26.85),
    ("VCB", "Ngân hàng TMCP Ngoại thương Việt Nam", "HOSE", 91.5),
    ("MWG", "Công ty Cổ phần Đầu tư Thế Giới Di Động", "HOSE", 63.8),
    ("SSI", "Công ty Cổ phần Chứng khoán SSI", "HOSE", 32.1),
    ("TCB", "Ngân hàng TMCP Kỹ thương Việt Nam", "HOSE", 24.95),
    ("VIC", "Tập đoàn Vingroup - Công ty CP", "HOSE", 44.7),
    ("ACB", "Ngân hàng TMCP Á Châu", "HOSE", 25.3),
    ("GAS", "Tổng Công ty Khí Việt Nam - CTCP", "HOSE", 69.9),
    ("SHS", "Công ty Cổ phần Chứng khoán Sài Gòn - Hà Nội", "HNX", 13.4),
    ("PVS", "Tổng Công ty CP Dịch vụ Kỹ thuật Dầu khí Việt Nam", "HNX", 33.6),
    ("IDC", "Tổng Công ty IDICO - CTCP", "HNX", 52.3),
    ("CEO", "Công ty Cổ phần Tập đoàn C.E.O", "HNX", 17.8),
    ("BSR", "Công ty Cổ phần Lọc hóa dầu Bình Sơn", "UPCOM", 21.6),
    ("ACV", "Tổng Công ty Cảng hàng không Việt Nam - CTCP", "UPCOM", 112.0),
    ("VGI", "Tổng Công ty Cổ phần Đầu tư Quốc tế Viettel", "UPCOM", 89.5),
]

CRYPTO = [
    ("BTC", 62450.0), ("ETH", 2480.0), ("SOL", 148.2), ("BNB", 565.0), ("XRP", 0.534),
    ("DOGE", 0.1092), ("ADA", 0.351), ("TON", 5.21), ("AVAX", 26.4), ("LINK", 11.2),
    ("PEPE", 0.00000912), ("SUI", 1.82),
]


def _series(seed: str, start: float, n: int, step: int, vol_scale: float) -> list[Candle]:
    rnd = random.Random(seed)
    now = int(time.time())
    t0 = now - now % step - (n - 1) * step
    price, out = start, []
    for i in range(n):
        o = price
        c = o * (1 + rnd.gauss(0.0004, 0.018))
        h = max(o, c) * (1 + abs(rnd.gauss(0, 0.006)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, 0.006)))
        out.append(Candle(t0 + i * step, o, h, lo, c, vol_scale * rnd.uniform(0.3, 1.7)))
        price = c
    # Đưa giá cuối về đúng giá tham chiếu để danh sách và biểu đồ khớp nhau.
    k = start / out[-1].close
    return [Candle(c.time, c.open * k, c.high * k, c.low * k, c.close * k, c.volume) for c in out]


class DemoVNProvider(Provider):
    category = "vn"
    label = "CK Việt Nam"
    timeframes = VN_TF

    def _meta(self, code: str):
        for row in VN_STOCKS:
            if row[0] == code.upper():
                return row
        raise NotFound(f"Không tìm thấy mã cổ phiếu {code}")

    async def list_assets(self) -> list[AssetSummary]:
        out = []
        for code, name, floor, px in VN_STOCKS:
            bars = _series(code + "1d", px * 1000, 2, 86400, 1)
            out.append(AssetSummary("vn", code, code, name, floor, px * 1000,
                                    (bars[-1].close / bars[-1].open - 1) * 100,
                                    random.Random(code).uniform(1e6, 2e7)))
        return out

    async def candles(self, symbol: str, timeframe: str, limit: int = 500) -> list[Candle]:
        code, _, _, px = self._meta(symbol)
        return _series(code + timeframe, px * 1000, min(limit, 300), TF_SECONDS[timeframe], 3e6)

    async def info(self, symbol: str) -> AssetInfo:
        code, name, floor, px = self._meta(symbol)
        row = next(a for a in await self.list_assets() if a.symbol == code)
        ref = row.price / (1 + row.change_pct / 100)
        band = {"HOSE": 0.07, "HNX": 0.10, "UPCOM": 0.15}[floor]
        year = await self.candles(code, "1d", 260)
        return AssetInfo("vn", code, code, name, floor, "VND", row.price, row.price - ref, row.change_pct, [
            InfoField("Giá tham chiếu", round(ref, -1), "price"),
            InfoField("Giá trần", round(ref * (1 + band), -2), "price"),
            InfoField("Giá sàn", round(ref * (1 - band), -2), "price"),
            InfoField("KL khớp lệnh", row.volume, "volume"),
            InfoField("Đỉnh 52 tuần", max(c.high for c in year), "price"),
            InfoField("Đáy 52 tuần", min(c.low for c in year), "price"),
            InfoField("Sàn niêm yết", floor, "text"),
            InfoField("Ghi chú", "Dữ liệu giả lập (DEMO_MODE)", "text"),
        ])


class DemoCryptoProvider(Provider):
    category = "crypto"
    label = "Crypto"
    timeframes = CRYPTO_TF

    def _meta(self, symbol: str):
        for base, px in CRYPTO:
            if f"{base}USDT" == symbol.upper():
                return base, px
        raise NotFound(f"Không tìm thấy mã {symbol} trên Binance")

    async def list_assets(self) -> list[AssetSummary]:
        out = []
        for base, px in CRYPTO:
            bars = _series(base + "1d", px, 2, 86400, 1)
            out.append(AssetSummary("crypto", f"{base}USDT", f"{base}/USDT", base, "Binance", px,
                                    (bars[-1].close / bars[-1].open - 1) * 100,
                                    random.Random(base).uniform(1e7, 2e9)))
        return out

    async def candles(self, symbol: str, timeframe: str, limit: int = 500) -> list[Candle]:
        base, px = self._meta(symbol)
        return _series(base + timeframe, px, min(limit, 300), TF_SECONDS[timeframe], 1e6 / px)

    async def info(self, symbol: str) -> AssetInfo:
        base, px = self._meta(symbol)
        row = next(a for a in await self.list_assets() if a.symbol == symbol.upper())
        day = await self.candles(symbol, "1h", 24)
        return AssetInfo("crypto", row.symbol, row.display, base, "Binance", "USDT", px,
                         px - px / (1 + row.change_pct / 100), row.change_pct, [
            InfoField("Cao nhất 24h", max(c.high for c in day), "price"),
            InfoField("Thấp nhất 24h", min(c.low for c in day), "price"),
            InfoField("Giá trị 24h (USDT)", row.volume, "volume"),
            InfoField("Sàn", "Binance Spot", "text"),
            InfoField("Ghi chú", "Dữ liệu giả lập (DEMO_MODE)", "text"),
        ])
