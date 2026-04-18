# Change Plan

## 1. Development Steps

1. 列出 `catalog/` 下所有已定义的工具文件（排除 `_template.md`）
2. 为每个工具设计 keywords：
   - read: read, 读取文件, 查看文件, 文件内容
   - edit: edit, 编辑文件, 修改文件, 替换内容
   - bash: bash, 执行命令, 运行脚本, 编译, 测试, git
   - grep: grep, 搜索内容, 查找代码, 内容匹配
   - agent: agent, subagent, 派发任务, 独立视角
   - find-skills: find-skills, skill, 查找技能, 扩展工具
   - git-commit: git-commit, git, 提交代码, commit
   - claude-code-context: compact, clear, 上下文维护, 压缩上下文, 清理上下文
3. 更新 `keywords.yaml`，保持现有格式
4. 设计 `ratings.yaml` 初始评分：
   - 核心高频工具（read, edit, bash, agent）→ 5 分
   - 常用工具（grep, git-commit）→ 4 分
   - 特定场景工具（find-skills, claude-code-context）→ 3 分
5. 保存所有文件

## 2. Verification Steps

1. 检查 `keywords.yaml` 条目数 = catalog 中有效工具数
2. 检查 `ratings.yaml` 条目数与 `keywords.yaml` 一致
3. 模拟 toolsManager 查询：
   - 意图 "读取文件" → 应匹配 read
   - 意图 "编辑代码" → 应匹配 edit
   - 意图 "运行测试" → 应匹配 bash
   - 意图 "搜索内容" → 应匹配 grep
   - 意图 "派发 subagent" → 应匹配 agent
