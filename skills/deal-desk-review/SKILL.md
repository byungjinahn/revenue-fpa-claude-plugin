---
name: deal-desk-review
description: Reviews deals against deal-desk guardrails (discount tiers, payment terms, contract length, billing frequency, ramps, usage commits and overage floors, non-standard terms), routes approvals, and flags ASC 606 and quarter-end timing risks. Use when the user asks to review a deal, check a quote or order form against policy, route approvals, prepare deal-desk notes, or scan the quarter-end pipeline for non-standard deals.
---

# Deal-desk guardrail review

## Inputs

- Deals CSV: `deal_id, customer, segment, close_date, list_acv, net_acv, term_months, payment_terms_days, billing_frequency, ramp, usage_commit_units, overage_price, non_standard_terms`. Sample: `../../sample-data/deals.csv` (relative to this skill's base directory).
- If the user pastes a single quote or order form instead, extract these fields into a one-row CSV, show the extraction, and ask the user to confirm it before running.
- Guardrails: `references/guardrails.json` (example approval matrix). If the user has a real policy, edit a copy and pass `--guardrails`.

## Steps

1. Run from this skill's base directory:
   `python3 scripts/deal_check.py <deals.csv> [--deal <id>] [--guardrails <path>]`
2. For each deal, write a deal-desk note:
   - **Economics**: net ACV, discount vs list, TCV, billing and payment terms → cash timing (days to cash vs a standard annual-upfront, net-30 deal).
   - **Approvals**: the routed chain from the script, in order.
   - **Revenue/ASC 606 flags**: ramps, separate performance obligations (free services), termination for convenience (can shorten the enforceable contract term), usage commits (variable consideration, breakage).
   - **Counter-proposal**: one or two trades that keep the deal inside guardrails, e.g., swap a deeper discount for a longer term at a smaller discount, annual-upfront billing, a higher commit with a lower overage rate, or removing an MFN in exchange for a price lock.
3. For a pipeline scan, rank deals by approval burden and quarter-end proximity and list the approvals to start now.

## Guardrails

- The thresholds are examples; never present them as the user's company policy unless the user supplied them.
- Planning-level ASC 606 flags only; route final treatment to Revenue Accounting.
