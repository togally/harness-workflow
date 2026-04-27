# Change Plan — chg-04（bugfix 引入 bugfix-交付总结.md（done 模板精简版））

> 所属 req：req-43（交付总结完善）；前置依赖：chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））（task_type="bugfix" 字段）+ chg-03（per-stage 合并到 stage × role × model 单表渲染）（复用单表 helper）。

## §目标

解决 AC-01 + AC-07 的 bugfix 维度：bugfix 完成时新增 `bugfix-交付总结.md` 全套对人产物路径；模板复用 done.md 六层回顾框架但**精简字段**（OQ-2 用户已确认）——删「chg 段」（bugfix 通常无 chg 拆分）+ 合并「testing+acceptance」为「修复验证」段；落位 `artifacts/{branch}/bugfixes/{bugfix-id}-{slug}/bugfix-交付总结.md`（与 repository-layout.md §3.2 bugfix 子树对齐）；不新增 stage（D-2 default-pick），由主 agent 在 acceptance pass 后绑定 `harness archive` pre-hook 直接产出；`harness validate --human-docs` 校验扩 bugfix 维度。

## §影响文件列表

- `.workflow/flow/repository-layout.md`：§2 对人文档白名单新增 `bugfix-交付总结.md` 类型行（bugfix 级，acceptance 后由主 agent 产出）；§3.2 bugfix 子树落位补 `artifacts/{branch}/bugfixes/{bugfix-id}-{slug}/bugfix-交付总结.md`；§5 命名前缀约定补一行。
- `.workflow/context/roles/done.md`：`## 对人文档输出` 段加 bugfix 分支模板（D-3 default-pick = B 扩 done.md，不另起新 role.md）——保留六层回顾 + 总耗时 + 总 token + stage × role × model 单表（chg-03 已落地）；删「chg 段」；合并 testing + acceptance 为「修复验证」段。
- `src/harness_workflow/workflow_helpers.py::done_efficiency_aggregate`：新增可选参数 `task_type: str = "req"` 切换 entries 读取路径（"req" → `.workflow/state/sessions/{req-id}/usage-log.yaml`；"bugfix" → `.workflow/state/sessions/{bugfix-id}/usage-log.yaml`），与 chg-01 task_type 配套。
- `src/harness_workflow/validate_human_docs.py::_collect_bugfix_items`（line 373）：新增 `bugfix-交付总结.md` 必查项（bugfix 已 acceptance pass 但缺该文件 → exit 非 0，阻断 `harness archive`）。
- `tests/test_bugfix_delivery_summary.py`（**新增**）：覆盖 bugfix 完成时 `bugfix-交付总结.md` 产出 / 缺失阻断 / 模板字段精简（无 chg 段、有「修复验证」合并段）/ 单表渲染 + done_efficiency_aggregate(task_type="bugfix") 正确读路径。
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md` + `.workflow/flow/repository-layout.md`：scaffold mirror 同步。

## §实施步骤

1. `repository-layout.md` 改写：§2 白名单加 `bugfix-交付总结.md` 行；§3.2 bugfix 子树补落位；§5 命名前缀加一行。
2. `done.md` `## 对人文档输出` 段加 bugfix 分支：保留六层回顾 + 总耗时 + 总 token + stage × role × model 单表（沿用 chg-03 模板）；删「chg 段」；合并 testing+acceptance 为「修复验证」段；新增段头标识「bugfix 交付总结模板（精简版）」。
3. helper 改 `done_efficiency_aggregate` 签名加 `task_type: str = "req"`；逻辑：`task_type == "bugfix"` 时 sessions_dir 路径模板换成 bugfix-id；既有 req 路径行为不变（向后兼容）。
4. `validate_human_docs._collect_bugfix_items` 加 `bugfix-交付总结.md` 必查项；当 bugfix state.yaml `status` 已为 done / acceptance pass 时校验该文件存在，缺失则 exit 非 0。
5. 写 pytest `tests/test_bugfix_delivery_summary.py` ≥ 5 case：bugfix-交付总结.md 产出 / 缺失阻断 `harness archive` / 模板「修复验证」合并段存在 / done_efficiency_aggregate(task_type="bugfix") 路径切换正确 / 模板无「chg 段」（精简验证）。
6. scaffold mirror 同步 `done.md` + `repository-layout.md`。
7. 收口：`harness validate --human-docs` exit 0 + `pytest tests/` 全绿（基线 + 5 条新 case）。

## §测试用例设计

> regression_scope: targeted（新增 bugfix 维度路径，不动既有 req 路径行为；helper 签名加默认参数向后兼容）
> 波及接口清单（git diff --name-only 预估 + 人工补全）：
> - `.workflow/flow/repository-layout.md` §2 / §3.2 / §5
> - `.workflow/context/roles/done.md`（对人文档输出段 bugfix 分支）
> - `src/harness_workflow/workflow_helpers.py::done_efficiency_aggregate`
> - `src/harness_workflow/validate_human_docs.py::_collect_bugfix_items`

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 bugfix-交付总结.md 产出 | bugfix-99 acceptance pass 后主 agent 调 done 模板渲染 | `artifacts/main/bugfixes/bugfix-99-{slug}/bugfix-交付总结.md` 落盘；含六段（需求是什么 / 交付了什么 / 修复验证 / 结果是什么 / 后续建议 / §效率与成本） | AC-01（bugfix 维度） | P0 |
| TC-02 缺失阻断 archive | bugfix-99 已 acceptance pass，artifacts 下无 `bugfix-交付总结.md`，调 `harness archive bugfix-99` | `harness validate --human-docs` exit 非 0；archive 阻断；错误信息含 "bugfix-交付总结.md missing" | AC-07（bugfix 维度） | P0 |
| TC-03 模板「修复验证」合并段 | 渲染 bugfix-99 模板 | 含「## 修复验证」段（合并 testing + acceptance）；不含独立的「## testing」/「## acceptance」分段 | AC-01 | P1 |
| TC-04 模板无 chg 段 | 渲染 bugfix-99 模板 | 不含「chg 列举段」（与 req 模板差异点） | AC-01 | P1 |
| TC-05 helper task_type="bugfix" 路径 | 调 `done_efficiency_aggregate(root, "bugfix-99", task_type="bugfix")` | sessions_dir 解析为 `.workflow/state/sessions/bugfix-99/usage-log.yaml`；entries 正确读取 | AC-04 | P0 |
| TC-06 helper 默认 task_type="req" 兼容 | 调 `done_efficiency_aggregate(root, "req-99")`（不传 task_type） | sessions_dir 解析为 req 路径（与既有行为一致）；不抛异常 | AC-04 | P0 |
| TC-07 单表渲染 bugfix 维度 | bugfix-99 真实 usage-log.yaml 跑 helper | stage_role_rows 至少含 regression / executing / testing / acceptance 四 stage（bugfix 流程经历的 stage）；按 stage_order 排序 | AC-02 / AC-04 | P0 |
| TC-08 scaffold mirror 同步 | `diff scaffold_v2/.workflow/context/roles/done.md .workflow/context/roles/done.md` + `repository-layout.md` | 两份均 exit 0（无 diff） | AC-04（前置） | P1 |

## §验证方式

- **AC-01（bugfix 维度）**：TC-01 / TC-03 / TC-04；本 chg 完成后下一个新 bugfix（或回填一个历史 bugfix dogfood，可选）端到端验证 bugfix-交付总结.md 产出 + 字段精简正确。
- **AC-07（bugfix 维度归档对接一致）**：TC-02；`harness archive` 对 bugfix 类型与 req 类型同等校验，缺 `bugfix-交付总结.md` 阻断。
- **AC-02 / AC-04（复用 chg-03 单表 + 数据通路）**：TC-05 / TC-06 / TC-07；helper 签名向后兼容、路径切换正确。
- pytest：`pytest tests/test_bugfix_delivery_summary.py -v` 全绿 + 基线不退化。
- `harness validate --human-docs` exit 0；scaffold mirror diff = 0。

## §回滚方式

`git revert` chg-04（bugfix 引入 bugfix-交付总结.md（done 模板精简版）） 的所有 commit；historic bugfix-1 ~ bugfix-6 已归档目录不做回填（豁免，与 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）） legacy fallback 一致）。

## §scaffold_v2 mirror 同步范围

按 harness-manager.md 硬门禁五：
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md` ↔ `.workflow/context/roles/done.md`（diff 应 = 0）
- `src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` ↔ `.workflow/flow/repository-layout.md`（diff 应 = 0）

`workflow_helpers.py` + `validate_human_docs.py` + `tests/` 不在 mirror 范围。

## §契约 7 注意点

- 本 plan.md 首次引用工作项 id 已带 title：req-43（交付总结完善）/ chg-04（bugfix 引入 bugfix-交付总结.md（done 模板精简版））/ chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））/ chg-03（per-stage 合并到 stage × role × model 单表渲染）/ bugfix-1（harness update --check 等 flag 被角色触发吞了）/ bugfix-4（harness install 升级清理：旧 layout / .bak / schema 不一致）/ bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））/ req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））。
- 提交信息须形如：`feat: chg-04（bugfix 引入 bugfix-交付总结.md（done 模板精简版））模板 + 校验扩展` —— 带 ≤ 15 字描述（硬门禁六）。
- 批量列举 bugfix-1 / bugfix-4 / bugfix-6 等多个不同 id 时每条必带 ≤ 15 字描述（reg-01（对人汇报批量列举 id 缺 title 不可读） / chg-06（硬门禁六 + 契约 7 批量列举子条款补丁））。
