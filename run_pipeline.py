"""One command runs everything.
   python run_pipeline.py              # real data (needs .env keys)
   python run_pipeline.py --synthetic  # offline smoke test with fake data
"""
import argparse, json
from datetime import date
import pandas as pd
from src import config as C, ingest_apify, ingest_tavily, backtest, features, db, model, visuals, summary, synthetic

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--skip-scrape", action="store_true", help="reuse cached data/raw files")
    a = ap.parse_args()
    for d in (C.RAW, C.PROC, C.CHARTS, C.REPORTS): d.mkdir(parents=True, exist_ok=True)
    end = pd.Timestamp(date.today())

    if a.synthetic:
        raw = synthetic.make_calendar(end)
        ev = ingest_apify.parse_events(raw); synthetic.make_news()
        close = synthetic.make_prices(end, ev)
    else:
        ev = ingest_apify._load_cache() if a.skip_scrape else ingest_apify.scrape()
        if not a.skip_scrape: ingest_tavily.fetch()
        import yfinance as yf
        start = ev.ts_utc.min().tz_localize(None) - pd.Timedelta(days=450)
        close = yf.download(C.SYMBOL, start=start, progress=False, auto_adjust=True)["Close"].squeeze().dropna()
        close.index = pd.DatetimeIndex(close.index).tz_localize(None)
    ev = features.enrich_events(ev)
    daily = features.daily_features(ev, close)
    logs = backtest.run(close)
    panel = db.build_panel(ev, daily, logs)
    panel = panel[panel.date >= ev.date.min()]          # model sees only the macro-covered window
    res, preds, imp, latest = model.walk_forward(panel, close)
    stats = model.evaluate(res, preds)
    visuals.all(ev, daily, panel, res, preds, imp)
    summary.build(ev, daily, latest, synthetic=a.synthetic)
    write_report(stats, res, a.synthetic)
    (C.OUT / "metrics.json").write_text(json.dumps({"synthetic": a.synthetic, "stats": stats,
        "latest_picks": latest.head(5)[["perm_id", "pred"]].to_dict("records")}, indent=2))
    res.reset_index().to_csv(C.OUT / "walk_forward_results.csv", index=False)
    print(json.dumps(stats["model"], indent=2))

def write_report(stats, res, synthetic_flag):
    rows = "\n".join(f"| {k} | {v['total_return']:+.1%} | {v['sharpe']:.2f} | {v['sortino']:.2f} | {v['max_drawdown']:.1%} | {v['hit_rate']:.0%} |"
                     for k, v in stats.items())
    m = stats["model"]
    banner = "> **SYNTHETIC DATA: smoke test only. These numbers are NOT real results.**\n\n" if synthetic_flag else ""
    (C.REPORTS / "evaluation_report.md").write_text(f"""# Evaluation Report

{banner}Walk-forward window: {res.index.min():%Y-%m-%d} to {res.index.max():%Y-%m-%d}, {len(res)} non-overlapping {C.HORIZON}-day periods.
Sharpe/Sortino annualised with {C.PERIODS_PER_YEAR:.1f} periods/year, risk-free = 0.

| Strategy | Total return | Sharpe | Sortino | Max drawdown | Hit rate |
|---|---|---|---|---|---|
{rows}

Model diagnostics: mean cross-sectional rank IC = {m['mean_rank_ic']:.3f}, pred/actual correlation = {m['pred_corr']:.3f}, MAE = {m['mae']:.4%}.

## Method
- **Trading logs:** 24 permutations (MA crossover and breakout, long-only and long-short) backtested on {C.SYMBOL} daily bars, {C.TRADING_COST*1e4:.0f} bps cost per position change.
- **Target:** P&L of each permutation over the next {C.HORIZON} trading days.
- **Model:** LightGBM regressor on permutation parameters, trailing P&L, macro-surprise, calendar-distance and volatility features.
- **Selection:** at each rebalance, trade the top {C.TOP_K} permutations by predicted P&L.

## Avoiding data leakage
1. Walk-forward, expanding window, no shuffling: training only uses data before each test date.
2. **Embargo of {C.HORIZON} days:** a training row's target spans t+1..t+{C.HORIZON}, so rows are only used if their target window ended on or before the test date.
3. Strategy positions use the signal at close t and earn returns from t+1.
4. Surprise z-scores are scaled by *past* surprises only (expanding, shifted by one).
5. Trailing P&L features use only past days. Calendar "days until next event" uses the publicly scheduled release dates.
6. Evaluation periods are non-overlapping, so Sharpe is not inflated by overlapping windows.

## Baselines
Historically-best permutations (same embargo), equal-weight of all permutations, and SPY buy and hold, shown in the table above.

## Limitations
- Only ~{C.LOOKBACK_DAYS} days of macro data, so only about {len(res)} test periods. Confidence intervals on Sharpe are very wide.
- One instrument, daily bars, simple strategies. Event-time (intraday) effects are not captured.
- High-importance US events only. No transaction-cost sensitivity or slippage model beyond a flat cost.
- Out-of-sample on a single path: treat results as evidence about the pipeline, not as a deployable edge.
""")

if __name__ == "__main__":
    main()
