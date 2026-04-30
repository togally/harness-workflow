---
id: bugfix-12
title: "runtime-block.yaml-误判用户野文件-白名单漏配"
created_at: 2026-04-30
operation_type: bugfix
stage: testing
---

## 测试对象

- bugfix-12：runtime-block.yaml-误判用户野文件-白名单漏配

## 执行结果

| 检查项 | 结果 | 备注 |
|--------|------|------|
| 编译 / 运行无报错 | pass | Lint-2: 4 passed, Lint-3: 无新增 fail |
| 核心功能符合预期 | pass | Lint-4 dogfood: rc=0 PASS（非 dev_repo + runtime-block.yaml → 不误报） |
| 边界场景已覆盖 | pass | TC-02（豁免精准，真野文件仍报）+ TC-04（dev_repo 行为不变） |

## Round-1 实跑数据

| Lint | 命令 | 期望 | 实测 | 通过 |
|------|------|------|------|------|
| Lint-1 | `grep -n "state/runtime-block.yaml" workflow_helpers.py` | 1 行命中，行号 ∈ [172,201] | 行 179 命中 ✅ | ✅ |
| Lint-2 | `pytest tests/test_bugfix_12_runtime_block_whitelist.py -v` | 4 passed | 4 passed in 0.18s | ✅ |
| Lint-3 | `pytest tests/ --tb=no -q \| tail -5` | ≤51 failed / ≥733 passed | 51 failed, 733 passed, 40 skipped | ✅ |
| Lint-4 | dogfood Python snippet | rc=0 + PASS | check rc=0 (期望 0) / PASS | ✅ |

## 发现问题

- 无

## 结论

- [x] 通过 — 可进入验收
- [ ] 未通过 — 需继续修复
