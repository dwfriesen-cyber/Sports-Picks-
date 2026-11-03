# Frozen NHL hybrid multi-season validation

## Method

This study applies the existing 2025-26 V1 and V6 rolling-shot hybrid rules unchanged to independently supplied 2023-24 and 2024-25 regular-season game records (1,312 games each). Games scored only if both opponents had >=3 previous games, mirroring the 2025-26 evaluation start of October 15. Calculations use only dates earlier than the predicted game. Same-day ratings and team history are updated after every game on the date has been predicted. Scores include overtime/shootout outcomes as represented by the source. No historical goalie, injury, xG, or betting line factors are included.

V1 predicts the difference of expected goals computed using season-to-date goals-per-shot, goals-allowed-per-shot, shots-per-game, and shots-allowed-per-game.

Rolling rating: start each team rating at zero. Shot-differential signal = clip((home shots - away shots)/30, -1.5, 1.5). Home rating next = 0.8 * old home rating + 0.2 * (signal + old away rating), and similarly away with negative signal and old home rating. Rating margin = 1.5 * (home rating - away rating).

V6 blend: weight 0.8 for minimum prior-games <=10, linearly declining to 0 at 40, then V1 alone. Post-40 variants replace the 0 with 0.2, 0.4, or 0.8, leaving earlier blending unchanged.

Top 25%: ceiling of one quarter of the day's eligible games, sorted by absolute predicted margin. Confidence-only variant uses 40%-rolling blended margin for ranking but V1 winner at 40+ games (and V6 winner under 40). For top-25 tests, the denominator differs from the previously reported October-15 window in prior seasons because eligibility uses >=3 prior games for each matchup.

## Main results

| Season | Eligible | V1 | V6 stop-40 | V6 +20% mature | V6 +40% mature | V6 +80% mature |
|---|---:|---:|---:|---:|---:|---:|
| 2023-24 | 1,259 | 729 | 755 | 749 | 750 | 761 |
| 2024-25 | 1,258 | 708 | 721 | 727 | 724 | 726 |
| 2025-26 (previously studied) | 1,256 | 670 | 693 | 694 | 677 | 674 |

2023-24 and 2024-25 combined: V1 1437/2517 (57.09%); V6 1476/2517 (58.64%). V6 improves by 39 winners, +1.55 percentage points. A simple game-level paired standard-error approximation gives 95% interval about +0.56 to +2.54 percentage points, although games are serially dependent and the choice of settings was informed by 2025-26, so this is not a complete uncertainty assessment.

Under-40: 2023-24 V1 335/602 vs V6 361/602; 2024-25 326/596 vs V6 339/596. Mature 40+: by construction V6 stop-40 equals V1 (2023-24 394/657, 2024-25 382/662).

## Daily top 25% (both older seasons combined)

- V1 picks: 484/769 (62.94%).
- V6 stop-40: 489/769 (63.59%).
- V6 +20%: 492/769 (63.98%).
- V6 +40% changing winner: 507/769 (65.93%).
- V6 +80%: 491/769 (63.85%).
- V6 with 40%-rolling ranking but V1 winner after game 40: 504/769 (65.54%).

The confidence-only method selects 20 additional correct winners from the same number of picks relative to V1 ranking. This result is promising but the confidence variants were previously compared on 2025-26, and still need prospective evaluation, probability calibration, daily-block uncertainty, and sportsbook odds checks before production.

## Limitations and next steps

This is a test of frozen rules derived from 2025-26, not a reconstruction of Billy Walters' proprietary model. The older seasons are independent of the parameter selection on 2025-26, but settings like the 40-game cutoff were informed by it. The provided CSVs have goals, shots, dates, teams, but no goalies, lineups, expected goals, shot locations, or odds. This run did not fit or evaluate probabilistic calibration, expected profitability, or bet value. No official model was changed. Further work should use chronologically earlier seasons for parameter development, 2026-27 prospective validation, and independent sportsbook odds comparisons.
