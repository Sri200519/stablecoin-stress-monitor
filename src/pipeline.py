from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .analysis import build_asset_summary, build_phase_summary, build_supply_summary, enrich_prices
from .config import FIGURE_DIR, PROCESSED_DIR, ensure_directories
from .data_sources import load_price_history, load_reserve_supply, load_ust_supply_partial
from .figures import export_static_figures


def _json_default(value: Any) -> Any:
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Unsupported JSON type: {type(value)!r}")


def run_pipeline(refresh: bool = False, offline: bool = False) -> dict[str, Path]:
    ensure_directories()
    raw_prices, price_meta = load_price_history(refresh=refresh, offline=offline)
    reserve_supply, reserve_meta = load_reserve_supply(refresh=refresh, offline=offline)
    ust_supply, ust_meta = load_ust_supply_partial(refresh=refresh, offline=offline)

    prices = enrich_prices(raw_prices)
    supply = pd.concat([reserve_supply, ust_supply], ignore_index=True)
    supply = supply.sort_values(["asset", "date"]).reset_index(drop=True)
    asset_summary = build_asset_summary(prices, threshold_pct=1.0)
    phase_summary = build_phase_summary(prices)
    supply_summary = build_supply_summary(supply)
    data_quality = (
        prices.groupby("asset")
        .agg(
            observed_hours=("price_usd", "size"),
            first_observation=("timestamp", "min"),
            last_observation=("timestamp", "max"),
        )
        .reset_index()
    )
    data_quality["expected_hours"] = 31 * 24
    data_quality["coverage_pct"] = data_quality["observed_hours"] / data_quality["expected_hours"] * 100

    paths = {
        "prices": PROCESSED_DIR / "prices_hourly_may2022.csv",
        "supply": PROCESSED_DIR / "supply_daily_may2022.csv",
        "asset_summary": PROCESSED_DIR / "asset_summary_1pct.csv",
        "phase_summary": PROCESSED_DIR / "phase_summary.csv",
        "supply_summary": PROCESSED_DIR / "supply_summary.csv",
        "data_quality": PROCESSED_DIR / "data_quality_summary.csv",
        "metrics_json": PROCESSED_DIR / "metrics_and_provenance.json",
    }
    prices.to_csv(paths["prices"], index=False)
    supply.to_csv(paths["supply"], index=False)
    asset_summary.to_csv(paths["asset_summary"], index=False)
    phase_summary.to_csv(paths["phase_summary"], index=False)
    supply_summary.to_csv(paths["supply_summary"], index=False)
    data_quality.to_csv(paths["data_quality"], index=False)

    payload = {
        "analysis_definition": {
            "study_window": "2022-05-01 through 2022-05-31 UTC",
            "phases": {
                "pre_crisis": "May 1-6",
                "crisis": "May 7-15",
                "post_crisis": "May 16-31",
            },
            "deviation": "100 * abs(price_usd - 1.00)",
            "recovery": "First hour beginning 24 consecutive hourly observations inside the chosen band after the first breach.",
            "default_threshold_pct": 1.0,
        },
        "sources": {"prices": price_meta, "reserve_supply": reserve_meta, "ust_supply": ust_meta},
        "asset_summary": asset_summary.to_dict(orient="records"),
        "supply_summary": supply_summary.to_dict(orient="records"),
        "data_quality": data_quality.to_dict(orient="records"),
    }
    with paths["metrics_json"].open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=_json_default)

    figure_paths = export_static_figures(prices, supply, FIGURE_DIR)
    for index, figure_path in enumerate(figure_paths, 1):
        paths[f"figure_{index}"] = figure_path
    return paths

