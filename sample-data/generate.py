"""Generate synthetic sample data for a fictional dev-tools SaaS company ("Northwind DevTools").

All figures are invented. Re-run to regenerate: python3 sample-data/generate.py
Outputs (in this folder):
  revenue_plan_forecast_actuals.csv  monthly plan / forecast / actual by segment, product, metric
  usage_history.csv                  monthly committed vs consumed units for usage customers
  deals.csv                          open quarter-end deals for deal-desk review
"""
import csv
import math
import random
from pathlib import Path

random.seed(42)
HERE = Path(__file__).parent
MONTHS = [f"2026-{m:02d}" for m in range(1, 13)]
CLOSED = MONTHS[:9]  # Jan-Sep actuals closed; Oct-Dec forecast only

SEGMENTS = {
    # segment: (subscription revenue base $K/month, usage revenue base $K/month, monthly growth)
    "Enterprise": (2400, 600, 0.012),
    "Mid-Market": (1300, 350, 0.015),
    "Self-Serve": (500, 420, 0.022),
}


def rows_plan():
    out = []
    for seg, (sub, use, g) in SEGMENTS.items():
        for i, m in enumerate(MONTHS):
            q_end = (i + 1) % 3 == 0
            for product, base in (("Subscription", sub), ("Usage", use)):
                plan_rev = base * (1 + g) ** i
                # billings: annual-upfront heavy in Enterprise, lumpy at quarter end
                bill_mult = {"Enterprise": 1.9 if q_end else 0.6, "Mid-Market": 1.3 if q_end else 0.85, "Self-Serve": 1.0}[seg]
                plan_bill = plan_rev * (bill_mult if product == "Subscription" else 1.0)
                plan_book = plan_rev * 12 * (0.28 if q_end else 0.08) if product == "Subscription" else 0.0
                for metric, plan in (("bookings", plan_book), ("billings", plan_bill), ("revenue", plan_rev)):
                    if plan == 0:
                        continue
                    noise = random.gauss(0, 0.03 if metric == "revenue" else 0.08)
                    fcst = plan * (1 + noise * 0.6)
                    actual = ""
                    if m in CLOSED:
                        a = plan * (1 + noise)
                        # planted stories for the variance skill to find
                        if seg == "Enterprise" and metric == "bookings" and m == "2026-09":
                            a = plan * 0.71  # two large deals slipped to Q4
                        if seg == "Self-Serve" and product == "Usage" and metric == "revenue" and m in ("2026-08", "2026-09"):
                            a = plan * (1.18 if m == "2026-08" else 1.27)  # usage spike
                        if seg == "Mid-Market" and metric == "billings" and m == "2026-06":
                            a = plan * 0.80  # move from annual to quarterly invoicing
                        actual = round(a, 1)
                    out.append({
                        "month": m, "segment": seg, "product": product, "metric": metric,
                        "plan": round(plan, 1), "forecast": round(fcst, 1), "actual": actual,
                    })
    return out


def rows_usage():
    out = []
    customers = [
        ("Acme Robotics", "Enterprise", 2_000_000, 0.004, 0.035),
        ("Blue Harbor Bank", "Enterprise", 3_500_000, 0.003, 0.032),
        ("Cobalt Health", "Mid-Market", 900_000, 0.006, 0.042),
        ("Dune Logistics", "Mid-Market", 600_000, 0.005, 0.045),
        ("Ember Games", "Self-Serve", 0, 0.0, 0.050),
        ("Fjord Analytics", "Self-Serve", 0, 0.0, 0.050),
    ]
    for name, seg, commit, unit, overage in customers:
        level = (commit or 400_000) * random.uniform(0.75, 0.95)
        trend = random.uniform(0.01, 0.05)
        if name == "Blue Harbor Bank":
            level, trend = commit * 0.70, -0.01  # under-consuming its commit
        for i, m in enumerate(CLOSED):
            if name == "Ember Games" and i >= 7:
                level *= 1.35  # step-change: new product launch
            consumed = level * (1 + trend) ** i * random.uniform(0.95, 1.05)
            out.append({
                "month": m, "customer": name, "segment": seg,
                "committed_units": commit, "consumed_units": int(consumed),
                "unit_price": unit, "overage_price": overage,
            })
    return out


def rows_deals():
    return [
        {"deal_id": "D-1041", "customer": "Granite Insurance", "segment": "Enterprise", "close_date": "2026-12-19",
         "list_acv": 480000, "net_acv": 312000, "term_months": 36, "payment_terms_days": 30, "billing_frequency": "annual",
         "ramp": "N", "usage_commit_units": 0, "overage_price": "", "non_standard_terms": ""},
        {"deal_id": "D-1042", "customer": "Helix Biotech", "segment": "Enterprise", "close_date": "2026-12-23",
         "list_acv": 260000, "net_acv": 221000, "term_months": 24, "payment_terms_days": 90, "billing_frequency": "quarterly",
         "ramp": "Y", "usage_commit_units": 1500000, "overage_price": 0.028, "non_standard_terms": "termination for convenience"},
        {"deal_id": "D-1043", "customer": "Ion Retail", "segment": "Mid-Market", "close_date": "2026-11-28",
         "list_acv": 95000, "net_acv": 85500, "term_months": 12, "payment_terms_days": 30, "billing_frequency": "annual",
         "ramp": "N", "usage_commit_units": 0, "overage_price": "", "non_standard_terms": ""},
        {"deal_id": "D-1044", "customer": "Juniper Telecom", "segment": "Enterprise", "close_date": "2026-12-30",
         "list_acv": 720000, "net_acv": 540000, "term_months": 48, "payment_terms_days": 60, "billing_frequency": "annual",
         "ramp": "Y", "usage_commit_units": 4000000, "overage_price": 0.030, "non_standard_terms": "MFN pricing; free services credits"},
        {"deal_id": "D-1045", "customer": "Kestrel Media", "segment": "Mid-Market", "close_date": "2026-12-15",
         "list_acv": 140000, "net_acv": 98000, "term_months": 12, "payment_terms_days": 45, "billing_frequency": "monthly",
         "ramp": "N", "usage_commit_units": 800000, "overage_price": 0.045, "non_standard_terms": ""},
    ]


def write(name, rows):
    with open(HERE / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {name}: {len(rows)} rows")


if __name__ == "__main__":
    write("revenue_plan_forecast_actuals.csv", rows_plan())
    write("usage_history.csv", rows_usage())
    write("deals.csv", rows_deals())
