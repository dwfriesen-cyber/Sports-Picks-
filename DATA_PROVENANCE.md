# Source and recovery provenance

## Original research recovered from the owner's files

- `HYBRID_INDEPENDENT_VALIDATION.md`, original `independent_hybrid_validation.py`, and 2023–26 NHL goals/shots CSVs.
- `V7_XG_INITIAL_REPORT.md`, original `v7_xg_test.py`, and all 3,773 rows of `v7_xg_game_audit.csv`.
- `ULTIMATE_RESEARCH_CONCLUSION.md` confirms V6 winners/V7-A rankings; challengers are not promoted.
- NFL `RESEARCH_CONCLUSIONS.md` and `model_comparison.csv` recover raw V1 and its validation. They do not contain the fitted transforms needed for V3.

Original research source is retained in `research/`; compressed immutable benchmark fixtures are under `tests/fixtures/`.

## Actual recovery runs

- Original replay: https://github.com/dwfriesen-cyber/Sports-Picks-/actions/runs/39990092754 . Downloaded and inspected its artifact: 122 games and 31 retrospective predictions. Its October 6 history start omitted 43 games and it did not ingest V7-A xG.
- Full source recovery: https://github.com/dwfriesen-cyber/Sports-Picks-/actions/runs/39992591854 . Retrieved September 1–October 23 official daily responses, 165 completed regular-season games, 2 scheduled October 23 games, and MoneyPuck 5v5 xG for all 165 completed games.
- Engineering validation: https://github.com/dwfriesen-cyber/Sports-Picks-/actions/runs/39994234211 . Real NHL freezes recovered from the artifact; NHL and NFL benchmark checks passed. Downloaded raw historical shot archives match all original xG confidence margins. Subsequent commits refine daily NFL freezes and activate the launcher; consult current run evidence.

## Public URLs and rules

NHL: `https://api-web.nhle.com/v1/score/YYYY-MM-DD`. Validate response date, season, game type, IDs, final status and nonnegative integral goals/shots; retain exact UTC puck-drop times.

MoneyPuck: `https://peter-tanner.com/moneypuck/downloads/shots_YEAR.zip`, documented through https://moneypuck.com/data.htm . Sum raw `xGoal` for regular-season shots with five home and five away skaters, preserving the exact original research population. Zero is valid; missing is not zero. Validate team identities against NHL IDs. Credit MoneyPuck.com.

IceScope: https://icescope.app/ and https://icescope.app/methodology . V8 uses the public page's full-precision last-five `xgBalance60`, complete five-game windows and a prior-day data cutoff. Parse JSON, never execute page JavaScript. This metric includes eligible non-empty-net strength states and is distinct from V7-A 5v5 xG sums.

NFL schedule: `https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv`. NFL play-by-play: `https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_YEAR.csv.gz`. Cross-check final scores and paired play counts. Count pass/rush plays with a possession team, excluding `no_play` and two-point attempts, matching the original historical source's aggregation definition. Schedule kickoff times are America/New_York and converted using IANA timezones.

## Preserved historical choices

Published-market and shadow lists were recovered from timestamped prior Daily NHL Picks messages and transcribed on October 23; source-message timestamps and recovery/import timestamps are distinct. Original conversation records were never edited. Historical lists have no newly invented probabilities or reconstructed original feature snapshots. V8 for October 23 keeps its originally published inputs/cutoff even though the source has since updated.
