"""Test phần xử lý dữ liệu bằng phản hồi mẫu, không cần mạng."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from backend.app.providers.base import fold, make_client, NotFound, ProviderError
from backend.app.providers.binance import BinanceProvider
from backend.app.providers.vndirect import VNDirectProvider, detect_scale

FIX = Path(__file__).parent / "fixtures"


def load(name: str):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def run(coro):
    return asyncio.run(coro)


# ---------------- Binance ----------------
def binance_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if request.url.host == "blocked.example":
        return httpx.Response(451, text="Service unavailable from a restricted location")
    if path.endswith("/exchangeInfo"):
        return httpx.Response(200, json=load("binance_exchange_info.json"))
    if path.endswith("/ticker/24hr"):
        sym = request.url.params.get("symbol")
        rows = load("binance_ticker_24hr.json")
        if sym:
            match = [r for r in rows if r["symbol"] == sym]
            if not match:
                return httpx.Response(400, json={"code": -1121, "msg": "Invalid symbol."})
            return httpx.Response(200, json=match[0])
        return httpx.Response(200, json=rows)
    if path.endswith("/klines"):
        return httpx.Response(200, json=load("binance_klines.json"))
    return httpx.Response(404)


def binance(base_urls=None):
    return BinanceProvider(
        make_client(httpx.MockTransport(binance_handler)),
        base_urls=base_urls or ["https://api.binance.com"],
    )


def test_binance_lists_only_trading_usdt_pairs_sorted_by_value():
    items = run(binance().list_assets())
    symbols = [a.symbol for a in items]
    assert symbols == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]  # ETHBTC (quote BTC) & LUNAUSDT (BREAK) bị loại
    btc = items[0]
    assert btc.display == "BTC/USDT"
    assert btc.price == 62450.12
    assert btc.change_pct == 1.25


def test_binance_candles_parse_ms_to_seconds():
    candles = run(binance().candles("btcusdt", "1h"))
    assert len(candles) == 3
    assert candles[0].time == 1759795200
    assert candles[0].open == 62000.0 and candles[0].volume == 120.5


def test_binance_falls_back_to_second_domain():
    p = binance(["https://blocked.example", "https://data-api.binance.vision"])
    assert len(run(p.candles("BTCUSDT", "1d"))) == 3


def test_binance_info_and_unknown_symbol():
    info = run(binance().info("ETHUSDT"))
    assert info.currency == "USDT" and info.price == 2480.5
    assert any(f.label == "Cao nhất 24h" for f in info.fields)
    with pytest.raises(NotFound):
        run(binance().info("NOPEUSDT"))


def test_binance_search():
    res = run(binance().search("sol"))
    assert res[0].symbol == "SOLUSDT"
    assert run(binance().search("btc/usdt"))[0].symbol == "BTCUSDT"


# ---------------- VNDirect ----------------
def vnd_handler(request: httpx.Request) -> httpx.Response:
    path, q = request.url.path, request.url.params.get("q", "")
    if path.endswith("/stocks"):
        return httpx.Response(200, json=load("vnd_stocks.json"))
    if path.endswith("/stock_prices"):
        rows = load("vnd_stock_prices.json")["data"]
        if q.startswith("code:"):
            code = q.split("~")[0].split(":")[1]
            rows = [r for r in rows if r["code"] == code]
        elif q.startswith("date:"):
            day = q.split(":")[1]
            rows = [r for r in rows if r["date"] == day]
        return httpx.Response(200, json={"data": rows})
    if path.endswith("/history"):
        if request.url.params["symbol"] == "XXX":
            return httpx.Response(200, json={"s": "no_data"})
        return httpx.Response(200, json=load("vnd_dchart.json"))
    return httpx.Response(404)


def vnd():
    return VNDirectProvider(make_client(httpx.MockTransport(vnd_handler)),
                            finfo_url="https://finfo-api.vndirect.com.vn/v4",
                            chart_url="https://dchart-api.vndirect.com.vn/dchart/history")


def test_vn_list_uses_latest_session_and_converts_to_vnd():
    items = run(vnd().list_assets())
    by = {a.symbol: a for a in items}
    assert set(by) == {"FPT", "VNM", "SHS", "BSR"}  # bỏ chứng quyền / mã không thuộc 3 sàn
    assert by["FPT"].price == 128400  # 128.4 nghìn đồng -> 128.400 đ
    assert by["FPT"].change_pct == 1.84
    assert by["SHS"].exchange == "HNX"
    assert items[0].symbol == "FPT"  # giá trị giao dịch lớn nhất lên đầu


def test_vn_candles_scale_and_no_data():
    candles = run(vnd().candles("fpt", "1d"))
    assert [c.close for c in candles] == [126100.0, 126100.0, 128400.0]
    assert candles[0].time < candles[-1].time
    assert run(vnd().candles("XXX", "1d")) == []
    with pytest.raises(ProviderError):
        run(vnd().candles("FPT", "4h"))  # CK VN không có khung 4h


def test_vn_info():
    info = run(vnd().info("FPT"))
    fields = {f.label: f.value for f in info.fields}
    assert info.price == 128400 and info.currency == "VND"
    assert fields["Giá tham chiếu"] == 126100
    assert fields["Giá trần"] == 134900
    assert fields["Đỉnh 52 tuần"] == 129000
    assert info.exchange == "HOSE"
    with pytest.raises(NotFound):
        run(vnd().info("ZZZ"))


def test_vn_search_without_accents():
    res = run(vnd().search("sua viet nam"))
    assert res[0].symbol == "VNM"
    assert run(vnd().search("FP"))[0].symbol == "FPT"


def test_detect_scale():
    assert detect_scale([26.85, 27.1]) == 1000
    assert detect_scale([26850, 27100]) == 1


def test_fold():
    assert fold("Hòa Phát Đầu Tư") == "hoa phat dau tu"
