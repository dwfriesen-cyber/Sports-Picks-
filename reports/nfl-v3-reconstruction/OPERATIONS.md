# NFL V3 Reconstruction — execution and weekly operation

## Recovery status

| Component | Status |
|---|---|
| V1 expected points and official winners | Recovered; original benchmarks reproduced, unchanged |
| V3 50/50 blend and selected-team confidence orientation | Recovered from original research and owner specification |
| Adopted V2 family | All_features identified from the saved model comparison and adopted research results |
| Exact V1/V2 fitted coefficients, feature algebra, decay, scaling and regularization | Missing; reconstructed choices explicitly fixed in the protocol before fitting |
| Original 145/180 V3 and 136/180 raw V1 totals | Both reproduced by the first fixed reconstruction |
| Exact original V2/V3 implementation | Not verified: reconstructed V2 425/671 and top 144/180 differ from reported 427/671 and 140/180 |

## Executed validation

[Tested source 422b416](https://github.com/dwfriesen-cyber/Sports-Picks-/commit/422b416db9dce4c03b0c141af22391ef6c7045f8).

[GitHub validation run 40000319354](https://github.com/dwfriesen-cyber/Sports-Picks-/actions/runs/40000319354) succeeded:
- All 25 existing NHL/NFL V1 tests passed.
- Ten new tests passed: prior-week isolation, missing inputs, ties, winner preservation under disagreement, fitted scaling/serialization, training-year leakage, immutable weekly freezes, international kickoff deadlines, incomplete/stale source rejection, deterministic ranks and pool scales.
- Fresh downloads from the pinned historical source reproduced coefficients, all season metrics, calibration bins and weekly selected-game memberships.
- All 671 evaluation predictions are saved in game-audit.csv; the artifact contains the same audits and full coefficients.
- Fresh 2026 play-by-play produced 94 completed games and 46 eligible feature rows. Every game matched the existing V1 adapter's points and play counts, and EPA/success/red-zone features passed validation.
- Current weekly generation correctly refused to backdate a week whose first kickoff had already occurred.

Original source SHA: 5231fb4c22923a344504fefdfe4b1520714dd5db. Each source file's SHA-256 is saved in validation.json; local files also matched the upstream Git blob identities exactly. Historical source revisions remain a limitation of any retrospective reconstruction.

## Independent shadow operation

[Launcher commit 4b9d29d](https://github.com/dwfriesen-cyber/Sports-Picks-/commit/4b9d29de68a6bf28239e61d4ed8aaba1d18b35d3) pins the validated source. It uses standard public GitHub runners and runs daily at **06:10, 06:30 and 06:50 America/Regina** (cron `10,30,50 12 * * *`). Daily checks freeze the next complete week as soon as the previous week has finished, accommodating Thursday, international and unusual early kickoffs. The existing official 06:00 workflow is unchanged.

[Shadow launcher run 40000561044](https://github.com/dwfriesen-cyber/Sports-Picks-/actions/runs/40000561044) succeeded and persisted an honest blocked status to [data commit 5b703ec](https://github.com/dwfriesen-cyber/Sports-Picks-/commit/5b703ec94373c2a9b99e52c4dfa7297884664517). No current-week pool was fabricated. The next valid prospective freeze remains to be observed; first scheduled execution is also still in the future.

Separate [research data branch](https://github.com/dwfriesen-cyber/Sports-Picks-/tree/nfl-v3-research-data):
- [latest.json](https://raw.githubusercontent.com/dwfriesen-cyber/Sports-Picks-/nfl-v3-research-data/latest.json): experimental status and, when valid, frozen slate.
- `frozen/2026-WNN.json`: original V1 winners, P1/P2/P3, V3 confidence, disagreement flag, ranks, top-quarter flags and pool points; write once.
- `inputs/<sha256>.json`: source team context, schedule and fitted model for replay.
- Existing freezes return byte-identically on retry. Modified/deleted audit files are rejected by the publishing guard.

Default pool points are N down to 1 in descending confidence order. The CLI accepts an explicit ascending N-value scale through `--pool-scale`. Weekly eligibility and full-slate coverage are enforced; no missing team is assigned a fake confidence. A late or incomplete week is blocked. This branch is entirely separate from official picks-data and existing grading records.

The 07:00 ChatGPT task has not been modified. Research results are not silently inserted into that report or labelled original V3.

## Recommendation

Do **not** replace the official original-V3 unavailable status yet. Keep the validated reconstruction running separately to collect prospective confidence rankings. It matched 145/180 without tuning, but aggregate parity cannot prove the original formula, the V2 audit differs, and the old blend was selected after examining historical outcomes. It is useful as a clearly labelled research confidence model; it is not yet verified original V3 or demonstrated future improvement.

Exact executable feature definitions are in research_v3/model.py and the protocol. Full fitted coefficients for each historical fold and the 2026 prospective fit are in coefficients.json and COEFFICIENTS.md. No NHL formula, NFL V1 formula, official frozen pick, or historical grade was modified.
