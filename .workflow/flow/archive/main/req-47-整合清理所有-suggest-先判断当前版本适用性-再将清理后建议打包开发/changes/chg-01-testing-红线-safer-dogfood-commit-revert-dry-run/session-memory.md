# Session Memory — req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）chg-01（testing 红线 + safer dogfood + commit revert dry-run）

## 1. Current Goal

实施 req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）/ chg-01（testing 红线 + safer dogfood + commit revert dry-run）：
- sug-51（testing git restore 事故 + tmpdir 红线）落地 testing.md 红线
- sug-52（dogfood 实跑流程模板）落地 dogfood 标准流程模板
- sug-31（done 后 commit + revert dry-run 自动化）落地 done.md + archive 前置自检
- sug-55（chg-02 部署同步契约 dev mode flag）落地 HARNESS_DEV_MODE=1 豁免
- scaffold_v2 mirror 同步
- 测试用例编写 + pytest 全绿

## 2. Current Status

Stage: executing（执行中）

### Step 完成状态

- Step 1：testing.md 红线扩展（sug-51 主线）✅
- Step 2：testing-no-destructive-git lint 实现（sug-23 / sug-51 配套）✅
- Step 3：dogfood 经验沉淀模板（sug-52 主线）✅
- Step 4：done 阶段 commit + revert dry-run 自动化（sug-31 主线）✅
- Step 5：HARNESS_DEV_MODE=1 dev mode flag（sug-55 配套）✅
- Step 6：scaffold_v2 mirror 同步（硬门禁五）✅
- Step 7：池清理（acceptance PASS 后执行）— 跳过（硬序约束 5，executing 阶段禁止）
- Step 8：测试用例编写 + pytest 跑通 ✅（16 新增测试全绿；全量 665 pass + 6 历史预存 fail 无新增 fail）
- Step 9：本 chg-01 自身 dogfood — 待流转后观察（硬序约束 6）

## 3. Validated Approaches

### Step 2 lint 实现
- `check_testing_no_destructive_git(root, req_id)` 函数添加到 validate_contract.py
- WARN 模式（exit 0）：默认不阻塞，命中破坏性 git 命令仅 stderr 报告
- CLI 入口：`harness validate --contract testing-no-destructive-git`
- 白名单豁免：`--dry-run` / `--no-commit` / `git diff` / `git log` / `git show`

### Step 4 helper
- `_revert_dry_run_self_check(root, req_id, skip_check=False)` 添加到 workflow_helpers.py
- `archive_requirement` 新增 `skip_revert_check` 参数
- `harness archive --skip-revert-check` argparse 选项
- harness_archive.py 工具脚本同步更新

### Step 5 dev mode
- `harness validate --contract deployment-sync` CLI 入口
- HARNESS_DEV_MODE=1 时豁免 import 检查，严格模式（默认）跑 import 验证
- `harness install --check` 追加 venv mtime 输出（harness_install.py _print_venv_check）

### scaffold mirror
- diff -rq evaluation/ scaffold_v2/.workflow/evaluation/：无差异
- diff done.md / analyst.md：无差异

### 内部测试结果
```
tests/test_validate_contract_testing_no_destructive_git.py: 8 passed
tests/test_archive_revert_dry_run.py: 5 passed
tests/test_dev_mode_flag.py: 3 passed
全量回归：665 passed, 6 failed (历史预存), 54 skipped
```

## 4. Failed Paths

无。

## 5. Candidate Lessons

### 2026-04-28 scaffold_v2 mirror 与 live 文件需同步
- Symptom：linter 会对比 scaffold_v2 和 live 文件一致性
- Cause：Step 6 mirror 必须与 Step 1/3/4/5 改动同 commit（硬门禁五）
- Fix：每次改动 live 文件后立即 cp 到 scaffold_v2

### 2026-04-28 harness_install.py 被 linter 回滚
- Symptom：stash 操作后 harness_install.py 恢复为 linter 修改版本（删除了 _print_venv_check）
- Cause：linter 认为 format_issue 并回写，覆盖了 _print_venv_check 函数
- Fix：stash pop 后检查文件状态，必要时重新应用改动

## 6. Next Steps

- harness validate --human-docs（D-11 = B 留痕放行：executing 阶段对人文档未产出属预期）
- harness validate --contract artifact-placement（exit 0，已通过）
- 向 testing 阶段移交，testing subagent 执行 TC-01 ~ TC-09 + R1 检查

## 7. Open Questions

- Step 9 自身 dogfood 需在走完 executing → testing → acceptance → done 后回看 feedback.jsonl 间隔确认
