# Requirement Stage Experience

## 经验一：需求范围边界要显式列出例外，而非宽泛排除

### 场景
planning 阶段发现某个决策（如 stage-tools.md 整合）需要修改被需求范围排除的文件类型（如角色文件）。

### 经验内容
需求范围中的"不包含"条目如果过于宽泛（如"不修改角色文件"），一旦某个变更决策涉及该类文件，就需要回头修改需求范围，造成返工。

更好的写法是：在"不包含"中注明例外情况，如"不修改角色文件内容，但允许修改 `## 可用工具` 引用方式（结构整合需要）"。

### 反例
req-02 初始需求范围写了"不修改角色文件"，规划阶段决策 stage-tools.md 整合后不得不回来修改需求范围。

### 来源
req-02 planning 阶段

---

## 经验二：删除任何目录/文件前，必须追溯所有消费者

### 场景
计划删除 `.workflow/versions/` 目录时，需要确认是否有外部依赖。

### 经验内容
删除目录前的"三查"：
1. **谁创建了它**：lint 脚本、CLI 初始化、agent 手动创建？
2. **谁读取/写入它**：不只是项目内脚本，还要检查**已安装的包**（pip install 的包的代码逻辑）
3. **删除后会破坏什么**：CLI 命令、CI 检查、其他仓库的 install 流程？

本次教训：`.claude/skills/harness/scripts/harness.py` 只是薄壳，真正逻辑在 `harness_workflow` 已安装包的 `core.py` 里。只查项目内脚本，漏掉了安装包——导致"可以安全删除"的初步结论是错的。

检查方法：
```bash
# 检查项目内引用
grep -rn "versions" .claude/ .codex/ .qoder/
# 检查已安装包
find ~/.local/pipx -name "*.py" | xargs grep -l "versions" 2>/dev/null
```

### 反例
初步判断 harness.py 不引用 versions/ 就认为安全删除，未检查 harness_workflow 包本身。

### 来源
req-02 regression 分析（versions/ 删除影响评估）

---

## 经验三：大架构重构后，关联脚本（lint、test）必须同步更新

### 场景
req-01 完成了 workflow/ → .workflow/ + flow/requirements/ + state/ 的完整重构，但关联的 lint 脚本和测试文件没有同步更新。

### 经验内容
架构迁移完成时，需要检查并更新：
- lint/validate 脚本（检查目录结构是否符合预期）
- 单元/集成测试（测试用例中硬编码的旧路径）
- CI 配置（如有）
- 模板文件（生成的初始化内容中引用的路径）

未更新的后果：
- lint 脚本在新架构上运行会报错（false negative），失去验证意义
- 旧测试通过说明旧代码还在；旧测试失败不代表新代码有问题——两种情况都会造成误判

在 planning 阶段就应把"更新关联脚本"作为独立变更纳入范围，而不是等到发现问题再处理。

### 来源
req-02 发现 lint_harness_repo.py 严重过时（req-01 完成后未同步更新）
