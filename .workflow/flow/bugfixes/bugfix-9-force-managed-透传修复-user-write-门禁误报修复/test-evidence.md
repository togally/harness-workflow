# Test Evidence — bugfix-9（force-managed 透传修复 + user-write 门禁误报修复）

> 本文件由 testing 阶段（testing subagent / sonnet）独立产出，非 executing 自测记录。

**日期**：2026-04-28
**角色**：测试工程师（testing / sonnet）
**模型一致性自检**：当前 model = sonnet，匹配 role-model-map.yaml `testing.model = "sonnet"` ✅

---

## TC 覆盖矩阵

| TC ID | 描述 | 对应 AC | 测试方法 | 结果 |
|-------|------|---------|---------|------|
| TC-A1（正向） | `init_repo(force_managed=True)` 覆盖用户改过的 managed 文件，无 `skipping user-modified` stderr | bugfix.md §Validation Criteria 第1条 | pytest unit（tmpdir） | PASS |
| TC-A1（反向对照） | `init_repo(force_managed=False)` 保留用户改动（对照组） | 同上（反向语义保护） | pytest unit（tmpdir） | PASS |
| TC-A2 | grep `workflow_helpers.py`：`install_repo` 内 `init_repo(` 调用含 `force_managed=force_managed`，无硬编码 `False` | bugfix.md §Validation Criteria 第2条 | pytest 源码静态分析 | PASS |
| TC-B1（unit） | tmpdir user project + `.claude/skills/harness/SKILL.md`（工具产出）→ `check_user_write_protected_zones` exit 0 | bugfix.md §Validation Criteria 第3条 | pytest unit（tmpdir） | PASS |
| TC-B1（subprocess） | CLI 变体：`harness validate --contract user-write-protected-zones --root <tmpdir>` exit 0 | 同上（CLI 入口覆盖） | pytest subprocess | PASS |
| TC-B2（unit） | tmpdir user project + `.workflow/context/roles/my-custom.md`（野文件）→ exit 1，stderr 含 violation + 路径 | bugfix.md §Validation Criteria 第4条 | pytest unit（tmpdir） | PASS |
| TC-B2（subprocess） | CLI 变体：含野文件 user project exit 1 | 同上（CLI 入口覆盖） | pytest subprocess | PASS |

全部 7 条用例 PASS。

---

## Dogfood 验证（4 项）

| # | 场景 | 命令 / 操作 | 预期 | 实测结果 |
|---|------|-----------|------|---------|
| a | 本仓 dev mode：`harness install --check --force-managed` | `python3 -m harness_workflow.cli install --check --force-managed` | stderr 含 `force_managed received: True`；无 `force_managed=False` skip 输出 | PASS — stderr 首行 `[install_repo] force_managed received: True`；grep `force_managed=False` 无结果 |
| b | 本仓 dev mode：`harness validate --contract user-write-protected-zones` | `python3 -m harness_workflow.cli validate --contract user-write-protected-zones` | PASS: user-write-protected-zones；exit 0 | PASS — `PASS: user-write-protected-zones`，exit 0 |
| c | mock user project（tmpdir）+ `.claude/skills/harness/SKILL.md`（工具产出）：validate exit 0 | subprocess，env `HARNESS_DEV_REPO_ROOT=''` | exit 0，stdout `PASS: user-write-protected-zones` | PASS — 269 个 skill 文件不再误报 |
| d | mock user project（同 tmpdir）+ `.workflow/context/roles/my-custom.md`（野文件）：validate exit 1 | subprocess，env `HARNESS_DEV_REPO_ROOT=''` | exit 1，stderr 含 `violation` + `.workflow/context/roles/my-custom.md` | PASS — ABORT 1 violation，路径完全匹配 |

---

## 全量回归结果

- **触发依据**：subagent briefing 显式要求全量回归（`pytest tests/` 0 新增 fail 验证）。
- **执行命令**：`python3 -m pytest tests/ 2>&1 | tail -10`
- **结果**：`13 failed, 695 passed, 40 skipped`（695 + 7 新增 = 702 passed，略有 skip 数差异）
- **0 新增 fail**：全部 13 个 FAIL 为 pre-existing 历史失败。

### 13 个历史 fail 溯源（read-only 核查）

| 测试文件 | 失败用例 | 根因（read-only）|
|---------|---------|----------------|
| `test_artifact_placement_chg01.py` | 6 条（req_review session-memory/sug-audit in flow、planning session-memory/roadmap in flow、sug35 existence、change/plan/session-memory in flow） | req-43（交付总结完善）flat layout 迁移后 artifacts/ 对应路径结构变更，测试用例硬编码旧路径未随之更新 |
| `test_req43_chg01.py` | `Sug25StatusTest::test_sug25_applied` | sug-25 对应 suggest 状态文件路径未按 req-43 新路径更新 |
| `test_smoke_req26.py` | `SmokeE2ETest::test_full_lifecycle_smoke` | req-26 smoke test 依赖历史 archive 结构，req-41/42 重定义后路径不存在 |
| `test_smoke_req28.py` | 2 条（full lifecycle + readme refresh hint） | req-28 smoke 依赖旧 archive layout，已被 req-42 重定义为 non-blocking |
| `test_smoke_req29.py` | `test_human_docs_checklist_for_req29` | req-29 archive 内 changes/ 目录缺失（pre-flat 迁移归档，不含新结构）|

以上 13 条均非 bugfix-9 引入，与 chg-01 / chg-02 无关。

---

## 合规扫描（5 项）

### R1 越界核查

git diff 命中文件：
- `src/harness_workflow/workflow_helpers.py` — chg-01 豁免范围内（bugfix.md §Fix Scope 明示）
- `src/harness_workflow/validate_contract.py` — chg-02 豁免范围内
- `tests/test_bugfix9_force_managed_and_user_write.py` — 对应修复的回归测试，合规

`.workflow/state/` 系列文件（runtime.yaml / platforms.yaml / feedback.jsonl）为工作流状态，非 src 越界。

**结论：R1 = PASS，无越界。**

### revert 抽样

**N/A**（理由：bugfix-9 的 chg-01 / chg-02 实施于 working tree，尚未 commit，无 sha 可 revert；执行 `git revert` 会破坏 working tree 中 src/ 改动，本 stage 硬门禁禁止任何破坏性 git 命令，标 N/A 留痕放行。）

### 契约 7 合规扫描

对 `.workflow/flow/bugfixes/bugfix-9-force-managed-透传修复-user-write-门禁误报修复/` 内 `.md` 文件执行 `grep -rnE "(req|chg|sug|bugfix|reg)-[0-9]+"` 抽样核查：
- `bugfix-8` 出现处均带上下文描述（"bugfix-8 后遗症"、"chg-03 of bugfix-8 暴露"、"chg-04 of bugfix-8 设计缺陷"），符合契约 7 首次出现带 ≤ 15 字描述要求。
- `chg-01` / `chg-02` 均带括号内标题（"init_repo force_managed 透传修复"、"user-write-protected-zones 移除 skill/commands 扫描列表"）。

**结论：契约 7 = PASS。**

### req-29（角色→模型映射）映射回归

`git log -- .workflow/context/role-model-map.yaml` 最新 commit 为 `2557385`（req-43 chore），bugfix-9 周期内无变更。
role-model-map.yaml 中 `testing.model = "sonnet"` 与本 subagent 运行模型一致。

**结论：req-29 = PASS。**

### req-30（用户面 model 透出）回归

`grep "testing / sonnet" .workflow/state/action-log.md` 命中：
- line 83：`AC-1~10 端到端独立验证（testing subagent / sonnet）`
- line 131：`角色：测试工程师（testing / sonnet）`
- line 140：`角色：测试工程师（testing / sonnet）`

自我介绍段包含 `（testing / sonnet）` 标识。

**结论：req-30 = PASS。**

---

## 退出条件验证

| 项 | 命令 | 结果 |
|----|------|------|
| `harness validate --human-docs` | `python3 -m harness_workflow.cli validate --human-docs` | exit 1（4 pending；regression/executing/done/acceptance_done 文档尚未产出，属 D-11=B 留痕放行，testing 阶段正常） |
| `harness validate --contract artifact-placement` | `python3 -m harness_workflow.cli validate --contract artifact-placement` | exit 0 PASS |

---

## 结论

bugfix-9（bugfix-9 = force-managed 透传修复 + user-write 门禁误报修复）两个 chg 全部验证通过：

- **chg-01**（init_repo force_managed 透传修复）：TC-A1/A2 全 PASS，dogfood-a 实证 `--force-managed` 全链路无 `False` 误断。
- **chg-02**（user-write-protected-zones 移除 skill/commands 误报）：TC-B1/B2 全 PASS，dogfood-c/d 实证 skill 工具产出不再误报、真野文件仍被拦截。
- 全量回归：0 新增 fail，13 历史 fail 与 bugfix-9 无关。
- 5 项合规扫描：R1=PASS，revert抽样=N/A（硬门禁豁免），契约7=PASS，req-29=PASS，req-30=PASS。

**测试结论：PASS，ready for acceptance。**
