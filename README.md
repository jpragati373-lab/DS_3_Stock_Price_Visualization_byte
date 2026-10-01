# AVIP 2026
## AVIP 2026 Task 3: Stock Price Data Visualization

Data Science Internship – Task 3: Stock Price Data Visualization

## Project overview

An interactive Streamlit application for exploring historical stock prices, moving averages, and daily returns from a downloaded Yahoo Finance CSV. All runtime data loading, cleaning, calculations, interactive Plotly charts, and CSV downloads are contained in `app.py`. The app reads the raw CSV without modifying it and derives analytical columns in memory; it does not require the notebook or fetch script to run.

## Objective

Visualize closing-price history and moving averages, examine daily return distribution, and summarize historical return and volatility for a user-selected date range.

## Selected ticker

The downloaded dataset is for **TCS.NS** (Tata Consultancy Services, NSE). The app automatically loads `data/TCS.NS_daily.csv` when present. If additional CSVs are placed in `data/`, the sidebar allows selecting one; the ticker label is inferred from its filename.

## Data source and retrieval method

Historical daily prices are from Yahoo Finance and were retrieved with the `yfinance` Python package using [`scripts/fetch_stock_data.py`](./scripts/fetch_stock_data.py). The fetch script's defaults are ticker `TCS.NS`, start date `2015-01-01`, and end date equal to the run date (inclusive). Yahoo Finance data is intended for personal/research use; review [Yahoo's terms](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html) before reuse or redistribution. `yfinance` is not affiliated with or endorsed by Yahoo.

## Data date range

The downloaded file currently spans **2015-01-01 through 2026-10-01**, as recorded in the CSV. The app also shows the date range from the currently selected CSV at runtime. The last date can represent an incomplete trading session if data is fetched during market hours.

## Technologies used

- Python
- Streamlit
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Plotly (interactive dashboard charts)
- yfinance (for the data-fetching script)

## Data cleaning

The app parses `Date`, converts `Close` to numeric, excludes rows with invalid dates or unusable closing prices from analysis, sorts by date, and removes duplicate dates in memory. These operations do not change the downloaded raw CSV. Missing required `Date` or `Close` columns produce a clear error. Other columns are not required for the current analysis.

## Closing-price analysis

The closing-price chart plots actual `Close` values against `Date` for the selected inclusive date range.

## Moving averages

The app calculates 20- and 50-trading-record rolling means from `Close` across the ordered dataset before applying the display date filter. This preserves prior observations needed for moving-average context at the start of a selected window. A window is reported unavailable if there are fewer than the required valid closing observations.

## Daily returns

Daily percentage returns are calculated as the percentage change in consecutive valid closes. The daily-return distribution and summary metrics use returns whose dates are within the selected range. Cumulative return is calculated from the first and last selected closing prices. The source CSV remains unchanged.

## Notebook analysis and exported charts

Run `notebooks/stock_price_analysis.ipynb` from this project tree. The notebook reads the same downloaded CSV, applies the same date/close cleaning and indicator formulas as the app, and exports actual-data charts to `charts/`:

- `charts/closing_price_trend.png`
- `charts/moving_averages.png`
- `charts/daily_returns_distribution.png`

Change `SELECTED_START` and `SELECTED_END` in the notebook to reproduce another inclusive analysis period, then run that cell and the cells below it.

## Date-range reproduction

In the app sidebar, choose both an inclusive start and end date. The same date selection filters the price, moving-average, and daily-return distribution charts and determines the displayed period metrics. The default view uses the full date range of the selected dataset. For downloading a different range, use the fetch script, for example:

```powershell
python scripts/fetch_stock_data.py --ticker TCS.NS --start 2015-01-01 --end 2026-10-01
```

## Volatility/return interpretation

The app calculates the mean daily return, sample standard deviation of daily returns, observed minimum and maximum daily returns, and close-to-close cumulative return from the selected data. Its short interpretation is generated from those selected-period values and describes historical observations only; it does not provide investment advice or predict future performance.

## Key findings

For the full downloaded TCS.NS dataset (2015-01-01 through 2026-10-01; 2,906 records), the first and last closes are 1,272.78 and 2,068.00, respectively, for a close-to-close cumulative return of 62.48%. Across 2,905 daily returns, the mean was 0.0280%, the sample standard deviation was 1.5012%, the minimum was -9.4103%, and the maximum was 9.8451%. These are descriptive historical values from this CSV; the app recalculates findings for the selected date range.

## Installation

From the project folder, install the listed dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run instructions

Run the app locally from the project folder:

```powershell
streamlit run app.py
```

To retrieve or refresh a dataset using the configured default ticker:

```powershell
python scripts/fetch_stock_data.py
```

## Project structure

```text
DS_3_Stock_Price_Visualization_byte/
├── app.py
├── AVIP_SUBMISSION_CHECKLIST.md
├── charts/
│   ├── closing_price_trend.png
│   ├── moving_averages.png
│   └── daily_returns_distribution.png
├── data/
│   └── TCS.NS_daily.csv
├── screenshots/
├── notebooks/
│   └── stock_price_analysis.ipynb
├── scripts/
│   └── fetch_stock_data.py
├── README.md
└── requirements.txt
```

## Screenshots

No screenshots of the running app have been captured yet. Add them to `screenshots/` before submission if required.

## GitHub Repository

https://github.com/jpragati373-lab/DS_3_Stock_Price_Visualization_byte

## Live Demo

[Open the live Stock Price Data Visualization dashboard](https://ds3stockpricevisualizationbyte-fw5ve2tra2wtzaqkxk2jbd.streamlit.app/)
