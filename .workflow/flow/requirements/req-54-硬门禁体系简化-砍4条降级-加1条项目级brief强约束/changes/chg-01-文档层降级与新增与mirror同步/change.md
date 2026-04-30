---
id: chg-01
title: "文档层降级与新增与mirror同步"
parent_req: req-54
operation_type: change
---

## Goal

完成 req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束）**文档层全部降级 + 新增**：WORKFLOW.md 全局硬门禁段砍 2 条；base-role.md 硬门禁一 / 二段标题改 + reasons 注 + 清单总览移除 2 行；base-role.md 新增硬门禁八整段；harness-manager.md / stage-role.md 同步硬门禁清单引用；4 文件 scaffold_v2 mirror 同步。

## Scope

### In scope（精确文件清单）

**Live 文件（4 个）**：
- `WORKFLOW.md` — 全局硬门禁段砍 2 条（移除 2 / 4，保留 1 / 3）+ 加注脚说明
- `.workflow/context/roles/base-role.md` — 硬门禁一 / 二段标题改 + reasons 注 + 硬门禁清单总览移除 2 行 + 新增硬门禁八整段
- `.workflow/context/roles/harness-manager.md` — 同步硬门禁清单引用（如有），新增 §3.6 「按硬门禁八 brief 项目级加载链」子条款（基础占位，正文留 chg-02 完整落地）
- `.workflow/context/roles/stage-role.md` — 「继承自 base-role 的执行清单」表内"硬门禁一"/"硬门禁二"行同步降级注

**Mirror 文件（4 个）**：
- `src/harness_workflow/assets/scaffold_v2/.workflow/../WORKFLOW.md`（注：scaffold_v2 mirror 不含 WORKFLOW.md，则同步至 WORKFLOW.md 模板镜像位置；本 chg 实施时核实）
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md`
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md`
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md`

### Out of scope

- 不动 src/ Python 代码
- 不写测试（chg-03 负责）
- 不动 stages.md 主体（OQ-5 仅"新增一段说明"非本 chg 必做项；若 stages.md 已有 conversation_mode 段则补一句即可）

## Acceptance

- AC-01 / AC-02 / AC-03 / AC-04 / AC-06 / AC-07（来自 req-54 requirement.md）
- diff -rq live mirror 4 对全 silent

## Dependencies

- 上游：req-54 requirement.md（OQ Verdicts 锁定）
- 下游：chg-02（引用 chg-01 落地的 base 八条款）/ chg-03（lint chg-01 落地结果）
