from __future__ import annotations

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd

from .config import ASSET_COLORS


def plot_price_comparison(prices: pd.DataFrame, output_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(12, 6), dpi=200)

    # Crisis shading (May 7 to May 16 UTC)
    ax.axvspan(
        pd.Timestamp("2022-05-07 00:00:00+00:00"),
        pd.Timestamp("2022-05-16 00:00:00+00:00"),
        color="#FFF3DC",
        alpha=0.6,
        zorder=1,
    )

    # Grid and peg line
    ax.grid(True, color="#E2E8F0", linestyle="-", linewidth=0.8, alpha=0.8, zorder=0)
    ax.axhline(1.0, color="black", linestyle="--", linewidth=1.2, label="$1 peg", zorder=2)

    for asset in ["UST", "USDT", "USDC"]:
        subset = prices[prices["asset"] == asset].sort_values("timestamp")
        if not subset.empty:
            ax.plot(
                subset["timestamp"],
                subset["price_usd"],
                color=ASSET_COLORS.get(asset, "#000000"),
                linewidth=2.0,
                label=asset,
                zorder=3,
            )

    ax.set_title("Stablecoin prices during the May 2022 crisis", fontsize=15, pad=12)
    ax.set_xlabel("Date in UTC", fontsize=11, labelpad=8)
    ax.set_ylabel("Price in U.S. dollars", fontsize=11, labelpad=8)
    ax.set_ylim(0.0, 1.08)
    ax.set_xlim(pd.Timestamp("2022-04-30 18:00:00+00:00"), pd.Timestamp("2022-06-01 06:00:00+00:00"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=4))
    ax.tick_params(axis="both", labelsize=10)
    ax.legend(loc="lower left", frameon=False, ncol=4, fontsize=11)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def plot_reserve_zoom(prices: pd.DataFrame, output_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(12, 6), dpi=200)

    # Crisis shading
    ax.axvspan(
        pd.Timestamp("2022-05-07 00:00:00+00:00"),
        pd.Timestamp("2022-05-16 00:00:00+00:00"),
        color="#FFF3DC",
        alpha=0.6,
        zorder=1,
    )

    # 1% band shading
    ax.axhspan(0.99, 1.01, color="#198754", alpha=0.08, label="1% band", zorder=1)

    # Grid and peg line
    ax.grid(True, color="#E2E8F0", linestyle="-", linewidth=0.8, alpha=0.8, zorder=0)
    ax.axhline(1.0, color="black", linestyle="--", linewidth=1.2, zorder=2)

    for asset in ["USDT", "USDC"]:
        subset = prices[prices["asset"] == asset].sort_values("timestamp")
        if not subset.empty:
            ax.plot(
                subset["timestamp"],
                subset["price_usd"],
                color=ASSET_COLORS.get(asset, "#000000"),
                linewidth=2.0,
                label=asset,
                zorder=3,
            )

    ax.set_title("Reserve-backed stablecoins near the $1 peg", fontsize=15, pad=12)
    ax.set_xlabel("Date in UTC", fontsize=11, labelpad=8)
    ax.set_ylabel("Price in U.S. dollars", fontsize=11, labelpad=8)
    ax.set_ylim(0.94, 1.035)
    ax.set_xlim(pd.Timestamp("2022-04-30 18:00:00+00:00"), pd.Timestamp("2022-06-01 06:00:00+00:00"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=4))
    ax.tick_params(axis="both", labelsize=10)
    ax.legend(loc="lower right", frameon=False, fontsize=11)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def plot_supply_index(supply: pd.DataFrame, output_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(12, 6), dpi=200)

    # Crisis shading
    ax.axvspan(
        pd.Timestamp("2022-05-07"),
        pd.Timestamp("2022-05-16"),
        color="#FFF3DC",
        alpha=0.6,
        zorder=1,
    )

    # Grid and 100 baseline
    ax.grid(True, color="#E2E8F0", linestyle="-", linewidth=0.8, alpha=0.8, zorder=0)
    ax.axhline(100.0, color="black", linestyle="--", linewidth=1.2, zorder=2)

    for asset in ["USDC", "USDT"]:
        subset = supply[(supply["asset"] == asset) & (supply["coverage_status"] == "complete")].sort_values("date")
        if not subset.empty:
            base = subset["supply_tokens"].iloc[0]
            indexed = (subset["supply_tokens"] / base) * 100.0
            dates = pd.to_datetime(subset["date"])
            ax.plot(
                dates,
                indexed,
                color=ASSET_COLORS.get(asset, "#000000"),
                linewidth=2.2,
                label=asset,
                zorder=3,
            )

    ax.set_title("USDT and USDC circulating supply indexed to May 1", fontsize=15, pad=12)
    ax.set_xlabel("Date", fontsize=11, labelpad=8)
    ax.set_ylabel("Index where May 1 equals 100", fontsize=11, labelpad=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=4))
    ax.tick_params(axis="both", labelsize=10)
    ax.legend(loc="upper left", frameon=False, fontsize=11)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def plot_workflow_diagram(output_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(12, 3.5), dpi=200)
    ax.axis("off")

    steps = [
        ("Public APIs\nDefiLlama and\nCoin Metrics"),
        ("Acquisition\nRetries, cache,\nsource metadata"),
        ("Normalization\nUTC timestamps and\ncommon asset labels"),
        ("Analysis\nDeviation, phases,\nrecovery, and supply"),
        ("Outputs\nCSV data, summaries,\nand static figures"),
    ]

    n_steps = len(steps)
    box_width = 0.16
    box_height = 0.55
    y_pos = 0.18
    gap = (1.0 - 0.04 - (n_steps * box_width)) / (n_steps - 1)
    start_x = 0.02

    for i, text in enumerate(steps):
        x = start_x + i * (box_width + gap)
        rect = mpatches.FancyBboxPatch(
            (x, y_pos),
            box_width,
            box_height,
            boxstyle="round,pad=0.015,rounding_size=0.03",
            edgecolor="#0B57D0",
            facecolor="#F0F4F9",
            linewidth=1.5,
            transform=ax.transAxes,
            clip_on=False,
        )
        ax.add_patch(rect)
        ax.text(
            x + box_width / 2,
            y_pos + box_height / 2,
            text,
            ha="center",
            va="center",
            fontsize=9.5,
            color="#1F2937",
            linespacing=1.3,
            transform=ax.transAxes,
        )

        if i < n_steps - 1:
            arrow_start_x = x + box_width
            arrow_end_x = arrow_start_x + gap
            arrow_y = y_pos + box_height / 2
            ax.annotate(
                "",
                xy=(arrow_end_x, arrow_y),
                xytext=(arrow_start_x, arrow_y),
                xycoords="axes fraction",
                textcoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="#5F6368", lw=1.5, mutation_scale=12),
            )

    ax.set_title("Stablecoin Stress Monitor analytical workflow", fontsize=14, pad=18, y=0.92)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def export_static_figures(prices: pd.DataFrame, supply: pd.DataFrame, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = [
        plot_price_comparison(prices, output_dir / "01_price_comparison.png"),
        plot_reserve_zoom(prices, output_dir / "02_reserve_coin_zoom.png"),
        plot_supply_index(supply, output_dir / "03_supply_index.png"),
        plot_workflow_diagram(output_dir / "04_workflow_diagram.png"),
    ]
    return paths
