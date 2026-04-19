# Session Memory

## 1. Current Goal

端到端验证 toolsManager 的查询流程，确认 chg-01 和 chg-02 完成后，按 SOP 执行的关键词匹配能够为各 stage 常见操作意图返回正确结果。

## 2. Current Status

- 已读取 `keywords.yaml` 和 `ratings.yaml`
- 已按 toolsManager SOP 的匹配算法（关键词重叠数 → 评分排序）对 6 个典型查询进行模拟
- 首次模拟发现 4/6 查询未命中预期工具，原因是初始 keywords 覆盖不足
- 已回退到 chg-01 优化 keywords（为 bash、edit、grep、claude-code-context 补充更细粒度的中文关键词）
- 复测后 6/6 全部通过

## 3. Validated Approaches

模拟查询结果（最终版本）：

| 查询意图 | 匹配结果 | 重叠关键词 | 状态 |
|---------|---------|-----------|------|
| 读取配置文件 | read | 读取配置 | ✅ |
| 修改代码逻辑 | edit | 代码、修改代码、改代码 | ✅ |
| 运行单元测试 | bash | 单元测试、运行、测试 | ✅ |
| 搜索函数定义 | grep | 搜索、函数、定义 | ✅ |
| 派发测试 subagent | agent | agent、subagent、测试 | ✅ |
| 上下文太长了需要压缩 | claude-code-context | 压缩、太长 | ✅ |

验证命令：
```bash
python3 -c "import yaml; ..."
```

## 4. Failed Paths

- **Attempt**: 使用初始 keywords.yaml 进行模拟
- **Failure reason**: 
  - "修改代码逻辑" 缺少 "代码" 相关关键词，未命中 edit
  - "运行单元测试" bash 与 agent 均只匹配到 "测试"，且评分相同导致随机选错
  - "搜索函数定义" 缺少 "搜索"、"函数" 关键词，未命中 grep
  - "上下文太长了需要压缩" 缺少 "压缩"、"太长" 关键词，未命中 claude-code-context
- **Fix**: 在 keywords.yaml 中为相关工具补充更细粒度、更贴近自然语言查询的中文关键词

## 5. Candidate Lessons

```markdown
### 2026-04-17 keywords 设计要覆盖自然语言变体
- Symptom: toolsManager 模拟查询命中率低（4/6 失败）
- Cause: 关键词只覆盖了工具名和通用动词，缺少用户实际会用的口语化表达（如"改代码"、"单元测试"、"太长"）
- Fix: 为每个工具设计关键词时，应至少覆盖 3 类表达：工具英文名、标准动作词、用户口语化表达
```

## 6. Next Steps

- chg-03 已完成，进入 chg-04：重构 `stage-tools.md`
