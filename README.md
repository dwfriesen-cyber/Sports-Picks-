# Sports Picks — recovered original models

Deterministic, noncommercial NHL/NFL research pipeline. No betting-favourite substitutions, paid APIs, paid runners or AI jobs.

## Verified model status

- **NHL V6 winners:** exact original V1 equation plus 20% opponent-adjusted shot-rating update; ±1.5 clipped shot-difference/30 signal; 80% early blend through ten prior games tapering to zero at 40.
- **NHL V7-A confidence:** original raw 5v5 xG-difference/2 rolling rating; the early blend is used for confidence before 40 games, and 40% xG/60% V1 thereafter. Winner stays V6. Confidence is an absolute margin score, not a probability.
- **NHL historical validation:** all 3,773 eligible V6 winner/margin and V7-A confidence rows reproduce from original goals/shots plus raw MoneyPuck shot aggregation. V6: 2,169/3,773; V7-A daily top quarter: 736/1,150.
- **NFL V1 winners:** original points-per-play cross-product equation; 2023–25 reproduces 429/671, including 142/223 in 2025.
- **NFL V3 confidence: BLOCKED.** Original fitted V1/V2 probability transforms and coefficients were not recovered. The documented 50/50 blend alone cannot reproduce those probabilities. The reported 145/180 result is not claimed as reproduced. NFL V1 can freeze independently, with confidence explicitly unavailable.
- **V8-lite:** original 0.5 goal-differential/game + 0.05 shot-differential/game + 0.25 IceScope last-five `xgBalance60`, minus 0.15 on consecutive game days. IceScope's all-eligible, non-empty-net per-60 population is retained; raw 5v5 totals are not substituted.

## Evidence and operation

`reports/oct18-23-comparison.md` and `.csv` contain all 33 October 18–23 matchups. V6/V7-A are retrospective reconstructions. Imported published and V8-lite selections and their source message timestamps are preserved under `ledgers/historical/`. The owner's October 21 Florida preference is a separate record.

`python -m unittest discover -s tests -v` checks original historical parity, temporal leakage, zero scores/xG, immutable retries, late-run rejection, appended grade corrections, Saskatchewan scheduling and the IceScope adapter. `python scripts/validate_history.py` and `python scripts/validate_nfl.py` write model evidence.

`python pipeline.py --state state` downloads the entire current NHL regular season from September 1, raw MoneyPuck shots, NFL schedule and nflverse play-by-play. Complete current NFL coverage is verified against final scores; NFL plays use the same countable-play definition as the historical source. Same-day NHL results never enter that date's predictions. NFL inputs use completed prior weeks only.

The daily workflow targets **06:00 America/Regina = 12:00 UTC**, with bounded recovery attempts at **06:20 and 06:40**. GitHub may delay or drop schedules; an entire date's freeze is rejected after its earliest start. Existing freezes are reused byte-for-byte. NFL Thursday/Sunday/Monday and unusual game dates each freeze before that date's earliest kickoff, including international games. V3 weekly ranks remain unavailable.

The scheduled launcher lives on `main`, pins an explicitly verified source commit, and writes only to `picks-data`. PR #1 remains draft until the missing NFL V3 verification can be completed. Registering this launcher does not merge the draft engine. The 07:00 ChatGPT automation is unchanged.

## Persistent data branch contract

- `latest.json`: machine-readable current report with `report_date`, `generated_at`, `valid_until`, component statuses and source receipts. Consumers must reject stale or blocked components; overall status remains `partial` while NFL V3 is missing.
- `frozen/nhl/YYYY-MM-DD.json`, `frozen/v8/YYYY-MM-DD.json`, `frozen/nfl/YYYY-MM-DD.json`: append-only prospective picks, ranks where supported, timestamps, code revision and input hash.
- `inputs/`: content-addressed normalized input snapshots.
- `source-receipts/`: URLs, fetch timestamps, SHA-256 and byte counts.
- `grading/<sport>/<game_id>/<outcome_hash>.json`: appended final grades; source corrections append a new outcome instead of editing forecasts or old grades.
- `runs/`: every attempt's status report, including blocked attempts.

Only `latest.json` may change. Git commits preserve history; no force pushes, deletions or replacement of audit records are allowed by the publishing script. These are application-enforced append-only records, not a claim of administrator-proof WORM storage.

Historical xG downloads can contain retrospective source revisions. Excluding future games prevents lookahead in the calculations; it cannot establish the original publication time of each source estimate. Current historical downloads reproduce the saved audits to numerical tolerance. The October reconstruction is not represented as originally timestamped live forecasting.

Data credits: NHL official API; **MoneyPuck.com** downloadable shot data (noncommercial use); IceScope public processed metrics; nflverse/nfldata and nflverse/nflverse-data; the original historical NFL team context from antonwilms/sleeper-dashboard-data. No account credentials or premium feeds are needed.

## NFL V3 Reconstruction research update

A separate, fixed reconstruction now reproduces the reported 145/180 weekly top-quarter aggregate, versus raw V1 136/180. This does not establish exact restoration: V2 differs from the original report. Production winners and original-V3 unavailable status remain unchanged. See [measured results](reports/nfl-v3-reconstruction/REPORT.md), [exact coefficients](reports/nfl-v3-reconstruction/COEFFICIENTS.md), and [execution and shadow operations](reports/nfl-v3-reconstruction/OPERATIONS.md).
