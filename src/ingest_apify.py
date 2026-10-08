"""Macro calendar ingestion via Apify (actor: pintostudio/economic-calendar-data-investing-com).

Scrapes in CHUNK_DAYS windows and caches each chunk to data/raw/calendar_<from>_<to>.json,
so re-running never pays twice. Output: data/raw/calendar.csv (parsed, UTC timestamps).

Observed actor output fields:
  date (DD/MM/YYYY), time (HH:MM), zone, currency, importance, event,
  actual / forecast / previous (strings like "81.9", "3.4%", "225K"), id
With timeZone left empty the timestamps are UTC (CB Consumer Confidence shows 14:00 = 10:00 ET).
"""
import json, os, re, sys
from datetime import date, timedelta
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from src.config import RAW, ROOT, LOOKBACK_DAYS, CHUNK_DAYS, COST_PER_EVENT_USD

load_dotenv(ROOT / ".env")
_MULT = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}


def parse_value(x):
    """'3.4%' -> 3.4 ; '225K' -> 225000 ; '-1.2M' -> -1.2e6 ; '' -> NaN."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return np.nan
    s = str(x).strip().replace(",", "").replace("$", "").replace("%", "")
    if s in ("", "-", "N/A"):
        return np.nan
    m = re.fullmatch(r"(-?\d+\.?\d*)\s*([KMBT])?", s, flags=re.I)
    if not m:
        return np.nan
    return float(m.group(1)) * _MULT.get((m.group(2) or "").upper(), 1.0)


def parse_events(items):
    df = pd.DataFrame(items)
    if df.empty:
        return df
    t = df["time"].where(df["time"].astype(str).str.fullmatch(r"\d{1,2}:\d{2}"), "00:00")
    df["ts_utc"] = pd.to_datetime(df["date"] + " " + t, format="%d/%m/%Y %H:%M", utc=True)
    df["ts_est"] = df["ts_utc"].dt.tz_convert("America/New_York")  # EST/EDT aware
    for c in ("actual", "forecast", "previous"):
        df[c + "_raw"] = df[c]
        df[c] = df[c].map(parse_value)
    df["event"] = df["event"].str.replace(r"\s+", " ", regex=True).str.strip()
    keep = ["id", "ts_utc", "ts_est", "zone", "currency", "importance", "event",
            "actual", "forecast", "previous"]
    return df[keep].drop_duplicates("id").sort_values("ts_utc").reset_index(drop=True)


def _windows(start: date, end: date, step: int):
    cur = start
    while cur <= end:
        nxt = min(cur + timedelta(days=step - 1), end)
        yield cur, nxt
        cur = nxt + timedelta(days=1)


def scrape(end: date | None = None, dry_run=False):
    end = end or date.today()
    start = end - timedelta(days=LOOKBACK_DAYS)
    base = json.loads((ROOT / "config" / "apify_input.json").read_text())
    wins = list(_windows(start, end, CHUNK_DAYS))
    todo = [w for w in wins if not (RAW / f"calendar_{w[0]}_{w[1]}.json").exists()]
    est = len(todo) * CHUNK_DAYS / 7 * 16 * COST_PER_EVENT_USD
    print(f"{len(wins)} chunks, {len(todo)} not cached. Rough cost of remaining: ~${est:.2f}")
    if dry_run or not todo:
        return _load_cache()
    token, actor = os.getenv("APIFY_TOKEN"), os.getenv("APIFY_ACTOR_ID")
    if not token or not actor:
        sys.exit("Set APIFY_TOKEN and APIFY_ACTOR_ID in .env (or run with --synthetic).")
    from apify_client import ApifyClient
    client = ApifyClient(token)
    for a, b in todo:
        inp = {**base, "fromDate": a.isoformat(), "toDate": b.isoformat()}
        print(f"  scraping {a} -> {b} ...")
        run = client.actor(actor).call(run_input=inp)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        (RAW / f"calendar_{a}_{b}.json").write_text(json.dumps(items))
        print(f"    {len(items)} events")
    return _load_cache()


def _load_cache():
    items = []
    for f in sorted(RAW.glob("calendar_*.json")):
        items += json.loads(f.read_text())
    df = parse_events(items)
    df.to_csv(RAW / "calendar.csv", index=False)
    print(f"calendar.csv: {len(df)} events")
    return df


if __name__ == "__main__":
    scrape(dry_run="--dry-run" in sys.argv)
