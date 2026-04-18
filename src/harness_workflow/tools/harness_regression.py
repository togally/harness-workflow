#!/usr/bin/env python3
"""Start or advance a regression confirmation flow."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import create_regression, regression_action


def main() -> int:
    parser = argparse.ArgumentParser(description="Start or advance a regression confirmation flow.")
    parser.add_argument("title", nargs="?", help="Start a regression with this title.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--status", action="store_true", help="Show the current regression state.")
    parser.add_argument("--confirm", action="store_true", help="Confirm that the current regression is a real problem.")
    parser.add_argument("--reject", action="store_true", help="Mark the current regression as not a real problem.")
    parser.add_argument("--cancel", action="store_true", help="Cancel the current regression flow.")
    parser.add_argument("--change", dest="change_title", default="", help="Convert the confirmed regression into a new change.")
    parser.add_argument("--requirement", dest="requirement_title", default="", help="Convert the confirmed regression into a new requirement update.")
    parser.add_argument("--testing", action="store_true", help="Roll back to testing stage and log the confirmed regression as a bug in testing/bugs/.")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    if args.title and not any([args.status, args.confirm, args.reject, args.cancel, args.change_title, args.requirement_title, args.testing]):
        return create_regression(root, args.title)

    return regression_action(
        root,
        status_only=args.status,
        confirm=args.confirm,
        reject=args.reject,
        cancel=args.cancel,
        change_title=args.change_title,
        requirement_title=args.requirement_title,
        to_testing=args.testing,
    )


if __name__ == "__main__":
    raise SystemExit(main())
