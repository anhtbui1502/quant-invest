"""Cấu hình đọc từ biến môi trường."""
from __future__ import annotations

import os


def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


# DEMO_MODE=1: dùng dữ liệu giả lập, không gọi mạng (để chạy thử / test giao diện).
DEMO_MODE = _flag("DEMO_MODE")

# Binance: thử lần lượt các domain. data-api.binance.vision là domain chỉ cung cấp
# dữ liệu thị trường, dùng khi api.binance.com bị chặn theo khu vực.
BINANCE_BASE_URLS = [
    u.strip()
    for u in os.getenv(
        "BINANCE_BASE_URLS",
        "https://api.binance.com,https://data-api.binance.vision",
    ).split(",")
    if u.strip()
]

VNDIRECT_CHART_URL = os.getenv(
    "VNDIRECT_CHART_URL", "https://dchart-api.vndirect.com.vn/dchart/history"
)
VNDIRECT_FINFO_URL = os.getenv("VNDIRECT_FINFO_URL", "https://finfo-api.vndirect.com.vn/v4")

HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "15"))
