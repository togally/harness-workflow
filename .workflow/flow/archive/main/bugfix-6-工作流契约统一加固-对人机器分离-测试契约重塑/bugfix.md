---
id: bugfix-6
title: 工作流契约统一加固（对人机器分离 + 测试契约重塑）
created_at: 2026-04-26
---

# 问题描述

融合 bugfix，打包用户 2026-04-25 夜连续提出的 3 件未决工作流契约问题：

- **事项 A**：对人 / 机器型工件路径关注点分离强化——artifacts/ 应只放对人产物（含 sql / 报告 / PDF / 对外发布），`.workflow/flow/` 应只放过程文档（session-memory / diagnosis / test-evidence / bugfix.md / change.md / plan.md / checklist.md）。bugfix CLI 路径全违规，吸收 sug-30（bugfix 路径关注点分离）；扩契约面到任意任务类型。
- **事项 B**：测试契约重塑——把"测试用例设计"权责前移到 planning（analyst / opus），testing 仅执行 + 客观评估，默认 targeted、全量回归仅 acceptance / done 触发或 planning 显式标记。
- **事项 C**：bugfix 流程的 planning 等价载体——bugfix 流程跳过 planning，事项 B 引入的 plan.md §测试用例设计 在 bugfix 路径无落地点。default-pick D-B1：regression/diagnosis.md 末尾新增 §测试用例设计 章节，testing 直接消费。

详见 `regression/diagnosis.md` 的 3 事项块独立诊断。

# 根因分析

见 `regression/diagnosis.md` 各事项 §根因分析（L1 / L2 / 根本根因 / 结构根因 四层）。综合：

- 事项 A 根本根因：req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）） / chg-02（CLI 路径迁移 flow layout）只覆盖 requirement 路径，未对 bugfix / sug / 任意未来任务类型施加同款契约；契约定义层（repository-layout.md）缺少"任务类型无关"硬门禁。
- 事项 B 根本根因：测试用例设计权责错配——AC 出自 analyst（opus），让 testing（sonnet）"再设计一遍"是责任倒挂；planning → testing 缺契约接口（plan.md §测试用例设计）。
- 事项 C 根本根因：bugfix 流程是 req 流程的精简映射，无 planning，事项 B 前置后 testing 无设计单可读。

# 修复范围

### 涉及文件 / 模块（按事项分类）

**事项 A（路径关注点分离）**：

- `src/harness_workflow/workflow_helpers.py::create_bugfix`（行 4540-4626）
- `src/harness_workflow/workflow_helpers.py::create_suggestion / create_change`（按需复核）
- `src/harness_workflow/validate_contract.py`（新增 `artifact-placement` 契约）
- `src/harness_workflow/cli.py::validate_parser --contract`（行 251-257，扩 choices）
- `.workflow/flow/repository-layout.md`（§1 + §3 + §5 扩任务类型）
- `.workflow/context/roles/{regression, executing, testing, acceptance, done, analyst}.md`（grep "artifacts/" 路径表述修正）
- `src/harness_workflow/assets/scaffold_v2/.workflow/...`（mirror 同步）
- 存量迁移脚本：bugfix-1 ~ bugfix-5 + bugfix-6 自身从 artifacts/ → `.workflow/flow/bugfixes/`

**事项 B（测试契约重塑）**：

- `.workflow/context/roles/analyst.md`（Step B2 / B3 加 §测试用例设计 产出步骤）
- `.workflow/context/roles/testing.md`（Step 2 / 2.5 改写）
- `.workflow/context/roles/{planning, requirement-review}.md`（legacy alias 同步）
- `.workflow/evaluation/testing.md`（默认 targeted + 全量触发条件段）
- `src/harness_workflow/assets/skill/assets/templates/change-plan.md.tmpl` + `.en.tmpl`（plan.md 模板加 §测试用例设计 章节）
- `src/harness_workflow/validate_contract.py`（新增 `test-case-design-completeness` 契约）
- `src/harness_workflow/cli.py::validate_parser --contract`（扩 choices）

**事项 C（bugfix 流程 planning 等价载体）**：

- `.workflow/context/roles/regression.md`（SOP 加"测试用例设计（bugfix 模式）"步骤）
- `.workflow/evaluation/regression.md`（加该项）
- `src/harness_workflow/assets/templates/bugfix.md`（diagnosis.md 模板加 §测试用例设计 章节）
- `validate_contract.py::test-case-design-completeness` 扩展覆盖 bugfix 流程

### 不在本次修复范围

- sug-31（done 后 commit + revert dry-run）：不吸收，独立成后续 bugfix-7+ 或 req（见 diagnosis §事项 D）。
- sug-32（回 req-43（交付总结完善） 跑 next 自证）：不吸收，待 bugfix-6 完成后由用户决定 req-43 续跑时合并处理。
- bugfix-1 ~ bugfix-5 历史 artifacts/ 目录的物理删除：不删，留 README 占位 + git mv 留痕（default-pick）。
- 业务代码（src/ 下非 workflow_helpers / validate_contract / cli 文件）：不动。
- 历史 req-02 ~ req-40 的存量结构：不追溯（按 repository-layout.md §4 三段式分水岭豁免规则）。

# 修复方案

> 共 14 个修复点（事项 A: 5 + 事项 B: 6 + 事项 C: 3），≤ 12 限制超出 2 点理由：B5 / B6 是事项 B 落地的两个独立 lint，不可合并；如需压缩，可把 B6（话术拦截）降级为 sug 后置项。

## 事项 A 块（5 点：路径关注点分离）

### A1：CLI `create_bugfix` 路径迁移到 flow layout

- **文件**：`src/harness_workflow/workflow_helpers.py::create_bugfix`（行 4540-4626）
- **改动**：参考 `create_requirement` 的 `_use_flow_layout(req_id)` 三分支模式，引入 `_use_flow_layout_for_bugfix(bugfix_id)`（默认 True，因 bugfix 无历史分水岭）；机器型文档 `bugfix.md` / `session-memory.md` / `regression/diagnosis.md` / `regression/required-inputs.md` / `test-evidence.md` 落 `.workflow/flow/bugfixes/{bugfix-id}-{slug}/`；artifacts/ 路径仅作"对人产物预留目录"创建（空或仅 README 占位）。
- **同步**：导出常量 `BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID = 6`（本 bugfix 起强制；bugfix-1 ~ bugfix-5 走 A5 迁移）。
- **验收**：`harness bugfix "<title>"` 执行后，artifacts/main/bugfixes/{dir}/ 下 0 个 .md，`.workflow/flow/bugfixes/{dir}/` 下 5 份机器型文档齐备。

### A2：复核 + 同步 `harness_suggest.py` / `harness_change.py` / `harness_requirement.py`

- **文件**：`src/harness_workflow/workflow_helpers.py::create_suggestion / create_change / create_requirement`
- **改动**：
  - `create_change`：现有行为已经走 req 树继承（req-41+ 走 `.workflow/flow/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/`），复核无违规即可。
  - `create_suggestion`：现有行为落 `.workflow/flow/suggestions/`（机器型，正确）；复核无违规。
  - `create_requirement`：复核 `_use_flow_layout` 在 `requirement.md` 副本是否仍 copy 到 artifacts/（这是对人产物，正确）。
- **scaffold_v2 mirror**：同步任何 helper 改动到 `src/harness_workflow/assets/scaffold_v2/`。
- **验收**：grep `artifacts/` 在三个 create_ 函数体内仅命中"对人产物" / "raw 副本" / "对人占位 README" 路径，无机器型 .md write_if_missing。

### A3：新增 `harness validate --contract artifact-placement` lint

- **文件**：`src/harness_workflow/validate_contract.py`（新增章节）+ `src/harness_workflow/cli.py::validate_parser --contract choices`（加 `"artifact-placement"`）
- **改动**：
  - lint 规则 1：扫 `artifacts/{branch}/**/*.md`，命中机器型文件名（白名单外）→ FAIL。机器型文件名清单：`bugfix.md` / `change.md` / `plan.md` / `diagnosis.md` / `session-memory.md` / `test-evidence.md` / `required-inputs.md` / `analysis.md` / `decision.md` / `meta.yaml` / `regression.md` / `done-report.md` / `checklist.md` 等。
  - lint 规则 2：扫 `.workflow/flow/**/*` 命中对人最终产物（白名单外）→ FAIL。对人最终产物模式：`*交付总结.md` / `*决策汇总.md` / `*.sql` / `*.pdf` / `部署文档*.md` / `接入配置说明*.md` / `runbook-*.md` / `manual-*.md` / `guide-*.md` / `contract-*.md` 等（参考 repository-layout.md §2 白名单）。
  - exit code：lint 命中违规 = 1，全绿 = 0。
- **挂载**：契约 4 硬门禁内联到 stage 角色 SOP（"subagent 交接前执行 `harness validate --contract artifact-placement`"），analyst / executing / testing / acceptance / regression / done 全部 stage 退出条件加该项（与现有 `harness validate --human-docs` 并列）。
- **验收**：在当前仓库实测——A1 落地前 `harness validate --contract artifact-placement` 应 FAIL（命中 bugfix-1 ~ bugfix-6 的 artifacts/ 违规）；A5 迁移后应 PASS。

### A4：文档侧路径表述修正

- **文件**：`.workflow/flow/repository-layout.md` + `.workflow/context/roles/{regression, executing, testing, acceptance, done, analyst, planning, requirement-review}.md` + `src/harness_workflow/assets/scaffold_v2/.workflow/...` mirror
- **改动**：
  - `repository-layout.md` §1 三大子树语义增加"任意任务类型"通用约束（不限 req，扩到 bugfix / sug-direct / 任意未来任务）。
  - `repository-layout.md` §3 后新增 §3.2 bugfix 机器型文档权威落位（与 §3 req 级对称）：
    ```
    .workflow/flow/bugfixes/{bugfix-id}-{slug}/
      ├── bugfix.md
      ├── session-memory.md
      ├── test-evidence.md
      └── regression/{diagnosis.md, required-inputs.md}
    ```
  - 各 role.md 文件内 grep `artifacts/` 路径表述：bugfix 相关引用统一改为 `.workflow/flow/bugfixes/...`。
  - scaffold_v2 mirror 同步。
- **验收**：grep `artifacts/.*bugfix` 在 .workflow/context/roles/ 命中行 = 0（除非显式说"对人占位目录"）。

### A5：存量迁移脚本 + 命令

- **文件**：新增 `src/harness_workflow/tools/harness_migrate.py`（或扩 `cli.py::migrate_parser`）
- **改动**：新增 `harness migrate --bugfix-layout` 子命令，把 `artifacts/{branch}/bugfixes/bugfix-1~5/` + `artifacts/{branch}/bugfixes/bugfix-6/` 的机器型文档 git mv 到 `.workflow/flow/bugfixes/{dir}/`；artifacts/ 旧目录保留 + 写一个 `README.md` 占位说明"本目录历史 bugfix 机器型工件已迁出，对人产物（如 sql / 部署脚本）按需追加"。
- **default-pick A5-1**：保留旧 artifacts/ 目录留 README 占位 + git mv 留痕，**不物理删除**——理由：保留历史可追溯性 + git log 自带迁移证据；用户随时可再加 `--purge` flag 物理删。
- **验收**：迁移后 `harness validate --contract artifact-placement` PASS；git log 显示 `git mv artifacts/main/bugfixes/bugfix-N/.. .workflow/flow/bugfixes/bugfix-N/...` 完整历史。

## 事项 B 块（6 点：测试契约重塑）

### B1：analyst.md SOP 加 "Step B 末：测试用例设计"

- **文件**：`.workflow/context/roles/analyst.md`（Step B2 与 B3 之间加 Step B2.5）
- **改动**：新增 Step B2.5 "测试用例设计（planning stage）"——
  - 通过 `git diff --name-only` + 人工分析 "波及接口" = 修改文件 → 直接 import / 跨模块调用链路；
  - 在每个 `plan.md` 末尾追加 §测试用例设计 章节，列出**所有波及接口**对应的 AC 用例：每条用例 ≤ 5 行，字段固定 = `用例名 / 输入 / 期望 / 对应 AC / 优先级 P0/P1/P2`；
  - default-pick：planning 默认不要求全量回归；plan.md §测试用例设计 段头加 `regression_scope: targeted` 字段（也可 = `full` 触发 testing 跑全量）。
- **验收**：执行 `harness next` 时，analyst 必产出 plan.md 含 §测试用例设计 段；段缺 / 用例数 = 0 / 波及接口无对应用例 → B5 lint FAIL。

### B2：testing.md SOP Step 2 / 2.5 改写

- **文件**：`.workflow/context/roles/testing.md`
- **改动**：
  - Step 2 改写为 "**读取 plan.md §测试用例设计**"（bugfix 模式回退到 `regression/diagnosis.md §测试用例设计`，由 C1 提供）；
  - Step 2.5 改写为 "**实现为可执行单测代码**"——按 plan.md / diagnosis.md §测试用例设计 列表逐条实现单测，文件命名遵循项目约定（`tests/test_*.py`）；
  - Step 2.5 末尾保留 "testing 仍可独立补充反例 / 边界用例" 例外子条款（避免 testing 被完全降权）；
  - Step 2.75 合规扫描默认范围保持 targeted（已有，无需改）；
  - Step 3 执行——按 plan.md `regression_scope` 字段决定 targeted（默认）/ full（仅当 plan.md 显式标记）；
  - Step 5 判定 → 不变。
- **退出条件**：删 "测试用例文件已编写并可执行"中的"设计"含义，改为 "plan.md §测试用例设计 / diagnosis.md §测试用例设计 中所有 P0/P1 用例已实现为单测且执行通过"。
- **验收**：grep `Step 2: 设计测试用例` 在 testing.md = 0 行；grep `读取 plan.md §测试用例设计` 在 testing.md ≥ 1 行。

### B3：evaluation/testing.md 加"默认 targeted + 全量触发条件"段

- **文件**：`.workflow/evaluation/testing.md`
- **改动**：在章节 1（R1 越界核查）之前新增章节 0 "测试范围默认 targeted"——
  - 默认 testing 范围 = plan.md / diagnosis.md §测试用例设计 列出的用例 + Step 2.75 合规扫描的 git diff 命中（已有规则）；
  - 全量回归触发条件（任一即可）：(a) plan.md §测试用例设计 段头标记 `regression_scope: full`；(b) acceptance / done 阶段显式触发；(c) 用户在 briefing 中显式要求；
  - **禁止**主 agent 在 briefing 中默认要求 testing 跑全量（违反视为 over-instructing，由 B6 lint WARN）。
- **验收**：testing.md SOP 中所有 "全量回归" 表述均有"触发条件"显式说明。

### B4：plan.md 模板加 §测试用例设计 章节

- **文件**：`src/harness_workflow/assets/skill/assets/templates/change-plan.md.tmpl` + `.en.tmpl`（同步双语）
- **改动**：在末尾"3. 依赖与执行顺序"之后新增 "4. 测试用例设计" 章节，结构：
  ```markdown
  ## 4. 测试用例设计

  > regression_scope: targeted  # 改为 full 触发 testing 全量回归（默认 targeted）
  > 波及接口清单（git diff --name-only 自动生成 + 人工补全）：
  > - {file1}
  > - {file2}

  | 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
  |-------|------|------|---------|--------|
  | TC-01 | ... | ... | AC-01 | P0 |
  ```
- **同步**：所有 mirror 路径（`.claude/skills/harness/assets/templates/`、`.codex/...`、`.qoder/...`、`build/lib/...`、`src/harness_workflow/assets/scaffold_v2/...`）。
- **验收**：`harness change "<title>"` 创建的 plan.md 模板含 §4. 测试用例设计 章节。

### B5：新增 `harness validate --contract test-case-design-completeness` lint

- **文件**：`src/harness_workflow/validate_contract.py`（新增章节）+ `src/harness_workflow/cli.py::validate_parser --contract choices`
- **改动**：
  - lint 规则 1（planning 完成后扫描 plan.md）：缺 §测试用例设计 段 / 用例数 = 0 → FAIL；
  - lint 规则 2（波及接口覆盖度）：对 plan.md `波及接口清单` 中每个 file，要求至少 1 条用例的 "对应 AC" 字段非空；缺失 → FAIL（git diff helper 自动生成清单，人工补全后 lint 校验完整性）；
  - lint 规则 3（bugfix 模式）：扫 `.workflow/flow/bugfixes/{dir}/regression/diagnosis.md`，要求含 §测试用例设计 段（C1 提供模板）；
  - exit code：违规 = 1，全绿 = 0。
- **挂载**：planning（analyst）退出条件 + bugfix regression 退出条件 + testing 进入前必跑。
- **验收**：B1 / C1 落地后跑 `harness validate --contract test-case-design-completeness` 在本 bugfix-6 自身应 PASS（diagnosis.md 含 §测试用例设计 段）。

### B6：briefing 话术拦截 lint（WARN，非 FAIL）

- **文件**：`src/harness_workflow/validate_contract.py`（扩 `test-case-design-completeness` 章节）+ briefing 文本扫描入口
- **改动**：新增 lint 规则 4：grep 主 agent 派发文本（如 `.workflow/state/sessions/{id}/briefings/*` 或 session-memory 留痕）含 `pytest tests/ -x` / `pytest tests/$` / `全量回归` 字样且无 plan.md / diagnosis.md §测试用例设计 引用 → WARN（不 FAIL，避免误伤合规场景）。
- **理由**：用户原话"testing 二次全过 471 全量回归"是症状；此 lint 帮助主 agent 自检，但不应阻塞 stage 推进。
- **default-pick B6-1**：可降级为 sug 后置项（若本 bugfix scope 太大），由后续 bugfix 实施。
- **验收**：在历史 bugfix-5 周期 session-memory 上跑此 lint 应至少 WARN 1 次（命中 over-instructing 证据）。

## 事项 C 块（3 点：bugfix 流程 planning 等价载体）

### C1：regression.md SOP 加 "Step 4.5：测试用例设计（bugfix 模式）"

- **文件**：`.workflow/context/roles/regression.md`
- **改动**：在 Step 4 "产出诊断文档" 与 Step 5 "交接" 之间新增 Step 4.5——
  - **bugfix 模式**：在 `regression/diagnosis.md` 末尾追加 §测试用例设计 章节（结构同 plan.md §测试用例设计：波及接口清单 + `regression_scope` 字段 + 用例表 `用例名 / 输入 / 期望 / 对应 AC / 优先级`）；
  - **req 模式（regression 重新触发的场景）**：跳过本 Step（plan.md 已由 analyst 产出）。
- **退出条件**：bugfix 模式增加 "diagnosis.md 含 §测试用例设计 段，用例覆盖所有波及接口"。
- **验收**：本 bugfix-6 自身的 diagnosis.md（即本目录文件）需在 executing 阶段补加 §测试用例设计 段（也可由 regression 在本 stage 直接补，但根据"不动业务代码 + 形式化诊断"约束，本 stage 仅形式化诊断 3 事项 + 写修复方案，§测试用例设计 段由 executing 落地后的 testing 在补做时按 B1/C1 模式追加，避免本 stage 跨职）。

### C2：evaluation/regression.md 加该项

- **文件**：`.workflow/evaluation/regression.md`
- **改动**：在 "## diagnosis.md 格式" 章节模板尾部追加 §测试用例设计 块（bugfix 模式必填、req 模式可选），并加章节 "测试用例设计契约（bugfix 模式）"——重申 B5 lint 在 bugfix 流程的覆盖。
- **验收**：grep `测试用例设计` 在 evaluation/regression.md ≥ 1 行。

### C3：B5 lint 扩展覆盖 bugfix 流程

- **文件**：`src/harness_workflow/validate_contract.py::test-case-design-completeness`
- **改动**：在 B5 lint 规则 3 中已写入"扫 `.workflow/flow/bugfixes/{dir}/regression/diagnosis.md`"，本 C3 是 B5-3 的形式确认（无新代码，仅契约文档侧明确"B5 lint 双向覆盖 plan.md + bugfix diagnosis.md"）。
- **验收**：B5 lint 在 bugfix 流程跑通；本 bugfix-6 完成 C1 落地后跑 lint 应 PASS。

# 验证清单

> 10-14 条可执行 + 可断言用例，标 A1 ~ A5 / B1 ~ B6 / C1 ~ C3 来源。

| # | 来源 | 用例 | 断言 |
|---|------|------|------|
| 1 | A1 | `harness bugfix "test-A1"` 后查 artifacts/main/bugfixes/test-A1*/ | 仅含 README.md 占位（或为空），不含任何机器型 .md |
| 2 | A1 | 同上后查 .workflow/flow/bugfixes/test-A1*/ | 含 bugfix.md + session-memory.md + regression/diagnosis.md + regression/required-inputs.md + test-evidence.md |
| 3 | A3 | `harness validate --contract artifact-placement`（A5 迁移前）| exit code = 1，stdout 列出 bugfix-1 ~ bugfix-6 违规文件 |
| 4 | A3 + A5 | `harness migrate --bugfix-layout && harness validate --contract artifact-placement` | exit code = 0 |
| 5 | A4 | `grep -rn "artifacts/.*bugfix" .workflow/context/roles/` | 命中行 = 0（除"对人占位目录"显式说明） |
| 6 | A2 | grep `artifacts/` in `create_change / create_suggestion` body | 仅命中"对人产物" / "raw 副本"路径，无机器型 .md write_if_missing |
| 7 | B1 | `harness change "test-B1"` 后查生成的 plan.md | 含 §测试用例设计 章节模板 |
| 8 | B2 | grep `Step 2: 设计测试用例` in testing.md | 命中 = 0；grep `读取 plan.md §测试用例设计` ≥ 1 |
| 9 | B3 | grep `全量回归` in evaluation/testing.md | 每处命中行 ±3 行内必含"触发条件" / "默认 targeted"语义 |
| 10 | B4 | diff 所有 plan-tmpl mirror（.claude / .codex / .qoder / build / scaffold_v2） | 全部含 §测试用例设计 章节 |
| 11 | B5 | 在缺 §测试用例设计 的 mock plan.md 跑 `harness validate --contract test-case-design-completeness` | exit code = 1，stdout 显示缺段 |
| 12 | B5 + C3 | 在缺 §测试用例设计 的 mock bugfix diagnosis.md 跑同上 lint | exit code = 1，stdout 显示缺段 |
| 13 | B6 | 在含 `pytest tests/ -x` 的 mock briefing 跑同上 lint | exit code = 0（WARN 不阻塞），stderr 含 WARN 消息 |
| 14 | C1 + C2 | grep `测试用例设计` in regression.md + evaluation/regression.md | 各 ≥ 1 行；regression.md SOP Step 4.5 存在 |

# 回滚方式

### 每修复点独立可回滚

- A1：恢复 `create_bugfix` 旧硬编码 `artifacts/{branch}/bugfixes/...` 路径（`git revert <A1-commit>`）。
- A2：单 helper 函数级回滚。
- A3：删 `validate_contract.py::artifact_placement` 章节 + 删 `cli.py` choices 中 `"artifact-placement"`。
- A4：`git revert <A4-commit>` 即可（纯文档改动）。
- A5：`harness migrate --bugfix-layout --reverse`（迁移命令需附带反向；否则手工 git mv 回旧位）。
- B1 / B2 / B3：纯文档 / 模板改动，`git revert` 即可。
- B4：删 §4 章节模板。
- B5 / B6：删 lint 规则 + 删 cli.py choices。
- C1 / C2：纯文档改动，`git revert` 即可。
- C3：与 B5 同源，无独立回滚。

### 整体兜底

- `git revert <bugfix-6-merge-commit>..<HEAD>` 一键回滚整个 bugfix-6 + 后续依赖 commit；前提是本 bugfix 提交时遵守"一 chg 一 commit"颗粒（建议 executing 阶段拆 14 commit 与 14 修复点对齐）。

# 后续 / 后置

### 不吸收项（diagnosis §事项 D 决策）

- sug-31（done 后 commit + revert dry-run）：保留 `.workflow/flow/suggestions/`，待用户独立立项 bugfix-7+ 或 req。
- sug-32（回 req-43（交付总结完善） 跑 next 自证）：保留，待 req-43 续跑时一并验证 bugfix-5 + bugfix-6 + req-43。

### 留痕项

- A5 迁移完成后，`artifacts/main/bugfixes/bugfix-1~6/` 旧目录是否物理删除：default-pick = 保留 README 占位 + git mv 留痕，不物理删；用户随时可加 `--purge` flag 物理删。
- B6 briefing 话术拦截 lint 若 scope 太大，可降级为 sug 后置项（标 sug-33 候选）。
- bugfix-6 自身的 §测试用例设计 段在 executing → testing 阶段按 C1 模式追加（regression stage 仅形式化诊断，避免跨职）。

# 验证标准

- 上述 §验证清单 14 条全 PASS；
- `harness validate --contract all` exit code = 0；
- `pytest tests/` 零回归（targeted 范围 = 修改的 workflow_helpers / validate_contract / cli 相关单测）；
- 文档 lint：`grep "artifacts/.*bugfix\|artifacts/.*sql" .workflow/context/roles/` 命中行符合 §修复点 A4 预期。
