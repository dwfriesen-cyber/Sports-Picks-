# Executable fitted probabilities

All coefficients below are fitted reconstruction values, not recovered original coefficients. Full-precision scaling and coefficients are in [coefficients.json](coefficients.json). Feature definitions are fixed in [the protocol](../../research/NFL_V3_RECONSTRUCTION_PROTOCOL.md).

For unstandardized input features x, use sigmoid(z) = 1/(1+exp(-z)). P1 = sigmoid(b1 + a1 * V1 margin); P2 = sigmoid(b2 + sum(a_j*x_j)); P3 = (P1+P2)/2. Attach P3 to a V1 home pick and 1-P3 to a V1 away pick. Do not change the V1 winner.

## 2023 evaluation / prospective model

Training seasons: [2021, 2022]; games: 445.

| Term | P1 raw coefficient | P2 raw coefficient |
|---|---:|---:|
| Intercept | 0.1924265132153502 | 0.19800535588346513 |
| v1_margin | 0.11036758654931525 | -0.053285077370518442 |
| scoring_net | 0 | 0.061770002032358481 |
| epa_net | 0 | -0.0034134631971811202 |
| recent_epa_net | 0 | 0.0055278619961170025 |
| epa_trend | 0 | 0.019565751752383662 |
| success_net | 0 | 3.7427488192999774 |
| redzone_net | 0 | -0.24570115035330337 |

## 2024 evaluation / prospective model

Training seasons: [2021, 2022, 2023]; games: 669.

| Term | P1 raw coefficient | P2 raw coefficient |
|---|---:|---:|
| Intercept | 0.23538852898631207 | 0.23890562754587458 |
| v1_margin | 0.1075508721304811 | -0.053077580087180394 |
| scoring_net | 0 | 0.079949087401265731 |
| epa_net | 0 | -0.011352045996371936 |
| recent_epa_net | 0 | -0.002263496695348591 |
| epa_trend | 0 | 0.013478477496087169 |
| success_net | 0 | 4.3396059030729877 |
| redzone_net | 0 | -0.68086935166859153 |

## 2025 evaluation / prospective model

Training seasons: [2021, 2022, 2023, 2024]; games: 893.

| Term | P1 raw coefficient | P2 raw coefficient |
|---|---:|---:|
| Intercept | 0.22830960483380497 | 0.22909046769277325 |
| v1_margin | 0.12392567586963125 | -0.091722655118015584 |
| scoring_net | 0 | 0.096911177364705156 |
| epa_net | 0 | -0.0051192223356587236 |
| recent_epa_net | 0 | 0.00087728648311131638 |
| epa_trend | 0 | 0.011148987925601353 |
| success_net | 0 | 4.6966576103344773 |
| redzone_net | 0 | -0.68905890435626027 |

## 2026 evaluation / prospective model

Training seasons: [2021, 2022, 2023, 2024, 2025]; games: 1116.

| Term | P1 raw coefficient | P2 raw coefficient |
|---|---:|---:|
| Intercept | 0.2154813347256154 | 0.21078557597343844 |
| v1_margin | 0.12896076790077038 | -0.12407816225277445 |
| scoring_net | 0 | 0.11157683533149942 |
| epa_net | 0 | -0.0029610220475908243 |
| recent_epa_net | 0 | 0.0029416282053423945 |
| epa_trend | 0 | 0.012941500945329155 |
| success_net | 0 | 4.2520233473392466 |
| redzone_net | 0 | -0.62198483891849921 |

