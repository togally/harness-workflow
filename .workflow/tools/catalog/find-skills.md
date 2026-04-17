# 工具：find-skills

## 用途

在本地工具索引未命中时，调用 `find-skills` skill 查询 skillhub 商店，发现是否有其他可用 skill 可以完成当前操作意图。

## 前提条件

- 当前 agent 环境中已安装并识别 `find-skills` skill
- 在 Claude Code 中，该 skill 需出现在可用 skill 列表中方可通过 `Skill` 工具调用

## 调用方式

### Claude Code

通过 `Skill` 工具调用：

```json
{
  "skill": "find-skills",
  "args": "<查询关键词>"
}
```

### 其他平台（如已安装 skillhub CLI）

```bash
skillhub find-skills --query "<操作意图>" --keywords "<关键词1,关键词2>"
```

## 预期行为

1. `find-skills` 接收当前操作意图和关键词
2. 在 skillhub 商店中搜索匹配的 skills
3. 返回推荐结果列表（包含 skill_id、名称、描述、安装方式、使用要点）

## 返回值处理

- **找到匹配 skill**：
  - 将新 skill 注册到 `keywords.yaml`，建立关键词映射
  - 返回 skill 信息给调用方
  - 建议用户/调用方安装该 skill（如尚未安装）

- **未找到匹配 skill**：
  - 记录本次查询到 `missing-log.yaml`
  - 返回 "未找到"
  - 允许调用方自行判断

## 当前状态

- `find-skills` 是 skillhub 生态中的标准 discovery skill
- 在 Harness Workflow 中，它被视为 toolsManager 的**外部查询工具**
- 若环境中尚未安装 `find-skills`，toolsManager 应记录环境缺失并允许模型自行判断

## 注意事项

- `find-skills` 本身也是一个 skill，需要被安装在当前环境中才能使用
- 它不替代本地 `keywords.yaml` 索引，而是作为本地未命中时的扩展查询层
- 查询结果应优先注册到本地索引，避免重复查询
