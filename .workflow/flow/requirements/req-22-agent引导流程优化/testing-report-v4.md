# Testing Report V4: req-22 (agent引导流程优化)

**测试日期**: 2026-04-17
**测试者**: 独立 testing agent
**状态**: testing 阶段

---

## 验收项验证结果

### chg-01 验收

#### 1. `role-loading-protocol.md` 存在，定义所有角色通用加载步骤
**结果**: PASS
**证据**: 文件 `.workflow/context/roles/role-loading-protocol.md` 存在，包含 Step 1~7 的通用加载流程（runtime.yaml → 背景文件 → index.md 确认身份 → 加载角色文件 → base-role → 附加上下文 → 开始执行），并附有流程速查图和禁止行为列表。

#### 2. `WORKFLOW.md` 引导语为：总结需求 → 去 `context/index.md` 找角色 → 按 `role-loading-protocol.md` 加载执行
**结果**: PASS
**证据**: `WORKFLOW.md` "入口" 章节原文："请总结当前用户需求，然后立即读取 `.workflow/context/index.md`，在其中的角色索引表中找到你所需的角色，并严格按照 `.workflow/context/roles/role-loading-protocol.md` 的协议加载该角色文件，最后按角色 briefing 执行任务。" 与验收描述完全一致。

#### 3. `context/index.md` 是纯角色索引，无具体加载步骤说明，包含角色索引表格和 protocol 引用
**结果**: PASS
**证据**: `.workflow/context/index.md` 仅包含角色索引表（顶级角色、Stage 执行角色、辅助角色、抽象父类、通用协议），无任何 Step-by-Step 加载说明；开头明确引用 `.workflow/context/roles/role-loading-protocol.md`。

#### 4. `technical-director.md` SOP 引用 `role-loading-protocol.md`，包含硬门禁四
**结果**: PASS
**证据**: `.workflow/context/roles/directors/technical-director.md` 中 "Step 1: 按角色加载协议完成前置加载" 明确引用 `role-loading-protocol.md`；"硬门禁四：stage 必须按研发流程图流转" 存在且包含完整流程图和禁止的流转说明。

#### 5. `base-role.md` 开头引用 `role-loading-protocol.md`
**结果**: PASS
**证据**: `.workflow/context/roles/base-role.md` 第 5 行原文："本文件中的加载约定是对 `.workflow/context/roles/role-loading-protocol.md` 的补充和细化。stage 角色在被加载前，必须已经按 `role-loading-protocol.md` 完成了通用加载步骤……"

---

### chg-02 验收

#### 6. 所有 stage 角色文件严格遵循 `ROLE-TEMPLATE.md` 的 11 个标准章节顺序
**结果**: PASS
**证据**: 使用脚本提取 8 个 stage 角色文件（requirement-review、planning、executing、testing、acceptance、regression、done、tools-manager）的所有二级标题，过滤后均严格匹配以下顺序：
1. 角色定义
2. 标准工作流程（SOP）
3. 可用工具
4. 允许的行为
5. 禁止的行为
6. 上下文维护职责
7. 职责外问题
8. 退出条件
9. ff 模式说明
10. 流转规则
11. 完成前必须检查

#### 7. `ROLE-TEMPLATE.md` 要求 SOP 必须覆盖角色完整生命周期
**结果**: PASS
**证据**: `.workflow/context/roles/ROLE-TEMPLATE.md` 中 "标准工作流程（SOP）" 章节明确要求："必须覆盖角色的完整生命周期：初始化 → 执行 → 退出 → 交接"，且每个 stage 角色文件的 SOP 均包含对应步骤。

#### 8. `base-role.md` 中新增通用加载职责章节
**结果**: PASS
**证据**: `.workflow/context/roles/base-role.md` 第 41 行存在独立章节 `## 角色生命周期中的通用加载职责`，涵盖经验文件加载、团队与项目上下文、风险文件、流转规则等内容。

---

### chg-03 验收

#### 9. `stages.md` 命令-行为对应清晰
**结果**: PASS
**证据**: `.workflow/flow/stages.md` 包含 "命令与 Stage 对应关系" 表格，明确列出 `harness requirement`、`harness change`、`harness next`、`harness ff`、`harness archive`、`harness regression` 的作用和适用 Stage；每个 Stage 定义中也明确了进入条件、退出条件、必须产出和下一步。

#### 10. ff/regression/done 节点说明完整
**结果**: PASS
**证据**:
- **ff**: `stages.md` 中有独立的 `harness ff（fast-forward）` 章节，涵盖启动条件、自动推进规则、session-memory 规范、暂停与退出机制、AI 自主决策边界、失败处理路径，内容完整。
- **regression**: `stages.md` 流转图中包含 regression 节点及分支路由；`.workflow/evaluation/regression.md` 详细定义诊断流程、diagnosis.md 格式、路由命令。
- **done**: `stages.md` 中 done Stage 定义明确；`context/roles/done.md` 包含六层回顾检查清单、工具层适配性问题模板、经验沉淀验证步骤、输出规范建议、建议转 suggest 池流程。

#### 11. `done.md` 中无 `changes_review` / `plan_review` 过时引用
**结果**: PASS
**证据**: 使用 grep 搜索 `.workflow/context/roles/done.md`，未找到 `changes_review` 或 `plan_review` 任何匹配。

#### 12. `catalog/find-skills.md` 存在且定义了 skillhub 查询适配器
**结果**: PASS
**证据**: `.workflow/tools/catalog/find-skills.md` 存在，定义了用途、前提条件、调用方式（`skillhub find-skills` 或 `Skill` 工具）、预期行为、返回值处理（注册到 keywords.yaml 或记录 missing-log.yaml）、当前状态和注意事项。

#### 13. `keywords.yaml` 中注册了 `find-skills`
**结果**: PASS
**证据**: `.workflow/tools/index/keywords.yaml` 中 `tool_id: "find-skills"` 已注册，keywords 包含 `skill`、`skills`、`skillhub`、`查找技能`、`发现工具`、`扩展工具`、`工具查询`、`未命中`。

#### 14. `tools-manager.md` 中不再硬编码 skillhub URL
**结果**: PASS
**证据**: 使用 grep 搜索 `.workflow/context/roles/tools-manager.md`，未找到任何硬编码的 skillhub URL（如 `https://skillhub` 等）。toolsManager 通过调用 `find-skills` skill 查询 skillhub 商店，未出现直接访问 URL 的情况。

---

### req-22 整体验收

#### 15. `requirement.md` 中的 4 条验收标准均已覆盖
**结果**: PASS
**证据**:
- **标准1** "各 stage 的引导文档和角色职责一致，无明显冲突或遗漏"：所有 stage 角色文件均遵循统一模板（ROLE-TEMPLATE.md），`stages.md` 中的 stage 定义与角色文件一一对应，`role-loading-protocol.md` 统一了加载流程，未发现冲突。
- **标准2** "`harness` 命令触发条件与 agent 行为对应关系明确"：`stages.md` 中的命令表格和 Stage 定义章节清晰说明了各命令的作用、适用 Stage 和触发条件。
- **标准3** "ff 模式、regression、done 等关键节点的引导说明完整"：`stages.md` 和对应 evaluation/role 文档中对 ff、regression、done 均有独立、详细的章节说明。
- **标准4** "完成一轮 agent 全流程走查验证，确保引导逻辑可执行"：本次 testing agent 按照 handoff 文档对 15 个验收项进行了独立走查验证，所有文件均可读取、所有流程步骤均有文档支撑，引导逻辑可执行。

---

## 总体结论

**全部 15 项验收标准均通过。**

**建议**: 接受 req-22 交付，无需进入 regression。可推进至 acceptance 阶段或按流程归档。
