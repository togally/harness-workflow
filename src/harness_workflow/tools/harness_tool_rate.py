#!/usr/bin/env python3
"""Rate a tool and update cumulative average."""

from __future__ import annotations

import argparse
from pathlib import Path
import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description="Rate a tool.")
    parser.add_argument("tool_id", help="Tool ID to rate.")
    parser.add_argument("rating", type=int, help="Rating from 1 to 5.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()

    if not 1 <= args.rating <= 5:
        print("Rating must be between 1 and 5.")
        return 1

    root = Path(args.root).resolve()
    harness_root = root / ".workflow"
    if not harness_root.exists():
        print("Harness workspace not found. Run `harness install` first.")
        return 1

    ratings_file = root / ".workflow" / "tools" / "ratings.yaml"
    ratings_data = yaml.safe_load(ratings_file.read_text(encoding="utf-8")) if ratings_file.exists() else {}
    ratings = ratings_data.get("ratings", {})
    if not isinstance(ratings, dict):
        ratings = {}

    current = ratings.get(args.tool_id, {})
    if not isinstance(current, dict):
        current = {}
    old_score = float(current.get("score", 0.0))
    count = int(current.get("count", 0))

    new_count = count + 1
    new_score = (old_score * count + args.rating) / new_count if new_count > 0 else float(args.rating)

    ratings[args.tool_id] = {"score": round(new_score, 2), "count": new_count}
    ratings_data["ratings"] = ratings

    ratings_file.parent.mkdir(parents=True, exist_ok=True)
    ratings_file.write_text(yaml.dump(ratings_data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    print(f"Rated {args.tool_id}: {new_score} (from {count} ratings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())