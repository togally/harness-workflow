---
id: bugfix-11
title: "install runtime.yaml 反写 3 bug：gstack_status 丢失 + 多重 quote + active_requirements 清空"
created_at: 2026-05-08
operation_type: bugfix
stage: testing
---

## 测试对象

- bugfix-11：install runtime.yaml 反写 3 bug 修复（方案 B 统一 writer）

## 执行方式

轻量版（与 req-55 chg-04 恢复同模式）：主 agent 自跑端到端实测 + pytest 全套，不派发 testing subagent。

## 执行结果

### 端到端实测：`harness install --agent claude` 真跑

| 检查项 | 结果 | 备注 |
|---|---|---|
| 编译 / 运行无报错 | ✅ PASS | pipx install --force 成功，install --agent claude 正常输出 |
| [gstack] Pushed 46 skills 输出 | ✅ PASS | vendor 推送真活（chg-01 端到端验证通过） |
| **B1：runtime.yaml 字段值多重 quote** | ✅ PASS | `locked_requirement: ""`（标准 yaml escape，无 `''''''` 累积） |
| **B2：gstack_status 字段写入** | ✅ PASS | 4 子字段完整：installed_skills（46 项列表）+ vendor_version=c7aefc1 + last_install=2026-05-08T08:58 + agent_kind_compatible=true |
| **B3：active_requirements 保留** | ✅ PASS | `[bugfix-11]` 不被清空 |
| _parse_simple_yaml_scalar self-heal | ✅ PASS | 历史污染 runtime 被自动剥层（用户拍板第 4 条） |

### pytest 全套

| 套件 | 用例数 | 通过 | 备注 |
|---|---|---|---|
| tests/installer/test_install_runtime_writer.py（新增） | 10 | 10 | P0×6 + P1×4 全 PASS |
| tests/installer/test_gstack_skills_push.py（既有 chg-01） | 8 | 8 | 0 回归 |
| tests/integration/test_install_pushes_gstack.py（既有 chg-01） | 7 | 7 | 0 回归 |
| **合计** | **25** | **25** | **0 回归** |

> regression 报告 31 passed 含 6 条 fixture / collection 项；实质功能用例 25/25。

## 发现问题

- 无（3 bug 全部端到端验证通过）

## 已知非本 bugfix 问题（pre-existing 噪声，不计本次责任）

- contract role-stage-continuity FAIL（来自 bugfix-5 历史 session-memory 文本，与本 bugfix 无关）
- test_dev_mirror_no_runtime_artifacts 1 条 pre-existing fail（mirror 下 trivial-spec.md / trivial-交付总结.md 运行时污染）
- /usr/local/bin/harness 残留（PEP 668 阻止 pip uninstall；PATH 优先级仍正确不影响功能）

## 结论

- [x] **通过 — 可进入验收**
- [ ] 未通过 — 需继续修复

**总体判定：PASS**

3 bug 端到端实测验证 + 25/25 测试通过 + 0 回归。chg-01（gstack 内置发布契约）的 acceptance 真活证此次兑现（先于 chg-05 候选 P deferred）。
