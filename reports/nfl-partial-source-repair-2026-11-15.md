# NFL partial-source isolation, 2026-11-15

## Observed failure

Run [43750665858](https://github.com/dwfriesen-cyber/Sports-Picks-/actions/runs/43750665858) persisted a partial report at 19:07:54 UTC. The NHL/V8 freezes were valid; NFL collection failed on `2026_10_NE_DET`. Source was pinned to `073a17d3849db83f684a8273dec77993742eec5d`. Data baseline: `e08f5aa538e181ad3a81bdea0851285ac937716f`.

Independent downloads established an upstream timing gap, not a model failure:

| Source | Downloaded UTC | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| [nflverse schedule](https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv) | 2026-11-15 19:23:25 | 2,189,677 | `92455dde6d6dfba95620000af3ae7dba13cd3bb8d15f2ebf3971baa88a934e0a` |
| [2026 nflverse PBP](https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2026.csv.gz) | 2026-11-15 19:23:34 | 9,416,756 | `b29cf0cc8bc90fdd6932d03b98c0b880d02d9829864a66cfe2f819f0bed96978` |

The schedule had 138 scored regular-season games, including NE–DET 10–35. PBP had 137 games and zero NE–DET rows. All 137 terminal rows were `END GAME`, including a tied game. The old parser rejected the entire collection. As a side effect, the latest derived report omitted all prior NFL grades and the original frozen slate. Saved freezes and grade files themselves remained intact.

## Narrow repair

- Keep missing/mismatched games explicitly blocked. A structured partial-data exception carries only independently validated games for grading and all quarantined game IDs/reasons.
- Require a terminal `END GAME` row, matching scores, and existing paired play-count validation. Matching live/truncated scores alone do not qualify. Schema, wrong-season and unknown-team failures remain global failures.
- Never send partial data into replay or new freezing. Read only existing current-week freezes selected by scheduled game IDs, checking original timestamps precede kickoff.
- Keep `v1_status` and `source_status` blocked and the workflow failure visible. Mark grading partial; show original freezes under `frozen_status: preserved`. Store a content-addressed grading-only input snapshot.
- Leave original formulas, confidence availability, immutable ledger behavior and V3 blocker unchanged. Do not infer final results from schedule scores alone or substitute another model/feed.

## Verification before activation

- 36 unit/regression tests passed, including the existing 3,773-game NHL parity check and 11 new NFL tests. New cases cover missing/mismatched/multiple games, matching truncated scores, zero scores, ties, missing counts, global schema failures, immutable freeze/grade bytes, no late backfill, automatic recovery, and January season identity.
- Historical NFL validation remained exact for 2021–25, including the original 2023–25 result **429/671** and 2025 result **142/223**.
- Offline saved-source replay used a **copy** of the data baseline. NHL collection was intentionally skipped and any call to new NFL freezing was forbidden. It restored all **43** prior NFL grades (**31–12**), while NE–DET remained ungraded.
- Original Week 10 freezes were returned unchanged: Nov12 (1 pick), Nov15 (12 picks), Nov16 (1 pick), each originally frozen Nov10 at 17:00:27 UTC. There were **zero new freezes**. All existing audit files were byte-identical; only the copied derived `latest.json` changed, with new append-only run/input/receipt evidence permitted.
- Independent code/test review found and corrected a January calendar-year versus season-year filter; matching schedule game IDs now prevents that issue.

The replay is a repair test, not a new publication or a retrospective forecast. No ticket, bet, user decision, prediction history, or model coefficient was changed. V3 remains unavailable until its original fitted transforms and audit can be recovered. Upstream missing games remain ungraded until complete verified play data arrives.
