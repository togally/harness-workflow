#!/usr/bin/env python3
"""Export feedback event summary from .workflow/state/feedback/feedback.jsonl."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export feedback event summary.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--reset", action="store_true", help="Clear the feedback log after export.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    # bugfix-3（新）问题 2：feedback.jsonl 落层归位到 .workflow/state/feedback/
    log_path = root / ".workflow" / "state" / "feedback" / "feedback.jsonl"

    events: list[dict[str, object]] = []
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    stage_skips: dict[str, int] = {}
    stage_durations: dict[str, list[float]] = {}
    regressions_created = 0
    mcp_adoptions: dict[str, object] = {}

    for ev in events:
        kind = ev.get("event", "")
        data = ev.get("data", {}) or {}
        if kind == "stage_skip":
            from_stage = str(data.get("from_stage", "unknown"))
            stage_skips[from_stage] = stage_skips.get(from_stage, 0) + 1
        elif kind == "stage_duration":
            stage_name = str(data.get("stage", "unknown"))
            duration = data.get("duration_seconds", 0)
            stage_durations.setdefault(stage_name, []).append(float(duration))
        elif kind == "regression_created":
            regressions_created += 1
        elif kind == "mcp_adoption":
            pass  # placeholder

    stage_durations_avg: dict[str, int] = {}
    for stage_name, durations in stage_durations.items():
        if durations:
            stage_durations_avg[stage_name] = int(sum(durations) / len(durations))

    timestamps = [str(ev.get("ts", "")) for ev in events if ev.get("ts")]
    period_from = min(timestamps) if timestamps else ""
    period_to = max(timestamps) if timestamps else ""

    project_hash = hashlib.sha256(str(root.resolve()).encode()).hexdigest()

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_hash": project_hash,
        "period": {"from": period_from, "to": period_to},
        "summary": {
            "stage_skips": stage_skips,
            "stage_durations_avg_seconds": stage_durations_avg,
            "regressions_created": regressions_created,
            "mcp_adoptions": mcp_adoptions,
        },
        "events_total": len(events),
    }

    out_path = root / "harness-feedback.json"
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Feedback exported to {out_path}")

    if args.reset and log_path.exists():
        log_path.write_text("", encoding="utf-8")
        print("Feedback log cleared.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())