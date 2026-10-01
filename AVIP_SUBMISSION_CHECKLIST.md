# AVIP 2026 Task 3 Submission Checklist

| Requirement | Status | Evidence/File |
|---|---|---|
| Closing price trend | PASS | `notebooks/stock_price_analysis.ipynb`; `charts/closing_price_trend.png`; `app.py` |
| 20-day moving average | PASS | `notebooks/stock_price_analysis.ipynb`; `charts/moving_averages.png`; `app.py` |
| 50-day moving average | PASS | `notebooks/stock_price_analysis.ipynb`; `charts/moving_averages.png`; `app.py` |
| Daily returns distribution | PASS | `notebooks/stock_price_analysis.ipynb`; `charts/daily_returns_distribution.png`; `app.py` |
| Date-range selector/reproduction | PASS | Sidebar in `app.py`; editable `SELECTED_START` / `SELECTED_END` in `notebooks/stock_price_analysis.ipynb`; README instructions |
| Volatility/return interpretation ≤200 words | PASS | `app.py` and notebook; notebook verifies word count at runtime |
| Data source | PASS | `README.md`; `scripts/fetch_stock_data.py`; actual CSV in `data/TCS.NS_daily.csv` |
| Notebook runs end-to-end | PASS | `notebooks/stock_price_analysis.ipynb`; all code cells executed successfully |
| Exported PNG charts | PASS | `charts/closing_price_trend.png`; `charts/moving_averages.png`; `charts/daily_returns_distribution.png` |
| README content | PASS | `README.md` |
| Requirements match imported packages | PASS | `requirements.txt` covers app, notebook, and fetch-script imports |
| `.gitignore` coverage | PASS | `.gitignore` ignores virtual environments, Python caches, `.env` files, notebook checkpoints, and Streamlit secrets |
| Streamlit app syntax and startup | PASS | `app.py`; validated with syntax check, Streamlit AppTest, and local server smoke test |
| Date filtering and metrics | PASS | `app.py`; date-range AppTest and calculations from the source CSV |
| Empty, invalid, missing, and insufficient-data handling | PASS | Guards and user messages in `app.py` |
| Raw source CSV integrity | PASS | `data/TCS.NS_daily.csv`; SHA-256 unchanged during audit |
| Secret/API-key scan | PASS | No matches in project files for common credential indicators |
| README screenshots section | PASS | `README.md`; section exists |
| Screenshots captured | MANUAL ACTION | `screenshots/` is empty; capture app screenshots if required for submission |
| GitHub Repository URL | MANUAL ACTION | No repository was created; do not provide a URL until one exists |
| Live Demo URL | MANUAL ACTION | App is not deployed; provide the real deployment URL after deployment |
