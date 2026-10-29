from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from .config import (
    ASSETS,
    COINMETRICS_ENDPOINT,
    END_DATE,
    JUNE_1_TIMESTAMP,
    PRICE_ENDPOINT,
    RAW_DIR,
    START_DATE,
    START_TIMESTAMP,
    UST_SUPPLY_ENDPOINT,
)


class DataSourceError(RuntimeError):
    """Raised when a live source fails and no usable cache is available."""


def _request_json(url: str, params: dict[str, Any] | None = None, attempts: int = 3) -> Any:
    headers = {"User-Agent": "stablecoin-stress-monitor/0.2 (academic project)"}
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=45)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < attempts - 1:
                time.sleep(1.5 * (attempt + 1))
    raise DataSourceError(f"Request failed after {attempts} attempts: {url}: {last_error}")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_price_history(refresh: bool = False, offline: bool = False) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return hourly May 2022 prices from DefiLlama's public coins endpoint."""
    cache_path = RAW_DIR / "defillama_prices_hourly_may2022.json"
    coin_selector = ",".join(ASSETS)
    # The free chart route rejects very large hourly spans, so the month is
    # requested in two non-overlapping chunks and combined into one cache.
    chunk_spans = [120, 120, 120, 120, 120, 120, 24]
    chunks: list[dict[str, int]] = []
    chunk_start = START_TIMESTAMP
    for chunk_span in chunk_spans:
        chunks.append({"start": chunk_start, "span": chunk_span})
        chunk_start += chunk_span * 3600
    source_url = PRICE_ENDPOINT.format(coins=coin_selector)

    if offline:
        if not cache_path.exists():
            raise DataSourceError(f"Offline cache is missing: {cache_path}")
        payload = _read_json(cache_path)
        source_mode = "cached"
    elif refresh or not cache_path.exists():
        combined: dict[str, Any] = {"coins": {source_id: {"prices": []} for source_id in ASSETS}}
        for chunk in chunks:
            params = {**chunk, "period": "1h", "searchWidth": "4h"}
            response = _request_json(source_url, params=params)
            for source_id in ASSETS:
                coin = response.get("coins", {}).get(source_id, {})
                target = combined["coins"][source_id]
                target["symbol"] = coin.get("symbol")
                target["confidence"] = coin.get("confidence")
                target["prices"].extend(coin.get("prices", []))
        payload = combined
        _write_json(cache_path, payload)
        source_mode = "live"
    else:
        payload = _read_json(cache_path)
        source_mode = "cached"

    rows: list[dict[str, Any]] = []
    for source_id, asset in ASSETS.items():
        coin = payload.get("coins", {}).get(source_id, {})
        for item in coin.get("prices", []):
            timestamp = int(item["timestamp"])
            if START_TIMESTAMP <= timestamp < JUNE_1_TIMESTAMP:
                rows.append(
                    {
                        "timestamp": pd.to_datetime(timestamp, unit="s", utc=True),
                        "asset": asset,
                        "price_usd": float(item["price"]),
                        "source_id": source_id,
                        "source_confidence": coin.get("confidence"),
                    }
                )
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise DataSourceError("The price endpoint returned no May 2022 observations.")
    frame["timestamp"] = frame["timestamp"].dt.floor("h")
    frame = frame.drop_duplicates(["asset", "timestamp"], keep="last")
    frame = frame.sort_values(["asset", "timestamp"]).reset_index(drop=True)
    metadata = {
        "source": "DefiLlama Coins API",
        "endpoint": source_url,
        "parameters": {"chunks": chunks, "period": "1h", "searchWidth": "4h"},
        "mode": source_mode,
        "retrieved_rows": int(len(frame)),
        "assets": sorted(frame["asset"].unique().tolist()),
        "notes": "No API key required. Prices are DefiLlama's aggregated CoinGecko identifiers.",
    }
    return frame, metadata


def load_reserve_supply(refresh: bool = False, offline: bool = False) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return daily circulating supply for USDT and USDC from Coin Metrics."""
    cache_path = RAW_DIR / "coinmetrics_supply_usdt_usdc_may2022.json"
    params: dict[str, Any] = {
        "assets": "usdt,usdc",
        "metrics": "SplyCur",
        "frequency": "1d",
        "start_time": START_DATE,
        "end_time": END_DATE,
        "page_size": 10000,
    }
    api_key = os.getenv("COINMETRICS_API_KEY", "").strip()
    if api_key:
        params["api_key"] = api_key

    if offline:
        if not cache_path.exists():
            raise DataSourceError(f"Offline cache is missing: {cache_path}")
        payload = _read_json(cache_path)
        source_mode = "cached"
    elif refresh or not cache_path.exists():
        payload = _request_json(COINMETRICS_ENDPOINT, params=params)
        _write_json(cache_path, payload)
        source_mode = "live"
    else:
        payload = _read_json(cache_path)
        source_mode = "cached"

    rows = [
        {
            "date": pd.to_datetime(item["time"], utc=True).date(),
            "asset": item["asset"].upper(),
            "supply_tokens": float(item["SplyCur"]),
            "coverage_status": "complete",
        }
        for item in payload.get("data", [])
        if item.get("SplyCur") is not None
    ]
    frame = pd.DataFrame(rows).sort_values(["asset", "date"]).reset_index(drop=True)
    if frame.empty:
        raise DataSourceError("Coin Metrics returned no USDT/USDC supply observations.")
    safe_params = {key: value for key, value in params.items() if key != "api_key"}
    metadata = {
        "source": "Coin Metrics Community API",
        "endpoint": COINMETRICS_ENDPOINT,
        "parameters": safe_params,
        "mode": source_mode,
        "retrieved_rows": int(len(frame)),
        "notes": "SplyCur is available historically for USDT and USDC without a community API key.",
    }
    return frame, metadata


def load_ust_supply_partial(refresh: bool = False, offline: bool = False) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return the available May 2022 UST chain balance series with an explicit partial flag."""
    cache_path = RAW_DIR / "defillama_ust_supply_partial_may2022.json"
    if offline:
        if not cache_path.exists():
            raise DataSourceError(f"Offline cache is missing: {cache_path}")
        compact = _read_json(cache_path)
        source_mode = "cached"
    elif refresh or not cache_path.exists():
        payload = _request_json(UST_SUPPLY_ENDPOINT)
        totals: dict[int, float] = {}
        for chain_data in payload.get("chainBalances", {}).values():
            for item in chain_data.get("tokens", []):
                timestamp = int(item.get("date", 0))
                circulating = item.get("circulating", {}).get("peggedUSD")
                if START_TIMESTAMP <= timestamp < JUNE_1_TIMESTAMP and circulating is not None:
                    totals[timestamp] = totals.get(timestamp, 0.0) + float(circulating)
        compact = {
            "source": "DefiLlama Stablecoins API",
            "endpoint": UST_SUPPLY_ENDPOINT,
            "warning": (
                "Native Terra Classic coverage begins during the crisis while bridged-chain records appear earlier; "
                "chain-level balances may also include bridged representations. "
                "Use as a provisional series, not a directly comparable full-month measure."
            ),
            "data": [{"timestamp": ts, "supply_tokens": value} for ts, value in sorted(totals.items())],
        }
        _write_json(cache_path, compact)
        source_mode = "live"
    else:
        compact = _read_json(cache_path)
        source_mode = "cached"

    rows = [
        {
            "date": pd.to_datetime(item["timestamp"], unit="s", utc=True).date(),
            "asset": "UST",
            "supply_tokens": float(item["supply_tokens"]),
            "coverage_status": "partial_provisional",
        }
        for item in compact.get("data", [])
    ]
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame = frame.groupby(["asset", "date", "coverage_status"], as_index=False)["supply_tokens"].last()
    metadata = {
        "source": compact.get("source", "DefiLlama Stablecoins API"),
        "endpoint": compact.get("endpoint", UST_SUPPLY_ENDPOINT),
        "mode": source_mode,
        "retrieved_rows": int(len(frame)),
        "notes": compact.get("warning"),
    }
    return frame, metadata

