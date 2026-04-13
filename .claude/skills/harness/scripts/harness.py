#!/usr/bin/env python3
"""Thin fallback wrapper for the installed Harness skill."""

from __future__ import annotations

from harness_workflow.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
