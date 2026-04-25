# Change Plan — chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止）

## 1. Development Steps

### Step 1: 盘点六角色文件 `→ artifacts/` 命中点 + 四类 brief 模板段

- 跑 `grep -nH "→ artifacts/" .workflow/context/roles/analyst.md .workflow/context/roles/executing.md .workflow/context/roles/regression.md .workflow/context/roles/done.md .workflow/context/roles/testing.md .workflow/context/roles/acceptance.md` 收集所有命中行；
- 跑 `grep -nH -E "需求摘要|变更简报|实施说明|回归简报" .workflow/context/roles/{analyst,executing,regression}.md` 定位 brief 模板段首尾；
- 产出改造清单到 chg-04 session-memory.md（每文件每命中行 TODO）。

### Step 2: 改 analyst.md

- 去路径化：
  - Part A Step A3 `产出对人文档 需求摘要.md → artifacts/{branch}/...` → 删整行；Part A 改为"产出 `requirement.md`（落位见 `.workflow/flow/repository-layout.md`）"；
  - Part B Step B3 `产出各 chg 的对人文档 chg-NN-变更简报.md → artifacts/{branch}/...` → 删整行；Part B 改为"产出 `change.md` + `plan.md`（落位见 repository-layout.md）"；
- 删"对人文档产出契约"整节（产出一 + 产出二 两模板）；
- 改为一段引用："本阶段不产出对人 brief（req-41（机器型工件回 flow + 废四类 brief）方向 C 废止）；req 级对人产物由 done 阶段产出 `交付总结.md`"；
- 退出条件清单：删"对人文档 `需求摘要.md` / `chg-NN-变更简报.md` 已产出，字段完整"相关 bullet；保留 `harness validate --human-docs` exit 0；
- `cp .workflow/context/roles/analyst.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md`。

### Step 3: 改 executing.md

- 去路径化 `→ artifacts/` 所有命中行；
- 删"实施说明.md" 模板段；改为引用 "本阶段不产出对人 brief"；
- 退出条件清单删 brief 相关 bullet；
- mirror 同步。

### Step 4: 改 regression.md

- 去路径化 `→ artifacts/` 所有命中行；
- 删"回归简报.md" 模板段；改为引用 "本阶段不产出对人 brief"；
- 退出条件清单删 brief 相关 bullet；
- mirror 同步。

### Step 5: 改 done.md

- 去路径化 `→ artifacts/交付总结.md` → 改为"产出 `交付总结.md`（落位见 repository-layout.md）"；
- 保留交付总结字段模板（§效率与成本段由 chg-05（done 交付总结扩效率与成本段）处理，本 chg 不碰）；
- mirror 同步。

### Step 6: 改 testing.md / acceptance.md

- 仅去残留 `→ artifacts/` 路径（`测试结论.md` / `验收摘要.md` 已由 req-31（角色功能优化整合与交互精简）废止）；
- 确认两文件内无遗漏 brief 模板段；
- mirror 同步。

### Step 7: 改 stage-role.md 契约 3 / 4

- 契约 3 表格：删 `requirement_review | 需求摘要.md | req | 需求分析师` / `planning | 变更简报.md | change | 架构师` / `executing | 实施说明.md | change | 开发者` / `regression | 回归简报.md | regression | 诊断师` 四行；保留 `done | 交付总结.md | req | 主 agent（done）` 行 + `决策汇总.md` ff 行；
- 契约 4 硬门禁 bullet 精简：加"req-id ≥ 41 起，req 级对人文档仅为 `交付总结.md`（done 阶段产出）+ raw `requirement.md` 副本；其他 stage 不产出对人 brief"分水岭声明；
- mirror 同步 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md`。

### Step 8: usage-reporter 废止

- `git rm .workflow/context/roles/usage-reporter.md`；
- `git rm src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md`（若存在）；
- 检查 `test -f .workflow/context/experience/roles/usage-reporter.md`；若存在，`git rm`；同步 mirror；
- 编辑 `.workflow/context/role-model-map.yaml` 删 `usage-reporter: "sonnet"` 行；mirror 同步；
- 编辑 `.workflow/context/index.md` 角色索引表删 usage-reporter 行；mirror 同步；
- grep 全仓库 `grep -r "usage-reporter" .workflow/context/ src/harness_workflow/` 确认命中点已清零（archive/ 豁免）。

### Step 9: 自检 + 交接

- `grep -l "→ artifacts/" .workflow/context/roles/{analyst,executing,regression,done,testing,acceptance}.md` 命中数 = 0；
- `grep -cE "需求摘要|变更简报|实施说明|回归简报" .workflow/context/roles/{analyst,executing,regression}.md .workflow/context/roles/stage-role.md` 命中数 = 0；
- `diff -rq .workflow/context/roles/ src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` 无输出；
- `diff -q .workflow/context/role-model-map.yaml src/harness_workflow/assets/scaffold_v2/.workflow/context/role-model-map.yaml` 无输出；
- `test ! -f .workflow/context/roles/usage-reporter.md`；
- `pytest tests/` 全量绿；
- 更新 chg-04 session-memory.md。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `[ $(grep -l "→ artifacts/" .workflow/context/roles/{analyst,executing,regression,done,testing,acceptance}.md 2>/dev/null | wc -l) -eq 0 ]`
- `[ $(grep -cE "需求摘要|变更简报|实施说明|回归简报" .workflow/context/roles/analyst.md .workflow/context/roles/executing.md .workflow/context/roles/regression.md .workflow/context/roles/stage-role.md) -eq 0 ]`
- `test ! -f .workflow/context/roles/usage-reporter.md`
- `test ! -f src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md`
- `! grep -q "usage-reporter" .workflow/context/role-model-map.yaml`
- `! grep -q "usage-reporter" src/harness_workflow/assets/scaffold_v2/.workflow/context/role-model-map.yaml`
- `diff -rq .workflow/context/roles/ src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/`（零输出）
- `pytest tests/`（全量绿）

### 2.2 Manual smoke / integration verification

- 人工读 analyst.md / executing.md / regression.md 三文件，确认"产出 `{doc-type}`（落位见 repository-layout.md）"引用契约一致；
- 人工读 done.md，确认交付总结引用改为契约引用（具体字段模板由 chg-05 处理）；
- 人工读 stage-role.md 契约 3 表格，确认只剩 done + 决策汇总两行（或 done 单行）；
- 跑 `harness install` 在 tempdir 验证 scaffold_v2 mirror 不再含 usage-reporter.md。

### 2.3 AC Mapping

- AC-02（角色去路径化） → Step 2-6 + 2.1 grep；
- AC-07（废 brief 角色模板清理） → Step 2-7 + 2.1 grep；
- AC-12（usage-reporter 废止） → Step 8 + 2.1 test ! -f + grep；
- AC-15（mirror diff 归零） → 每步 mirror 同步 + 2.1 `diff -rq`；
- AC-06（回归不破坏） → Step 9 pytest 全量绿。

## 3. Dependencies & Execution Order

- **前置依赖**：chg-01（repository-layout 契约底座）必须先落地（"落位见 repository-layout.md" 引用靶点）；
- **可并行邻居**：chg-02（CLI 路径迁移 flow layout）/ chg-03（validate_human_docs 重写删四类 brief）/ chg-08（硬门禁六扩 TaskList + stdout + 提交信息）共骨架后并行；
- **后置依赖**：chg-05（done 交付总结扩效率与成本段）/ chg-06（harness-manager Step 4 派发硬门禁）都依赖本 chg 的 usage-reporter 废止前提；
- **本 chg 内部顺序**：Step 1 盘点 → Step 2~6 六文件去路径化（建议串行 avoid cross-file 漏改）→ Step 7 stage-role.md → Step 8 usage-reporter 废止 → Step 9 自检；
- **不并行**：单一 subagent 单通道执行（文件改动有耦合）。
