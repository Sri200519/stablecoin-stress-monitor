# Data Dictionary

## prices_hourly_may2022.csv

| Field | Meaning |
| --- | --- |
| `timestamp` | UTC observation hour |
| `asset` | UST, USDT, or USDC |
| `price_usd` | Aggregated U.S. dollar price returned by DefiLlama |
| `source_id` | DefiLlama CoinGecko-style source identifier |
| `source_confidence` | Confidence value supplied by DefiLlama when available |
| `deviation_usd` | Price minus the one-dollar target |
| `deviation_pct` | `100 × (price - 1)` |
| `absolute_deviation_pct` | Absolute percentage deviation from one dollar |
| `downside_depeg_pct` | Percentage shortfall below one dollar; zero for premiums |
| `phase` | Pre-crisis, Crisis, or Post-crisis |

## supply_daily_may2022.csv

| Field | Meaning |
| --- | --- |
| `date` | UTC calendar date |
| `asset` | UST, USDT, or USDC |
| `supply_tokens` | Reported circulating tokens or provisional chain-balance aggregate |
| `coverage_status` | `complete` for comparable Coin Metrics series or `partial_provisional` for UST |

## Summary files

- `asset_summary_1pct.csv` contains minimum price, maximum depeg, time inside peg bands, and the sustained one-percent recovery result.
- `phase_summary.csv` contains observation counts, price ranges, and absolute deviations for each project phase.
- `supply_summary.csv` computes May 1-31 changes only for complete supply series. UST change fields are intentionally blank.
- `data_quality_summary.csv` compares observed hourly price rows with the expected 744 hours in May.
- `metrics_and_provenance.json` records definitions, endpoint parameters, source notes, and the same summary metrics in machine-readable form.
