from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.app.services.market_data import get_indexes, get_kline, get_quote


app = FastAPI(
    title="QuantDash Market Data API",
    description="FastAPI BFF/data service for real A-share quote, K-line, and market index data.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "quantdash-market-api"}


@app.get("/api/market/indexes")
def market_indexes() -> dict:
    try:
        return get_indexes()
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/api/stock/quote/{symbol}")
def stock_quote(symbol: str) -> dict:
    try:
        return get_quote(symbol)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/api/stock/kline/{symbol}")
def stock_kline(
    symbol: str,
    kline_type: Literal["daily", "weekly", "monthly", "yearly"] = Query("daily", alias="type"),
) -> dict:
    try:
        return get_kline(symbol, kline_type)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
