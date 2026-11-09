---
name: weekly-revenue-flash
description: Runs the full weekly revenue review end to end (forecast roll-up, variance and anomaly scan, consumption outlook, and quarter-end deal-desk risk) and assembles a one-page CFO revenue flash with owners and asks. Built to run unattended as a scheduled task. Use when the user asks for the weekly revenue flash, the Monday revenue review, a full revenue pack, or to automate revenue reporting.
---

# Weekly revenue flash (automated workflow)

Chain the four revenue-fpa skills into one pack. This skill is designed to run as a scheduled task with nobody watching: do not stop to ask questions. Use the defaults below, state any assumption in the flash's "Assumptions" line, and finish.

## Inputs and defaults

- Data folder: the user's attached or connected files if present. Otherwise use the plugin samples at `../../sample-data/` (relative to this skill's base directory) and label the flash **"SAMPLE DATA — fictional company"**.
- Current quarter: the latest quarter containing an open month in the forecast file. Last closed month: the latest month with actuals.
- Thresholds: variance ≥ 5% and ≥ 50 (file units); anomaly z ≥ 2.0; consumption outlook 3 months.

## Steps

Run every script from the matching skill's base directory, which is a sibling of this one (`../<skill>/scripts/...`). Capture each output verbatim.

1. **Last quarter closed:** `python3 ../revenue-forecast-rollup/scripts/rollup.py <forecast.csv> --period <last closed quarter> --by segment`
2. **Current quarter outlook:** the same command with `--period <current quarter>`.
3. **Variance and anomalies:** `python3 ../forecast-variance/scripts/variance.py <forecast.csv> --month <last closed month>`
4. **Consumption outlook:** `python3 ../consumption-revenue-model/scripts/consumption_model.py <usage.csv> --months 3`
5. **Deal-desk risk:** `python3 ../deal-desk-review/scripts/deal_check.py <deals.csv>`
6. If a script fails or a file is missing, skip that section, write "Not run: <reason>" in its place, and continue.

## Assemble the flash

Write `revenue_flash_<YYYY-MM-DD>.md` (and send it to the user) using exactly these sections. Every number must appear in a script output from steps 1–5. Do not calculate new figures.

1. **Headline**: one sentence on the current-quarter outlook vs plan (revenue, billings, bookings).
2. **Last quarter, closed**: totals vs plan and the largest segment variance.
3. **What moved**: up to 3 material variances or anomalies, each with its likely driver (marked as a hypothesis) and the owner to confirm it.
4. **Usage outlook**: base-case 3-month total with its downside–upside range; commit-shortfall and expansion accounts.
5. **Quarter-end deals at risk**: deals with 4+ approvers or non-standard terms, and the approvals to start this week.
6. **Asks by owner**: Sales, RevOps, Deal Desk, Revenue Accounting. One line each.
7. **Assumptions and data**: files used, periods, thresholds, and the run timestamp.

Keep it to one page. Write it for a CFO reading on a phone.
