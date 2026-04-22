# Change

## 1. Title

对人文档落盘校验机制：harness validate --human-docs + 覆盖性测试 + acceptance SOP 引用

## 2. Goal

- 提供一个可跑的校验入口，断言 req / bugfix 周期中每个 stage 的对人文档都真实落盘到 `artifacts/{branch}/...`，并在 acceptance 角色 SOP 中引用该入口作为验收硬门禁。

## 3. Requirement

- `req-28`

## 4. Scope

### Included

- 新增 CLI 子命令 `harness validate --human-docs [--requirement <id> | --bugfix <id>]`：
  - 扫描目标 req / bugfix 的 artifacts 目录，按 stage 映射表核对 6 份对人文档是否落盘。
  - 输出结构化结果：每个 stage `已产出 / 未产出 / 路径异常`，附缺失路径。
  - 未通过时以非零退出码退出，便于 CI / smoke 使用。
- 在 `.workflow/context/roles/acceptance.md` 的 SOP 中追加一条："验收开始前必须跑 `harness validate --human-docs --requirement <id>` 并在 `验收摘要.md` 中引用结果"。
- 新增 `tests/test_validate_human_docs.py`：构造 fixture（某 stage 故意缺文档 / 某 stage 路径异常）断言 CLI 返回非零 + 结果字段。

### Excluded

- 不校验对人文档的"字段内容完整性"，仅校验是否真实落盘（内容完整性由各角色自检）。
- 不新增 `harness validate` 其他子开关（未来 sug 可再扩）。
- 不自动补写缺失文档，只报告。

## 5. Acceptance

- Covers requirement.md **AC-09**：可跑的校验方式存在、缺失时能明确指出路径、失败 exit code 非 0。
- 与 AC-11 联动：chg-07 的端到端 smoke 会直接调用本校验对 req-28 自身的 6 份对人文档做反向验证。

## 6. Risks

- 风险 A：stage 映射表（哪 stage 对应哪份对人文档）与 `.workflow/context/roles/stage-role.md` 的契约 3 需单一真相 → 缓解：在 CLI 代码中从 `stage-role.md` 契约 3 的表格做硬编码映射，添加注释指向源表。
- 风险 B：`artifacts/{branch}/` 路径的 branch 判定依赖 git → 缓解：复用既有的 `resolve_branch_root` 逻辑，CLI 支持 `--branch` 手动覆盖便于测试。
- 风险 C：regression 级对人文档路径复杂（req 下的 regressions + bugfix 下的 regressions） → 缓解：V1 只校验 req / bugfix 主路径 6 份；regression 路径留 TODO，并在 plan 中标注。
