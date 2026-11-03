# NHL V7-A — 5-on-5 expected-goals research (2026-10-16)

## Scope
Used user-supplied MoneyPuck shots_2023.zip, shots_2024.zip, shots_2025.zip, matched to existing full-season NHL game CSVs by game ID. All 1,312 regular-season games per season matched; 2025–26 evaluation follows prior established October 15 cutoff. Pregame forecasts use prior games only; same-date updates occur after the date's games.

Evaluation sample: 2023–24 1,259 games; 2024–25 1,258 games; 2025–26 1,256 games = 3,773 predictions. Exclude until both teams have at least three prior games. Nonplayoff, five skaters against five, xGoal sums per team/game from shot-level records.

## Frozen exploratory methods
- V1: original season-to-date goals and shots expected-score equation.
- V6: 20%-update opponent-adjusted shot-difference rating, cap shot-difference/30 to ±1.5; early blending weight 0.8 through 10 prior games, declines linearly to zero at 40.
- V7_xG: same rating update and blend schedule, but performance signal = cap((home 5v5 xG - away 5v5 xG)/2, ±1.5). This is *raw*, not flurry- or score-adjusted xG.
- V7_xGshot_blend: 50/50 shot and xG rolling signal.
- V7_xG20_post40: 20% xG rolling signal retained after both have >=40 games.
- V7_xG_confidence: keep V6 winner below 40 games and V1 winner thereafter, but use 40% xG rolling margin to rank confidence in games >=40.

## Results
|Season|V1 winner|V6 winner|V7 xG winner|V6 top25|V7 xG confidence top25|
|---|---|---|---|---|---|
|2023–24|729/1259|755/1259|738/1259|247/383|257/383|
|2024–25|708/1258|721/1258|735/1258|242/386|249/386|
|2025–26|670/1256|693/1256|694/1256|220/381|230/381|
|Combined|2107/3773|2169/3773|2167/3773|709/1150|736/1150|

Note: V7 confidence top25 changes only rankings, not winner direction in mature season. Results are retrospective and explored against seasons used in prior model development, not fresh independent validation. Rankings are margin-score based, not calibrated probabilities. No betting-return claims.

## Limitations and next tests
- Raw MoneyPuck xGoal, no score adjustments, flurry adjustment, shot-count normalization or special-teams component for V7; full V1 still reflects whole-game scores and shots.
- xG signal was divided by 2 to put it on a rough comparability scale, NOT fitted using a held-out sample.
- Both team ratings initialized neutral, rather than properly estimated preseason prior strength.
- Shot xGoal models can be retrospectively revised; ensure as-of-timestamp availability for strict historical live simulation.
- Opponent update adds the opponent's previous rating; needs stability tests and shrinkage diagnostics.
- No starters, individual goalie GSAx, historical injury replacements, market lines, calibrated probability evaluation yet.
- Current result for V7 xG confidence is a candidate hypothesis; test against a new untouched season with parameters frozen.

Files: v7_xg_test.py, v7_xg_comparison.csv, v7_xg_daily_top25.csv, v7_xg_game_audit.csv. Original V1 and V6 code untouched.
