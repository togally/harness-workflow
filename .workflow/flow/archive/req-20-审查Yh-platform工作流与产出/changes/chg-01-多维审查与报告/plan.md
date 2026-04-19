# Plan

## 执行步骤

### Step 1: 读取 Yh-platform 项目的状态与流程基线
- 读取 `/Users/jiazhiwei/IdeaProjects/Yh-platform/.workflow/state/runtime.yaml`
- 读取 `/Users/jiazhiwei/IdeaProjects/Yh-platform/WORKFLOW.md`（确认 Harness 版本基线）
- 读取 `/Users/jiazhiwei/IdeaProjects/Yh-platform/.workflow/flow/stages.md`（了解阶段流转规则）

### Step 2: 逐个需求读取状态与制品
按 req-01 → req-02 → req-03 → req-04 → req-05 顺序，对每个需求执行：
- 读取 `state/requirements/req-XX.yaml`（提取阶段时间戳、stage 历史）
- 读取 `requirement.md`
- 遍历 `changes/` 或 `archive/req-XX/changes/` 目录，记录变更数量和关键产物
- 读取 `done-report.md`（如存在）
- 读取 `session-memory.md`（如存在）
- 记录 testing / acceptance / regression 相关报告文件

### Step 3: 审查经验产出
- 读取 `.workflow/context/experience/index.md`
- 遍历 `.workflow/context/experience/stage/` 和 `tool/`、`risk/`，记录：
  - 哪些文件有实质内容（非占位符）
  - 哪些文件仍为空模板
  - 每个经验的来源需求 ID

### Step 4: 审查工具层变更
- 读取 `.workflow/tools/index.md`
- 检查 `tools/catalog/` 和 `tools/stage-tools.md` 等是否有新增或修改
- 对比 req-01 之前的状态（如有 backup 可参考）

### Step 5: 汇总 bug 与反思
- 从 regression/diagnosis.md 中提取所有真实问题
- 分类：编译阻断、字段映射错误、null 兜底遗漏、语法错误、结构不匹配等
- 检查每个问题的根因分析质量和修复记录完整性

### Step 6: 撰写审查报告
- 按 5 个维度组织报告结构
- 每个需求给出简要评分/结论
- 输出整体评价和改进建议

## 产物

1. 审查报告（Markdown），建议输出到本变更目录或需求根目录的 `review-report.md`
2. 问题清单（可选附表）

## 依赖

- 无前置变更依赖
- 本变更为 req-20 的唯一变更，独立完成

## 执行顺序

单独执行，无需串并行编排。

## 预计上下文消耗

- **文件读取次数**：约 40-60 次（5 个需求 × 平均每需求 8-12 个文件 + experience/tools 层约 10 个文件）
- **大文件读取**：无特别大的文件（单文件均 < 500 行）
- **总体评估**：中等负载，预计不会触发上下文维护阈值
