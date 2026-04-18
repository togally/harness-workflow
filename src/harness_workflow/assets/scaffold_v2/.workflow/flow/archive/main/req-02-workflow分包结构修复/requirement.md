# req-02 workflow 分包结构修复

## 背景

当前 `.workflow/` 分包在 req-01（版本重做）中完成了基础架构搭建，但遗留了以下结构性问题：

1. **evaluation/ 与主加载链断链**：`context/index.md` 的 Step 2 只说明加载 `roles/{stage}.md`，未指引加载 `evaluation/{stage}.md`。在 testing / acceptance / regression 阶段，评估规则有可能被 agent 完全跳过。

2. **`context/rules/` 是死目录**：`context/rules/workflow-runtime.yaml` 存有 harness CLI 的执行状态，但 `context/index.md` 完全未提及此目录，agent 无法感知其存在，该文件是"泄露到知识层的运行时配置"。

3. **`context/team/` 和 `context/project/` 加载时机未定义**：`context/index.md` 的加载顺序中没有 `team/development-standards.md` 和 `project/project-overview.md` 的加载规则，这两个文件对 agent 实际上也不可见。

4. **`context/backup/` 放置在知识层不当**：backup 是旧系统历史存档，放在 `context/`（知识内容层）从语义上不正确。

5. **`versions/` 是 CLI 内部状态目录，职责不明**：`versions/active/` 下的 `meta.yaml` 和 `progress.yaml` 是 harness CLI 内部生成的执行状态文件，`context/index.md` 完全未引用此目录。与 `context/rules/` 问题同质——CLI 产物泄露到了 .workflow/ 结构中，agent 无法感知其存在，也无明确处理规则。

6. **`tools/` 工具层在迁移中整体丢失**：旧系统 `workflow/tools/` 包含完整的工具定义与规则体系（`stage-tools.md` 工具白名单、`selection-guide.md` 选择指南、`maintenance.md` 维护规范、`catalog/` 单工具文件）。req-01 迁移时该层级未被建立，只留下了 `context/experience/tool/harness.md` 一个空占位符。注意：`context/experience/tool/` 目录本身是正确的（存放工具使用经验），缺失的是独立的工具定义层。

## 目标

修复后，`.workflow/` 分包结构完整体现以下理念：

- **每个目录都有明确的职责定义**，且在加载规则中被正确引用
- **主加载链无断点**：agent 按 `context/index.md` 加载后，能感知并加载所有必要规则文件
- **state/ 与 context/ 职责不混用**：运行时状态不出现在知识层
- **无语义不当的目录**：backup 等非知识内容不放在 `context/` 下

## 范围

### 包含

- 修复 `context/index.md`，将 `evaluation/`、`team/`、`project/` 纳入加载规则
- 处理 `context/rules/`：明确职责并决策保留/迁移/删除
- 处理 `context/backup/`：迁移到语义正确的位置（如 `.workflow/archive/` 或项目根）
- 明确 `versions/` 的职责定位：是 CLI 内部目录还是 agent 可读状态，并补充相应的处理规则或加载规则
- 恢复 `tools/` 工具层：在 `.workflow/` 下建立对应结构（参考旧系统 `workflow/tools/`），迁移 stage-tools.md、selection-guide.md、catalog/ 等内容，并调整路径引用
- 补充 `context/project/project-overview.md` 的基础内容

### 不包含

- 修改经验文件（`experience/`）的内容
- 修改约束文件（`constraints/`）的内容

> 注1：各角色文件的 `## 可用工具` 小节将从内联白名单改为引用 `tools/stage-tools.md`，属于结构整合的一部分，纳入本需求范围。
> 注2：`harness_workflow` CLI 包（`src/harness_workflow/core.py`）的 `versions/` 路径迁移纳入本需求范围（chg-07）。

## 验收标准

- [ ] `context/index.md` 的加载顺序覆盖所有需要被 agent 加载的子目录（evaluation/、team/、project/ 均有加载时机规则）
- [ ] `evaluation/index.md` 在主加载链中有明确引用入口
- [ ] `context/rules/` 不再作为死目录存在（已迁移、删除或职责明确文档化）
- [ ] `context/backup/` 不出现在 `context/` 目录下
- [ ] `.workflow/versions/` 已删除（无需迁移，直接删除）
- [ ] `harness version`、`harness active`、`harness use` 命令已不存在
- [ ] `harness archive <req-id> [--folder <name>]` 正常执行，支持新建和合并文件夹
- [ ] `src/harness_workflow/core.py` 中无版本相关函数和路径引用
- [ ] `harness_workflow` 包已重新安装，`harness status` / `harness next` 正常执行
- [ ] `.workflow/tools/` 工具层已恢复（含 stage-tools.md、selection-guide.md、catalog/、maintenance.md），路径引用已更新
- [ ] `context/project/project-overview.md` 有实际内容（非空模板）
- [ ] 各角色文件的 `## 可用工具` 小节已改为引用 `tools/stage-tools.md`，不再内联白名单
- [ ] 项目根 `README.md`（英文）+ `README.zh.md`（中文）已创建，含项目介绍、六层原理、安装方式、使用方式，两文件互有跳转链接
- [ ] 所有修改后，`context/index.md` 的加载顺序与实际目录结构一致，无悬空引用
