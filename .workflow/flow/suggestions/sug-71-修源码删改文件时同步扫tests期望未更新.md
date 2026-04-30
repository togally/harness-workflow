---
id: sug-71
title: "修源码 + 删/改文件时同步扫 tests/ 是否有相关期望需更新"
status: pending
created_at: 2026-04-30
priority: medium
---

bugfix-13 round-4 修复时删除 `assets/templates/project-skeleton/experience/{roles,tool,risk,regression,stage}/.gitkeep` 后未同步更新 `tests/test_bugfix_13_project_skeleton_bootstrap.py` 中相关 .gitkeep 期望断言，导致 round-4 testing 虚报 "52 failed=baseline" 实测 +1 fail（README line 21 + 模板 README line 21 各 1 行偏差），主 agent 独立核查后 round-2 微调修回 51。建议 executing 角色 SOP 增加显式步骤：「修改 / 新增 / 删除源码 + 资产文件时，必须同步 grep 文件名 + 关键 bytes 在 tests/ 目录的命中点，确认测试期望与实际一致」；可作为 contract `test-expectation-sync` 由 `harness validate` 自动扫描"删了文件但测试期望仍引用"模式。来源：req-53 done 阶段六层回顾 Constraints 层。
