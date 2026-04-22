# Session Memory

## 1. Current Goal

- chg-05：交付 `harness validate --human-docs`（AC-09），覆盖 req / bugfix 对人文档落盘校验 + acceptance SOP 引用 + 测试。

## 2. Current Status

- ✅ Step 1：`HUMAN_DOC_CONTRACT` 映射硬编码完成，注释指向 stage-role.md 契约 3。
- ✅ Step 2：`validate_human_docs(root, target)` 实现完整，支持 req/bugfix 两种 target + runtime 回退。
- ✅ Step 3：CLI `validate --human-docs [--requirement | --bugfix]` 已接入，`--requirement` / `--bugfix` 互斥校验就绪。
- ✅ Step 4：`.workflow/context/roles/acceptance.md` 与 scaffold_v2 副本同步追加硬门禁条目，两处 `diff=0`。
- ✅ Step 5：`tests/test_validate_human_docs.py` 新增 8 条用例（core 6 + CLI 2），全绿；全仓 128 个测试 OK。
- ✅ 实施说明.md 已产出于 change 目录。

## 3. Validated Approaches

- 使用 `tempfile.mkdtemp` + tempdir 构造 `artifacts/main/requirements/req-XX-slug/` + `changes/chg-YY-slug/` 假树：验证 req / bugfix 路径分支无需碰主仓 runtime。
- `_check_doc` 三态（ok / missing / malformed）允许覆盖"把文档写成目录"这种反例路径。
- `resolve_requirement_reference` 的前缀匹配复用自 workflow_helpers，确保 `req-28` → `req-28-批量建议合集（7条）` 命中。
- 通过 `python -m harness_workflow validate --help` 验证新 flag 正确注册。

## 4. Failed Paths

- Attempt: 无
- Failure reason: 无
- Reminder: 测试运行中 `test_cli_mutual_exclusion` 曾想放在 `--requirement` 真实路径下，但保持 bugfix root 不存在更简洁——直接走分发前的互斥检查。

## 5. Candidate Lessons

```markdown
### 2026-04-19 validate --human-docs subcommand wiring
- Symptom: CLI 已有 `validate` 子命令，如何挂子开关而不破坏原 argparse 层级。
- Cause: 原 `harness_validate.py` 是独立 script 入口；新增需要在 cli.py 分支内拦截 `--human-docs`。
- Fix: 不动 `harness_validate.py`；在 `cli.py` 的 `if args.command == "validate"` 分支内前置判断 `args.human_docs`，走新模块的 `run_cli`，默认路径保持 legacy。
```

## 6. Next Steps

- 交回 executing 主 agent 报告 chg-05 完成；chg-07 smoke 将反向使用本 CLI 做 AC-11 反向覆盖。
- regression 级对人文档路径校验留作后续扩展。

## 7. Open Questions

- 是否需要 `--json` 结构化输出：plan.md Step 3 提到可选，AC-09 未强制；如 CI 集成需要，再扩展。
