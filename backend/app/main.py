"""Ứng dụng FastAPI: cung cấp API dữ liệu và phục vụ giao diện đã build."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .providers.base import NotFound, Provider, ProviderError, rank_search
from .providers.binance import BinanceProvider
from .providers.demo import DemoCryptoProvider, DemoVNProvider
from .providers.vndirect import VNDirectProvider

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


def build_providers(demo: bool) -> dict[str, Provider]:
    if demo:
        return {"vn": DemoVNProvider(), "crypto": DemoCryptoProvider()}
    return {"vn": VNDirectProvider(), "crypto": BinanceProvider()}


def create_app(providers: dict[str, Provider] | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        for p in app.state.providers.values():
            await p.client.aclose()

    app = FastAPI(title="Quant Invest", lifespan=lifespan)
    app.state.providers = providers or build_providers(config.DEMO_MODE)

    def get_provider(category: str) -> Provider:
        p = app.state.providers.get(category)
        if not p:
            raise HTTPException(404, f"Danh mục không tồn tại: {category}")
        return p

    async def call(coro):
        try:
            return await coro
        except NotFound as exc:
            raise HTTPException(404, str(exc)) from exc
        except ProviderError as exc:
            raise HTTPException(502, str(exc)) from exc

    @app.get("/api/categories")
    async def categories():
        return {
            "demo": config.DEMO_MODE,
            "categories": [
                {"id": k, "label": p.label, "timeframes": p.timeframes}
                for k, p in app.state.providers.items()
            ],
        }

    @app.get("/api/assets/{category}")
    async def list_assets(category: str):
        items = await call(get_provider(category).list_assets())
        return {"items": [a.to_dict() for a in items]}

    @app.get("/api/search")
    async def search(q: str = Query(..., min_length=1), category: str | None = None, limit: int = 20):
        cats = [category] if category else list(app.state.providers)
        results, errors = [], []
        for c in cats:
            try:
                results += await get_provider(c).search(q, limit)
            except ProviderError as exc:
                errors.append(str(exc))
        if not results and errors:
            raise HTTPException(502, " | ".join(errors))
        # Gộp kết quả các danh mục rồi xếp hạng lại một lần.
        return {"items": [a.to_dict() for a in rank_search(results, q, limit)], "errors": errors}

    @app.get("/api/assets/{category}/{symbol}/candles")
    async def candles(category: str, symbol: str, tf: str = "1d", limit: int = Query(500, le=1000)):
        p = get_provider(category)
        if tf not in p.timeframes:
            raise HTTPException(400, f"Khung {tf} không hỗ trợ cho danh mục {category}")
        data = await call(p.candles(symbol, tf, limit))
        return {"symbol": symbol.upper(), "timeframe": tf, "candles": [c.__dict__ for c in data]}

    @app.get("/api/assets/{category}/{symbol}/info")
    async def info(category: str, symbol: str):
        return (await call(get_provider(category).info(symbol))).to_dict()

    # Phục vụ giao diện React đã build (frontend/dist), nếu có.
    if FRONTEND_DIST.exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="static")

        @app.get("/{path:path}", include_in_schema=False)
        async def spa(path: str):
            if path.startswith("api/"):
                raise HTTPException(404)
            file = (FRONTEND_DIST / path).resolve()
            if path and file.is_relative_to(FRONTEND_DIST) and file.is_file():
                return FileResponse(file)
            return FileResponse(FRONTEND_DIST / "index.html")

    return app


app = create_app()
