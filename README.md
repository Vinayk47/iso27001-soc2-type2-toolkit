# ISO 27001 and SOC 2 Type 2 Readiness Toolkit

A portfolio project that shows how one set of controls can support both ISO/IEC 27001:2022 and SOC 2, and how to find evidence problems before an audit.

> **All company data here is fictional.** This isn't client work, an audit, or legal or compliance advice. It contains my own control summaries, not text from the standards.

## The problem

SOC 2 Type 2 tests whether controls operated across a whole audit period. If a monthly review was missed in February, it can't be fixed in June. This tool checks every expected period and sampled item, then reports what's missing while there's still time to respond.

## What's included

| Path | Contents |
|---|---|
| `data/controls.csv` | 18 controls mapped to ISO 27001:2022 and SOC 2 |
| `readiness.py` | Evidence checker and report generator (Python standard library only) |
| `sample/` | Fictional evidence, event populations and a risk register |
| `sample/readiness_report.md` | Report produced from the sample data |
| `docs/type2-readiness-guide.md` | Key concepts, framework comparison and limits |

## Run it

Requires Python 3.9 or later.

```bash
python3 readiness.py --output report.md
python3 -m unittest discover -s tests -t .
```

Use `--start` and `--end` to set the audit window, and `--strict` to make the command fail when anything isn't ready.

## How it works

- **Monthly, quarterly and annual controls:** each period in the window needs evidence.
- **Event controls (such as changes and leavers):** a repeatable sample is drawn from the event population, and each selected item needs evidence.
- **Results:** a control is marked **Ready**, **Exception** (evidence shows a failure) or **Gap** (evidence is missing).

The sample data contains planted problems, so the report shows what real findings look like.

## Sample result

**Controls:** 18 | **Ready:** 13 | **Exceptions:** 3 | **Gaps:** 2

See the [full report](sample/readiness_report.md).

## Limits

The control mappings are my own working mapping, and the sample sizes are illustrative. In a real audit, the auditor sets the testing approach. See the [guide](docs/type2-readiness-guide.md).

## License

MIT
