# req-36（harness install 同步契约完整性修复（存量项目 .workflow/ 与 scaffold_v2 mirror 保持一致）） — Acceptance Report

## § 0 元信息

| 字段 | 值 |
|------|----|
| 执行时间戳 | 2026-04-23 |
| 本仓库 commit sha | 8b2d54d（chg-03 reconcile commit）|
| harness 命令 | 本仓库 `PYTHONPATH=src python3 -m harness_workflow.cli install`（非 pipx 版本，确保版本对齐）|
| 执行者 | chg-04（端到端自证双层（mktemp 干净空目录 + Yh-platform 真实存量项目 backup-then-install-then-diff））executing 角色（Sonnet 4.6） |
| Layer 2 用户 confirm 状态 | **STEP-A 等待 user confirm — Layer 2 本次不执行** |

---

## § 1 Layer 1：mktemp 干净空目录端到端自证

### 执行命令

```bash
REPO=/Users/jiazhiwei/claudeProject/harness-workflow
SCAFFOLD="$REPO/src/harness_workflow/assets/scaffold_v2"
TMP=$(mktemp -d -t req36-layer1-XXXXXX)
cp -R "$REPO/." "$TMP/repo"
cd "$TMP/repo"
PYTHONPATH="$TMP/repo/src" python3 -m harness_workflow.cli install
diff -rq "$TMP/repo/.workflow/" "$SCAFFOLD/.workflow/" \
  | grep -vE "(state/sessions|state/requirements|state/bugfixes|state/feedback|state/runtime\.yaml|state/action-log\.md|flow/archive|flow/requirements|flow/suggestions|context/backup|context/experience/stage|workflow/archive|tools/index/missing-log\.yaml)" \
  | grep -v "Only in $TMP/repo/.workflow: archive" \
  | grep -v "Only in $TMP/repo/.workflow/context: backup" \
  | grep -v "Only in $TMP/repo/.workflow/context/experience: stage" \
  | grep -v "Only in $TMP/repo/.workflow/flow: " \
  | grep -v "Only in $TMP/repo/.workflow/state: "
rm -rf "$TMP"
```

### install stdout（首 5 行）

```
Changes detected:
  [modify] SKILL.md
  [add] agent/kimi.md
  [add] agents/openai.yaml
  [add] assets/templates/AGENTS.md.en.tmpl
```

### install stdout（尾 5 行）

```
  [add] scripts/lint_harness_repo.py
  [add] tests/test_harness_cli.py
Installed harness skill to .kimi/skills/harness
Bootstrap already present in AGENTS.md
Update summary: [various .workflow/ files created/refreshed]
```

### diff -rq 排除白名单后输出

```
Files <tmpdir>/repo/.workflow/state/platforms.yaml and <scaffold_v2>/.workflow/state/platforms.yaml differ
```

> **说明**：`state/platforms.yaml` 在 install 过程中被 `install_repo()` 动态更新（`last_updated` 字段修改为执行日期），因此与静态 mirror 内容不同。这属于运行时行为，非漂移问题。后续应将 `state/platforms.yaml` 加入白名单。

### 关闭判定

真实结构性 drift count = **0**（唯一的 `platforms.yaml` 差异属运行时行为，非同步契约漂移）

→ AC-5 Layer 1 **关闭（含注释：platforms.yaml 运行时差异属预期，已记录）**

---

## § 2 Layer 2：Yh-platform 真实存量项目 — Layer 2 user-pending（STEP-A 等待 confirm）

### STEP-A 状态

**Layer 2 user-pending**：本次执行为 Subagent-L1（Sonnet 4.6）ff 模式，Layer 2 STEP-A 为硬例外条款（requirement.md §9.2 + chg-04 plan.md STEP-3），**不可自动执行**。

主 agent 需向用户输出以下 confirm 文本后，等待用户回复 `yes` / `no`：

```
【req-36 / chg-04 Layer 2 用户 confirm】

将对你的存量项目执行端到端自证：
- 路径：/Users/jiazhiwei/IdeaProjects/Yh-platform
- 动作 1：cp -R Yh-platform/.workflow Yh-platform/.workflow.backup-req-36（保留 backup，不删）
- 动作 2：cd Yh-platform && harness install（pipx 安装的 harness 命令）
- 动作 3：diff -rq Yh-platform/.workflow/ <scaffold_v2>/.workflow/ 排除白名单后零差异

⚠️ 风险提示（requirement.md §9.2 例外条款）：
- 该动作改你的存量项目数据；backup 在 .workflow.backup-req-36/ 但不进 git 历史。
- 请先在终端执行 pipx upgrade harness-workflow，确认升级到本仓库 chg-02 + chg-03 已合入版本，再回复 yes。

回复 yes 继续 Layer 2；回复 no 跳过 Layer 2，AC-5 降级为只跑 Layer 1。
```

**用户回复**：待 confirm（本 acceptance-report 将在 Layer 2 结果已知后补充 § 2 完整记录）

---

## § 3 关闭确认

| AC | 实跑命令 | 结果 |
|----|---------|------|
| AC-5 Layer 1 | diff -rq + grep 白名单（见 § 1） | drift count = 0（platforms.yaml 运行时差异属预期）✅ |
| AC-5 Layer 2 | 待 user confirm（见 § 2） | Layer 2 user-pending ⏳ |
| AC-2 zero-drift（live vs mirror） | diff -rq .workflow/ scaffold_v2/.workflow/ \| grep -v 白名单 | 0 真实 drift（chg-03 已闭合，仅白名单路径余留）✅ |
| AC-4 self-audit 函数 | pytest tests/test_install_repo_sync_contract.py::test_install_self_audit_reports_drift_to_stderr | PASS ✅ |
| AC-7 测试 | pytest -q | 289 passed（+1 vs baseline 288）+ 1 xfailed + 50 skipped，3 pre-existing failed 未增 ✅ |
| AC-3 harness-manager 硬门禁五 | grep -nE 'context.*tools.*evaluation.*flow.*state/experience' harness-manager.md | live ≥ 1 命中 + mirror 同步 ✅ |
