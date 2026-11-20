"""Append-only quote receipt intake, separate from prediction and betting ledgers.

Usage:
 python -m evaluation.archive_quote --input receipt.json --archive-dir local-odds
No scraping, network calls, model edits or existing-file replacements.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from .independent import instant


def archive(receipt, directory):
    required = ("quote_id", "game_id", "book", "market", "selection",
                "decimal_odds", "observed_at", "source_url", "start_time",
                "home", "away", "status", "executable")
    if any(key not in receipt for key in required):
        raise ValueError("Missing required receipt field")
    if receipt["market"] != "full_game_moneyline":
        raise ValueError("V1 supports only full-game moneyline")
    if receipt["selection"] not in {receipt["home"], receipt["away"]}:
        raise ValueError("Selection is not a game participant")
    if receipt["status"] != "observed" or receipt["executable"] is not True:
        raise ValueError("Only verifiably observed executable quotes accepted")
    if not isinstance(receipt["decimal_odds"], (int, float)) or not math.isfinite(receipt["decimal_odds"]) or receipt["decimal_odds"] <= 1:
        raise ValueError("Invalid odds")
    if instant(receipt["observed_at"]) >= instant(receipt["start_time"]):
        raise ValueError("Cannot archive quote observed after game start as pregame")
    if not isinstance(receipt["source_url"], str) or not receipt["source_url"].startswith(("https://", "http://")):
        raise ValueError("Source URL required")
    payload = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    target_dir = Path(directory)
    target_dir.mkdir(parents=True, exist_ok=True)
    # Filename is content-addressed, never based on user-supplied paths.
    target = target_dir / (digest + ".json")
    with target.open("x", encoding="utf-8") as file:
        file.write(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return str(target)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--archive-dir", required=True)
    args = parser.parse_args()
    receipt = json.loads(Path(args.input).read_text(encoding="utf-8"))
    print(archive(receipt, args.archive_dir))


if __name__ == "__main__":
    main()
