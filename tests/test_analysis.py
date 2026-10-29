from __future__ import annotations

import pandas as pd

from src.analysis import assign_phase, enrich_prices, recovery_after_breach


def test_phase_boundaries() -> None:
    assert assign_phase(pd.Timestamp("2022-05-06 23:00", tz="UTC")) == "Pre-crisis"
    assert assign_phase(pd.Timestamp("2022-05-07 00:00", tz="UTC")) == "Crisis"
    assert assign_phase(pd.Timestamp("2022-05-16 00:00", tz="UTC")) == "Post-crisis"


def test_deviation_is_percentage_points_from_one_dollar() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2022-05-01T00:00:00Z", "2022-05-01T01:00:00Z"]),
            "asset": ["TEST", "TEST"],
            "price_usd": [0.98, 1.01],
        }
    )
    result = enrich_prices(frame)
    assert result["deviation_pct"].round(8).tolist() == [-2.0, 1.0]
    assert result["absolute_deviation_pct"].round(8).tolist() == [2.0, 1.0]


def test_recovery_requires_sustained_observations() -> None:
    timestamps = pd.date_range("2022-05-01", periods=30, freq="h", tz="UTC")
    prices = [1.0, 0.97] + [1.0] * 28
    frame = enrich_prices(pd.DataFrame({"timestamp": timestamps, "asset": "TEST", "price_usd": prices}))
    result = recovery_after_breach(frame, threshold_pct=1.0, consecutive_observations=24)
    assert result["status"] == "Recovered"
    assert result["recovery_time"] == timestamps[2]
    assert result["recovery_hours"] == 1.0


def test_no_recovery_when_window_ends_inside_breach() -> None:
    timestamps = pd.date_range("2022-05-01", periods=10, freq="h", tz="UTC")
    frame = enrich_prices(pd.DataFrame({"timestamp": timestamps, "asset": "TEST", "price_usd": [0.8] * 10}))
    result = recovery_after_breach(frame, threshold_pct=1.0, consecutive_observations=3)
    assert result["status"] == "Not recovered in study window"
    assert result["recovery_time"] is None

