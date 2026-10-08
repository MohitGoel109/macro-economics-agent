"""SYNTHETIC data, used ONLY to smoke-test the pipeline offline (--synthetic).
Never submit numbers produced from this as real results."""
import json
import numpy as np
import pandas as pd
from src.config import RAW, LOOKBACK_DAYS

def make_calendar(end, seed=7):
    rng = np.random.default_rng(seed)
    days = pd.bdate_range(end - pd.Timedelta(days=LOOKBACK_DAYS), end)
    rows, i = [], 1
    def add(d, t, name, f, sd):
        nonlocal i
        a = f + rng.normal(0, sd)
        rows.append(dict(id=i, date=d.strftime("%d/%m/%Y"), time=t, zone="united states",
                         currency="USD", importance="high", event=name,
                         actual=f"{a:.1f}", forecast=f"{f:.1f}", previous=f"{f+rng.normal(0,sd):.1f}"))
        i += 1
    for d in days:
        if d.weekday() == 3: add(d, "12:30", "Initial Jobless Claims", 225, 12)
        if d.weekday() == 4 and d.day <= 7: add(d, "12:30", "Nonfarm Payrolls (Sep)", 150, 40)
        if d.weekday() == 4 and d.day <= 7: add(d, "12:30", "Unemployment Rate (Sep)", 4.2, 0.1)
        if d.day in (12, 13, 14) and d.weekday() < 5 and not any(r["event"].startswith("CPI") and r["date"][3:] == d.strftime("%d/%m/%Y")[3:] for r in rows):
            add(d, "12:30", "CPI (MoM) (Sep)", 0.3, 0.1)
        if d.weekday() == 2 and 15 <= d.day <= 21 and d.month % 2 == 1: add(d, "18:00", "Fed Interest Rate Decision", 4.5, 0.15)
        if d.weekday() == 1 and d.day >= 25: add(d, "14:00", "CB Consumer Confidence (Sep)", 89, 5)
    return rows

def make_prices(end, calendar_df, seed=11):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(end - pd.Timedelta(days=LOOKBACK_DAYS + 450), end)
    ret = rng.normal(0.0004, 0.009, len(idx))
    # plant a weak, honest-to-label link: positive net surprise -> slightly better next days
    if not calendar_df.empty:
        s = calendar_df.assign(d=calendar_df.ts_utc.dt.tz_localize(None).dt.normalize())
        s["z"] = np.sign(s.actual - s.forecast).fillna(0)
        daily = s.groupby("d").z.sum().reindex(idx).fillna(0).values
        ret[1:] += 0.0006 * daily[:-1]
    px = 400 * np.exp(np.cumsum(ret))
    return pd.Series(px, index=idx, name="SPY")

def make_news():
    items = [{"query": "synthetic", "title": f"[SYNTHETIC] Placeholder macro headline {k}",
              "url": f"https://example.com/{k}", "published": "", "snippet": "Synthetic text for offline testing."} for k in range(1, 5)]
    (RAW / "news.json").write_text(json.dumps(items, indent=2))
    return items
