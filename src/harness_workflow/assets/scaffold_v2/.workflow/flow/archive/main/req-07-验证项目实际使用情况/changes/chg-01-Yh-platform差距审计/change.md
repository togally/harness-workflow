# Change: chg-01

## Title

Yh-platform 项目 Harness workflow 差距审计

## Goal

全面读取 Yh-platform 的 `.workflow/` 目录，并与 harness-workflow 最新状态进行对比，产出详细的差距审计报告。

## Scope

**包含**：
- 逐文件对比 `stages.md`、角色文件、约束文件、工具清单
- 对比 `state/` 目录结构和字段命名
- 对比 `flow/` 目录结构和归档规范
- 检查 `harness_workflow` 包中 scaffold 模板的来源和版本
- 识别 `harness install` 安装的旧版本原因

**不包含**：
- 实际修复 Yh-platform 的文件（属于 chg-03）
- 修改 install/update 代码（属于 chg-02）

## Acceptance Criteria

- [ ] 差距审计报告已产出，列出所有缺失/过时的文件和字段
- [ ] 已识别 `harness install` 安装旧版本的具体原因
