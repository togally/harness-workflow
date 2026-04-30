---
id: chg-05
title: "区段级只读语义修订（base-role 硬门禁十 §4） + playbook-check 兼容"
req: req-56
created_at: 2026-04-30
---

## 1. 执行步骤

1. **读上下文**：读 reg-01 analysis.md §5（维度 D 根因 + 候选 D1 区段级只读 default-pick）、req-55 chg-02 落地的 `base-role.md` 硬门禁十（§1-§4 完整内容）、req-55 chg-05 落地的 `harness_playbook_check.py`（_AUTO_OPEN_RE / _AUTO_CLOSE_RE 正则 + 7 类漂移检测）、chg-04（install/refresh 集成 LLM）落地的 `<!-- LLM:* -->` 双 marker 系统设计。
2. **改 `.workflow/context/roles/base-role.md`**：
   - 找到硬门禁十 §4 "### 4. 不该做的事"段；
   - 整段替换为新版 "### 4. 区段级只读语义（req-56 / chg-05 OQ-4=D1 修订）"，含三层语义说明（AUTO/LLM 区段只读 / TODO 可改 / 路径硬约束沿用）；
   - 在末尾追加合规示例 + 违规示例对比（≤ 8 行）；
   - 保持硬门禁号 #10 不变（仅修订 §4 内容，不新增编号）。
3. **改 `src/harness_workflow/tools/harness_playbook_check.py`**：
   - 模块 docstring 更新（说明 chg-05 注释更新覆盖 LLM 区段，行为基本不变只扩正则面）；
   - `_AUTO_OPEN_RE` / `_AUTO_CLOSE_RE` 正则改为 `re.compile(r"<!--\s*(AUTO|LLM):(\w+)\s*-->")` / `re.compile(r"<!--\s*/(AUTO|LLM):(\w+)\s*-->")`；
   - `_find_auto_segments` / `_check_auto_pairs` 内部正则同步扩展（关键字组多一个 group 但 match name 不变）；
   - issue 字符串保持 `SEGMENT_UNPAIRED:` / `AUTO_SECTION_HASH_DRIFT:` 前缀（与 baseline 41 TC 断言兼容）。
4. **改 `.workflow/flow/playbook-layout.md`**：
   - 在 §4 末尾追加"区段级只读语义"注释段（引用 base-role 硬门禁十 §4 + chg-05 OQ-4=D1 决策，不重复全部语义）；
   - 如有 §5 LLM 区段语法节，附加段说明 `<!-- LLM:* -->` 与 `<!-- AUTO:* -->` 同语法、命名空间分离、check 行为相同。
5. **改 README.md / SKILL.md mirror 同步行**："路书 AUTO / LLM 区段只读（脚本 / LLM 维护，agent 不动）；TODO 区域用户可改（agent 默认不改，用户 explicit 后可改）"。
6. **新增 pytest 用例 ≥ 2 条**（`tests/test_section_readonly_semantics.py`）：
   - TC-01 base-role 文字 lint：用 `pathlib.Path(...).read_text()` 读 `.workflow/context/roles/base-role.md`，正则匹配三个语义关键词（"AUTO 区段只读" / "TODO 区域可改" / "agent 默认不改"），全部命中。
   - TC-02 check 包含 LLM 区段漂移：tmpdir 完整路书 fixture（含 LLM:OVERVIEW_DESC 区段）；用户人工删 LLM 区段中 1 行 → playbook-check exit ≠ 0 + stderr 含 `AUTO_SECTION_HASH_DRIFT`（issue 字符串复用 baseline）。
   - TC-03 check 不报告 TODO 区段编辑：tmpdir 完整路书 fixture；用户人工把"## 用途描述"段下的 TODO 改成自定义中文 → playbook-check exit 0（区段外不漂移）。
7. **dogfood TC**（`tests/test_section_readonly_dogfood.py::test_section_readonly_full_semantics`）：tmp_path + install 完整路书 + 三种修改场景 + subprocess `python3 -m harness_workflow.cli playbook-check --root <tmp>` + 断言：
   - 场景 a（仅 TODO 区段编辑）→ check exit 0
   - 场景 b（LLM 区段被人为删行）→ check exit ≠ 0
   - 场景 c（AUTO 区段被人为删行）→ check exit ≠ 0
   - runtime.yaml stage 字段存在 + feedback.jsonl 事件数 ≥ 1
8. **跑 pytest**：`pytest tests/test_section_readonly_semantics.py tests/test_section_readonly_dogfood.py tests/test_playbook_check.py -v`。
9. **harness validate**：`harness validate --contract artifact-placement && harness validate --human-docs`。
10. **session-memory 留痕**：所有数字 + exit code + base-role 修订 diff 摘要。

## 2. 产物

- `.workflow/context/roles/base-role.md`（改：硬门禁十 §4 文字精修）
- `src/harness_workflow/tools/harness_playbook_check.py`（改：docstring + 正则扩 LLM 区段，行为不变）
- `.workflow/flow/playbook-layout.md`（改：§4 末尾追加注释段）
- `README.md` / `SKILL.md`（改：同步行）
- `tests/test_section_readonly_semantics.py`（新增，3 TC）
- `tests/test_section_readonly_dogfood.py`（新增，1 dogfood TC）

## 3. 依赖

- 上游：chg-04（install / refresh 集成 LLM）落地的 LLM 区段写入面（验证"区段外可改 + 区段内只读"语义需要 LLM 区段已存在）。
- 下游：无（本 chg 是 req-56 收尾）。

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - .workflow/context/roles/base-role.md（硬门禁十 §4 文字精修）
> - src/harness_workflow/tools/harness_playbook_check.py（正则扩 LLM 区段，行为不变）
> - .workflow/flow/playbook-layout.md（§4 注释段追加）
> - README.md / SKILL.md（mirror 同步行）
> - 调用链：harness playbook-check → playbook_check → _find_auto_segments / _check_auto_pairs → 7 类漂移检测（覆盖面扩 LLM 区段）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 base-role 文字 lint | 读 .workflow/context/roles/base-role.md | grep 命中三个语义关键词："AUTO 区段只读" / "TODO 区域可改" / "agent 默认不改" | AC-19 | P0 |
| TC-02 check LLM 区段漂移 | tmpdir 完整路书（含 LLM:OVERVIEW_DESC 区段）+ 人工删区段中 1 行 | playbook-check exit ≠ 0 + stderr 含 AUTO_SECTION_HASH_DRIFT | AC-20 | P0 |
| TC-03 check 不报 TODO 区段编辑 | tmpdir 完整路书 + 人工改 "## 用途描述" 段下 TODO 内容 | playbook-check exit 0（区段外不漂移） | AC-20 | P0 |
| TC-04 baseline AUTO 区段漂移仍检 | tmpdir 完整路书（含 AUTO:STACK 区段）+ 人工删区段中 1 行 | playbook-check exit ≠ 0（baseline 行为保留） | AC-20 / AC-22 | P0 |
| TC-05 base-role 硬门禁号唯一性 | grep `^## 硬门禁十` .workflow/context/roles/base-role.md | 命中数 = 1（不新增编号） | AC-19 | P1 |
| TC-Dogfood-01 区段级只读完整语义 | tmp_path + install + 三种修改场景 + subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'playbook-check', '--root', tmpdir]) | 场景 a（TODO 编辑）exit 0；场景 b（LLM 区段删行）exit ≠ 0；场景 c（AUTO 区段删行）exit ≠ 0；runtime.yaml stage 存在；feedback.jsonl ≥ 1 事件 | AC-19 / AC-20 / AC-21 | P0 |
