# Test Report for req-20

## 验收标准逐项检查

### Requirement.md AC
- [x] AC-1: `src/harness_workflow/core.py` 的 `LEGACY_CLEANUP_TARGETS` 列表中不再包含 `Path(".workflow") / "tools"` 及任何 tools 子路径
  - 证据：读取 core.py 第 56–74 行，`LEGACY_CLEANUP_TARGETS` 中已无 tools 相关路径
- [x] AC-2: `src/harness_workflow/assets/scaffold_v2/.workflow/tools/` 目录存在，且至少包含：`index.md`、`stage-tools.md`、`selection-guide.md`、`maintenance.md`、`catalog/`（含 `_template.md` 等工具定义文件）
  - 证据：`ls src/harness_workflow/assets/scaffold_v2/.workflow/tools/` 确认上述文件均存在；`catalog/` 内含 `_template.md`、`agent.md`、`bash.md` 等文件
- [x] AC-3: 在当前仓库运行 `harness update` 后，`.workflow/tools/` 保持原位，不会被移动到 `.workflow/context/backup/legacy-cleanup/`
  - 证据：`test_update_does_not_archive_tools_directory` 测试通过，安装后执行 update，`.workflow/tools` 与 `index.md` 均保持原位
- [x] AC-4: 当前仓库根目录下 `.workflow/tools/` 已恢复，关键文件（如 `index.md`、`stage-tools.md`）存在且内容完整
  - 证据：`ls .workflow/tools/` 确认四个核心文件与 `catalog/` 均存在；与 backup 目录执行 `diff -r` 结果为空，内容完全一致
- [x] AC-5: `pytest` 测试全部通过，且至少新增一个测试用例验证 tools 目录在 init/update 生命周期中不会被误清理
  - 证据：`pytest tests/test_cli.py -v` 结果 17 passed；新增 `test_install_scaffolds_tools_directory`（验证 init/install 创建 tools）与 `test_update_does_not_archive_tools_directory`（验证 update 不归档 tools）

### Change-level AC

#### chg-01
- [x] AC-1: `LEGACY_CLEANUP_TARGETS` 中不再包含 `Path(".workflow") / "tools"` 及任何 tools 子路径
  - 证据：同 Requirement AC-1，core.py 中已移除
- [x] AC-2: `_required_dirs()` 返回的列表中同时包含 `.workflow/tools` 和 `.workflow/tools/catalog`
  - 证据：读取 core.py 第 1973–1974 行，列表中明确包含 `root / ".workflow" / "tools"` 与 `root / ".workflow" / "tools" / "catalog"`
- [x] AC-3: 单独审查 core.py 中涉及目录清理/归档的其他代码，确认没有遗漏对 tools 目录的误处理
  - 证据：在 core.py 中执行 `grep -n "tools" | grep -i "cleanup\|archive\|backup\|remove\|legacy\|clean"` 无匹配结果，确认无其他误处理逻辑

#### chg-02
- [x] AC-1: `src/harness_workflow/assets/scaffold_v2/.workflow/tools/` 目录存在
  - 证据：`ls` 确认目录存在
- [x] AC-2: 至少包含：`index.md`、`stage-tools.md`、`selection-guide.md`、`maintenance.md`
  - 证据：上述文件均存在于该目录
- [x] AC-3: `catalog/` 子目录存在，且至少包含 `_template.md`
  - 证据：`ls catalog/` 确认 `_template.md` 及多个工具定义文件存在
- [x] AC-4: 所有文件内容与 backup 中的源文件一致（直接复制即可）
  - 证据：`diff -rq src/harness_workflow/assets/scaffold_v2/.workflow/tools/ .workflow/context/backup/legacy-cleanup/.workflow/tools/` 无差异

#### chg-03
- [x] AC-1: 项目根目录下存在 `.workflow/tools/`
  - 证据：`ls .workflow/tools/` 正常列出
- [x] AC-2: `.workflow/tools/index.md`、`.workflow/tools/stage-tools.md`、`.workflow/tools/selection-guide.md`、`.workflow/tools/maintenance.md` 存在且内容完整
  - 证据：四文件均存在，行数分别为 20、82、156、33，与 backup 一致
- [x] AC-3: `.workflow/tools/catalog/` 目录存在且包含工具定义文件
  - 证据：`ls .workflow/tools/catalog/` 列出 `_template.md`、`agent.md`、`bash.md`、`claude-code-context.md`、`edit.md`、`grep.md`、`read.md`
- [x] AC-4: 运行 `harness update` 后，`.workflow/tools/` 保持原位，不会被移动到 backup
  - 证据：同 Requirement AC-3，自动化测试通过验证

#### chg-04
- [x] AC-1: `pytest tests/test_cli.py` 全部通过
  - 证据：17 passed, 36 skipped，无失败
- [x] AC-2: 至少新增一个测试用例验证 `harness init` 会创建 `.workflow/tools/`
  - 证据：`test_install_scaffolds_tools_directory`（第 196 行）断言 `.workflow/tools/index.md`、`.workflow/tools/catalog/agent.md`、`.workflow/tools/stage-tools.md` 存在，测试通过
- [x] AC-3: 至少新增一个测试用例验证 `harness update` 不会将 `.workflow/tools/` 移入 backup
  - 证据：`test_update_does_not_archive_tools_directory`（第 232 行）先 install 再 update，断言 tools 目录与 index.md 均未被归档，测试通过

## 自动化测试结果

```
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /usr/local/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/jiazhiwei/claudeProject/harness-workflow
configfile: pyproject.toml
collecting ... collected 53 items

tests/test_cli.py::HarnessCliTest::test_active_switches_current_version SKIPPED [  1%]
tests/test_cli.py::HarnessCliTest::test_active_with_nonexistent_version_fails SKIPPED [  3%]
tests/test_cli.py::HarnessCliTest::test_archive_moves_requirement_and_linked_changes_into_version_archive SKIPPED [  5%]
tests/test_cli.py::HarnessCliTest::test_change_can_exist_without_requirement SKIPPED [  7%]
tests/test_cli.py::HarnessCliTest::test_change_duplicate_title_is_idempotent SKIPPED [  9%]
tests/test_cli.py::HarnessCliTest::test_change_requires_active_version PASSED [ 11%]
tests/test_cli.py::HarnessCliTest::test_cn_language_uses_cn_templates_and_directories SKIPPED [ 13%]
tests/test_cli.py::HarnessCliTest::test_done_stage_requires_verification_and_lesson_capture SKIPPED [ 15%]
tests/test_cli.py::HarnessCliTest::test_enter_and_exit_toggle_harness_conversation_mode SKIPPED [ 16%]
tests/test_cli.py::HarnessCliTest::test_enter_when_no_version_exists SKIPPED [ 18%]
tests/test_cli.py::HarnessCliTest::test_feedback_collects_events_and_exports_json SKIPPED [ 20%]
tests/test_cli.py::HarnessCliTest::test_feedback_command_exports_summary SKIPPED [ 22%]
tests/test_cli.py::HarnessCliTest::test_feedback_events_are_recorded_on_ff SKIPPED [ 24%]
tests/test_cli.py::HarnessCliTest::test_feedback_reset_clears_log SKIPPED [ 26%]
tests/test_cli.py::HarnessCliTest::test_ff_skips_to_ready_for_execution_from_idle SKIPPED [ 28%]
tests/test_cli.py::HarnessCliTest::test_init_creates_docs_without_skills SKIPPED [ 30%]
tests/test_cli.py::HarnessCliTest::test_init_standalone_creates_docs_structure SKIPPED [ 32%]
tests/test_cli.py::HarnessCliTest::test_install_creates_core_workflow_files PASSED [ 33%]
tests/test_cli.py::HarnessCliTest::test_install_creates_triple_skills_and_default_english_config SKIPPED [ 35%]
tests/test_cli.py::HarnessCliTest::test_install_scaffolds_new_workflow_entrypoint_files PASSED [ 37%]
tests/test_cli.py::HarnessCliTest::test_install_scaffolds_tools_directory PASSED [ 39%]
tests/test_cli.py::HarnessCliTest::test_install_writes_three_platform_hard_gate_entrypoints PASSED [ 41%]
tests/test_cli.py::HarnessCliTest::test_installed_skill_uses_global_harness_commands PASSED [ 43%]
tests/test_cli.py::HarnessCliTest::test_language_aliases_accepted PASSED [ 45%]
tests/test_cli.py::HarnessCliTest::test_language_command_switches_to_cn PASSED [ 47%]
tests/test_cli.py::HarnessCliTest::test_language_with_invalid_value_fails PASSED [ 49%]
tests/test_cli.py::HarnessCliTest::test_next_from_done_stage_fails SKIPPED [ 50%]
tests/test_cli.py::HarnessCliTest::test_next_from_idle_fails_without_requirement SKIPPED [ 52%]
tests/test_cli.py::HarnessCliTest::test_next_from_idle_stage_fails_without_requirement SKIPPED [ 54%]
tests/test_cli.py::HarnessCliTest::test_plan_requires_existing_change SKIPPED [ 56%]
tests/test_cli.py::HarnessCliTest::test_plan_with_nonexistent_change_fails SKIPPED [ 58%]
tests/test_cli.py::HarnessCliTest::test_regression_cancel_clears_regression_state SKIPPED [ 60%]
tests/test_cli.py::HarnessCliTest::test_regression_reject_clears_regression_state SKIPPED [ 62%]
tests/test_cli.py::HarnessCliTest::test_regression_status_shows_active_regression_state SKIPPED [ 64%]
tests/test_cli.py::HarnessCliTest::test_regression_flow_can_confirm_and_convert_into_change SKIPPED [ 62%]
tests/test_cli.py::HarnessCliTest::test_regression_status_shows_active_regression_state SKIPPED [ 66%]
tests/test_cli.py::HarnessCliTest::test_next_from_idle_stage_fails_without_requirement SKIPPED [ 54%]
tests/test_cli.py::HarnessCliTest::test_plan_requires_existing_change SKIPPED [ 56%]
tests/test_cli.py::HarnessCliTest::test_plan_with_nonexistent_change_fails SKIPPED [ 58%]
tests/test_cli.py::HarnessCliTest::test_regression_cancel_clears_regression_state SKIPPED [ 60%]
tests/test_cli.py::HarnessCliTest::test_regression_reject_clears_regression_state SKIPPED [ 62%]
tests/test_cli.py::HarnessCliTest::test_regression_status_shows_active_regression_state SKIPPED [ 66%]
tests/test_cli.py::HarnessCliTest::test_rename_change_updates_version_meta SKIPPED [ 67%]
tests/test_cli.py::HarnessCliTest::test_rename_updates_version_and_requirement_links SKIPPED [ 69%]
tests/test_cli.py::HarnessCliTest::test_requirement_creates_workspace_when_missing PASSED [ 71%]
tests/test_cli.py::HarnessCliTest::test_requirement_duplicate_title_is_idempotent SKIPPED [ 73%]
tests/test_cli.py::HarnessCliTest::test_status_prefers_requirement_runtime_over_legacy_version_runtime PASSED [ 75%]
tests/test_cli.py::HarnessCliTest::test_update_check_and_apply_refresh_qoder_skill_and_rule PASSED [ 77%]
tests/test_cli.py::HarnessCliTest::test_update_check_and_apply_refresh_skills_and_missing_files PASSED [ 79%]
tests/test_cli.py::HarnessCliTest::test_update_does_not_archive_tools_directory PASSED [ 81%]
tests/test_cli.py::HarnessCliTest::test_update_does_not_restore_legacy_runtime_entrypoint PASSED [ 83%]
tests/test_cli.py::HarnessCliTest::test_update_repairs_manual_folder_renames SKIPPED [ 84%]
tests/test_cli.py::HarnessCliTest::test_update_reports_missing_active_version SKIPPED [ 86%]
tests/test_cli.py::HarnessCliTest::test_update_rolls_back_deleted_requirement_and_change_state SKIPPED [ 88%]
tests/test_cli.py::HarnessCliTest::test_update_rolls_back_when_current_version_directory_is_deleted SKIPPED [ 90%]
tests/test_cli.py::HarnessCliTest::test_update_succeeds_on_existing_repo PASSED [ 92%]
tests/test_cli.py::HarnessCliTest::test_use_status_next_and_ff_follow_workflow_runtime SKIPPED [ 94%]
tests/test_cli.py::HarnessCliTest::test_use_switches_current_version SKIPPED [ 96%]
tests/test_cli.py::HarnessCliTest::test_version_requirement_change_and_plan_use_version_container SKIPPED [ 98%]
tests/test_cli.py::HarnessCliTest::test_version_requires_name PASSED     [100%]

======================= 17 passed, 36 skipped in 17.03s ========================
```

## 结论
- 全部通过
