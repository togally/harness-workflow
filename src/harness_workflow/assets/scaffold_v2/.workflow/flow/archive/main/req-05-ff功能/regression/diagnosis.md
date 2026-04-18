# Regression Diagnosis

## 问题描述

用户操作的外部项目（大疆 OSD 模型相关）使用了 Harness workflow。在处理 `DockDetail` 字段缺失问题时，会话经历了以下异常链：

1. 用户提示 "去官网上云API的文档搜索下"
2. Agent 调用 `Skill(websearch)`
3. 平台返回 `Error: Unknown skill: websearch`
4. 后续所有对话（包括 "为什么卡住了？"、多次 `/harness-next`）均返回 `API Error: 400`
5. 会话完全卡住，无法通过 Harness 命令恢复

## 根因分析

### 直接原因
`Skill(websearch)` 不是 Claude Code 标准内置 skill，也未在该外部项目中安装/定义，导致调用失败。

### 深层原因（待确认分支）

**分支 A：外部项目文档/配置缺陷**
- 如果外部项目的角色文件、plan.md 或工具清单中明确要求或暗示可以使用 `websearch`，则属于错误引用未安装 skill 的配置缺陷。
- 这种缺陷应在外部项目内修复，不属于 harness-workflow 核心问题。

**分支 B：Agent 自主决定调用未验证的 skill，且缺少 skill 时无搜索安装机制**
- 如果用户只是口头说 "搜索下"，agent 自行决定调用 `Skill(websearch)` 而未先检查可用技能列表，这属于 agent 行为问题。
- Harness workflow 目前的约束和角色文件中，并未明确要求 agent 在调用 skill 前验证其存在性。
- 更重要的是：**当发现 skill 缺失时，流程没有定义下一步动作**。理想情况下，agent 应该先搜索是否有同名或功能相近的可用 skill，尝试安装或寻找替代方案，而不是直接失败或卡住。

**分支 C：Harness workflow 缺乏失败恢复机制**
- 即使 skill 调用失败是偶发或误操作，后续所有 harness 命令都因 `API Error: 400` 失效，说明会话状态可能已损坏。
- Harness workflow 当前没有定义 "底层平台调用失败后如何重置或恢复" 的恢复路径（`constraints/recovery.md` 主要覆盖任务失败，未覆盖平台级 400 错误）。
- 这是一个 **流程韧性缺陷**，即使根因不在 Harness，也应该有恢复策略。

## 当前结论

- **是否为 harness-workflow 的真实缺陷**：**是，至少分支 C 是**。
  - 无论 skill 调用失败是谁的责任，Harness workflow 作为流程框架，应当定义 "平台级错误（如 API 400）导致会话不可用时" 的恢复路径。
  - 此外，需要检查 harness-workflow 自身的模板/文档中是否推荐了不存在的技能（分支 A）。

- **路由决定**：
  - 先确认分支 A（通过外部项目的文件检查）。
  - 同时把分支 C 作为一个明确的 **流程改进点**：在 `constraints/recovery.md` 中增加 "平台 API 错误/会话损坏" 的恢复路径。
  - 由于这是流程层面的改进，属于需求/设计问题，修复后应当更新 req-05 或新增变更，然后回到 `planning` 阶段继续。

## 建议的修复动作

1. **短期**：要求用户补充外部项目的触发文件（`required-inputs.md` 已填写）。
2. **中期**：在 harness-workflow 的 `constraints/recovery.md` 中新增条目：
   - 当遇到连续 API Error 400 且无法通过正常 Harness 命令恢复时，建议用户执行 `/clear` 或新开 agent，并通过 `handoff.md` 恢复任务状态。
3. **长期**：在角色文件中补充 "调用 skill 前应先确认其在当前环境中可用" 的行为约束。
