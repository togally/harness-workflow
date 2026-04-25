# Change Plan — chg-07（dogfood 活证 + scaffold_v2 mirror + 收口）

## 1. Development Steps

### Step 1: 前置检查 chg-01（repository-layout 契约底座）~ chg-06（harness-manager Step 4 派发硬门禁）+ chg-08（硬门禁六扩 TaskList stdout 提交信息）全部落地

- `git status` 确认工作区干净；
- 跑 `pytest tests/` 全量绿（回归护栏基线）；
- grep 验证 chg-01（repository-layout 契约底座）/ chg-04（角色去路径化 + brief 删除 + usage-reporter 废止）的关键契约文件存在：
  - `test -f .workflow/flow/repository-layout.md`
  - `test ! -f .workflow/flow/artifacts-layout.md`
  - `test ! -f .workflow/context/roles/usage-reporter.md`
  - `grep -q "FLOW_LAYOUT_FROM_REQ_ID = 41" src/harness_workflow/workflow_helpers.py`
  - `grep -q "BRIEF_DEPRECATED_FROM_REQ_ID = 41" src/harness_workflow/validate_human_docs.py`
  - `grep -q "## 效率与成本" .workflow/context/roles/done.md`
  - `grep -q "record_subagent_usage" .workflow/context/roles/harness-manager.md`
- 若任一项缺，ABORT 返回让对应 chg executing 补齐；
- 产出前置验证清单到 chg-07 session-memory.md。

### Step 2: 搬运 state/→flow/ 机器型工件（req-41（机器型工件回 flow/requirements）自身）

- `slug="机器型工件回-flow-requirements-关注点分离-废四类-brief-方向-c"`；
- `mkdir -p .workflow/flow/requirements/req-41-${slug}/changes .workflow/flow/requirements/req-41-${slug}/regressions .workflow/flow/requirements/req-41-${slug}/task-context`；
- `git mv .workflow/state/requirements/req-41/requirement.md .workflow/flow/requirements/req-41-${slug}/requirement.md`；
- `git mv .workflow/state/sessions/req-41/session-memory.md .workflow/flow/requirements/req-41-${slug}/session-memory.md`；
- `git mv .workflow/state/sessions/req-41/chg-01-* .workflow/flow/requirements/req-41-${slug}/changes/chg-01-*`（共 8 个 chg 目录全搬）；
- 若 `.workflow/state/sessions/req-41/regressions/` 或 `task-context/` 有内容，一并 `git mv` 到 flow/ 对应位；
- 若 `.workflow/state/requirements/req-41/` 下还有 req yaml（`stage_timestamps` 之类），`git mv` 到 `.workflow/flow/requirements/req-41-${slug}/req.yaml`；
- 搬运后检查 `.workflow/state/requirements/req-41/` 与 `.workflow/state/sessions/req-41/` 两目录为空，`rmdir` 收尾。

### Step 3: 更新 runtime.yaml 指向新位 + session-memory 路径自引用

- 编辑 `.workflow/state/runtime.yaml`：若 `current_requirement_path` 或类似字段指向 state/ 旧位，改为 `.workflow/flow/requirements/req-41-${slug}/`；若 CLI 已基于 chg-02（CLI 路径迁移 flow layout）自动 resolve，此步骤可跳过（`harness status` 自动正确定位即 PASS）；
- `session-memory.md` 内如有 `.workflow/state/sessions/req-41/...` 硬编码路径，改为 flow/ 新位。

### Step 4: 清理 artifacts 侧四类 brief 空壳

- `cd artifacts/main/requirements/req-41-${slug}/`；
- 列当前内容：`ls -1`（预期含 `requirement.md`（raw 副本）+ `chg-01-变更简报.md` ~ `chg-08-变更简报.md` 8 个空壳 + 可能的 `需求摘要.md` / `实施说明.md` 残留）；
- `git rm chg-0{1..8}-变更简报.md`（或精确列表 `chg-01-变更简报.md` ... `chg-08-变更简报.md`）；
- `git rm` 其他四类 brief 残留（`需求摘要.md` / `*-实施说明.md` / `*-回归简报.md`）若存在；
- **保留**：raw `requirement.md`（或从 `.workflow/flow/requirements/req-41-${slug}/requirement.md` 复制作 artifacts 副本）+ `交付总结.md`（done 阶段产出）；
- 若 `requirement.md` artifacts 副本缺失，从 flow/ 复制过来。

### Step 5: 确认 usage-log.yaml 含 ≥ 1 条真实 entry

- `ls .workflow/flow/requirements/req-41-${slug}/usage-log.yaml` → 若存在，检查 entries 数；
- 若不存在或 entries = 0（early adoption 缺历史）：
  - 主 agent 手动派发 1-2 次子 agent（如 testing：跑 `pytest tests/` 确认绿）；
  - chg-06（harness-manager Step 4 派发硬门禁）硬门禁落地后，每次派发返回自动 `record_subagent_usage` 写入 flow/ 新位 usage-log.yaml；
- `grep -c "^- role:" .workflow/flow/requirements/req-41-${slug}/usage-log.yaml` ≥ 1；
- 断言至少 1 条 entry 的 `input_tokens` 非 0（排除纯 stub）。

### Step 6: done 阶段产出 `交付总结.md` 含 §效率与成本（本 chg 只验证，实际 done 阶段产出）

- 跑 done 聚合 helper（chg-05（done 交付总结扩效率与成本段）实现）或 done subagent 逻辑；
- 读 `.workflow/flow/requirements/req-41-${slug}/usage-log.yaml` + req yaml `stage_timestamps`；
- 产出 `artifacts/main/requirements/req-41-${slug}/交付总结.md` 含 §效率与成本四子字段；
- 断言四子字段有真实数值，无 `⚠️ 无数据` 标记。

### Step 7: scaffold_v2 mirror 全量收口 diff

- `diff -rq .workflow/context/ src/harness_workflow/assets/scaffold_v2/.workflow/context/` 零输出（除 runtime-only 豁免清单）；
- `diff -q .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` 零输出；
- `pytest tests/test_scaffold_v2_mirror.py` PASS（若存在契约测试）；
- `pytest tests/test_package_data_completeness.py` PASS；
- 若 diff 有命中，执行 `cp` 同步 + 重跑 diff。

### Step 8: 契约 7 + 硬门禁六 + 批量列举子条款自检

- `grep -nE "(req|chg|sug|bugfix|reg)-[0-9]+" .workflow/flow/requirements/req-41-${slug}/ -r --include=*.md` 人眼扫每命中行；
- 检查：首次引用是否含 `（title）` / `— 描述`；批量列举场景是否每条带描述；
- 命中违规行即当场 Edit 修正；
- 同样对 `artifacts/main/requirements/req-41-${slug}/交付总结.md` 扫一遍。

### Step 9: 最终验证命令全绿

- `harness validate --human-docs req-41` → 预期 exit 0，输出只列 `requirement.md` + `交付总结.md` 两条 ok；
- `pytest tests/` → 全量绿；
- `harness status` → 显示 req-41 状态正常；
- `harness status --lint` 如有 lint 选项，也跑一遍。

### Step 10: 产出 dogfood 收口报告 + 交接

- 在 `.workflow/flow/requirements/req-41-${slug}/session-memory.md` 追加 "chg-07 dogfood 收口" 章节，列每 AC 通过情况 + 证据（grep 命令输出摘要）；
- 更新 chg-07 自身的 `changes/chg-07-*/session-memory.md` 记录完成步骤；
- 批次汇报遵循 stage-role.md 统一精简汇报模板四字段；
- 汇报末尾含 `**本阶段已结束。**`。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `test -f .workflow/flow/requirements/req-41-*/requirement.md`
- `[ $(ls -1 .workflow/flow/requirements/req-41-*/changes/ | wc -l) -ge 8 ]`（≥ 8 个 chg 子目录）
- `[ ! -d .workflow/state/requirements/req-41 ]`
- `[ ! -d .workflow/state/sessions/req-41 ]`
- `ls -1 artifacts/main/requirements/req-41-*/` 输出只含 `requirement.md` + `交付总结.md`（+ 可选 `决策汇总.md`）
- `find artifacts/main/requirements/req-41-*/ -name '*-变更简报.md' -o -name '*-实施说明.md' -o -name '需求摘要.md' -o -name '*-回归简报.md'` 零输出
- `test -f .workflow/flow/requirements/req-41-*/usage-log.yaml`
- `[ $(grep -c "^- role:" .workflow/flow/requirements/req-41-*/usage-log.yaml) -ge 1 ]`
- `grep -q "## 效率与成本" artifacts/main/requirements/req-41-*/交付总结.md`
- `! grep -q "⚠️ 无数据" artifacts/main/requirements/req-41-*/交付总结.md`
- `diff -rq .workflow/context/ src/harness_workflow/assets/scaffold_v2/.workflow/context/` 零输出
- `diff -q .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` 零输出
- `pytest tests/test_scaffold_v2_mirror.py`（若存在）PASS
- `pytest tests/test_package_data_completeness.py` PASS
- `harness validate --human-docs req-41` exit 0
- `pytest tests/` 全量绿
- `[ $(grep -rc "本阶段已结束" .workflow/flow/requirements/req-41-*/) -ge 4 ]`

### 2.2 Manual smoke / integration verification

- 人工 `ls -R .workflow/flow/requirements/req-41-*/` 肉眼核对目录结构（requirement.md / changes/chg-01..chg-08/{change.md,plan.md,session-memory.md} / session-memory.md / usage-log.yaml 齐全）；
- 人工 `cat artifacts/main/requirements/req-41-*/交付总结.md` 读 §效率与成本段，核对总耗时 / 总 token / 各阶段耗时 / 各阶段 token 四子字段有真实数值；
- 人工跑 `grep -nE "(req|chg|sug|bugfix|reg)-[0-9]+" .workflow/flow/requirements/req-41-*/ -r --include=*.md | head -40` 抽样核对命中行带描述；
- 人工跑 `harness status` 确认 CLI 能从 flow/ 新位 resolve req-41；
- 人工跑 `git log --follow .workflow/flow/requirements/req-41-*/requirement.md` 确认 history 贯通到 state/ 旧位（git mv 未丢 history）。

### 2.3 AC Mapping

- AC-13 (a)（机器型齐全） → Step 2 + 2.1 test -d/-f；
- AC-13 (b)（artifacts 仅 raw + 交付总结） → Step 4 + 2.1 find；
- AC-13 (c)（usage-log ≥ 1 真实 entry） → Step 5 + 2.1 grep；
- AC-13 (d)（§效率与成本真实聚合） → Step 6 + 2.1 grep "⚠️ 无数据" = 0；
- AC-14（契约 7 + 硬门禁六 + 批量列举） → Step 8 + 2.2 人眼扫；
- AC-15（mirror diff 全量归零） → Step 7 + 2.1 diff；
- AC-16（统一精简汇报模板） → Step 10 + 2.1 `本阶段已结束` 命中 ≥ 4；
- AC-06（回归不破坏 + validate 绿） → Step 9 + 2.1 pytest + harness validate。

## 3. Dependencies & Execution Order

- **前置依赖**：chg-01（repository-layout 契约底座）/ chg-02（CLI 路径迁移）/ chg-03（validate_human_docs 重写）/ chg-04（角色去路径化 + brief 删除 + usage-reporter 废止）/ chg-05（done 交付总结扩效率与成本段）/ chg-06（harness-manager Step 4 派发硬门禁）/ chg-08（硬门禁六扩 TaskList stdout 提交信息）**全部**完成（DAG 收口点）；
- **后置依赖**：无（本 chg 是 DAG 终点，下一步是 done 阶段 + archive）；
- **本 chg 内部顺序**：Step 1 前置检查 → Step 2 搬家 → Step 3 runtime 更新 → Step 4 artifacts 清理 → Step 5 usage-log 验证 → Step 6 交付总结 → Step 7 mirror → Step 8 契约 7 自检 → Step 9 最终验证 → Step 10 收口；严格串行（每步是下一步的前提）；
- **不并行**：dogfood 本质是端到端自证，单通道执行避免副作用。
