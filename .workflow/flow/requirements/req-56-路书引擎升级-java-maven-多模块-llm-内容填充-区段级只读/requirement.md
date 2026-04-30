---
id: req-56
title: "路书引擎升级——Java/Maven 多模块 + LLM 内容填充 + 区段级只读"
created_at: 2026-04-30
operation_type: requirement
stage: analysis
baseline_requirement: req-55
trigger_regression: reg-01
---

> 关联：req-55（项目路书Playbook体系-项目地图+代码导航）作为 baseline；reg-01（chg-03/04 Java/Maven 项目盲点 + LLM 填骨架决策反转）作为触发器。本 req 是 req-55 done verdict=PASS 后的 dogfood 衍生升级——req-55 5 chg 落地的契约 / 实现 / 测试不重写、只扩展 / 修订；reg-01 三份诊断工件（regression.md / analysis.md / decision.md）作为本 req spec 输入的单一权威源。

## Goal

### 问题

req-55 路书引擎在 Java/Maven 多模块项目（PetMallPlatform 类，主流企业 Java/Spring Boot 栈）实测**零适配**：

- 维度 A（推断器盲点）：`domain_inference.py` 4 级降级链假设 Python/JS 单仓 / 单包结构，未识别"顶层平级 platform-* 模块根 + `pom.xml <modules>`"惯例，PetMallPlatform 5 个真业务模块（platform-admin / platform-common / platform-modules / platform-extend / platform-demo-ui）被忽略，错把 `app/logs` 推成业务领域。
- 维度 B（SCRIPTS detector 盲点）：`harness_playbook_refresh.py::_scan_scripts` 只识别 pyproject / package.json / Makefile，对 Maven lifecycle / Gradle / Cargo / .NET 命令零支持，runbook AUTO:SCRIPTS 区段空。
- 维度 C（spec 决策反转）：原 spec §四"不调 LLM，纯静态分析"导致骨架 90% 是 `<!-- TODO -->`，对人不友好，用户首装无法看到有意义初稿。
- 维度 D（区段级只读语义松动）：base-role.md 硬门禁十 §4 "不要修改 `artifacts/project/playbooks/` 下任何文件"在维度 C 反转后字面义不再成立，需细化为"AUTO 区段只读 + TODO 人写区域用户可改"的区段级语义。

### 交付能力（4 件一体升级）

1. **多语言推断器（注册化重构）**：`domain_inference.py` 由 4 级降级链重构为 detector 注册器架构（OQ-1 = B1），原生注册 Python / Node.js / Java-Maven / Gradle / Cargo workspace / .NET sln 6 类 detector，每类独立检测多模块结构；保留兜底 fallback 与 `--domains` last-resort flag。PetMallPlatform 类 fixture 命中 5 个真业务模块。
2. **多语言 SCRIPTS detector（注册化重构）**：`harness_playbook_refresh.py::_scan_scripts` 由 if-elif 链重构为按文件类型分发的 detector 注册器，覆盖 Maven lifecycle（`mvn clean install` / `mvn test` / `mvn package` / `mvn spring-boot:run`） / Gradle（`./gradlew build` / `./gradlew test`） / Cargo（`cargo build` / `cargo test`） / .NET（`dotnet build` / `dotnet test`）。
3. **LLM provider 抽象层 + install / refresh 集成**：新增 `src/harness_workflow/playbook/llm.py`，定义 `LLMProvider` 抽象基类与 4 个具体实现（Anthropic / OpenAI / Ollama / Noop）；按 env 自动检测 provider 优先级（OQ-3 default = 自动检测）；`init_playbook` 与 `playbook_refresh` 在生成骨架后调 LLM 填充业务内容（overview 业务描述 / domains README 职责 / code-map 关键词 / architecture 技术决策摘要）；CLI flag `--no-llm` 显式跳过（CI 兼容；OQ-2 = C2 全程可选）；网络错重试 → fallback Noop。
4. **区段级只读语义修订 + check 兼容**：base-role.md 硬门禁十 §4 改写为"`<!-- AUTO:* -->` 区段只读（agent 与用户均不直接编辑） + 区段外 TODO / 人写区域用户可改（agent 默认不改，用户 explicit 后可改）"（OQ-4 = D1 区段级）；`harness_playbook_check.py` AUTO 区段哈希漂移检测沿用，区段外不报警；`playbook-check` 注释更新但行为零变化。

### 与 req-55 baseline 的关系

- **不动**：req-55 done commit / acceptance verdict / 12 AC / 5 OQ 决策记录（保留 history）；req-55 inputs/initial-spec.md（用户原始 spec，§四"不调 LLM"原文作为反转留 history 的对比基线）；req-55 已落地 5 chg 的契约文档（`playbook-layout.md`）。
- **扩展 / 修订**：req-55 chg-03 / chg-04 / chg-05 实现层（推断器 / SCRIPTS detector / check 注释），按本 req 5 chg 在原文件上做注册化重构 + LLM 集成；req-55 chg-02 落地的 base-role.md 硬门禁十 §4 文字（仅文字精修，硬门禁号继续沿用 #10）。

## Scope

### Included（5 chg DAG，详见 §Split Rules）

- **chg-01（推断器多语言注册化）**：`src/harness_workflow/playbook/domain_inference.py` 由硬编码 4 级降级链重构为 detector 注册器架构；新增 6 类 detector（PythonModulesDetector / PythonDomainsDetector / AppDirDetector / PythonPackageDetector / **MavenMultiModuleDetector** / **GradleMultiModuleDetector** / **CargoWorkspaceDetector** / **DotNetSlnDetector**）；每个 detector 独立优先级 + 独立 stdout 命中级别打印；新增 last-resort `harness install --domains <list>` 显式指定（A4 兜底）；保留 4 级降级语义作为 detector 优先级排序的兼容路径。pytest +5~8 TC（含 PetMallPlatform-like fixture）。
- **chg-02（SCRIPTS detector 注册化）**：`src/harness_workflow/tools/harness_playbook_refresh.py::_scan_scripts` 由 if-elif 链重构为按文件类型分发的 detector 注册器；既有 Python / Node.js / Makefile detector 不变，新增 Maven / Gradle / Cargo / .NET detector；每类 detector 独立返回命令列表 + 一句话注释；pytest +4~6 TC。
- **chg-03（LLM provider 抽象层）**：新建 `src/harness_workflow/playbook/llm.py` 与 `src/harness_workflow/playbook/prompts/` 目录；定义 `LLMProvider` 抽象基类（接口 `generate_overview / generate_domain_description / generate_keywords / generate_tech_decisions`）；4 个具体 provider 实现（AnthropicProvider 走 `ANTHROPIC_API_KEY` env / OpenAIProvider 走 `OPENAI_API_KEY` env / OllamaProvider 走本地 `localhost:11434` / NoopProvider 兜底）；自动检测顺序按 env API key 探测，无 key 退 Noop；3-5 份提示词模板 markdown 文件；pytest +8~12 TC（含 4 provider 单元 + mock 网络 + retry / fallback）。
- **chg-04（install / refresh 集成 LLM）**：修改 `src/harness_workflow/playbook/init.py` 与 `src/harness_workflow/tools/harness_playbook_refresh.py`，在骨架生成 / refresh 后调 LLM 填充业务内容（overview 业务描述 / domains README 职责 / code-map 关键词 / architecture 技术决策）；修改 `src/harness_workflow/cli.py` install / playbook-refresh 子命令加 `--no-llm` flag（与 LLM 调用互斥，env CI=true 自动 on）；LLM 调用失败时重试 1 次 → fallback Noop（不阻塞主流程，stderr WARN）；pytest +5~7 TC。
- **chg-05（区段级只读语义修订 + check 兼容）**：`.workflow/context/roles/base-role.md` 硬门禁十 §4 文字精修（"AUTO 区段只读 + TODO 人写区域用户可改 + agent 默认不改 / 用户 explicit 后可改"）；`harness_playbook_check.py` 注释更新（行为不变，AUTO 区段哈希漂移检测沿用）；`.workflow/flow/playbook-layout.md` 同步注释段（不改契约骨架）；README.md / SKILL.md mirror 同步行；pytest +2~3 TC（base-role 文字 lint + check 行为不变断言）。

### Excluded（明示不做）

- **不重写 chg-01 playbook-layout.md 骨架契约**：路书目录结构 / 4 顶层文件 / domains 4 件套 / AUTO 区段定界规约**沿用** req-55 chg-01 落地版本；本 req 仅在第 §4 节附加"区段级只读"注释段。
- **不改 base-role.md 其他硬门禁**：硬门禁一 / 二 / 三 / 四 / 六 / 七 / 九 文字零变化；只改硬门禁十 §4。
- **不撤回 req-55 verdict**：req-55 已 done verdict=PASS / 12 AC PASS / 5 OQ 拍板记录保留 history；req-56 引用 req-55 作为 baseline。
- **不修改 req-55 inputs/initial-spec.md**：用户原始 spec §四"不调 LLM"作为反转留 history 的对比基线，文件只读。
- **不修改 req-55 acceptance/checklist.md / test-report.md**：保护 done 终局。
- **不集成 LLM 训练 / fine-tune**：仅 inference；不写 prompt engineering 细则进 spec（细则归 chg-03 plan.md）；不引 LangChain / Anthropic SDK 之外的高阶框架。
- **不引入 PreToolUse hook 拦截 agent 写路书**：硬门禁十文字 + chg-05 playbook-check CI 漂移检测兜底已足够（OQ-5=A 沿用 req-55）。
- **不在本 req 跑真实 PetMallPlatform A/B 测试**：dogfood TC 在 worktree fixture 内模拟 PetMallPlatform 结构（OQ-5 default = A worktree fixture），真实 A/B 测试由主 agent 在路由后另起任务做。

## Acceptance Criteria

> 所有 AC 必须有可验证手段（文件存在性 / grep 命中 / pytest 用例 / CLI exit code），无空话条目。AC 编号沿 req-55（AC-13 起避免冲突）。

- **AC-13（PetMallPlatform-like fixture 推断器命中正确）**：构造 fixture（`platform-admin / platform-common / platform-modules / platform-extend / platform-demo-ui` 5 个顶层目录 + 父 `pom.xml <modules>` 列出 5 模块 + `app/logs` 噪声目录），跑 `infer_domains(root)` 返回 `mode='maven_multi_module'`、`domains=['platform-admin', 'platform-common', 'platform-modules', 'platform-extend', 'platform-demo-ui']`。验证：pytest TC `tests/test_domain_inference_multi_lang.py::test_petmall_like_maven_modules` PASS；stdout 含 `domain inference: matched 'maven_multi_module'`。
- **AC-14（Maven SCRIPTS detector 命中 lifecycle 命令）**：fixture 含 `pom.xml`（带 `<artifactId>` + `<plugins>` 段含 `spring-boot-maven-plugin`），跑 `_scan_scripts(root)` 返回行含 `mvn clean install` / `mvn test` / `mvn package` / `mvn spring-boot:run`（≥ 4 行）。验证：pytest TC `tests/test_playbook_refresh_multi_lang.py::test_maven_scripts_detector` PASS。
- **AC-15（Gradle / Cargo / .NET SCRIPTS detector 各命中 ≥ 1 命令）**：3 类 fixture 各对应一 TC，分别断言 `./gradlew build` / `cargo build` / `dotnet build` 在输出中。验证：pytest TC ≥ 3 条 PASS。
- **AC-16（LLM provider 抽象支持 4 种 + env 自动检测）**：`src/harness_workflow/playbook/llm.py` 暴露 `LLMProvider` 抽象基类 + `AnthropicProvider` / `OpenAIProvider` / `OllamaProvider` / `NoopProvider` 4 实现 + `auto_detect_provider() -> LLMProvider` 工厂；按 env 优先级（`ANTHROPIC_API_KEY` > `OPENAI_API_KEY` > Ollama localhost ping > Noop）选择。验证：pytest 4 TC mock env 各场景，断言返回正确 provider 类型。
- **AC-17（`harness install --no-llm` 跳过 LLM 调用）**：在 fixture 跑 `python3 -m harness_workflow.cli install --root <tmp> --no-llm`，subprocess stdout 含 `playbook initialized` 且 **不**含 `[llm]`；overview.md / domains README 内容保持 `<!-- TODO -->` 占位（与 req-55 baseline 一致）。验证：pytest dogfood TC PASS。
- **AC-18（默认 LLM 填充 overview / domains README / code-map 关键词）**：在 fixture 跑 `python3 -m harness_workflow.cli install --root <tmp>`（无 `--no-llm`，预置 mock LLM provider 返回固定文本），完成后 `overview.md` 业务描述段、各 `domains/*/README.md` 职责段、`code-map.md` 关键词段含非 TODO 文本（grep `<!-- TODO -->` 在这三处的命中数 ≤ 1，对照 baseline 是 ≥ 4）。验证：pytest dogfood TC PASS。
- **AC-19（base-role 硬门禁十 §4 区段级只读文字落地）**：`grep -A20 '^### 4. 不该做的事' .workflow/context/roles/base-role.md` 输出含 "AUTO 区段只读" / "TODO 区域可改" / "agent 默认不改 / 用户 explicit 后可改"三个语义关键词；硬门禁十总数仍为 1 个（不新增编号）。验证：pytest TC `tests/test_baserole_section_readonly.py::test_section_level_readonly_wording` PASS。
- **AC-20（playbook-check 兼容新语义：AUTO 区段漂移仍检 + 区段外不报警）**：构造 fixture 把 TODO 区段内容人工改写（区段外编辑），跑 `harness playbook-check`，exit 0 / 不报告漂移；同 fixture 把 AUTO 区段内 1 行删掉再跑，exit ≠ 0 / 报告 `AUTO_SECTION_HASH_DRIFT`。验证：pytest TC ≥ 2 条 PASS。
- **AC-21（dogfood 端到端流程：PetMallPlatform 类 fixture 跑 install + refresh + check）**：在 worktree 内构造 PetMallPlatform-like fixture，subprocess 跑完整 3 步（install → refresh → check），断言：(a) install 命中 maven_multi_module 推断 + LLM 填充非空（mock provider）；(b) refresh 后 runbook AUTO:SCRIPTS 区段含 ≥ 4 行 mvn 命令；(c) check exit 0；(d) `runtime.yaml` stage 字段存在；(e) `feedback.jsonl` 事件数 ≥ 3。验证：pytest dogfood TC `tests/test_petmall_fixture_dogfood.py::test_petmall_full_pipeline` PASS。
- **AC-22（现有 41 TC 全部继续 PASS）**：req-55 落地的 41 条测试用例（test_playbook_install / test_playbook_refresh / test_playbook_check 各文件）在本 req 5 chg 完成后继续全 PASS / 0 fail。验证：`pytest tests/test_playbook_*.py -v` 输出 ≥ 41 passed / 0 failed。
- **AC-23（全量回归零引入 fail）**：本 req 完成后 `pytest tests/ -q` fail 数 ≤ baseline（req-55 done 时基线 57 fail），不引入新 fail；新增用例数 ≥ 19（每 chg ≥ 2 + dogfood TC ≥ 2）。验证：testing stage 跑 pytest 看真实数字。
- **AC-24（LLM 调用失败兜底）**：mock LLM provider 抛 `NetworkError`，install / refresh 主流程不阻塞，stderr 含 `[llm] WARN: provider failed, falling back to Noop`，exit 0；overview / domains README 保持 TODO 占位。验证：pytest TC `tests/test_llm_fallback.py::test_llm_network_error_fallback` PASS。
- **AC-25（hardgate：新契约 lint）**：新增 `harness validate --contract playbook-multi-lang` 子契约（验证：(1) `domain_inference.py` 含 ≥ 6 detector 注册；(2) `_scan_scripts` 含 ≥ 4 detector 分支；(3) `llm.py` 含 4 provider 实现 + auto_detect_provider 工厂）exit 0；既有 `harness validate --contract artifact-placement` / `--human-docs` 继续 exit 0。验证：CLI 实跑三契约。

## Split Rules

### 拆分原则（基于 reg-01 decision.md §4 chg DAG 草案 + analyst 实际审视）

1. **按交付物层次**：底层抽象（chg-01 推断器 / chg-02 SCRIPTS detector / chg-03 LLM provider）独立可并行 → 中层集成（chg-04 install/refresh 调用 LLM）依赖 chg-03 → 顶层语义（chg-05 base-role 区段级只读 + check 兼容）依赖 chg-03/04 落地后的 LLM 写入面。
2. **依赖单向**：chg-01 / chg-02 / chg-03 三者**完全独立**，可并行执行；chg-04 依赖 chg-03（LLM provider 已就绪）；chg-05 依赖 chg-03/04 落地后才能验证"区段外 LLM 写入 + AUTO 区段哈希仍检"语义；不允许反向依赖。
3. **粒度均衡**：每个 chg 落地代码 + 测试在 1 个 stage（≤ 1.5 day）完成；chg-03 / chg-04 是相对大改（LLM provider + 集成），其余三 chg 是中小改。
4. **dogfood 内置**：每个 chg 必含 ≥ 1 条 dogfood TC（subprocess 实跑 CLI 入口 + tmpdir + stdout 断言 + runtime stage / feedback.jsonl 断言）；chg-04 dogfood TC 必含 PetMallPlatform-like fixture。

### chg DAG（5 chg）

```
chg-01（推断器多语言注册化） ──┐
chg-02（SCRIPTS detector 注册化） ─┼──> chg-04（install/refresh 集成 LLM） ──> chg-05（区段级只读语义 + check 兼容）
chg-03（LLM provider 抽象层） ─────┘
```

- chg-01 / chg-02 / chg-03 可并行（无文件冲突，分别落 domain_inference.py / harness_playbook_refresh.py / 新建 llm.py）；
- chg-04 等 chg-03 落地后做（需 LLMProvider 抽象就绪）；
- chg-05 最后做（需 chg-04 落地后才能验证区段外 LLM 写入 + 区段外不报警语义）。

### 风险与缓解

- **风险 R-5（推断器注册化重构破坏 req-55 4 级降级语义）**：chg-01 重构需保持 Python `src/modules/*` / `src/domains/*` / `app/*` / `src/{pkg}/*次级模块` 4 类 detector 优先级与 req-55 baseline 行为一致，否则破坏 41 TC 现有断言。**缓解**：detector 注册器架构设 `priority` 字段，让 4 类 Python detector 与 req-55 4 级降级排序一致；chg-01 plan.md 测试用例设计中显式列出"baseline 兼容 TC"（沿用 req-55 TC-07~10），新增 TC 不删旧 TC。
- **风险 R-6（LLM provider 网络抖动 / API key 缺失导致 install 不可用）**：CI 环境通常无 LLM API key，install 默认走 LLM 路径会触发 fallback；本地用户网络抖动也会失败。**缓解**：chg-03 provider 自动检测无 key 退 Noop；chg-04 LLM 调用 wrapper 含 1 次 retry + 2s timeout + fallback Noop；env `CI=true` 自动设置 `--no-llm`；所有路径异常 stderr WARN 但主流程 exit 0。
- **风险 R-7（dogfood TC 在 worktree fixture vs 真实 PetMallPlatform A/B 偏差）**：fixture 模拟可能与真实 PetMallPlatform 结构有偏差，导致 fixture PASS 但真实 fail。**缓解**：fixture 严格按 reg-01 regression.md §3 维度 A 原始证据 A-3 描述的 PetMallPlatform 结构构造（5 顶层模块 + 父 pom.xml `<modules>` + `app/logs` 噪声）；OQ-5 = A 决定不在本 req 跑真实 A/B（避免离开 worktree），真实验证由主 agent 路由后另起任务。
- **风险 R-8（区段级只读语义松动后 agent 误改路书）**：硬门禁十 §4 由"全文件只读"改为"AUTO 只读 + TODO 可改"，可能让 agent 在没有用户 explicit 指示时也去改 TODO 区段。**缓解**：chg-05 文字精修保留"agent 默认不改"硬约束（仅"用户 explicit 后可改"是新增豁免）；chg-05 playbook-check 区段外漂移可由后续 sug 添加（本 req 不引入区段外检测）。

### 估算

| chg | 估算 | 关键交付 |
|-----|------|---------|
| chg-01（推断器多语言注册化） | 1.5 day | `domain_inference.py` 重构为 detector 注册器 + 6 类 detector + last-resort `--domains` flag + pytest 5~8 TC |
| chg-02（SCRIPTS detector 注册化） | 1 day | `harness_playbook_refresh.py::_scan_scripts` 重构 + Maven/Gradle/Cargo/.NET detector + pytest 4~6 TC |
| chg-03（LLM provider 抽象层） | 1.5 day | `playbook/llm.py` + `playbook/prompts/*.md` + 4 provider + 自动检测 + pytest 8~12 TC |
| chg-04（install/refresh 集成 LLM） | 1 day | `init.py` + `harness_playbook_refresh.py` 集成调用 + `cli.py` `--no-llm` flag + pytest 5~7 TC（含 PetMallPlatform-like dogfood） |
| chg-05（区段级只读语义 + check 兼容） | 0.5 day | `base-role.md` §4 文字精修 + `harness_playbook_check.py` 注释 + `playbook-layout.md` 注释段 + README/SKILL mirror + pytest 2~3 TC |

总计：5.5 day（线性）/ 3.5 day（chg-01/02/03 并行 + chg-04 + chg-05）。
