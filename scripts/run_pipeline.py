#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Stablecoin Stress Monitor data and evidence files.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--refresh", action="store_true", help="Download fresh copies from the public APIs.")
    mode.add_argument("--offline", action="store_true", help="Use only included raw JSON caches.")
    args = parser.parse_args()
    paths = run_pipeline(refresh=args.refresh, offline=args.offline)
    print("Pipeline completed. Outputs:")
    for label, path in paths.items():
        print(f"  {label}: {path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()

