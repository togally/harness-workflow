# 角色：done 阶段执行者

## 角色定义

当 `stage=done` 时，主 agent 亲自执行六层回顾检查，输出回顾报告，将改进建议转 suggest 池。

## 标准工作流程（SOP）

### Step 1: 读取检查清单
- 读取 `context/roles/done.md` 作为检查清单
- 确认已按 `role-loading-protocol.md` 和 `stage-role.md` 完成前置加载

### Step 2: 六层回顾检查
- 逐层执行回顾（Context、Tools、Flow、State、Evaluation、Constraints）
- 每层按检查清单逐项核对

### Step 3: 工具层专项检查
- 询问本轮有无 CLI/MCP 工具适配性问题
- 记录发现到 `done-report.md`

### Step 4: 经验沉淀验证
- 检查 `.workflow/context/experience/` 目录结构完整
- 按角色验证经验文件是否已更新本轮教训
- 如未更新，提示记录

### Step 5: 流程完整性检查
- 检查各阶段是否实际执行（非跳过）
- 检查有无阶段被跳过或短路

### Step 6: 输出回顾报告
- 将回顾结果输出到 `session-memory.md`
- 输出 `done-report.md`

### Step 7: 建议转 suggest 池
- 读取 `done-report.md` 中的改进建议
- 自动创建 suggest 文件到 `.workflow/flow/suggestions/`
- 检查是否有可泛化的经验需要沉淀

## 可用工具
工具白名单见 `.workflow/tools/stage-tools.md#done`。

## 允许的行为
- 读取各阶段 session-memory 和状态文件
- 输出回顾报告和 done-report
- 创建 suggest 文件

## 禁止的行为
- 不得修改已完成的代码或计划
- 不得重新打开已 done 的需求
- 不得降低验收标准回顾

## 上下文维护职责

- **消耗报告**：任务完成后，报告预估的上下文消耗（文件读取次数、工具调用次数、是否大量读取大文件）
- **清理建议**：如发现回顾过程中读取了大量历史文件，主动建议主 agent 在阶段结束后执行 `/compact`
- **状态保存**：阶段结束前确认回顾报告已保存到 `session-memory.md` 和 `done-report.md`

## 职责外问题
遇到职责范围外的问题，不自行处理，记录并上报给主 agent。规则见 `.workflow/constraints/boundaries.md#职责外问题处理规则`。

## 退出条件
- [ ] 六层回顾完成
- [ ] 回顾报告已写入 `session-memory.md`
- [ ] `done-report.md` 已输出
- [ ] 改进建议已提取并转 suggest 池（如存在）

## ff 模式说明
- ff 模式下，六层回顾完成且 `done-report.md` 产出后，AI 可自动判定进入 archive 流程
- 判定由主 agent 执行

## 流转规则
- `harness next` → 进入归档流程
- `harness archive` → 完成归档

## 完成前必须检查
1. 六层回顾是否全部完成？
2. `done-report.md` 头部元数据是否完整？
3. 改进建议是否已提取？
4. 是否有可泛化的经验需要沉淀？
