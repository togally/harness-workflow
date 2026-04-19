# Regression Intake

## 1. Issue Title

harness update 不会为已有版本补全 testing/ 和 acceptance/ 生命周期目录

## 2. Reported Concern

引入 `testing` 和 `acceptance` 阶段后，已有版本（包括新建的 v0.2.0-refactor）的目录下没有 `testing/` 和 `acceptance/` 子目录，工作流进入这两个阶段时找不到对应目录，无法写入测试计划、测试用例、验收清单等文档。

## 3. Current Behavior

- **复现路径**：在 v0.2.0-refactor 实现前创建版本 → 实现 change 1 → 运行 `harness update` → 检查版本目录
- **实际表现**：
  - v0.2.0-refactor 目录：`changes/ requirements/ regressions/ plans/ archive/`，无 `testing/` 和 `acceptance/`
  - v0.1.0-self-optimization（旧版本）同样缺失
  - `harness update` 的 `_required_dirs` 只创建全局目录，不处理版本级目录
  - `create_version` 已更新为创建这两个目录，但无法修复已有版本
- **影响**：进入 `testing` 阶段后，Subagent 无法写入 `testing/test-plan.md`；bug 无法写入 `testing/bugs/`

## 4. Expected Outcome

`harness update` 应检测所有 `workflow/versions/active/` 下的现有版本，为每个缺少 `testing/` 或 `acceptance/` 目录的版本自动补全（`mkdir -p`，幂等操作）。

## 5. Next Step

确认为真实问题，转为新 change 修复。
