# Change Plan — chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））

> 所属 req：req-43（交付总结完善）；本 chg 吸收 sug-25（record_subagent_usage 派发链路真实接通），是 req-43 后续 4 chg 的数据底座。

## §目标

把 chg-08（硬门禁六扩 TaskList + 进度条 + stdout + 提交信息）已立的「Agent 工具返回必调 `record_subagent_usage`」**纯文字硬门禁**真接通到主 agent / harness-manager 的运行时派发钩子，让 `usage-log.yaml` 真有 entries 写入；同时给 helper 加 `task_type` 参数（OQ-5 default-pick），为后续 chg-04（bugfix 引入 bugfix-交付总结.md（done 模板精简版））/ chg-05（sug 直接处理路径产出 3 段轻量交付总结 + State 校验扩三类任务） 三类任务数据通路打底；本 chg 自身周期 dogfood 自证 entries 数 ≥ 派发次数 - 容差。

## §影响文件列表

- `src/harness_workflow/workflow_helpers.py::record_subagent_usage`（line 2714-2787）：函数签名加 `task_type: str = "req"`（kw-only），entry_lines 写入 `task_type` 字段；`record_feedback_event` payload 同步加 `task_type`；`req_id` 字段语义扩展为「任务级 id」（可为 `req-XX` / `bugfix-XX` / `sug-XX`），目录路径仍按 `.workflow/state/sessions/{任务 id}/usage-log.yaml`（与既有归档逻辑兼容，不改 sessions_dir 结构）。
- `.workflow/context/roles/harness-manager.md` §3.6 Step 4（line 371-400）：把"必调"硬门禁从纯文字契约升级为**可观测执行步骤**——每次派发后主 agent 须在 session-memory.md 追加 1 行 `record_subagent_usage called: {role} / {model} / ts={iso}`；增补 task_type 默认推断规则（active req → "req"；active bugfix → "bugfix"；suggestion --apply 路径 → "sug"）。
- `.workflow/context/roles/base-role.md` `## done 六层回顾 State 层自检`（line ~210-220）：保持文字契约不变，**仅注释**说明 chg-05 后续将扩三类任务（本 chg 不动语义）。
- `tests/test_record_subagent_usage.py`（**新增**）：覆盖 `task_type` 默认 / "req" / "bugfix" / "sug" / 缺省自动推断 五条 case + entries 写入 schema 校验 + feedback.jsonl 同步校验。
- `.workflow/flow/suggestions/sug-25-record-subagent-usage.md`：frontmatter `status: pending → applied`（最后一步走 `harness suggest --archive sug-25` 落地）。
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` + `base-role.md`：scaffold mirror 同步（硬门禁五）。

## §实施步骤

1. 改 `record_subagent_usage` helper：加 `task_type: str = "req"` kw-only 参数；entry 文本块新增 `  task_type: {task_type}`（紧跟 ts 之后，stage 之前）；`record_feedback_event` payload dict 加 `"task_type": task_type` 键。保持向后兼容（既有调用方不传 task_type 默认 "req"，与历史 entries 语义一致）。
2. 写最小单测 `tests/test_record_subagent_usage.py`（≥ 5 条 case）：默认 task_type 写入 / 显式传 "req" / 显式传 "bugfix" / 显式传 "sug" / req_id 为空时 noop（不写文件）。每条 case 校验 usage-log.yaml 内含 task_type 行 + feedback.jsonl 同步含 task_type 字段。
3. 改 `harness-manager.md` §3.6 Step 4：把"必调"段升级——每次派发后追加可观测留痕步骤（在主 agent 自身 session-memory.md 写一行 `record_subagent_usage called: {role} / {model} / task_type={t} / ts={iso}`）；新增 task_type 推断规则段（active req → "req"；active bugfix → "bugfix"；sug --apply 不转 req 路径 → "sug"）。
4. 端到端 dogfood：本 chg 自身 executing / testing / acceptance / done 派发后即时 grep `^- ts:` 在 `.workflow/state/sessions/req-43-交付总结完善/usage-log.yaml` 的 entries 数与主 agent session-memory 留痕的 `record_subagent_usage called:` 行数相等（误差 ≤ 容差，容差 = 失败派发次数 + 降级 stub 次数）。
5. scaffold_v2 mirror 同步：`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` 与本仓库 `.workflow/context/roles/harness-manager.md` diff = 0；`base-role.md` 同理（按硬门禁五）。
6. 收口：`harness suggest --archive sug-25`（翻 `status: applied`）+ `harness validate --human-docs` exit 0 + `pytest tests/` 全绿（基线 + 5 条新 case）。

## §测试用例设计

> regression_scope: targeted（本 chg 仅动 helper + harness-manager.md 文字契约 + scaffold mirror，未触动主流程 CLI 入口）
> 波及接口清单（git diff --name-only 预估 + 人工补全）：
> - `src/harness_workflow/workflow_helpers.py::record_subagent_usage`
> - `.workflow/context/roles/harness-manager.md` §3.6 Step 4
> - `.workflow/flow/suggestions/sug-25-record-subagent-usage.md`
> - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` + `base-role.md`

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 task_type 默认值 | 调 `record_subagent_usage(root, "executing", "sonnet", usage, req_id="req-99")` 不传 task_type | usage-log.yaml entry 含 `task_type: req`；feedback.jsonl 含 `"task_type": "req"` | AC-04 | P0 |
| TC-02 task_type 显式 bugfix | 调用时显式传 `task_type="bugfix"`，req_id="bugfix-7" | entry 写入 `task_type: bugfix`；目录落 `.workflow/state/sessions/bugfix-7/usage-log.yaml` | AC-04 | P0 |
| TC-03 task_type 显式 sug | 显式传 `task_type="sug"`，req_id="sug-30" | entry 写入 `task_type: sug`；目录落 `.workflow/state/sessions/sug-30/usage-log.yaml` | AC-04 | P0 |
| TC-04 req_id 为空 noop | 调用时 req_id="" | 不写任何文件，函数 silent return（与既有 noop 行为一致） | AC-04 | P1 |
| TC-05 entries schema 完整性 | 写入 1 条 entry 后 yaml.safe_load | 含字段 ts / task_type / stage / role / model / usage（七子字段齐） | AC-04 | P0 |
| TC-06 派发链路端到端 dogfood | 跑本 chg 自身 executing 阶段（真实派发 ≥ 1 个 subagent） | `.workflow/state/sessions/req-43-交付总结完善/usage-log.yaml` 含 ≥ 1 条 entry；主 agent session-memory.md 含对应 `record_subagent_usage called:` 行 | AC-05 | P0 |
| TC-07 scaffold mirror diff = 0 | `diff src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md .workflow/context/roles/harness-manager.md` | exit 0（无 diff） | AC-04（前置） | P1 |
| TC-08 sug-25 状态翻转 | `harness suggest --archive sug-25` 后读 frontmatter | `status: applied` | AC-04 | P2 |

## §验证方式

- **AC-04（数据通路只消费不重采）**：TC-01~TC-05 helper 单测 + TC-07 scaffold mirror 校验；本 chg 不新建采集逻辑，仅扩 helper 字段（task_type）+ 升级派发钩子可观测性。
- **AC-05（State 层校验不退化）**：TC-06 端到端活证；本 chg 自身 done 阶段 grep `^- ts:` 在 req-43 的 usage-log.yaml entries 数 ≥ 主 agent session-memory.md 中 `record_subagent_usage called:` 行数 - 容差。
- pytest：`pytest tests/test_record_subagent_usage.py -v` 全绿（5+ 条新 case）+ 基线全量 pytest 不退化。
- `harness validate --human-docs` exit 0（chg-01 完成前自检）。

## §回滚方式

`git revert` chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25）） 的所有 commit；usage-log.yaml 文件无需删除（追加模式，旧 entries 兼容）；sug-25 frontmatter 手工翻回 `pending`（一行 sed 即可）。

## §scaffold_v2 mirror 同步范围

按 harness-manager.md 硬门禁五：
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` ↔ `.workflow/context/roles/harness-manager.md`（diff 应 = 0）
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md` ↔ `.workflow/context/roles/base-role.md`（diff 应 = 0）

`workflow_helpers.py` 不在 scaffold mirror 范围（CLI 源码非 scaffold 模板）；`tests/` 同理。

## §契约 7 注意点

- 本 plan.md 首次引用工作项 id 已带 title：req-43（交付总结完善）/ chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））/ sug-25（record_subagent_usage 派发链路真实接通）/ chg-08（硬门禁六扩 TaskList + 进度条 + stdout + 提交信息）/ chg-04（bugfix 引入 bugfix-交付总结.md（done 模板精简版））/ chg-05（sug 直接处理路径产出 3 段轻量交付总结 + State 校验扩三类任务）。
- 提交信息须形如：`feat: chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））接通派发钩子 + task_type 字段` —— 带 ≤ 15 字描述（硬门禁六）。
- 同段后续重复 id 可简写（同上下文豁免）；批量列举多个不同 id 时禁止裸数字扫射（reg-01（对人汇报批量列举 id 缺 title 不可读） / chg-06（硬门禁六 + 契约 7 批量列举子条款补丁））。
