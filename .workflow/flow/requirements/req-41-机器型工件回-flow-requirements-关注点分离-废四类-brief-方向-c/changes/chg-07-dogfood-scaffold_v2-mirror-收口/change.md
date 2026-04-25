# Change

## 1. Title

dogfood 活证 + scaffold_v2 mirror + 收口

## 2. Goal

- 本 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief）自身落地 dogfood 活证：机器型工件回搬到 `.workflow/flow/requirements/req-41-{slug}/`、artifacts 侧只留 raw `requirement.md` 副本 + `交付总结.md`（无四类 brief）、usage-log.yaml 存在 ≥ 1 条真实 entry、交付总结 §效率与成本段从真实 usage-log 聚合、scaffold_v2 mirror diff = 0；跑 `harness validate --human-docs req-41` exit 0 + `pytest tests/` 全量绿；契约 7 + 硬门禁六 + 批量列举子条款 grep 自检命中行全合规。

## 3. Requirement

- `req-41`（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））

## 4. Scope

### Included

- **dogfood 搬家**（req-41 seed 阶段落在 state/ 的工件，由本 chg 搬到 flow/）：
  - 源：`.workflow/state/requirements/req-41/requirement.md`；
  - 源：`.workflow/state/sessions/req-41/session-memory.md` + `.workflow/state/sessions/req-41/chg-01..chg-08/{change.md, plan.md, session-memory.md}` + 可能的 `task-context/`；
  - 目标：`.workflow/flow/requirements/req-41-机器型工件回-flow-requirements-关注点分离-废四类-brief-方向-c/requirement.md` + `changes/chg-01..chg-08/{...}` + `session-memory.md`；
  - 用 `git mv` 保 history；
  - req yaml（`stage_timestamps`）如果在 state/ 也搬到 flow/ 对应位；
- **artifacts 侧清理四类 brief 空壳**：
  - `artifacts/main/requirements/req-41-{slug}/` 下：
    - 保留：raw `requirement.md` 副本 + `交付总结.md`（done 阶段产出）；
    - `git rm` 空壳：`chg-01-变更简报.md` ~ `chg-08-变更简报.md`（共 8 个 CLI 自动生成残留）；
    - 若存在 `需求摘要.md` / `实施说明.md` / `回归简报.md` 空壳也一并清；
- **usage-log.yaml dogfood 活证**：
  - 验证 `.workflow/flow/requirements/req-41-{slug}/usage-log.yaml` 存在 ≥ 1 条真实 entry（从 chg-06（harness-manager Step 4 派发硬门禁）硬门禁落地后本 req 执行过程中采集的真实数据）；
  - 若 dogfood 验证时 usage-log 为空（early adoption 可能缺历史），由 done 阶段主 agent 补充 ≥ 1 条派发后写入（至少 dogfood 自身 chg-07（dogfood 活证 + scaffold_v2 mirror 收口）的执行派发要写入）；
- **交付总结 §效率与成本段从真实数据聚合**（done 阶段产出 `交付总结.md`）：
  - 读取 usage-log.yaml + req yaml `stage_timestamps`；
  - 按 chg-05（done 交付总结扩效率与成本段）模板填四子字段；
  - 断言四子字段有真实数值（无 `⚠️ 无数据`）；
- **scaffold_v2 mirror 收口**：
  - `diff -rq` 全仓库 mirror 对比 live：`.workflow/context/` / `.workflow/flow/` 对应 scaffold_v2 子树零输出（除 runtime-only 豁免文件）；
  - 重点复查：repository-layout.md / 六角色文件 / stage-role.md / base-role.md / harness-manager.md / role-model-map.yaml / index.md；
  - 跑 `pytest tests/test_scaffold_v2_mirror.py` 或等价契约测试；
- **契约 7 + 硬门禁六 + 批量列举子条款 grep 自检**：
  - `grep -nE "(req|chg|sug|bugfix|reg)-[0-9]+" .workflow/flow/requirements/req-41-{slug}/ -r --include=*.md` 每命中行核对含 `（...）` 或 `— ...` 简短描述；
  - 批量列举场景（如 chg DAG 表）每条带描述，无 `chg-01/02/03` 裸数字扫射；
- **验证命令跑绿**：
  - `harness validate --human-docs req-41` exit 0；
  - `pytest tests/` 全量绿；
  - `harness status` 显示 req-41 状态正常（CLI 能识别新 flow/ 位）；
- **dogfood 收口报告**（写 session-memory）：列每 AC 通过情况 + 缺失项（若有）。

### Excluded

- **不改** 其他前置 chg 已落地产物（chg-01（repository-layout 契约底座）~ chg-06（harness-manager Step 4 派发硬门禁）+ chg-08（硬门禁六扩 TaskList + stdout + 提交信息）成果只做验证，不改动）；
- **不动** 历史归档 / legacy 子树 (`.workflow/flow/archive/` / `artifacts/main/archive/` / req-02（workflow 分包结构修复）~ req-40（阶段合并与用户介入窄化）artifacts 存量)；
- **不跑** `harness archive req-41`（归档由 done 阶段之后人工触发，本 chg 只负责 dogfood 活证不收工归档）；
- **不重新定义** 任何契约（仅验证前置 chg 落地情况）。

## 5. Acceptance

- Covers requirement.md **AC-13 (a)**（机器型工件齐全）：
  - `test -f .workflow/flow/requirements/req-41-{slug}/requirement.md`；
  - `test -d .workflow/flow/requirements/req-41-{slug}/changes/chg-01-.../` 且含 `change.md` + `plan.md` + `session-memory.md`；
  - chg-01~chg-08 八个目录齐全；
  - 若有 regression，`.workflow/flow/requirements/req-41-{slug}/regressions/` 子目录齐全。
- Covers requirement.md **AC-13 (b)**（artifacts 仅 raw + 交付总结）：
  - `ls artifacts/main/requirements/req-41-{slug}/` 输出只含 `requirement.md` + `交付总结.md`（+ 可选 `决策汇总.md`）；
  - `find artifacts/main/requirements/req-41-{slug}/ -name "*-变更简报.md" -o -name "*-实施说明.md" -o -name "需求摘要.md" -o -name "*-回归简报.md"` 零输出。
- Covers requirement.md **AC-13 (c)**（usage-log ≥ 1 真实 entry）：
  - `test -f .workflow/flow/requirements/req-41-{slug}/usage-log.yaml`；
  - `grep -c "^- role:" .workflow/flow/requirements/req-41-{slug}/usage-log.yaml` ≥ 1（或对应 yaml 结构 entry 计数 ≥ 1）；
  - 至少 1 条 entry 的 `input_tokens` / `output_tokens` / `total_tokens` 字段不为 0 或 null（排除纯 stub）。
- Covers requirement.md **AC-13 (d)**（§效率与成本从真实 usage-log 聚合）：
  - `grep -q "## 效率与成本" artifacts/main/requirements/req-41-{slug}/交付总结.md`；
  - `grep -q "总耗时" artifacts/main/requirements/req-41-{slug}/交付总结.md` + 总耗时值为真实秒数（非占位 `{duration_s}`）；
  - `grep -q "⚠️ 无数据" artifacts/main/requirements/req-41-{slug}/交付总结.md` 命中数 = 0（有真实数据）；
- Covers requirement.md **AC-14**（契约 7 + 硬门禁六 + 批量列举子条款自证）：
  - `grep -nE "(req|chg|sug|bugfix|reg)-[0-9]+" .workflow/flow/requirements/req-41-{slug}/ -r --include=*.md` 每命中行紧随含 `（...）` 或 `— ...` 或已有 title 字段；
  - 裸 id 人眼核对数 = 0；
  - DAG 表 / 批量列举场景无 `chg-01/02/03` 形态。
- Covers requirement.md **AC-15**（scaffold_v2 mirror 同步，最终收口）：
  - `pytest tests/test_scaffold_v2_mirror.py` PASS（或等价契约测试）；
  - `diff -rq .workflow/context/ src/harness_workflow/assets/scaffold_v2/.workflow/context/` 无输出（除 runtime-only 豁免）；
  - `diff -q .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` 无输出。
- Covers requirement.md **AC-16**（统一精简汇报模板沿用）：
  - `grep -c "本阶段已结束" .workflow/flow/requirements/req-41-{slug}/ -r --include=session-memory.md` ≥ 4；
- Covers requirement.md **AC-06 / 全量回归**：
  - `harness validate --human-docs req-41` exit 0；
  - `pytest tests/` 全量绿。

## 6. Risks

- **风险 1：`git mv` 搬运 state/→flow/ 前主 agent 还在 state/ 持续读写当前 session-memory，导致搬运瞬间冲突**。缓解：dogfood 搬运在 done 阶段**之前**、其他 chg 全部完成**之后**执行；搬运前先 `git status` 确认工作区干净；搬运后 session-memory 引用改 flow/ 新位；搬运窗口不超 1 分钟。
- **风险 2：artifacts 侧四类 brief 空壳 `git rm` 时 CI 或 reviewer 工具（若存在）将其视为退化风险报警**。缓解：rm 时 commit message 引用 req-41（机器型工件回 flow）/ chg-07（dogfood 活证 + scaffold_v2 mirror 收口），附 "按 req-41 方向 C 废止四类 brief" 溯源；grep `validate_human_docs` 扫描已由 chg-03（validate_human_docs 重写删四类 brief）精简跳过，无报警。
- **风险 3：usage-log.yaml early adoption 为空 → AC-13 (c) 失败**。缓解：dogfood 验证前由主 agent 手动派发 1-2 次子 agent（如"跑 pytest 确认绿" → `record_subagent_usage` 真实写入）；或 chg-07 执行本身的派发（executing → testing 过渡）就会触发。
- **风险 4：`diff -rq` mirror 验证误报 runtime-only 文件**。缓解：基于既有 `test_package_data_completeness.py` 或 `test_scaffold_v2_mirror.py` 的豁免白名单（`state/sessions/` / `state/feedback/` / `flow/archive/` / `__pycache__`）跑；仅比对 context/ 与 flow/（非 state/）子树。
- **风险 5：契约 7 批量列举自检命中历史遗留裸 id**。缓解：本 chg grep 范围严格限定 `.workflow/flow/requirements/req-41-{slug}/`（活证范围），不扫描历史归档或其他 req 子树；命中违规即当场修正（改本 req 文档，不追溯历史）。
