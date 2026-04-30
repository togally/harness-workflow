---
id: req-52
title: "硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证"
created_at: 2026-04-29
operation_type: requirement
stage: analysis
---

## Background

> 用户原话（reg-01 已 confirm route B → req-52）：
>
> 1. "现在的项目级路径绑 branch（`artifacts/{branch}/project/`），切到 release-2.0 / feature-* 等分支项目级数据就消失，**跟项目走，不跟 branch**。"
> 2. "constraints / experience 两类应该有自己的索引（index.md），按需加载、不要一次性 glob 全树读，吃 token。"
> 3. "`_merge_project_level_files` docstring 自承不接入 install_repo / update_repo 主流程；要接入主流程、加 stderr 日志、用真实 CLI 端到端验证（不只 fixture-mock）。"
> 4. "硬编码 `main` 路径要全面去除（不只是 4 处明显的，全树扫干净）。"

### 现状（req-51 已落地的项目级承载层）

req-51（项目级规则-经验-工具支持从制品引入）/ chg-01 ~ chg-04 已落地：

- 路径承载 = `artifacts/{branch}/project/{constraints,experience,tools}/`（OQ-1 = B-modified）；
- `repository-layout.md` §2.1 / §3 顶部豁免段已落定；
- `harness-manager.md` 硬门禁五例外白名单含 `artifacts/{branch}/project/`；
- `_SCAFFOLD_V2_MIRROR_WHITELIST` 含 `"artifacts/main/project/"` 字符串前缀（src/harness_workflow/workflow_helpers.py:201）；
- `_merge_project_level_files` helper 已实现（src/harness_workflow/workflow_helpers.py:8279）；
- `role-loading-protocol.md` Step 7.6 已落项目级覆盖加载段；`tools-manager.md` Step 2.0 已落项目级合并段；
- 5 份 tests：`test_req51_project_level_protection.py` / `test_req51_project_level_loading.py` / `test_req51_project_level_dogfood.py` 等。

### 实证缺陷（用户给出的 4 类反馈）

#### P1：路径绑 branch 不跟项目

`{branch}` = `_get_git_branch(root)`，下游 PetMallPlatform 在 `release-2.0` / `app_interface` / `member` 等分支切换时，项目级数据"消失"——本质上项目级 constraints / experience / tools 应当**跨分支共享**（同一项目共用一份规则，不该绑分支）。

#### P2：缺索引懒加载

`artifacts/{branch}/project/constraints/` / `experience/` 目录目前没有 `index.md` 清单文件；agent 加载链按 `_merge_project_level_files` 走 `rglob("*")` 一次性把整子树加载，下游一旦写入大量项目级规则会吃光 token。tools 子目录因为有 `keywords.yaml` 天然懒加载（按 keyword 命中再读 catalog/{tool_id}.md），不动。

#### P3：流程触发缺失 + 缺日志验证

`_merge_project_level_files` docstring 第 8293-8294 行原文："本 helper 不接入 install_repo / update_repo 主流程；仅供 role-loading-protocol Step 7.6 与 tools-manager Step 2.0 的加载链按文档 SOP 解析使用，以及 tests/test_req51_project_level_loading.py 断言。"

这是设计缺陷——加载链要真实生效必须在主流程触发（subagent 派发时由 harness-manager / 主 agent 通过 helper 加载），目前完全靠 agent 按文档自觉走 SOP，无 stderr 可证、无 e2e CLI 触发，下游真实仓的"项目级是否生效"完全黑盒。

#### P4：硬编码 `main` 路径全树未清除

src 树扫到的硬编码 `main` 字符串（不只 4 处，全扫面如下）：

| 文件 | 行号 | 当前形态 | 性质 |
|------|------|---------|------|
| `src/harness_workflow/validate_contract.py` | 551 | `str(artifacts_dir / "main" / "archive")` | archive 历史豁免目录 |
| `src/harness_workflow/validate_contract.py` | 552 | `str(artifacts_dir / "main" / "regressions")` | reg 历史豁免目录 |
| `src/harness_workflow/validate_contract.py` | 562 | `req_base = artifacts_dir / "main" / "requirements"` | 规则 0 stage-name 子目录扫描根（req-46 / chg-01） |
| `src/harness_workflow/validate_contract.py` | 1114 | docstring 含 `artifacts/main/project/` 示例 | 注释（属契约口径同步） |
| `src/harness_workflow/workflow_helpers.py` | 201 | `_SCAFFOLD_V2_MIRROR_WHITELIST` 元素 `"artifacts/main/project/"` | mirror 豁免白名单字面值（**核心**，影响 install / update / self-audit 三处过滤逻辑） |
| `src/harness_workflow/workflow_helpers.py` | 4153 | `root / ".workflow" / "flow" / "archive" / "main"`（`_next_req_id` 扫描归档树） | id 唯一性扫描历史路径 |
| `src/harness_workflow/workflow_helpers.py` | 4187 | 同上（`_next_bugfix_id` 扫描归档树） | id 唯一性扫描历史路径 |
| `src/harness_workflow/workflow_helpers.py` | 6548 | docstring 含 `artifacts/main/archive/main/req-xx` 注释（双层 branch 反例） | 注释 |
| `src/harness_workflow/workflow_helpers.py` | 3426 / 3428 / 8140 | docstring 含 `"artifacts/main/project/"` 示例 | 注释 |
| `src/harness_workflow/ff_auto.py` | 210 | `return "main"`（git branch fallback） | fallback 默认值（合理，不动） |

历史背景：PetMallPlatform / uav 等下游项目 git branch 常为 `v1.0.0` / `app_interface` / `member` / `release-2.0`，硬编码 `main` 直接失配。

### 红线（用户原话承载）

- **不动 PetMallPlatform 任何文件**（本 req 仅在 harness-workflow 自身仓改）；
- **不回滚 bugfix-11 / bugfix-12 / req-51 已落地的产物**（仅在路径维度做向前兼容性扩展）；
- **P4 硬编码扫描必须全树扫**（不只上表 4 处明显项，要确保扫面 `grep -rn '"main"' src/` 全覆盖）；
- 只改 harness-workflow 自身仓；下游用户的迁移由后续 req / harness-manager 主导。

---

## Goal

**核心目标**：把"项目级规则 / 经验 / 工具"承载层从分支绑定升级为项目绑定，加索引懒加载、接入主流程、加 stderr 日志、补端到端真实 CLI 验证；同时把 src 树所有硬编码 `main` 字符串改为 branch-aware（运行时 `_get_git_branch` 解析或 glob `artifacts/*/`）。

**可度量预期效果**：

1. PetMallPlatform 在 `release-2.0` / `feature-x` 等任意非 main 分支 git checkout 后，项目级 constraints / experience / tools 数据**仍可读**（不再因 `{branch}` 切换消失）；
2. agent 加载链按 `index.md` 懒加载，token 消耗 ≤ 旧 glob 全读 1/3（针对 ≥ 5 文件项目）；
3. `harness install` / `harness update` 主流程 stderr 真实输出 `[harness] project-level loaded: X files from artifacts/project/`（新路径）/ `... from artifacts/{branch}/project/`（legacy fallback）日志；
4. 端到端 pytest 用 `subprocess.run([sys.executable, "-m", "harness_workflow.cli", ...])` 真实 CLI 调用断言 stderr 日志命中（不再是 fixture-only mock）；
5. `grep -rn '"main"' src/harness_workflow/ | grep -v "ff_auto.py.*return.*\"main\""` 命中数 = 0（除 git fallback 默认值，所有硬编码 main 字面值移除）。

---

## Scope

### In scope（本 req 范围内）

1. **路径迁移（双轨过渡）**：项目级承载层主路径迁到 `artifacts/project/{constraints,experience,tools}/`（**无 branch 维度**）；保留 `artifacts/{branch}/project/` 为 legacy fallback，加载链先扫主路径未命中再 fallback；
2. **scaffold mirror 同步**：`repository-layout.md` §2.1 / §3 / `harness-manager.md` 硬门禁五例外白名单 / `tools-manager.md` Step 2.0 / `role-loading-protocol.md` Step 7.6 全部从 `artifacts/{branch}/project/` 改为新主路径 + legacy fallback 描述；scaffold_v2 mirror 同 commit 镜像；
3. **src 硬编码 main 全面去除**：上表 4 个核心点（validate_contract.py:551 / 552 / 562 + workflow_helpers.py:201）+ 同源处（4147 / 4180 / 4153 / 4187 等 `_get_git_branch(root) or "main"` 中可降级的硬编码 + 注释口径同步）改为 branch-aware（`_get_git_branch` 解析或 `glob artifacts/*/`）；新增反例 lint test；
4. **索引懒加载**：每个项目级子目录（`constraints/` / `experience/` 五分类 `roles,tool,risk,regression,stage`）加 `index.md` 模板（schema = `[{path, title, scope, when_load}]`）；`role-loading-protocol.md` Step 7.6 改为按 index.md 懒加载（agent 先读 index.md 再按需加载条目）；新增加载机制 helper `_load_project_level_index`；
5. **接入主流程 + stderr 日志**：`_merge_project_level_files` docstring "不接入主流程"消除；新增 `_log_project_level_load(root, hits)` helper，被 `install_repo` / `update_repo` 入口段调用；stderr 输出 `[harness] project-level loaded: {N} files from {path}`；
6. **端到端 CLI 验证**：新增 `tests/test_req52_e2e_log.py`，subprocess 真实 CLI 触发 `harness install` / `harness update`，断言 stderr 含 `project-level loaded` 字面值；新增 `tests/test_req52_no_main_hardcode.py` 反例 lint（grep `"main"` src/ 命中数白名单）；
7. **artifacts/project/ 占位**：仓库根 `artifacts/project/{constraints,experience,tools}/.gitkeep` + README.md 占位（与现 `artifacts/main/project/` 同结构）。

### Out of scope（明确划界，避免 scope creep）

1. **下游 PetMallPlatform 自身的项目级数据迁移**：本 req 仅交付双轨承载层契约 + 主路径加载链；下游用户从 `artifacts/{branch}/project/` 搬到 `artifacts/project/` 由其自己后续操作（regression / suggest 路径）；
2. **legacy 路径硬下线**：`artifacts/{branch}/project/` 退役为只读 / fallback only，不在本 req 内删除；后续 req / 一次大版本归档时统一收口；
3. **roles/ 项目级化**：req-51 OQ-3 = A 已明确不开放，本 req 不动；
4. **tools 子目录的 catalog 文件级合并增强**：`tools-manager.md` Step 2.0 现有"项目级 dict 覆盖全局 dict"逻辑不变，仅做路径迁移；
5. **构建独立的项目级 schema lint**：`harness validate --contract project-overrides`（req-51 OQ-5）继续入 sug 池，不在本 req 范围；
6. **archive 时双层 branch 路径修复**：workflow_helpers.py:6548 注释提到 `artifacts/main/archive/main/req-xx` 的双层 branch 是历史 reg-NN 残留，由 archive 重定义类 req 收口（reg-02 / req-42 已部分覆盖，本 req 仅同步注释口径，不动逻辑）。

### §OQ — 关键 Open Questions（用户拍板请求）

> 本 req 与既有契约（req-51 已落地路径 + bugfix-12 白名单 + repository-layout 三大子树）耦合度高；analyst 已识别 5 条决策点 + default-pick + 一句话理由；用户可一次性拍板或调整。

#### OQ-A：路径策略选型（**最大决策点**）

| 选项 | 路径 | 优点 | 缺点 |
|------|------|------|------|
| B（简单迁移） | `artifacts/project/{constraints,experience,tools}/`（无 branch 维度，单路径） | 字面贴合用户"跟项目走"；下游切 branch 数据不丢；契约简单 | 破坏 req-51 已落地的所有契约（5 份 tests / 4 处契约文档 / 5 处 helper / 1 处白名单字面值），回滚面大 |
| **D-modified**（**default-pick**） | 主路径 `artifacts/project/`（无 branch 维度，新建一律入此）+ legacy fallback `artifacts/{branch}/project/`（加载链先主路径未命中再 fallback；后续 req 收口退役） | 用户原话"跟项目走"主导，且不回滚 req-51 已落地物；过渡期 ≤ 1 版本 | 加载链多一层 fallback，contract 文档需双轨描述 |
| C（双轨永久并存） | 主路径 + legacy 永久双活 | 灵活 | 长期复杂度翻倍；reviewer / done 永久要核两套；不推荐 |

**default-pick = D-modified**。理由：用户原话"跟项目走，不跟 branch"占主导，且 req-51 已落地物不可回滚；D-modified 在新建一律入主路径（`artifacts/project/`）、legacy（`artifacts/{branch}/project/`）作为加载链 fallback 兼容存量，后续 req 收口退役 legacy 路径。**请用户拍板 default-pick D-modified；若坚持纯 B（直接迁移、立即退役 legacy），则需补 req-51 5 份 tests 全部改写 + scaffold mirror 大改动估时增加 1 chg**。

#### OQ-B：索引懒加载 schema

| 选项 | schema | 优缺点 |
|------|-------|-------|
| **A**（default-pick） | YAML frontmatter + Markdown 表，每条目 `{path, title, scope, when_load}`；`scope` ∈ `{constraints, experience-roles, experience-tool, ...}`；`when_load` ∈ `{always, on-stage, on-keyword}` | 与现有 experience/index.md schema 兼容；新增 `when_load` 支持懒加载；agent 解析简单 |
| B | 仅 markdown bullet 列表 | 无结构化语义，agent 难判 when_load |
| C | 纯 JSON | 与 markdown 文档分离，下游写文档时易遗漏更新 |

**default-pick = A**。理由：与 `.workflow/state/experience/index.md` 现有规则同 schema，下游学习成本低。

#### OQ-C：stderr 日志格式

| 选项 | 格式 | 优缺点 |
|------|------|-------|
| **A**（default-pick） | `[harness] project-level loaded: {N} files from {path}（fallback={legacy_path}）`；structured prefix `[harness]` 与 install_repo 现有日志同源 | grep 友好；与现有 `[install_repo]` / `[update_repo]` stderr 日志风格一致 |
| B | JSON 单行 | 对 e2e pytest 断言更稳，但人读不友好 |
| C | 仅控制台彩色 | 不利 CI/CLI 抓取 |

**default-pick = A**。理由：契合现有 stderr 日志风格（line 3761 / 3782 / 3787 等），grep / pytest substring assert 简单。

#### OQ-D：端到端 CLI 触发的子命令

| 选项 | 触发命令 | 优缺点 |
|------|---------|-------|
| **A**（default-pick） | `harness install --check`（dry-run，不写盘）+ `harness update`（写盘）双触发，stderr 各断言一次 | 不污染测试 fixture 实际状态；覆盖 install + update 两条主路径 |
| B | 仅 `harness install --check` | 覆盖面窄，update 路径未验证 |
| C | 加 `harness next` / `harness status` 等更多触发面 | 超出 P3 范围；下次 sug 入池 |

**default-pick = A**。理由：install + update 是 `_merge_project_level_files` 接入主流程的两个主入口，覆盖全；其他触发面不阻塞本 req。

#### OQ-E：硬编码 main 防回归 lint 实现

| 选项 | 实现 | 优缺点 |
|------|------|-------|
| **A**（default-pick） | `tests/test_req52_no_main_hardcode.py` pytest 反例 lint：`grep -rn '"main"' src/harness_workflow/` 命中数 ≤ 白名单（含 `ff_auto.py:return "main"`、`workflow_helpers.py: \"main\"` 中的 `_get_git_branch(root) or "main"` 兜底默认值）；新增硬编码命中即 FAIL | 实现简单，pytest 直跑；与现有 contract lint 风格一致 |
| B | 新增 `harness validate --contract no-main-hardcode` | 工程量更大；与现有 contract 套件耦合，本 req 收益不显 |
| C | git pre-commit hook | 跨开发者一致性差，CI 不一定跑 |

**default-pick = A**。理由：pytest 反例 lint 与 `tests/test_install_repo_sync_contract.py` 等现有 lint 同源，最小改动。

---

## Acceptance Criteria

> 8 条 AC，覆盖 P1 / P2 / P3 / P4 + 同型病防回归 + 真实 CLI 端到端日志断言 + scaffold mirror 同步。

- **AC-01（P1：路径迁移到无 branch 主路径）**：`repository-layout.md` §2.1 / §3 顶部豁免段含新主路径 `artifacts/project/{constraints,experience,tools}/`；同 commit 同步 `src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md`；`harness validate --human-docs` exit 0；`grep -nE "artifacts/project/" .workflow/flow/repository-layout.md` ≥ 3 命中。

- **AC-02（P1：legacy 路径 fallback 行为）**：当 `artifacts/project/` 不存在但 `artifacts/{branch}/project/` 存在时，`_merge_project_level_files` 加载链 fallback 命中 legacy 路径；stderr 日志含 `(fallback=artifacts/{branch}/project/)` 字面值；新增 `tests/test_req52_legacy_fallback.py` 单测覆盖。

- **AC-03（P4：src 硬编码 main 全面去除）**：`grep -rn '"main"' src/harness_workflow/` 命中数 ≤ 白名单（白名单仅含 `ff_auto.py:210` 的 `_get_git_branch` fallback `return "main"` + `workflow_helpers.py` 中 `_get_git_branch(root) or "main"` 形式兜底默认值；其他所有字面 `"main"` 全部消除）；validate_contract.py:551 / 552 / 562 改为 `_get_git_branch(root)` 解析或 `glob artifacts/*/`；workflow_helpers.py:201 `_SCAFFOLD_V2_MIRROR_WHITELIST` 中 `"artifacts/main/project/"` 改为 `"artifacts/project/"`（主路径）+ `"project/"`（substring 子串豁免兜底，覆盖 legacy `artifacts/*/project/`）；4153 / 4187 `flow/archive/main` 改为 `glob .workflow/flow/archive/*`。

- **AC-04（P4：反例 lint 防回归）**：新增 `tests/test_req52_no_main_hardcode.py`，pytest 直跑 `pytest tests/test_req52_no_main_hardcode.py -v` 全 PASS；包含 ≥ 3 用例（src 全树扫 / 注释 docstring 扫 / 白名单豁免单测）；后续若开发者新加硬编码 main 字面值即 FAIL。

- **AC-05（P2：索引懒加载）**：每个项目级子目录（`constraints/` / `experience/{roles,tool,risk,regression,stage}/`）含 `index.md` 模板（schema 见 OQ-B = A）；`role-loading-protocol.md` Step 7.6 改为按 `index.md` 懒加载；新增 helper `_load_project_level_index(root, scope)` 返回过滤后清单；scaffold_v2 mirror 同步契约文件。

- **AC-06（P3：接入主流程 + stderr 日志）**：`_merge_project_level_files` docstring "不接入 install_repo / update_repo 主流程" 字样消除；新增 `_log_project_level_load(root, hits, fallback_used)` helper；`install_repo` / `update_repo` 入口段（line ~3760 区域）调用并输出 stderr 日志 `[harness] project-level loaded: {N} files from {path}` 字面值。

- **AC-07（端到端真实 CLI 触发 + stderr 断言）**：新增 `tests/test_req52_e2e_log.py`，使用 `subprocess.run([sys.executable, "-m", "harness_workflow.cli", ...])` 真实子进程触发 `harness install --check` + `harness update --check`；断言 `stderr` 含 `project-level loaded` 字面值；包含 ≥ 3 用例（含项目级 0 文件 / 项目级 ≥ 1 文件 / legacy fallback 命中三场景）。

- **AC-08（scaffold mirror 同步 + contract 全绿）**：本次涉及的 4 份契约文件（`repository-layout.md` / `harness-manager.md` / `role-loading-protocol.md` / `tools-manager.md`）live + scaffold_v2 mirror 字节级一致（`diff -q` silent）；`harness validate --contract all` exit 0；`harness validate --human-docs` exit 0；现有 5 份 req-51 tests + 本 req 新增 ≥ 3 份 tests 全 PASS（无回归）。

## Split Rules

> Phase 2（chg 拆分）由 analyst 自主完成；本 req 落 4 chg：契约 + 路径迁移 / src 硬编码去除 / 索引懒加载 / 接入主流程 + 端到端日志验证。

- 各 chg 落地后跑 `harness validate --contract all` 全绿；
- 综合退出标准：AC-01 ~ AC-08 dogfood 全 PASS；
- 红线复核：(a) 不动 PetMallPlatform 任何文件；(b) 不回滚 req-51 / bugfix-11 / bugfix-12 已落产物；(c) src 全树硬编码 `"main"` 命中数 ≤ 白名单。

---

## OQ Verdicts（待用户拍板）

| # | analyst default-pick | 备注 |
|---|---------------------|------|
| **OQ-A** | **D-modified**：主路径 = `artifacts/project/{constraints,experience,tools}/`（无 branch）；legacy `artifacts/{branch}/project/` 作为加载链 fallback；后续 req 收口 | 用户原话"跟项目走、不跟 branch"主导；不回滚 req-51 已落物 |
| OQ-B | A：YAML frontmatter + Markdown 表（含 `when_load` 字段） | 与现有 experience/index.md schema 同源 |
| OQ-C | A：`[harness] project-level loaded: {N} files from {path}（fallback=...）` | 与现有 `[install_repo]` stderr 风格一致 |
| OQ-D | A：`harness install --check` + `harness update --check` 双触发 | 覆盖两条主入口，不污染 fixture |
| OQ-E | A：`tests/test_req52_no_main_hardcode.py` pytest 反例 lint | 与现有 lint 测试同源 |

**chg 拆分预告（Phase 2 锁定）**：

- **chg-01（契约 + 路径迁移）**：`repository-layout.md` / `harness-manager.md` / `role-loading-protocol.md` / `tools-manager.md` 4 份契约文件主路径改为 `artifacts/project/`（双轨过渡描述）；scaffold_v2 mirror 同步；`artifacts/project/` 占位 README + .gitkeep；
- **chg-02（src 硬编码 main 全面去除）**：validate_contract.py:551 / 552 / 562 + workflow_helpers.py:201 / 4153 / 4187 + 注释 docstring 同步；新增 `tests/test_req52_no_main_hardcode.py` 反例 lint；
- **chg-03（索引懒加载）**：每个项目级子目录加 `index.md` 模板；`role-loading-protocol.md` Step 7.6 改为按 index.md 懒加载；新增 `_load_project_level_index` helper；scaffold_v2 mirror 同步；
- **chg-04（接入主流程 + stderr 日志 + 端到端 CLI 验证）**：`_merge_project_level_files` 接入 `install_repo` / `update_repo`；新增 `_log_project_level_load` helper；新增 `tests/test_req52_e2e_log.py`（subprocess 真实 CLI 触发 stderr 断言）。
