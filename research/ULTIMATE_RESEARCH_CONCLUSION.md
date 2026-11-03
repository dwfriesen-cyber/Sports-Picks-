# NHL Research Cycle — Experimental Model Comparison

## Decision
Keep **V6 for official experimental winner selection** and **V7-A xG for the current confidence-ranking research benchmark**. Do not promote the newer fitted statistical ensemble to production. It is a promising challenger, particularly for early-season games, but the gain is small, unstable, and probability calibration is inadequate. No live NHL or NFL formula has been modified.

## Inputs and chronological methodology
- Data: 2023–24, 2024–25, 2025–26 season game results (goals, shots, teams, dates) and pregame-derived 5v5 xG rolling ratings from MoneyPuck shot archives. The rolling xG ratings were computed strictly from previous dates' games; the archive's estimates could nevertheless have undergone retrospective revisions.
- Candidates: V1, V6 hybrid, shot differential, xG differential, simplified score/flurry xG, goalie GSAx proxy (previous starter), rest, prior recent wins/losing streaks, past 10-game performance and opponent-adjusted residuals.
- Model-selection protocol: train alternative regularized logistic models on 2023–24, choose by lowest Brier score on 2024–25, then report 2025–26. Additionally refit the selected fixed configuration on 2023–24 plus 2024–25 before assessing 2025–26. Selection on 2024–25 is not genuine independence from all past research, as all three seasons have already been explored extensively in previous work.
- No actual-starter hindsight feature is used. Goalie feature is prior-date quality of team's previously starting goalie, not a confirmed starter.
- Per-day top 25%: rank within date and select ceiling(25% of games). Counts include only games with adequate rolling history and match prior V6 test window.

## Baseline and selected model results
| Model | 2024–25 all games | 2024–25 daily top quarter | 2025–26 all games | 2025–26 daily top quarter |
|---|---|---|---|---|
| V1 | 708/1258 = 56.28% | 238/386 = 61.66% | 670/1256 = 53.34% | 216/381 = 56.69% |
| V6 frozen | 721/1258 = 57.31% | 242/386 = 62.69% | 693/1256 = 55.18% | 220/381 = 57.74% |
| V7-A xG confidence ranking, V6 winners | 721/1258 = 57.31% | 249/386 = 64.51% | 693/1256 = 55.18% | 230/381 = 60.37% |
| Full ridge, trained on 2023–24 only | 750/1258 = 59.62% | 279/386 = 72.28% | 691/1256 = 55.02% | 241/381 = 63.25% |
| Full ridge, refit on 2023–24+2024–25 | in-sample, omit | in-sample, omit | 699/1256 = 55.65% | 235/381 = 61.68% |

The refit model outperformed V6 by 6 selections in 2025–26, but it was 57.68% versus V6's 59.64% on 664 mature-season games; early-season performance rose to 53.38% from 50.17%. Of its 381 selected games, 233 were correct if we preserved V6's winner, so much of its selection advantage comes from improved confidence ranking rather than winner reversal. Its top-quarter average declared win probability is 68.1%, versus a realized 61.68%. **Do not treat these numbers as calibrated probabilities.**

In 2025–26 the 2023-only-trained selected logistic model versus V6 was 159 better decisions and 161 worse decisions across discordant games (paired sign-test p≈0.96). With refitting, the whole-slate difference is only 6 wins; this is too small to establish superiority.

## Factors and failure analysis
- **Recent form, bounce-back, prior H2H**: prior standalone ablations failed to beat V1/V6 consistently; useful to test as indicators, not justified automatic adjustments.
- **Shot/xG ratings**: V6 rolling shot feature improved over V1 on all three studied seasons, while xG rating was best used in confidence ranking, not as a wholesale winner replacement.
- **Score and flurry adjustments**: historical approximations did not improve V7-A; official retrospective score/flurry adjusted xG is not yet available in the model.
- **Goalie estimates**: historically lagged starter/goalie quality did not consistently improve predictions. Historical *actual* goalie as a feature is hindsight and must not enter normal pregame models.
- **Rest and home**: prior fixed rules were not consistently valuable; fitted coefficients can only be trusted after additional prospective evaluation.
- **Ensembles**: the full ridge model improved 2024–25 considerably but did not yield a stable improvement in 2025–26. Refitting mitigated some drift, at the expense of confidence calibration.

## Remaining missing evidence
Actual confirmed goalie forecast snapshots and times; historical injury and lineup forecasts; opponent-strength-adjusted 5v5 shot quality using fully timestamped xG; reliable historic pregame sportsbook odds; external seasons entirely untouched by any model development; 2026–27 prospective forecasts. Statistical uncertainty is substantial for differences of 6 games or 5–11 daily top-quarter picks.

## Recommendation
1. Keep **V6 winner model** and **V7-A raw 5v5 xG confidence ranking** as frozen research leaders.
2. Shadow-test the **regularized multi-feature challenger** with probabilities marked provisional. Do not report them as true win percentages without calibration.
3. Log predictions and data timestamps prospectively during 2026–27 and validate by season stage, daily top quarter, Brier, log loss and comparison with no-vig sportsbook odds.
4. Preserve original V1 and all prior experimental variants; no production deployment authorized.
