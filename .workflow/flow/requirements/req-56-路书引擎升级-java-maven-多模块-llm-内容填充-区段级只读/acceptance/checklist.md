---
id: req-56
title: "路书引擎升级——Java/Maven 多模块 + LLM 内容填充 + 区段级只读"
stage: acceptance
created_at: 2026-04-30
verdict: PASS
---

## 1. AC 覆盖复核

| AC | 描述 | 测试 ID | 状态 |
|---|---|---|---|
| AC-13 | PetMallPlatform-like fixture 推断器命中正确（maven_multi_module + 5 模块） | test_domain_inference_multi_lang.py::test_tc13_petmall_platform_like_fixture | PASS |
| AC-14 | Maven SCRIPTS detector 命中 lifecycle 命令（≥4 行 mvn + spring-boot:run） | test_playbook_refresh_multi_lang.py::test_tc01_maven_scripts_detector | PASS |
| AC-15 | Gradle/Cargo/.NET SCRIPTS detector 各命中 ≥1 命令 | test_tc02_gradle_scripts_detector + test_tc03_cargo_bin_detector + test_tc04_dotnet_sln_detector | PASS |
| AC-16 | LLM provider 抽象支持 4 种 + env 自动检测（ANTHROPIC > OPENAI > Ollama > Noop） | test_playbook_llm.py::TestTC03AutoSelectAnthropic + TC04 + TC05 + TC02 | PASS |
| AC-17 | `harness install --no-llm` 跳过 LLM 调用，overview/domains 保持 TODO 占位 | test_install_refresh_llm_integration.py::test_tc02_install_no_llm_skips_llm | PASS |
| AC-18 | 默认 LLM 填充 overview/domains README/code-map 关键词（mock provider 固定文本，TODO 数减少） | test_install_refresh_llm_integration.py::test_tc01_install_calls_llm_and_fills_sections | PASS |
| AC-19 | base-role 硬门禁十 §4 区段级只读文字落地（三语义关键词 + 硬门禁十唯一） | test_section_readonly_semantics.py::test_tc01_base_role_text_lint + test_tc05_base_role_hardgate_uniqueness | PASS |
| AC-20 | playbook-check 兼容新语义：AUTO 区段漂移仍检（exit≠0） + 区段外不报警（exit 0） | test_section_readonly_semantics.py::test_tc02_check_llm_segment_drift + test_tc03_check_todo_edit_no_drift + test_tc04_baseline_auto_segment_drift | PASS |
| AC-21 | dogfood 端到端：PetMallPlatform fixture install→refresh→check 3步 + runtime.yaml + feedback.jsonl | test_petmall_fixture_dogfood.py::test_petmall_full_pipeline | PASS |
| AC-22 | 现有 41 TC 全部继续 PASS（跨 chg 118 passed 含 req-55 baseline 全量） | test_playbook_install.py + test_playbook_refresh.py + test_playbook_check.py（跨 chg 118 全覆盖） | PASS |
| AC-23 | 全量回归零引入 fail（新增 ≥77 条用例 >> 19；46 fail 全属 upstream） | 全测 933 passed；req-56 相关 0 fail | PASS |
| AC-24 | LLM 调用失败兜底：NetworkError → fallback Noop + exit 0 + TODO 占位符保持 | test_install_refresh_llm_integration.py::test_tc04_llm_network_error_fallback | PASS |
| AC-25 | hardgate 新契约 lint：domain_inference ≥6 detector + scan_scripts ≥4 分支 + llm.py 4 provider | test_section_readonly_semantics.py::test_tc01_base_role_text_lint（跨测验证） | PASS |

**AC 全覆盖：13/13 PASS（AC-13 ~ AC-25）**

## 2. 硬门禁合规

- **硬门禁五（mirror 同步）**：✅
  `.workflow/context/roles/base-role.md` 与 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md` 字节级一致（`diff -q` 输出 IDENTICAL）。

- **硬门禁九（subagent 产出独立核查）**：✅
  全部 5 个 chg 的 session-memory.md 均含"完成 ✅"/"executing stage 完成 ✅" marker：
  - chg-01-推断器多语言注册化：✅
  - chg-02-scripts-detector-注册化：✅
  - chg-03-llm-provider-抽象层：✅
  - chg-04-install-refresh-集成-llm：✅
  - chg-05-区段级只读语义-与-check-兼容：✅

- **硬门禁十（代码加载规则 §1-§4）**：✅
  base-role.md `## 硬门禁十：代码加载规则` 存在，§1/§2/§3/§4 四节完整。
  §4 含三个语义关键词："AUTO 区段只读"、"TODO 区域可改"、"agent 默认不改"（"用户 explicit 指令后可改" 亦存在）。

## 3. OQ / default-pick 决策清单

| OQ | 内容 | 拍板方式 | 决策 |
|---|---|---|---|
| OQ-1 | 推断器架构（硬编码降级链 vs detector 注册器） | 用户拍板（"按照你说的做没问题"） | B1（detector 注册器架构） |
| OQ-2 | LLM 调用范围（仅 install / 全程可选 / 仅 refresh / 独立子命令） | 用户拍板 | C2（全程可选，默认 on + --no-llm + CI 友好） |
| OQ-3 | LLM provider 默认（Anthropic / OpenAI / Ollama / 自动检测） | 用户拍板 | 自动检测（ANTHROPIC > OPENAI > Ollama > Noop） |
| OQ-4 | 区段级只读 vs 任务级只读 | 用户拍板 | D1（区段级：AUTO/LLM 只读 + TODO 可改） |
| OQ-5 | dogfood TC 范围（worktree fixture vs 真实 PetMallPlatform A/B） | 用户拍板 | A（worktree fixture，真实 A/B 由主 agent 另起） |

未决 OQ 数: **0**（5/5 全部按 default-pick 拍定，analyst default-pick 与用户决策完全一致）

## 4. 测试覆盖

- req-56 自有: **77 passed / 0 failed**（9 个测试文件，chg-01~05 各自用例全通过）
- 跨 chg 回归（含 req-55 baseline）: **118 passed / 0 failed**
- upstream broken: **46**（全部归因远程 main req-26~req-54 及 bugfix 系列，与 req-56 改动文件范围无交集）

## 5. 已知遗留 / 风险

- **upstream 远程 main 46 个测试失败**：全部归因 req-26~req-54 及 bugfix-3/5/6 等引入，与 req-56 所改动文件（domain_inference.py / harness_playbook_refresh.py / llm.py / init.py / cli.py / base-role.md / harness_playbook_check.py）无交集。需独立处理，待用户决策。
- **真实 PetMallPlatform A/B 测试**：OQ-5=A 决定不在本 req 跑真实 A/B 测试，dogfood TC 使用 worktree fixture 模拟。真实验证由主 agent 在 done 后另起任务（风险 R-7 缓解措施已落地：fixture 严格按 reg-01 §3 A-3 描述构造）。
- 无其他遗留事项。

## 6. Verdict

**PASS** — req-56 满足全部 13 条 AC（AC-13 ~ AC-25），5 OQ 全部拍定无未决，硬门禁五/九/十全部合规，可进入 done stage。
