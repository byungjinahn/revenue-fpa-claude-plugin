#!/usr/bin/env python3
"""Variance and anomaly detection on closed months.

Input CSV columns: month, segment, product, metric, plan, forecast, actual.
Usage:
  python3 variance.py DATA.csv --month 2026-09 [--threshold-pct 5] [--threshold-abs 50] [--z 2.0]

Two checks per line (segment x product x metric):
  1. Variance: actual vs plan and actual vs forecast for --month; flagged if BOTH |%| >= threshold-pct
     and |$| >= threshold-abs (materiality gate).
  2. Anomaly: the month's actual-to-plan ratio compared with that line's trailing history
     (z-score of the ratio). Catches breaks in pattern that a plan miss alone would not.
Also reports forecast accuracy (MAPE of forecast vs actual) over all closed months per line.
"""
import argparse
import csv
import json
import statistics
from collections import defaultdict


def f(v):
    return float(v) if v not in ("", None) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--month", required=True)
    ap.add_argument("--threshold-pct", type=float, default=5.0)
    ap.add_argument("--threshold-abs", type=float, default=50.0)
    ap.add_argument("--z", type=float, default=2.0)
    ap.add_argument("--json")
    a = ap.parse_args()

    hist = defaultdict(list)
    with open(a.data, newline="") as fh:
        for r in csv.DictReader(fh):
            act, plan, fc = f(r["actual"]), f(r["plan"]), f(r["forecast"])
            if act is None or not plan:
                continue
            hist[(r["segment"], r["product"], r["metric"])].append((r["month"], plan, fc, act))

    flagged, anomalies, accuracy = [], [], []
    for key, pts in sorted(hist.items()):
        pts.sort()
        cur = [p for p in pts if p[0] == a.month]
        prior = [p for p in pts if p[0] < a.month]
        fc_err = [abs(p[3] - p[2]) / abs(p[3]) for p in pts if p[2] and p[3]]
        if fc_err:
            accuracy.append((key, round(statistics.mean(fc_err) * 100, 1), len(fc_err)))
        if not cur:
            continue
        _, plan, fc, act = cur[0]
        vp, vpp = act - plan, (act / plan - 1) * 100
        vf = act - fc if fc else None
        vfp = (act / fc - 1) * 100 if fc else None
        if abs(vpp) >= a.threshold_pct and abs(vp) >= a.threshold_abs:
            flagged.append((key, plan, fc, act, vp, vpp, vf, vfp))
        ratios = [p[3] / p[1] for p in prior]
        if len(ratios) >= 4:
            mu, sd = statistics.mean(ratios), statistics.pstdev(ratios)
            z = (act / plan - mu) / sd if sd > 0 else 0.0
            if abs(z) >= a.z:
                anomalies.append((key, round(z, 2), round(mu, 3), round(act / plan, 3)))

    print(f"### Variance report — {a.month}")
    print(f"Materiality: |var| >= {a.threshold_pct}% AND >= {a.threshold_abs:,.0f}; anomaly z >= {a.z}\n")
    if flagged:
        print("| Segment | Product | Metric | Plan | Forecast | Actual | Var vs plan | Var vs fcst |")
        print("|---|---|---|---|---|---|---|---|")
        for (s, p, m), plan, fc, act, vp, vpp, vf, vfp in sorted(flagged, key=lambda x: -abs(x[4])):
            vf_s = f"{vf:+,.1f} ({vfp:+.1f}%)" if vf is not None else "n/a"
            print(f"| {s} | {p} | {m} | {plan:,.1f} | {fc:,.1f} | {act:,.1f} | {vp:+,.1f} ({vpp:+.1f}%) | {vf_s} |")
    else:
        print("No lines breach materiality thresholds.")
    print("\n#### Pattern breaks (anomalies)")
    if anomalies:
        for (s, p, m), z, mu, r in sorted(anomalies, key=lambda x: -abs(x[1])):
            print(f"- {s} / {p} / {m}: actual/plan {r:.3f} vs trailing mean {mu:.3f} (z = {z:+.2f})")
    else:
        print("- None detected.")
    print("\n#### Forecast accuracy (MAPE, all closed months)")
    for (s, p, m), mape, n in sorted(accuracy, key=lambda x: -x[1])[:8]:
        print(f"- {s} / {p} / {m}: {mape:.1f}% over {n} months")


    if a.json:
        with open(a.json, "w") as fh:
            json.dump({
                "month": a.month,
                "material": [{"segment": k[0], "product": k[1], "metric": k[2], "plan": round(pl, 1), "forecast": round(fc, 1),
                              "actual": round(ac, 1), "var": round(vp, 1), "var_pct": round(vpp, 1)}
                             for k, pl, fc, ac, vp, vpp, vf, vfp in sorted(flagged, key=lambda x: -abs(x[4]))],
                "anomalies": [{"segment": k[0], "product": k[1], "metric": k[2], "z": z, "ratio": r, "trailing_mean": mu}
                              for k, z, mu, r in anomalies],
                "accuracy": [{"segment": k[0], "product": k[1], "metric": k[2], "mape": m, "months": n} for k, m, n in accuracy],
            }, fh, indent=2)


if __name__ == "__main__":
    main()
