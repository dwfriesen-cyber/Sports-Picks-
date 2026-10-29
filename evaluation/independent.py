"""Read-only evaluation of immutable sports picks and timestamped odds.
No network, no model execution, no writes. Standard library only.
"""
import argparse
import datetime as dt
import json
import math
from collections import defaultdict
from pathlib import Path


def instant(value):
    if not isinstance(value, str):
        raise ValueError("Missing ISO timestamp")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must have UTC offset")
    return parsed.astimezone(dt.timezone.utc)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def freeze_rows(path):
    data = load_json(path)
    if data.get("kind") not in {"nhl_v6_v7a", "nhl_v8_lite", "nfl_v1_only"}:
        raise ValueError("Unrecognized immutable freeze kind")
    frozen = instant(data["frozen_at"])
    rows = []
    for p in data["picks"]:
        start = instant(p["start_time"])
        if frozen >= start:
            raise ValueError("Freeze was not before kickoff: " + p["game_id"])
        if not p.get("eligible", False) or p.get("winner") not in {p["home"], p["away"]}:
            raise ValueError("Ineligible or invalid frozen pick")
        rows.append(dict(p, kind=data["kind"], frozen_at=data["frozen_at"]))
    return rows


def compare(freeze_files, outcomes):
    """Compare only identical game IDs with verified results; do not treat gaps as losses."""
    actual = {o["game_id"]: o["winner"] for o in outcomes}
    if len(actual) != len(outcomes):
        raise ValueError("Duplicate result ID")
    by_model = defaultdict(dict)
    for path in freeze_files:
        for row in freeze_rows(path):
            key = row["game_id"]
            if key in by_model[row["kind"]]:
                raise ValueError("Duplicate model/game freeze: " + key)
            by_model[row["kind"]][key] = row
    models = sorted(by_model)
    shared = set.intersection(*(set(by_model[m]) for m in models)) & set(actual) if models else set()
    metrics = {}
    for model in models:
        entries = by_model[model]
        graded = sorted(set(entries) & set(actual))
        correct = sum(entries[g]["winner"] == actual[g] for g in graded)
        common_correct = sum(entries[g]["winner"] == actual[g] for g in shared)
        metrics[model] = dict(graded=len(graded), correct=correct,
                              accuracy=correct / len(graded) if graded else None,
                              matched_games=len(shared), matched_correct=common_correct,
                              matched_accuracy=common_correct / len(shared) if shared else None)
    disagreements = []
    for gid in sorted(shared):
        choices = {m: by_model[m][gid]["winner"] for m in models}
        if len(set(choices.values())) > 1:
            disagreements.append(dict(game_id=gid, actual=actual[gid], choices=choices))
    return dict(models=metrics, matched_game_ids=sorted(shared), disagreements=disagreements)


def validate_quote(q, game):
    required = ("quote_id", "game_id", "book", "market", "selection",
                "decimal_odds", "observed_at", "source_url")
    if any(not q.get(k) for k in required):
        raise ValueError("Incomplete quote provenance")
    if q["game_id"] != game["game_id"]:
        raise ValueError("Quote game mismatch")
    if q["market"] != "full_game_moneyline":
        raise ValueError("Only full-game moneylines supported in V1")
    if q["selection"] not in {game["home"], game["away"]}:
        raise ValueError("Invalid quote selection")
    if not isinstance(q["decimal_odds"], (int, float)) or not math.isfinite(q["decimal_odds"]) or q["decimal_odds"] <= 1:
        raise ValueError("Invalid decimal odds")
    if instant(q["observed_at"]) >= instant(game["start_time"]):
        raise ValueError("Post-start quote cannot be backtested")
    if q.get("status") != "observed" or q.get("executable") is not True:
        raise ValueError("Quote not marked executable/observed")
    if not q["source_url"].startswith(("https://", "http://")):
        raise ValueError("Missing verifiable source URL")
    return q


def assess_singles(picks, quotes, outcomes, stake=2.0):
    """Descriptive returns for predeclared selections, never optimize in-sample."""
    if stake <= 0:
        raise ValueError("Stake must be positive")
    qmap = defaultdict(list)
    for q in quotes:
        qmap[(q["game_id"], q["selection"])].append(q)
    actual = {x["game_id"]: x["winner"] for x in outcomes}
    if len(actual) != len(outcomes):
        raise ValueError("Duplicate outcomes")
    rows = []
    missing = []
    for p in picks:
        if p["game_id"] not in actual:
            missing.append(dict(game_id=p["game_id"], reason="unsettled"))
            continue
        eligible = []
        for q in qmap[(p["game_id"], p["winner"])]:
            try:
                validate_quote(q, p)
                if instant(q["observed_at"]) < instant(p["frozen_at"]):
                    continue  # A quote before prediction is not automatically available at selection time.
                eligible.append(q)
            except ValueError:
                continue
        if not eligible:
            missing.append(dict(game_id=p["game_id"], reason="no verified post-freeze pregame executable price"))
            continue
        # Earliest post-freeze observed quote; never choose the best hindsight price.
        q = min(eligible, key=lambda x: instant(x["observed_at"]))
        won = p["winner"] == actual[p["game_id"]]
        payout = stake * q["decimal_odds"] if won else 0
        rows.append(dict(game_id=p["game_id"], selection=p["winner"], quote_id=q["quote_id"],
                         book=q["book"], stake=stake, return_amount=round(payout, 4),
                         net=round(payout - stake, 4), won=won))
    total = sum(x["stake"] for x in rows)
    returned = sum(x["return_amount"] for x in rows)
    return dict(eligible=len(rows), missing=missing, wins=sum(x["won"] for x in rows),
                losses=sum(not x["won"] for x in rows), stakes=round(total, 4),
                returns=round(returned, 4), net=round(returned-total, 4),
                roi=(returned-total)/total if total else None, bets=rows)


def grade_tickets(tickets, quotes, outcomes, owner_pending_game_ids=()):
    """Evaluate only explicitly timestamped, precommitted ticket versions."""
    qids = {q["quote_id"]: q for q in quotes}
    actual = {x["game_id"]: x["winner"] for x in outcomes}
    pending = set(owner_pending_game_ids)
    results = []
    seen = set()
    active_dates = set()
    for ticket in tickets:
        key = (ticket["date"], ticket["version"])
        if key in seen:
            raise ValueError("Duplicate ticket version")
        seen.add(key)
        if ticket.get("status") != "active":
            continue
        if ticket["date"] in active_dates:
            raise ValueError("More than one active ticket for date: " + ticket["date"])
        active_dates.add(ticket["date"])
        placed = instant(ticket["published_at"])
        legs = ticket["legs"]
        if len(legs) < 2 or len({x["game_id"] for x in legs}) != len(legs):
            raise ValueError("Ticket must have two distinct games")
        if any(x["game_id"] in pending for x in legs):
            raise ValueError("Ticket duplicates an owner's pending game")
        if ticket["stake"] <= 0:
            raise ValueError("Invalid stake")
        odds = 1.0
        for leg in legs:
            q = qids[leg["quote_id"]]
            game = dict(game_id=leg["game_id"], home=leg["home"], away=leg["away"],
                        start_time=leg["start_time"])
            validate_quote(q, game)
            if instant(q["observed_at"]) > placed or placed >= instant(leg["start_time"]):
                raise ValueError("Quote not available at ticket publication or post-start ticket")
            if q["selection"] != leg["selection"]:
                raise ValueError("Ticket quote/selection mismatch")
            odds *= q["decimal_odds"]
        statuses = [actual.get(leg["game_id"]) == leg["selection"] if leg["game_id"] in actual else None for leg in legs]
        settled = False if None in statuses and all(s is not False for s in statuses) else True
        won = all(s is True for s in statuses)
        payout = ticket["stake"] * odds if won else 0 if settled else None
        results.append(dict(date=ticket["date"], version=ticket["version"],
                            settled=settled, won=won if settled else None,
                            combined_decimal=round(odds, 6),
                            return_amount=round(payout, 4) if payout is not None else None,
                            net=round(payout-ticket["stake"], 4) if payout is not None else None))
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="append", required=True)
    ap.add_argument("--outcomes", required=True)
    ap.add_argument("--quotes")
    ap.add_argument("--tickets")
    ap.add_argument("--owner-pending")
    args = ap.parse_args()
    outcomes = load_json(args.outcomes)
    picks = [p for path in args.freeze for p in freeze_rows(path)]
    result = {"comparison": compare(args.freeze, outcomes)}
    if args.quotes:
        quotes = load_json(args.quotes)
        result["single_price_audit"] = assess_singles(picks, quotes, outcomes)
        if args.tickets:
            result["ticket_audit"] = grade_tickets(load_json(args.tickets), quotes, outcomes,
                load_json(args.owner_pending) if args.owner_pending else ())
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
