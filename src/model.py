"""Expanding-window walk-forward validation (no shuffling, embargo = HORIZON days).

At each rebalance date t (every HORIZON trading days after MIN_TRAIN_DAYS):
  * train only on rows whose 5-day target window ended on/before t  (date index <= i - HORIZON)
  * predict next-5-day P&L for all 24 permutations, trade the TOP_K highest predictions
  * realised P&L = mean actual target of those permutations (non-overlapping periods)
Baselines: (a) historically-best permutation (same embargo), (b) equal-weight all permutations, (c) SPY buy&hold.
"""
import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.stats import spearmanr
from src.config import HORIZON, TOP_K, MIN_TRAIN_DAYS, PERIODS_PER_YEAR
from src import metrics

FEATURES = ["p1", "p2", "is_ma", "is_long_short", "pos", "trailing_5", "trailing_20",
            "n_events", "net_sentiment", "sentiment_idx", "sentiment_cum", "sentiment_5d",
            "first_event_hour_est", "dow", "month_day",
            "days_to_fomc", "days_since_fomc", "days_to_cpi", "days_since_cpi",
            "days_to_employment", "days_since_employment",
            "spy_ret_1d", "spy_ret_5d", "spy_vol_10d", "spy_vol_20d", "spy_dd_20d"]

PARAMS = dict(n_estimators=150, learning_rate=0.03, num_leaves=6, min_child_samples=40,
              subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=5.0,
              random_state=42, verbose=-1)

def prep(panel):
    p = panel.copy()
    p["is_ma"] = (p.strategy == "ma_cross").astype(int)
    p["is_long_short"] = (p["mode"] == "long_short").astype(int)
    return p

def walk_forward(panel: pd.DataFrame, spy_close: pd.Series):
    p = prep(panel)
    dates = sorted(p.loc[p.target_pnl.notna(), "date"].unique())
    rows, preds = [], []
    for i in range(MIN_TRAIN_DAYS, len(dates), HORIZON):
        t = dates[i]
        train = p[(p.date <= dates[i - HORIZON]) & p.target_pnl.notna()]
        test = p[p.date == t].copy()
        if len(train) < 200 or test.empty:
            continue
        m = lgb.LGBMRegressor(**PARAMS).fit(train[FEATURES], train["target_pnl"])
        test["pred"] = m.predict(test[FEATURES])
        top = test.nlargest(TOP_K, "pred")
        hist = train.groupby("perm_id")["target_pnl"].mean()
        best_hist = hist.nlargest(TOP_K).index
        spy_5d = spy_close.shift(-HORIZON).loc[t] / spy_close.loc[t] - 1
        ic = spearmanr(test["pred"], test["target_pnl"])[0] if test["target_pnl"].nunique() > 1 and test["pred"].nunique() > 1 else np.nan
        rows.append(dict(date=t, model=top.target_pnl.mean(),
                         hist_best=test[test.perm_id.isin(best_hist)].target_pnl.mean(),
                         equal_weight=test.target_pnl.mean(), spy_buy_hold=spy_5d,
                         chosen=",".join(top.perm_id), rank_ic=ic))
        preds.append(test[["date", "perm_id", "pred", "target_pnl"]])
    res = pd.DataFrame(rows).set_index("date")
    pr = pd.concat(preds)
    final = lgb.LGBMRegressor(**PARAMS).fit(p[p.target_pnl.notna()][FEATURES], p[p.target_pnl.notna()]["target_pnl"])
    imp = pd.Series(final.feature_importances_, index=FEATURES).sort_values(ascending=False)
    latest = p[p.date == p.date.max()].copy()
    latest["pred"] = final.predict(latest[FEATURES])
    return res, pr, imp, latest.sort_values("pred", ascending=False)

def evaluate(res, preds):
    out = {c: metrics.summary(res[c], PERIODS_PER_YEAR) for c in ["model", "hist_best", "equal_weight", "spy_buy_hold"]}
    out["model"]["mean_rank_ic"] = float(res["rank_ic"].mean())
    out["model"]["pred_corr"] = float(np.corrcoef(preds.pred, preds.target_pnl)[0, 1])
    out["model"]["mae"] = float((preds.pred - preds.target_pnl).abs().mean())
    return out
