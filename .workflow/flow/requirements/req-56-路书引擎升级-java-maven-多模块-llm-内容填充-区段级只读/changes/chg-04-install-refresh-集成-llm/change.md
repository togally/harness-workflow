---
id: chg-04
title: "install / refresh 集成 LLM（默认开启 / --no-llm 关闭 + 失败 fallback）"
req: req-56
created_at: 2026-04-30
---

## 目标

在 `init_playbook`（install 路径）与 `playbook_refresh`（refresh 路径）中集成 chg-03（LLM provider 抽象层）落地的 `auto_detect_provider()`，调 LLM 填充骨架业务内容（overview 业务描述 / domains README 职责 / code-map 关键词 / architecture 技术决策摘要），让 reg-01（chg-03/04 Java/Maven 项目盲点 + LLM 填骨架决策反转） 维度 C "首装看到有意义初稿"诉求落地（OQ-2 = C2 全程可选 + 默认开启 local / `--no-llm` 关闭 CI / env CI=true 自动 off）。

## 范围（Scope）

### Included

- **修改 `src/harness_workflow/playbook/init.py::init_playbook`**：
  - 新增 `no_llm: bool = False` 参数；
  - 在 `render_skeleton(root, domains)` 之后新增 LLM 填充阶段：若 `no_llm=False` 且 env `CI` 不等于 `'true'`，调 `llm = auto_detect_provider()` + 各方法填充对应骨架内容；NoopProvider 命中时跳过填充（保留 TODO 占位，与 baseline 一致）；
  - 新增 `_fill_with_llm(root, domains, llm)` helper：依次调 `llm.generate_overview` / `generate_domain_description` / `generate_keywords` / `generate_tech_decisions`，把返回值写入对应文件的对应段（用区段标记 `<!-- LLM:OVERVIEW_DESC -->...<!-- /LLM:OVERVIEW_DESC -->`，与 AUTO 区段同语义但单独命名空间，方便 chg-05 区段级只读区分 + check 检测）。
- **修改 `src/harness_workflow/tools/harness_playbook_refresh.py::playbook_refresh`**：
  - 新增 `no_llm: bool = False` 参数；
  - 在所有 AUTO 区段刷新完成后，新增 LLM 填充阶段（仅刷新 `<!-- LLM:* -->` 区段，沿用 AUTO 区段替换 helper `replace_auto_section`，但 marker 前缀改 `LLM:`）；
  - LLM 调用失败兜底：每个 `llm.generate_*` 调用包裹 try-except，失败时 stderr `[llm] WARN: provider failed, falling back to Noop` + 保留原区段内容（不破坏既有数据）+ 主流程 exit 0。
- **修改 `src/harness_workflow/cli.py`**：
  - install_parser 加 `--no-llm` flag（与 chg-03 abstract 联动）；
  - playbook-refresh_parser 加 `--no-llm` flag；
  - 两条命令的 handler 透传 `no_llm` 到 init_playbook / playbook_refresh；
  - 自动检测 env CI=true → 强制 `no_llm=True`（CI 兼容 + spec §四原承诺保留）。
- **修改 `src/harness_workflow/playbook/skeleton.py`**：
  - 在 `_OVERVIEW_TEMPLATE` / `_ARCHITECTURE_TEMPLATE` / `_domain_readme_template` / `_CODE_MAP_TEMPLATE` 4 模板中追加 `<!-- LLM:* -->` / `<!-- /LLM:* -->` 区段定界（与 AUTO 区段同语法但 marker 前缀 LLM）；
  - 新增 5 类 LLM marker：`LLM:OVERVIEW_DESC` / `LLM:TECH_DECISIONS` / `LLM:DOMAIN_DESC` / `LLM:KEYWORDS` / `LLM:CODE_MAP_KEYWORDS`。
- **新增 pytest 用例 ≥ 5 条**（`tests/test_install_refresh_llm_integration.py`）：
  - `test_install_calls_llm_with_mock_provider`（mock auto_detect_provider 返回 mock provider，断言 4 method 被调）
  - `test_install_no_llm_flag_skips_llm`（`--no-llm` flag 透传 → mock provider 0 调用）
  - `test_install_ci_env_auto_disables_llm`（env CI=true → 自动 no_llm=True）
  - `test_llm_network_error_fallback`（mock provider 抛 NetworkError → stderr WARN + exit 0）
  - `test_refresh_llm_section_replaces_correctly`（fixture 含 LLM:* 区段，refresh 后区段内容由 mock provider 返回值替换）
- **dogfood TC**（`tests/test_petmall_fixture_dogfood.py::test_petmall_full_pipeline`）：tmp_path + PetMallPlatform-like fixture（5 顶层模块 + 父 pom.xml `<modules>` + spring-boot-maven-plugin） + subprocess 完整 3 步（install → refresh → check），断言：
  1. install 命中 `maven_multi_module` 推断（chg-01 落地） + LLM 填充非空（mock provider 返回固定文本）
  2. refresh 后 runbook AUTO:SCRIPTS 含 ≥ 4 行 mvn 命令（chg-02 落地）
  3. check exit 0（chg-05 兼容验证）
  4. runtime.yaml stage 字段存在 + feedback.jsonl 事件数 ≥ 3

### Excluded

- 不实现 LLM 调用结果缓存（落 sug 池）。
- 不动 chg-01 推断器 / chg-02 SCRIPTS detector / chg-03 provider 实现（仅集成调用）。
- 不引入 streaming / 进度条（一次性等待 LLM 返回，timeout 设 30s）。
- 不做 prompt engineering 微调（按 chg-03 模板原样调用）。

## 依赖

- 上游：chg-01（推断器多语言注册化，输出领域名作为 LLM 输入）+ chg-02（SCRIPTS detector 注册化，输出脚本列表作为 LLM 上下文）+ chg-03（LLM provider 抽象层，提供 auto_detect_provider）。
- 下游：chg-05（区段级只读语义 + check 兼容）依赖本 chg 落地的 `<!-- LLM:* -->` 区段写入面，验证"区段外可改 + 区段内只读"语义。

## 验收（Acceptance）

- AC-17（`harness install --no-llm` 跳过 LLM 调用）：subprocess 跑 install + `--no-llm` → stdout 不含 `[llm]` 前缀；overview / domains README 保持 TODO 占位。
- AC-18（默认 LLM 填充三处骨架内容）：subprocess 跑 install（mock provider 返回固定文本） → overview / domains README / code-map 三处 grep `<!-- TODO -->` 命中数 ≤ 1（baseline 是 ≥ 4）。
- AC-21（dogfood 端到端流程：PetMallPlatform 类 fixture 跑 install + refresh + check）。
- AC-24（LLM 调用失败兜底）：mock provider 抛 NetworkError → stderr WARN + exit 0 + 区段保留原内容。
- AC-22（现有 41 TC 不破坏）+ AC-23（全量回归零引入 fail）。

## 风险与缓解

- **风险 R-15（LLM 调用慢导致 install 体验差）**：默认开启 LLM 填充会让 install 从亚秒级跑到 10-30 秒。**缓解**：每个 LLM 调用 timeout 设 30s（chg-03 provider 内部强制）；stdout 进度提示 `[llm] generating overview...` / `[llm] generating domain descriptions (3/5)...`；env `HARNESS_LLM_TIMEOUT` 可覆盖。
- **风险 R-16（mock provider 在测试中泄漏成真实调用）**：测试时若 ANTHROPIC_API_KEY 在 CI 真实存在，mock 失效会触发真实 LLM 调用。**缓解**：所有 TC 显式 monkeypatch env 清空 LLM API key + monkeypatch `auto_detect_provider` 返回 NoopProvider 或 mock；新增 `tests/conftest.py::ensure_no_real_llm` autouse fixture 兜底。
- **风险 R-17（LLM 区段标记与 AUTO 区段冲突）**：用 `<!-- LLM:* -->` 与 `<!-- AUTO:* -->` 双 marker 系统，可能让 chg-05 playbook-check 漂移检测混淆。**缓解**：marker 命名空间显式分离（`LLM:OVERVIEW_DESC` vs `AUTO:STACK`），chg-05 哈希漂移检测沿用正则 `<!-- (AUTO|LLM):(\w+) -->` 同时支持两类区段，CI 行为统一。
