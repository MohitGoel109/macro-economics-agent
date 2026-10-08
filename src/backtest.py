"""Generate the 'trading logs': daily P&L for every strategy permutation on SPY.

Permutations (24 total):
  - MA crossover : fast in {5,10,20} x slow in {30,50,100} x mode {long_only,long_short}   (18)
  - Breakout     : lookback in {10,20,40} x mode {long_only,long_short}                     (6)
Signal uses the close of day t; the position is earned on day t+1 (no look-ahead).
"""
import itertools
import numpy as np
import pandas as pd
from src.config import TRADING_COST

def permutations():
    p = []
    for f, s, m in itertools.product([5, 10, 20], [30, 50, 100], ["long_only", "long_short"]):
        p.append(dict(strategy="ma_cross", p1=f, p2=s, mode=m))
    for n, m in itertools.product([10, 20, 40], ["long_only", "long_short"]):
        p.append(dict(strategy="breakout", p1=n, p2=0, mode=m))
    for q in p:
        q["perm_id"] = f"{q['strategy']}_{q['p1']}_{q['p2']}_{q['mode']}"
    return p

def _position(close, q):
    if q["strategy"] == "ma_cross":
        sig = np.sign(close.rolling(q["p1"]).mean() - close.rolling(q["p2"]).mean())
    else:
        n = q["p1"]
        up, dn = close > close.shift(1).rolling(n).max(), close < close.shift(1).rolling(n).min()
        sig = pd.Series(np.nan, index=close.index)
        sig[up], sig[dn] = 1.0, -1.0
        sig = sig.ffill().fillna(0.0)
    if q["mode"] == "long_only":
        sig = sig.clip(lower=0)
    return sig.fillna(0.0)

def run(close: pd.Series) -> pd.DataFrame:
    """Return long table: date, perm_id, params, pos, daily_pnl."""
    ret = close.pct_change().fillna(0.0)
    out = []
    for q in permutations():
        pos = _position(close, q)
        pnl = pos.shift(1).fillna(0.0) * ret - TRADING_COST * pos.diff().abs().shift(1).fillna(0.0)
        out.append(pd.DataFrame({"date": close.index, **q, "pos": pos.values, "daily_pnl": pnl.values}))
    return pd.concat(out, ignore_index=True)
