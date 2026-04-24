
## [2026-04-24] req-39（对人文档家族契约化 + artifacts 扁平化）/ chg-05（CLI 路径对齐扁平化 + scaffold mirror 同步）executing 完成

- **命令**：改写 `workflow_helpers.py`（新增双轨常量 + `_use_flat_layout` + 改写 `create_requirement`/`create_change`/`create_regression`/`_next_chg_id`/`archive_requirement` 5 个 helper）；新增 test_create_change_flat.py（7条）/ test_create_regression_flat.py（5条）/ test_archive_requirement_flat.py（2条）；修复 test_regression_independent_title.py；scaffold_v2 mirror 5 文件 diff 归零
- **结果**：AC-7（机器型文档迁离）/ AC-8（CLI 对齐）/ AC-1（扁平结构）/ AC-12（mirror 归零）全自证；370 passed（+15条），ReadmeRefreshHintTest 1 failed 为 req-28 遗留，零新回归

## [2026-04-24] req-39（对人文档家族契约化 + artifacts 扁平化）/ chg-02（validate_human_docs 重写 + 精简废止项）executing 完成

- **命令**：重写 `validate_human_docs.py`（删废止项常量 + 扁平路径扫描 + 历史存量豁免）；`test_validate_human_docs.py` 8→16 条全绿；`test_smoke_req28.py` smoke 用例更新
- **结果**：AC-6 `grep -cn "测试结论\|验收摘要"` = 0；AC-5 CLI exit code 非零/零验证通过；全量 pytest 356 passed（+11 条）；`ReadmeRefreshHintTest` failure 为并行 chg 影响，非本 chg 引入

## [2026-04-23] req-39 chg-04（acceptance gate 强执行：lint 阻塞 + 未绿 FAIL）executing 完成

- **命令**：改写 `.workflow/evaluation/acceptance.md`（§2 硬门禁阻塞 + 完成条件前置硬门禁）+ 新增 `tests/test_acceptance_gate_contract.py`（2 passed）+ scaffold mirror 同步
- **结果**：AC-5 / AC-12（本 chg 部分）自证通过；2 passed，零新增回归

## [2026-04-23] req-38 chg-01 executing 完成

- **命令**：chg-01（protocols 目录 + catalog 单行引用 + 硬门禁五保护扩展）实现
- **结果**：成功
- **详情**：新建 `.workflow/tools/protocols/mcp-precheck.md`；更新 `tools/index.md`、`catalog/api-document-upload.md`、`harness-manager.md §硬门禁五`；scaffold_v2 mirror 4 文件同步；AC-3 / AC-4 / AC-9 全 PASS

## [2026-04-22T18:05:00Z] req-34 executing 5 chg 完成

- **req-34**：新增工具 api-document-upload + 修复 scaffold_v2 mirror 漂移
- **结果**：5 commit（5c63bf1 / 5f0c51d / f0063aa / f5ccb88 / 1aab1af）全部成功
- **详情**：chg-01 工具文件 + chg-02 索引 + chg-03 mirror 同步 + chg-04 硬门禁五 + chg-05 端到端自证；pytest 零新增失败

## 2026-04-23 reg-01（install 不全量同步 scaffold_v2 到存量项目）regression 诊断完成

- 角色：诊断师（regression / opus）。
- 操作：填充 reg-01 工作区五份文件 — regression.md / analysis.md / decision.md / session-memory.md / 回归简报.md。
- 结果：判定真实问题；路由 = append-to-current（req-36 追加 chg-05 install 全量同步 + chg-06 audit 解锚点）；阻塞 req-36（harness install 同步契约完整性修复（存量项目 .workflow/ 与 scaffold_v2 mirror 保持一致））done。

## chg-02 执行完成（2026-04-23T15:15:12Z）
- harness-manager.md 新增 §3.5.2 触发 api-document-upload 召唤
- cli.py --contract choices 追加 triggers
- validate_contract.py 新增 check_contract_triggers
- tests/test_validate_contract_triggers.py 新增 7 条用例
- scaffold_v2 mirror 同步
- harness validate --contract triggers EXIT: 0

---
2026-04-24 | executing | req-39/chg-01（artifacts-layout 契约底座 + stage-role 路径同构改写）
- 新建 .workflow/flow/artifacts-layout.md（5 节骨架，白名单 13 类，迁移位表三段）
- 改写 .workflow/context/roles/stage-role.md 契约 2/3（扁平路径 + artifacts-layout.md 引用段）
- cp mirror × 2；diff -q 自检零差异
- AC 量化判据全 PASS（节数=5，白名单 grep=36，mirror diff=0）
- 产出 实施说明.md（legacy 路径）+ session-memory.md（state + artifacts 双路径）
