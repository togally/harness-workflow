# Change Plan — chg-08（硬门禁六扩 TaskList + 进度条 + stdout + 提交信息）

## 1. Development Steps

### Step 1: 读取 base-role.md 硬门禁六 + stage-role.md 契约 7 现状

- 读取 `.workflow/context/roles/base-role.md` 完整"## 硬门禁六..."段，记录：
  - 触发场景清单（表格列 / 行内文字 / harness-manager 派发 / session-memory 对人摘要等）；
  - 强制规则格式示例；
  - 批量列举子条款（reg-01（对人汇报批量列举 id 缺 title 不可读）/ chg-06（硬门禁六 + 契约 7 批量列举子条款补丁））；
  - 自检方法现状；
- 读取 `.workflow/context/roles/stage-role.md` 契约 7 "id 密集展示反向豁免条款"；
- 产出扩展对齐笔记到 chg-08 session-memory.md。

### Step 2: 扩展 base-role.md 硬门禁六触发场景

- 在"触发场景"清单末尾新增 5 条 bullet（沿用现有清单格式）：
  ```markdown
  - **TodoWrite / TaskList 任务标题**（agent 主动调 TodoWrite 工具列任务时，任务文本含 id 必带描述）
  - **进度条 / `harness status` 进度摘要 / stage 流转动画**（CLI 所有对人进度输出）
  - **命令 stdout**（`harness next` / `harness status` / `harness validate` / `harness change` 等所有 CLI 面向用户输出）
  - **归档 commit message**（`archive: req-XX-<title>` / `archive: chg-XX-<desc>` / `bugfix: ...`）
  - **git log message**（所有 commit 一行化后人读取路径，含 commit title 与 body）
  ```
- 在"强制规则"段首增补一句加粗声明："**所有人读取路径**（含上列所有场景）一律 `{id}（{title}）` 或纯名称替代；禁止裸 `req-XX` / `chg-XX` / `reg-XX` / `sug-XX` / `bugfix-XX` 单独出现"。

### Step 3: 扩展 base-role.md 硬门禁六"批量列举子条款"

- 定位 "批量列举子条款" 段；
- 在触发边界描述处增补："**TaskList 多条任务并列 / commit message 列 ≥ 2 个不同 id / CLI stdout 表格列 ≥ 2 id** 时，每条都按首次引用处理（带完整 title 或 ≤ 15 字描述）"；
- 正例新增：`TodoWrite 任务：- [ ] Verify chg-01（repository-layout 契约底座）落地 + [ ] 检查 chg-02（CLI 路径迁移 flow layout）pytest`；
- 反例新增：`TodoWrite 任务：- [ ] Verify chg-01 + [ ] 检查 chg-02`（裸数字扫射，违反）。

### Step 4: 扩展 base-role.md 硬门禁六"自检方法"

- 在"自检方法"段增补两项：
  ```markdown
  1. `git log --oneline --since=<req-41 落地日期> | grep -E "(req|chg|sug|bugfix|reg)-[0-9]+"` 每命中行核对含 `（...）` / `— ...` / title 字段；
  2. agent 执行 TodoWrite 前自检任务文本；CLI 开发时 grep `render_work_item_id` 调用覆盖 stdout 输出路径（遗留覆盖缺口记录到 suggest / 后续 req）。
  ```
- 保留既有自检方法（grep 段落扫裸 id）不动。

### Step 5: 扩展 stage-role.md 契约 7 反向豁免触发判定

- 定位契约 7 "触发判定" 段；
- 原文：`同一段落 / 表格 / 列表内并列 ≥ 2 个不同 id 即触发反向豁免`；
- 改为：`同一段落 / 表格 / 列表 / TaskList / commit message / CLI stdout 中并列 ≥ 2 个不同 id 即触发反向豁免`；
- 保留其他子条款文字不动。

### Step 6: 更新 harness-manager.md 示例 stdout（若含 sample 样板）

- grep `.workflow/context/roles/harness-manager.md` 内的示例 stdout 片段；
- 若存在裸 id 样板（如 `req-41`），改为 `req-41（机器型工件回 flow/requirements）` 形态；
- 若无此类样板，本步骤跳过（不强求增加）。

### Step 7: 同步 scaffold_v2 mirror

- `cp .workflow/context/roles/base-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md`；
- `cp .workflow/context/roles/stage-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md`；
- 若 harness-manager.md 本 chg 改动，`cp` 同步；
- `diff -q` 三组零输出。

### Step 8: 自检 + 交接

- `grep -q "TodoWrite\|TaskList" .workflow/context/roles/base-role.md` PASS；
- `grep -q "进度条\|stdout\|commit message\|git log" .workflow/context/roles/base-role.md` PASS；
- `grep -q "所有人读取" .workflow/context/roles/base-role.md` PASS；
- `diff -q` mirror 零输出；
- `pytest tests/` 全量绿；
- 更新 chg-08 session-memory.md。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `grep -q "TodoWrite" .workflow/context/roles/base-role.md`
- `grep -q "TaskList" .workflow/context/roles/base-role.md`
- `grep -q "进度条\|进度摘要" .workflow/context/roles/base-role.md`
- `grep -q "stdout" .workflow/context/roles/base-role.md`
- `grep -q "commit message" .workflow/context/roles/base-role.md`
- `grep -q "git log" .workflow/context/roles/base-role.md`
- `grep -q "所有人读取" .workflow/context/roles/base-role.md`
- `grep -q "TaskList\|commit message\|CLI stdout" .workflow/context/roles/stage-role.md`（契约 7 反向豁免触发判定扩展）
- `diff -q .workflow/context/roles/base-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md`（零输出）
- `diff -q .workflow/context/roles/stage-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md`（零输出）
- `pytest tests/`（全量绿）

### 2.2 Manual smoke / integration verification

- 人工读 base-role.md 硬门禁六段改造后全文，确认：
  1. 触发场景清单含原有表格列 / 行内文字 + 新增 5 条（TaskList / 进度条 / stdout / commit / git log）；
  2. 强制规则段加粗声明"所有人读取路径一律...禁裸 id"语义清晰；
  3. 批量列举子条款示例含 TodoWrite 正反例；
  4. 自检方法含 git log grep + TodoWrite 自检两新步骤；
- 人工读 stage-role.md 契约 7 触发判定，确认含 TaskList / commit message / CLI stdout 三关键词；
- 人工跑 `git log --oneline -20 | grep -cE "(req|chg|sug|bugfix|reg)-[0-9]+\s*[^（—]"` 统计历史裸 id commit（仅观察，不追溯修正）；
- chg-07（dogfood 活证 + scaffold_v2 mirror 收口）dogfood 时，本 chg 的硬门禁六扩展生效 → grep 本 req-41（机器型工件回 flow + 废四类 brief）所有 commit message 无裸 id 形态（执行时自律遵守）。

### 2.3 AC Mapping

- AC-14（硬门禁六文字扩展部分） → Step 2 + Step 3 + Step 4 + 2.1 grep 多关键词；
- AC-15（mirror diff 归零） → Step 7 + 2.1 diff；
- AC-06（回归不破坏） → 2.1 pytest 全量绿 + 现有硬门禁六 / 七 / 契约 7 其他段文字 diff 验证。

## 3. Dependencies & Execution Order

- **前置依赖**：chg-01（repository-layout 契约底座）（repository-layout 先行，保证新契约一致性参考）；
- **可并行邻居**：chg-02（CLI 路径迁移 flow layout）/ chg-03（validate_human_docs 重写删四类 brief）/ chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止）共骨架后并行；
- **后置依赖**：chg-07（dogfood + scaffold_v2 mirror 收口）需 chg-08 的硬门禁六扩展落地后跑契约 7 批量列举子条款自检（AC-14）；
- **本 chg 内部顺序**：Step 1 读取 → Step 2 触发场景扩展 → Step 3 批量列举子条款扩展 → Step 4 自检方法扩展 → Step 5 契约 7 触发判定扩展 → Step 6 harness-manager 样板 → Step 7 mirror → Step 8 自检；强制串行。
