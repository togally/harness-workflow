# req-36（harness install 同步契约完整性修复（存量项目 .workflow/ 与 scaffold_v2 mirror 保持一致）） — Acceptance Report

## § 0 元信息

| 字段 | 值 |
|------|----|
| 执行时间戳 | 2026-04-23 |
| 涉及 commit | chg-01 audit / chg-02 helper+test / chg-03 reconcile / chg-04 acceptance Layer 1 / chg-05 mirror→live sync / chg-06 audit 解锁 / chg-07 CLI 路由 / chg-08 packaging glob |
| 验证 harness 命令 | pipx 安装版 `harness install --force-managed`（chg-07/08 合后真 wheel）|
| Layer 2 用户 confirm 状态 | **yes**（2026-04-23）|

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

### 关闭判定

真实结构性 drift count = **0**（仅 `state/platforms.yaml` `last_updated` 字段动态更新，属运行时行为，非同步契约漂移）

→ AC-5 Layer 1 **PASS**（chg-04）

---

## § 2 Layer 2：Yh-platform 真实存量项目 — 收口（user confirm = yes）

### 2.1 触发与首次真跑（reg-01 缘起）

用户 confirm = `yes`（2026-04-23）。首次真跑暴露 AC-5 未达：

```bash
cp -R /Users/jiazhiwei/IdeaProjects/Yh-platform/.workflow /Users/jiazhiwei/IdeaProjects/Yh-platform/.workflow.backup-req-36
cd /Users/jiazhiwei/IdeaProjects/Yh-platform && harness install
```

`harness install` 退出码 0，但 diff 排白名单后剩 **43 项 drift**（14 个 role 全差 + reg-01..04 / role-model-map / project-reporter / api-document-upload 缺失 + experience/evaluation/tools 一批差异）。

→ 触发 **reg-01**（install_repo 不全量同步 scaffold_v2 + _install_self_audit 锚点锁死），决议 append-to-current 加 chg-05/06。

### 2.2 chg-05 + chg-06（reg-01 路由产物）

- **chg-05**：`install_repo` 末尾接 `_sync_scaffold_v2_mirror_to_live` helper（mirror 全量铺到 target，遵循 17 项白名单 + sug-13/14 user-modified 保护）。新建 `_SCAFFOLD_V2_MIRROR_WHITELIST` 模块常量；`tests/test_install_repo_sync_contract.py` +4 用例 + 解 chg-02 1 xfail。
- **chg-06**：`_install_self_audit` 删 `pyproject.toml name == "harness-workflow"` 锚点段，保留 `HARNESS_DEV_REPO_ROOT` 作开发 escape hatch；audit 在所有 install 末尾跑，drift 不再沉默。`tests/test_install_repo_sync_contract.py` +2 用例。

chg-05/06 单测全绿（pytest 296 passed），但 Yh-platform 真跑 drift 仍 43 — executing 触底排查发现 **CLI 路由 + packaging 双结构性根因**，触发 **reg-02**。

### 2.3 chg-07 + chg-08（reg-02 路由产物）

- **chg-07**：`tools/harness_install.py:main()` 末尾追加 `install_repo(...)` 调用，`cli.py` install argparse 加 `--check / --force-managed / --all-platforms` 透传；`cli.py` cmd_update 删 bugfix-1 hack（任何 `--flag` 走 install_repo 的旁路），改硬 fail + stderr 迁移提示 `请改用 harness install --{flag}`；`--scan` 分支保留独立。`tests/test_cli_routing.py` +10 用例，`tests/test_cli.py` 旧 update --flag 断言 3 处迁移。
- **chg-08**：`pyproject.toml` `package-data` 替换为全量 glob `assets/scaffold_v2/.workflow/**/*`（删 15 行细分 patterns），`tests/test_package_data_completeness.py` +2 用例（pyproject patterns 模拟 setuptools glob + dev mirror runtime 污染锁），杜绝未来漏装回归。

### 2.4 端到端最终真跑（chg-05/06/07/08 全合后）

```bash
cd /Users/jiazhiwei/claudeProject/harness-workflow && pipx install --force .
rm -rf /Users/jiazhiwei/IdeaProjects/Yh-platform/.workflow
cp -R /Users/jiazhiwei/IdeaProjects/Yh-platform/.workflow.backup-req-36 /Users/jiazhiwei/IdeaProjects/Yh-platform/.workflow
cd /Users/jiazhiwei/IdeaProjects/Yh-platform && harness install --force-managed
diff -rq .../Yh-platform/.workflow .../scaffold_v2/.workflow | <扣 17+3 项完整白名单>
```

**结果**：
- install 输出含 `synced mirror→live: 29 file(s) processed`（证 chg-07 路由生效 + chg-05 helper 真跑）
- self-audit stderr 无漂移告警（证 chg-06 解锁 + audit 真跑 + 全部铺齐）
- diff 扣完整白名单后 drift = **0** ✅
- 真 wheel sanity：dev mirror == wheel mirror == 76 文件（证 chg-08 packaging 不漏装）

### 2.5 默认 install 行为说明（无 --force-managed）

不带 `--force-managed` 时，install 跳过 30 个已被用户改动的文件，stderr 提示 `skipping user-modified file <path>; pass --force-managed to overwrite`。这是 chg-05 sug-13/14 的**保护契约**（既登记 hash 又被改 = 用户故意改 = 不强覆盖），不是缺陷。首次 install 落地后 hash 登记，后续无噪声。

---

## § 3 关闭确认（最终版）

| AC | 实跑命令 / 证据 | 结果 |
|----|---------|------|
| AC-1 audit.md 完整 | `audit.md` 含 §2.3 A/B/C 三类 + 复现脚本 | PASS ✅（chg-01）|
| AC-2 live vs mirror zero-drift | `diff -rq .workflow/ scaffold_v2/.workflow/` 扣白名单 = 0 | PASS ✅（chg-03）|
| AC-3 硬门禁五覆盖扩展 | grep harness-manager.md 命中保护面 + mirror 同步 | PASS ✅（chg-02）|
| AC-4 install_repo self-audit | pytest test_install_repo_sync_contract.py 含 audit stderr 用例 PASS | PASS ✅（chg-02 + chg-06 解锁）|
| AC-5 Layer 1 mktemp drift=0 | diff -rq + 白名单（见 §1）| PASS ✅（chg-04）|
| AC-5 Layer 2 Yh-platform drift=0 | pipx install + 真跑 + diff 扣完整白名单（见 §2.4）| **PASS** ✅（reg-01 + reg-02 收口）|
| AC-6 ≥3 commit 独立可 revert | chg-01..08 各独立 commit，message 引 req-36 + chg-NN | PASS ✅（8 commit）|
| AC-7 pytest 零新增失败 + ≥2 sync test | testing 复跑 308 passed + 50 skipped + 3 pre-existing fails，新增 chg 专项 20/20 PASS（test_install_repo_sync_contract 8 + test_cli_routing 10 + test_package_data_completeness 2）| PASS ✅ |
| AC-8 契约 7 + 硬门禁六 | 全部产物首次引用 ID 带描述 / title | PASS ✅ |

**总判定**：req-36 acceptance **PASS**，全部 8 条 AC 关闭，可推 done。

---

## § 4 旁支问题（不阻塞 done，留给后续）

1. 3 个 pre-existing pytest 失败（test_chg03_title_contract / test_smoke_req29 硬编码 req-29/req-30 归档目录名）— 与 req-36 无关，建议另起 bugfix
2. scaffold_v2 mirror 缺空目录占位符 — cosmetic，不影响功能
3. CLI sug-12 / sug-13 复发（regression / planning 后 `harness next` 吞 stage、runtime.yaml ↔ req-*.yaml stage 不同步）— 已多次手工修，建议另起 req 系统修
