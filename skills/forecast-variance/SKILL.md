---
name: forecast-variance
description: Explains forecast misses and finds anomalies in bookings, billings, and revenue actuals versus plan and forecast, with materiality thresholds and forecast-accuracy tracking. Use when the user asks why the forecast missed, for a variance analysis, month-end or quarter-end variance commentary, anomaly detection, or forecast accuracy (MAPE).
---

# Forecast variance and anomaly detection

## Inputs

Same CSV shape as `revenue-forecast-rollup`: `month, segment, product, metric, plan, forecast, actual`. Sample: `../../sample-data/revenue_plan_forecast_actuals.csv` (relative to this skill's base directory).

## Steps

1. Confirm the closed month to analyze and the materiality gate. Defaults: |variance| ≥ 5% **and** ≥ 50 (file units). Ask only if the user's scale makes the default absurd.
2. Run from this skill's base directory:
   `python3 scripts/variance.py <data.csv> --month <YYYY-MM> --threshold-pct 5 --threshold-abs 50 --z 2.0`
3. Separate the two signals the script prints:
   - **Plan/forecast variances** — material misses this month.
   - **Pattern breaks** — lines whose actual/plan ratio departs from their own trailing history (z-score). A pattern break with a small $ variance is still worth a question; a large variance that is not a pattern break often reflects a known plan issue.
4. For each material item write: what happened ($, %, vs plan and vs forecast) → candidate drivers → the evidence that would confirm each → owner to ask. Use this driver taxonomy:
   - Bookings: deal slippage/timing, win rate, deal size, discounting, pipeline coverage.
   - Billings: billing frequency or payment-term changes, ramp deals, invoicing timing, collections holds.
   - Revenue: consumption/usage swings, start-date delays, ASC 606 timing (ramps, services POBs, variable consideration), churn/contraction.
5. Forecast accuracy: report the worst-MAPE lines and suggest one process fix each (e.g., commit-category discipline for bookings, usage telemetry feed for consumption lines).
6. Do not state a cause as fact unless the user provided it. Mark hypotheses.

## Output

A variance memo: summary line, table of material items, pattern breaks, accuracy section, open questions by owner (Sales, RevOps, Deal Desk, Revenue Accounting).
