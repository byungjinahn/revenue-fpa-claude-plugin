#!/usr/bin/env python3
"""Simulate this week's revenue data for the fictional "Northwind DevTools" (demo mode).

Behaves like a real weekly data pull:
  - Closed months (before the as-of month) have fixed actuals: same values every week.
  - Open months carry a forecast that is re-cut every ISO week.
  - The deal pipeline (deals closing between the as-of date and quarter end) changes every week.
Usage:
  python3 simulate_week.py --as-of 2026-11-09 --out /tmp/pulse-data
Writes revenue_plan_forecast_actuals.csv, usage_history.csv, deals.csv (same columns as sample-data/).
All figures are invented.
"""
import argparse
import csv
import datetime as dt
import hashlib
import random
from pathlib import Path

SEGMENTS = {"Enterprise": (2400, 600, 0.012), "Mid-Market": (1300, 350, 0.015), "Self-Serve": (500, 420, 0.022)}
CUSTOMERS = [
    ("Acme Robotics", "Enterprise", 2_000_000, 0.004, 0.035),
    ("Blue Harbor Bank", "Enterprise", 3_500_000, 0.003, 0.032),
    ("Cobalt Health", "Mid-Market", 900_000, 0.006, 0.042),
    ("Dune Logistics", "Mid-Market", 600_000, 0.005, 0.045),
    ("Ember Games", "Self-Serve", 0, 0.0, 0.050),
    ("Fjord Analytics", "Self-Serve", 0, 0.0, 0.050),
]
PROSPECTS = ["Granite Insurance", "Helix Biotech", "Ion Retail", "Juniper Telecom", "Kestrel Media", "Lumen Energy",
             "Mosaic Health", "Nimbus Air", "Orchid Pharma", "Pioneer Freight", "Quartz Bank", "Redwood Games"]
NST = ["", "", "", "", "", "", "", "termination for convenience", "MFN pricing", "free services credits", "customer acceptance"]


def rng(*key):
    """Deterministic RNG per key, so a closed month's actual never changes between runs."""
    return random.Random(int(hashlib.sha256("|".join(map(str, key)).encode()).hexdigest()[:12], 16))


def month_list(as_of):
    start = as_of.year - 1
    return [f"{y}-{m:02d}" for y in (start, start + 1) for m in range(1, 13)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", default=dt.date.today().isoformat())
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    as_of = dt.date.fromisoformat(a.as_of)
    week = "%d-W%02d" % as_of.isocalendar()[:2]
    cur_month = f"{as_of.year}-{as_of.month:02d}"
    months = month_list(as_of)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    # 1. Plan / forecast / actuals, 24 months
    rows = []
    for seg, (sub, use, g) in SEGMENTS.items():
        for i, m in enumerate(months):
            q_end = int(m[5:]) % 3 == 0
            for product, base in (("Subscription", sub), ("Usage", use)):
                plan_rev = base * (1 + g) ** i
                bill_mult = {"Enterprise": 1.9 if q_end else 0.6, "Mid-Market": 1.3 if q_end else 0.85, "Self-Serve": 1.0}[seg]
                plan_bill = plan_rev * (bill_mult if product == "Subscription" else 1.0)
                plan_book = plan_rev * 12 * (0.28 if q_end else 0.08) if product == "Subscription" else 0.0
                for metric, plan in (("bookings", plan_book), ("billings", plan_bill), ("revenue", plan_rev)):
                    if not plan:
                        continue
                    sd = 0.03 if metric == "revenue" else 0.08
                    if product == "Usage":
                        sd *= 1.8  # consumption is noisier
                    closed = m < cur_month
                    if closed:
                        actual = round(plan * (1 + rng(seg, product, metric, m, "act").gauss(0, sd)), 1)
                        fcst = round(plan * (1 + rng(seg, product, metric, m, "fc").gauss(0, sd * 0.6)), 1)
                    else:
                        actual = ""
                        fcst = round(plan * (1 + rng(seg, product, metric, m, week).gauss(-0.01, sd * 0.6)), 1)
                    rows.append({"month": m, "segment": seg, "product": product, "metric": metric,
                                 "plan": round(plan, 1), "forecast": fcst, "actual": actual})
    write(out / "revenue_plan_forecast_actuals.csv", rows)

    # 2. Usage history: trailing 9 closed months
    closed_months = [m for m in months if m < cur_month][-9:]
    urows = []
    for name, seg, commit, unit, overage in CUSTOMERS:
        r = rng(name, "profile")
        level = (commit or 400_000) * r.uniform(0.7, 0.95)
        trend = r.uniform(-0.01, 0.05)
        for i, m in enumerate(closed_months):
            consumed = level * (1 + trend) ** i * rng(name, m).uniform(0.93, 1.07)
            urows.append({"month": m, "customer": name, "segment": seg, "committed_units": commit,
                          "consumed_units": int(consumed), "unit_price": unit, "overage_price": overage})
    write(out / "usage_history.csv", urows)

    # 3. Pipeline: deals closing between as-of and quarter end, re-cut weekly
    q_end_month = ((as_of.month - 1) // 3 + 1) * 3
    q_end = (dt.date(as_of.year + (q_end_month == 12), q_end_month % 12 + 1, 1) - dt.timedelta(days=1))
    r = rng(week, "deals")
    drows = []
    for j, cust in enumerate(r.sample(PROSPECTS, r.randint(5, 8))):
        seg = r.choice(["Enterprise", "Enterprise", "Mid-Market"])
        list_acv = r.choice([90, 140, 260, 480, 720]) * 1000
        days = max(1, (q_end - as_of).days)
        usage = r.random() < 0.3
        drows.append({
            "deal_id": f"D-{as_of.isocalendar()[1]:02d}{j + 1:02d}", "customer": cust, "segment": seg,
            "close_date": (as_of + dt.timedelta(days=r.randint(1, days))).isoformat(),
            "list_acv": list_acv, "net_acv": round(list_acv * (1 - r.choice([0.05, 0.05, 0.08, 0.1, 0.1, 0.15, 0.25, 0.35]))),
            "term_months": r.choice([12, 12, 12, 24, 36, 48]), "payment_terms_days": r.choice([30, 30, 30, 30, 45, 60, 90]),
            "billing_frequency": r.choice(["annual", "annual", "annual", "annual", "quarterly", "monthly"]), "ramp": r.choice(["N", "N", "N", "N", "Y"]),
            "usage_commit_units": r.choice([800_000, 1_500_000, 4_000_000]) if usage else 0,
            "overage_price": r.choice([0.028, 0.035, 0.04, 0.045]) if usage else "",
            "non_standard_terms": r.choice(NST),
        })
    write(out / "deals.csv", drows)
    print(f"as-of {as_of} ({week}); closed through {closed_months[-1]}; quarter ends {q_end}")


def write(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
