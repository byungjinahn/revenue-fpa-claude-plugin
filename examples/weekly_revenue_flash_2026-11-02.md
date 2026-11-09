# Weekly Revenue Flash — Mon 2 Nov 2026

**SAMPLE DATA — fictional company (Northwind DevTools).** Produced unattended by the scheduled `weekly-revenue-flash` workflow. Units: $K except usage ($).

**Headline:** The Q4 outlook is revenue 19,459.6 vs plan 19,317.4 (+0.7%) and billings +1.4%, but bookings are tracking -2.6% (-661.4) behind plan.

## Last quarter (Q3), closed
- Revenue 18,407.6 vs plan 18,493.1 (-0.5%). Billings +0.8%. Bookings 23,418.9 vs 24,626.6 (-4.9%).
- Largest miss: Enterprise bookings -2,284.6 (-16.5%).

## What moved (September)
1. **Enterprise subscription bookings -2,572.8 (-29.0%) vs plan**, and a pattern break (z = -4.61). *Hypothesis:* large deals slipped into Q4. **Owner:** Sales, to confirm slipped deals and their new close dates.
2. **Self-Serve usage revenue +134.9 (+27.0%)**, also a pattern break (z = +3.88). *Hypothesis:* a usage spike at one or two accounts (see Ember Games below). **Owner:** RevOps, to confirm whether it will recur.
3. **Mid-Market bookings +627.1 (+12.7%)**, which partly offsets the Enterprise miss.

## Usage outlook (Oct–Dec)
- Base 386,896. Range 351,990 (downside) to 423,251 (upside).
- **Shortfall risk:** Blue Harbor Bank is at 67% of its commit (breakage and renewal-downsell risk).
- **Expansion:** Dune Logistics (125%), Acme Robotics (119%) and Cobalt Health (104%) are over commit, so they are candidates for a larger commit.
- **Check before relying on it:** Ember Games consumption rose 33% month over month. Its growth is capped in the projection.

## Quarter-end deals at risk
- **D-1042 Helix Biotech** and **D-1044 Juniper Telecom** need 6 approvers each, and their terms include termination for convenience, MFN, free services and ramps. Start CFO, Legal and Revenue Accounting approvals this week.
- **D-1041 Granite Insurance** has a 35% discount (beyond the top tier). **D-1045 Kestrel Media** has monthly billing on a 30% discount.

## Asks by owner
- **Sales:** re-commit dates for the slipped September Enterprise deals. Open re-commit conversations with Dune, Acme and Cobalt.
- **RevOps:** confirm whether the Self-Serve usage spike (Ember Games) is a one-off.
- **Deal Desk:** start approvals for D-1042 and D-1044. Propose a smaller discount on a longer term for D-1041.
- **Revenue Accounting:** review ASC 606 treatment of the ramps and free services in D-1042 and D-1044, and the breakage estimate for Blue Harbor.

## Assumptions and data
Files: `sample-data/revenue_plan_forecast_actuals.csv`, `usage_history.csv`, `deals.csv`. Last closed month: 2026-09. Current quarter: 2026-Q4. Thresholds: ≥5% and ≥50; z ≥ 2.0. Every figure is taken from script output; causes are labeled as hypotheses.
