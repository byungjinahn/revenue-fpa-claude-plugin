# Revenue FP&A plugin for Claude

A Claude plugin (works in Claude Cowork and Claude Code) that runs four everyday revenue-finance workflows. Python scripts compute the numbers, and Claude writes the commentary from those numbers.

| Skill | What it does | Ask Claude something like |
|---|---|---|
| `revenue-forecast-rollup` | Bookings, billings, and revenue vs plan by segment/product; drafts the CFO flash | "Roll up Q3 vs plan and draft the flash" |
| `forecast-variance` | Material variances vs plan and forecast, z-score anomaly detection, forecast accuracy (MAPE), driver hypotheses by owner | "Why did September miss?" |
| `consumption-revenue-model` | Driver-based usage revenue projection with downside/base/upside; commit shortfall (breakage), overage expansion, step-change flags; ASC 606 notes | "Project usage revenue for Q4 with scenarios" |
| `deal-desk-review` | Checks deals against discount, payment-term, term-length, billing, ramp, overage-floor, and non-standard-term guardrails; routes approvals; flags ASC 606 and quarter-end timing risk; suggests counter-proposals | "Review the quarter-end deals against guardrails" |

## Design principles

- **Numbers come from code, not the model.** Every figure in Claude's write-up is printed by a script first, so it can be checked and reproduced.
- **Hypotheses are labeled.** Variance drivers are hypotheses with the evidence that would confirm them and the owner to ask.
- **Materiality first.** Variances are gated on both % and $ so commentary focuses on what matters.
- **Policy is configuration.** Deal guardrails live in `skills/deal-desk-review/references/guardrails.json`, so you can swap in a real approval matrix without touching code.

## Try it with sample data

`sample-data/` holds a fictional dev-tools SaaS company ("Northwind DevTools") with subscription and usage revenue, nine closed months, and planted stories for the skills to find: Enterprise bookings slipping at quarter end, a self-serve usage spike, an under-consuming committed customer, and deals that break guardrails. Regenerate the data with `python3 sample-data/generate.py`.

Sample outputs are in [`examples/`](examples/).

Run the scripts directly (Python 3.9+, standard library only):

```bash
python3 skills/revenue-forecast-rollup/scripts/rollup.py sample-data/revenue_plan_forecast_actuals.csv --period 2026-Q3
python3 skills/forecast-variance/scripts/variance.py sample-data/revenue_plan_forecast_actuals.csv --month 2026-09
python3 skills/consumption-revenue-model/scripts/consumption_model.py sample-data/usage_history.csv --months 3
python3 skills/deal-desk-review/scripts/deal_check.py sample-data/deals.csv
```

## Install

**Claude (Cowork):** download `revenue-fpa.plugin` from [Releases](../../releases) and upload it as a plugin in Claude.

**Claude Code:**

```
/plugin marketplace add byungjinahn/revenue-fpa-claude-plugin
/plugin install revenue-fpa@byungjinahn-finance
```

## Use with your own data

Export your forecast, usage, or deal data to CSV with the columns listed in each skill's `SKILL.md`. Claude maps differently named columns and confirms the mapping with you before running. Connect your CRM or warehouse through a connector and Claude can pull the extract itself.

## Roadmap

- Pull pipeline and closed-won data directly from Salesforce through a connector
- Bridge chart (plan → actual) output for Board decks
- Price/volume/mix decomposition for pricing and packaging changes

## Disclaimer

All sample data is fictional. ASC 606 notes are planning-level guidance, not accounting advice.

## License

MIT © Byungjin Ahn
