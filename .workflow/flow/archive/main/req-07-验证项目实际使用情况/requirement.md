# Requirement

## 1. Title

验证项目实际使用情况

## 2. Goal

当前 Harness workflow 已经过多次迭代（req-01 ~ req-06），新增/完善了版本管理、分包结构、done 阶段六层回顾、上下文维护、ff 自动推进、done 报告时长记录等机制。但大部分验证基于理论推导和自举测试，缺乏在**真实业务项目**中的使用反馈。

本需求的目标是：**在真实业务项目 `/Users/jiazhiwei/IdeaProjects/Yh-platform` 中检查并修复 Harness workflow 的部署问题**，验证流程在真实场景下的可用性，收集使用过程中的痛点、遗漏场景和优化建议。

## 3. Background

用户已通过 `cc install` 在 `Yh-platform` 项目中部署了 Harness workflow，并尝试使用它完成了需求 `req-01-dockDetail新增字段`。但经初步检查发现，安装产出存在**严重的版本不同步问题**：

1. **安装模板严重过时**：`stages.md`、角色文件、`state/*.yaml` 结构均为旧版，缺少 req-03 ~ req-06 的所有改进（如六层回顾角色、ff 模式、时长记录等）
2. **state 结构不兼容**：`runtime.yaml` 缺少 `ff_mode`、`ff_stage_history`；`requirements/*.yaml` 使用旧字段名（`req_id` 而非 `id`，`created` 而非 `created_at`），缺少 `started_at`、`stage_timestamps`、`completed_at`
3. **session-memory 缺失**：`state/sessions/` 目录为空，需求执行过程中未按规范保存各 stage 的 session-memory
4. **归档产物不完整**：archive 下的 req-01 缺少 `done-report.md`，testing 产物命名为 `test-results.md` 而非 `testing-report.md`，session-memory 散落在 change 目录下而非 `state/sessions/`
5. **活跃需求未清理**：`flow/requirements/` 下仍残留 req-01 目录，与 archive 中的副本并存

这些问题表明 **harness install / harness update 的模板同步机制存在缺陷**，安装出的项目没有继承最新的流程规范和产物模板。

## 4. Scope

**包含**：
- 以 `Yh-platform` 项目为验证对象，全面审计其 `.workflow/` 目录与最新规范的差距
- 修复/升级 `Yh-platform` 的 Harness workflow 模板到最新版本
- 识别并记录 `harness install` / `harness update` 未同步最新模板的具体原因
- 修复 install/update 机制（如 scaffold 模板未更新、CLI 命令未打包最新文件等）
- 补全 req-01 缺失的产物（如 done-report.md、state/sessions/ 下的 session-memory）
- 产出验证报告和改进建议清单

**不包含**：
- 修改 Yh-platform 的业务代码
- 重新执行 req-01 的代码实现（只补全流程产物和文档）
- 开发全新的自动化监控系统

## 5. Acceptance Criteria

- [ ] `Yh-platform` 的 `.workflow/` 结构与 harness-workflow 最新规范的对齐清单已产出
- [ ] `Yh-platform` 的 Harness workflow 已升级到最新版本（核心文档和角色文件已同步）
- [ ] `harness install` / `harness update` 的缺陷已定位并修复
- [ ] req-01 的缺失产物已补全（至少包含 done-report.md 和按规范重放的 session-memory）
- [ ] 验证报告已产出，包含：发现的问题、根因分析、修复动作、改进建议

## 6. Split Rules

### chg-01 Yh-platform 项目 Harness workflow 差距审计

全面读取 `Yh-platform/.workflow/` 并与 harness-workflow 最新状态对比：
- 列出所有缺失/过时的文件和字段
- 识别 `harness install` 安装的旧版本来源
- 产出差距审计报告

### chg-02 修复 harness install/update 模板同步机制

定位并修复 CLI install/update 命令的模板缺陷：
- 检查 `harness_workflow` 包中的 scaffold 模板是否包含最新文件
- 检查 pip install / pipx inject 后的包内容是否与仓库最新状态一致
- 修复模板同步问题并重新验证 install

### chg-03 升级 Yh-platform 的 workflow 到最新版本

在 `Yh-platform` 项目中执行升级：
- 运行修复后的 `harness update`（或手动同步核心文件）
- 更新 `runtime.yaml` 和 `state/requirements/*.yaml` 到新结构
- 确保核心文档（stages.md、角色文件、约束文件）与最新规范一致

### chg-04 补全 req-01 缺失产物

根据现有文件记录，补全 req-01 的规范产物：
- 补全 `state/sessions/req-01/` 下的 session-memory、testing-report、acceptance-report、done-report
- 修复归档目录结构（清理 `flow/requirements/` 中的残留，确保 archive 结构完整）

### chg-05 验证报告与经验沉淀

产出验证报告并沉淀经验：
- 记录 install/update 模板同步问题的根因
- 在 `context/experience/tool/harness.md` 或新文件中增加"安装后必须验证模板版本"的经验
