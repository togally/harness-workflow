# req-22 测试报告（V3）

**测试日期**：2026-04-16  
**测试工程师**：独立 testing agent  
**需求**：req-22 - agent引导流程优化  
**当前阶段**：testing（第三次 regression 修复后）  

---

## 验收项验证结果

### chg-01 验收

| 序号 | 验收项 | 结果 | 说明 |
|------|--------|------|------|
| 1 | `.workflow/context/roles/role-loading-protocol.md` 存在 | 通过 | 文件存在，内容完整。 |
| 2 | `role-loading-protocol.md` 定义所有角色（含顶级角色）的通用加载步骤 | 通过 | 明确包含 Step 1~7，覆盖顶级角色、stage 角色、辅助角色。 |
| 3 | `role-loading-protocol.md` 中顶级角色和 stage 角色遵循同一套前置加载流程 | 通过 | 文件首段即声明"所有角色平等：顶级角色（Director）和 stage 角色都遵循同一套前置加载流程"，Step 1~4 对全部角色通用。 |
| 4 | `.workflow/context/index.md` 是纯角色索引，标题为"Context 角色索引"或类似 | 通过 | 标题为 `# Context 角色索引`。 |
| 5 | `context/index.md` 包含角色索引表格和 `role-loading-protocol.md` 的引用 | 通过 | 包含顶级角色、stage 角色、辅助角色、抽象父类、通用协议共 5 张表格，并引用 `role-loading-protocol.md`。 |
| 6 | `context/index.md` **不再包含**任何具体的"角色加载流程"步骤说明 | **不通过** | 文件末尾仍保留 `## 如何加载角色` 章节，列出 4 步加载说明（先读 protocol、按 Step 1~7 执行、通过索引表确认角色、读取角色文件后执行）。这与第三次 regression 修复目标"只保留角色索引表格 + '按 role-loading-protocol.md 加载'的引导语"不符，且与验收项"不再包含任何具体的角色加载流程步骤说明"直接冲突。 |
| 7 | `WORKFLOW.md` 的入口引导语为：总结需求 → 去 `context/index.md` 找角色 → 按 `role-loading-protocol.md` 加载执行 | 通过 | 原文："请总结当前用户需求，然后立即读取 `.workflow/context/index.md`，在其中的角色索引表中找到你所需的角色，并严格按照 `.workflow/context/roles/role-loading-protocol.md` 的协议加载该角色文件，最后按角色 briefing 执行任务。" |
| 8 | `technical-director.md` 的 SOP 明确引用 `role-loading-protocol.md` | 通过 | SOP Step 1 明确写道："读取 `.workflow/context/roles/role-loading-protocol.md`"，Step 3 也引用该协议为 subagent 加载角色。 |
| 9 | `technical-director.md` 包含"硬门禁四：stage 必须按研发流程图流转" | 通过 | 存在完整硬门禁四，包含研发流程图、流转规则、禁止的流转。 |
| 10 | `base-role.md` 开头明确引用 `role-loading-protocol.md` 作为前置要求 | 通过 | 第 5 行明确说明："stage 角色在被加载前，必须已经按 `role-loading-protocol.md` 完成了通用加载步骤"。 |

### chg-02 验收

| 序号 | 验收项 | 结果 | 说明 |
|------|--------|------|------|
| 11 | 所有 stage 角色文件结构统一 | **不通过** | `ROLE-TEMPLATE.md` 规定标准章节顺序为：角色定义 → SOP → 可用工具 → 允许/禁止行为 → 上下文维护职责 → 职责外问题 → 退出条件 → ff 模式说明 → 流转规则 → 完成前必须检查。实际文件存在以下偏离：  <br>1. `requirement-review.md`、`planning.md`、`executing.md`、`testing.md`、`acceptance.md`、`regression.md` 均在 SOP 后插入了 `## 本阶段任务` 章节，而 `done.md`、`tools-manager.md` 没有该章节；  <br>2. `testing.md` 在 `流转规则` 和 `完成前必须检查` 之间插入了 `## 自验证 Checklist（AC 逐项检查）`；  <br>3. `acceptance.md` 在相同位置插入了 `## requirement.md 对齐检查 Checklist` 和 `## change.md 对齐检查`；  <br>4. `tools-manager.md` 在相同位置插入了 `## 返回值格式`。  <br>这些额外章节破坏了模板规定的统一章节顺序。 |
| 12 | `ROLE-TEMPLATE.md` 要求 SOP 必须覆盖角色完整生命周期 | 通过 | 模板"核心原则"和"各章节说明"均明确要求 SOP 必须覆盖初始化 → 执行 → 退出 → 交接的完整生命周期。 |
| 13 | `base-role.md` 中新增"角色生命周期中的通用加载职责"章节 | 通过 | 存在该章节，涵盖经验文件、团队规范、风险文件、流转规则的加载约定。 |

### chg-03 验收

| 序号 | 验收项 | 结果 | 说明 |
|------|--------|------|------|
| 14 | `stages.md` 命令-行为对应清晰 | 通过 | "命令与 Stage 对应关系"表格明确列出 6 个命令的作用和适用 stage，另有 `harness update` / `harness archive` 补充说明。 |
| 15 | ff/regression/done 节点说明完整 | 通过 | `stages.md` 中 ff 模式包含启动条件、自动推进规则、session-memory 规范、暂停与退出机制、AI 自主决策边界、失败处理路径；regression 在完整流转图和命令表格中均有说明；done 阶段的进入条件、动作、归档命令均明确。 |
| 16 | `done.md` 中无 `changes_review` / `plan_review` 过时引用 | 通过 | 全文搜索未发现 `changes_review` 或 `plan_review` 字样。 |
| 17 | `catalog/find-skills.md` 存在且定义了 skillhub 查询适配器 | 通过 | 文件存在，定义了 `find-skills` skill 的用途、调用方式、返回值处理、当前状态和注意事项。 |
| 18 | `keywords.yaml` 中注册了 `find-skills` | 通过 | `.workflow/tools/index/keywords.yaml` 中已注册 `tool_id: find-skills`，并关联 `catalog: catalog/find-skills.md`。 |
| 19 | `tools-manager.md` 中不再硬编码 `https://skillhub.cn/skills/find-skills` | 通过 | Step 3 描述为"调用 `find-skills` skill 查询 skillhub 商店"，未出现任何硬编码 URL。 |

### req-22 整体验收

| 序号 | 验收项 | 结果 | 说明 |
|------|--------|------|------|
| 20 | `requirement.md` 中的 4 条验收标准均已覆盖 | 部分通过 | 标准 2（harness 命令对应关系）、3（关键节点说明完整）、4（全流程走查验证）均已覆盖。标准 1（各 stage 的引导文档和角色职责一致，无明显冲突或遗漏）在内容层面无冲突，但因 item 11 发现的结构不统一问题，存在"引导文档格式不一致"的遗漏，影响了标准 1 的完全达成。 |

---

## 缺陷汇总

### 缺陷 1：context/index.md 仍包含角色加载步骤说明（对应 chg-01 验收项 6）
- **严重程度**：中
- **具体证据**：`.workflow/context/index.md` 第 47~53 行存在 `## 如何加载角色` 章节，列出 4 步加载流程。第三次 regression 修复的目标为"纯索引化"和"只保留角色索引表格 + '按 role-loading-protocol.md 加载'的引导语"，当前实现超出该范围。
- **建议修复**：删除 `## 如何加载角色` 章节，仅保留一句引导语如："所有角色的加载步骤见 `.workflow/context/roles/role-loading-protocol.md`。"

### 缺陷 2：stage 角色文件结构未完全统一（对应 chg-02 验收项 11）
- **严重程度**：中
- **具体证据**：
  - `requirement-review.md`、`planning.md`、`executing.md`、`testing.md`、`acceptance.md`、`regression.md` 均包含 `## 本阶段任务` 章节，而 `done.md`、`tools-manager.md` 没有；
  - `testing.md` 额外包含 `## 自验证 Checklist（AC 逐项检查）`；
  - `acceptance.md` 额外包含 `## requirement.md 对齐检查 Checklist` 和 `## change.md 对齐检查`；
  - `tools-manager.md` 额外包含 `## 返回值格式`。
  这些额外章节均插入在模板规定的标准章节顺序之间，破坏了结构统一性。
- **建议修复**：将 `本阶段任务` 内容合并到各角色的 SOP 或 `角色定义` 中；将 `testing.md` 和 `acceptance.md` 的 checklist 移至 `完成前必须检查` 或 `附录`；将 `tools-manager.md` 的 `返回值格式` 移至 `可用工具` 章节内或 `附录`。确保所有 stage 角色严格遵循 `ROLE-TEMPLATE.md` 的 11 个章节顺序。

---

## 整体验收结论

**结论：不通过**

req-22 在内容层面（角色定义、流转规则、命令映射、关键节点说明、find-skills 集成）已基本完成，但存在 2 项中等级缺陷：
1. `context/index.md` 未实现彻底的"纯索引化"，仍保留了应下沉到 `role-loading-protocol.md` 的角色加载步骤说明；
2. 各 stage 角色文件的结构统一性未完全达成，存在多个额外章节破坏模板规定的统一章节顺序。

---

## 是否建议进入 regression

**建议：进入 regression**

原因：
- 两项缺陷均属于设计/结构层面的问题，需要回到 planning 阶段重新调整 `context/index.md` 和多个 stage 角色文件的章节结构；
- 修复动作明确且范围可控，预计可在 1 个 regression 周期内完成；
- 若不修复，将导致 `ROLE-TEMPLATE.md` 的约束力被削弱，长期影响 agent 引导文档的一致性和可维护性。
