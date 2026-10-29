# Stablecoin Stress Monitor Milestone 2

This folder contains a reproducible data pipeline, processed evidence, static figures, and the Milestone 2 progress report for the May 2022 comparison of UST, USDT, and USDC.

## What is complete

- Hourly price collection for May 1-31, 2022 from a public no-key endpoint
- Daily USDT and USDC circulating supply collection from Coin Metrics
- A documented partial UST supply series that is kept separate from comparable full-month results
- Peg-deviation, downside-depeg, crisis-phase, and sustained-recovery calculations
- Static figures and depeg threshold analyses for 0.5%, 1%, and 5%
- Offline rebuild support from submitted raw API caches
- Automated tests for phase boundaries, deviation calculations, and recovery logic

## Quick start

Python 3.11 or later is recommended.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/run_pipeline.py --offline
```

To download fresh source data instead of using the included caches:

```bash
python scripts/run_pipeline.py --refresh
```

No API key is needed. See `API_SETUP.md` for endpoints, parameters, limitations, and the optional Coin Metrics key setting.

## Key outputs

| Path | Purpose |
| --- | --- |
| `Milestone_2_Progress_Report.docx` and `.pdf` | Submission-ready 2-4 page report |
| `data/raw/` | Submitted API response caches |
| `data/processed/prices_hourly_may2022.csv` | Clean price and deviation data |
| `data/processed/asset_summary_1pct.csv` | Main one-percent threshold results |
| `data/processed/phase_summary.csv` | Pre-crisis, crisis, and post-crisis statistics |
| `data/processed/supply_summary.csv` | Supply change calculations and coverage labels |
| `data/processed/data_quality_summary.csv` | Observed versus expected hourly coverage |
| `evidence/figures/` | Price, supply, and workflow figures |
| `tests/test_analysis.py` | Tests for the core calculations |

## Analytical definitions

Price deviation is `100 × (price - 1.00)`. Absolute deviation uses its absolute value. Downside depeg is the positive shortfall below one dollar. Recovery begins at the first hour of 24 consecutive hourly observations inside the selected band after the first breach. An asset that never breaches the threshold is labeled separately from one that breaches and later recovers.

The study phases match Milestone 1: pre-crisis is May 1-6, crisis is May 7-15, and post-crisis is May 16-31. All timestamps are UTC.

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
├── MILESTONE_2_CHECKLIST.md
└── requirements.txt
```

## Important limitation

Coin Metrics' Community ReferenceRate catalog currently exposes only recent price history, not May 2022. The pipeline therefore uses DefiLlama for historical price and Coin Metrics for USDT and USDC supply. UST supply is partial and provisional because native-chain coverage begins during the crisis and bridged-chain rows appear earlier. The current comparable supply analysis is therefore limited to USDT and USDC. The report states this limitation and the revision plan explicitly.


