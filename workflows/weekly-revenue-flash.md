# Automated workflow: Weekly Revenue Flash

Each Monday, Claude runs the full revenue review on its own and delivers a one-page CFO flash. Nobody has to prompt it.

```
Scheduled task (Mon 7:40am)
   └─ weekly-revenue-flash skill
        ├─ revenue-forecast-rollup  → last quarter closed + current quarter outlook
        ├─ forecast-variance        → material misses + anomalies (z-score)
        ├─ consumption-revenue-model→ 3-month usage outlook, shortfall/expansion flags
        └─ deal-desk-review         → quarter-end deals needing approvals now
   └─ revenue_flash_<date>.md delivered (and optionally posted to Slack or email)
```

## Set it up in Claude (Cowork), about 2 minutes

1. Install this plugin (see the main README).
2. Open the Cowork tab and ask Claude:

   > Create a scheduled task that runs every Monday at 7:40am Pacific: "Run the weekly revenue flash using the revenue-fpa plugin and send me the flash."

   Or create it yourself in Claude's scheduled tasks with this prompt:

   ```
   Run the revenue-fpa weekly-revenue-flash skill. Use my attached revenue files if
   available, otherwise the plugin's sample data. Do not ask questions; state
   assumptions in the flash. Deliver revenue_flash_<date>.md.
   ```
3. To use real data, connect your CRM or data warehouse, or drop weekly CSV exports into a connected folder, and name that folder in the task prompt.

## Why it's built this way

- **Runs with nobody watching:** the skill never waits for answers. It states its assumptions and skips a failing section rather than stopping.
- **Numbers you can trust:** every figure comes from a script, and Claude writes only the narrative.
- **Accountability:** every flagged item ends with an owner and an ask.

Example output: [`examples/weekly_revenue_flash_2026-11-02.md`](../examples/weekly_revenue_flash_2026-11-02.md)
