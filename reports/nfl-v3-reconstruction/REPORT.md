# NFL V3 Reconstruction — measured results

**Not verified original V3. Production NFL V1 and NHL are unchanged.**

One fixed, predeclared reconstruction; no evaluation-driven tuning. Details: [protocol](../../research/NFL_V3_RECONSTRUCTION_PROTOCOL.md).
Coefficients/scaling: [coefficients.json](coefficients.json). Full [671-game audit](game-audit.csv), [paired weeks](paired-weeks.csv), [calibration bins](calibration.csv) and [validation JSON](validation.json).

| Season | V1 winners | V2 winners | Raw V1 top quarter | Fitted V1 top quarter | V2 top quarter | V3 top quarter |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 133/224 | 132/224 | 42/60 | 42/60 | 46/60 | 46/60 |
| 2024 | 154/224 | 148/224 | 46/60 | 48/60 | 49/60 | 50/60 |
| 2025 | 142/223 | 145/223 | 48/60 | 43/60 | 49/60 | 49/60 |
| Combined | 429/671 | 425/671 | 136/180 | 133/180 | 144/180 | 145/180 |

V3 preserves every V1 winner. Its overall winner accuracy is therefore identical to V1; confidence changes which games enter the top quarter. Fitted V1 uses probability assigned to the original V1 selection, not absolute distance from 0.5.

| Sample | Probability | Brier | Log loss | ECE (10 fixed bins) |
|---|---|---:|---:|---:|
| 2023 | p1 | 0.231418 | 0.654497 | 0.040439 |
| 2023 | p2 | 0.234267 | 0.659297 | 0.038287 |
| 2023 | p3 | 0.231829 | 0.654908 | 0.045888 |
| 2024 | p1 | 0.219059 | 0.628737 | 0.097362 |
| 2024 | p2 | 0.213292 | 0.616387 | 0.096626 |
| 2024 | p3 | 0.215270 | 0.620596 | 0.105779 |
| 2025 | p1 | 0.226071 | 0.641743 | 0.064607 |
| 2025 | p2 | 0.221983 | 0.633034 | 0.069475 |
| 2025 | p3 | 0.223258 | 0.635731 | 0.045563 |
| Combined | p1 | 0.225515 | 0.641659 | 0.040398 |
| Combined | p2 | 0.223183 | 0.636244 | 0.054547 |
| Combined | p3 | 0.223453 | 0.637080 | 0.043966 |

## Original result comparison

Original reported V3: 145/180 (80.6%). Reconstruction: 145/180 (80.56%). Difference: +0 wins.
Paired weekly comparison against fitted V1: 13 improved, 2 worsened, 30 unchanged; net +12 wins. Full membership changes are in paired-weeks.csv.
Against raw V1 (the original 136/180 baseline): 14 improved, 7 worsened, 24 unchanged; net +9 wins.
V2 does not reproduce exactly: 425/671 versus original reported 427/671; reconstructed V2 top quarter 144/180 versus reported 140/180. Thus the matching V3 aggregate is insufficient to claim the original implementation was recovered.
The exact original feature algebra, scaling, regularization and recent decay are missing. These can change fitted probabilities and weekly ordering. Different historical source revisions may also matter. No saved original game-level probability audit exists to attribute the gap uniquely. Matching an aggregate would not establish restoration.
The original 145/180 was chosen after examining several blend ratios. The reconstructed 50/50 ratio is fixed from that evidence, not reselected. The adopted expanding/refit protocol is distinct from the fixed 2021–23 parameters-on-2025 comparison recorded separately in validation.json.

## Recommendation

Keep research-only; do not replace original-V3 unavailable status. Require prospective shadow evidence before promotion.
The historical checks validate arithmetic, chronology and reproducibility; they do not establish a dependable future improvement. Keep the candidate explicitly labelled V3 Reconstruction. The prospective 2026 coefficients use 2021–25 only.
Weekly pool generation is implemented separately and refuses late or incomplete slates. Rank 1 maps to N points by default; a supplied N-value pool scale is supported. No existing freeze or grading record is altered.

## Limits

2023 coefficients use only 2021–22, but model structure was informed by original 2024 research. 2025 is excluded from its own fitting and no new tuning used it, but original 2025 research results were already examined. Future independent shadow weeks are needed. Historical data may include source revisions. Neutral-site games retain nominal home labels, as in the recovered data; no invented home-field overrides are applied.
