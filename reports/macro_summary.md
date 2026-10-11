# Macro Outlook: week of 08 Oct 2026

## Snapshot
The US high-importance calendar covers **284 releases** over the window (14 Apr to 08 Oct 2026).
The surprise-based sentiment index (actual vs forecast, sign-adjusted so positive = supportive for risk assets)
is **improving** over the last month (cumulative +12.6 vs +7.2 a month ago).

## Largest recent positive surprises
- Sep 23: **S&P Global Manufacturing PMI (Sep)** actual 57 vs forecast 53.6
- Sep 23: **S&P Global Services PMI (Sep)** actual 58.7 vs forecast 55.8
- Sep 16: **Core Retail Sales (MoM) (Aug)** actual 1.4 vs forecast 0.6

## Largest recent negative surprises
- Sep 29: **CB Consumer Confidence (Sep)** actual 81.9 vs forecast 89.2
- Sep 30: **Core PCE Price Index (YoY) (Aug)** actual 3 vs forecast 3.3
- Oct 02: **Average Hourly Earnings (MoM) (Sep)** actual 0.1 vs forecast 0.3

## What the news flow says (Tavily)
- [4 Reasons to Think US Inflation Will Come Back Down](https://global.morningstar.com/en-nd/economy/4-reasons-think-us-inflation-will-come-back-down)
- [Inflation stayed hot in August with annual pace of 3.4%, raising the odds of a Fed hike - CBS News](https://www.cbsnews.com/news/august-cpi-report-inflation-fed-rates)
- [CPI inflation report August 2026:](https://www.cnbc.com/2026/09/11/cpi-inflation-report-august-2026.html)
- [Elevated Inflation Keeps Pressure on Fed to Raise Interest Rates - The New York Times](https://www.nytimes.com/live/2026/09/11/business/inflation-cpi-report)
- [US Core CPI Up More Than Forecast, Bolstering Case for Hike - Bloomberg](https://www.bloomberg.com/news/articles/2026-09-11/us-core-cpi-rises-more-than-forecast-bolstering-case-for-hike)
- [Federal Reserve expected to hike interest rates 25 basis points at FOMC meeting | Fox Business](https://www.foxbusiness.com/economy/stubborn-inflation-sets-stage-federal-reserve-hike-interest-rates)
- [WATCH: Warsh says 'inflation is too high' after Fed raises interest rate 1st time in 3 years | PBS News](https://www.pbs.org/newshour/economy/watch-live-warsh-holds-briefing-after-fed-meeting-as-interest-rates-expected-to-rise)
- [Michael Barr says Fed will likely raise interest rates to fight inflation](https://thehill.com/business/6107670-fed-governor-barr-rate-hike)

## Implication for strategy selection
The model's top permutations for the coming 5 trading days:
- `ma_cross_20_30_long_short` (predicted 5-day P&L -0.40%)
- `breakout_40_0_long_short` (predicted 5-day P&L -0.59%)
- `breakout_40_0_long_only` (predicted 5-day P&L -0.59%)

*Method:* surprise = actual - forecast, scaled by the expanding mean absolute surprise of the same release
(past data only), clipped to +/-3, inverted for releases where a higher print is negative (unemployment, claims, CPI).
Template-generated from data; read the headlines for qualitative context before relying on it.
