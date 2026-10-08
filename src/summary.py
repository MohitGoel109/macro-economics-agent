"""1-page macro outlook (template-based: no LLM key needed). Uses scraped events + Tavily headlines."""
import json
import pandas as pd
from src.config import RAW, REPORTS

def build(ev, daily, latest, synthetic=False):
    last = ev["date"].max()
    recent = ev[ev.date > last - pd.Timedelta(days=30)]
    s_now, s_prev = daily["sentiment_cum"].iloc[-1], daily["sentiment_cum"].iloc[-22]
    trend = "improving" if s_now > s_prev else "deteriorating"
    beats = recent[recent.sentiment > 0.5].nlargest(3, "sentiment")
    misses = recent[recent.sentiment < -0.5].nsmallest(3, "sentiment")
    fmt = lambda df: "\n".join(f"- {r.date:%b %d}: **{r.event}** actual {r.actual:g} vs forecast {r.forecast:g}"
                               for r in df.itertuples()) or "- none"
    news = json.loads((RAW / "news.json").read_text()) if (RAW / "news.json").exists() else []
    heads = "\n".join(f"- [{n['title']}]({n['url']})" for n in news[:8]) or "- (no news fetched)"
    top = latest.head(3)
    picks = "\n".join(f"- `{r.perm_id}` (predicted 5-day P&L {r.pred:+.2%})" for r in top.itertuples())
    banner = "> **SYNTHETIC DATA: pipeline smoke test only, not real results.**\n\n" if synthetic else ""
    md = f"""# Macro Outlook: week of {last:%d %b %Y}

{banner}## Snapshot
The US high-importance calendar covers **{len(ev)} releases** over the window ({ev.date.min():%d %b} to {last:%d %b %Y}).
The surprise-based sentiment index (actual vs forecast, sign-adjusted so positive = supportive for risk assets)
is **{trend}** over the last month (cumulative {s_now:+.1f} vs {s_prev:+.1f} a month ago).

## Largest recent positive surprises
{fmt(beats)}

## Largest recent negative surprises
{fmt(misses)}

## What the news flow says (Tavily)
{heads}

## Implication for strategy selection
The model's top permutations for the coming 5 trading days:
{picks}

*Method:* surprise = actual - forecast, scaled by the expanding mean absolute surprise of the same release
(past data only), clipped to +/-3, inverted for releases where a higher print is negative (unemployment, claims, CPI).
Template-generated from data; read the headlines for qualitative context before relying on it.
"""
    (REPORTS / "macro_summary.md").write_text(md)
    return md
