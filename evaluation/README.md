# Independent evaluation and odds archive — draft, isolated

This research-only module is intentionally separate from the production NHL/NFL engines, \`picks-data\` branch, Daily Edge reports and both betting ledgers. **No automatic collection, model promotion, live odds source, sportsbook connection, scheduled job, or Daily Edge integration is installed.** Do not merge or activate without a review of provenance and acceptance tests.

## Two independent scoreboards

**Winner prediction**: matched game-ID comparisons, exact frozen winners, accuracy on the shared set, and disagreements. NHL V6/V7-A and V8-lite can be compared from their existing immutable dated freezes. Never compare NFL and NHL as if they were the same competition. V7-A is a ranking score, not a probability; original NFL V3 remains blocked.

**Betting profitability**: separate quoted prices and tickets. \`independent.py\` supports descriptive singles and precommitted parlay settlement, but does **not** estimate calibrated probabilities, EV, Kelly fractions, closing-line value, statistical confidence intervals, or risk-adjusted superiority. These require additional genuine point-in-time market data. Do not optimize or promote a strategy from these descriptive results.

## Data contracts

- \`--freeze\`: one or more existing frozen files from \`picks-data/frozen/nhl/YYYY-MM-DD.json\` and \`picks-data/frozen/v8/YYYY-MM-DD.json\` (or same-sport NFL freezes). Must have \`kind\`, \`frozen_at\`, \`picks\` with game ID, winner, participants, eligibility, start time. Freeze must predate kickoff.
- \`--outcomes\`: JSON array of independently verified \`{"game_id":"...","winner":"TEAM"}\`. Missing results are excluded, not counted as losses. Record original result source and retrieval timestamp separately.
- \`--quotes\`: JSON array of observed quotes. Every quote requires \`quote_id\`, \`game_id\`, \`book\`, \`market:"full_game_moneyline"\`, \`selection\`, \`decimal_odds\`, \`observed_at\` with UTC offset, \`source_url\`, \`status:"observed"\`, \`executable:true\`. These assertions must be supported by a sportsbook API receipt or contemporaneous screenshot. A web article's indicative line is **not** an executable quote. The evaluator will not manufacture prices.
- \`--tickets\`: JSON array of immutable hypothetical ticket versions, each with \`date\`, integer \`version\`, \`status\` (only one active per date), \`published_at\`, positive \`stake\`, and at least two \`legs\` with \`game_id\`, \`home\`, \`away\`, \`selection\`, \`quote_id\`, \`start_time\`. Superseded versions are preserved but not graded as additional tickets.
- \`--owner-pending\`: optional JSON array of game IDs from the actual pending PlayNow ledger; if a proposed active hypothetical duplicates a pending game, evaluation fails. Never derive this list from stale settlement snapshots without review.

Quote observations after kickoff, or before a pick's freeze when scoring singles, cannot be used as if they were available at pick time. Singles choose the earliest eligible observed quote after the freeze rather than the best hindsight price. Tickets require the quoted price to be available no later than their actual publication time. No quote matching = **unpriced**, not zero profit.

### Read-only evaluation

\`\`\`bash
python -m unittest discover -s evaluation -v
python evaluation/independent.py \
  --freeze frozen/nhl/2026-10-28.json \
  --freeze frozen/v8/2026-10-28.json \
  --outcomes /path/to/verified-results.json
\`\`\`

Run with \`--quotes /path/to/verified-quotes.json\` to add descriptive single-bet results. Add \`--tickets\` and \`--owner-pending\` to grade already-published hypothetical versions. The command prints JSON to stdout; it does not write to a ledger.

### Explicit opt-in quote archive

\`\`\`bash
python -m evaluation.archive_quote \
  --input /path/to/verified-receipt.json \
  --archive-dir /path/to/local-research-odds
\`\`\`

The archive writes a SHA-256 content-addressed JSON receipt using exclusive creation; identical repeats fail rather than overwrite. This is a local research archive, not a market feed. Do not put private PlayNow screenshots, account identifiers, or unredacted receipts in a public GitHub repository.

## Required next gates before production use

1. Independently execute tests and run matched-game comparisons against existing immutable freeze fixtures.
2. Add same-game, same-deadline calibration analysis only after obtaining genuine probabilities; never treat V7-A ranking scores or NFL V1 margins as probabilities.
3. Establish an approved timestamped odds provider and its terms, with observable pregame and closing prices, source IDs, market definitions, book, and quote latency. No retroactive price reconstruction.
4. Reconcile hypothetical ticket versions and operator settlements without changing originals. Keep owner cash wagers in a separate, access-controlled ledger.
5. Evaluate predetermined singles/doubles/triples on forward-only chronological splits with ROI, max drawdown, confidence intervals, bookmaker vig and correlation; permit no-bet outcomes.
6. Review evidence and explicit promotion criteria before adding any Daily Edge display or scheduling. Keep the 6 AM model job and 7 AM report task separate.

## Scope limitations

This prototype is intentionally strict and incomplete: it only supports full-game moneylines, requires user-supplied genuine quote receipts, and has no autonomous collection or bankroll-risk simulation. Missing prices are reported as gaps. It is not proof of profitable betting.
