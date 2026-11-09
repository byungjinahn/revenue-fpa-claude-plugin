"""Synthetic sample for the ARR vs GAAP revenue reconciliation skill (fictional customers).

Writes arr_by_customer.csv (ARR as of 2026-10-31) and gaap_revenue_by_customer.csv (2026-09 and 2026-10).
Planted cases: mid-month start, one-time services fee, start-date delay, churned customer still in ARR,
usage overage, credit/concession, ramp deal, revenue with no ARR.
"""
import csv
from pathlib import Path

HERE = Path(__file__).parent
# customer: (ARR, Sep revenue, Oct revenue)
DATA = {
    "Acme Robotics":     (240000, 20000, 20000),
    "Blue Harbor Bank":  (420000, 35000, 35400),
    "Cobalt Health":     (180000, 15000, 14700),
    "Dune Logistics":    (96000,  8000,  8000),
    "Granite Insurance": (312000, 0,     13000),   # signed, started Oct 16 -> partial month
    "Helix Biotech":     (221000, 18400, 30900),   # one-time implementation fee in Oct
    "Ion Retail":        (85500,  0,     0),       # booked, go-live delayed
    "Juniper Telecom":   (360000, 30000, 30000),
    "Kestrel Media":     (98000,  8170,  0),       # churned Sep 30, not removed from ARR
    "Lumen Payments":    (150000, 15800, 16200),   # usage overage above commit
    "Mesa Foods":        (120000, 10000, 7500),    # service credit issued in Oct
    "Nimbus AI":         (300000, 18750, 18750),   # year-1 ramp at 75% of ARR
    "Orbit Labs":        (0,      4000,  6500),    # professional services only
    "Pioneer Energy":    (60000,  5000,  5250),
}


def main():
    with open(HERE / "arr_by_customer.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["as_of", "customer", "arr"])
        for c, (arr, _, _) in DATA.items():
            if arr:
                w.writerow(["2026-10-31", c, arr])
    with open(HERE / "gaap_revenue_by_customer.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["month", "customer", "revenue"])
        for m, idx in (("2026-09", 1), ("2026-10", 2)):
            for c, vals in DATA.items():
                if vals[idx]:
                    w.writerow([m, c, vals[idx]])
    print("wrote arr_by_customer.csv, gaap_revenue_by_customer.csv")


if __name__ == "__main__":
    main()
