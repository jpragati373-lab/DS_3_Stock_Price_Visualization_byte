"""Download daily stock-price data from Yahoo Finance using yfinance."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import yfinance as yf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_TICKER = "TCS.NS"
DEFAULT_START_DATE = date(2015, 1, 1)
PRICE_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


def parse_date(value: str) -> date:
    """Parse a command-line date in YYYY-MM-DD format."""
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'; use YYYY-MM-DD."
        ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch daily historical stock data from Yahoo Finance and save it "
            "as a CSV in the project's data/ directory."
        )
    )
    parser.add_argument(
        "--ticker",
        default=DEFAULT_TICKER,
        help=f"Yahoo Finance ticker symbol (default: {DEFAULT_TICKER}).",
    )
    parser.add_argument(
        "--start",
        type=parse_date,
        default=DEFAULT_START_DATE,
        help=(
            "Inclusive start date in YYYY-MM-DD format "
            f"(default: {DEFAULT_START_DATE.isoformat()})."
        ),
    )
    parser.add_argument(
        "--end",
        type=parse_date,
        default=date.today(),
        help=(
            "Inclusive end date in YYYY-MM-DD format "
            "(default: today when the script runs)."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.end < args.start:
        print("Error: --end must be on or after --start.", file=sys.stderr)
        return 2

    try:
        # yfinance treats `end` as exclusive; add one day for an inclusive CLI date.
        prices = yf.download(
            args.ticker,
            start=args.start.isoformat(),
            end=(args.end + timedelta(days=1)).isoformat(),
            interval="1d",
            auto_adjust=False,
            actions=False,
            progress=False,
            multi_level_index=False,
        )
    except Exception as exc:
        print(
            f"Error downloading data for {args.ticker}: {exc}",
            file=sys.stderr,
        )
        return 1

    if prices.empty:
        print(
            f"Error: Yahoo Finance returned no data for {args.ticker} "
            f"from {args.start} through {args.end}. Check the ticker, dates, "
            "and network connection.",
            file=sys.stderr,
        )
        return 1

    if getattr(prices.columns, "nlevels", 1) > 1:
        prices.columns = prices.columns.get_level_values(0)

    available_columns = [column for column in PRICE_COLUMNS if column in prices]
    missing_columns = [column for column in PRICE_COLUMNS if column not in prices]
    if not available_columns:
        print(
            f"Error: The download for {args.ticker} contained none of the "
            "expected price or volume columns.",
            file=sys.stderr,
        )
        return 1
    if missing_columns:
        print(
            "Warning: The downloaded data did not include: "
            + ", ".join(missing_columns),
            file=sys.stderr,
        )

    prices = prices.loc[:, available_columns].copy()
    prices.index = prices.index.strftime("%Y-%m-%d")
    prices.index.name = "Date"

    safe_ticker = re.sub(r"[^A-Za-z0-9._-]+", "_", args.ticker)
    output_path = DATA_DIR / f"{safe_ticker}_daily.csv"
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        prices.to_csv(output_path)
    except OSError as exc:
        print(f"Error saving CSV to {output_path}: {exc}", file=sys.stderr)
        return 1

    print(f"Saved {len(prices)} daily rows to {output_path}")
    print(f"CSV columns: Date, {', '.join(available_columns)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
