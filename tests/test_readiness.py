import unittest
from datetime import date

from readiness import assess, expected_periods, sample_size, select_sample

START, END = date(2025, 7, 1), date(2026, 6, 30)


def control(cid, frequency):
    return {"control_id": cid, "title": "t", "iso27001_2022": "A.5.1",
            "soc2_tsc": "CC1.1", "frequency": frequency, "evidence_expected": "e"}


def proof(cid, day, reference="r", result="pass", notes=""):
    return {"control_id": cid, "performed_on": day, "reference": reference,
            "result": result, "notes": notes}


class Periods(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(expected_periods("monthly", START, END)), 12)
        self.assertEqual(len(expected_periods("quarterly", START, END)), 4)
        self.assertEqual(expected_periods("annual", START, END), ["audit window"])


class Sampling(unittest.TestCase):
    def test_sizes(self):
        self.assertEqual([sample_size(n) for n in (3, 20, 40, 200)], [3, 5, 10, 25])

    def test_repeatable(self):
        items = [str(n) for n in range(100)]
        self.assertEqual(select_sample(items, 1, "X"), select_sample(items, 1, "X"))


class Assess(unittest.TestCase):
    def status(self, ctrl, evidence, population=()):
        return assess([ctrl], evidence, list(population), START, END)[0]

    def test_one_missing_month_is_a_gap(self):
        months = [f"{y}-{m:02d}-15" for y, m in
                  [(2025, m) for m in range(7, 13)] + [(2026, m) for m in range(1, 6)]]
        result = self.status(control("M", "monthly"), [proof("M", d) for d in months])
        self.assertEqual(result["status"], "Gap")
        self.assertEqual(result["gaps"], ["2026-06"])

    def test_failed_evidence_is_an_exception(self):
        result = self.status(control("A", "annual"),
                             [proof("A", "2026-01-15", result="fail", notes="late")])
        self.assertEqual(result["status"], "Exception")

    def test_evidence_outside_window_does_not_count(self):
        result = self.status(control("A", "annual"), [proof("A", "2024-01-15")])
        self.assertEqual(result["status"], "Gap")

    def test_all_sampled_events_needed(self):
        population = [{"control_id": "E", "item_id": "I1", "event_date": "2026-01-01"},
                      {"control_id": "E", "item_id": "I2", "event_date": "2026-01-02"}]
        result = self.status(control("E", "event"),
                             [proof("E", "2026-01-01", "I1")], population)
        self.assertEqual(result["gaps"], ["I2"])


if __name__ == "__main__":
    unittest.main()
