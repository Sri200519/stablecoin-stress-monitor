from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
FIGURE_DIR = EVIDENCE_DIR / "figures"

START_DATE = "2022-05-01"
END_DATE = "2022-05-31"
START_TIMESTAMP = 1651363200
JUNE_1_TIMESTAMP = 1654041600

ASSETS = {
    "coingecko:terrausd": "UST",
    "coingecko:tether": "USDT",
    "coingecko:usd-coin": "USDC",
}

ASSET_ORDER = ["UST", "USDT", "USDC"]
ASSET_COLORS = {"UST": "#C2413B", "USDT": "#198754", "USDC": "#1F6FEB"}

PHASES = [
    ("Pre-crisis", "2022-05-01", "2022-05-06 23:59:59"),
    ("Crisis", "2022-05-07", "2022-05-15 23:59:59"),
    ("Post-crisis", "2022-05-16", "2022-05-31 23:59:59"),
]

PRICE_ENDPOINT = "https://coins.llama.fi/chart/{coins}"
COINMETRICS_ENDPOINT = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
UST_SUPPLY_ENDPOINT = "https://stablecoins.llama.fi/stablecoin/3"


def ensure_directories() -> None:
    for path in (RAW_DIR, PROCESSED_DIR, FIGURE_DIR):
        path.mkdir(parents=True, exist_ok=True)

