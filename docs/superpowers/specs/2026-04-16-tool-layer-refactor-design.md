# 工具层重构设计文档

## 1. 背景与目标

当前 Harness 工作流中：
- 各 stage 角色文件独立，没有抽象父类
- 工具选择主要依赖 agent 自行判断
- 没有工具评分和优胜劣汰机制
- 缺少系统化的操作日志

**目标**：
1. 引入基础角色（base-role），统一所有 stage 角色的通用硬门禁和行为准则
2. 建立工具索引、匹配、评分闭环
3. 接入 skill hub 扩展工具来源
4. 增加结构化操作日志

---

## 2. 架构总览

本次重构覆盖三层：

| 层级 | 变更内容 |
|------|---------|
| Context | 新增 `base-role.md`，由 loader 自动拼接到各 stage 角色之前 |
| Tools | 新增 `tools/index/keywords.yaml`、`tools/ratings.yaml`、`tools/index/missing-log.yaml`；新增 CLI 命令 `tool-search`、`tool-rate` |
| State | 新增 `state/action-log.md`，记录 agent 操作轨迹 |

核心工作流：

```
agent 要执行操作
    ↓
启动 toolsManager subagent（一个任务周期内只查一次）
    ↓
读取 keywords.yaml → 关键词匹配 → 返回最匹配工具
    ↓
未命中 → 查询 skill hub → 注册新 skill 或记录缺失
    ↓
agent 使用工具 → 执行前/后记录日志 → 立即评分更新 ratings.yaml
```

---

## 3. 基础角色 `base-role.md`

### 3.1 加载方式

在 `.workflow/context/index.md` 的 Step 2 中增加：
> 加载具体 stage 角色文件前，必须先加载 `.workflow/context/roles/base-role.md`。

### 3.2 硬门禁一：工具优先

> 在执行任何实质性操作前，必须先启动 `toolsManager` subagent 查询可用工具。若有匹配工具，优先使用；无匹配工具则查询 skill hub；仍未找到时，才允许由模型自行判断。

### 3.3 硬门禁二：操作说明与日志

> 每执行一个操作前，必须在对话中说明"接下来我要执行 X"；执行后，必须说明"执行完成，结果是 Y"。同时，将操作摘要追加到 `.workflow/state/action-log.md`。

### 3.4 通用准则

- 上下文负载达到阈值时，主动建议维护
- 遇到职责外问题时，记录到 `session-memory.md` 的待处理捕获问题
- 每个 stage 的特有行为在 `base-role.md` 之后加载

### 3.5 toolsManager 调用规范

> 将当前操作意图用关键词形式传递给 toolsManager，接收返回的 `tool_id`、`使用说明` 和 `confidence`。一个任务周期内，同类型的工具查询结果可复用。

---

## 4. 工具索引与匹配机制

### 4.1 文件结构

```
.workflow/tools/
├── index/
│   ├── keywords.yaml       # 关键词 → 工具映射
│   └── missing-log.yaml    # 未命中记录
├── catalog/
│   ├── git.md
│   ├── test.md
│   └── ...
└── ratings.yaml            # 工具评分数据库
```

### 4.2 `keywords.yaml` 格式

```yaml
tools:
  - tool_id: "run-pytest"
    keywords: ["运行测试", "执行测试", "pytest", "test python"]
    catalog: "catalog/test.md"
    description: "使用 pytest 运行 Python 测试"

  - tool_id: "git-commit"
    keywords: ["提交代码", "git commit", "commit"]
    catalog: "catalog/git.md"
    description: "将变更提交到 Git"
```

### 4.3 匹配算法（toolsManager 执行）

1. 将 agent 的操作意图拆分成关键词列表
2. 遍历 `keywords.yaml`，计算每个 `tool_id` 与关键词列表的**重叠数**
3. 按以下优先级排序，返回最匹配的一个：
   - 关键词重叠数高者优先
   - 重叠数相同，评分高者优先
   - 评分也相同，随机选择

### 4.4 skill hub 查询

- 本地未命中时，调用 `https://skillhub.cn/skills/find-skills`
- 若找到：将 skill 信息注册到 `keywords.yaml`，并返回给 agent
- 若未找到：记录到 `missing-log.yaml`，然后返回空，允许 agent 自行判断

---

## 5. 评分机制

### 5.1 评分规则

- **时机**：每次工具使用完成后，agent 立即评分
- **维度**：单一总体满意度，1-5 分
- **计算方式**：累计均分
  ```
  new_score = (old_score * count + new_rating) / (count + 1)
  count += 1
  ```

### 5.2 `ratings.yaml` 格式

```yaml
ratings:
  run-pytest:
    score: 4.5
    count: 12

  git-commit:
    score: 4.8
    count: 20
```

### 5.3 首次使用的新工具

若 `ratings.yaml` 中没有该 `tool_id`，初始 `score = new_rating`，`count = 1`。

---

## 6. 操作日志机制

新增文件 `.workflow/state/action-log.md`。

### 日志格式

```markdown
## 2026-04-16 10:30

- **操作**: Read(.workflow/state/runtime.yaml)
- **说明**: 读取运行时状态以确认当前需求
- **结果**: current_requirement=req-21, stage=requirement_review
- **使用工具**: 无
- **评分**: N/A
```

### 记录规则

- 每个操作产生一个条目
- 若使用了工具，必须记录 `tool_id` 和评分
- 日志采用追加写，不覆盖历史

---

## 7. CLI 命令新增

### 7.1 `harness tool-search <keywords...>`

- 启动 toolsManager 逻辑
- 接收一个或多个关键词，执行本地匹配 → skill hub 查询的完整流程
- 输出最匹配的工具 ID、使用说明、confidence

示例：
```bash
harness tool-search "运行测试" "pytest"
# Matched: run-pytest
# Catalog: catalog/test.md
# Description: 使用 pytest 运行 Python 测试
# Score: 4.5 (12 ratings)
```

### 7.2 `harness tool-rate <tool-id> <score>`

- 更新 `ratings.yaml` 中的累计均分
- 若 `tool-id` 不存在，自动创建条目

示例：
```bash
harness tool-rate run-pytest 5
```

### 7.3 缓存机制

`tool-search` 的结果在一个任务周期内按关键词缓存，避免重复查询。

---

## 8. 实施边界（方案 B 范围）

**包含**：
- 新增 `base-role.md` 及修改 `index.md` 的加载顺序
- 新增 `keywords.yaml`、`ratings.yaml`、`missing-log.yaml` 的结构定义
- 在 CLI/Python 层实现 `tool-search` 和 `tool-rate` 命令
- 新增 `action-log.md` 的写入逻辑
- toolsManager 的 stub/辅助调用入口

**不包含**：
- 重写或大规模修改现有 `catalog/` 中的工具定义
- 在 Python 层完整实现一个全自动化的 toolsManager（agent 仍需参与决策）
- 修改现有角色的具体业务逻辑（除 loader 拼接外）

---

## 9. 变更清单

| 文件/目录 | 动作 | 说明 |
|-----------|------|------|
| `.workflow/context/roles/base-role.md` | 新增 | 基础角色定义 |
| `.workflow/context/index.md` | 修改 | Step 2 增加 base-role 加载 |
| `.workflow/tools/index/keywords.yaml` | 新增 | 关键词索引 |
| `.workflow/tools/index/missing-log.yaml` | 新增 | 未命中记录 |
| `.workflow/tools/ratings.yaml` | 新增 | 评分库 |
| `.workflow/state/action-log.md` | 新增 | 操作日志 |
| `src/harness_workflow/cli.py` | 修改 | 注册 `tool-search`、`tool-rate` |
| `src/harness_workflow/core.py` | 修改 | 实现命令逻辑 |

---

## 10. 下一步

设计确认后，进入 `writing-plans` 阶段，产出详细实施计划。
