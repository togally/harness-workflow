# req-22 Testing Report V2

> 测试工程师：独立测试 agent
> 日期：2026-04-16
> 需求：req-22 - agent引导流程优化
> 状态：当前变更已全部执行完毕，包含两次 regression 修复

---

## chg-01 验收

### 1. `.workflow/context/roles/directors/technical-director.md` 存在且内容完整
**结果：通过**

文件存在，内容包含：角色定义、硬门禁（5条）、SOP（Step 1~7）、允许/禁止行为、上下文维护职责、ff 协调职责、职责外问题处理、done 阶段行为、退出条件、流转规则、完成前必须检查。结构完整。

---

### 2. `technical-director.md` 包含"硬门禁四：stage 必须按研发流程图流转"，且流程图完整
**结果：通过**

文件第 23-46 行明确列出"硬门禁四：stage 必须按研发流程图流转"，包含 ASCII 流程图：
- 正向流程：requirement_review → planning → executing → testing → acceptance → done
- regression 分支：任意阶段 → regression →（需求/设计问题 → requirement_review；实现/测试问题 → testing）
- 同时包含流转规则、禁止的流转说明。

---

### 3. `technical-director.md` 的 SOP 覆盖角色完整生命周期
**结果：通过**

SOP 包含 Step 1（读取运行时状态）→ Step 2（加载自身角色）→ Step 3（根据 stage 路由执行角色）→ Step 4（派发 subagent 任务）→ Step 5（监控上下文与异常）→ Step 6（处理阶段流转）→ Step 7（done 阶段六层回顾）。覆盖初始化、执行、退出、交接完整生命周期。

---

### 4. `WORKFLOW.md` 极简化：仅保留全局硬门禁 + 一句话引导到 `context/index.md`
**结果：通过**

`WORKFLOW.md` 全文仅 13 行：
- 全局硬门禁 4 条
- "入口"章节仅一句话："请立即读取 `.workflow/context/index.md`，按照其中的**角色索引**找到你的角色，并按照**角色加载流程**执行。"
无过细的"入口步骤"说明。

---

### 5. `WORKFLOW.md` 中不再有过细的"入口步骤"说明（如"1.读取本文件 2.读取 index.md..."）
**结果：通过**

经全文检查，`WORKFLOW.md` 中无编号步骤列表，无"1.读取本文件 2.读取 index.md"这类过细说明。

---

### 6. `.workflow/context/index.md` 标题为"Context 角色索引与加载规则"或类似，同时包含：
- **角色索引**章节（表格形式：角色/类型/职责/文件路径）
- **角色加载流程**章节（Step 1~6 的步骤说明）
**结果：通过**

`index.md` 标题为"Context 角色索引与加载规则"。
- "角色索引"章节包含：顶级角色（Director）、Stage 执行角色、辅助角色、抽象父类，均以表格形式列出角色名称/职责/文件路径。
- "角色加载流程"章节包含 Step 1~6 的详细说明，以及流程速查图。

---

### 7. `context/index.md` 不再保留经验加载/风险扫描等不属于索引的职责
**结果：通过**

经全文检查，`context/index.md` 中无"经验加载"、"风险扫描"、"流转规则"等不属于纯索引和加载流程的职责。这些职责已下沉到 `base-role.md` 的"角色生命周期中的通用加载职责"章节。

---

## chg-02 验收

### 8. 所有 stage 角色文件结构统一
**结果：通过**

检查了以下 stage 角色文件：
- `requirement-review.md`
- `planning.md`
- `executing.md`
- `testing.md`
- `acceptance.md`
- `regression.md`
- `done.md`
- `tools-manager.md`

所有文件均遵循统一章节顺序：角色定义 → 标准工作流程（SOP）→ 可用工具 → 允许的行为 → 禁止的行为 → 上下文维护职责 → 职责外问题 → 退出条件 → ff 模式说明 → 流转规则 → 完成前必须检查。`done.md` 在标准结构后保留了附录（六层检查清单、工具层适配性问题模板等），符合 `ROLE-TEMPLATE.md` 中的特殊说明。

---

### 9. `.workflow/context/roles/ROLE-TEMPLATE.md` 要求 SOP 必须覆盖角色完整生命周期
**结果：通过**

`ROLE-TEMPLATE.md` 第 9-13 行核心原则明确："每个角色必须包含且仅包含两类流程定义"，其中第一类为"角色的工作流程（Role Lifecycle）"。第 42-53 行"标准工作流程（SOP）"章节说明中明确要求："必须覆盖角色的完整生命周期（初始化 → 执行 → 退出 → 交接）"。

---

### 10. `base-role.md` 与各 stage 角色无冲突
**结果：通过**

经对比检查：
- `base-role.md` 定义的硬门禁一（工具优先）、硬门禁二（操作说明与日志）在各 stage 角色中未被覆盖或否定。
- `base-role.md` 新增的"角色生命周期中的通用加载职责"（经验文件、团队与项目上下文、风险文件、流转规则）与各 stage 角色的 SOP 互补，无冲突。
- `base-role.md` 的"Session Start 约定"和"Stage 切换上下文交接约定"与 `technical-director.md` 的 Step 3/Step 6 一致。

---

### 11. `base-role.md` 中新增"角色生命周期中的通用加载职责"章节
**结果：通过**

`base-role.md` 第 39-65 行包含"角色生命周期中的通用加载职责"章节，详细规定了经验文件加载、团队与项目上下文加载、风险文件扫描、流转规则读取等通用职责。

---

## chg-03 验收

### 12. `.workflow/flow/stages.md` 命令与 stage 对应关系清晰
**结果：通过**

`stages.md` 第 175-185 行"命令与 Stage 对应关系"表格清晰列出：
- `harness requirement` / `harness change` / `harness next` / `harness ff` / `harness archive` / `harness regression`
每条命令的作用、适用 stage 均明确。

---

### 13. ff/regression/done 节点说明完整
**结果：通过**

- **ff 节点**：`stages.md` 第 94-171 行完整说明启动条件、自动推进规则、session-memory 规范、暂停与退出机制、AI 自主决策边界、失败处理路径。
- **regression 节点**：`stages.md` 流转图和 `regression.md` 角色文件均完整说明触发条件、诊断流程、恢复路径。
- **done 节点**：`stages.md` 第 51-58 行说明进入条件、动作、归档命令；`done.md` 角色文件详细说明六层回顾检查清单和输出规范。

---

### 14. `done.md` 中无 `changes_review` / `plan_review` 过时引用
**结果：通过**

经全文 grep 搜索，`done.md` 中未出现 `changes_review` 或 `plan_review` 字样。流程完整性检查项中列出的阶段为：requirement_review、planning、executing、testing、acceptance，与实际 stage 列表一致。

---

### 15. `catalog/find-skills.md` 存在且定义了 skillhub 查询适配器
**结果：通过**

文件存在（`.workflow/tools/catalog/find-skills.md`），内容定义了：
- 用途：本地索引未命中时调用 `find-skills` skill 查询 skillhub 商店
- 调用方式（skillhub CLI 和 Skill 工具两种）
- 预期行为、返回值处理、当前状态、注意事项

---

### 16. `keywords.yaml` 中注册了 `find-skills`
**结果：通过**

`.workflow/tools/index/keywords.yaml` 第 7-10 行注册了 `find-skills`：
```yaml
- tool_id: "find-skills"
  keywords: ["skill", "skills", "skillhub", "查找技能", "发现工具", "扩展工具", "工具查询", "未命中"]
  catalog: "catalog/find-skills.md"
  description: "调用 find-skills skill 查询 skillhub 商店发现其他可用 skills"
```

---

### 17. `tools-manager.md` 中不再硬编码 `https://skillhub.cn/skills/find-skills`
**结果：通过**

经全文 grep 和人工检查，`tools-manager.md` 中未出现 `https://skillhub.cn/skills/find-skills` 字样。Step 3 描述为："调用 `find-skills` skill 查询 skillhub 商店"，符合抽象要求。

---

## req-22 整体验收

### 18. requirement.md 中的 4 条验收标准均已覆盖
**结果：通过**

req-22 `requirement.md` 中的 4 条验收标准：

1. **各 stage 的引导文档和角色职责一致，无明显冲突或遗漏**
   - 通过 chg-02 统一了所有 stage 角色结构，`base-role.md` 与 `ROLE-TEMPLATE.md` 确保一致性，无冲突。

2. **`harness` 命令触发条件与 agent 行为对应关系明确**
   - 通过 chg-03 更新 `stages.md`，命令与 stage 对应关系表格清晰，各角色文件的"流转规则"章节也明确了命令行为。

3. **ff 模式、regression、done 等关键节点的引导说明完整**
   - 通过 chg-03，`stages.md` 中 ff 节点说明完整（启动条件、推进规则、暂停/退出、决策边界、失败处理）；`regression.md` 和 `constraints/recovery.md` 覆盖 regression 节点；`done.md` 覆盖 done 节点。

4. **完成一轮 agent 全流程走查验证，确保引导逻辑可执行**
   - `session-memory.md` 中记录了 chg-03 的全流程走查报告，从 session start 到 executing 阶段逐节点验证，结论为通过。走查中发现的问题（`changes_review`/`plan_review` 过时引用）已修复。

---

## 整体验收结论

**通过**

全部 17 项验收项均通过，req-22 的 4 条验收标准均已覆盖。两次 regression 修复内容已验证落实，无遗留问题。

**建议**：无需进入 regression，可推进至 acceptance。
