"""Charts -> outputs/charts/*.png"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.config import CHARTS

COL = {"CPI": "#c0392b", "FOMC": "#1f4e79", "EMPLOYMENT": "#2e8b57"}
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False})

def sentiment_timeline(ev, daily):
    d = daily.loc[daily.index >= ev.date.min()]
    fig, ax = plt.subplots(2, 1, figsize=(11, 6), sharex=True, gridspec_kw={"height_ratios": [3, 2]})
    ax[0].plot(d.index, d.sentiment_cum, color="#222", lw=1.8, label="Cumulative surprise sentiment")
    ax[0].plot(d.index, d.sentiment_idx * 10, color="#e67e22", lw=1, label="EWM sentiment x10 (halflife 10d)")
    ax[0].axhline(0, color="#999", lw=.6)
    for fam, c in COL.items():
        for x in ev.loc[ev.family == fam, "date"].unique():
            ax[0].axvline(x, color=c, alpha=.12, lw=1)
    ax[0].set_title("Macro sentiment over time (positive surprise = supportive for risk assets)")
    ax[0].legend(frameon=False, loc="upper left")
    ax[1].bar(d.index, d.net_sentiment, color=np.where(d.net_sentiment >= 0, "#2e8b57", "#c0392b"), width=1.0)
    ax[1].set_title("Daily net surprise score"); fig.tight_layout()
    fig.savefig(CHARTS / "sentiment_timeline.png"); plt.close(fig)

def heatmap(panel):
    p = panel[panel.target_pnl.notna()].copy()
    p["family"] = p.strategy + "|" + p["mode"] + "|" + p.p1.astype(str)
    piv = p.groupby(["family", "fwd_event_type"]).target_pnl.mean().unstack() * 100
    piv = piv[[c for c in ["NONE", "CPI", "EMPLOYMENT", "FOMC"] if c in piv.columns]]
    fig, ax = plt.subplots(figsize=(7.5, 8))
    v = np.nanmax(np.abs(piv.values))
    im = ax.imshow(piv.values, cmap="RdYlGn", vmin=-v, vmax=v, aspect="auto")
    ax.set_xticks(range(piv.shape[1])); ax.set_xticklabels(piv.columns)
    ax.set_yticks(range(piv.shape[0])); ax.set_yticklabels(piv.index, fontsize=7)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            if not np.isnan(piv.values[i, j]):
                ax.text(j, i, f"{piv.values[i, j]:.2f}", ha="center", va="center", fontsize=6)
    ax.set_title("Mean next-5-day P&L (%) by strategy vs upcoming event type")
    fig.colorbar(im, ax=ax, shrink=.6); fig.tight_layout()
    fig.savefig(CHARTS / "strategy_event_heatmap.png"); plt.close(fig)

def equity(res):
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    for c, lab, col in [("model", "Model (top-3 predicted)", "#1f4e79"), ("hist_best", "Historically-best baseline", "#e67e22"),
                        ("equal_weight", "Equal-weight all permutations", "#7f8c8d"), ("spy_buy_hold", "SPY buy & hold", "#c0392b")]:
        eq = (1 + res[c]).cumprod(); ax[0].plot(eq.index, eq, label=lab, color=col, lw=1.8 if c == "model" else 1.2)
        ax[1].plot(eq.index, eq / eq.cummax() - 1, color=col, lw=1.2)
    ax[0].set_title("Walk-forward equity (non-overlapping 5-day periods)"); ax[0].legend(frameon=False, fontsize=8)
    ax[1].set_title("Drawdown"); fig.tight_layout(); fig.savefig(CHARTS / "equity_curves.png"); plt.close(fig)

def pred_vs_actual(preds):
    fig, ax = plt.subplots(figsize=(5.5, 5))
    ax.scatter(preds.pred * 100, preds.target_pnl * 100, s=6, alpha=.35, color="#1f4e79")
    lim = max(abs(preds.pred).max(), abs(preds.target_pnl).max()) * 100
    ax.plot([-lim, lim], [-lim, lim], color="#999", lw=.8); ax.axhline(0, lw=.4, color="#999"); ax.axvline(0, lw=.4, color="#999")
    ax.set_xlabel("Predicted 5-day P&L (%)"); ax.set_ylabel("Actual 5-day P&L (%)"); ax.set_title("Out-of-sample predicted vs actual")
    fig.tight_layout(); fig.savefig(CHARTS / "pred_vs_actual.png"); plt.close(fig)

def importance(imp):
    fig, ax = plt.subplots(figsize=(6, 6)); imp.head(15)[::-1].plot.barh(ax=ax, color="#1f4e79")
    ax.set_title("Feature importance (final model, split count)"); fig.tight_layout()
    fig.savefig(CHARTS / "feature_importance.png"); plt.close(fig)

def all(ev, daily, panel, res, preds, imp):
    sentiment_timeline(ev, daily); heatmap(panel); equity(res); pred_vs_actual(preds); importance(imp)
