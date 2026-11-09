---
name: consumption-revenue-model
description: Builds a driver-based consumption (usage-based) revenue projection with downside, base, and upside scenarios from customer usage history, and flags commit shortfalls, overage expansion, and step-changes. Use when the user asks to forecast usage-based or consumption revenue, model commits and overages, run usage scenarios, or assess breakage and expansion risk.
---

# Consumption revenue model

## Inputs

CSV columns: `month, customer, segment, committed_units, consumed_units, unit_price, overage_price`. `committed_units = 0` means pay-as-you-go. Sample: `../../sample-data/usage_history.csv` (relative to this skill's base directory) (fictional, $).

## Steps

1. Confirm the pricing mechanics match the script's assumption (monthly minimum commit at `unit_price`, overage above commit at `overage_price`, PAYG at `overage_price`). If the user's contracts differ (annual prepaid drawdown, tiered rates, rollover), say what changes and adjust the `charge()` function before running.
2. Run from this skill's base directory:
   `python3 scripts/consumption_model.py <usage.csv> --months 3 --window 6 --scenarios 0.5,1.0,1.5 --growth-cap 0.10`
3. Present:
   - Scenario table (monthly and total), with the growth multiplier for each scenario stated.
   - Top customers driving the base case.
   - Flags, grouped: **shortfall/breakage risk** (below 85% of commit), **expansion** (above 100% of commit → re-commit conversation), **step-changes** (capped growth, >25% MoM jumps — confirm whether one-off before projecting).
4. Translate to decisions: which accounts Sales should approach for a larger commit, which are renewal-downsell risks, and how much of the base case depends on the one or two fastest-growing customers (concentration).
5. Add the revenue-recognition caveats from `references/asc606-notes.md` that apply to the user's contract types. The script's output equals billings; say where recognized revenue could differ.

## Guardrails

- Growth is fit on trailing data; state the window and that seasonality is not modeled.
- Never extrapolate a capped or step-change customer without saying so.
