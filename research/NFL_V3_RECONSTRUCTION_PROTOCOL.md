# NFL V3 Reconstruction protocol — fixed before fitting, 2026-10-23

This is a new, explicitly labelled reconstruction of missing implementation details, not verified original V3. Production NHL/NFL files and existing ledgers are untouched.

## Recovered evidence

`NFL_RESEARCH_CONCLUSIONS.md` and `nfl_model_comparison.csv` identify All_features as the 2024 Brier-optimal model. Its 2024 150/224 and refitted 2025 144/223 agree with the adopted V2 described in the October 16 19:08 UTC conversation. The adopted comparison used 2021–22 -> 2023, 2021–23 -> 2024, 2021–24 -> 2025. Reported V2: 427/671 overall, 140/180 weekly top quarter. The 19:17 UTC conversation reports 50/50 V3 at 145/180 versus V1 136/180; alternative blends were examined. Those are unverified exploratory research figures, not independent holdout evidence.

Recovered: original V1 expected points/winner; minimum three prior regular-season games; exclude tied outcomes from fitting/evaluation; 50/50 home-probability blend; confidence attached to the preserved V1 selection; weekly ceiling(N/4). Tied earlier games remain legitimate pregame team statistics.

Missing: original executable, coefficients, exact feature algebra, recent decay, scaling, regularization, solver, tie-breaking and row-level confidence audit. Library searches and targeted original-conversation recovery found no additional implementation artifact. Aggregate performance does not identify unique coefficients.

## Fixed reconstructed choices (no search against evaluation scores)

Seven home-minus-away features, in this order:

1. Original V1 expected home points minus expected away points.
2. Mean season points scored minus points allowed, home minus away.
3. Season net EPA per play: 60 * (sum offensive EPA / offensive EPA plays - sum defensive EPA / defensive EPA plays), home minus away.
4. Last-four net EPA per play using weights 2^(-age/2), newest age 0; weighted ratios of EPA sums to EPA plays, multiplied by 60, home minus away. Two-game half-life is reconstructed, not recovered.
5. Recent net EPA minus season net EPA, home minus away.
6. Season offensive success rate minus defensive success rate, home minus away; ratios of summed successes and summed eligible plays.
7. Season offensive red-zone TD trips / trips minus defensive TD trips allowed / trips allowed, home minus away. A zero trip denominator uses Jeffreys smoothing (TD+0.5)/(trips+1); only for this zero-denominator case, disclosed and counted.

Opponent-relative means comparing home and away offensive-minus-defensive rates. No recursive schedule-strength adjustment is claimed recovered or added. Feature families are supported by All_features evidence; these precise seven scalar definitions are reconstructed.

P1 = sigmoid(intercept1 + coefficient1 * standardized V1 margin).
P2 = sigmoid(intercept2 + sum(coefficient_j * standardized feature_j)).
P3 = (P1+P2)/2. Confidence = P3 for a V1 home pick, 1-P3 for a V1 away pick. Confidence may be below 0.5; flag disagreement, never flip the V1 winner. P1 confidence uses the same selected-team orientation; absolute raw V1 margin is also reported as a separate baseline.

Fit training-only StandardScaler (population variance); L2 logistic regression C=1, lbfgs, fit_intercept=True, class_weight=None, tol=1e-10, max_iter=10000. No additional calibration layer, no hyperparameter sweep. numpy 2.3.5, scipy 1.17.0, scikit-learn 1.8.0. Serialize means, scales, standardized and raw coefficients to full floating precision. Training seasons start at 2021 and end before the evaluation year. A separate prospective fit uses all 2021–25 and never enters historical evaluation.

Prior-week statistics only, sorted game IDs for deterministic ties; no within-week updates. Model structure already informed by original 2024 research, so 2023 diagnostics are chronological coefficient tests, not evidence of a prospectively selected structure. 2025 is held out from reconstruction fitting/tuning, but its original results have already been viewed. Neither is a newly untouched test set.

## Evaluation and promotion

First assert original V1 2023 133/224, 2024 154/224, 2025 142/223. Report each season and combined: raw V1 winner accuracy, thresholded P1 accuracy, V2 winner accuracy, preserved-winner V3 accuracy; P1/P2/P3 Brier and log loss; ten fixed probability-bin reliability tables/ECE; weekly top-quarter records, membership changes, paired weekly changes and game-level audit. V3 overall winner accuracy must equal V1 exactly.

Keep the 2021–23 fixed-parameter 2025 analysis distinct from the adopted expanding/refitted analysis. No refitting or feature adjustment after results. Do not claim exact restoration merely if a total matches 145/180.

Prospective weekly ranks require complete eligible weekly coverage, all preceding scheduled games final and represented, source score parity, and freeze time before the earliest kickoff (international games included). Rank 1 receives N pool points by default; caller may supply an explicit distinct ascending N-value point scale. Already-started weeks are blocked, never backdated. Research freezes live in a separate research state directory. Do not activate in the production daily launcher unless the evidence supports a clearly labelled reconstruction; preserve the original-V3 unavailable status otherwise.
