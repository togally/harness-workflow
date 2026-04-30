---
id: chg-03
title: "LLM provider 抽象层（Anthropic / OpenAI / Ollama / Noop + 自动检测）"
req: req-56
created_at: 2026-04-30
---

## 目标

新建 `src/harness_workflow/playbook/llm.py` 与 `src/harness_workflow/playbook/prompts/` 目录，定义 `LLMProvider` 抽象基类与 4 个具体实现（Anthropic / OpenAI / Ollama / Noop），按 env 自动检测 provider 顺序（OQ-3 default = 自动检测），承载 reg-01（chg-03/04 Java/Maven 项目盲点 + LLM 填骨架决策反转） 维度 C "spec 不调 LLM 决策反转"的核心抽象层；本 chg 仅落 provider 层，不集成到 install / refresh（chg-04 负责集成）。

## 范围（Scope）

### Included

- **新建 `src/harness_workflow/playbook/llm.py`**：
  - `LLMProvider` 抽象基类（`abc.ABC`），定义 4 个抽象方法：
    - `generate_overview(project_name: str, tech_stack: list[str], domains: list[str]) -> str`：生成 overview.md 业务描述段
    - `generate_domain_description(domain_name: str, code_files: list[str]) -> str`：生成 domains/{name}/README.md 职责段
    - `generate_keywords(domain_name: str, code_files: list[str]) -> list[str]`：生成 code-map.md 关键词
    - `generate_tech_decisions(tech_stack: list[str], scripts: list[str]) -> str`：生成 architecture.md 技术决策摘要
  - 4 个具体实现：
    - `AnthropicProvider`：走 `ANTHROPIC_API_KEY` env，调 `anthropic` SDK（dependency optional install）；模型默认 `claude-3-5-haiku-latest`（成本低快）；加载 `prompts/anthropic-*.md` 提示词模板
    - `OpenAIProvider`：走 `OPENAI_API_KEY` env，调 `openai` SDK；模型默认 `gpt-4o-mini`
    - `OllamaProvider`：走 `OLLAMA_HOST` env（默认 `http://localhost:11434`），HTTP POST `/api/generate`；模型默认 `llama3.2`；零外部依赖（用 `urllib.request`，不引 `requests`）
    - `NoopProvider`：所有方法返回固定 sentinel string `"<!-- LLM disabled (Noop provider) -->"`，用于 CI / `--no-llm` / 无 API key 兜底
- **`auto_detect_provider() -> LLMProvider` 工厂函数**：按以下优先级探测，返回第一个可用 provider：
  1. `ANTHROPIC_API_KEY` env 存在 → AnthropicProvider
  2. `OPENAI_API_KEY` env 存在 → OpenAIProvider
  3. Ollama localhost:11434 ping 通（HTTP HEAD 1s timeout） → OllamaProvider
  4. 全部失败 → NoopProvider（stderr WARN 一次）
- **新建 `src/harness_workflow/playbook/prompts/` 目录**：3-5 份提示词模板 markdown 文件：
  - `prompts/overview.md`：项目概览生成模板（input 占位符：project_name / tech_stack / domains）
  - `prompts/domain-description.md`：领域职责生成模板（input：domain_name / code_files）
  - `prompts/keywords.md`：关键词提取模板（input：domain_name / code_files）
  - `prompts/tech-decisions.md`：技术决策摘要模板（input：tech_stack / scripts）
- **`pyproject.toml` optional dependencies**：新增 `[project.optional-dependencies]` `llm = ["anthropic>=0.30", "openai>=1.0"]`（用户按需 `pip install harness-workflow[llm]`，不强制依赖）；Ollama / Noop 零依赖。
- **新增 pytest 用例 ≥ 8 条**（`tests/test_llm_provider.py`）：
  - `test_noop_provider_returns_sentinel`（4 method 各返回 sentinel）
  - `test_anthropic_provider_mock_response`（mock `anthropic.Anthropic` SDK，断言 prompt 拼接正确 + 返回值传递）
  - `test_openai_provider_mock_response`（mock `openai.OpenAI` SDK）
  - `test_ollama_provider_mock_http`（mock urllib，断言 POST 端点 / payload）
  - `test_auto_detect_anthropic_priority`（mock env 含 ANTHROPIC_API_KEY → 返回 AnthropicProvider）
  - `test_auto_detect_openai_fallback`（无 ANTHROPIC_API_KEY 但有 OPENAI_API_KEY → OpenAIProvider）
  - `test_auto_detect_ollama_ping_pass`（mock urllib HEAD 200 → OllamaProvider）
  - `test_auto_detect_noop_fallback`（全部 mock 失败 → NoopProvider + stderr WARN）

### Excluded

- 不集成到 `init_playbook` / `playbook_refresh`（chg-04 负责）。
- 不调真实 LLM API（所有 TC mock）。
- 不实现 streaming 输出（一次性 generate）。
- 不实现 LLM 调用缓存（chg-04 / 后续 sug 可加）。
- 不实现 prompt 长度自动截断（提示词模板设计时控制 ≤ 2k tokens）。

## 依赖

- 上游：无（独立新建）。
- 下游：chg-04（install/refresh 集成 LLM）依赖本 chg 落地的 `LLMProvider` 抽象 + `auto_detect_provider()` 工厂。

## 验收（Acceptance）

- AC-16（LLM provider 抽象支持 4 种 + env 自动检测）：`llm.py` 暴露 `LLMProvider` 抽象基类 + 4 实现 + `auto_detect_provider()`；按 env 优先级探测正确。pytest 4 mock TC PASS。
- AC-25（hardgate `playbook-multi-lang` 契约 lint）：契约校验 `llm.py` 含 4 provider 实现 + auto_detect_provider 工厂。
- AC-23（全量回归零引入 fail）。

## 风险与缓解

- **风险 R-12（anthropic / openai SDK 必装假设破坏 CI 兼容）**：CI 环境通常不装 LLM SDK；若 `import anthropic` 在模块顶层就 fail，整个 install 报错。**缓解**：AnthropicProvider / OpenAIProvider 内 import 放在方法内部（`def generate_overview` 内 `import anthropic`），lazy import；`auto_detect_provider` 探测时 `try: import anthropic; ... except ImportError: skip`，无 SDK 视为该 provider 不可用。
- **风险 R-13（Ollama localhost ping 1s timeout 在慢机器误判）**：开发机网络抖动可能导致 ping 失败回 Noop。**缓解**：Ollama detector 仅 1s timeout，失败回退即可（用户可显式 `LLM_PROVIDER=ollama` env 强制覆盖自动检测）；本 chg AC-16 不强制 Ollama 必命中，仅断言"按优先级正确选 provider"语义。
- **风险 R-14（提示词模板过长导致 token 超限）**：code_files 列表超 50 条时 prompt 过长。**缓解**：每个 provider 内部对 input list 做截断（`code_files[:30]`）；prompt 模板末尾加 `（截断显示前 30 个文件）`说明。
