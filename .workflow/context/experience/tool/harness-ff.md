# Harness Fast-Forward (ff) Experience

## 经验一：ff 模式的核心价值是消除"等待确认"阻塞，而非跳过工作

### 场景
req-05 设计 ff 模式时，用户最初的理解可能是"一路跳过所有阶段"。

### 经验内容
ff 模式的设计边界必须非常清晰：
- **保留**：每个 stage 的实质产出（requirement.md、change.md、plan.md、代码变更、测试报告、验收报告、session-memory）
- **移除**：用户逐 stage 的人工确认阻塞点
- **替代**：由 AI 根据上下文和最佳实践自主判断何时推进

如果 ff 模式被设计成"跳过工作"，会导致：
- 文档缺失，后续维护无法理解决策
- 测试和验收被跳过，质量不可控
- 经验无法沉淀

正确的 ff 模式推进逻辑：
```
subagent 完成当前 stage 任务
    ↓
主 agent 检查退出条件
    ↓
保存 session-memory
    ↓
自动更新 runtime.yaml 到下一 stage
    ↓
继续下一 stage 的 subagent 任务
```

### 来源
req-05 ff 模式语义设计

---

## 经验二：skill 缺失时，agent 有责任主动搜索替代方案，不应直接卡住

### 场景
req-05 的 regression 分析中，外部项目出现 `Skill(websearch)` 调用失败（Unknown skill），随后会话因连续 API Error 400 完全卡住。

### 经验内容
当 agent 遇到 `Error: Unknown skill: xxx` 时，标准恢复流程：

```
Step 1  停止重试同一 skill
Step 2  检查本地 skill 目录（.claude/skills/、.qoder/skills/）
Step 3  搜索功能相近的已安装 skill
Step 4  尝试用原生工具替代（如没有 websearch skill 时，尝试 WebSearch/WebFetch 工具）
Step 5  若仍无法解决，向用户报告已尝试的替代方案
Step 6  记录到 session-memory
```

**反例**：
- 直接失败并停止，不尝试任何恢复
- 连续调用不存在的 skill 导致平台进入异常状态
- 不向用户说明已尝试的替代路径

**关键教训**：在调用任何非标准 skill 前，agent 应先验证其存在性；发现缺失后，必须执行恢复流程而非直接放弃。

### 来源
req-05 regression 分析（外部项目 skill 调用失败导致会话损坏）

---

## 经验三：平台级错误（连续 API Error 400）需要独立的恢复路径

### 场景
skill 调用失败后，后续的 `harness next` 和其他对话均返回 `API Error: 400`，正常 Harness 命令失效，会话无法通过工作流命令恢复。

### 经验内容
平台级错误与会话内部错误不同，其恢复路径应写入 `constraints/recovery.md`：

**恢复步骤**：
1. **停止尝试失败命令** — 避免恶化状态
2. **快速评估损坏范围** — 尝试最简单的 `Read` 工具调用
3. **保存关键状态** — 如果 `Write` 仍可用，立即保存 session-memory
4. **选择恢复动作**：
   - 简单调用可用 → 尝试 `/compact`
   - 简单调用不可用 → 尝试 `/clear`
   - `/clear` 后仍异常 → 必须新开 agent + handoff
5. **恢复后继续** — 重新读取 runtime.yaml、session-memory、相关变更文档
6. **记录到 session-memory** — 沉淀教训

**预防措施**：
- 在 harness workflow 的角色文件和约束中，应明确：遇到第一次 API Error 400 时即提高警惕，不要连续重试 harness 命令
- 主 agent 应将平台错误视为独立的异常类型，而不是普通的执行失败

### 来源
req-05 regression 分析和 recovery.md 更新

---

## 经验四：ff 模式下的验收阶段可以由 AI 自主判定，但必须有明确的判定标准

### 场景
req-05 的 acceptance 角色文件原本强调"最终判定必须由人工做出"，这与 ff 模式的"免除人工确认"目标冲突。

### 经验内容
解决冲突的方式不是删除人工验收，而是为 ff 模式定义 AI 自主判定的标准：

**AI 可以自主判定通过的条件**：
- 所有验收标准已逐条核查完毕
- 验收报告已客观产出
- 无未满足的 AC
- 无需要人工介入的争议点

**AI 必须暂停求援的条件**：
- 存在未满足的 AC
- 验收结果与需求目标明显冲突
- 涉及用户体验或安全的主观判断（如界面是否"可用"）

**文档化要求**：
- 在 `acceptance.md` 中必须明确说明 ff 模式下的判定规则
- 避免"AI 只能辅助人工"与"ff 模式自动推进"之间的逻辑矛盾

### 来源
req-05 chg-03 角色文件更新
