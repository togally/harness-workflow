#!/usr/bin/env python3
"""Detect circular dependencies in subagent call chains.

本文件历史上同时承担两种职责：

1. CLI 入口（``main()``，被 ``python -m`` 或 harness 命令调用），基于文件
   级 JSON 调用链持久化。
2. in-process API（``CallChainNode`` / ``CycleDetector`` 等），供其它 Python
   代码在派发 subagent 前做快速判断。

req-28 / chg-04 恢复时把对象模型统一迁到
``harness_workflow.cycle_detection``，本文件保留 CLI，并**再出口**一次这些
符号以兼容旧 import 路径 ``from harness_workflow.tools.harness_cycle_detector
import CallChainNode``。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from harness_workflow.cycle_detection import (  # noqa: F401  (re-export)
    CallChainNode,
    CycleDetectionResult,
    CycleDetector,
    detect_subagent_cycle,
    get_cycle_detector,
    report_cycle_detection,
    reset_cycle_detector,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect subagent call cycles.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--add", metavar="AGENT_ID", help="Add agent to chain and check for cycles.")
    parser.add_argument("--role", default="", help="Role of the agent being added.")
    parser.add_argument("--task", default="", help="Task description for the agent.")
    parser.add_argument("--session-path", default="", help="Path to agent session memory.")
    parser.add_argument("--parent-id", default="", help="Parent agent ID.")
    parser.add_argument("--clear", action="store_true", help="Clear the call chain.")
    parser.add_argument("--snapshot", action="store_true", help="Get current chain snapshot.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    chain_file = root / ".workflow" / "state" / "cycle-chain.json"

    if args.clear:
        if chain_file.exists():
            chain_file.unlink()
        print("Call chain cleared.")
        return 0

    chain: list[dict] = []
    if chain_file.exists():
        try:
            chain = json.loads(chain_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            chain = []

    if args.snapshot:
        print(json.dumps(chain, indent=2))
        return 0

    if args.add:
        agent_id = args.add
        chain_ids = [node.get("agent_id") for node in chain]

        if agent_id in chain_ids:
            cycle_start_idx = chain_ids.index(agent_id)
            full_cycle_path = chain_ids[cycle_start_idx:] + [agent_id]
            cycle_path_str = " -> ".join(full_cycle_path)

            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            report_lines = [
                f"## [{timestamp}] Cycle Detection Alert",
                "",
                "- **Type**: Subagent Call Cycle Detected",
                f"- **Cycle Path**: {cycle_path_str}",
                f"- **Message**: Cycle detected: {cycle_path_str}. Agent '{agent_id}' (role: {args.role}) is already in the call chain. Task: {args.task}",
                "- **Action**: Terminated - cannot spawn already-in-chain agent",
                "",
            ]
            report_content = "\n".join(report_lines)

            action_log_path = root / ".workflow" / "state" / "action-log.md"
            if action_log_path.exists():
                with open(action_log_path, "a", encoding="utf-8") as f:
                    f.write("\n" + report_content)
            else:
                action_log_path.write_text(report_content, encoding="utf-8")

            cycle_log_dir = root / ".workflow" / "state" / "cycle-logs"
            cycle_log_dir.mkdir(parents=True, exist_ok=True)
            cycle_log_file = cycle_log_dir / f"cycle-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.md"
            cycle_log_file.write_text(report_content, encoding="utf-8")

            print(f"CYCLE DETECTED: {' -> '.join(full_cycle_path)} -> {agent_id}")
            return 1

        new_node = {
            "agent_id": agent_id,
            "role": args.role,
            "task": args.task,
            "session_memory_path": args.session_path,
            "parent_agent_id": args.parent_id or None,
        }
        chain.append(new_node)
        chain_file.parent.mkdir(parents=True, exist_ok=True)
        chain_file.write_text(json.dumps(chain, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Agent {agent_id} added to call chain.")
        return 0

    print("No action specified. Use --add, --clear, or --snapshot.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())