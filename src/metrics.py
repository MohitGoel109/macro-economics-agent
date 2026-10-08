import numpy as np
import pandas as pd

def sharpe(r, periods_per_year, rf=0.0):
    r = pd.Series(r).dropna()
    return float((r.mean() - rf) / r.std(ddof=1) * np.sqrt(periods_per_year)) if len(r) > 2 and r.std() > 0 else float("nan")

def sortino(r, periods_per_year, rf=0.0):
    r = pd.Series(r).dropna()
    dd = np.sqrt((np.minimum(r - rf, 0) ** 2).mean())
    return float((r.mean() - rf) / dd * np.sqrt(periods_per_year)) if dd > 0 else float("nan")

def max_drawdown(r):
    eq = (1 + pd.Series(r).dropna()).cumprod()
    return float((eq / eq.cummax() - 1).min())

def summary(r, periods_per_year):
    r = pd.Series(r).dropna()
    return {"periods": int(len(r)), "total_return": float((1 + r).prod() - 1),
            "mean_period_return": float(r.mean()), "hit_rate": float((r > 0).mean()),
            "sharpe": sharpe(r, periods_per_year), "sortino": sortino(r, periods_per_year),
            "max_drawdown": max_drawdown(r)}
