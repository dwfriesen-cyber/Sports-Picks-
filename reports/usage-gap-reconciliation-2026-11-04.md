# Usage-gap reconciliation — November 4, 2026

**Status:** Evidence-based proposed reconciliation, prepared in a review branch. Does not modify original frozen model predictions, grading artifacts, schedules, model code, or previously published Daily Edge messages.

## 1. Verified prediction outcomes

The official `picks-data/frozen/nhl/2026-11-03.json` was frozen at **2026-11-03 18:39:23 UTC (12:39 PM Saskatchewan)**, before puck drop, but after the 7 AM Daily Edge. The original NHL V6 choices were:

| Original V7-A rank | V6 pick | Final winner | Grade |
|---:|---|---|---|
| 1 | Minnesota | Minnesota | W |
| 2 | Montreal | Winnipeg (5–4 OT) | L |
| 3 | Colorado | Columbus (7–2) | L |
| 4 | Carolina | Nashville (4–1) | L |
| 5 | Utah | Utah | W |
| 6 | Washington | Dallas (6–5) | L |
| 7 | Anaheim | Anaheim | W |
| 8 | Vegas | Vegas | W |
| 9 | NY Rangers | NY Rangers | W |
| 10 | New Jersey | New Jersey | W |
| 11 | Detroit | Tampa Bay | L |

**Nov 3 original V6: 6–5 overall, 1–2 top-quarter.** V8-lite, frozen 12:39 PM Saskatchewan, went **7–4 overall, 1–2 top-quarter**. These are independently outcome-graded, not an alteration of GitHub's original freeze or an assertion that the next 6 AM grading job ran.

From the last machine-readable GitHub graded summary through Nov 2, original prospective NHL V6 was 44–26 overall and 15–6 top-quarter. Adding the independently verified Nov 3 results yields **50–31 (61.73%)** overall and **16–8 (66.67%)** top-quarter, pending canonical grading publication. V8-lite's equivalent totals become **50–29 (63.29%)** and **15–8 (65.22%)** over its shorter prospective coverage (Oct 24 onward). These have **different start dates**, so no direct superiority conclusion follows.

Evidence: [Original V6 freeze](https://github.com/dwfriesen-cyber/Sports-Picks-/blob/picks-data/frozen/nhl/2026-11-03.json), [V8 shadow freeze](https://github.com/dwfriesen-cyber/Sports-Picks-/blob/picks-data/frozen/v8/2026-11-03.json), [Canadian Press Nov 3 final scores](https://infonews.ca/news/7969603/scores-and-sports-schedule-for-tuesday-nov-3-2026/).

### NFL Week 9 recovery

The original NFL V1 freezes for **Nov 5, Nov 8, Nov 9** were created on Nov 3 at 18:39 UTC. They contain 1 + 13 + 1 = **15** genuine Week 9 selections. Original NFL V3 fitted transforms are still unavailable. These selections were not available in the November 3 morning report, but are now available for the next Daily Edge. Do not invent V3 confidence probabilities.

**Important reporting defect:** `latest.json.prospective_summary.nfl_v1_only.weekly` groups by ISO calendar week rather than NFL competition week. Calendar 2026-W44 includes Oct 26's **Week 7** Monday game and the Thursday/Sunday **Week 8** games; calendar W45 includes Nov 2's **Week 8** Monday game. Consequently, the GitHub calendar-week value **11–3** is *not* NFL Week 8. Genuine Week 8 finished **10–4** (GB Thursday 1–0, Sunday 9–3, SEA Monday 0–1). Repair should be separately tested without changing original frozen predictions.

### Publication reliability

The Nov 3 model was published late (12:39 PM Sask.), but pregame. The 7 AM edition correctly could not use it. The Nov 4 6 AM target had **not yet occurred** when this reconciliation was prepared around 5:44 AM Saskatchewan. Do not report Nov 4 as a missed run prematurely. Inspect scheduled workflow run history after 6 AM before assigning cause. The pinned model's workflow describes 6 AM with recovery at 6:20 and 6:40; do not confuse model scheduling with 7 AM report delivery.

## 2. Assistant hypothetical tickets — preserve every version

These were published in chat reports, not necessarily recorded in the canonical assistant ledger. Outcome grades below are **game-result observations only**. A same-day original and later proposed revision are **not two separate $2 tickets**. Do not retroactively select the profitable version.

| Date | Published or proposed combination | Outcome | Official active version? |
|---|---|---|---|
| Oct 23 | Montreal / Milwaukee / NC State | Lost (NC State) | Yes, ledger v1; temporary Raptors v2 superseded |
| Oct 24 | Minnesota NHL / Pittsburgh NHL | Both won | Proposal only, not frozen |
| Oct 25 | SF / Minnesota Vikings / Carolina | Lost (SF, Carolina) | Yes, active revised ledger v2; original SF/KC v1 superseded |
| Oct 26 | Toronto / NY Rangers / Dallas | Lost | Report-published, not in ledger |
| Oct 27 | Anaheim / Montreal / Florida | Lost (Anaheim) | Report-published, not in ledger |
| Oct 28 morning | Washington / Colorado | Both won | Original morning report, not in ledger |
| Oct 28 later | Washington / New Jersey | Lost (New Jersey) | Later proposed revision, active status not established |
| Oct 29 morning | Carolina / Tampa Bay | Both won | Original morning report, not in ledger |
| Oct 29 later | Carolina / Minnesota / Washington | Lost (Minnesota) | Later proposed revision, active status not established; matches actual owner's separate ticket |
| Oct 30 | New England / Jacksonville / LA Rams | All won | Report-published, not in ledger |
| Oct 31 | Dallas / Buffalo / Pittsburgh | Lost (Dallas) | Report-published, not in ledger |
| Nov 1 | New England / LA Rams / Dallas | Lost (Dallas) | Report-published, not in ledger |
| Nov 2 | Seattle / Colorado | Lost (Seattle) | Report-published, not in ledger |
| Nov 3 | Carolina / Minnesota | Lost (Carolina) | Report-published, not in ledger |

The **canonical assistant ledger** can safely grade the Oct 25 active v2 loss without choosing a later winner. This review branch updates its saved settled record from **0–1, -$2** to **0–2, -$4** with original versions unchanged. Remaining report-published versions are not silently counted until original timestamps, bookmaker quotes and active-version rules are reconciled. No hypothetical starting bankroll was approved.

## 3. Actual PlayNow tickets — game result versus sportsbook settlement

The original PlayNow `settled` list remains unchanged at **2–11**, $68 settled stakes, $39.77 returns, **-$28.23** settled net. The saved `pending` list now includes four tickets, **$9 total stake**, each with a decisive on-field losing leg but without independently verified PlayNow operator settlement:

| Date | Real ticket | Decisive losing leg | Stake |
|---|---|---|---:|
| Oct 24 | PIT Penguins / MIN Wild / KC +2.5 | KC lost 3–20 to SEA, fails +2.5 | $2 |
| Oct 25 | PIT Steelers / BAL / CAR / CLE / SF | BAL, CAR and SF lost | $3 |
| Oct 25 | SF / FLA / COL / MIN Wild | SF lost 20–29 to ATL | $2 |
| Oct 29 | CAR Hurricanes / MIN Wild / WSH Capitals | MIN lost 3–4 OT to NYI | $2 |

The **Oct 29 real ticket** is added from owner-provided screenshot evidence: placed at 4:14 PM Saskatchewan, individual decimal odds **1.39 / 1.51 / 1.90**, displayed combined **4.02**, $2 stake, potential total payout **$8.04**, cash-out offer **$1.56** at the 5:28 PM screenshot, and account balance **$12.77** at that instant. This is **not a current balance** and is not a second hypothetical wager.

If all four tickets are later operator-confirmed settled losses, the illustrative settled record would become **2–15**, $77 stakes, $39.77 returns, **-$37.23 net**, ROI **-48.35%**. These illustrative figures are **not** the saved settled ledger until settlement evidence arrives.

Do not merge owner wagers and hypothetical tickets. Do not infer deposits, cash-outs, boosts, or sportsbook settlements from game scores alone.

## 4. Follow-up before merging

- Review the Oct 29 screenshot-derived ticket fields and check PlayNow operator-settlement receipts if available.
- Confirm which report-published hypothetical versions were truly active before kickoff; do not select hindsight winners.
- Validate the next canonical NHL grading update against the Nov 3 game IDs; keep original freeze unchanged.
- Investigate NFL calendar-week versus competition-week reporting as a separate bugfix.
- Check the Nov 4 morning workflow only after its 6 AM target/recovery window.
- No new scheduled task is required.
