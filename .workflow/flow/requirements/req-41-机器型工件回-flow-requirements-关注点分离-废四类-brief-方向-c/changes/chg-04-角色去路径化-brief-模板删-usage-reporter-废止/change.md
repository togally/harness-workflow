# Change

## 1. Title

角色去路径化 + brief 模板删 + usage-reporter 废止

## 2. Goal

- 对 `analyst.md` / `executing.md` / `regression.md` / `done.md` / `testing.md` / `acceptance.md` 六个角色文件去除硬编码 `→ artifacts/{branch}/...` 路径段，改为"产出 `{doc-type}`（落位见 `.workflow/flow/repository-layout.md`）"统一引用契约；`analyst.md` / `executing.md` / `regression.md` 删除四类 brief 模板段；`stage-role.md` 契约 3 表格删四行 + 契约 4 硬门禁同步精简；`role-model-map.yaml` 删 `usage-reporter: "sonnet"` 行；`git rm .workflow/context/roles/usage-reporter.md`（含 mirror）+ `.workflow/context/experience/roles/usage-reporter.md`（若存在）。

## 3. Requirement

- `req-41`（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））

## 4. Scope

### Included

- **角色去路径化**（六文件 `→ artifacts/` 命中点全删 / 改）：
  - `.workflow/context/roles/analyst.md`：Part A Step A3 / Part B Step B3 / "对人文档产出契约"段 / 退出条件相关 bullet 的 `→ artifacts/{branch}/...` 全改为"产出 `{doc-type}`（落位见 repository-layout.md）"；
  - `.workflow/context/roles/executing.md`：同上处理；
  - `.workflow/context/roles/regression.md`：同上处理；
  - `.workflow/context/roles/done.md`：同上处理（`交付总结.md` 路径引用改为契约引用，保留文件名）；
  - `.workflow/context/roles/testing.md`：同上处理（`测试结论.md` 已废止，仅去残留路径）；
  - `.workflow/context/roles/acceptance.md`：同上处理（`验收摘要.md` 已废止，仅去残留路径）；
- **删四类 brief 模板段**：
  - `analyst.md` 删 "产出一：需求摘要.md" + "产出二：chg-NN-变更简报.md" 两个模板段；
  - `executing.md` 删 "chg-NN-实施说明.md" 模板段；
  - `regression.md` 删 "reg-NN-回归简报.md" 模板段；
  - 替换为一句"本阶段不产出对人 brief；req 级对人产物见 `done.md` 交付总结"；
- **stage-role.md 契约 3 / 4 精简**：
  - 契约 3 表格删 `requirement_review | 需求摘要.md | req | 需求分析师` / `planning | 变更简报.md | change | 架构师` / `executing | 实施说明.md | change | 开发者` / `regression | 回归简报.md | regression | 诊断师` 四行；
  - 契约 4 硬门禁 bullet "每个 stage 角色的退出条件清单中必须包含一条'对人文档 `{文件名}.md` 已产出且字段完整'" → 改为"req-id ≥ 41 起，req 级对人文档仅为 `交付总结.md`（done 阶段产出）+ raw `requirement.md` 副本；其他 stage 不产出对人 brief"；
- **usage-reporter 废止**：
  - `git rm .workflow/context/roles/usage-reporter.md`；
  - `git rm src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md`（mirror）；
  - `git rm .workflow/context/experience/roles/usage-reporter.md`（若存在，Q-2 捕获）；
  - 同步 mirror `src/harness_workflow/assets/scaffold_v2/.workflow/context/experience/roles/usage-reporter.md`（若存在）；
  - `.workflow/context/role-model-map.yaml` 删 `usage-reporter: "sonnet"` 行；
  - 同步 mirror `src/harness_workflow/assets/scaffold_v2/.workflow/context/role-model-map.yaml` 删同行；
  - `.workflow/context/index.md` 角色索引表删 usage-reporter 行；同步 mirror；
- **scaffold_v2 mirror 同步**：
  - 六角色文件改完每份立即 `cp` 到 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/{role}.md`；
  - `stage-role.md` 同步 mirror；
  - `diff -rq .workflow/context/roles/ src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` 无输出（除归档 / 非 mirror 文件）；

### Excluded

- **不动** `.workflow/flow/repository-layout.md`（归属 chg-01（repository-layout 契约底座），本 chg 依赖其作为权威路径源）；
- **不动** CLI 代码（归属 chg-02（CLI 路径迁移 flow layout））；
- **不动** `validate_human_docs.py`（归属 chg-03（validate_human_docs 重写删四类 brief））；
- **不改** `done.md` "## 效率与成本"段（归属 chg-05（done 交付总结扩效率与成本段））；
- **不改** `harness-manager.md` §3.6 Step 4 硬门禁（归属 chg-06（harness-manager Step 4 派发硬门禁））；
- **不扩** base-role.md 硬门禁六文字覆盖面到 TaskList / stdout / 提交信息（归属 chg-08（硬门禁六扩 TaskList + stdout + 提交信息））；
- **不删除、不迁移**历史存量 brief 文件（artifacts/main/requirements/req-02（workflow 分包结构修复）~ req-40（阶段合并与用户介入窄化）原地保留）。

## 5. Acceptance

- Covers requirement.md **AC-02**（角色去路径化）：
  - `grep -l "→ artifacts/" .workflow/context/roles/analyst.md .workflow/context/roles/executing.md .workflow/context/roles/regression.md .workflow/context/roles/done.md .workflow/context/roles/testing.md .workflow/context/roles/acceptance.md` 命中数 = 0；
  - 六文件 grep `repository-layout.md` 各至少 1 次引用。
- Covers requirement.md **AC-07**（废 brief 白名单 + 角色模板清理）：
  - `grep -E "需求摘要|变更简报|实施说明|回归简报" .workflow/context/roles/analyst.md .workflow/context/roles/executing.md .workflow/context/roles/regression.md .workflow/context/roles/stage-role.md` 命中数 = 0；
  - `stage-role.md` 契约 3 表格仅保留 `done | 交付总结.md | req | 主 agent（done）` 与 `regression | 回归简报.md | ...`（**已删**，修正：仅保留 done 行）+ 可选行如 ff 决策汇总。
- Covers requirement.md **AC-12**（usage-reporter 废止）：
  - `test ! -f .workflow/context/roles/usage-reporter.md`；
  - `test ! -f src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md`；
  - `grep -q "usage-reporter" .workflow/context/role-model-map.yaml` 命中数 = 0；
  - `grep -q "usage-reporter" src/harness_workflow/assets/scaffold_v2/.workflow/context/role-model-map.yaml` 命中数 = 0。
- Covers requirement.md **AC-15**（scaffold_v2 mirror 同步）：
  - `diff -rq .workflow/context/roles/ src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` 无输出；
  - `diff -q .workflow/context/role-model-map.yaml src/harness_workflow/assets/scaffold_v2/.workflow/context/role-model-map.yaml` 无输出；
- Covers requirement.md **AC-06**（回归不破坏）：
  - `pytest tests/` 全量绿（删角色文件后相关 fixture 若有硬编码 usage-reporter 路径，同步清理）。

## 6. Risks

- **风险 1：六角色文件 `→ artifacts/` 命中点分布广，漏改残留造成 AC-02 grep 命中 > 0**。缓解：executing 先 grep 出所有命中行作 TODO 清单，逐行核对改完；每改一份跑独立 grep 复查；全部改完最终 `grep -r "→ artifacts/" .workflow/context/roles/` 收口验证。
- **风险 2：stage-role.md 契约 3 表格删四行后原有引用（done / testing / acceptance 行）错位或段落被误删**。缓解：编辑前读取表格全 diff，精确按行删除；保留 `done | 交付总结.md | req | 主 agent（done）` 行；`regression | 回归简报.md | regression | 诊断师` 按 req-41（机器型工件回 flow + 废四类 brief）Scope 也属四类 brief，**删除**此行；人工 review 表格结构完整。
- **风险 3：`git rm usage-reporter.md` 后 pytest / CI 引用残留导致失败**。缓解：executing 先 grep `usage-reporter` 全仓库（含 tests / docs）确认无硬编码期望路径；mirror 同步时一并删除 scaffold_v2 对应副本；grep `grep -r "usage-reporter" .workflow/ src/ tests/` 命中应仅存在于归档或本 req 的记录中。
- **风险 4：历史归档文档里 usage-reporter 引用（如 req-39（对人文档家族契约化）交付总结）grep 会命中**。缓解：AC-12 grep 范围限定活跃文件（role-model-map.yaml / index.md / roles/），不扫历史归档；archive/ 子树豁免不追溯。
- **风险 5：index.md 删除 usage-reporter 行破坏表格对齐**。缓解：编辑时保留表格格式，测试 `md` 渲染；`cat .workflow/context/index.md | head -50` 确认表结构完整。
