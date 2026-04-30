---
id: chg-04
title: "install / refresh 集成 LLM（默认开启 / --no-llm 关闭 + 失败 fallback）"
req: req-56
created_at: 2026-04-30
---

## 1. 执行步骤

1. **读上下文**：读 chg-03（LLM provider 抽象层）落地的 `llm.py` API（`LLMProvider` / 4 实现 / `auto_detect_provider`）、req-55 chg-03 落地的 `init.py`（`init_playbook(root, skip, only)` 主入口）、req-55 chg-04 落地的 `harness_playbook_refresh.py::playbook_refresh`、`skeleton.py` 4 模板。
2. **改 `skeleton.py`**：在 4 模板中追加 5 类 LLM 区段定界（`<!-- LLM:OVERVIEW_DESC -->` / `<!-- LLM:TECH_DECISIONS -->` / `<!-- LLM:DOMAIN_DESC -->` / `<!-- LLM:KEYWORDS -->` / `<!-- LLM:CODE_MAP_KEYWORDS -->`）。每对 marker 之间默认放 `<!-- TODO: ... -->` 占位（不调 LLM 时保留）。
3. **改 `init.py::init_playbook`**：
   - 函数签名加 `no_llm: bool = False`；
   - 在 `render_skeleton` 之后插入 LLM 填充阶段：
     ```python
     if not no_llm and os.getenv('CI', '').lower() != 'true':
         from harness_workflow.playbook.llm import auto_detect_provider
         llm = auto_detect_provider()
         _fill_with_llm(root, domains, llm, project_metadata)
     ```
   - 新增 `_fill_with_llm(root, domains, llm, metadata)` helper：依次调 4 method + 用 chg-04 复用的 `replace_auto_section`（marker 改 LLM 前缀）写入对应文件；try-except 包裹每次调用 + stderr WARN fallback。
4. **改 `harness_playbook_refresh.py::playbook_refresh`**：
   - 函数签名加 `no_llm: bool = False`；
   - 在所有 AUTO 区段刷新完成后追加 LLM 填充阶段（与 init.py 同语义，但只对已存在的 LLM 区段刷新）；
   - 复用 `replace_auto_section` helper（marker 前缀改 LLM）；
   - try-except 包裹每次调用，failure 时不破坏现有内容。
5. **改 `cli.py`**：
   - install_parser 加 `--no-llm` flag（store_true）；
   - playbook-refresh_parser 加 `--no-llm` flag；
   - install handler 透传 `no_llm=args.no_llm`；
   - playbook-refresh handler 透传 `no_llm=args.no_llm`；
   - 顶层（或 helper）增加 `_resolve_no_llm(args) -> bool`：返回 `args.no_llm or os.getenv('CI', '').lower() == 'true'`。
6. **新增 `tests/conftest.py::ensure_no_real_llm` autouse fixture**：每个测试自动 monkeypatch `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` env 为空 + monkeypatch `auto_detect_provider` 返回 `NoopProvider`（避免测试泄漏真实 API 调用）。
7. **新增 pytest 用例 ≥ 5 条**（`tests/test_install_refresh_llm_integration.py`）：
   - TC-01 install 调 LLM（mock provider 4 method 被调，断言调用次数 + 区段被替换）
   - TC-02 install --no-llm 跳过 LLM（mock provider 0 调用）
   - TC-03 install env CI=true 自动跳过 LLM
   - TC-04 LLM 抛 NetworkError fallback（stderr WARN + exit 0 + 区段保留 TODO）
   - TC-05 refresh 替换 LLM 区段（fixture 含 LLM:* 区段，刷新后区段内容由 mock provider 返回值替换）
8. **dogfood TC**（`tests/test_petmall_fixture_dogfood.py::test_petmall_full_pipeline`）：详见 §4 表 TC-Dogfood-01。
9. **跑 pytest**：`pytest tests/test_install_refresh_llm_integration.py tests/test_petmall_fixture_dogfood.py -v`。
10. **harness validate**：`harness validate --contract artifact-placement && harness validate --human-docs`。
11. **session-memory 留痕**：所有数字 + dogfood subprocess stdout/stderr 全文 + LLM mock 调用统计。

## 2. 产物

- `src/harness_workflow/playbook/skeleton.py`（改：4 模板加 5 类 LLM 区段定界）
- `src/harness_workflow/playbook/init.py`（改：`init_playbook` 加 `no_llm` 参数 + `_fill_with_llm` helper）
- `src/harness_workflow/tools/harness_playbook_refresh.py`（改：`playbook_refresh` 加 `no_llm` 参数 + LLM 填充阶段）
- `src/harness_workflow/cli.py`（改：install / playbook-refresh 加 `--no-llm` flag + handler 透传 + `_resolve_no_llm` helper）
- `tests/conftest.py`（新增 / 改：`ensure_no_real_llm` autouse fixture）
- `tests/test_install_refresh_llm_integration.py`（新增，5 TC）
- `tests/test_petmall_fixture_dogfood.py`（新增，1 dogfood TC，端到端 3 步）

## 3. 依赖

- 上游：chg-01（推断器多语言注册化，输出领域名）+ chg-02（SCRIPTS detector 注册化，输出脚本上下文）+ chg-03（LLM provider 抽象层）。
- 下游：chg-05（区段级只读语义 + check 兼容）验证本 chg 落地的 LLM 区段语义。

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - src/harness_workflow/playbook/skeleton.py（4 模板加 LLM 区段）
> - src/harness_workflow/playbook/init.py（init_playbook 加 no_llm + LLM 填充阶段）
> - src/harness_workflow/tools/harness_playbook_refresh.py（playbook_refresh 加 no_llm + LLM 填充阶段）
> - src/harness_workflow/cli.py（install / playbook-refresh 加 --no-llm flag）
> - 调用链：harness install --no-llm → init_playbook(no_llm=True) → 跳过 LLM；
>           harness install → init_playbook(no_llm=False) → auto_detect_provider() → llm.generate_*；
>           harness playbook-refresh → playbook_refresh → AUTO 区段刷新 → LLM 区段填充

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 install 调 LLM 4 method | tmpdir + mock provider（返回固定文本）+ install --no-llm 不传 | mock provider.generate_overview / generate_domain_description / generate_keywords / generate_tech_decisions 各被调 ≥ 1 次 + overview/domains README/code-map 对应区段被替换 | AC-18 | P0 |
| TC-02 install --no-llm 跳过 | tmpdir + install --no-llm | mock provider 4 method 0 调用 + 区段保留 TODO 占位 | AC-17 | P0 |
| TC-03 install env CI=true 自动跳过 | tmpdir + monkeypatch CI=true + install（无 --no-llm） | 同 TC-02（_resolve_no_llm 返回 True） | AC-17 | P0 |
| TC-04 LLM NetworkError fallback | tmpdir + mock provider.generate_overview raise NetworkError | stderr 含 `[llm] WARN: provider failed, falling back to Noop` + exit 0 + 区段保留 TODO | AC-24 | P0 |
| TC-05 refresh 替换 LLM 区段 | tmpdir + 完整路书（含 LLM:OVERVIEW_DESC 区段 TODO 占位）+ mock provider + playbook-refresh | refresh 后 LLM:OVERVIEW_DESC 区段内容 = mock provider 返回值 | AC-18 | P0 |
| TC-06 多语言项目集成测试 | tmpdir + Maven 多模块 fixture（chg-01）+ pom.xml + mock LLM | install 成功 + 5 模块 domain README 各被 LLM 填充 | AC-13 / AC-18 | P1 |
| TC-Dogfood-01 PetMallPlatform 完整 pipeline | tmp_path + PetMallPlatform-like fixture（5 顶层模块 platform-* + 父 pom.xml `<modules>` 列出 5 模块 + spring-boot-maven-plugin + app/logs 噪声）+ mock LLM provider；subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'install', '--root', tmpdir]) 然后 subprocess playbook-refresh 然后 playbook-check | (a) install exit 0 + stdout 含 `matched 'maven_multi_module'` + 5 模块 domain README 被 mock LLM 填充；(b) refresh exit 0 + runbook AUTO:SCRIPTS 含 ≥ 4 行 mvn 命令；(c) check exit 0；(d) runtime.yaml stage 字段存在；(e) feedback.jsonl 事件数 ≥ 3 | AC-13 / AC-14 / AC-18 / AC-21 | P0 |
