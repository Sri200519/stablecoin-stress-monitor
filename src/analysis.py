from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .config import ASSET_ORDER, PHASES


def assign_phase(timestamp: pd.Timestamp) -> str:
    naive = timestamp.tz_convert(None) if timestamp.tzinfo else timestamp
    for phase, start, end in PHASES:
        if pd.Timestamp(start) <= naive <= pd.Timestamp(end):
            return phase
    return "Outside scope"


def enrich_prices(prices: pd.DataFrame) -> pd.DataFrame:
    frame = prices.copy()
    frame["deviation_usd"] = frame["price_usd"] - 1.0
    frame["deviation_pct"] = frame["deviation_usd"] * 100.0
    frame["absolute_deviation_pct"] = frame["deviation_pct"].abs()
    frame["downside_depeg_pct"] = np.maximum(0.0, -frame["deviation_pct"])
    frame["phase"] = frame["timestamp"].map(assign_phase)
    return frame


def recovery_after_breach(
    group: pd.DataFrame,
    threshold_pct: float,
    consecutive_observations: int = 24,
) -> dict[str, Any]:
    """Find recovery after the first threshold breach using sustained hourly observations."""
    ordered = group.sort_values("timestamp").reset_index(drop=True)
    breached = ordered["absolute_deviation_pct"] > threshold_pct
    if not breached.any():
        return {
            "breach_time": None,
            "recovery_time": None,
            "recovery_hours": None,
            "status": f"No breach beyond {threshold_pct:.1f}%",
        }
    first_index = int(np.flatnonzero(breached.to_numpy())[0])
    breach_time = ordered.loc[first_index, "timestamp"]
    in_band = ordered["absolute_deviation_pct"] <= threshold_pct
    rolling = in_band.rolling(consecutive_observations).sum()
    candidates = rolling.index[(rolling == consecutive_observations) & (rolling.index >= first_index)]
    if len(candidates) == 0:
        return {
            "breach_time": breach_time,
            "recovery_time": None,
            "recovery_hours": None,
            "status": "Not recovered in study window",
        }
    end_index = int(candidates[0])
    start_index = end_index - consecutive_observations + 1
    recovery_time = ordered.loc[start_index, "timestamp"]
    hours = (recovery_time - breach_time).total_seconds() / 3600.0
    return {
        "breach_time": breach_time,
        "recovery_time": recovery_time,
        "recovery_hours": float(hours),
        "status": "Recovered",
    }


def build_asset_summary(prices: pd.DataFrame, threshold_pct: float = 1.0) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for asset in ASSET_ORDER:
        group = prices[prices["asset"] == asset].sort_values("timestamp")
        if group.empty:
            continue
        min_row = group.loc[group["price_usd"].idxmin()]
        max_abs_row = group.loc[group["absolute_deviation_pct"].idxmax()]
        recovery = recovery_after_breach(group, threshold_pct)
        records.append(
            {
                "asset": asset,
                "observations": int(len(group)),
                "min_price_usd": float(min_row["price_usd"]),
                "min_price_time": min_row["timestamp"],
                "max_downside_depeg_pct": float(group["downside_depeg_pct"].max()),
                "max_abs_deviation_pct": float(max_abs_row["absolute_deviation_pct"]),
                "max_abs_deviation_time": max_abs_row["timestamp"],
                "hours_within_0_5pct": float((group["absolute_deviation_pct"] <= 0.5).mean() * 100),
                "hours_within_1pct": float((group["absolute_deviation_pct"] <= 1.0).mean() * 100),
                "threshold_pct": threshold_pct,
                **recovery,
            }
        )
    return pd.DataFrame(records)


def build_phase_summary(prices: pd.DataFrame) -> pd.DataFrame:
    summary = (
        prices.groupby(["asset", "phase"], observed=True)
        .agg(
            observations=("price_usd", "size"),
            average_price_usd=("price_usd", "mean"),
            min_price_usd=("price_usd", "min"),
            max_price_usd=("price_usd", "max"),
            mean_abs_deviation_pct=("absolute_deviation_pct", "mean"),
            max_abs_deviation_pct=("absolute_deviation_pct", "max"),
        )
        .reset_index()
    )
    phase_order = pd.CategoricalDtype([phase[0] for phase in PHASES], ordered=True)
    summary["phase"] = summary["phase"].astype(phase_order)
    return summary.sort_values(["asset", "phase"]).reset_index(drop=True)


def build_supply_summary(supply: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for asset, group in supply.groupby("asset"):
        group = group.sort_values("date")
        first = group.iloc[0]
        last = group.iloc[-1]
        complete = first["coverage_status"] == "complete"
        change = float(last["supply_tokens"] - first["supply_tokens"]) if complete else np.nan
        records.append(
            {
                "asset": asset,
                "coverage_status": first["coverage_status"],
                "first_date": first["date"],
                "last_date": last["date"],
                "first_supply_tokens": float(first["supply_tokens"]),
                "last_supply_tokens": float(last["supply_tokens"]),
                "change_tokens": change,
                "change_pct": change / float(first["supply_tokens"]) * 100.0 if complete else np.nan,
            }
        )
    return pd.DataFrame(records)

