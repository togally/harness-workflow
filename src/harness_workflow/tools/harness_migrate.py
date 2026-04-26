#!/usr/bin/env python3
"""Migrate legacy harness-workflow directories to ``artifacts/{branch}/...``.

Supported resources:

- ``requirements``：把 ``.workflow/flow/requirements/`` 与 ``artifacts/requirements/``
  下的 requirement 目录搬到 ``artifacts/{branch}/requirements/``。
- ``archive``（req-29 / chg-02, AC-04）：把 ``.workflow/flow/archive/`` 下带分支前缀
  或裸形态的 ``{requirements,bugfixes}/<dir>`` 统一搬到
  ``artifacts/{branch}/archive/{requirements,bugfixes}/``。
- ``bugfix-layout``（bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） / A5）：
  把 bugfix-1~5 机器型文档从 ``artifacts/{branch}/bugfixes/`` 迁移到
  ``.workflow/flow/bugfixes/``，artifacts/ 旧目录保留 README.md 占位。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import migrate_archive, migrate_bugfix_layout, migrate_requirements


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Migrate legacy harness-workflow directories. "
            "Supports 'requirements', 'archive', and 'bugfix-layout'."
        )
    )
    parser.add_argument(
        "resource",
        choices=["requirements", "archive", "bugfix-layout"],
        help=(
            "Migration target resource: "
            "'requirements' for legacy requirement directories; "
            "'archive' for legacy .workflow/flow/archive/ entries; "
            "'bugfix-layout' for bugfix-1~5 machine-type docs (bugfix-6 A5)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the migration plan without moving any directory (rc=0).",
    )
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.resource == "requirements":
        return migrate_requirements(root, dry_run=args.dry_run)
    if args.resource == "archive":
        return migrate_archive(root, dry_run=args.dry_run)
    if args.resource == "bugfix-layout":
        return migrate_bugfix_layout(root, dry_run=args.dry_run)
    raise SystemExit(f"Unsupported migrate resource: {args.resource}")


if __name__ == "__main__":
    raise SystemExit(main())
