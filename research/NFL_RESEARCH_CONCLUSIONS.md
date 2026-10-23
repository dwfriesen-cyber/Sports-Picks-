# NFL Five-Season Research — 2026-10-16

## Data and source

Historical team game context from `antonwilms/sleeper-dashboard-data`, paths `nflverse/teamcontext/{2021,2022,2023,2024,2025}.json` (derived from nflverse play-by-play): https://github.com/antonwilms/sleeper-dashboard-data . Original upstream: https://github.com/nflverse/nflverse-data . Data includes per-team regular-season plays, scoring, EPA, success rate and red-zone summaries. No verified historical pregame injury, QB availability, timezone travel, weather or bookmaker odds were supplied.

## Sample

2021: 272 regular-season games, 224 eligible before removing one tie; 2022: 271 games, 223 eligible before removing one tie; 2023: 272 games, 224 eligible; 2024: 272 games, 224 eligible; 2025: 272 games, 224 eligible before removing one tie. Eligible games have both teams with at least three earlier regular-season games in that season. Modeling excludes ties: 2021–23 development n=669, 2024 selection n=224, 2025 untouched holdout n=223. Weekly rather than daily top-25% used because the source lacks actual game dates.

## Original V1

For team A versus B, predicted points A = 0.5 × [(B defensive points allowed / B defensive plays) × A offensive plays/game + (A offensive points scored / A offensive plays) × B defensive plays/game]. Use only games before the matchup. Winner = team with higher predicted points. This implementation uses *team-scored points* in the nflverse-derived game data, which matched opponents' allowed points in the matched sample. Do not assume it perfectly replicates every historical scoring-play edge case in earlier conversational tests.

## Experimental approaches

Features: V1 predicted home-minus-away point margin; season-to-date scoring differential; season-to-date offense-minus-defense EPA/play scaled by 60; exponentially weighted last-four games EPA/play; recent-minus-season EPA trend; season-to-date offensive vs defensive success rates; red-zone TD conversion vs TDs allowed; and constant home intercept. No hypothetical fixed-point bonuses. Penalized logistic regressions trained on 2021–23; compared on 2024 using Brier score, then refitted to 2021–24, evaluated on 2025. Calibration is from logistic training; check out-of-sample Brier and log loss.

## Key results

2025 raw original V1: 142/223, 63.68%. Raw-margin confidence top weekly quartile: 48/60, 80.0% (using logistic monotonic transform).

2025 recalibrated original V1 (trained 2021–24): 139/223, 62.33%, Brier .2261, log loss .6419, top 43/60, 71.67%.

2025 all-features challenger retrained 2021–24: 144/223, 64.57%, Brier .2218, log loss .6327, weekly top 47/60, 78.33%.

2025 2021–23-only frozen parameters (no refit): all-features 142/223 (63.68%), Brier .2238, top 50/60 (83.33%); original V1 logistic 139/223, Brier .2272, top 45/60 (75.0%). Because model candidates were examined using the same held-out 2025 results, treat this as a single research evaluation and do not select post-hoc the higher-performing configuration.

Full validation and fixed evaluation matrix in model_comparison.csv. The 2024 Brier-optimal configuration was all-features, although red-zone configuration had more winning picks. This illustrates why winner accuracy alone can be misleading.

## Decision

Do not replace original NFL V1. The best chronological challenger shows +2 raw-winner hits over V1 in 2025; this is not statistically convincing. It also did not surpass raw V1's weekly top-quarter record after the 2021–24 refit. EPA-recent, success-rate, and red-zone are sensible research signals, but mixed season-level results do not demonstrate dependable gains. Preserve independent raw predictions and rank confidence separately. Historical starting QBs, active rosters, injury reports, travel, market no-vig odds, and weather are needed for a complete test of Walters-style game-specific effects.

## Caveats

* This is **not** an all-weeks or all-games backtest; excludes weeks before both clubs played three games and ties.
* No preseason priors. NFL game IDs identify home teams, but do not carry kickoff time or weather.
* Top quarter chosen **by NFL week**, not calendar day; rounding up per week.
* Regression models use only historical games before each forecast for predictors, with model coefficients learned from prior seasons. Season-wise validation is held out, but the research process is exploratory.
* The 2024 and 2025 outcomes have now been studied; future independent seasons are required to prove selected gains.
* No claims of betting profit, because archived point spreads, opening/closing lines and bet prices were not incorporated.
