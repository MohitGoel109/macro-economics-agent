"""Join events-derived features with backtest logs inside DuckDB."""
import duckdb
import pandas as pd
from src.config import DB_PATH, HORIZON

def build_panel(events: pd.DataFrame, daily: pd.DataFrame, logs: pd.DataFrame) -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH))
    e = events.copy(); e["ts_utc"] = e["ts_utc"].astype(str); e["ts_est"] = e["ts_est"].astype(str)
    con.register("ev_df", e); con.execute("CREATE OR REPLACE TABLE events AS SELECT * FROM ev_df")
    d = daily.reset_index().rename(columns={"index": "date"})
    con.register("d_df", d); con.execute("CREATE OR REPLACE TABLE daily_features AS SELECT * FROM d_df")
    con.register("l_df", logs); con.execute("CREATE OR REPLACE TABLE strategy_logs AS SELECT * FROM l_df")
    # target = P&L over the NEXT `HORIZON` trading days (t+1 .. t+H); trailing_20 uses only the past
    panel = con.execute(f"""
        WITH l AS (
          SELECT date, perm_id, strategy, p1, p2, mode, pos, daily_pnl,
                 SUM(daily_pnl) OVER (PARTITION BY perm_id ORDER BY date
                                      ROWS BETWEEN 1 FOLLOWING AND {HORIZON} FOLLOWING) AS target_raw,
                 COUNT(daily_pnl) OVER (PARTITION BY perm_id ORDER BY date
                                      ROWS BETWEEN 1 FOLLOWING AND {HORIZON} FOLLOWING) AS n_fwd,
                 SUM(daily_pnl) OVER (PARTITION BY perm_id ORDER BY date
                                      ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS trailing_20,
                 SUM(daily_pnl) OVER (PARTITION BY perm_id ORDER BY date
                                      ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS trailing_5
          FROM strategy_logs)
        SELECT l.* EXCLUDE (target_raw), CASE WHEN l.n_fwd = {HORIZON} THEN l.target_raw END AS target_pnl,
               f.* EXCLUDE (date)
        FROM l JOIN daily_features f USING (date) ORDER BY date, perm_id
    """).df()
    con.register("p_df", panel); con.execute("CREATE OR REPLACE TABLE panel AS SELECT * FROM p_df")
    con.close()
    return panel
