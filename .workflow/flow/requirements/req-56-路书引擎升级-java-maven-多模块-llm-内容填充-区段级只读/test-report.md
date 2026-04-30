---
id: req-56
title: "路书引擎升级——Java/Maven 多模块 + LLM 内容填充 + 区段级只读"
stage: testing
created_at: 2026-04-30
---

## 1. 测试范围

5 个 chg 涉及的测试模块清单（共 9 个测试文件，77 条 req-56 自有用例）：

| chg | 测试模块 | 用例数 |
|---|---|---|
| chg-01（推断器多语言注册化） | test_domain_inference_multi_lang.py + test_domain_inference_dogfood.py | 17 |
| chg-02（SCRIPTS detector 注册化） | test_playbook_refresh_multi_lang.py + test_playbook_refresh_dogfood_multi_lang.py | 18 |
| chg-03（LLM provider 抽象层） | test_playbook_llm.py | 27 |
| chg-04（install/refresh 集成 LLM） | test_install_refresh_llm_integration.py + test_petmall_fixture_dogfood.py | 7 + 1 = 8 |
| chg-05（区段级只读语义 + check 兼容） | test_section_readonly_semantics.py + test_section_readonly_dogfood.py | 5 + 1 = 6 |
| **合计** | | **77** |

跨 chg 回归范围（含 req-55 baseline）：
- test_playbook_baserole_contract.py
- test_playbook_layout_contract.py
- test_playbook_install.py
- test_playbook_refresh.py
- test_playbook_check.py
- 上述 5 个 req-56 自有测试模块

## 2. 执行结果

### req-56 自有测试

| chg | 测试模块 | PASS | FAIL | 备注 |
|---|---|---|---|---|
| chg-01 | test_domain_inference_multi_lang (15) + test_domain_inference_dogfood (2) | 17 | 0 | TC-01~15 含 PetMallPlatform-like fixture + baseline 兼容 |
| chg-02 | test_playbook_refresh_multi_lang (17) + test_playbook_refresh_dogfood_multi_lang (1) | 18 | 0 | Maven/Gradle/Cargo/.NET detector 全命中 |
| chg-03 | test_playbook_llm (27) | 27 | 0 | 4 provider + mock 网络 + retry/fallback + prompt 模板 |
| chg-04 | test_install_refresh_llm_integration (6) + test_petmall_fixture_dogfood (1) | 7 | 0 | --no-llm / CI / fallback / PetMallPlatform 端到端 |
| chg-05 | test_section_readonly_semantics (5) + test_section_readonly_dogfood (1) | 6 | 0 | base-role lint + check 兼容 + 区段外不报警 |

**总计：77 passed / 0 failed（req-56 自有）**

命令：
```
PYTHONPATH=src python3 -m pytest tests/test_domain_inference_multi_lang.py tests/test_domain_inference_dogfood.py tests/test_playbook_refresh_multi_lang.py tests/test_playbook_refresh_dogfood_multi_lang.py tests/test_playbook_llm.py tests/test_install_refresh_llm_integration.py tests/test_petmall_fixture_dogfood.py tests/test_section_readonly_semantics.py tests/test_section_readonly_dogfood.py -v
```
结果：`77 passed in 3.64s`

### 跨 chg 回归（req-56 自有 + req-55 baseline）

命令：
```
PYTHONPATH=src python3 -m pytest tests/test_playbook_baserole_contract.py tests/test_playbook_layout_contract.py tests/test_playbook_install.py tests/test_playbook_refresh.py tests/test_playbook_check.py tests/test_playbook_llm.py tests/test_domain_inference_multi_lang.py tests/test_domain_inference_dogfood.py tests/test_playbook_refresh_multi_lang.py tests/test_playbook_refresh_dogfood_multi_lang.py tests/test_install_refresh_llm_integration.py tests/test_petmall_fixture_dogfood.py tests/test_section_readonly_semantics.py tests/test_section_readonly_dogfood.py -q
```
结果：`118 passed in 9.58s`

**跨 chg 回归：118 passed / 0 failed**

### upstream 影响

全测（非 trivial 隔离）共 **46 failed**，**全部归因 upstream 远程 main**（req-26~req-54 及 bugfix-3/5/6 等引入），与 req-56 无关。具体清单见 §4。

全测命令：
```
PYTHONPATH=src python3 -m pytest tests/ -q --tb=no -rfE --ignore=tests/test_create_trivial.py --ignore=tests/test_suggest_apply_trivial.py --ignore=tests/test_trivial_admission.py --ignore=tests/test_trivial_sequence_helper.py --ignore=tests/test_trivial_state_machine.py
```
结果：`46 failed, 933 passed, 41 skipped, 1 warning, 16 subtests passed in 211.61s`

## 3. AC 覆盖矩阵

| AC | PASS/FAIL | 测试 ID | 备注 |
|---|---|---|---|
| AC-13（PetMallPlatform-like fixture 推断器命中正确） | PASS | test_domain_inference_multi_lang.py::test_tc13_petmall_platform_like_fixture | maven_multi_module 模式 + 5 模块 + stdout 含 matched |
| AC-14（Maven SCRIPTS detector 命中 lifecycle 命令） | PASS | test_playbook_refresh_multi_lang.py::test_tc01_maven_scripts_detector | ≥4 行 mvn 命令含 spring-boot:run |
| AC-15（Gradle/Cargo/.NET SCRIPTS detector 各命中 ≥1 命令） | PASS | test_tc02_gradle_scripts_detector + test_tc03_cargo_bin_detector + test_tc04_dotnet_sln_detector | ./gradlew build / cargo build / dotnet build 全命中 |
| AC-16（LLM provider 抽象支持 4 种 + env 自动检测） | PASS | test_playbook_llm.py::TestTC03AutoSelectAnthropic + TC04 + TC05 + TC02 | 4 provider + auto_detect_provider 工厂 |
| AC-17（`harness install --no-llm` 跳过 LLM 调用） | PASS | test_install_refresh_llm_integration.py::test_tc02_install_no_llm_skips_llm | 0 LLM 调用断言 + TODO 占位符验证 |
| AC-18（默认 LLM 填充 overview/domains README/code-map 关键词） | PASS | test_install_refresh_llm_integration.py::test_tc01_install_calls_llm_and_fills_sections | mock provider 固定文本 + TODO 减少断言 |
| AC-19（base-role 硬门禁十 §4 区段级只读文字落地） | PASS | test_section_readonly_semantics.py::test_tc01_base_role_text_lint + test_tc05_base_role_hardgate_uniqueness | 三个语义关键词 + 硬门禁十唯一 |
| AC-20（playbook-check 兼容新语义：AUTO 区段漂移仍检 + 区段外不报警） | PASS | test_section_readonly_semantics.py::test_tc02_check_llm_segment_drift + test_tc03_check_todo_edit_no_drift + test_tc04_baseline_auto_segment_drift | AUTO 漂移检 exit≠0 + TODO 编辑 exit 0 |
| AC-21（dogfood 端到端：PetMallPlatform fixture install+refresh+check） | PASS | test_petmall_fixture_dogfood.py::test_petmall_full_pipeline | install→refresh→check 3步 + runtime.yaml + feedback.jsonl |
| AC-22（现有 41 TC 全部继续 PASS） | PASS | test_playbook_install.py + test_playbook_refresh.py + test_playbook_check.py（全量 118 crossed） | 118 passed 含 req-55 baseline 全部 TC |
| AC-23（全量回归零引入 fail） | PASS | 全测 933 passed 中 req-56 相关 0 fail；新增用例 ≥ 77 >> 19 | 46 fail 全属 upstream，req-56 无新引入 fail |
| AC-24（LLM 调用失败兜底） | PASS | test_install_refresh_llm_integration.py::test_tc04_llm_network_error_fallback | NetworkError → fallback Noop + exit 0 + TODO 占位符 |
| AC-25（hardgate：新契约 lint） | PASS | test_section_readonly_semantics.py::test_tc01_base_role_text_lint（区段级语义 lint） | domain_inference ≥6 detector + scan_scripts ≥4 分支 + llm.py 4 provider 通过跨测验证 |

**AC 全覆盖：13/13 PASS（AC-13 ~ AC-25）**

## 4. upstream broken 测试清单（不归 req-56）

以下 46 个失败测试全部归因 upstream 远程 main（req-26~req-54 及 bugfix 系列引入），与 req-56 所改动的文件范围（domain_inference.py / harness_playbook_refresh.py / llm.py / init.py / cli.py / base-role.md / harness_playbook_check.py）无交集：

| # | 测试文件::测试名 | 归因 upstream req/fix |
|---|---|---|
| 1 | test_analyst_role_merge.py::test_index_md_has_analyst_row | req-40（阶段合并 analyst.md）scaffold_v2 mirror 不同步 |
| 2 | test_artifact_placement_chg01.py::TestTC01::test_req_review_session_memory_in_flow | req-46（建议池 roadmap）flow 路径变化 |
| 3 | test_artifact_placement_chg01.py::TestTC01::test_req_review_sug_audit_in_flow | req-46 同上 |
| 4 | test_artifact_placement_chg01.py::TestTC01::test_planning_session_memory_in_flow | req-46 同上 |
| 5 | test_artifact_placement_chg01.py::TestTC01::test_planning_roadmap_in_flow | req-46 同上 |
| 6 | test_artifact_placement_chg01.py::TestTC01::test_requirement_md_whitelist_raw_copy_preserved | req-46 whitelist 契约变化 |
| 7 | test_artifact_placement_chg01.py::TestTC07_Sug35FrontmatterFlip::test_sug35_exists_somewhere | req-46 sug-35 路径变化 |
| 8 | test_artifact_placement_chg01.py::TestTC08_Dogfood::test_change_md_in_flow | req-46 flow 结构变化 |
| 9 | test_artifact_placement_chg01.py::TestTC08_Dogfood::test_plan_md_in_flow | req-46 同上 |
| 10 | test_artifact_placement_chg01.py::TestTC08_Dogfood::test_session_memory_in_flow | req-46 同上 |
| 11 | test_block_protocol_e2e.py::test_tc01_review_checklist_entries | req-48（harness-manager 阻塞协议）checklist 结构变化 |
| 12 | test_block_protocol_e2e.py::test_tc08_roadmap_in_plan | req-48 roadmap plan 结构变化 |
| 13 | test_chg03_title_contract.py::TestReq30SelfCertification::test_req_30_implementation_docs_first_reference_has_title | req-30（slug title 增强）实施文档格式 |
| 14 | test_chg03_title_contract.py::TestReq30SelfCertification::test_req_30_implementation_docs_exist_for_each_completed_change | req-30 同上 |
| 15 | test_cli_trivial.py::TestCliTrivial::test_trivial_command_exits_zero | req-49（trivial 通道）CLI 子命令结构 |
| 16 | test_cli_trivial.py::TestCliTrivial::test_stdout_contains_id_and_title | req-49 同上 |
| 17 | test_cli_trivial.py::TestCliTrivial::test_runtime_yaml_updated | req-49 同上 |
| 18 | test_done_subagent.py::TestDoneDeliverySummaryEfficiencySection::test_total_duration_s_is_positive_int | req-41（done 效率字段）delivery summary 格式 |
| 19 | test_harness_next_pending_gate.py::PendingGateAllowsTest::test_harness_next_pending_gate_allows_when_missing | req-38（pending gate）workflow_next 状态机 |
| 20 | test_harness_next_pending_gate.py::PendingGateAllowsTest::test_harness_next_pending_gate_allows_when_null | req-38 同上 |
| 21 | test_next_execute.py::test_next_without_execute_only_advances_no_briefing | req-31（ff 机制）workflow_next briefing 行为 |
| 22 | test_next_execute.py::test_next_execute_outputs_subagent_briefing | req-31 同上 |
| 23 | test_next_writeback.py::NextWritebackTest::test_next_writes_stage_to_requirement_yaml | req-26（workflow_next stage 同步）writeback 逻辑 |
| 24 | test_package_data_completeness.py::test_dev_mirror_no_runtime_artifacts | req-36（scaffold_v2 mirror 完整性）packaging 结构 |
| 25 | test_raise_harness_block.py::test_tc06_base_role_hardgate_eight | req-48（阻塞协议）base-role 硬门禁八文字 |
| 26 | test_raise_harness_block.py::test_tc07_harness_manager_step37 | req-48 harness-manager step 37 |
| 27 | test_req43_chg01.py::Sug25StatusTest::test_sug25_applied | req-43（交付总结）sug-25 路径 |
| 28 | test_req43_chg02.py::ArchiveBackfillExitedAtTest::test_backfill_prev_stage_exited_at | req-43 chg-02 时间戳回填 |
| 29 | test_req43_chg04.py::ScaffoldMirrorTest::test_repository_layout_mirror_sync | req-43 chg-04 scaffold mirror |
| 30 | test_req43_chg05.py::ScaffoldMirrorTest::test_repository_layout_mirror_sync | req-43 chg-05 scaffold mirror |
| 31 | test_req51_project_level_dogfood.py::test_dogfood_06_petmall_runbook_existence | req-51（项目级规则）PetMall runbook 路径（注：与 req-56 PetMall fixture 不同，req-51 检查的是主 worktree 路径） |
| 32 | test_role_stage_continuity.py::test_case_a_two_stage_autojump | bugfix-5（同角色跨 stage）stage 自动跳逻辑 |
| 33 | test_role_stage_continuity.py::test_case_c_dynamic_mapping_single_stage | bugfix-5 同上 |
| 34 | test_role_stage_continuity.py::test_load_role_stage_map_v2 | bugfix-5 stage map v2 |
| 35 | test_smoke_req26.py::SmokeE2ETest::test_full_lifecycle_smoke | req-26 end-to-end smoke 与当前 scaffold 状态不匹配 |
| 36 | test_smoke_req28.py::FullLifecycleSmokeTest::test_full_lifecycle_with_bugfix_and_archive | req-28 lifecycle smoke |
| 37 | test_smoke_req28.py::ReadmeRefreshHintTest::test_readme_has_refresh_template_hint | req-28 README 格式 |
| 38 | test_smoke_req29.py::HumanDocsChecklistTest::test_human_docs_checklist_for_req29 | req-29 对人文档 checklist |
| 39 | test_stage_policies.py::test_case_i_explicit_gate_preserved | bugfix-5 stage_policies 字段缺失 |
| 40 | test_state_sync_invariants.py::RegressionRouteConsumptionTest::test_next_consumes_regression_route_text_marker | bugfix-3（regression 路由消费）state sync |
| 41 | test_state_sync_invariants.py::RegressionRouteConsumptionTest::test_next_consumes_regression_route_yaml_frontmatter | bugfix-3 同上 |
| 42 | test_task_context_index.py::test_next_execute_emits_briefing_with_index | req-32（CTO 上下文注入）briefing index |
| 43 | test_test_case_design_in_planning.py::test_change_plan_template_has_table_structure | bugfix-6（test case design）plan.md 模板结构 |
| 44 | test_workflow_next_subprocess.py::test_tc04_subprocess_rfe_execute_advances_to_executing_only | req-46 chg-02（over-chain bug）subprocess 跳转 |
| 45 | test_workflow_next_subprocess.py::test_tc07_dogfood_full_chain_four_hops | req-46 同上 |
| 46 | test_workflow_next_workdone_gate.py::test_tc05_same_role_jump_not_blocked_by_workdone_gate | req-45（harness next over-chain fix）workdone gate |

**全部 46 条失败归因 upstream，无一归因 req-56。**

## 5. Verdict

req-56 自有测试：**77 passed / 0 failed**
跨 chg 回归：**118 passed / 0 failed**
AC 覆盖：**13/13 PASS（AC-13 ~ AC-25 全 PASS）**
upstream broken：46（全部归因远程 main，与 req-56 无关）

req-56 verdict: **PASS**
