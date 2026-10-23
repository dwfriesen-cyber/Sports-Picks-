# Sports Picks recovery — 23 October 2026

NHL V6/V7-A, NFL V1 and the daily pipeline are running. Full recovery remains incomplete because the exact original NFL V3 fitted probability transforms and coefficients were not present in the recovered research. No replacement confidence formula has been introduced. PR #1 remains draft and unmerged.

## Verified execution

- Tested engine: [073a17d](https://github.com/dwfriesen-cyber/Sports-Picks-/commit/073a17d3849db83f684a8273dec77993742eec5d).
- Full engineering validation: [run 39996055424 — successful](https://github.com/dwfriesen-cyber/Sports-Picks-/actions/runs/39996055424).
- Daily launcher: [946a36a](https://github.com/dwfriesen-cyber/Sports-Picks-/commit/946a36a6a61a0a607b40cb58e08da64269d22cc5).
- Actual launcher execution: [run 39996534719 — successful](https://github.com/dwfriesen-cyber/Sports-Picks-/actions/runs/39996534719). All 25 tests, downloads, calculations, persistence and artifact upload passed.
- Persisted output: [52041b5](https://github.com/dwfriesen-cyber/Sports-Picks-/commit/52041b56e6dcd4bf996af5c825ab4405592f2288).
- Saved report inspected: generated 2026-10-23 17:37:10 UTC, engine 073a17d, 2 genuine NHL picks, 13 NFL V1 picks, preserved V8 selections, 33 historical comparison rows, 56 source receipts. Overall status is deliberately partial because NFL V3 is blocked.
- NHL freeze: Montreal rank 1, Colorado rank 2. NFL: 12 Sunday picks and 1 Monday pick. Existing freeze blobs match the preceding data commit exactly; retries did not rewrite picks.
- Historical grading snapshot is stored separately. No prospective frozen game has finished yet, so live grading has no completed entries at this handoff. Append-only grading and correction behavior pass tests.

## Model validation

| Check | Result |
|---|---|
| NHL original V6 winner/margin and V7-A confidence parity | All 3,773 eligible audit rows match from 3,936 games of original goals/shots and raw MoneyPuck 5v5 xG |
| NHL V6 benchmark, 2023–25 | 2,169/3,773 = 57.49% |
| NHL V7-A daily top-quarter benchmark | 736/1,150 = 64.0% |
| NFL original V1, 2023–25 | 429/671 = 63.93% |
| NFL V1, 2025 | 142/223 = 63.68% |
| NFL V3 | Blocked; reported 145/180 top-quarter result is NOT reproduced |
| Safety and regression checks | 25 passed |

The starter missed the first 43 NHL games by beginning at October 6. Ingestion now scans from September 1 and verified 165 completed 2026–27 regular-season games through October 22, with all 165 raw 5v5 xG records, plus two October 23 games. NFL current inputs use fresh nflverse play-by-play, checked against final schedule scores.

## October reconstruction

The complete [33-game table](oct18-23-comparison.md), [CSV](oct18-23-comparison.csv) and [JSON](oct18-23-comparison.json) preserve published and V8-lite choices separately from reconstructed V6/V7-A.

| Selection source | Completed record | Accuracy | Daily top quarter | Accuracy |
|---|---:|---:|---:|---:|
| Retrospective V6/V7-A | 15–16 | 48.4% | 3/9 | 33.3% |
| Originally published market picks | 16–15 | 51.6% | 4/9 | 44.4% |
| Original V8-lite shadow | 12–19 | 38.7% | 3/9 | 33.3% |

October 23's two results remain pending. Each day's top quarter rounds up. On three graded V6/V8 disagreements, V6 was correct three times and V8 zero. Daily, weekly and available-season V8 metrics are in the feed.

These are retrospective reconstructions, not originally timestamped live V6 forecasts. Calculations exclude target-date and later games. Historical sources may have revisions; exact contemporaneous availability of every source estimate cannot be proved. Recovered published/shadow coverage starts October 18, so season totals do not claim earlier unrecovered picks.

## Daily operation and records

The launcher on main targets **06:00 America/Regina daily (12:00 UTC)** with bounded recovery runs at **06:20 and 06:40**: cron `0,20,40 12 * * *`. It uses standard public GitHub runners, no paid APIs and no AI inference. Today's successful run was triggered by activating the launcher; the first future 06:00 scheduled run has not yet occurred. GitHub schedules are best effort.

NHL date slates freeze before the earliest puck drop. NFL date slates freeze before the earliest kickoff, including international games, using prior weeks only. Thursday October 22 was already played when recovery completed and is marked missed, not backdated. Missing, partial, stale or late inputs block affected predictions. Retries preserve existing forecasts.

- [Machine-readable feed](https://raw.githubusercontent.com/dwfriesen-cyber/Sports-Picks-/picks-data/latest.json)
- [Frozen prospective records](https://github.com/dwfriesen-cyber/Sports-Picks-/tree/picks-data/frozen): `frozen/nhl`, `frozen/nfl`; new future shadow picks use `frozen/v8`.
- [Grading records](https://github.com/dwfriesen-cyber/Sports-Picks-/tree/picks-data/grading): historical snapshot now; future prospective outcomes append per game and outcome hash.
- [Input snapshots](https://github.com/dwfriesen-cyber/Sports-Picks-/tree/picks-data/inputs), [source receipts](https://github.com/dwfriesen-cyber/Sports-Picks-/tree/picks-data/source-receipts), [run reports](https://github.com/dwfriesen-cyber/Sports-Picks-/tree/picks-data/runs).
- Original imported published/shadow ledgers remain under `ledgers/historical/` on the development branch, with source-message times separate from import time.

The existing 07:00 Saskatchewan ChatGPT automation was not modified. The feed is ready for it to consume; automatic consumption by that unchanged task has not been verified. Consumers must check report date, expiry and individual component status. Application rules reject modification/deletion of audit records; only latest.json is replaceable.

## Remaining blocker

The recovered NFL research documents the V3 50/50 V1/V2 probability blend but omits the fitted transforms, coefficients and original confidence audit needed to reproduce it. Available Library research, repository files and prior project context were searched. NFL V1 is operational; NFL V3 rankings stay unavailable until that original implementation can be recovered. This is a missing model-specification blocker, not a paid-service or GitHub permission problem.
