# API Setup and Data Provenance

The Milestone 2 pipeline runs with public endpoints and does not require an API key.

## Price history

Provider: DefiLlama Coins API  
Endpoint: `https://coins.llama.fi/chart/{coins}`  
Identifiers: `coingecko:terrausd`, `coingecko:tether`, `coingecko:usd-coin`  
Parameters: seven non-overlapping chunks of at most 120 hours, beginning at Unix timestamp `1651363200`, with `period=1h` and `searchWidth=4h`  
Authentication: none

## USDT and USDC circulating supply

Provider: Coin Metrics Community API v4  
Endpoint: `https://community-api.coinmetrics.io/v4/timeseries/asset-metrics`  
Assets: `usdt,usdc`  
Metric: `SplyCur`  
Frequency: `1d`  
Dates: `2022-05-01` through `2022-05-31`  
Authentication: none for the Community API

## Provisional UST supply

Provider: DefiLlama Stablecoins API  
Endpoint: `https://stablecoins.llama.fi/stablecoin/3`  
Authentication: none


## Refresh and offline modes

From the project folder:

```bash
python scripts/run_pipeline.py --refresh
python scripts/run_pipeline.py --offline
```

`--refresh` calls the public endpoints and overwrites the raw caches. `--offline` performs the same transformations using the included cache files, which makes the submitted evidence reproducible if an API is temporarily unavailable.
