"""Kiểm tra kết nối tới nguồn dữ liệu THẬT (Binance, VNDirect).

Chạy:  python -m scripts.check_sources
In ra từng bước OK / LỖI để biết nguồn nào đang hoạt động.
"""
from __future__ import annotations

import asyncio

from backend.app.providers.binance import BinanceProvider
from backend.app.providers.vndirect import VNDirectProvider


async def step(name, coro, show):
    try:
        result = await coro
        print(f"  OK   {name}: {show(result)}")
    except Exception as exc:  # noqa: BLE001 - in mọi lỗi cho người dùng xem
        print(f"  LỖI  {name}: {exc}")


async def main():
    print("Binance (crypto)")
    b = BinanceProvider()
    await step("Danh sách cặp USDT", b.list_assets(),
               lambda r: f"{len(r)} mã, đầu tiên {r[0].display} = {r[0].price}")
    await step("Nến BTCUSDT 1h", b.candles("BTCUSDT", "1h", 5),
               lambda r: f"{len(r)} nến, close cuối {r[-1].close}")
    await step("Thông tin ETHUSDT", b.info("ETHUSDT"), lambda r: f"giá {r.price}, {r.change_pct}%")

    print("VNDirect (cổ phiếu VN)")
    v = VNDirectProvider()
    await step("Danh sách cổ phiếu", v.list_assets(),
               lambda r: f"{len(r)} mã, có giá: {sum(1 for a in r if a.price)}; "
                         f"đầu tiên {r[0].symbol} = {r[0].price} đ")
    await step("Nến FPT 1D", v.candles("FPT", "1d", 5),
               lambda r: f"{len(r)} nến, close cuối {r[-1].close} đ" if r else "không có dữ liệu")
    await step("Nến FPT 15m", v.candles("FPT", "15m", 5),
               lambda r: f"{len(r)} nến" if r else "không có dữ liệu")
    await step("Thông tin FPT", v.info("FPT"),
               lambda r: f"giá {r.price} đ, {r.change_pct}%, {len(r.fields)} trường")

    await b.client.aclose()
    await v.client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
