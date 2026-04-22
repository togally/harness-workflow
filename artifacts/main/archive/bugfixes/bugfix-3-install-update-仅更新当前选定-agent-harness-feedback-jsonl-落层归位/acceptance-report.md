# Acceptance Report — bugfix-3 install/update 仅更新当前选定 agent + feedback.jsonl 落层归位

## 验收场次
- Level 0 主 agent → stage: acceptance (ff 模式)
- Level 1 Subagent (本报告作者) → 独立核查
- 验收时间：2026-04-20
- 验收依据：`bugfix.md` Validation Criteria 5 条（briefing 里称"6 条"系表述口径，实际 bugfix.md 列了 5 条，按 5 条核查）

## Validation Criteria 逐条核查

| # | Criterion | 结论 | 证据 |
|---|-----------|------|------|
| 1 | `test_active_agent_and_feedback_relocation.py` 3 passed | [x] | 独立复跑 3/3 PASS（1.52s 内）|
| 2 | 全量 pytest 零新增回归（容忍 pre-existing `test_smoke_req29::HumanDocsChecklistTest`）| [x] | `152 passed / 50 skipped / 1 failed`；failure 经 git stash 回 HEAD baseline 复跑仍 FAIL，认证为 pre-existing |
| 3 | 手动烟测 install --agent claude + update + feedback 迁移 | [x] | `/tmp/petmall-bugfix3-acceptance-smoke/`：`platforms.yaml` 写入 `active_agent: claude`；`.harness/` 被 rmdir；新路径 `.workflow/state/feedback/feedback.jsonl` 28 行 3748 bytes（与迁移前完全一致）；`.codex/.qoder/.kimi/skills/harness` mtime 未变，`.claude/skills/harness` mtime 推进 |
| 4 | `harness update --all-platforms` escape hatch 可恢复旧行为 | [x] | testing 阶段烟测步 c 已证（stdout `refreshed .codex/.claude/.qoder`）；本次 acceptance 未重复验证，但 `test_cli.py` 2 条既有用例改用 `--all-platforms` 并全绿，等价覆盖 |
| 5 | `harness feedback` CLI 从新路径正确读取，事件 ≥ 迁移前 + 新增 | [x] | testing 阶段烟测步 d `harness-feedback.json` 导出成功；本次烟测新路径保留 28 行未丢失（迁移零数据损失）|

**整体**：5/5 核查通过。

## 全量 pytest 独立复跑 + baseline 认证

- 主 repo 独立 `PYTHONPATH=src python3 -m pytest -q --no-header` → **152 passed / 50 skipped / 1 failed**
- 唯一 failure：`tests/test_smoke_req29.py::HumanDocsChecklistTest::test_human_docs_checklist_for_req29`（req-29 artifacts 目录命名不匹配）
- **经验二硬门禁执行**：`git stash push -u` 回到 HEAD baseline 复跑同一条 → 仍然 FAIL（同一 AssertionError 同一行）→ 认证为 pre-existing，与 bugfix-3 修改范围无关
- `git stash pop` 已完成，executing 改动恢复完整

## 代码变更范围核查

`git diff --stat HEAD`：
- `src/harness_workflow/workflow_helpers.py` ✓（白名单）
- `src/harness_workflow/tools/harness_update.py` ✓
- `src/harness_workflow/tools/harness_export_feedback.py` ✓
- `src/harness_workflow/cli.py` ✓（Fix Scope 未列但实施说明已交代，CLI 入口必改）
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` ✓
- `src/harness_workflow/assets/scaffold_v2/.workflow/tools/catalog/harness-export-feedback.md` ✓
- `tests/test_cli.py` ✓（2 条既有断言改 `--all-platforms`，符合 experience 七"同步行为变更老断言"）
- `tests/test_active_agent_and_feedback_relocation.py` ✓（3 红用例）
- `tests/test_active_agent_feedback_edge_cases.py` ✓（3 边界用例，testing 补强）
- `.harness/feedback.jsonl` ~运行副产物（ff 事件追加 2 行），非本 bugfix 范畴
- `.workflow/state/runtime.yaml` ~stage 切换正常产物

**结论**：零越界，无意外文件。

## 对人文档落盘 validate

`harness validate --human-docs --bugfix bugfix-3` 输出 **2/5**：
- [✓] 实施说明.md
- [✓] 测试结论.md
- [ ] 回归简报.md（regression 阶段产出，本 bugfix regression 阶段未产出，由主 agent 判断是否需补）
- [ ] 验收摘要.md（本阶段产出，下文补齐）
- [ ] 交付总结.md（done 阶段产出，非本阶段）

本阶段产出 `验收摘要.md` 后 validate 可达 3/5；4/5 需补 `回归简报.md`；5/5 需 done 阶段产 `交付总结.md`。回归简报缺失已上报主 agent。

## 烟测结果（3 核查点）

| 核查点 | 期望 | 实际 | 结论 |
|---|---|---|---|
| `platforms.yaml` 含 `active_agent: claude` | ✓ | `active_agent: claude` 存在 | ✓ |
| `.harness/` 不存在或被 rmdir | ✓ | 目录已消失 | ✓ |
| `.workflow/state/feedback/feedback.jsonl` ≥ 28 行（数据连续）| ≥28 | 28 行、3748 bytes（与迁移前一字节不差）| ✓ |

跳过 `--all-platforms` 分支（briefing 许可）。

## 衍生问题（上报主 agent）

1. **回归简报.md 缺失**：bugfix-3 走 ff 跳过了 regression 产出步，`harness validate` 要求 4/5，可能需要主 agent 或 done 阶段判断是否补产或豁免。
2. **主仓 `.harness/feedback.jsonl`（182 行）真实迁移时机**：实施说明交代由下次真实 `harness update` 触发；本次主 repo 未跑 update，迁移未发生。建议 done 阶段评估是否在本分支主动触发一次 update 以完成主仓数据迁移，避免遗留。

## 最终结论

**acceptance pass**

理由：
- 5/5 Validation Criteria 满足；
- 独立复跑 152 passed，唯一 failure 经 HEAD baseline 认证为 pre-existing；
- 代码变更范围零越界；
- 烟测 3/3 核查点通过；
- 对人文档 2/5 为本阶段前的预期状态，本轮补齐验收摘要后 3/5，regression 简报缺失与 done 交付总结待路径推进，不阻塞本阶段判定。

建议主 agent 在 ff 模式下自主推进 `acceptance → done`。
