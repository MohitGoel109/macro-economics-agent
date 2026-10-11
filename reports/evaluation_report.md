# Evaluation Report

Walk-forward window: 2026-06-17 to 2026-09-28, 15 non-overlapping 5-day periods.
Sharpe/Sortino annualised with 50.4 periods/year, risk-free = 0.

|Strategy|Total return|Sharpe|Sortino|Max drawdown|Hit rate|
|-|-|-|-|-|-|
|model|+0.3%|0.16|0.26|-4.9%|53%|
|hist\_best|+3.5%|1.22|2.39|-2.2%|53%|
|equal\_weight|-0.9%|-0.44|-0.59|-2.6%|47%|
|spy\_buy\_hold|+5.1%|1.69|3.43|-2.1%|60%|

Model diagnostics: mean cross-sectional rank IC = 0.155, pred/actual correlation = 0.062, MAE = 1.3274%.
## Results

The model did not beat the baselines over this window. Its Sharpe of 0.16 compares with 1.22 for the

historically-best permutations and 1.69 for SPY buy-and-hold, and its max drawdown (-4.9%) was the

deepest of the four. Predicted and actual 5-day P\&L are essentially uncorrelated (0.06), and the

cross-sectional rank IC of 0.155 is a weak positive that I would not rely on.



With 15 non-overlapping periods, the standard error of an annualised Sharpe ratio is roughly 1.8, so

none of these Sharpe differences is statistically distinguishable from zero or from each other. I did

not tune the model after seeing these results. One change was made after inspecting the strategy-vs-event

heatmap: weekly jobless claims had been mislabelled as employment events and were removed from that group.

## Method

* **Trading logs:** 24 permutations (MA crossover and breakout, long-only and long-short) backtested on SPY daily bars, 2 bps cost per position change.
* **Target:** P\&L of each permutation over the next 5 trading days.
* **Model:** LightGBM regressor on permutation parameters, trailing P\&L, macro-surprise, calendar-distance and volatility features.
* **Selection:** at each rebalance, trade the top 3 permutations by predicted P\&L.

## Avoiding data leakage

1. Walk-forward, expanding window, no shuffling: training only uses data before each test date.
2. **Embargo of 5 days:** a training row's target spans t+1..t+5, so rows are only used if their target window ended on or before the test date.
3. Strategy positions use the signal at close t and earn returns from t+1.
4. Surprise z-scores are scaled by *past* surprises only (expanding, shifted by one).
5. Trailing P\&L features use only past days. Calendar "days until next event" uses the publicly scheduled release dates.
6. Evaluation periods are non-overlapping, so Sharpe is not inflated by overlapping windows.

## Baselines

Historically-best permutations (same embargo), equal-weight of all permutations, and SPY buy and hold, shown in the table above.

## Limitations

* Only \~180 days of macro data, so only about 15 test periods. Confidence intervals on Sharpe are very wide.
* One instrument, daily bars, simple strategies. Event-time (intraday) effects are not captured.
* High-importance US events only. No transaction-cost sensitivity or slippage model beyond a flat cost.
* Out-of-sample on a single path: treat results as evidence about the pipeline, not as a deployable edge.

