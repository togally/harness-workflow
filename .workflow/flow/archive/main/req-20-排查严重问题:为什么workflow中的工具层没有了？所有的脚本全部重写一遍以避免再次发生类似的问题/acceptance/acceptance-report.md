# Acceptance Report for req-20

## 背景对齐
- 结论：已满足
- 说明：`.workflow/tools/` 被误清理的根因已定位并修复——`LEGACY_CLEANUP_TARGETS` 错误地将 tools 目录列为旧系统残留。当前代码已移除该路径，模板和当前仓库的 tools 目录均已恢复，问题已解决。

## 目标对齐
- 结论：已满足
- 说明：四项需求目标全部达成：
  1. 根因修复：`core.py` 中已移除对 `.workflow/tools/` 的误清理。
  2. 模板恢复：`scaffold_v2/.workflow/tools/` 模板目录已重建，包含全部核心文件。
  3. 当前仓库恢复：项目根目录下 `.workflow/tools/` 已恢复且内容完整。
  4. 防护增强：新增测试用例覆盖 init/update 生命周期，确保 tools 目录不会被误清理。

## 范围对齐
- 结论：已满足
- 说明：交付内容严格在需求范围内，无遗漏、无越界。Included 项（core.py 修改、模板重建、当前仓库恢复、测试新增）全部完成；Excluded 项（项目根目录 `tools/`、scaffold_v2 其他结构、状态机逻辑、新层级）均未触碰。

## Requirement-level AC 核查

| AC | 标准 | 核查方式 | 结论 | 备注 |
|----|------|---------|------|------|
| AC-1 | `src/harness_workflow/core.py` 的 `LEGACY_CLEANUP_TARGETS` 列表中不再包含 `Path(".workflow") / "tools"` 及任何 tools 子路径 | 自动检查 | ✅ | 读取 core.py 第 56–66 行，`LEGACY_CLEANUP_TARGETS` 中已无 tools 相关路径 |
| AC-2 | `src/harness_workflow/assets/scaffold_v2/.workflow/tools/` 目录存在，且至少包含：`index.md`、`stage-tools.md`、`selection-guide.md`、`maintenance.md`、`catalog/`（含 `_template.md` 等工具定义文件） | 自动检查 | ✅ | `ls` 确认四文件及 `catalog/` 均存在；`catalog/` 内含 `_template.md`、`agent.md`、`bash.md` 等 7 个文件 |
| AC-3 | 在当前仓库运行 `harness update` 后，`.workflow/tools/` 保持原位，不会被移动到 `.workflow/context/backup/legacy-cleanup/` | 自动检查 | ✅ | `test_update_does_not_archive_tools_directory` 测试通过，验证 update 后 tools 目录与 index.md 均保持原位 |
| AC-4 | 当前仓库根目录下 `.workflow/tools/` 已恢复，关键文件（如 `index.md`、`stage-tools.md`）存在且内容完整 | 自动检查 | ✅ | `ls .workflow/tools/` 确认四文件与 `catalog/` 均存在；与 backup 目录执行 `diff -r` 结果为空，内容完全一致 |
| AC-5 | `pytest` 测试全部通过，且至少新增一个测试用例验证 tools 目录在 init/update 生命周期中不会被误清理 | 自动检查 | ✅ | `pytest tests/test_cli.py -v` 结果 17 passed, 36 skipped，无失败；新增 `test_install_scaffolds_tools_directory` 与 `test_update_does_not_archive_tools_directory` 两个测试用例 |

## Change-level AC 核查

### chg-01
| AC | 标准 | 结论 | 备注 |
|----|------|------|------|
| AC-1 | `LEGACY_CLEANUP_TARGETS` 中不再包含 `Path(".workflow") / "tools"` 及任何 tools 子路径 | ✅ | 同 Requirement AC-1，core.py 中已移除 |
| AC-2 | `_required_dirs()` 返回的列表中同时包含 `.workflow/tools` 和 `.workflow/tools/catalog` | ✅ | 读取 core.py 第 1973–1974 行，列表中明确包含两路径 |
| AC-3 | 单独审查 core.py 中涉及目录清理/归档的其他代码，确认没有遗漏对 tools 目录的误处理 | ✅ | `grep -n "tools" core.py | grep -i "cleanup\|archive\|backup\|remove\|legacy\|clean"` 无匹配结果，确认无其他误处理逻辑 |

### chg-02
| AC | 标准 | 结论 | 备注 |
|----|------|------|------|
| AC-1 | `src/harness_workflow/assets/scaffold_v2/.workflow/tools/` 目录存在 | ✅ | `ls` 确认目录存在 |
| AC-2 | 至少包含：`index.md`、`stage-tools.md`、`selection-guide.md`、`maintenance.md` | ✅ | 上述文件均存在于该目录 |
| AC-3 | `catalog/` 子目录存在，且至少包含 `_template.md` | ✅ | `ls catalog/` 确认 `_template.md` 及多个工具定义文件存在 |
| AC-4 | 所有文件内容与 backup 中的源文件一致（直接复制即可） | ✅ | `diff -rq src/harness_workflow/assets/scaffold_v2/.workflow/tools/ .workflow/context/backup/legacy-cleanup/.workflow/tools/` 无差异 |

### chg-03
| AC | 标准 | 结论 | 备注 |
|----|------|------|------|
| AC-1 | 项目根目录下存在 `.workflow/tools/` | ✅ | `ls .workflow/tools/` 正常列出 |
| AC-2 | `.workflow/tools/index.md`、`.workflow/tools/stage-tools.md`、`.workflow/tools/selection-guide.md`、`.workflow/tools/maintenance.md` 存在且内容完整 | ✅ | 四文件均存在，与 backup 一致 |
| AC-3 | `.workflow/tools/catalog/` 目录存在且包含工具定义文件 | ✅ | `ls .workflow/tools/catalog/` 列出 `_template.md`、`agent.md`、`bash.md`、`claude-code-context.md`、`edit.md`、`grep.md`、`read.md` |
| AC-4 | 运行 `harness update` 后，`.workflow/tools/` 保持原位，不会被移动到 backup | ✅ | 同 Requirement AC-3，自动化测试通过验证 |

### chg-04
| AC | 标准 | 结论 | 备注 |
|----|------|------|------|
| AC-1 | `pytest tests/test_cli.py` 全部通过 | ✅ | 17 passed, 36 skipped，无失败 |
| AC-2 | 至少新增一个测试用例验证 `harness init` 会创建 `.workflow/tools/` | ✅ | `test_install_scaffolds_tools_directory`（第 196 行）断言 `.workflow/tools/index.md`、`.workflow/tools/catalog/agent.md`、`.workflow/tools/stage-tools.md` 存在，测试通过 |
| AC-3 | 至少新增一个测试用例验证 `harness update` 不会将 `.workflow/tools/` 移入 backup | ✅ | `test_update_does_not_archive_tools_directory`（第 232 行）先 install 再 update，断言 tools 目录与 index.md 均未被归档，测试通过 |

## AI 核查结论
全部 Requirement-level AC（5/5）与 Change-level AC（14/14）均通过自动检查确认满足。测试运行结果 17 passed, 36 skipped，无任何失败。代码、模板、当前仓库状态与需求文档完全一致，无遗漏、无越界。

## 最终判定
- [x] 通过
- [ ] 驳回
