"""Interactive stock-price analysis for the AVIP 2026 Task 3 demo."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
REQUIRED_COLUMNS = {"Date", "Close"}
WINDOWS = (20, 50)


st.set_page_config(
    page_title="Stock Price Data Visualization – AVIP 2026 Task 3",
    page_icon=":material/monitoring:",
    layout="wide",
)


@st.cache_data
def load_stock_data(csv_path: str) -> pd.DataFrame:
    """Read a source CSV and derive analysis columns without changing the file."""
    return pd.read_csv(csv_path)


def ticker_from_filename(csv_path: Path) -> str:
    stem = csv_path.stem
    return stem.removesuffix("_daily")


st.title("Stock Price Data Visualization – AVIP 2026 Task 3")

csv_files = sorted(DATA_DIR.glob("*.csv"))
if not csv_files:
    st.error(
        f"No CSV data file was found in `{DATA_DIR}`. "
        "Run `python scripts/fetch_stock_data.py` to retrieve historical data."
    )
    st.stop()

with st.sidebar:
    st.header("Dataset")
    preferred_file = next(
        (path for path in csv_files if path.name == "TCS.NS_daily.csv"),
        csv_files[0],
    )
    selected_file_name = st.selectbox(
        "Stock data CSV",
        options=[path.name for path in csv_files],
        index=[path.name for path in csv_files].index(preferred_file.name),
    )

selected_file = DATA_DIR / selected_file_name
try:
    raw_data = load_stock_data(str(selected_file))
except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
    st.error(f"Could not read `{selected_file.name}`: {exc}")
    st.stop()

missing_required = REQUIRED_COLUMNS.difference(raw_data.columns)
if missing_required:
    st.error(
        "The selected CSV is missing required column(s): "
        + ", ".join(sorted(missing_required))
        + ". Required columns are `Date` and `Close`."
    )
    st.stop()

data = raw_data.copy()
data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
data["Close"] = pd.to_numeric(data["Close"], errors="coerce")
valid_close = np.isfinite(data["Close"].to_numpy(dtype=float, na_value=np.nan))
usable_rows = data["Date"].notna() & valid_close
invalid_rows = int((~usable_rows).sum())
data = data.loc[usable_rows, ["Date", "Close"]].copy()
data = data.sort_values("Date", kind="stable").drop_duplicates(
    subset="Date", keep="last"
)

if invalid_rows:
    st.warning(
        f"Excluded {invalid_rows:,} row(s) with an invalid date or missing/non-numeric "
        "closing price from calculations. The raw CSV was not changed."
    )

if data.empty:
    st.error("No rows with valid dates and closing prices are available.")
    st.stop()

data = data.set_index("Date")
for window in WINDOWS:
    data[f"MA_{window}"] = data["Close"].rolling(window=window, min_periods=window).mean()
data["Daily Return"] = data["Close"].pct_change(fill_method=None)

full_start = data.index.min().date()
full_end = data.index.max().date()
ticker = ticker_from_filename(selected_file)

with st.sidebar:
    st.header("Date range")
    selected_dates = st.date_input(
        "Select inclusive dates",
        value=(full_start, full_end),
        min_value=full_start,
        max_value=full_end,
    )

if not isinstance(selected_dates, (tuple, list)) or len(selected_dates) != 2:
    st.info("Select both a start date and an end date to view the analysis.")
    st.stop()

start_date, end_date = selected_dates
if start_date > end_date:
    st.error("Invalid date range: the start date must be on or before the end date.")
    st.stop()

selected = data.loc[
    (data.index.date >= start_date) & (data.index.date <= end_date)
].copy()
if selected.empty:
    st.info("No trading records fall within the selected date range.")
    st.stop()

latest_close = data["Close"].iloc[-1]
st.caption(f"Selected ticker: **{ticker}**")
with st.container(horizontal=True):
    st.metric("Dataset date range", f"{full_start:%Y-%m-%d} – {full_end:%Y-%m-%d}", border=True)
    st.metric("Trading records", f"{len(data):,}", border=True)
    st.metric("Latest closing price", f"{latest_close:,.2f}", border=True)

st.caption(
    f"Analysis window: **{start_date:%Y-%m-%d} – {end_date:%Y-%m-%d}** "
    f"({len(selected):,} trading record(s))."
)

st.subheader("Closing Price Trend")
fig, ax = plt.subplots(figsize=(11, 4.5))
ax.plot(selected.index, selected["Close"], color="#1f77b4", linewidth=1.7)
ax.set_xlabel("Date")
ax.set_ylabel("Closing price")
ax.grid(True, alpha=0.25)
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.subheader("Moving Averages")
fig, ax = plt.subplots(figsize=(11, 4.8))
ax.plot(selected.index, selected["Close"], label="Close", color="#1f77b4", linewidth=1.5)
for window, color in ((20, "#ff7f0e"), (50, "#2ca02c")):
    average = selected[f"MA_{window}"]
    if average.notna().any():
        ax.plot(
            selected.index,
            average,
            label=f"{window}-day moving average",
            color=color,
            linewidth=1.4,
        )
    else:
        st.info(
            f"The {window}-day moving average is unavailable: "
            f"at least {window} valid closing prices are required."
        )
ax.set_xlabel("Date")
ax.set_ylabel("Closing price")
ax.legend()
ax.grid(True, alpha=0.25)
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

returns = selected["Daily Return"].replace([np.inf, -np.inf], np.nan).dropna()
st.subheader("Daily Returns Distribution")
if returns.empty:
    st.info(
        "Daily returns cannot be displayed for this selection; at least two "
        "consecutive valid closing prices are required."
    )
else:
    fig, ax = plt.subplots(figsize=(10, 4.2))
    sns.histplot(returns, bins="auto", kde=len(returns) >= 2, ax=ax, color="#4c78a8")
    ax.set_xlabel("Daily percentage return")
    ax.set_ylabel("Trading days")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:.1%}"))
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

st.subheader("Selected-period metrics")
if returns.empty:
    st.warning("Return metrics are unavailable because the selection has no daily returns.")
    mean_return = volatility = min_return = max_return = None
else:
    mean_return = float(returns.mean())
    volatility = float(returns.std(ddof=1)) if len(returns) > 1 else None
    min_return = float(returns.min())
    max_return = float(returns.max())

selected_close = selected["Close"].dropna()
cumulative_return = (
    float(selected_close.iloc[-1] / selected_close.iloc[0] - 1)
    if len(selected_close) >= 2
    else None
)

def metric_value(value: float | None) -> str:
    return "N/A" if value is None or not np.isfinite(value) else f"{value:.2%}"


with st.container(horizontal=True):
    st.metric("Mean daily return", metric_value(mean_return), border=True)
    st.metric("Daily return volatility (sample std. dev.)", metric_value(volatility), border=True)
    st.metric("Minimum daily return", metric_value(min_return), border=True)
    st.metric("Maximum daily return", metric_value(max_return), border=True)
    st.metric("Cumulative return", metric_value(cumulative_return), border=True)

st.header("Volatility and Return Interpretation")
if returns.empty:
    st.write(
        "There are not enough valid closing-price observations in the selected "
        "window to calculate daily returns or their summary statistics."
    )
else:
    volatility_text = (
        f"{volatility:.2%}" if volatility is not None else "not available from one return"
    )
    st.write(
        f"For {start_date:%Y-%m-%d} through {end_date:%Y-%m-%d}, the mean daily "
        f"return was {mean_return:.2%} and the sample standard deviation of daily "
        f"returns was {volatility_text}. Daily returns ranged from "
        f"{min_return:.2%} to {max_return:.2%}. The cumulative return from the "
        f"first to last selected closing price was {metric_value(cumulative_return)}. "
        "These values describe only the selected historical observations; "
        "volatility measures the dispersion of daily returns and does not predict "
        "future performance. This is descriptive analysis, not investment advice."
    )

st.header("Key Findings")
first_close = float(selected_close.iloc[0])
last_close = float(selected_close.iloc[-1])
price_change_pct = last_close / first_close - 1 if first_close else float("nan")
findings = [
    f"The selected window contains {len(selected):,} trading record(s), from "
    f"{selected.index.min():%Y-%m-%d} to {selected.index.max():%Y-%m-%d}.",
    f"Closing price changed from {first_close:,.2f} to {last_close:,.2f} "
    f"({metric_value(price_change_pct)} close-to-close).",
]
if not returns.empty:
    findings.append(
        f"The mean daily return was {mean_return:.2%}; observed daily returns "
        f"ranged from {min_return:.2%} to {max_return:.2%}."
    )
else:
    findings.append("Daily return statistics are unavailable for this selection.")
for finding in findings:
    st.markdown(f"- {finding}")

with st.expander("Data quality notes"):
    st.write(f"Source file: `{selected_file.name}`")
    st.write(f"Rows excluded due to invalid dates or closing prices: {invalid_rows:,}")
    st.write(
        "Moving averages and daily returns are computed in memory on the ordered "
        "dataset before applying the selected display window, so the indicators "
        "can use preceding trading records. The source CSV is read-only."
    )
