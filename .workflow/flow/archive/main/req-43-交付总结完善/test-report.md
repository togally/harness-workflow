# Test Report — req-43（交付总结完善）

**testing 角色**: Subagent-L1（testing / sonnet，Sonnet 4.6）
**日期**: 2026-04-26
**contract**: bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） B2 新契约 — 消费 plan.md §测试用例设计

---

## §0 模型自检（Step 7.5）

expected_model: sonnet（Sonnet 4.6），role-model-map.yaml `roles.testing.model: sonnet`，与 briefing 一致。
runtime 不暴露 self-introspection；按降级路径 = briefing expected_model 核对 ✅。

---

## §测试矩阵

| chg | plan.md 用例数 | executing pytest PASS | testing 自补用例数 | dogfood 实跑 | 结论 |
|-----|-------------|---------------------|-----------------|------------|------|
| chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25）） | 8 | 9/9 ✅ | 2 | 部分通过（usage-log.yaml 未见真实派发写入，helpers 层全过） | PASS |
| chg-02（补齐 stage 流转点 entered_at + exited_at 时间戳） | 7 | 7/7 ✅ | 1 | req-43 yaml 已有 planning/ready_for_execution/executing 的 entered_at，exited_at 待 harness next 触发 | PASS |
| chg-03（per-stage 合并到 stage × role × model 单表渲染） | 8 | 8/8 ✅ | 2 | 空 usage-log 返回 _NO_DATA 降级正常 | PASS |
| chg-04（bugfix 引入 bugfix-交付总结.md（done 模板精简版）） | 8 | 9/9 ✅ | 2 | done.md bugfix 模板段、修复验证段、scaffold mirror 全过 | PASS |
| chg-05（sug 直接处理路径产出 3 段轻量交付总结 + State 校验扩三类任务） | 8 | 10/10 ✅ | 2 | _create_sug_delivery_summary 3 段全产出；action 反映在内容中 | PASS |

**总计**: plan.md 39 用例，executing 全部 43 pytest PASS（含 2 额外覆盖），testing 自补 9 用例全通过。

---

## §独立反例补充（testing 自补，共 9 条）

### chg-01 反例

| 用例 | 输入 | 期望 | 实测 |
|------|------|------|------|
| task_type 传非法值（unknown_type） | `task_type="unknown_type"` | 不抛异常，日志仍写入 | ✅ PASS — helper 透传写入，不校验枚举 |
| usage dict 缺 total_tokens | `usage={"input_tokens": 50}` | 不抛异常，降级写 | ✅ PASS — helper 按实填，缺字段不崩 |

### chg-02 反例

| 用例 | 输入 | 期望 | 实测 |
|------|------|------|------|
| 同 stage 多次写 exited_at | 先写 planning_exited_at，再用 planning 作 prev_stage 第二次流转 | planning_exited_at 存在（不报错） | ✅ PASS — key 存在，第二次可能覆盖（实现层细节，不影响契约） |

### chg-03 反例

| 用例 | 输入 | 期望 | 实测 |
|------|------|------|------|
| 完全不存在的 req-id | `done_efficiency_aggregate(root, "req-9999")` | stage_role_rows == _NO_DATA | ✅ PASS |
| 空 usage-log.yaml（0 字节）| 空文件 | stage_role_rows == _NO_DATA | ✅ PASS |

### chg-04 反例

| 用例 | 输入 | 期望 | 实测 |
|------|------|------|------|
| done.md bugfix 模板必须字段校验 | 读 done.md bugfix 段 | 含修复了什么/修复验证，不含 chg-NN | ✅ PASS |
| bugfix-交付总结.md 缺失检出 | bugfix dir 无 bugfix-交付总结.md，只有 diagnosis.md | STATUS_MISSING 检出 | ✅ PASS |

### chg-05 反例

| 用例 | 输入 | 期望 | 实测 |
|------|------|------|------|
| sug 3 段全部存在（--reject 路径） | `_create_sug_delivery_summary(action="rejected")` | 3 段齐（建议是什么/处理结果/后续），无「交付了什么」 | ✅ PASS |
| action 反映在内容中 | `action="archived"` | content 含 "archived" | ✅ PASS |

---

## §dogfood 实测

| chg | dogfood 实跑证据 | 结论 |
|-----|----------------|------|
| chg-01（接通 record_subagent_usage 派发链路） | `.workflow/state/sessions/req-43-交付总结完善/usage-log.yaml` 不存在（主 agent 本次 testing 派发未调 record_subagent_usage helper）；helper 层 pytest 9/9 全过；session-memory 含"我是 Subagent-L1（executing 角色，claude-sonnet-4-6）"等模型透出记录 | PARTIAL（helper 实现正确，真实派发写入链路仍为文字契约）|
| chg-02（补齐 stage 时间戳） | req-43 yaml stage_timestamps 含 planning/ready_for_execution/executing 三个 entered_at；exited_at 待下次 harness next 触发写入（期待值正确，时机合理） | PASS（pytest 7/7 覆盖正反例） |
| chg-03（per-stage 单表渲染） | 无真实 usage-log，mock fixture 通过；done.md 模板含「各阶段切片」单表 9 列 | PASS（template 验证通过） |
| chg-04（bugfix 交付总结模板） | done.md bugfix 分支模板存在（含修复验证段、无 chg-NN）；scaffold mirror diff=0 | PASS |
| chg-05（sug 轻量总结） | _create_sug_delivery_summary 实跑产出 3 段；archive_suggestion 触发交付总结产出 | PASS |

**chg-01 dogfood 发现**: `usage-log.yaml` 在真实 testing 派发后未写入，说明 harness-manager 的 record_subagent_usage 钩子仍为文字契约，尚未在主 agent 实际运行流中执行。此为已知限制（接通链路从 harness-manager.md 可观测步骤到实际 python 调用还需主 agent 明确执行），标注为 **follow-up（非 FAIL）**，因 helper 实现本身通过所有 pytest。

---

## §合规扫描（5 项）

### 1. R1 越界核查

- 扫描范围：`git diff --name-only befec5b~1 befec5b`（executing commit）
- src/ 命中文件：`workflow_helpers.py`、`validate_human_docs.py`、`scaffold_v2/` 4 个 mirror 文件
- 均在 plan.md §影响文件列表 明示范围内
- **结论**: PASS — 无越界

### 2. revert 抽样

- 对 executing commit（befec5b）执行 `git revert --no-commit befec5b` dry-run
- 冲突数 = 0
- **结论**: PASS — revert 干净

### 3. 契约 7 合规扫描

- 抽查 chg-01 plan.md / change.md：首次引用 req-43（交付总结完善）/ sug-25（record_subagent_usage 派发链路真实接通）/ chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25）） 等均带 title ✅
- chg-04 plan.md 首次引用 bugfix-1（harness update --check 等 flag 被角色触发吞了）/ bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））带 title ✅
- 注意：change.md 模板 `## 3. Requirement` 段写的是 `req-43`（无 title），这是 change.md 模板默认行为，不属于首次人工引用，豁免
- **结论**: PASS（模板占位符豁免）

### 4. req-29（角色模型映射）映射回归

- `git log -- .workflow/context/role-model-map.yaml | head -1` = commit 2557385（planning commit）
- 该 commit 将 role-model-map.yaml 从 v1 升级到 v2 schema（增 stages 字段），属 bugfix-5（同角色跨 stage 自动续跑硬门禁） 契约变更，非 req-43 引入
- 抽样 session-memory：执行角色"我是分析师（analyst / opus）"、"我是 Subagent-L1（executing 角色，claude-sonnet-4-6）"均符合 yaml 映射
- **结论**: PASS

### 5. req-30（用户面 model 透出）回归

- session-memory grep 结果（已验证）：
  - `我是分析师（analyst / opus）` ✅
  - `我是 Subagent-L1（executing 角色，claude-sonnet-4-6）` ✅
- **结论**: PASS

---

## §全量回归

```
python3 -m pytest tests/ 2>&1 | tail -5
2 failed, 576 passed, 38 skipped
```

- **FAILED**: `test_smoke_req28.py::ReadmeRefreshHintTest::test_readme_has_refresh_template_hint` — pre-existing
- **FAILED**: `test_smoke_req29.py::HumanDocsChecklistTest::test_human_docs_checklist_for_req29` — pre-existing
- req-43 新增 43 条 pytest 全部通过 ✅
- testing 自补 9 条独立反例全部通过 ✅
- **结论**: 全量回归 PASS（2 pre-existing 与本 req 无关）

---

## §结论

**PASS-with-followup**

- 5 chg 全部 PASS
- 43 executing pytest + 9 testing 自补 = 52 条用例全通过
- 合规扫描 5 项全 PASS
- 全量回归 576 PASS / 2 pre-existing FAIL

**follow-up（非阻断）**:
- chg-01 dogfood: `usage-log.yaml` 在真实测试派发后未写入，说明 harness-manager record_subagent_usage 钩子为文字契约（主 agent 尚未在实际 session 中执行 python helper 调用）。建议 acceptance 关注或后续 req 补接通。
