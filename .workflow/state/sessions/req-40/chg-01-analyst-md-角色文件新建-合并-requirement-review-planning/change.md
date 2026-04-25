# Change

## 1. Title

analyst.md 角色文件新建（合并 requirement-review + planning）

## 2. Goal

- 新建 `.workflow/context/roles/analyst.md`，把原 `requirement-review.md`（需求分析师）+ `planning.md`（架构师）的硬门禁 / SOP / 职责 / 禁止条款 / 退出条件 / 产出清单合并为单一角色文件，作为 req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））方向 C 的角色层物理合并载体。

## 3. Requirement

- `req-40`（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））

## 4. Scope

### Included

- 新建 `.workflow/context/roles/analyst.md`（≤ 200 行），继承 `base-role.md` + `stage-role.md`；
- 合并原 `requirement-review.md` + `planning.md` 的**硬门禁**（含 `harness validate --human-docs` 自检硬门禁、对人文档产出硬门禁）、**SOP 步骤**（Step 0~5 融合：需求澄清 → 变更拆分 → 执行计划 → 产出检查 → 交接）、**允许 / 禁止行为**、**退出条件**、**对人文档输出契约**（同时产出 `需求摘要.md` + 各 chg 的 `chg-NN-变更简报.md`）；
- 明示"两 stage（requirement_review + planning）由同一 analyst 角色执行"的调用语义（保留"同一会话续跑"为默认、"两次派发"为 fallback）；
- 显式引用 base-role 硬门禁六（req-35（base-role 加硬门禁：对人汇报 ID 必带简短描述（契约 7 扩展））/ chg-01）+ 硬门禁七（req-37（阶段结束汇报简化：周转时不给选项，只停下+报本阶段结束+报状态）/ chg-01）+ req-38（api-document-upload 工具闭环）/ chg-06（硬门禁六 + 契约 7 批量列举子条款补丁）批量列举子条款；
- 同步 mirror：`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md` 与 live 文件字节一致；
- 涉及文件路径：
  - live：`.workflow/context/roles/analyst.md`（新建）
  - mirror：`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md`（新建）

### Excluded

- **不删除** `requirement-review.md` / `planning.md`（两文件仍保留作 legacy 角色文件；index.md / role-model-map.yaml 层面合并由 chg-02 处理，harness-manager 派发目标路由由 chg-03 处理）；
- **不改** `harness-manager.md` / `technical-director.md` / `stage-role.md` 内容（归属 chg-03）；
- **不改** CLI 源码；
- **不跑** dogfood 验证（归属 chg-05）；
- **不写** pytest（归属 chg-04）；
- **不写** 专业化反馈捕捉模板（归属 chg-06）。

## 5. Acceptance

- Covers requirement.md **AC-1**（analyst.md 存在 + 职责完整）：
  - `ls .workflow/context/roles/analyst.md` 存在；
  - `grep -c "^## " .workflow/context/roles/analyst.md` ≥ 6（覆盖角色定义 / 硬门禁 / SOP / 退出条件 / 产出 / 禁止 / 流转至少 6 节）；
  - 文件头部声明继承 `base-role.md` + `stage-role.md`；
  - grep 命中 req-35（硬门禁六）/ req-37（硬门禁七）/ req-38（批量列举子条款）三处引用。
- Covers requirement.md **AC-10**（契约 7 + 硬门禁六自证）起点：
  - analyst.md 内所有工作项 id 首次引用形如 `{id}（{title}）` 或 ≤ 15 字描述；
  - grep 扫描 `analyst.md` 命中裸 id 违规数 = 0。
- Covers requirement.md **AC-9**（scaffold_v2 mirror 跨文件 diff 归零）起点：
  - `diff -rq .workflow/context/roles/analyst.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md` 无输出。

## 6. Risks

- **风险 1：两角色合并导致行数超限 200 行**。缓解：优先合并交集（相同硬门禁 / 相同基础 SOP 步骤）；差异部分按"需求澄清 / 变更拆分"双小节拆行，不用整段重复；保留原角色的禁止条款并集；若仍超限按 default-pick F-1 = 分 SOP 双小节（Part A / Part B），而非裁剪内容。
- **风险 2：mirror 同步遗漏导致硬门禁五违反**。缓解：executing 执行步骤强制"live 写完立刻 `cp` 到 mirror"；executing 结束前跑 `diff -rq` 自检。
- **风险 3：合并后原角色文件是否保留引发 legacy 引用链断裂**。缓解：default-pick P-1 = 保留原两文件作 legacy（不删除），index.md / role-model-map 层面做别名合并（chg-02 承接）；避免归档 legacy 需求内的 `context/roles/requirement-review.md` 引用失效。
