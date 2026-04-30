# Session Memory — chg-03（LLM provider 抽象层）

## 1. Current Goal

新建 `src/harness_workflow/playbook/llm.py` + `prompts/` 目录，定义 `LLMProvider` 抽象基类与 4 实现（Anthropic / OpenAI / Ollama / Noop），按 env 自动检测 provider 顺序（OQ-3 = 自动检测决策），承载 reg-01（chg-03/04 Java/Maven 项目盲点 + LLM 填骨架决策反转） 维度 C "spec 不调 LLM 决策反转"的核心抽象层；本 chg 不集成到 install / refresh（chg-04 负责）。lazy import + optional dependencies 保证零依赖默认路径（NoopProvider 兜底）。

## 2. Context Chain

- Level 0: 主 agent（harness-manager）→ analysis stage 编排
- Level 1: Subagent-L1（analyst / opus）→ req-56（路书引擎升级——Java/Maven + LLM + 区段级只读）analysis stage
- Level 2（计划中 executing / sonnet）：执行本 chg-03

## 3. Completed Tasks（analysis stage 拆分阶段）

- [x] 读 reg-01（chg-03/04 Java/Maven 项目盲点 + LLM 填骨架决策反转） analysis.md §4 维度 C 根因 + 候选 C2 + §4.4 provider 抽象架构
- [x] 读 reg-01 decision.md §5 OQ-3 default-pick = 自动检测；OQ-2 default-pick = C2 全程可选
- [x] 拆分本 chg：抽象基类 + 4 provider + auto_detect_provider 工厂 + 4 prompt 模板 + 8 + 1 dogfood TC
- [x] lazy import 风险 R-12 缓解策略写入 change.md
- [x] 与 chg-01 / chg-02 / chg-04 / chg-05 边界划清：本 chg 只新建 llm.py + prompts/ + 改 pyproject + 新增 1 测试文件，不集成到 install/refresh

## 4. Results（analysis stage 产物）

| 产物路径 | 说明 |
|---------|------|
| `change.md` | 本 chg 范围 / 依赖 / AC / 风险 |
| `plan.md` | 13 步执行 + §4 测试用例设计（8 mock TC + 1 placeholder TC + 1 dogfood TC）|
| `session-memory.md` | 本文件 |

## 5. Issues / Bugs

无。

## 6. default-pick 决策清单（本 chg 范围内）

无（reg-01 decision.md §5 OQ-2 / OQ-3 已 default-pick = C2 + 自动检测，本 chg 直接继承）。

## 7. 下一步

- analysis stage 退出 → 等用户拍板 → executing 实施
- chg-01 / chg-02 / chg-03 可并行 executing；chg-04 等 chg-03 落地后做

---

## 8. executing stage 留痕（2026-04-30）

### 实施内容

- **新建** `src/harness_workflow/playbook/llm.py`（约 250 行）
  - `PlaybookContext` dataclass（LLM 输入上下文）
  - `GeneratedContent` dataclass（LLM 输出）
  - `LLMProvider` 抽象基类（ABC）
  - `make_prompt(context)` → 提示词模板构建函数
  - `parse_response(text)` → JSON 响应解析（失败返回 None，不抛）
  - `AnthropicProvider`：ANTHROPIC_API_KEY + lazy import anthropic SDK
  - `OpenAIProvider`：OPENAI_API_KEY + lazy import openai SDK
  - `OllamaProvider`：OLLAMA_HOST or 127.0.0.1:11434 via urllib.request
  - `NoopProvider`：降级实现，generate() 永远返回 None
  - `DEFAULT_PROVIDERS = [Anthropic, OpenAI, Ollama, Noop]`
  - `auto_select_provider(providers=None)` 工厂：按优先级顺序检测
  - `_retry_once` helper：单次重试机制（兼顾 R-12 / R-13 风险）

- **改** `src/harness_workflow/playbook/__init__.py`：导出 6 个新符号（LLMProvider / DEFAULT_PROVIDERS / auto_select_provider / PlaybookContext / GeneratedContent / NoopProvider）

- **新增** `tests/test_playbook_llm.py`：29 TC 全部 PASS
  - TC-01 NoopProvider always available + generate returns None
  - TC-02 auto_select no env → Noop
  - TC-03 auto_select ANTHROPIC_API_KEY → AnthropicProvider
  - TC-04 auto_select OPENAI_API_KEY → OpenAIProvider
  - TC-05 auto_select Ollama ping 200 → OllamaProvider
  - TC-06 AnthropicProvider 无 SDK → generate returns None
  - TC-07 parse_response 正确 JSON → GeneratedContent
  - TC-08 parse_response 错误 JSON → None
  - TC-09 make_prompt 含关键字段
  - TC-10 retry 机制（两种场景）
  - 其他 7 个辅助 TC（DEFAULT_PROVIDERS 验证等）

### 测试结果

- `pytest tests/test_playbook_llm.py -v`: **29 passed**
- 全量回归基线（无新文件）：55 failed / 751 passed
- 全量回归（含所有新文件）：59 failed / 852 passed
  - 4 个新增 fail 全属于 req-55/54 其他 chg 的 pre-existing fails（test_playbook_baserole_contract.py / test_playbook_layout_contract.py）
  - chg-03 引入 **+0 新增 fail**

- `harness validate --contract artifact-placement --root .`: exit 0 / PASS

### 边界遵守

- 未修改 `domain_inference.py`（chg-01 范围）
- 未修改 `harness_playbook_refresh.py`（chg-02 范围）
- 未修改 `cli.py`（chg-04 集成时才改）
- 未集成 LLM 到 install / refresh（chg-04 负责）
- lazy import 保证 CI 零外部依赖

### 经验留痕

- 经验十六适用（Python 3.14 中文引号 SyntaxError 风险）：本次全程使用 ASCII 引号，无问题
- TC-10 第一版断言逻辑错误（assertIsNone 但实际 retry 成功）→ 修正为"两次都失败 → None + call_count==2"

## 完成态

本 chg executing stage 完成 ✅
