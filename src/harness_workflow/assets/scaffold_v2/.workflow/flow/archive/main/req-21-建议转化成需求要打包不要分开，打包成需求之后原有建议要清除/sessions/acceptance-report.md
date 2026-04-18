# Acceptance Report: req-21 "suggest 批量转需求支持打包与自动清理"

**Date:** 2026-04-15  
**Reviewer:** Acceptance Agent  
**Scope:** `--apply-all` 打包与清理功能

---

## Requirement.md 验收标准核查

| # | 标准 | 核查方式 | 结论 | 备注 |
|---|---|---|---|---|
| 1 | `--apply-all` 支持将所有 pending suggest 打包为**一个**需求 | 自动检查：临时项目端到端测试 | ✅ | 3 条 suggest 打包为 req-01 |
| 2 | 打包后的需求标题可由用户指定（`--pack-title`），若未指定则使用默认标题 | 自动检查：分别测试默认和自定义标题 | ✅ | 默认标题为"批量建议合集（N条）"，自定义标题正常生效 |
| 3 | 转化成功后，所有被处理的 suggest 文件从 `.workflow/flow/suggestions/` 中**删除** | 自动检查：验证 suggest 目录为空 | ✅ | suggest 文件已删除 |
| 4 | 命令输出清晰的转换结果报告（成功删除的 suggest 数量及对应 ID、生成的 req ID） | 自动检查：捕获 CLI stdout | ✅ | 输出包含 "Packed N suggestion(s) into req-XX:" |
| 5 | 当 suggest 池为空或无 pending suggest 时，命令给出明确提示且不报错 | 自动检查：运行 `--apply-all` 于空池 | ✅ | 输出 "No pending suggestions found." |
| 6 | CLI 帮助和 README 文档已更新 | 自动检查：搜索 README.md | ✅ | README 和 scaffold_v2 均已更新 |

---

## Change.md 验收标准核查

### chg-01 打包与清理逻辑实现

| # | 标准 | 结论 | 备注 |
|---|---|---|---|
| 1 | `--apply-all` 将所有 pending suggest 打包为**一个**需求 | ✅ | TC-01 验证通过 |
| 2 | 未指定 `--pack-title` 时使用合理的默认标题 | ✅ | "批量建议合集（N条）" |
| 3 | 转化成功后，suggest 文件被**删除** | ✅ | TC-03 验证通过 |
| 4 | 输出报告包含成功删除的 suggest 数量和生成的 req ID | ✅ | 输出格式正确 |
| 5 | 无 pending suggest 时给出明确提示且不报错 | ✅ | TC-04 验证通过 |

### chg-02 文档与验证

| # | 标准 | 结论 | 备注 |
|---|---|---|---|
| 1 | README 已更新 `--apply-all` 和 `--pack-title` 的说明 | ✅ | README 和 scaffold_v2 已同步 |
| 2 | 临时项目验证：多条 suggest 打包成一个 req，且原文件被删除 | ✅ | testing-report 全部 PASS |
| 3 | 包已重新安装 | ✅ | `pipx inject` 已完成 |

---

## 范围对齐检查

- **背景对齐**：实际交付解决了 `--apply-all` 产生过多零散需求、suggest 池文件膨胀的问题。✅
- **目标对齐**：实现了打包成一个需求和自动删除 suggest 文件。✅
- **范围对齐**：未修改单条 `--apply` 行为，未添加排序/筛选，未自动执行需求。✅

---

## AI 核查结论

所有验收标准均已满足，测试报告 5/5 通过。

**判定：通过**

---

## 人工验收待确认项

无。本需求为纯 CLI 功能，所有验收项均可通过自动化测试和文档检查覆盖。

---

## 最终判定

**通过** — 所有验收标准已满足，可进入 done 阶段。
