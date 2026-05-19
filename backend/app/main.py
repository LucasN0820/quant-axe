from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.app.services.market_data import (
    get_financials,
    get_indexes,
    get_kline,
    get_order_book,
    get_quote,
    search_stocks,
    unavailable_dataset,
)


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


@app.get("/api/stocks/search")
def stocks_search(q: str = Query("")) -> dict:
    return search_stocks(q)


@app.get("/api/stock/intraday/{symbol}")
def stock_intraday(symbol: str) -> dict:
    try:
        return unavailable_dataset(symbol, "not_configured")
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/stock/order-book/{symbol}")
def stock_order_book(symbol: str) -> dict:
    try:
        return get_order_book(symbol)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/api/stock/trades/{symbol}")
def stock_trades(symbol: str) -> dict:
    try:
        return unavailable_dataset(symbol, "not_configured")
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/stock/news/{symbol}")
def stock_news(symbol: str) -> dict:
    try:
        return unavailable_dataset(symbol, "not_configured")
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/stock/announcements/{symbol}")
def stock_announcements(symbol: str) -> dict:
    try:
        return unavailable_dataset(symbol, "not_configured")
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/stock/financials/{symbol}")
def stock_financials(symbol: str) -> dict:
    try:
        return get_financials(symbol)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/api/intelligence/hot-keywords")
def hot_keywords() -> dict:
    return unavailable_dataset(None, "not_configured")
