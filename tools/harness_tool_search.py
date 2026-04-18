#!/usr/bin/env python3
"""Search local tool index by keywords."""

from __future__ import annotations

import argparse
from pathlib import Path
import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description="Search local tool index by keywords.")
    parser.add_argument("keywords", nargs="+", help="Keywords to search for.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    keywords_file = root / ".workflow" / "tools" / "index" / "keywords.yaml"

    if not keywords_file.exists():
        print("No keywords file found.")
        return 1

    data = yaml.safe_load(keywords_file.read_text(encoding="utf-8")) or {}
    tools = data.get("tools", [])
    if not isinstance(tools, list):
        print("Invalid keywords file format.")
        return 1

    ratings_file = root / ".workflow" / "tools" / "ratings.yaml"
    ratings: dict[str, dict[str, object]] = {}
    if ratings_file.exists():
        ratings_data = yaml.safe_load(ratings_file.read_text(encoding="utf-8")) or {}
        ratings = ratings_data.get("ratings", {})
        if not isinstance(ratings, dict):
            ratings = {}

    query_set = {k.lower() for k in args.keywords}
    candidates: list[tuple[str, int, float]] = []

    for tool in tools:
        if not isinstance(tool, dict):
            continue
        tool_id = str(tool.get("tool_id", ""))
        if not tool_id:
            continue
        tool_keywords = tool.get("keywords", [])
        if not isinstance(tool_keywords, list):
            continue
        tool_set = {str(tk).lower() for tk in tool_keywords}
        overlap = len(query_set & tool_set)
        if overlap == 0:
            continue
        score = float(ratings.get(tool_id, {}).get("score", 0.0)) if isinstance(ratings.get(tool_id), dict) else 0.0
        candidates.append((tool_id, overlap, score))

    if not candidates:
        print("No matching tool found.")
        return 0

    import random
    random.shuffle(candidates)
    candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)

    best_id = candidates[0][0]
    best_tool = next((t for t in tools if isinstance(t, dict) and t.get("tool_id") == best_id), None)
    if not best_tool:
        print("No matching tool found.")
        return 0

    print(f"Matched: {best_id}")
    print(f"Catalog: {best_tool.get('catalog', '')}")
    print(f"Description: {best_tool.get('description', '')}")
    print(f"Score: {candidates[0][2]}")
    print(f"Overlap: {candidates[0][1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())