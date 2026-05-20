from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.app.services.data_center import (
    data_health,
    get_announcements,
    get_served_kline,
    list_data_jobs,
    quality_daily_bars,
    run_data_job,
    search_stock_profiles,
    stock_profile,
    stock_status,
    trading_days,
)
from backend.app.services.news_data import get_hot_news, get_stock_news
from backend.app.services.market_data import (
    get_financials,
    get_indexes,
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
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "quantdash-market-api"}


@app.get("/api/data/health")
def data_center_health() -> dict:
    return data_health()


@app.get("/api/data/jobs")
def data_jobs() -> dict:
    return list_data_jobs()


@app.post("/api/data/jobs/run")
def data_jobs_run(job_type: str = Query(..., alias="type")) -> dict:
    try:
        return run_data_job(job_type)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


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
    kline_type: Literal[
        "1min", "5day", "daily", "weekly", "monthly", "yearly"
    ] = Query("daily", alias="type"),
    adjust: Literal["none", "qfq", "hfq"] = Query("none"),
) -> dict:
    try:
        return get_served_kline(symbol, kline_type, adjust)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/api/stocks/search")
def stocks_search(q: str = Query("")) -> dict:
    return search_stocks(q)


@app.get("/api/stocks/profiles")
def stocks_profiles_search(q: str = Query(""), limit: int = Query(20, ge=1, le=100)) -> dict:
    return search_stock_profiles(q, limit)


@app.get("/api/stocks/{symbol}/profile")
def stocks_profile(symbol: str) -> dict:
    try:
        return stock_profile(symbol)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/api/calendar/trading-days")
def calendar_trading_days(
    start: str | None = Query(None),
    end: str | None = Query(None),
    exchange: str = Query("SSE"),
) -> dict:
    try:
        return trading_days(start, end, exchange)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/api/stock/status/{symbol}")
def stock_daily_status(symbol: str, target_date: str | None = Query(None, alias="date")) -> dict:
    try:
        return stock_status(symbol, target_date)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/api/data/quality/daily-bars/{symbol}")
def data_quality_daily_bars(
    symbol: str,
    adjust: Literal["none", "qfq", "hfq"] = Query("none"),
) -> dict:
    try:
        return quality_daily_bars(symbol, adjust)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


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
def stock_news(symbol: str, limit: int = Query(30, ge=1, le=100)) -> dict:
    try:
        return get_stock_news(symbol, limit)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/stock/announcements/{symbol}")
def stock_announcements(symbol: str, limit: int = Query(30, ge=1, le=100)) -> dict:
    try:
        return get_announcements(symbol, limit)
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


@app.get("/api/news/hot")
def hot_news(
    sources: str | None = Query(None),
    limit: int = Query(60, ge=1, le=200),
) -> dict:
    return get_hot_news(sources, limit)
