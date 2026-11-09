# Scheduled task: Weekly Revenue Pulse

Schedule: every Monday, 5:37 AM Pacific.

Prompt the task runs (each run starts fresh, so it is self-contained):

```
Run the revenue-fpa plugin's weekly-revenue-pulse skill for today's date, in demo mode,
and refresh the dashboard at <your Revenue Pulse dashboard URL>.
This runs unattended: do not ask questions. Use only figures from the scripts.
If the weekly-revenue-pulse skill is not available, stop and report that the
revenue-fpa plugin needs version 0.2.0 or later.
Finish with a short summary: week, headline, three asks, refresh status.
```

To set up your own: install the plugin, create a dashboard from Claude's Dashboard type, run the skill once by hand with that dashboard's URL so it writes the page, then create a weekly scheduled task with the prompt above.
