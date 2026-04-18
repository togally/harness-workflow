# req-25 测试报告

## 测试工程师
jiazhiwei

## 测试日期
2026-04-18

## 需求
harness 完全由 harness-manager 角色托管

---

## 验收标准检查结果

### 1. `harness install claude` 能正常完成安装

**状态**: PARTIAL（部分实现）

**验证结果**:
- `core.py` 第 4310 行实现了 `install_agent()` 函数
- `install_agent()` 功能完整：
  - 检测模板与目标目录的差异（add/modify/delete）
  - 复制 skill 文件到目标 agent 目录
  - 向 CLAUDE.md/AGENTS.md 写入 bootstrap 指令
  - bootstrap 指令包含 "立即加载 harness-manager 角色" 的引导
- `harness-manager.md` 第 309-321 行定义了 `harness install --agent <agent>` 的执行流程

**问题**:
- core.py 尚未删除，与需求"删除 core.py 等非工具层脚本"矛盾
- 工具层脚本 `tools/harness_cycle_detector.py` 等已存在

---

### 2. 其他命令均能正常执行

**状态**: PARTIAL（部分实现）

**验证结果**:
| 命令 | 引导逻辑位置 | 实现状态 |
|------|-------------|---------|
| `harness requirement` | harness-manager.md 第 436-446 行 | 定义完整 |
| `harness change` | harness-manager.md 第 447-457 行 | 定义完整 |
| `harness bugfix` | harness-manager.md 第 458-468 行 | 定义完整 |
| `harness next` | harness-manager.md 第 410-419 行 | 定义完整 |
| `harness ff` | harness-manager.md 第 421-433 行 | 定义完整 |
| `harness status` | harness-manager.md 第 388-397 行 | 定义完整 |
| `harness archive` | harness-manager.md 第 470-478 行 | 定义完整 |
| `harness rename` | harness-manager.md 第 480-487 行 | 定义完整 |
| `harness suggest` | harness-manager.md 第 491-500 行 | 定义完整 |
| `harness tool-search` | harness-manager.md 第 502-510 行 | 定义完整 |
| `harness tool-rate` | harness-manager.md 第 512-519 行 | 定义完整 |
| `harness regression` | harness-manager.md 第 521-530 行 | 定义完整 |
| `harness feedback` | harness-manager.md 第 532-540 行 | 定义完整 |

**问题**:
- CLI 入口 (`cli.py`) 调用 `core.py` 中的函数执行命令
- 尚未实现为 agent 读取 role 文件自主执行的方式

---

### 3. Subagent 嵌套调用正常工作

**状态**: PARTIAL（部分实现）

**验证结果**:
- `base-role.md` 第 96-171 行定义了完整的 Subagent 嵌套调用规则
  - 嵌套调用链结构（Level 0 到 Level N）
  - 派发协议（角色文件、任务描述、context_chain、会话内存路径）
  - 上下文传递机制（读取/写入/不修改上层）
  - Session Memory 格式
- `harness-manager.md` 第 178-234 行定义了派发 subagent 的详细流程（Step 3.6）

**问题**:
- 尚未有实际 subagent 派发的代码实现
- 需要通过 Agent 工具调用来验证实际运行效果

---

### 4. 循环调用能被检测和终止

**状态**: IMPLEMENTED（已实现）

**验证结果**:
- `tools/harness_cycle_detector.py` 已实现循环检测脚本
  - `--add` 参数添加 agent 到调用链并检测循环
  - `--snapshot` 获取当前调用链快照
  - `--clear` 清除调用链
  - 检测到循环时返回退出码 1
  - 循环检测结果写入 action-log.md 和 cycle-logs/ 目录
- `core.py` 第 125-346 行实现了 `CycleDetector` 类和 `detect_subagent_cycle()` 函数
  - 使用 CallChainNode 数据结构追踪调用链
  - 检测 A->B->A 和 A->B->C->A 类型的循环
  - `report_cycle_detection()` 函数记录循环到 action-log

---

### 5. 安装后 agent 能正确加载 `harness-manager`

**状态**: IMPLEMENTED（已实现）

**验证结果**:
- `install_agent()` 函数（第 4380-4407 行）会向 entry file 写入 bootstrap 指令：
  ```python
  bootstrap_cn = "4. **立即加载 `harness-manager` 角色**：使用 Skill 工具调用 `harness-install`，由 harness-manager 接管后续路由"
  bootstrap_en = '4. **Immediately load the `harness-manager` role**: use the Skill tool to invoke `harness-install`, letting harness-manager take over routing.'
  ```
- bootstrap 指令仅在不存在时注入，避免重复

---

### 6. 工具层工具能正常工作

**状态**: IMPLEMENTED（已实现）

**验证结果**:
- 工具层脚本已注册在 `.workflow/tools/catalog/` 目录：
  - `harness-cycle-detector.md` - 循环检测工具
  - `harness-log-action.md` - 操作日志工具
  - `harness-export-feedback.md` - 反馈导出工具
  - `harness-tool-search.md` - 工具搜索工具
  - `harness-tool-rate.md` - 工具评分工具
- `stage-tools.md` 定义了各 stage 的工具约束与推荐

---

## 问题汇总

### 严重问题

1. **core.py 尚未删除**
   - 需求明确要求"删除 core.py 等非工具层脚本（项目中只允许工具层存在脚本）"
   - 当前 core.py 仍然存在，包含所有命令处理逻辑
   - 这与"role 文件成为唯一执行依据"的设计理念不符

### 中等问题

2. **change 文件内容不完整**
   - chg-01 到 chg-05 的 change.md 文件都是 placeholder 内容
   - 缺少实际的设计和实现计划
   - 需要补充 `design.md` 和 `plan.md`

3. **尚未验证实际执行效果**
   - 当前验证基于代码静态分析
   - 建议执行实际的 `harness install` 等命令进行端到端测试

---

## 建议

1. **完成 core.py 迁移**: 将 core.py 中的函数迁移到工具层脚本，然后删除 core.py
2. **补充 change 设计文档**: 为每个 change 补充完整的设计和实现计划
3. **执行端到端测试**: 实际运行 `harness install claude` 等命令验证完整流程
4. **验证 subagent 派发**: 通过实际派发 subagent 验证嵌套调用和循环检测

---

## 结论

**当前实现进度**: 约 60%

| 验收标准 | 状态 |
|---------|------|
| `harness install claude` 能正常完成安装 | PARTIAL |
| 其他命令均能正常执行 | PARTIAL |
| Subagent 嵌套调用正常工作 | PARTIAL |
| 循环调用能被检测和终止 | IMPLEMENTED |
| 安装后 agent 能正确加载 `harness-manager` | IMPLEMENTED |
| 工具层工具能正常工作 | IMPLEMENTED |

**下一步**: 需要将 core.py 中的命令执行逻辑迁移到工具层，完成剩余的 change 设计文档，并进行端到端测试验证。