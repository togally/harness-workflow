---
id: chg-03
title: "LLM provider 抽象层（Anthropic / OpenAI / Ollama / Noop + 自动检测）"
req: req-56
created_at: 2026-04-30
---

## 1. 执行步骤

1. **读上下文**：读 reg-01 analysis.md §4（维度 C 根因 + 候选 C2 全程可选 + §4.4 LLM provider 抽象层架构候选）、reg-01 decision.md §5 OQ-3 default-pick = 自动检测。
2. **建 prompts 目录**：`mkdir -p src/harness_workflow/playbook/prompts/`，创建 4 份模板 markdown 文件（overview.md / domain-description.md / keywords.md / tech-decisions.md），每份含 `{placeholder}` 占位符 + 末尾约束（"≤ 200 字" / "≤ 5 条关键词" 等）。
3. **新建 `src/harness_workflow/playbook/llm.py`**：
   - 顶部 import：`from __future__ import annotations` + `import abc, os, sys, urllib.request, urllib.error, json` + `from pathlib import Path` + `from typing import Optional`
   - 定义 `LLMProvider(abc.ABC)` 抽象基类，4 个 `@abc.abstractmethod`：generate_overview / generate_domain_description / generate_keywords / generate_tech_decisions
   - `_load_prompt(template_name: str) -> str` helper：从 `playbook/prompts/{template_name}.md` 读模板字符串
4. **写 NoopProvider**：4 method 全返回固定 sentinel `"<!-- LLM disabled (Noop provider) -->"`；`generate_keywords` 返回 `[]`。
5. **写 OllamaProvider**：
   - `__init__`：`self.host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')`；`self.model = os.getenv('OLLAMA_MODEL', 'llama3.2')`
   - `_call_ollama(prompt: str) -> str`：urllib.request POST `{self.host}/api/generate` payload `{model, prompt, stream: false}`，解析 JSON 返回 `response` 字段；失败 raise NetworkError
   - 4 method 实现：load 对应 prompt 模板，format placeholder，调 `_call_ollama`
6. **写 AnthropicProvider**：
   - `__init__`：`self.api_key = os.getenv('ANTHROPIC_API_KEY')`；`self.model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-haiku-latest')`
   - `_call_anthropic(prompt: str) -> str`：方法内 lazy `import anthropic`；`Anthropic(api_key=self.api_key).messages.create(...)`；失败 raise NetworkError
   - 4 method 实现同 OllamaProvider 模式
7. **写 OpenAIProvider**：同 AnthropicProvider 模式，调 `openai.OpenAI().chat.completions.create(...)`。
8. **写 `auto_detect_provider() -> LLMProvider` 工厂**：
   - 顺序探测：
     1. `os.getenv('ANTHROPIC_API_KEY')` → try import anthropic → AnthropicProvider；
     2. `os.getenv('OPENAI_API_KEY')` → try import openai → OpenAIProvider；
     3. urllib HEAD `{OLLAMA_HOST}/api/version` 1s timeout → OllamaProvider；
     4. fallback → NoopProvider + stderr `[llm] WARN: no provider available, falling back to Noop`
9. **改 `pyproject.toml`**：`[project.optional-dependencies]` 加 `llm = ["anthropic>=0.30", "openai>=1.0"]`（注：Ollama / Noop 零依赖）。
10. **新增 pytest 用例 ≥ 8 条**（`tests/test_llm_provider.py`）：
    - TC-01 NoopProvider 返回 sentinel（4 method 各 1 断言 + generate_keywords 返回 `[]`）
    - TC-02 AnthropicProvider mock SDK（用 `unittest.mock.patch` mock `anthropic.Anthropic` 类，断言 messages.create 被调 + prompt 含 placeholder 替换值）
    - TC-03 OpenAIProvider mock SDK
    - TC-04 OllamaProvider mock urllib（patch `urllib.request.urlopen`，断言 POST URL / payload）
    - TC-05 auto_detect ANTHROPIC_API_KEY 优先（mock env + try import 成功）
    - TC-06 auto_detect OPENAI_API_KEY fallback（mock 无 ANTHROPIC_API_KEY 但有 OPENAI_API_KEY）
    - TC-07 auto_detect Ollama ping 通（mock 无 LLM API key + urllib HEAD 200）
    - TC-08 auto_detect 全部失败回 Noop（mock 无 env + urllib HEAD 失败）
11. **跑 pytest**：`pytest tests/test_llm_provider.py -v` 看真实数字。
12. **harness validate**：`harness validate --contract artifact-placement && harness validate --human-docs`。
13. **session-memory 留痕**：所有数字 + exit code + 4 provider 实测 mock 调用次数。

## 2. 产物

- `src/harness_workflow/playbook/llm.py`（新增，LLMProvider 抽象基类 + 4 实现 + auto_detect_provider 工厂，估算 ~250 LOC）
- `src/harness_workflow/playbook/prompts/overview.md`（新增）
- `src/harness_workflow/playbook/prompts/domain-description.md`（新增）
- `src/harness_workflow/playbook/prompts/keywords.md`（新增）
- `src/harness_workflow/playbook/prompts/tech-decisions.md`（新增）
- `pyproject.toml`（改：`[project.optional-dependencies]` 加 `llm = [...]`）
- `tests/test_llm_provider.py`（新增，8 TC，全 mock）

## 3. 依赖

- 上游：无（独立新建模块 + 模板）。
- 下游：chg-04（install/refresh 集成 LLM）使用本 chg 落地的 `LLMProvider` 抽象 + `auto_detect_provider()` 工厂。

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - src/harness_workflow/playbook/llm.py（新建）
> - src/harness_workflow/playbook/prompts/*.md（新建 4 份）
> - pyproject.toml（加 optional-dependencies）
> - 调用链：本 chg 仅落 provider 层，无 CLI 入口被改；下游 chg-04 集成时调 auto_detect_provider() → 4 provider 实现

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 NoopProvider 返回 sentinel | 实例化 NoopProvider 调 4 method | generate_overview / generate_domain_description / generate_tech_decisions 返回 `"<!-- LLM disabled (Noop provider) -->"`；generate_keywords 返回 `[]` | AC-16 | P0 |
| TC-02 AnthropicProvider mock SDK | mock anthropic.Anthropic + mock env ANTHROPIC_API_KEY；调 generate_overview('proj', ['Python'], ['core']) | mock client.messages.create 被调 ≥ 1 次 + prompt 含 'proj' 占位符替换值 | AC-16 | P0 |
| TC-03 OpenAIProvider mock SDK | mock openai.OpenAI + mock env OPENAI_API_KEY | mock client.chat.completions.create 被调 ≥ 1 次 | AC-16 | P0 |
| TC-04 OllamaProvider mock urllib | mock urllib.request.urlopen 返回 JSON {response: 'mock-text'}；调 generate_overview | urlopen 被调 + URL = http://localhost:11434/api/generate + 返回值 = 'mock-text' | AC-16 | P0 |
| TC-05 auto_detect ANTHROPIC 优先 | mock env ANTHROPIC_API_KEY=k + try import anthropic 成功 | auto_detect_provider() 返回 isinstance AnthropicProvider | AC-16 | P0 |
| TC-06 auto_detect OPENAI fallback | mock env 无 ANTHROPIC_API_KEY 有 OPENAI_API_KEY + try import openai 成功 | auto_detect_provider() 返回 isinstance OpenAIProvider | AC-16 | P0 |
| TC-07 auto_detect Ollama ping 通 | mock 无 LLM env + urllib HEAD 返回 200 | auto_detect_provider() 返回 isinstance OllamaProvider | AC-16 | P0 |
| TC-08 auto_detect 全部失败回 Noop | mock 无 env + urllib HEAD raise URLError | auto_detect_provider() 返回 isinstance NoopProvider + stderr 含 'falling back to Noop' | AC-16 | P0 |
| TC-09 提示词模板 placeholder 替换 | 调 _load_prompt('overview') + format(project_name='X') | 返回字符串含 'X' 替代占位符 | AC-16 | P1 |
| TC-Dogfood-01 LLM provider 模块 import | subprocess.run([sys.executable, '-c', 'from harness_workflow.playbook.llm import LLMProvider, auto_detect_provider, NoopProvider; p = NoopProvider(); print(p.generate_overview("x", [], []))']) | exit 0 + stdout 含 sentinel 字符串 | AC-16 | P1 |
