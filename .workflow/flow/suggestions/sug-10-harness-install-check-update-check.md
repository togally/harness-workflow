---
id: sug-10
title: "补 harness install --check 命令与 update --check 对齐"
status: pending
created_at: 2026-04-22
priority: low
---

harness install 当前不支持 --check 语义（只有 --root / --force-skill / --agent），导致 CI 自检需绕开。建议对齐 harness update --check 的 check-only 行为。
