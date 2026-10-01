"""Self-contained Streamlit dashboard for AVIP 2026 Task 3."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
REQUIRED_COLUMNS = {"Date", "Close"}
MOVING_AVERAGE_WINDOWS = (20, 50)
PRICE_TICKER_PREFERENCE = "TCS.NS_daily.csv"


def load_data(csv_path: str) -> pd.DataFrame:
    """Load a source CSV without changing it on disk."""
    return pd.read_csv(csv_path)


def clean_data(raw_data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Validate and clean the required fields in memory."""
    missing_columns = REQUIRED_COLUMNS.difference(raw_data.columns)
    if missing_columns:
        raise ValueError(
            "The selected CSV is missing required column(s): "
            + ", ".join(sorted(missing_columns))
            + ". Required columns are Date and Close."
        )

    data = raw_data.copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data["Close"] = pd.to_numeric(data["Close"], errors="coerce")

    has_volume = "Volume" in data.columns
    if has_volume:
        data["Volume"] = pd.to_numeric(data["Volume"], errors="coerce")

    finite_close = np.isfinite(data["Close"].to_numpy(dtype=float, na_value=np.nan))
    valid_rows = data["Date"].notna() & finite_close
    invalid_date_or_close_rows = int((~valid_rows).sum())
    data = data.loc[valid_rows].copy()

    duplicate_dates = int(data["Date"].duplicated(keep="last").sum())
    data = (
        data.sort_values("Date", kind="stable")
        .drop_duplicates(subset="Date", keep="last")
        .reset_index(drop=True)
    )

    if data.empty:
        raise ValueError("The selected CSV contains no usable dates and closing prices.")

    quality = {
        "invalid_date_or_close_rows": invalid_date_or_close_rows,
        "duplicate_dates_removed": duplicate_dates,
        "volume_available": has_volume,
        "missing_volume_values": int(data["Volume"].isna().sum()) if has_volume else 0,
    }
    return data, quality


def calculate_indicators(cleaned_data: pd.DataFrame) -> pd.DataFrame:
    """Calculate rolling averages and returns from actual chronological closes."""
    data = cleaned_data.copy()
    for window in MOVING_AVERAGE_WINDOWS:
        data[f"MA_{window}"] = data["Close"].rolling(
            window=window,
            min_periods=window,
        ).mean()
    data["Daily Return"] = data["Close"].pct_change(fill_method=None)
    return data


def create_charts(selected_data: pd.DataFrame) -> tuple[Any, Any, Any | None]:
    """Build the three interactive charts from the selected actual observations."""
    price_chart = px.line(
        selected_data,
        x="Date",
        y="Close",
        title="Closing Price Trend",
        labels={"Date": "Date", "Close": "Closing price"},
        template="plotly_white",
    )
    price_chart.update_traces(line={"color": "#1769aa", "width": 2})
    price_chart.update_layout(hovermode="x unified", margin={"t": 55, "b": 20})

    moving_average_chart = go.Figure()
    moving_average_chart.add_trace(
        go.Scatter(
            x=selected_data["Date"],
            y=selected_data["Close"],
            name="Close",
            mode="lines",
            line={"color": "#1769aa", "width": 2},
        )
    )
    colors = {20: "#ef7d32", 50: "#2f8f62"}
    for window in MOVING_AVERAGE_WINDOWS:
        column = f"MA_{window}"
        if selected_data[column].notna().any():
            moving_average_chart.add_trace(
                go.Scatter(
                    x=selected_data["Date"],
                    y=selected_data[column],
                    name=f"{window}-day moving average",
                    mode="lines",
                    line={"color": colors[window], "width": 1.7},
                )
            )
    moving_average_chart.update_layout(
        title="Closing Price and Moving Averages",
        xaxis_title="Date",
        yaxis_title="Closing price",
        template="plotly_white",
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.12, "x": 0},
        margin={"t": 80, "b": 20},
    )

    returns = selected_data["Daily Return"].replace([np.inf, -np.inf], np.nan).dropna()
    returns_chart = None
    if not returns.empty:
        returns_frame = pd.DataFrame({"Daily Return": returns})
        returns_chart = px.histogram(
            returns_frame,
            x="Daily Return",
            nbins=50,
            title="Daily Returns Distribution",
            labels={"Daily Return": "Daily percentage return", "count": "Trading days"},
            template="plotly_white",
            color_discrete_sequence=["#4c78a8"],
        )
        returns_chart.update_layout(
            yaxis_title="Trading days",
            xaxis_tickformat=".1%",
            bargap=0.06,
            margin={"t": 55, "b": 20},
        )
    return price_chart, moving_average_chart, returns_chart


def format_percent(value: float | None) -> str:
    """Format a calculated percentage or return a safe unavailable marker."""
    if value is None or not np.isfinite(value):
        return "N/A"
    return f"{value:.2%}"


def calculate_metrics(selected_data: pd.DataFrame) -> dict[str, float | None]:
    """Calculate selected-period return metrics from actual closes and returns."""
    returns = selected_data["Daily Return"].replace([np.inf, -np.inf], np.nan).dropna()
    closes = selected_data["Close"].dropna()
    cumulative_return = (
        float(closes.iloc[-1] / closes.iloc[0] - 1)
        if len(closes) >= 2 and closes.iloc[0] != 0
        else None
    )
    return {
        "latest_close": float(closes.iloc[-1]) if not closes.empty else None,
        "mean_daily_return": float(returns.mean()) if not returns.empty else None,
        "daily_volatility": (
            float(returns.std(ddof=1)) if len(returns) > 1 else None
        ),
        "minimum_daily_return": float(returns.min()) if not returns.empty else None,
        "maximum_daily_return": float(returns.max()) if not returns.empty else None,
        "cumulative_return": cumulative_return,
    }


def render_interpretation(metrics: dict[str, float | None]) -> None:
    """Explain only the actual selected-period results; do not offer advice."""
    st.header("Volatility and Return Interpretation")
    mean_return = metrics["mean_daily_return"]
    volatility = metrics["daily_volatility"]
    minimum = metrics["minimum_daily_return"]
    maximum = metrics["maximum_daily_return"]
    cumulative = metrics["cumulative_return"]

    if mean_return is None:
        st.write(
            "There are not enough valid closing-price observations in the selected "
            "period to calculate daily return statistics."
        )
        return

    volatility_text = (
        format_percent(volatility)
        if volatility is not None
        else "unavailable from a single daily return"
    )
    st.write(
        f"The mean daily return for this selection was {format_percent(mean_return)}. "
        f"The sample standard deviation of daily returns was {volatility_text}. "
        f"Observed daily returns ranged from {format_percent(minimum)} to "
        f"{format_percent(maximum)}. Close-to-close cumulative return was "
        f"{format_percent(cumulative)}. These figures describe only the selected "
        "historical observations; volatility measures return dispersion and does "
        "not predict future performance. This is descriptive analysis, not "
        "investment advice."
    )


def render_key_findings(selected_data: pd.DataFrame, metrics: dict[str, float | None]) -> None:
    """Summarize values calculated from the selected dataset."""
    st.header("Key Findings")
    first_close = float(selected_data["Close"].iloc[0])
    latest_close = float(selected_data["Close"].iloc[-1])
    close_change = (
        latest_close / first_close - 1 if first_close != 0 else None
    )
    st.markdown(
        f"- The selected range contains **{len(selected_data):,}** trading records, "
        f"from **{selected_data['Date'].iloc[0]:%Y-%m-%d}** through "
        f"**{selected_data['Date'].iloc[-1]:%Y-%m-%d}**."
    )
    st.markdown(
        f"- The closing price changed from **{first_close:,.2f}** to "
        f"**{latest_close:,.2f}** (**{format_percent(close_change)}** close-to-close)."
    )
    mean_return = metrics["mean_daily_return"]
    minimum = metrics["minimum_daily_return"]
    maximum = metrics["maximum_daily_return"]
    if mean_return is not None:
        st.markdown(
            f"- Mean daily return was **{format_percent(mean_return)}**; observed "
            f"daily returns ranged from **{format_percent(minimum)}** to "
            f"**{format_percent(maximum)}**."
        )
    else:
        st.markdown("- Daily return statistics are unavailable for this selection.")


def main() -> None:
    """Render the interactive dashboard using the project's data/ CSV files."""
    st.set_page_config(
        page_title="Stock Price Data Visualization – AVIP 2026 Task 3",
        page_icon=":material/monitoring:",
        layout="wide",
    )
    st.title("Stock Price Data Visualization – AVIP 2026 Task 3")
    st.caption(
        "Explore historical closing prices and returns from the downloaded "
        "Yahoo Finance dataset."
    )

    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        st.error(f"No stock CSV was found in the project data folder: `{DATA_DIR}`.")
        st.info("Add the downloaded stock CSV to `data/` and reload the application.")
        return

    preferred_index = next(
        (index for index, path in enumerate(csv_files) if path.name == PRICE_TICKER_PREFERENCE),
        0,
    )
    with st.sidebar:
        st.header("Dataset")
        selected_filename = st.selectbox(
            "Stock data CSV",
            options=[path.name for path in csv_files],
            index=preferred_index,
        )

    csv_path = DATA_DIR / selected_filename
    try:
        raw_data = load_data(str(csv_path))
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        st.error(f"Could not load `{selected_filename}`: {exc}")
        return

    try:
        cleaned_data, quality = clean_data(raw_data)
    except ValueError as exc:
        st.error(str(exc))
        return

    # Indicators are computed in chronological order before the date filter,
    # matching the project analysis and allowing prior records to warm up averages.
    calculated_data = calculate_indicators(cleaned_data)
    first_date = calculated_data["Date"].iloc[0].date()
    last_date = calculated_data["Date"].iloc[-1].date()
    ticker = Path(selected_filename).stem.removesuffix("_daily")

    with st.sidebar:
        st.header("Date range")
        selected_dates = st.date_input(
            "Select inclusive dates",
            value=(first_date, last_date),
            min_value=first_date,
            max_value=last_date,
        )

    if not isinstance(selected_dates, (tuple, list)) or len(selected_dates) != 2:
        st.info("Select both a start and end date to view the analysis.")
        return

    start_date, end_date = selected_dates
    if start_date > end_date:
        st.error("Invalid date range: the start date must be on or before the end date.")
        return

    date_mask = calculated_data["Date"].dt.date.between(start_date, end_date)
    selected_data = calculated_data.loc[date_mask].copy()
    if selected_data.empty:
        st.info("No trading records fall within the selected date range.")
        return

    selected_data = selected_data.reset_index(drop=True)
    metrics = calculate_metrics(selected_data)
    date_range_label = f"{first_date:%Y-%m-%d} – {last_date:%Y-%m-%d}"

    st.caption(
        f"Selected ticker: **{ticker}** · Dataset date range: **{date_range_label}** "
        f"· **{len(calculated_data):,}** trading records"
    )
    with st.container(horizontal=True):
        selected_close = metrics["latest_close"]
        st.metric(
            "Latest closing price in selection",
            f"{selected_close:,.2f}" if selected_close is not None else "N/A",
            border=True,
        )
        st.metric(
            "Mean daily return",
            format_percent(metrics["mean_daily_return"]),
            border=True,
        )
        st.metric(
            "Daily volatility",
            format_percent(metrics["daily_volatility"]),
            border=True,
        )
        st.metric(
            "Cumulative return",
            format_percent(metrics["cumulative_return"]),
            border=True,
        )

    st.caption(
        f"Selected analysis period: **{start_date:%Y-%m-%d} – {end_date:%Y-%m-%d}** "
        f"({len(selected_data):,} trading record(s))."
    )

    price_chart, moving_average_chart, returns_chart = create_charts(selected_data)

    st.subheader("Closing Price Trend")
    st.plotly_chart(price_chart, width="stretch")

    st.subheader("Closing Price + 20-Day + 50-Day Moving Averages")
    st.plotly_chart(moving_average_chart, width="stretch")
    for window in MOVING_AVERAGE_WINDOWS:
        if selected_data[f"MA_{window}"].notna().sum() == 0:
            st.info(
                f"The {window}-day moving average is unavailable in this selection; "
                f"at least {window} valid chronological closing prices are required."
            )

    st.subheader("Daily Returns Distribution")
    if returns_chart is None:
        st.info(
            "Daily returns cannot be displayed for this selection; at least two "
            "consecutive valid closing prices are required."
        )
    else:
        st.plotly_chart(returns_chart, width="stretch")

    st.subheader("Selected-period return metrics")
    with st.container(horizontal=True):
        st.metric(
            "Minimum daily return",
            format_percent(metrics["minimum_daily_return"]),
            border=True,
        )
        st.metric(
            "Maximum daily return",
            format_percent(metrics["maximum_daily_return"]),
            border=True,
        )

    render_interpretation(metrics)
    render_key_findings(selected_data, metrics)

    st.subheader("Download selected data")
    source_columns = cleaned_data.columns.tolist()
    filtered_source = selected_data.loc[:, source_columns]
    filtered_source_csv = filtered_source.to_csv(index=False, date_format="%Y-%m-%d")
    calculated_csv = selected_data.to_csv(index=False, date_format="%Y-%m-%d")
    left_download, right_download = st.columns(2)
    with left_download:
        st.download_button(
            "Download filtered source data",
            data=filtered_source_csv,
            file_name=f"{ticker}_filtered_data.csv",
            mime="text/csv",
        )
    with right_download:
        st.download_button(
            "Download cleaned data with indicators",
            data=calculated_csv,
            file_name=f"{ticker}_filtered_calculated_data.csv",
            mime="text/csv",
        )

    with st.expander("Data quality notes"):
        st.write(f"Source file: `{selected_filename}`")
        st.write(f"Rows excluded for invalid dates or closing prices: {quality['invalid_date_or_close_rows']:,}")
        st.write(f"Duplicate dates removed in memory: {quality['duplicate_dates_removed']:,}")
        if quality["volume_available"]:
            st.write(
                "Volume is available. Missing volume values in the cleaned dataset: "
                f"{quality['missing_volume_values']:,}; these rows remain available "
                "for price analysis."
            )
        else:
            st.write("Volume is not present in this CSV; the price analysis remains available.")
        st.write(
            "The source CSV is read-only. Moving averages and daily returns are "
            "calculated in memory from chronologically ordered actual closing prices."
        )


if __name__ == "__main__":
    main()
