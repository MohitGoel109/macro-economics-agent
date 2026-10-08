"""Central settings. Edit here, not inside the modules."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
CHARTS = OUT / "charts"
REPORTS = ROOT / "reports"
DB_PATH = PROC / "macro.duckdb"

LOOKBACK_DAYS = 180          # calendar window required by the assignment
CHUNK_DAYS = 30              # Apify scrape is done in chunks and cached per chunk
COST_PER_EVENT_USD = 0.01    # $10 / 1000 results for the chosen actor
SYMBOL = "SPY"
HORIZON = 5                  # prediction horizon in trading days (target = next-5-day P&L)
TOP_K = 3                    # permutations traded per rebalance
TRADING_COST = 0.0002        # 2 bps per unit of position change
MIN_TRAIN_DAYS = 45          # first walk-forward fold starts after this many trading days
PERIODS_PER_YEAR = 252 / HORIZON   # non-overlapping 5-day periods

# Keywords used to tag event families (lower-case substring match on event name)
FAMILIES = {
    "FOMC": ["fomc", "fed interest rate", "federal funds", "fed chair", "powell"],
    "CPI": ["cpi", "consumer price"],
    "EMPLOYMENT": ["nonfarm", "non-farm", "unemployment rate", "adp", "jobless", "payroll", "jolts"],
}
# Events where a HIGHER-than-forecast print is bad for risk assets
INVERSE = ["unemployment rate", "jobless claims", "continuing claims", "cpi", "ppi", "inflation"]
