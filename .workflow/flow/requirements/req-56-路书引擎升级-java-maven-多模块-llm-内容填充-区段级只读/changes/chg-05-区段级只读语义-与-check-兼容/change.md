---
id: chg-05
title: "区段级只读语义修订（base-role 硬门禁十 §4） + playbook-check 兼容"
req: req-56
created_at: 2026-04-30
---

## 目标

`.workflow/context/roles/base-role.md` 硬门禁十 §4 文字精修，把"不要修改 `artifacts/project/playbooks/` 下任何文件"细化为"`<!-- AUTO:* -->` / `<!-- LLM:* -->` 区段只读 + 区段外 TODO / 人写区域用户可改 + agent 默认不改 / 用户 explicit 后可改"的**区段级只读语义**（OQ-4 = D1 决策落地）；`harness_playbook_check.py` 注释更新（行为不变，AUTO 区段哈希漂移检测沿用），同时把 chg-04（install / refresh 集成 LLM） 落地的 `<!-- LLM:* -->` 区段纳入哈希漂移检测正则；同步 `playbook-layout.md` 与 README / SKILL.md mirror。

## 范围（Scope）

### Included

- **修改 `.workflow/context/roles/base-role.md` 硬门禁十 §4**：
  - 将"### 4. 不该做的事"改为"### 4. 区段级只读语义（req-56（路书引擎升级——Java/Maven 多模块 + LLM 内容填充 + 区段级只读） / chg-05（区段级只读语义 + check 兼容） OQ-4=D1 修订）"；
  - 写明三层语义：
    1. **AUTO / LLM 区段（脚本 / LLM 写入）只读**：`<!-- AUTO:* -->` / `<!-- LLM:* -->` 之间内容由 `harness install` / `harness playbook-refresh` 自动维护，agent **禁止**直接编辑（要改请跑 refresh）；用户可观察但不建议手改（手改会被下次 refresh 覆盖）。
    2. **TODO / 人写区域用户可改**：区段外的 `<!-- TODO: ... -->` 占位与人写文字，用户可任意修改；agent **默认不改**（保持安全）；用户在任务中 explicit 说"修路书 X 章节"时 agent 才允许写。
    3. **路径硬约束沿用**：路径 `artifacts/project/playbooks/` 仍由 `repository-layout.md` §2.1 项目级豁免章节覆盖（OQ-1=B 决策不变）；只读语义只是细化"agent / 用户写入边界"。
  - 删除原"不要修改 `artifacts/project/playbooks/` 下任何文件"裸语义（与 chg-04 LLM 写入面冲突）。
- **修改 `src/harness_workflow/tools/harness_playbook_check.py`**：
  - 文档 docstring 更新（注释新语义"AUTO + LLM 区段哈希漂移仍检 / 区段外不报警"）；
  - AUTO 区段哈希漂移检测正则扩到同时支持 LLM 区段：`<!--\s*(AUTO|LLM):(\w+)\s*-->`（chg-04 双 marker 系统配套）；
  - 行为不变（仍是漂移检测 + exit code），只是覆盖面扩展。
- **修改 `.workflow/flow/playbook-layout.md`**：
  - 在第 §4 节（HTML 注释定界规约）追加"区段级只读语义"注释段（引用 base-role 硬门禁十 §4，不重复语义）；
  - 在 §5 节（如有）追加"LLM 区段语法（chg-04 引入）"段说明 `<!-- LLM:* -->` 与 `<!-- AUTO:* -->` 同语法；
  - 不动 §1-§3 骨架契约（保持 req-55 baseline）。
- **修改 README.md / SKILL.md mirror**：同步行说明"路书 AUTO / LLM 区段只读 + TODO 区域用户可改"。
- **新增 pytest 用例 ≥ 2 条**（`tests/test_section_readonly_semantics.py`）：
  - `test_baserole_section_readonly_wording`：grep `.workflow/context/roles/base-role.md` 命中"AUTO 区段只读" / "TODO 区域可改" / "agent 默认不改" 三个语义关键词
  - `test_check_includes_llm_section_drift`：fixture 含 LLM 区段哈希漂移 → playbook-check exit ≠ 0；fixture 仅 TODO 区段被改 → playbook-check exit 0
- **dogfood TC**（`tests/test_section_readonly_dogfood.py::test_section_readonly_full_semantics`）：tmp_path + 完整路书（含 LLM 区段 + TODO 区段） + subprocess 三种修改场景 + check 命令断言。

### Excluded

- 不修改 base-role.md 其他硬门禁（一/二/三/四/六/七/九 文字零变化）。
- 不引入 PreToolUse hook 拦截 agent 写路书（OQ-5 = A 沿用 req-55，仅文字 + check CI 兜底）。
- 不实现"区段外编辑追踪 / 人改区域 git diff 检测"（本 req 不做，留 sug 池）。
- 不动 chg-01 推断器 / chg-02 SCRIPTS detector / chg-03 LLM provider / chg-04 集成代码（仅文字 + check 注释 + 正则扩展）。

## 依赖

- 上游：chg-04（install / refresh 集成 LLM，落地 `<!-- LLM:* -->` 区段写入面）。
- 下游：无（本 chg 是收尾文字 + 配套 check 校正）。

## 验收（Acceptance）

- AC-19（base-role 硬门禁十 §4 区段级只读文字落地）：grep 命中三个语义关键词；硬门禁十总数仍为 1 个。
- AC-20（playbook-check 兼容新语义）：fixture TODO 区段编辑 → check exit 0；fixture LLM 区段哈希漂移 → check exit ≠ 0。
- AC-22（现有 41 TC 不破坏）+ AC-23（全量回归零引入 fail）。

## 风险与缓解

- **风险 R-18（base-role 硬门禁十 §4 文字改写后语义模糊）**：从"全文件只读"改"区段级只读"语义复杂度上升，agent 可能误读。**缓解**：文字精修时严格按"三层语义"分点表述（AUTO/LLM 只读 / TODO 可改 / 路径硬约束沿用）；写明 escape hatch（"用户 explicit 指示后 agent 才可写"），对比示例（合规 vs 违规）补在 §4 末尾。
- **风险 R-19（check 正则扩展破坏 req-55 41 TC 兼容）**：`<!--\s*(AUTO|LLM):(\w+)\s*-->` 改后可能匹配既有 AUTO 区段时行为变化。**缓解**：正则改后必须 `pytest tests/test_playbook_check.py -v` 全 PASS（baseline TC 沿用），新加 LLM 区段 TC 是新增不替换；测试用例设计中显式列出"baseline 兼容 TC"（沿用 req-55 chg-05 原 7 类漂移检测断言）。
