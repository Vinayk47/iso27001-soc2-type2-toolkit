#!/usr/bin/env python3
"""Rebuild the fictional sample data, including five planted problems."""
import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from readiness import select_sample  # noqa: E402

START, SEED = date(2025, 7, 1), 2026
rng = random.Random(SEED)
controls = list(csv.DictReader(open(ROOT / "data/controls.csv", encoding="utf-8")))
population, evidence = [], []
SIZES = {"HR-01": ("HIRE", 22), "IAM-04": ("LEAVER", 18), "CHG-01": ("CHG", 120)}

for control in controls:
    cid, frequency = control["control_id"], control["frequency"]
    if frequency == "event":
        prefix, size = SIZES[cid]
        ids = [f"{prefix}-{n:03d}" for n in range(1, size + 1)]
        dates = {}
        for item in ids:
            dates[item] = START + timedelta(days=rng.randrange(365))
            population.append([cid, item, dates[item]])
        sampled = select_sample(ids, SEED, cid)
        for pos, item in enumerate(sampled):
            if cid == "IAM-04" and pos == 0:
                continue  # planted gap: no removal ticket found
            result, notes = "pass", ""
            if cid == "CHG-01" and pos == 3:
                result, notes = "fail", "Approved after release"
            evidence.append([cid, dates[item], item, result, notes])
    else:
        months = {"monthly": range(12), "quarterly": (2, 5, 8, 11), "annual": (6,)}[frequency]
        for offset in months:
            year = 2025 + (6 + offset) // 12
            performed = date(year, (6 + offset) % 12 + 1, 15)
            if cid == "LOG-01" and performed.month == 2:
                continue  # planted gap: no review recorded in February
            result, notes = "pass", ""
            if cid == "IAM-02" and performed.month == 3:
                result, notes = "fail", "Two leavers still active at review"
            if cid == "VEN-01":
                result, notes = "fail", "One vendor report past its review date"
            evidence.append([cid, performed, f"{cid}-{performed:%Y%m}", result, notes])


def write(name, header, rows):
    with open(ROOT / "sample" / name, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


write("population.csv", ["control_id", "item_id", "event_date"], population)
write("evidence.csv", ["control_id", "performed_on", "reference", "result", "notes"], evidence)
