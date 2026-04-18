#!/usr/bin/env python3
"""Append an action entry to action-log.md."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Log an action to action-log.md.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--operation", required=True, help="Operation name.")
    parser.add_argument("--description", required=True, help="Operation description.")
    parser.add_argument("--result", required=True, help="Operation result.")
    parser.add_argument("--tool-id", default="", help="Tool ID used.")
    parser.add_argument("--rating", type=int, help="Tool rating (1-5).")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    harness_root = root / ".workflow"
    if not harness_root.exists():
        print("Harness workspace not found. Run `harness install` first.")
        return 1

    log_file = root / ".workflow" / "state" / "action-log.md"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"## {timestamp}",
        "",
        f"- **操作**: {args.operation}",
        f"- **说明**: {args.description}",
        f"- **结果**: {args.result}",
        f"- **使用工具**: {args.tool_id if args.tool_id else '无'}",
    ]
    if args.rating is not None:
        lines.append(f"- **评分**: {args.rating}")
    else:
        lines.append("- **评分**: N/A")
    lines.append("")

    with log_file.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())