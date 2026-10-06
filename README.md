# GTM Tracking Taxonomy Linter and Attribution Recovery Audit

A campaign-launch-sheet linter that catches a tracking-taxonomy violation by exact rule before a link ships, plus an attribution recovery audit that traces a simulated session reported as "(direct)/(none)" back to the campaign that actually earned it, within a bounded lookback window. Every number below was measured on this machine by running the code in this repository, not targeted in advance.

## Why this exists

A UTM taxonomy only works if every planned link actually follows it, and a last-touch attribution model only tells the truth about a channel's performance if sessions that lost their tracking parameters are either correctly traced back to the campaign that earned them or correctly left alone. Both failures are silent in a spreadsheet: a malformed `utm_medium` does not throw an error, it just fragments a channel's reporting into two rows, and a session a browser or an email client stripped the parameters from does not announce that it should have been attributed to last week's campaign, it just shows up as "(direct)/(none)" forever. This project makes both failures loud: a linter that names the exact broken rule before a link ships, and a bounded, measured recovery model that is honest about where its own lookback window ends.

## Honest framing

- **What this is not.** Not a GA4 or GTM plugin; the taxonomy, the registry, and the session model are all authored here, standing in for the real systems a marketing team's launch sheet and analytics platform would be. Not a claim that the attribution model recovers every lost session ever; it recovers exactly the ones within its own stated lookback window (30 days) and is measured, separately, on how it behaves at and beyond that boundary.
- **Synthetic launch sheet and sessions, stated as synthetic.** `tracking_audit/registry.py` generates 60 fictional registered campaigns from a seeded `random.Random`; `tracking_audit/launch_sheet.py` generates 400 valid and 180 deliberately broken links from the same kind of seeding; `tracking_audit/sessions.py` generates 1,254 simulated sessions across 500 fictional visitors, each carrying a ground-truth `true_origin_campaign` label the recovery algorithm is never given. No real campaign, no real visitor, no real session.
- **The 180 broken links are each isolated to exactly one violation.** Every seeded violation corrupts exactly one aspect of an otherwise genuinely valid, registered link (`launch_sheet._corrupt`), so "caught by the exact rule" is checked against an input that is broken in exactly the claimed way, not a link that happens to be broken in several ways and could be caught by any of them. `tests/test_launch_sheet.py::test_every_broken_row_genuinely_fails_with_its_expected_rule` is the dedicated check for this, the same discipline `natural-language-segment-builder/tests/test_invalid_dataset.py` applies to its own mutation generator.
- **The recovery model's scope boundary is deliberate, not a missed case.** A visitor's direct session more than 30 days after their last tagged touch is, by this model's own stated rule, not attributed to that old campaign, even in the synthetic data where the generator happens to know it really was the same person. That is treated as the correct, honest answer (a real analytics team would not want campaign credit for a touch a month old either), and is measured as its own case, not folded into the headline recovery number.
- **Machine and toolchain, exactly as measured.** 8 physical / 16 logical cores, Windows 11 Home (build 10.0.26200), Python 3.12.10, pytest 8.3.3, pyyaml 6.0.2.

## Architecture

```
tracking_audit/
  taxonomy.py       the taxonomy spec: allowed utm_source vocabulary, the
                     medium-per-source map, the campaign-code naming regex,
                     and one named rule function per check, each returning
                     a tagged RuleViolation or None, never a bare boolean
  registry.py        seeded synthetic campaign registry (60 campaigns);
                     the source of truth for "is this code actually
                     registered", a check the naming regex alone cannot do
  linter.py           LaunchLinkRow, LintViolation; lint_row() applies every
                     taxonomy rule plus the registry check to one link;
                     lint_sheet() does it for a whole sheet
  launch_sheet.py      seeded generators: 400 genuinely valid links and 180
                     deliberately broken links (20 per violation kind, 9
                     kinds), each broken link paired with the exact rule
                     it was built to break
  sessions.py          seeded synthetic sessions with a ground-truth
                     true_origin_campaign label, for 300 campaign-touched
                     visitors (with in-window and out-of-window followups)
                     and 200 genuinely organic visitors
  attribution.py        naive_channel() (what GA4-style last-touch would
                     report) and recover_attribution() (the bounded,
                     last-tagged-touch recovery model), which never reads
                     the ground-truth label
scripts/
  run_lint_battery.py               400 valid + 180 broken links
  run_attribution_recovery_battery.py   the recovery accuracy measurement
  generate_sample_sheet.py          writes data/launch_sheet.csv
  lint_campaign_sheet.py             the CI entry point; exits 1 on any
                                     violation in the real launch sheet
tests/
  test_taxonomy.py, test_registry.py, test_linter.py, test_launch_sheet.py,
  test_sessions.py, test_attribution.py
.github/workflows/lint-gate.yml   CI: tests, both batteries, then lints the
                                    real committed launch sheet
data/
  launch_sheet.csv   20 genuinely valid links (regenerate with
                      `python scripts/generate_sample_sheet.py`)
docs/
  test_output.txt, lint_battery_output.txt, attribution_recovery_output.txt,
  ci_lint_demo_output.txt, ci_workflow_validation.txt
```

**Why every taxonomy rule returns a tagged `RuleViolation`, never a bare boolean.** A linter that returns `False` for "medium invalid" and `False` for "source unknown" cannot tell a launch-sheet owner which one happened without re-deriving it. Every function in `taxonomy.py` either returns `None` (clean) or a `RuleViolation(rule_id, message)`, and `linter.lint_row` never collapses that into a boolean; the battery scripts check the exact `rule_id`, not just "something fired".

**Why a code's shape and its registration are two separate rules.** `campaign_code_wrong_shape` catches a code that could never be valid (wrong punctuation, missing quarter); `campaign_not_registered` catches a code that is shaped correctly but was never actually planned (a typo'd quarter, a code copied from last cycle). A linter that only checked the regex would wave through a plausible-looking but nonexistent campaign; `registry.py` exists specifically to make that the registry's job, not the regex's.

**Why the recovery model only looks backward through a visitor's own prior tagged sessions, never forward and never across visitors.** Looking forward would use information that was not available at the time a (direct)/(none) session actually happened, which is not something a real attribution system can do causally. Looking across visitors would correctly attribute nothing to anyone; `tests/test_attribution.py::test_never_recovers_a_session_from_a_different_visitor` pins this.

## Validation

**1. Test suite** (`docs/test_output.txt`):

```
27 passed in 0.10s
```

**2. Lint battery, 400 valid + 180 deliberately broken links** (`docs/lint_battery_output.txt`):

```
valid links checked: 400
false flags on valid links: 0 / 400

seeded violations caught by exact rule: 180 / 180
  missing_required_param: 20 / 20
  unknown_utm_source: 20 / 20
  medium_not_valid_for_source: 20 / 20
  campaign_code_wrong_shape: 20 / 20
  campaign_code_not_lowercase: 20 / 20
  campaign_not_registered: 20 / 20
  not_https: 20 / 20
  landing_domain_not_allowed: 20 / 20
  duplicate_query_param: 20 / 20

LINT BATTERY: PASS
```

**3. Attribution recovery battery, 1,254 simulated sessions** (`docs/attribution_recovery_output.txt`):

```
total sessions: 1254
naive (direct)/(none) sessions: 954
  of those, genuinely earned by a campaign within the lookback window: 403
  of those, genuinely organic (no recoverable campaign, ever or in-window): 551

correctly traced back to the exact earning campaign: 403 / 403
false recoveries on genuinely organic sessions: 0 / 551

ATTRIBUTION RECOVERY BATTERY: PASS
```

**4. CI lint of the real committed launch sheet** (`docs/ci_lint_demo_output.txt`):

```
rows checked: 20
clean rows: 20 / 20
violations: 0
```

**5. CI workflow YAML** (`docs/ci_workflow_validation.txt`): parsed successfully with `yaml.safe_load`.

## Findings

**The first version of the `medium_not_valid_for_source` violation generator sometimes produced a valid link instead of a broken one.** The corruption swapped a campaign's real medium for `"organic"` (or `"affiliate"` if it already was `"organic"`), on the assumption that either value would be wrong for any source. That assumption was false for a Google campaign whose real medium happened to be `"cpc"`: swapping it to `"organic"` produced `(google, organic)`, which `taxonomy.ALLOWED_MEDIUM_BY_SOURCE` explicitly allows, so the "broken" link was not actually broken. This did not surface in a casual run because it depends on which random campaign the corruption happened to draw; it was caught by writing `tests/test_launch_sheet.py::test_every_broken_row_genuinely_fails_with_its_expected_rule` and running it across every seeded case rather than spot-checking a few. Fix: the corruption now picks any medium value that is not in the real source's allowed set (`next(m for m in _ALL_MEDIUMS if m not in allowed)`), which is correct for every source rather than correct for most of them.

**A direct session's week-over-week framing hides a real design question: should "the campaign that earned it" ever expire?** Early in building the recovery model, the instinct was to recover a direct session to whichever campaign most recently touched that visitor, with no time limit at all. The seeded data exposed why that is wrong: a visitor touched by a campaign on day 0 who returns organically on day 55 is not meaningfully "earned" by that campaign anymore, and crediting it that way would make every channel's reported performance drift upward forever as the simulation window grows. The fix was not a code bug but a scope decision, made explicit and measured: `LOOKBACK_DAYS = 30`, with the out-of-window case built into the session generator and checked by its own test (`tests/test_sessions.py::test_out_of_window_followups_have_no_true_origin`) rather than left as an edge case nobody tried.

## Measured results

Machine: 8 physical / 16 logical cores, Windows 11 Home (build 10.0.26200), Python 3.12.10, pytest 8.3.3. All numbers are single-run, bit-for-bit reproducible measurements (fixed seeds, no network, no threading).

**The one number that matters: 180 of 180 seeded violations caught by the exact rule that was broken, 0 of 400 valid links falsely flagged.**

| Claim | Measured | Meets claim |
|---|---|---|
| 180 of 180 seeded violations caught by name | 180 / 180, broken down 20/20 across all 9 violation kinds | yes |
| 0 of 400 valid links falsely flagged | 0 / 400 | yes |
| Campaign launch sheets linted against a tracking taxonomy in CI | `.github/workflows/lint-gate.yml` runs the test suite, both batteries, and `lint_campaign_sheet.py` against the real committed `data/launch_sheet.csv` on every push/PR, failing the build on any violation; YAML validated with `yaml.safe_load`, not yet executed by a live GitHub Actions run (see Limitations) | yes, with that caveat |
| Simulated sessions traced back out of direct/none to the campaign that earned them | 403 of 403 sessions genuinely earned by a campaign within the 30-day lookback window were traced back to the exact right campaign; separately, 0 of 551 genuinely organic direct sessions were ever falsely attributed | yes |

What "180/180" and "403/403" measure, and what they do not: they measure that this repository's own linter and recovery model correctly handle every case its own seeded generators constructed, including the genuinely-broken-in-exactly-one-way discipline described above. They do not measure how often a real marketing team's launch sheets contain these specific defects, or how often a real analytics pipeline's sessions lose their UTM parameters; both are modeled plausibly here, not drawn from a real GTM container or a real GA4 export.

## Building and running

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# test suite
set PYTHONPATH=.
python -m pytest tests -q

# the 400-valid / 180-broken lint battery
python scripts/run_lint_battery.py

# the attribution recovery battery
python scripts/run_attribution_recovery_battery.py

# regenerate the sample launch sheet (fixed seed)
python scripts/generate_sample_sheet.py

# lint the real committed launch sheet (the CI command; exits 1 on any violation)
python scripts/lint_campaign_sheet.py
```

On a POSIX shell, replace `set PYTHONPATH=.` with `export PYTHONPATH=.`.

## Sibling comparison

This portfolio's [`cloud-spend-allocation-showback`](https://github.com/Manas103/cloud-spend-allocation-showback) and [`technology-runrate-forecast-variance`](https://github.com/Manas103/technology-runrate-forecast-variance) share this repo's "N of N seeded defects caught by exact rule, 0 false flags on clean input" measurement shape, applied there to cloud cost tagging and technology spend excursions. This repo is the first in the portfolio to apply that shape to a marketing tracking taxonomy, and it adds a second, different kind of check neither sibling needs: the attribution recovery audit, which is not a defect-catching problem (nothing is malformed) but a causal-inference-shaped one (which past touch, if any, explains a session that currently looks unattributed), measured against a ground-truth label the recovery algorithm itself never sees.

## Limitations

- **No live GitHub Actions run has executed `.github/workflows/lint-gate.yml` yet.** The YAML is authored and validated; every command it runs was run directly on this machine instead, with output committed under `docs/`.
- **The taxonomy covers 5 sources and campaign-code shape, not every field a real GTM container tracks** (no `utm_term` rules, no click-id or gclid/fbclid validation, no cross-domain linking rules).
- **The attribution recovery model is last-tagged-touch within a fixed 30-day window**, a defensible but not the only reasonable choice; a real team might want a different window or a different model (linear, time-decay, data-driven) entirely, and this repository does not compare against those alternatives.
- **The registry and launch sheet are both synthetic**, generated by the same kind of seeded process they are meant to be checked against; this measures the linter's and the recovery model's own logic, not how often these specific defects occur in a real marketing team's actual launch sheets or analytics exports.
