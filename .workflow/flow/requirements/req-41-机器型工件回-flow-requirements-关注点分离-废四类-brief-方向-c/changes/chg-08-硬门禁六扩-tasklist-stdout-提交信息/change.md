# Change

## 1. Title

硬门禁六扩 TaskList + 进度条 + stdout + 归档 commit message + git log

## 2. Goal

- `.workflow/context/roles/base-role.md` 硬门禁六（对人汇报场景 ID 必带简短描述）**触发场景**清单扩展覆盖面：TodoWrite TaskList 任务标题 / 进度条（`harness status` 进度摘要）/ 命令 stdout（CLI 所有对人输出）/ 归档 commit message / git log message 等此前漏网路径；明确"所有人读取"路径禁裸 id，必须形如 `{id}（{title}）` 或纯名称替代；自检方法增补（grep `git log --oneline` / TodoWrite 任务文本扫描）；契约 7 "id 密集展示反向豁免条款" 同步覆盖新场景。

## 3. Requirement

- `req-41`（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））

## 4. Scope

### Included

- `.workflow/context/roles/base-role.md` 硬门禁六段落改造：
  - **触发场景**清单新增 5 条 bullet：
    - `TodoWrite / TaskList 任务标题`（如 `Check requirement` → `Check req-41（机器型工件回 flow/requirements）`）；
    - `进度条 / harness status 进度摘要 / 阶段流转动画`；
    - `命令 stdout`（所有 CLI 面向用户输出：`harness next` / `harness status` / `harness validate` / `harness change` 等）；
    - `归档 commit message`（`archive: req-XX-...` / `archive: chg-XX` / `bugfix: ...` 等）；
    - `git log message`（所有 commit 一行化后人读取路径）；
  - **强制规则**明确："所有人读取路径一律 `{id}（{title}）` 或纯名称替代；禁止裸 `req-41` / `chg-05` / `reg-01` 单独出现"；
  - **自检方法**新增两步：
    1. `git log --oneline --all | grep -E "(req|chg|sug|bugfix|reg)-[0-9]+"` 每命中行核对含 `（...）` / `— ...` / title 字段；
    2. CLI 开发 / agent 输出阶段，grep 自身 stdout 片段 + TodoWrite 任务列表扫裸 id；
  - 批量列举子条款同步覆盖新场景（TaskList 多条任务并列 / commit message 列 ≥ 2 个 id 时，每条带 ≤ 15 字描述）；
- `.workflow/context/roles/stage-role.md` 契约 7 "id 密集展示反向豁免条款" 更新：
  - 触发判定 4 扩展为：同一段落 / 表格 / 列表 / TaskList / commit message / CLI stdout 中并列 ≥ 2 个不同 id 即触发反向豁免；
- `.workflow/context/roles/harness-manager.md`（若涉及 CLI 输出 sample 示例）：
  - 示例 stdout 样板更新为带 title / 描述的合规形态（如 `req-41（机器型工件回 flow/requirements）` 而非裸 `req-41`）；
- 可选（default-pick C-A 推荐不落）：
  - CLI 代码层新增 `render_work_item_id` helper 在 stdout 输出路径的覆盖面审计（若 chg-08（硬门禁六扩 TaskList + stdout + 提交信息）发现 CLI 输出还有裸 id 点，追加一条 TODO 给后续 req 处理，不在本 chg 展开）；
- scaffold_v2 mirror 同步：
  - base-role.md / stage-role.md / harness-manager.md 三文件；
- 涉及文件：
  - live：`.workflow/context/roles/base-role.md` / `.workflow/context/roles/stage-role.md` / `.workflow/context/roles/harness-manager.md`
  - mirror：scaffold_v2 对应路径三文件

### Excluded

- **不改** `.workflow/flow/repository-layout.md`（归属 chg-01（repository-layout 契约底座））；
- **不改** CLI 代码（归属 chg-02（CLI 路径迁移 flow layout））；
- **不改** `validate_human_docs.py`（归属 chg-03（validate_human_docs 重写删四类 brief））；
- **不改** 其他角色文件的业务段（归属 chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止））；
- **不改** done.md 交付总结模板（归属 chg-05（done 交付总结扩效率与成本段））；
- **不改** harness-manager.md §3.6 Step 4 硬门禁或 §3.5.3 召唤词（归属 chg-06（harness-manager Step 4 派发硬门禁））；
- **不追溯**历史 commit message / 历史 TodoWrite 任务文本（只对本 chg 落地之后的新增行为硬门禁生效；legacy 引用豁免，与契约 7 legacy fallback 一致）；
- **不**在本 chg 落地 CLI 代码层的 render_work_item_id 审计 / 重构（仅在 Included 标记为 optional TODO）。

## 5. Acceptance

- Covers requirement.md **AC-14**（契约 7 + 硬门禁六 + 批量列举子条款自证，文字扩展部分）：
  - `grep -q "TodoWrite\|TaskList" .workflow/context/roles/base-role.md` 命中 ≥ 1 次（触发场景清单扩展）；
  - `grep -q "进度条\|进度摘要\|stdout" .workflow/context/roles/base-role.md` 命中 ≥ 1 次；
  - `grep -q "commit message\|git log" .workflow/context/roles/base-role.md` 命中 ≥ 1 次；
  - `grep -q "所有人读取" .workflow/context/roles/base-role.md` 命中 ≥ 1 次（关键强制语义）；
  - 硬门禁六段 "批量列举子条款" 更新后含 TaskList / commit message 等新场景声明；
- Covers requirement.md **AC-15**（scaffold_v2 mirror 同步）：
  - `diff -q .workflow/context/roles/base-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md` 无输出；
  - `diff -q .workflow/context/roles/stage-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md` 无输出；
- Covers requirement.md **AC-06**（回归不破坏）：
  - `pytest tests/` 全量绿；
  - 既有硬门禁六 / 七 / 契约 7 其他段落文字不变（diff 仅限新增 / 扩展区域）。

## 6. Risks

- **风险 1：base-role.md 硬门禁六段落扩展后行数增长，与现有硬门禁七 / 经验沉淀等段落排版冲突**。缓解：executing 先读硬门禁六段全文，按"在现有段落内加 bullet / 加自检子句"方式扩展，不新起独立段；扩展后 `wc -l` 对比前后行数，确认增量合理（≤ +30 行）。
- **风险 2：新规则与既有硬门禁六 / 契约 7 文字冲突**。缓解：扩展措辞明确"并列扩展"而非"替代"；保留既有触发场景（表格列 / 行内文字等）不动，只追加新场景 bullet；自检方法也是追加不替代；人工 diff review 段落结构。
- **风险 3：CLI stdout 现有 `render_work_item_id` helper 覆盖率不足 → 新硬门禁落地后实际 CLI 输出仍有裸 id**。缓解：本 chg 只扩文字契约，不展开 CLI 代码审计；遗留问题捕获到 session-memory "待处理捕获问题"，由后续 req / sug 独立处理；不阻塞本 req 落地。
- **风险 4：TodoWrite 工具本身由 LLM runtime 控制，agent 自律遵守，pytest 无法强校验**。缓解：硬门禁六本质是规约而非 CLI 代码约束；契约测试覆盖"文字契约存在"（grep 关键词命中），实际遵守靠主 agent / subagent 自律 + done 阶段六层回顾 grep 自检；与已有硬门禁六执行机制一致。
- **风险 5：历史 commit message 的裸 id 被误当作违规**。缓解：明文排除"不追溯历史"；自检方法 `git log --oneline` 限定本 req 落地后的 commit（`git log --since=<date>`）或仅对新建 commit 硬门禁；legacy 引用豁免与契约 7 保持一致。
