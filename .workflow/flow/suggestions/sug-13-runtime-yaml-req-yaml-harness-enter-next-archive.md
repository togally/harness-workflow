---
id: sug-13
title: "runtime.yaml 与 req-*.yaml 同步时机不一致（harness enter / next / archive 窗口）"
status: pending
created_at: 2026-04-22
priority: medium
---

本轮 req-29 acceptance 后观察到 runtime.yaml 的 current_requirement 被清空（从 req-29 变成空串）但 req-29.yaml 仍 stage=acceptance status=active。疑似某次 harness 调用修改 runtime 但未同步 req yaml。最终由主 agent 手工 edit runtime.yaml + req-29.yaml 对齐才能 archive。建议加原子写入或一致性自检。
