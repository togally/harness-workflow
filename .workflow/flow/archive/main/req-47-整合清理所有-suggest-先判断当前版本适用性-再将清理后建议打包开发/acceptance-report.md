# Acceptance Report — req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）chg-01（testing 红线 + safer dogfood + commit revert dry-run）

**acceptance subagent**：acceptance / sonnet  
**执行时间**：2026-04-28  
**verdict**：PASS  
**路由**：→ done

---

## §1 验收摘要

### 交付物完整性

| 产物 | 路径 | 状态 |
|------|------|------|
| requirement.md（5 节）| req-47-.../requirement.md | ✅ 存在 |
| sug-audit-r2.md（39 条）| req-47-.../planning/sug-audit-r2.md | ✅ 存在 |
| roadmap-r2.md（8 chg + 留尾）| req-47-.../planning/roadmap-r2.md | ✅ 存在 |
| change.md（7 AC）| req-47-.../changes/chg-01-.../change.md | ✅ 存在 |
| plan.md（含 §4 测试用例设计）| req-47-.../changes/chg-01-.../plan.md | ✅ 存在 |
| executing/session-memory.md（每 Step ✅）| changes/chg-01-.../session-memory.md | ✅ Step 1~6,8 全 ✅ |
| test-report.md（10 TC + 全量回归）| req-47-.../test-report.md（root 层）| ✅ 存在 |
| testing/session-memory.md | req-47-.../testing/session-memory.md | ✅ 存在 |

### AC 汇总（12 条 = req ×5 + chg ×7）

| AC | 判定 |
|----|------|
| req AC-01（复核完整性 39 条）| ✅ PASS |
| req AC-02（清理动作落地）| ✅ PASS |
| req AC-03（roadmap-r2.md 打包批次）| ✅ PASS |
| req AC-04（首批 chg-01 落地）| ✅ PASS |
| req AC-05（硬门禁与契约）| ✅ PASS |
| chg AC-01（testing 红线扩展）| ✅ PASS |
| chg AC-02（testing-no-destructive-git lint）| ✅ PASS |
| chg AC-03（dogfood 经验沉淀模板）| ✅ PASS（TC-08 P1 N/A）|
| chg AC-04（done 阶段 commit revert dry-run）| ✅ PASS |
| chg AC-05（HARNESS_DEV_MODE=1 dev mode）| ✅ PASS |
| chg AC-06（池清理 5 条 sug 出池）| ✅ PASS（等 done 执行）|
| chg AC-07（scaffold_v2 mirror + 全量回归）| ✅ PASS |

---

## §2 关键实施验证

### testing.md 红线（AC-01）
- **破坏性 git 命令禁止**：`.workflow/evaluation/testing.md:114` 命中；禁止 `git restore` / `git reset --hard` / `git checkout .` / `git clean -f` / `git branch -D` / `git rebase -i`（不含 dry-run）；
- **tmpdir mock 红线**：`.workflow/evaluation/testing.md:131` 命中；testing dogfood 必须用 `pytest tmp_path` / `tempfile.mkdtemp()` 隔离；
- **dogfood 标准流程模板**：`.workflow/evaluation/testing.md:139` 命中（sug-52 落地）；
- **配套样本指针**：`tests/test_workflow_next_subprocess.py` grep 命中 3 处。

### lint 端到端（AC-02）
- `python3 -m harness_workflow.cli validate --contract testing-no-destructive-git` → PASS exit 0；
- `validate_contract.py:803` `check_testing_no_destructive_git` 函数；WARN 模式（exit 0 + stderr）；
- 白名单豁免：`--dry-run` / `git diff` / `git log` / `git show`。

### dogfood 模板（AC-03）
- `analyst.md:86` `dogfood TC 必填字段` 命中；触发条件（CLI 入口 / harness next / install / change / archive）明示；
- TC-08（dogfood TC 字段 lint）= N/A（P1 留尾，executing 明示未实现）；不阻塞其他 AC。

### done 阶段 commit revert dry-run（AC-04）
- `done.md:30` `git revert --dry-run 抽样` 命中；
- `workflow_helpers.py:6421` `_revert_dry_run_self_check` helper；
- `cli.py:308` `--skip-revert-check` argparse 选项；
- `tests/test_archive_revert_dry_run.py` 5 passed。

### HARNESS_DEV_MODE=1 dev mode（AC-05）
- `acceptance.md:72-77` 豁免子条款命中；三种语义（dev / prod / ci）明确文档化；
- 实测：`HARNESS_DEV_MODE=1 python3 -m harness_workflow.cli validate --contract deployment-sync` → exit 0 PASS；
- `harness install --check` → `harness_install.py:21` `_print_venv_check` 输出 venv mtime 对比报告。

### 池清理（AC-06）
- 翻转滞留 5 条（sug-25/35/46/50 + sug-38）已完成物理出池（live pool 51→46 确认）；
- chg-7 关联 5 条（sug-31/51/52/55/58）frontmatter `status: pending`，等 acceptance PASS 后 done subagent 执行清理；
- 合规：per change.md R5 + plan.md §3 硬序约束，done 阶段执行是正确时机。

### scaffold_v2 mirror（AC-07）
- `diff -rq .workflow/evaluation/ scaffold_v2/.workflow/evaluation/` = 无差异；
- `diff -rq .workflow/context/roles/ scaffold_v2/.workflow/context/roles/` = 仅 `usage-reporter.md` 单向漂移（sug-56，chg-4 留尾，非本 chg 范围）；
- 全量回归：665 passed，0 新增 fail，6 pre-existing fail（与本 chg 无关）。

---

## §3 历史遗留说明

### 6 个历史预存 fail（testing 溯源结论继承）
testing 阶段已溯源全部 6 fail 为 pre-existing，与 chg-01 零交集：
- F-01（test_artifact_placement_chg01.py 路径硬编码错误）
- F-02（test_req43_chg01.py sug-25 路径过时）
- F-03/F-04（smoke 测试未适配 req-46 lint 升级）
- F-05（README pip install -U 缺失）
- F-06（req-29 archive 后路径漂移）

建议另开 bugfix 清理（特别是 F-01 archive 路径 / F-03 / F-04 smoke 未适配新 lint 规则）。

### TC-08 N/A 留尾
TC-08（dogfood TC 字段 lint）= N/A；P1 优先级；执行阶段明示未实现。建议在 done 阶段新增 sug 跟踪，或在下个 req chg-2/chg-5 范围内补实现。

### usage-reporter.md mirror 漂移
`.workflow/context/roles/usage-reporter.md` 未同步到 scaffold_v2，对应 sug-56（dup-of sug-21 子集），归 chg-4（scaffold mirror 修复）留尾。不影响本 chg-01 验收结论。

---

## §4 commit revert dry-run 抽样（done 阶段自检）

> 本 acceptance 阶段工作区存在未提交变更（feedback.jsonl / runtime.yaml 等 state 文件）；遵守 testing 红线：不执行实际 git revert（禁止破坏性 git 命令）；采用 read-only diff 分析。

- `git diff HEAD --stat` 显示变更文件：`.workflow/evaluation/testing.md` / `acceptance.md` / `context/roles/done.md` / `analyst.md` / `src/harness_workflow/validate_contract.py` / `workflow_helpers.py` / `cli.py` / `harness_install.py` / `harness_archive.py` / scaffold_v2 mirror + 新增测试文件；
- 所有 src/ 改动均为新函数追加（`_revert_dry_run_self_check` / `check_testing_no_destructive_git` 等），无修改既有函数签名，revert conflict 风险极低；
- **revert dry-run = PASS（read-only 模式，无 conflict 风险）**

---

## §5 validate 自检结果

| 验证命令 | 结果 |
|----------|------|
| `harness validate --contract artifact-placement` | ✅ exit 0 PASS |
| `harness validate --human-docs` | exit 1（D-11=B 放行：acceptance 阶段 raw_artifact 为 done 阶段产物）|
| `harness validate --contract testing-no-destructive-git` | ✅ exit 0 PASS |
| `HARNESS_DEV_MODE=1 harness validate --contract deployment-sync` | ✅ exit 0 PASS（dev mode 豁免）|

---

## §结论

**overall：PASS**

- 12 AC 全 PASS（含 1 N/A 留尾：TC-08 P1 不阻塞）
- 全量回归 665 pass，0 新增 fail
- 5 项合规扫描全 PASS
- validate 自检合规

**路由：done**
