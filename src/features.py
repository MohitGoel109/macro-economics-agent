"""Feature engineering. Every feature for date t uses only information available at the close of t
(released events up to t, scheduled calendar dates, price history up to t)."""
import numpy as np
import pandas as pd
from src.config import FAMILIES, INVERSE, HORIZON

def tag_family(name):
    n = name.lower()
    for fam, kws in FAMILIES.items():
        if any(k in n for k in kws):
            return fam
    return "OTHER"

def enrich_events(ev: pd.DataFrame) -> pd.DataFrame:
    ev = ev.copy().sort_values("ts_utc").reset_index(drop=True)
    ev["family"] = ev["event"].map(tag_family)
    ev["base_name"] = ev["event"].str.replace(r"\s*\([^)]*\)\s*", " ", regex=True).str.strip()
    ev["raw_surprise"] = ev["actual"] - ev["forecast"]
    # z-score vs PAST surprises of the same event only (expanding std, shifted -> no look-ahead)
    sd = ev.groupby("base_name")["raw_surprise"].transform(lambda s: s.abs().expanding(2).mean().shift(1))
    ev["surprise_z"] = (ev["raw_surprise"] / sd).replace([np.inf, -np.inf], np.nan).clip(-3, 3).fillna(0.0)
    inv = ev["event"].str.lower().map(lambda n: any(k in n for k in INVERSE))
    ev["sentiment"] = np.where(inv, -1.0, 1.0) * ev["surprise_z"]   # + = good for risk assets
    ev["hour_utc"] = ev["ts_utc"].dt.hour + ev["ts_utc"].dt.minute / 60
    ev["hour_est"] = ev["ts_est"].dt.hour + ev["ts_est"].dt.minute / 60
    ev["date"] = ev["ts_utc"].dt.tz_localize(None).dt.normalize()
    return ev

def daily_features(ev: pd.DataFrame, close: pd.Series) -> pd.DataFrame:
    idx = close.index
    df = pd.DataFrame(index=idx)
    g = ev.groupby("date")
    df["n_events"] = g.size().reindex(idx).fillna(0)
    df["net_sentiment"] = g["sentiment"].sum().reindex(idx).fillna(0)
    df["first_event_hour_est"] = g["hour_est"].min().reindex(idx).fillna(-1)
    df["sentiment_idx"] = df["net_sentiment"].ewm(halflife=10).mean()
    df["sentiment_cum"] = df["net_sentiment"].cumsum()
    df["sentiment_5d"] = df["net_sentiment"].rolling(5, min_periods=1).sum()
    df["dow"] = idx.dayofweek
    df["month_day"] = idx.day
    for fam in FAMILIES:
        dates = pd.DatetimeIndex(sorted(ev.loc[ev.family == fam, "date"].unique()))
        nxt, prv = [], []
        for d in idx:
            after = dates[dates >= d]
            before = dates[dates <= d]
            nxt.append((after[0] - d).days if len(after) else 30)     # schedule is public in advance
            prv.append((d - before[-1]).days if len(before) else 30)
        df[f"days_to_{fam.lower()}"] = np.minimum(nxt, 30)
        df[f"days_since_{fam.lower()}"] = np.minimum(prv, 30)
    ret = close.pct_change()
    df["spy_ret_1d"], df["spy_ret_5d"] = ret, close.pct_change(5)
    df["spy_vol_10d"], df["spy_vol_20d"] = ret.rolling(10).std(), ret.rolling(20).std()
    df["spy_dd_20d"] = close / close.rolling(20).max() - 1
    # event-type flag for the FORWARD window (calendar is known in advance) used for the heatmap only
    flag = pd.Series("NONE", index=idx)
    for fam in ["CPI", "EMPLOYMENT", "FOMC"]:
        dates = set(ev.loc[ev.family == fam, "date"])
        fwd = pd.Series([any((idx[min(i + k, len(idx) - 1)] in dates) for k in range(1, HORIZON + 1))
                         for i in range(len(idx))], index=idx)
        flag[fwd] = fam
    df["fwd_event_type"] = flag
    return df.replace([np.inf, -np.inf], np.nan)
