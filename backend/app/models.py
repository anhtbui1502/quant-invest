"""Kiểu dữ liệu dùng chung giữa các nguồn và API."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Candle:
    time: int  # unix giây (UTC), thời điểm mở nến
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass
class AssetSummary:
    """Một dòng trong danh sách / kết quả tìm kiếm."""

    category: str  # "vn" | "crypto"
    symbol: str  # mã dùng để gọi API: "FPT", "BTCUSDT"
    display: str  # mã hiển thị: "FPT", "BTC/USDT"
    name: str
    exchange: str  # HOSE / HNX / UPCOM / Binance
    price: float | None = None
    change_pct: float | None = None
    volume: float | None = None  # khối lượng (VN) hoặc giá trị GD theo đồng quote (crypto)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class InfoField:
    label: str
    value: Any
    kind: str = "number"  # number | price | percent | text | date | volume

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AssetInfo:
    category: str
    symbol: str
    display: str
    name: str
    exchange: str
    currency: str
    price: float | None = None
    change: float | None = None
    change_pct: float | None = None
    fields: list[InfoField] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["fields"] = [f.to_dict() for f in self.fields]
        return d
