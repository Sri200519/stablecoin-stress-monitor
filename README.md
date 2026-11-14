# Stablecoin Stress Monitor

This repository contains a reproducible data pipeline, processed evidence, static figures, and an interactive dashboard for the May 2022 comparison of UST, USDT, and USDC.

## What is complete

- Hourly price collection for May 1-31, 2022 from a public no-key endpoint
- Daily USDT and USDC circulating supply collection from Coin Metrics
- A documented partial UST supply series that is kept separate from comparable full-month results
- Peg-deviation, downside-depeg, crisis-phase, and sustained-recovery calculations
- Static figures and depeg threshold analyses for 0.5%, 1%, and 5%
- Offline rebuild support from submitted raw API caches
- Automated tests for phase boundaries, deviation calculations, and recovery logic

## Quick start

Python 3.12 or later is required by the pinned NumPy version.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/run_pipeline.py --offline
streamlit run scripts/app.py
```

To download fresh source data instead of using the included caches:

```bash
python scripts/run_pipeline.py --refresh
```

No API key is needed. See `API_SETUP.md` for endpoints, parameters, limitations, and the optional Coin Metrics key setting.

## Key outputs

| Path | Purpose |
| --- | --- |
| `data/raw/` | Submitted API response caches |
| `data/processed/prices_hourly_may2022.csv` | Clean price and deviation data |
| `data/processed/asset_summary_1pct.csv` | Main one-percent threshold results |
| `data/processed/threshold_comparison.csv` | Breach and recovery results at 0.5%, 1%, and 5% tolerances |
| `data/processed/phase_summary.csv` | Pre-crisis, crisis, and post-crisis statistics |
| `data/processed/supply_summary.csv` | Supply change calculations and coverage labels |
| `data/processed/data_quality_summary.csv` | Observed versus expected hourly coverage |
| `evidence/figures/` | Price, supply, and workflow figures |
| `tests/test_analysis.py` | Tests for the core calculations |

## Analytical definitions

Price deviation is `100 × (price - 1.00)`. Absolute deviation uses its absolute value. Downside depeg is the positive shortfall below one dollar. Recovery begins at the first hour of 24 consecutive clock hours inside the selected band after the first breach. A missing hour breaks the streak. An asset that never breaches the threshold is labeled separately from one that breaches and later recovers.

The study phases match Milestone 1: pre-crisis is May 1-6, crisis is May 7-15, and post-crisis is May 16-31. All timestamps are UTC.

## Peg-tolerance sensitivity

The table uses the same May 2022 hourly source and 24 consecutive clock-hour recovery rule at each tolerance. A recovery time measures the delay from the first breach to the **start** of the qualifying 24-hour streak.

| Asset | ±0.5% band | ±1% band | ±5% band |
| --- | --- | --- | --- |
| UST | Breached; no recovery | Breached; no recovery | Breached; no recovery |
| USDT | Recovered; streak began 16 h after breach | No breach | No breach |
| USDC | Breached; no recovery | Breached; no recovery | No breach |

The earlier 1% USDC result counted 24 in-band **observations** across missing hours and reported recovery beginning six hours after the first breach. With the clock-hour rule, that streak is interrupted, so the corrected result is **not recovered within the observed May window**. This does not establish that USDC remained off peg through May 31: missing data prevent confirmation of a continuous recovery streak. USDC's first 1% breach was an upside price move; the classification uses absolute deviation rather than downside loss alone. See `data/processed/threshold_comparison.csv` for breach timestamps and the exact outcomes.

## Folder map

```text
.
├── src/                  analysis and API modules
├── scripts/              command-line pipeline runner
├── tests/                automated calculation tests
├── data/raw/             cached API responses
├── data/processed/       clean data and summaries
├── evidence/             figures
├── API_SETUP.md
├── DATA_DICTIONARY.md
└── requirements.txt
```

## Important limitations

Coin Metrics' Community ReferenceRate catalog currently exposes only recent price history, not May 2022. The pipeline therefore uses DefiLlama for historical price and Coin Metrics for USDT and USDC supply. UST supply is partial and provisional because native-chain coverage begins during the crisis and bridged-chain rows appear earlier. The current comparable supply analysis is therefore limited to USDT and USDC. The report states this limitation and the revision plan explicitly.

The opposing USDT and USDC supply movements are consistent with possible reallocation, but aggregate supply series cannot trace where the same investors' money went or establish their motives.


