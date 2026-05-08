---
id: bugfix-11
title: "install runtime.yaml 反写 3 bug：gstack_status 丢失 + 多重 quote + active_requirements 清空"
created_at: 2026-05-08
operation_type: bugfix
stage: regression
---

## 1. Current Goal

- 诊断 bugfix-11（install runtime.yaml 反写 3 bug：gstack_status 丢失 + 多重 quote + active_requirements 清空），独立核实 B1/B2/B3 现场 + 锁定 root cause + 给修复方案与路由决策。

## 2. Context Chain

- Level 0: 用户 → harness install --agent claude → 发现 B1/B2/B3 → harness bugfix
- Level 0.5: 主 agent / harness-manager
- Level 1（本 subagent）: regression（regression / Opus 4.7）

## 3. Completed Tasks

- [x] 加载 runtime.yaml + base-role.md + stage-role.md + regression.md + evaluation/regression.md + role-loading-protocol.md
- [x] 项目级加载链 Step 7.6 / 7.6.1 自检（artifacts/project/constraints/coding/测试-rule.md 1 命中；其他 5 个索引为占位）
- [x] 模型一致性自检：本 subagent 运行于 opus，与 role-model-map.yaml `roles[regression]=opus` 声明一致
- [x] 独立核实 3 个 bug 现场（cat runtime.yaml + git diff + 写最小复现脚本 /tmp/test_yaml_roundtrip.py）
- [x] 定位 B1 root cause（pyyaml 单引号 + simple_yaml 不剥 + json.dumps 双引号包裹累积）
- [x] 定位 B2 root cause（`save_requirement_runtime.ordered_keys` 白名单缺 gstack_status / gstack_run_log）
- [x] 定位 B3 root cause（`load_simple_yaml` 不兼容 pyyaml block-seq 0 缩进形态）
- [x] 评估方案 A/B/C，选定 default-pick = B（统一 runtime.yaml writer 走 `save_requirement_runtime`）
- [x] 写 diagnosis.md（含现场摘要 + 根因 + 影响评估 + 修复方案 + 测试用例设计 §4.5 + 结论）
- [x] 写本 session-memory.md

## 4. Results

### 关键根因摘要

3 bug 同源——**`runtime.yaml` 写盘路径分裂成 2 个不兼容 writer**（pyyaml `yaml.dump` 与自家 `save_simple_yaml`），同一文件被两个 writer 交替反写时 round-trip 不闭合：

- `workflow_helpers.py:8369` _write_gstack_status 用 yaml.dump
- `workflow_helpers.py:3427` _sync_requirement_workflow_managed_files 用 save_simple_yaml
- `workflow_helpers.py:307` _parse_simple_yaml_scalar 只剥双引号
- `workflow_helpers.py:347` load_simple_yaml 用 indent > collection_indent 判 list item
- `workflow_helpers.py:668-685` save_requirement_runtime.ordered_keys 缺 gstack_status / gstack_run_log

### 路由决策

- **confirm**：真实问题（已复现）
- **目标阶段**：executing（实现/写盘契约问题）
- **修复方案**：B（default-pick；统一 runtime.yaml writer 单一来源）

### 产出文件

- `.workflow/flow/bugfixes/bugfix-11-.../regression/diagnosis.md`（本次填充）
- `.workflow/flow/bugfixes/bugfix-11-.../session-memory.md`（本文件）

## 5. Default-Pick 决策清单（同阶段不打断硬门禁四 + S-E 决策批量化）

| 决策点 | options | default-pick | 一句话理由 |
|-------|---------|--------------|----------|
| 修复方案选择 | A 最小修复分 3 fix / B 统一 writer / C 加 contract lint | **B** | 3 bug 同源、统一一个写盘点根治、改动最小、回归面最窄 |
| 是否扩到 contract lint | 是 / 否 | **否** | C 范围本 bugfix 不含；可作 sug 跟进 |
| 是否 retroactive 重 archive req-55 | 是 / 否 | **是** | chg-01 acceptance 实际未过；建议 fix 落地 + chg-01 重 acceptance 后滚回 archive 修订 |
| _parse_simple_yaml_scalar 是否同步加单引号 self-heal | 是 / 否 | **是** | 历史已污染的 runtime.yaml 自愈，避免人工剥层 |

## 6. Failed Paths

- 暂无（B1 复现一次到位；机理推演经脚本反证）。

## 7. Next Steps / Open Questions

- executing 阶段按 diagnosis.md "executing 阶段动作清单"（6 步）实施；
- testing 阶段实施 TC-01 ~ TC-10；
- 是否在本 bugfix 一并 self-heal 当前仓库被污染的 runtime.yaml（建议：是，作为 executing 第 5 步）。

## 8. 待处理捕获问题

- 无（职责外问题）。

## 9. Usage 采集留痕

- 本 subagent 由 harness-manager 派发，task_type=bugfix，bugfix-id=bugfix-11，role=regression；
- 主 agent 在收到本 subagent 返回后须调 `record_subagent_usage` 写入 `.workflow/state/sessions/bugfix-11/usage-log.yaml`；本 subagent 已完成自检留痕。

---

## executing 阶段（2026-05-08）✅

### 角色

executing（Sonnet 4.6）

### 步骤状态

| Step | 描述 | 状态 |
|------|------|------|
| Step 1 | 修 `_parse_simple_yaml_scalar`（行 307，B1 self-heal）加成对单引号剥层 | ✅ |
| Step 2 | 修 `load_simple_yaml`（B3 root）改 `indent >= collection_indent` + 嵌套 dict 内 list 解析 | ✅ |
| Step 3 | 修 `save_requirement_runtime.ordered_keys`（B2 root）追加 `gstack_status` / `gstack_run_log` | ✅ |
| Step 4 | 修 `_write_gstack_status`（行 8350，方案 B 核心）改走 `save_requirement_runtime` 单一写盘 | ✅ |
| Step 5 | 手工清理 `.workflow/state/runtime.yaml` 多重单引号污染（6 字段还原为空字符串） | ✅ |
| Step 6 | 写测试 `tests/installer/test_install_runtime_writer.py`（10 条：TC-01~TC-10） | ✅ |
| Step 7 | 跑测试：16 passed 0 failed + 已有 15 测试 0 回归 | ✅ |
| grep guard | `yaml\.(dump\|safe_dump)\s*\(.+runtime` 返回 0 命中 | ✅ |

### 额外修复（测试驱动发现）

- `load_simple_yaml` 嵌套 dict 内 list 解析：当 `current_sub_key` 存在且父值为 dict 时，`- item` 行追加到 `dict[sub_key]` 而非父 dict。修复 `gstack_status.installed_skills` 加载失真问题（TC-07 发现）。

### 产出文件

- `src/harness_workflow/workflow_helpers.py`（5 处修改：B1 self-heal + B3 load + B3 嵌套 list + B2 ordered_keys + 方案 B _write_gstack_status 统一 writer）
- `tests/installer/test_install_runtime_writer.py`（新增，10 条测试用例）
- `.workflow/state/runtime.yaml`（污染字段清理）
- `.workflow/flow/bugfixes/bugfix-11-.../session-memory.md`（本文件追加）
