"""Report figures for Milestone 3, Sections 4-5 (Figures 1, 3, and 4).

Built only from the repo's processed CSVs, using the repo's coin colors.
Run from the project root:
    python scripts/make_report_figures.py . evidence/figures
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch

repo, out = Path(sys.argv[1]), Path(sys.argv[2])
COL = {"UST": "#C2413B", "USDT": "#198754", "USDC": "#1F6FEB"}
INK, MUTED, GRID = "#1F2328", "#57606A", "#E6E8EB"
CRISIS = (pd.Timestamp("2022-05-07", tz="UTC"), pd.Timestamp("2022-05-16", tz="UTC"))

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"], "font.size": 8, "axes.edgecolor": "#8C959F",
    "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
})

prices = pd.read_csv(repo / "data/processed/prices_hourly_may2022.csv")
prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
supply = pd.read_csv(repo / "data/processed/supply_daily_may2022.csv", parse_dates=["date"])


def with_breaks(g, max_gap_h=3):
    """Blank row inside gaps > max_gap_h so lines break; prices are never filled."""
    g = g.sort_values("timestamp")
    gap = g["timestamp"].diff() > pd.Timedelta(hours=max_gap_h)
    br = pd.DataFrame({"timestamp": g.loc[gap, "timestamp"] - pd.Timedelta(hours=1)})
    return pd.concat([g, br]).sort_values("timestamp")


def style_time_axis(ax):
    ax.set_xticks([pd.Timestamp(f"2022-05-{d:02d}", tz="UTC") for d in (1, 8, 15, 22, 29)])
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %-d"))
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def crisis(ax, label=True):
    ax.axvspan(*CRISIS, color="#F5A623", alpha=0.10, lw=0, zorder=0)
    if label:
        ax.text(CRISIS[0] + pd.Timedelta(hours=6), 0.985, "Crisis window",
                transform=ax.get_xaxis_transform(), va="top", fontsize=7, color=MUTED)


# ---------------------------------------------------------------- Figure 3: prices
fig, (a, b) = plt.subplots(1, 2, figsize=(6.5, 2.45), dpi=300, gridspec_kw={"wspace": 0.28})
crisis(a)
a.axhline(1, color=MUTED, ls="--", lw=0.7)
for coin in ["UST", "USDT", "USDC"]:
    g = with_breaks(prices[prices.asset == coin])
    a.plot(g.timestamp, g.price_usd, color=COL[coin], lw=1.1 if coin == "UST" else 1.0)
a.text(pd.Timestamp("2022-05-20", tz="UTC"), 0.14, "UST", color=INK, fontsize=8, fontweight="bold")
a.text(pd.Timestamp("2022-05-20", tz="UTC"), 1.03, "USDT and USDC", color=INK, fontsize=8, fontweight="bold")
a.set_ylim(-0.02, 1.12)
a.set_ylabel("Price (USD)")
a.set_title("(a) All three coins", loc="left", fontsize=8.5, color=INK)
style_time_axis(a)

crisis(b)
b.axhspan(0.99, 1.01, color="#2E8B57", alpha=0.08, lw=0)
b.axhline(1, color=MUTED, ls="--", lw=0.7)
for coin in ["USDT", "USDC"]:
    g = with_breaks(prices[prices.asset == coin])
    b.plot(g.timestamp, g.price_usd, color=COL[coin], lw=0.9)
b.annotate("USDC $1.026\n(May 12, 07:00)", xy=(pd.Timestamp("2022-05-12 07:00", tz="UTC"), 1.026),
           xytext=(pd.Timestamp("2022-05-17", tz="UTC"), 1.024), fontsize=7, color=INK,
           arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6), va="center")
b.annotate("USDT $0.9926\n(May 12, 11:00)", xy=(pd.Timestamp("2022-05-12 11:00", tz="UTC"), 0.9926),
           xytext=(pd.Timestamp("2022-05-17", tz="UTC"), 0.983), fontsize=7, color=INK,
           arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6), va="center")
b.text(pd.Timestamp("2022-05-01 06:00", tz="UTC"), 1.0115, "±1% band", fontsize=7, color=MUTED)
b.set_ylim(0.975, 1.032)
b.set_title("(b) Reserve-backed coins, zoomed", loc="left", fontsize=8.5, color=INK)
style_time_axis(b)
# legend for (b): identity also carried by the labels in the annotations
b.plot([], [], color=COL["USDT"], label="USDT")
b.plot([], [], color=COL["USDC"], label="USDC")
b.legend(loc="lower left", frameon=False, fontsize=7, ncol=1, handlelength=1.4, borderaxespad=0.2)
fig.savefig(out / "fig3_prices.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

# ---------------------------------------------------------------- Figure 4: supply
fig, ax = plt.subplots(figsize=(5.0, 2.05), dpi=300)
crisis(ax)
ax.axhline(100, color=MUTED, ls="--", lw=0.7)
for coin in ["USDT", "USDC"]:
    g = supply[supply.asset == coin].sort_values("date")
    idx = g.supply_tokens / g.supply_tokens.iloc[0] * 100
    x = pd.to_datetime(g.date).dt.tz_localize("UTC")
    ax.plot(x, idx, color=COL[coin], lw=1.4, marker="o", ms=2.2)
    chg = idx.iloc[-1] - 100
    ax.text(x.iloc[-1] + pd.Timedelta(hours=14), idx.iloc[-1], f"{coin} {chg:+.1f}%",
            va="center", fontsize=8, color=INK, fontweight="bold")
ax.set_ylabel("Index (May 1 = 100)")
ax.set_xlim(right=pd.Timestamp("2022-06-04", tz="UTC"))
style_time_axis(ax)
fig.savefig(out / "fig4_supply.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

# ---------------------------------------------------------------- Figure 1: workflow
steps = [
    ("Public APIs", "DefiLlama prices,\nCoin Metrics\nsupply"),
    ("Acquisition", "7 chunked\nrequests, retries,\nraw JSON cache"),
    ("Normalization", "UTC hours,\ncommon labels,\nno gap filling"),
    ("Analysis", "Deviation, phases,\nbreach, recovery,\nsupply"),
    ("Testing", "6 automated\npytest checks"),
    ("Outputs", "CSV summaries,\nfigures,\nStreamlit app"),
]
fig, ax = plt.subplots(figsize=(6.5, 1.2), dpi=300)
ax.set_xlim(0, len(steps)); ax.set_ylim(0, 1); ax.axis("off")
w, gap = 0.88, 0.12
for i, (title, body) in enumerate(steps):
    x0 = i + gap / 2
    ax.add_patch(FancyBboxPatch((x0, 0.06), w, 0.88, boxstyle="round,pad=0,rounding_size=0.06",
                                fc="#EEF3FB", ec="#1F6FEB", lw=0.9))
    ax.text(x0 + w / 2, 0.78, title, ha="center", va="center", fontsize=7.5, fontweight="bold", color=INK)
    ax.text(x0 + w / 2, 0.40, body, ha="center", va="center", fontsize=6.2, color=INK, linespacing=1.25)
    if i < len(steps) - 1:
        ax.annotate("", xy=(i + 1 + gap / 2 - 0.005, 0.5), xytext=(x0 + w + 0.005, 0.5),
                    arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.8, mutation_scale=7))
fig.savefig(out / "fig1_workflow.png", bbox_inches="tight", facecolor="white", pad_inches=0.02)
plt.close(fig)
print("ok")
