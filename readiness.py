#!/usr/bin/env python3
"""SOC 2 Type 2 and ISO 27001 readiness check for control evidence.

A Type 2 report tests whether controls operated across a whole period, so this
tool looks for every expected occurrence in the window instead of one example.
"""
import argparse
import csv
import random
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sample_size(population):
    """Illustrative sample sizes. The auditor sets the real ones."""
    if population <= 5:
        return population
    if population <= 25:
        return 5
    if population <= 50:
        return 10
    return 25


def select_sample(items, seed, control_id):
    ordered = sorted(items)
    picker = random.Random(f"{seed}:{control_id}")
    return sorted(picker.sample(ordered, sample_size(len(ordered))))


def expected_periods(frequency, start, end):
    """Return the period labels a recurring control must cover."""
    if frequency == "annual":
        return ["audit window"]
    periods = []
    year, month = start.year, start.month
    while date(year, month, 1) <= end:
        if frequency == "monthly":
            label = f"{year}-{month:02d}"
        elif frequency == "quarterly":
            label = f"{year}-Q{(month - 1) // 3 + 1}"
        else:
            raise ValueError(f"Unknown frequency: {frequency}")
        if label not in periods:
            periods.append(label)
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return periods


def period_of(frequency, performed):
    if frequency == "annual":
        return "audit window"
    if frequency == "monthly":
        return f"{performed.year}-{performed.month:02d}"
    return f"{performed.year}-Q{(performed.month - 1) // 3 + 1}"


def assess(controls, evidence, population, start, end, seed=2026):
    """Return one result per control, with its gaps and exceptions."""
    by_control = defaultdict(list)
    for row in evidence:
        by_control[row["control_id"]].append(row)
    items_by_control = defaultdict(list)
    for row in population:
        if start <= date.fromisoformat(row["event_date"]) <= end:
            items_by_control[row["control_id"]].append(row["item_id"])

    results = []
    for control in controls:
        cid, frequency = control["control_id"], control["frequency"]
        rows = by_control[cid]
        gaps, exceptions = [], []
        if frequency == "event":
            required = select_sample(items_by_control[cid], seed, cid)
            found = {r["reference"]: r for r in rows}
            for item in required:
                if item not in found:
                    gaps.append(item)
                elif found[item]["result"] != "pass":
                    exceptions.append(f"{item}: {found[item]['notes']}")
            tested = f"{len(required)} of {len(items_by_control[cid])} sampled"
        else:
            required = expected_periods(frequency, start, end)
            found = defaultdict(list)
            for row in rows:
                performed = date.fromisoformat(row["performed_on"])
                if start <= performed <= end:
                    found[period_of(frequency, performed)].append(row)
            for period in required:
                if not found[period]:
                    gaps.append(period)
                for row in found[period]:
                    if row["result"] != "pass":
                        exceptions.append(f"{period}: {row['notes']}")
            tested = f"{len(required)} expected"
        status = "Gap" if gaps else "Exception" if exceptions else "Ready"
        results.append({**control, "status": status, "tested": tested,
                        "gaps": gaps, "exceptions": exceptions})
    return results


def render(results, start, end):
    counts = {s: sum(r["status"] == s for r in results)
              for s in ("Ready", "Exception", "Gap")}
    lines = [
        "# Readiness report",
        "",
        f"**Audit window:** {start} to {end}",
        "",
        f"**Controls:** {len(results)} | **Ready:** {counts['Ready']} | "
        f"**Exceptions:** {counts['Exception']} | **Gaps:** {counts['Gap']}",
        "",
        "| Control | Title | ISO 27001:2022 | SOC 2 | Tested | Status |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['control_id']} | {r['title']} | "
            f"{r['iso27001_2022'].replace(';', ', ')} | "
            f"{r['soc2_tsc'].replace(';', ', ')} | {r['tested']} | {r['status']} |")
    lines += ["", "## Items to resolve", ""]
    issues = [r for r in results if r["gaps"] or r["exceptions"]]
    if not issues:
        lines.append("None.")
    for r in issues:
        for gap in r["gaps"]:
            lines.append(f"- **{r['control_id']}** missing evidence: {gap}")
        for item in r["exceptions"]:
            lines.append(f"- **{r['control_id']}** exception: {item}")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controls", default="data/controls.csv", type=Path)
    parser.add_argument("--evidence", default="sample/evidence.csv", type=Path)
    parser.add_argument("--population", default="sample/population.csv", type=Path)
    parser.add_argument("--start", default="2025-07-01", type=date.fromisoformat)
    parser.add_argument("--end", default="2026-06-30", type=date.fromisoformat)
    parser.add_argument("--seed", default=2026, type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true",
                        help="exit with status 1 if anything is not Ready")
    args = parser.parse_args(argv)
    if args.start > args.end:
        parser.error("--start must not be after --end")

    results = assess(read_csv(args.controls), read_csv(args.evidence),
                     read_csv(args.population), args.start, args.end, args.seed)
    report = render(results, args.start, args.end)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 1 if args.strict and any(r["status"] != "Ready" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
