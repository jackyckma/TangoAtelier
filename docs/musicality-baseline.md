# Musicality baseline (M3)

**Date:** 2026-08-19  
**Commit context:** Pre–M-task engine (E1–E12 landed; M3 critic only — no engine changes)  
**Reference:** Expert prior in `backend/app/critic/reference/golden_age.json` (not PD corpus stats)

## Purpose

M3 establishes measurement baselines. Fingerprint test thresholds in `backend/tests/musicality/test_fingerprint.py` are set to these aggregate KL values so regressions are caught when M-tasks tighten quality. Hard-rule tests (`test_no_error_violations`) **intentionally fail** until M1/M2/M4 fix the engine.

## Aggregate fingerprints (vs golden_age expert prior)

### Tango — 100 seeds

| Metric | Value | Golden prior | Notes |
|--------|------:|-------------:|-------|
| `interval_hist` KL | 0.2053 | — | Stepwise-heavy; low leaps |
| `onset_hist` KL | 0.3779 | — | Weak anacrusis / syncopa |
| `duration_hist` KL | 0.1783 | — | Short values dominate |
| `notes_per_bar` | 1.847 | 3.2 | Density param ineffective |
| `rest_ratio` | 0.306 | 0.18 | Bar-level silence high; phrase rests still weak |
| `repeated_note_ratio` | 0.160 | 0.14 | Near prior (unison-kill effect subtle in aggregate) |
| `leap_ratio` | 0.052 | 0.16 | §1: ≥5 semitone leaps rare |

### Vals — 50 seeds

| Metric | Value | Golden prior |
|--------|------:|-------------:|
| `interval_hist` KL | 0.7008 | — |
| `onset_hist` KL | 0.0402 | — |
| `duration_hist` KL | 0.4519 | — |
| `notes_per_bar` | 1.413 | 2.4 |
| `rest_ratio` | 0.222 | 0.16 |
| `repeated_note_ratio` | 0.162 | 0.12 |
| `leap_ratio` | 0.097 | 0.20 |

### Milonga — 50 seeds

| Metric | Value | Golden prior |
|--------|------:|-------------:|
| `interval_hist` KL | 0.6812 | — |
| `onset_hist` KL | 3.0333 | — |
| `duration_hist` KL | 0.4529 | — |
| `notes_per_bar` | 2.636 | 3.0 |
| `rest_ratio` | 0.278 | 0.15 |
| `repeated_note_ratio` | 0.167 | 0.16 |
| `leap_ratio` | 0.076 | 0.18 |

## Hard-rule violation totals

| rule_id | tango | vals | milonga |
|---------|------:|-----:|--------:|
| CHORD_SPELLING_INVALID | 104 | 6 | 4 |
| SECTION_NO_CADENCE | 61 | 0 | 8 |
| PHRASE_NO_CADENCE | 85 | 50 | 111 |
| LEAP_NOT_RECOVERED | 160 | 150 | 179 |
| MELODY_NO_LONG_NOTE | 338 | 6 | 200 |
| MELODY_NO_REST | 800 | 194 | 869 |
| LH_PARALLEL_FIFTHS | 0 | 0 | 0 |
| RANGE_EXCEEDED | 323 | 1211 | 152 |
| DENSITY_MISMATCH | 100 | 50 | 10 |
| HARMONIC_RHYTHM_ORPHAN | 200 | 100 | 100 |

`LH_PARALLEL_FIFTHS` is zero under `SIMPLE_PROFILE` render (mostly broken LH). Rule fires on block-heavy profiles (e.g. Pugliese).

## §1 diagnostic coverage

| §1 issue | Detected by |
|----------|-------------|
| Stepwise interval / few leaps | `leap_ratio`, `interval_hist` KL |
| Low notes per bar | `DENSITY_MISMATCH`, `notes_per_bar` |
| Onset / no anacrusis | `onset_hist` KL |
| Short durations / no breath | `duration_hist` KL, `MELODY_NO_LONG_NOTE` |
| Unison suppression | `repeated_note_ratio` vs prior (weak signal); `MELODY_NO_REST` |
| Chord spelling bugs | `CHORD_SPELLING_INVALID` |
| Harmonic cycle vs section length | `HARMONIC_RHYTHM_ORPHAN`, `SECTION_NO_CADENCE` |
| Same macro form every seed | Not in M3 scope → M7 |

## Commands

```bash
cd backend && PYTHONPATH=. pytest tests/musicality/ -v
python scripts/musicality-report.py --dance tango --seeds 100
python scripts/musicality-report.py --dance vals --seeds 50
python scripts/musicality-report.py --dance milonga --seeds 50
```

## Next tightening targets (after M-tasks)

Suggested post-M4 fingerprint gates (from spec): `interval_hist` KL < 0.25, `duration_hist` KL < 0.25, `leap_ratio` 0.12–0.20, `notes_per_bar` within ±25% of density target.
