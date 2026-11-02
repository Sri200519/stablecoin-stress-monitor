"""Stablecoin Stress Monitor: interactive dashboard.

Run from the project root:
    streamlit run app.py

The dashboard reads only the processed CSV files in data/processed/ and reuses the
calculation functions in src/analysis.py. It does not call any API.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analysis import build_asset_summary, build_phase_summary, build_supply_summary
from src.config import ASSET_COLORS, ASSET_ORDER, PHASES, PROCESSED_DIR

THRESHOLDS = [0.5, 1.0, 5.0]
CRISIS_START = pd.Timestamp("2022-05-07", tz="UTC")
CRISIS_END = pd.Timestamp("2022-05-16", tz="UTC")
STUDY_START = pd.Timestamp("2022-05-01 00:00", tz="UTC")
STUDY_END = pd.Timestamp("2022-05-31 23:00", tz="UTC")
RESERVE_COINS = ["USDT", "USDC"]

st.set_page_config(page_title="Stablecoin Stress Monitor", page_icon="🪙", layout="wide")


# ---------------------------------------------------------------- data loading
@st.cache_data
def load_prices() -> pd.DataFrame:
    prices = pd.read_csv(PROCESSED_DIR / "prices_hourly_may2022.csv")
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    return prices.sort_values(["asset", "timestamp"]).reset_index(drop=True)


@st.cache_data
def load_supply() -> pd.DataFrame:
    supply = pd.read_csv(PROCESSED_DIR / "supply_daily_may2022.csv")
    supply["date"] = pd.to_datetime(supply["date"])
    return supply.sort_values(["asset", "date"]).reset_index(drop=True)


@st.cache_data
def load_quality() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "data_quality_summary.csv")


@st.cache_data
def summaries_by_threshold(prices: pd.DataFrame) -> dict[float, pd.DataFrame]:
    return {t: build_asset_summary(prices, threshold_pct=t) for t in THRESHOLDS}


def with_gaps(group: pd.DataFrame, max_gap_hours: int = 3) -> pd.DataFrame:
    """Insert a blank row inside every gap longer than max_gap_hours.

    Plotly then breaks the line there, so long stretches of missing data are visible
    instead of being bridged by a straight line. Prices are never filled or estimated.
    """
    group = group.sort_values("timestamp")
    long_gap = group["timestamp"].diff() > pd.Timedelta(hours=max_gap_hours)
    breaks = pd.DataFrame({"timestamp": group.loc[long_gap, "timestamp"] - pd.Timedelta(hours=1)})
    return pd.concat([group, breaks]).sort_values("timestamp").reset_index(drop=True)


def missing_gaps(group: pd.DataFrame) -> pd.DataFrame:
    """List each run of consecutive missing hours for one asset."""
    full_range = pd.date_range(STUDY_START, STUDY_END, freq="h")
    observed = set(group["timestamp"])
    missing = [ts for ts in full_range if ts not in observed]
    gaps, start, prev = [], None, None
    for ts in missing:
        if start is None:
            start = prev = ts
        elif ts - prev == pd.Timedelta(hours=1):
            prev = ts
        else:
            gaps.append((start, prev))
            start = prev = ts
    if start is not None:
        gaps.append((start, prev))
    return pd.DataFrame(
        [{"Gap starts (UTC)": s, "Gap ends (UTC)": e,
          "Missing hours": int((e - s) / pd.Timedelta(hours=1)) + 1} for s, e in gaps]
    )


def shade_crisis(fig: go.Figure) -> None:
    fig.add_vrect(x0=CRISIS_START, x1=CRISIS_END, fillcolor="#F5A623", opacity=0.10,
                  line_width=0, annotation_text="Crisis window (May 7–15)",
                  annotation_position="top left")


def fmt_time(value) -> str:
    return "—" if pd.isna(value) else pd.Timestamp(value).strftime("%b %d, %H:%M")


def fmt_hours(value) -> str:
    return "—" if pd.isna(value) else f"{value:.0f} h"


prices = load_prices()
supply = load_supply()
quality = load_quality()
all_summaries = summaries_by_threshold(prices)

# --------------------------------------------------------------------- sidebar
st.sidebar.header("Settings")
threshold = st.sidebar.radio(
    "Depeg threshold",
    THRESHOLDS,
    index=1,
    format_func=lambda t: f"{t:g}%  (outside \\${1 - t / 100:.3f} – \\${1 + t / 100:.3f})",
    help="A coin breaches its peg when its price moves farther than this from $1 in either direction.",
)
selected = st.sidebar.multiselect("Stablecoins", ASSET_ORDER, default=ASSET_ORDER)
st.sidebar.caption(
    "Recovery = the first hour of 24 consecutive hourly observations back inside the band "
    "after the first breach. Missing hours are never filled in."
)
st.sidebar.caption("Data: DefiLlama hourly prices; Coin Metrics daily supply. All times UTC.")

if not selected:
    st.warning("Choose at least one stablecoin in the sidebar.")
    st.stop()

summary = all_summaries[threshold]
view = prices[prices["asset"].isin(selected)]

# ---------------------------------------------------------------------- header
st.title("Stablecoin Stress Monitor")
st.markdown(
    "How **UST** (algorithmic), **USDT**, and **USDC** (reserve-backed) held their $1 peg "
    "during the May 2022 crypto collapse."
)

cols = st.columns(len(selected))
for col, asset in zip(cols, selected):
    row = summary[summary["asset"] == asset].iloc[0]
    if row["status"] == "Recovered":
        status = f"Recovered in {row['recovery_hours']:.0f} h"
    elif row["status"].startswith("No breach"):
        status = "Never breached"
    else:
        status = "Not recovered"
    col.metric(label=f"{asset} · lowest price", value=f"${row['min_price_usd']:.4f}")
    col.caption(f"Largest move from \\$1: {row['max_abs_deviation_pct']:.2f}%  \nAt {threshold:g}%: **{status}**")

tab_price, tab_dev, tab_peg, tab_supply, tab_data = st.tabs(
    ["Prices", "Deviation from $1", "Peg loss & recovery", "Circulating supply", "Data coverage"]
)

# ---------------------------------------------------------------------- prices
with tab_price:
    zoom = st.toggle(
        "Zoom in near $1",
        value="UST" not in selected,
        help="UST's collapse dwarfs the other coins; zoom in to see USDT and USDC.",
    )
    fig = go.Figure()
    shade_crisis(fig)
    fig.add_hrect(y0=1 - threshold / 100, y1=1 + threshold / 100, fillcolor="#2E8B57",
                  opacity=0.08, line_width=0)
    fig.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="$1 peg")
    for asset in selected:
        g = with_gaps(view[view["asset"] == asset])
        fig.add_trace(go.Scatter(
            x=g["timestamp"], y=g["price_usd"], name=asset, mode="lines",
            line=dict(color=ASSET_COLORS[asset], width=2), connectgaps=False,
            hovertemplate="%{x|%b %d %H:%M} UTC<br>$%{y:.4f}<extra>" + asset + "</extra>",
        ))
    if zoom:
        pad = max(threshold / 100 * 1.6, 0.03)
        fig.update_yaxes(range=[1 - pad, 1 + pad])
    fig.update_layout(height=480, yaxis_title="Price (USD)", hovermode="x unified",
                      legend=dict(orientation="h", y=1.08), margin=dict(t=40))
    st.plotly_chart(fig, width="stretch")
    st.caption(f"Shaded green band = ±{threshold:g}% around $1. Breaks in a line are gaps of more than 3 hours with no data.")

# ------------------------------------------------------------------- deviation
with tab_dev:
    measure = st.radio(
        "Measure",
        ["Signed deviation (above or below $1)", "Absolute deviation"],
        horizontal=True,
    )
    col_name = "deviation_pct" if measure.startswith("Signed") else "absolute_deviation_pct"
    fig = go.Figure()
    shade_crisis(fig)
    fig.add_hline(y=threshold, line_dash="dot", line_color="crimson",
                  annotation_text=f"+{threshold:g}%")
    if col_name == "deviation_pct":
        fig.add_hline(y=-threshold, line_dash="dot", line_color="crimson",
                      annotation_text=f"−{threshold:g}%")
    fig.add_hline(y=0, line_color="gray", line_width=1)
    for asset in selected:
        g = with_gaps(view[view["asset"] == asset])
        fig.add_trace(go.Scatter(
            x=g["timestamp"], y=g[col_name], name=asset, mode="lines",
            line=dict(color=ASSET_COLORS[asset], width=2), connectgaps=False,
            hovertemplate="%{x|%b %d %H:%M} UTC<br>%{y:.3f}%<extra>" + asset + "</extra>",
        ))
    log_scale = st.toggle(
        "Log scale", value=False, disabled=col_name == "deviation_pct",
        help="Available for absolute deviation only. Helps compare UST with the reserve-backed coins.",
    )
    if log_scale and col_name == "absolute_deviation_pct":
        fig.update_yaxes(type="log")
    fig.update_layout(height=480, yaxis_title="Deviation from $1 (%)", hovermode="x unified",
                      legend=dict(orientation="h", y=1.08), margin=dict(t=40))
    st.plotly_chart(fig, width="stretch")

    st.subheader("Deviation by crisis window")
    phases = build_phase_summary(prices)
    phases = phases[phases["asset"].isin(selected)]
    st.dataframe(
        phases.rename(columns={
            "asset": "Coin", "phase": "Window", "observations": "Hours observed",
            "average_price_usd": "Avg price ($)", "min_price_usd": "Min price ($)",
            "max_price_usd": "Max price ($)", "mean_abs_deviation_pct": "Avg |deviation| (%)",
            "max_abs_deviation_pct": "Max |deviation| (%)",
        }),
        hide_index=True, width="stretch",
        column_config={
            c: st.column_config.NumberColumn(format="%.4f")
            for c in ["Avg price ($)", "Min price ($)", "Max price ($)"]
        } | {
            c: st.column_config.NumberColumn(format="%.3f")
            for c in ["Avg |deviation| (%)", "Max |deviation| (%)"]
        },
    )
    windows = ", ".join(f"{name} ({start[5:10]} to {end[5:10]})" for name, start, end in PHASES)
    st.caption(f"Windows: {windows}.")

# ------------------------------------------------------------ peg loss/recovery
with tab_peg:
    st.subheader(f"When each coin lost and recovered its peg at the {threshold:g}% threshold")
    table = summary[summary["asset"].isin(selected)]
    st.dataframe(
        pd.DataFrame({
            "Coin": table["asset"],
            "Lowest price ($)": table["min_price_usd"].map(lambda v: f"{v:.4f}"),
            "Largest move from $1": table["max_abs_deviation_pct"].map(lambda v: f"{v:.2f}%"),
            "Largest move at (UTC)": table["max_abs_deviation_time"].map(fmt_time),
            "Lost peg (UTC)": table["breach_time"].map(fmt_time),
            "Recovered (UTC)": table["recovery_time"].map(fmt_time),
            "Time to recover": table["recovery_hours"].map(fmt_hours),
            "Status": table["status"].map(
                lambda v: "Recovered" if v == "Recovered"
                else "Never breached" if v.startswith("No breach") else "Not recovered"),
        }),
        hide_index=True, width="stretch",
    )

    st.subheader("How the threshold changes the result")
    rows = []
    for t in THRESHOLDS:
        for _, r in all_summaries[t][all_summaries[t]["asset"].isin(selected)].iterrows():
            if r["status"] == "Recovered":
                outcome = f"Recovered after {r['recovery_hours']:.0f} h"
            elif r["status"].startswith("No breach"):
                outcome = "Never breached"
            else:
                outcome = "Not recovered by May 31"
            rows.append({"Threshold": f"{t:g}%", "Coin": r["asset"], "Outcome": outcome})
    pivot = pd.DataFrame(rows).pivot(index="Coin", columns="Threshold", values="Outcome")
    pivot = pivot.reindex([a for a in ASSET_ORDER if a in selected])[[f"{t:g}%" for t in THRESHOLDS]]
    st.dataframe(pivot, width="stretch")
    st.caption(
        "Lost peg = first hour the price moved beyond the threshold in either direction "
        "(so a price spike above $1 also counts). Recovered = first hour of 24 consecutive "
        "observations back inside the band. Because some hours are missing, 24 observations "
        "can span more than 24 clock hours."
    )

# ---------------------------------------------------------------------- supply
with tab_supply:
    reserve = supply[supply["asset"].isin(RESERVE_COINS) & supply["asset"].isin(selected)]
    if reserve.empty:
        st.info("Select USDT or USDC in the sidebar to see circulating supply.")
    else:
        mode = st.radio("Show supply as", ["Index (May 1 = 100)", "Billions of tokens"],
                        horizontal=True)
        fig = go.Figure()
        fig.add_vrect(x0="2022-05-07", x1="2022-05-16", fillcolor="#F5A623", opacity=0.10,
                      line_width=0)
        for asset in [a for a in RESERVE_COINS if a in selected]:
            g = reserve[reserve["asset"] == asset]
            if mode.startswith("Index"):
                y = g["supply_tokens"] / g["supply_tokens"].iloc[0] * 100
                hover = "%{x|%b %d}<br>%{y:.1f}<extra>" + asset + "</extra>"
            else:
                y = g["supply_tokens"] / 1e9
                hover = "%{x|%b %d}<br>%{y:.2f}B<extra>" + asset + "</extra>"
            fig.add_trace(go.Scatter(x=g["date"], y=y, name=asset, mode="lines+markers",
                                     line=dict(color=ASSET_COLORS[asset], width=2),
                                     hovertemplate=hover))
        if mode.startswith("Index"):
            fig.add_hline(y=100, line_dash="dash", line_color="gray")
        fig.update_layout(height=440, yaxis_title=mode, hovermode="x unified",
                          legend=dict(orientation="h", y=1.08), margin=dict(t=40))
        st.plotly_chart(fig, width="stretch")

        supply_summary = build_supply_summary(reserve).set_index("asset").reindex(
            [a for a in RESERVE_COINS if a in selected]).reset_index()
        cols = st.columns(len(supply_summary))
        for col, (_, r) in zip(cols, supply_summary.iterrows()):
            col.metric(f"{r['asset']} supply, May 1 → May 31",
                       f"{r['last_supply_tokens'] / 1e9:.2f}B",
                       f"{r['change_pct']:+.1f}% ({r['change_tokens'] / 1e9:+.2f}B)",
                       delta_color="off")
    st.caption(
        "Supply changes show net issuance and redemption; they do not tell us why holders acted. "
        "UST supply is excluded because its series is partial and provisional."
    )

# ----------------------------------------------------------------- data coverage
with tab_data:
    st.subheader("Hourly price coverage (744 expected hours in May)")
    q = quality[quality["asset"].isin(selected)].set_index("asset").reindex(
        [a for a in ASSET_ORDER if a in selected]).reset_index()
    cols = st.columns(len(q))
    for col, (_, r) in zip(cols, q.iterrows()):
        col.metric(r["asset"], f"{r['coverage_pct']:.1f}%")
        col.caption(f"{r['observed_hours']} observed · {r['expected_hours'] - r['observed_hours']} missing")
        col.progress(min(r["coverage_pct"] / 100, 1.0))

    st.subheader("Missing hours by day")
    daily = []
    for asset in selected:
        g = prices[prices["asset"] == asset]
        counts = g.groupby(g["timestamp"].dt.date).size()
        for day in pd.date_range("2022-05-01", "2022-05-31").date:
            daily.append({"day": day, "asset": asset, "missing": 24 - int(counts.get(day, 0))})
    daily = pd.DataFrame(daily)
    fig = go.Figure()
    for asset in selected:
        d = daily[daily["asset"] == asset]
        fig.add_trace(go.Bar(x=d["day"], y=d["missing"], name=asset,
                             marker_color=ASSET_COLORS[asset]))
    fig.update_layout(barmode="group", height=360, yaxis_title="Missing hours",
                      legend=dict(orientation="h", y=1.1), margin=dict(t=40))
    st.plotly_chart(fig, width="stretch")

    st.subheader("Longest gaps")
    gap_tables = []
    for asset in selected:
        gaps = missing_gaps(prices[prices["asset"] == asset])
        if not gaps.empty:
            gaps.insert(0, "Coin", asset)
            gap_tables.append(gaps)
    if gap_tables:
        gaps = pd.concat(gap_tables).sort_values("Missing hours", ascending=False).head(10)
        gaps["Gap starts (UTC)"] = gaps["Gap starts (UTC)"].map(fmt_time)
        gaps["Gap ends (UTC)"] = gaps["Gap ends (UTC)"].map(fmt_time)
        st.dataframe(gaps, hide_index=True, width="stretch")
    st.caption(
        "Missing hours are left blank rather than estimated, so a short depeg during a gap "
        "would not appear in the results."
    )
