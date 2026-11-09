# Revenue FP&A plugin for Claude

A Claude plugin (works in Claude Cowork and Claude Code) that runs five everyday revenue-finance workflows, plus a scheduled workflow that chains them into a weekly CFO revenue flash. Python scripts compute the numbers, and Claude writes the commentary from those numbers.

| Skill | What it does | Ask Claude something like |
|---|---|---|
| `revenue-forecast-rollup` | Bookings, billings, and revenue vs plan by segment/product; drafts the CFO flash | "Roll up Q3 vs plan and draft the flash" |
| `forecast-variance` | Material variances vs plan and forecast, z-score anomaly detection, forecast accuracy (MAPE), driver hypotheses by owner | "Why did September miss?" |
| `consumption-revenue-model` | Driver-based usage revenue projection with downside/base/upside; commit shortfall (breakage), overage expansion, step-change flags; ASC 606 notes | "Project usage revenue for Q4 with scenarios" |
| `weekly-revenue-flash` | **Automated workflow:** runs all four skills unattended on a schedule and delivers a one-page CFO flash with owners and asks ([setup](workflows/weekly-revenue-flash.md), [example](examples/weekly_revenue_flash_2026-11-02.md)) | "Run the weekly revenue flash", or a Monday scheduled task |
| `weekly-revenue-pulse` | Runs the four checks together on a schedule: refreshes the week's data, writes the CFO takeaway and three owner-tagged asks, and refreshes a Revenue Pulse dashboard | Runs every Monday from a scheduled task |
| `arr-revenue-reconciliation` | Monthly: ARR by customer vs annualized GAAP revenue (monthly × 12), flags gaps > 10% with likely drivers (partial-month start, go-live delay, churn still in ARR, one-time fees, overage, credits, ramps), separates timing from fixes; runs on a schedule against Google Drive or a local folder | "Run the ARR vs revenue reconciliation" |
| `arr-revenue-recon` | ARR by customer vs annualized monthly GAAP revenue (x12); flags gaps over 10%, ARR-only and revenue-only customers, and name mismatches; drafts driver hypotheses by owner. Runs monthly as a scheduled task on a Google Drive folder | "Run the ARR vs revenue recon for October" |
| `deal-desk-review` | Checks deals against discount, payment-term, term-length, billing, ramp, overage-floor, and non-standard-term guardrails; routes approvals; flags ASC 606 and quarter-end timing risk; suggests counter-proposals | "Review the quarter-end deals against guardrails" |

## Automated weekly pulse

A scheduled Claude task runs every Monday at 5:37 AM Pacific with no one watching:

1. `simulate_week.py` produces the week's data (closed months fixed, open-month forecast and pipeline re-cut weekly). Swap in real exports or a CRM connector for production.
2. `pulse.py` runs the roll-up, variance, usage-model and deal-desk scripts and writes one data file per dashboard card.
3. Claude writes the takeaway and three asks (Deal desk, Sales, Billing) from those figures only.
4. Claude uploads the files and refreshes the **Northwind Revenue Pulse** dashboard, then reads the dashboard's own check.

The scheduled task's prompt is in [`automation/weekly-pulse-task.md`](automation/weekly-pulse-task.md).

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
python3 skills/arr-revenue-recon/scripts/recon.py sample-data/arr_by_customer_2026-10.csv sample-data/gaap_revenue_by_customer_2026-10.csv --month 2026-10
python3 skills/arr-revenue-reconciliation/scripts/arr_vs_revenue.py sample-data/arr_by_customer.csv sample-data/gaap_revenue_by_customer.csv --month 2026-10
```

## Monthly automation (Cowork scheduled task)

1. Create a folder on your computer, e.g. `ARR-Rev-Recon/`, with one subfolder per month (`2026-10/`) holding `arr_by_customer.csv` and `gaap_revenue_by_customer.csv`. See `sample-data/arr-rev-recon/`.
2. In Cowork, open **Scheduled → New task → Set up manually**. Choose the folder, set the frequency to **Weekly** (Cowork has no monthly option; the skill only runs in the first week of the month and skips months already reported), and use this prompt:

   > Use the revenue-fpa arr-revenue-reconciliation skill on this folder. Only run if today is between the 1st and 7th of the month. Compare ARR by customer with annualized GAAP revenue for the latest month, flag customers with a gap over 10%, and save the report with an investigation plan in the reports folder.

3. Each month, drop the two exports into a new month folder. The report appears in `reports/`.

## Install

**Claude (Cowork):** download `revenue-fpa.plugin` from [Releases](../../releases) and upload it as a plugin in Claude.

**Claude Code:**

```
/plugin marketplace add byungjinahn/revenue-fpa-claude-plugin
/plugin install revenue-fpa@byungjinahn-finance
```

## Monthly automation: ARR vs revenue recon

A scheduled Claude task runs on the 5th of each month. It reads the prior month's `ARR_by_Customer_YYYY-MM` and `GAAP_Revenue_by_Customer_YYYY-MM` files from one Google Drive folder (`ARR-Rev-Recon`), runs `arr-revenue-recon`, and writes `ARR_Rev_Recon_YYYY-MM` (detail sheet) and `ARR_Rev_Recon_Memo_YYYY-MM` (flagged customers and drivers) back to that same folder. The task is limited to that folder: it doesn't read, search or write anywhere else in Drive.

## Use with your own data

Export your forecast, usage, or deal data to CSV with the columns listed in each skill's `SKILL.md`. Claude maps differently named columns and confirms the mapping with you before running. Connect your CRM or warehouse through a connector and Claude can pull the extract itself.

## Roadmap

- Pull pipeline and closed-won data directly from Salesforce through a connector, replacing the weekly simulator
- Bridge chart (plan → actual) output for Board decks
- Price/volume/mix decomposition for pricing and packaging changes

## Disclaimer

All sample data is fictional. ASC 606 notes are planning-level guidance, not accounting advice.

## License

MIT © Byungjin Ahn
