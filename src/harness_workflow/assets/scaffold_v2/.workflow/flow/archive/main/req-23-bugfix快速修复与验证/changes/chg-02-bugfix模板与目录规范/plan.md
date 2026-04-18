# chg-02 Plan: bugfix 模板与目录规范

## 执行步骤

### Step 1: 设计 bugfix.md 模板
- 参考 req-23 的 `requirement.md` 中"产物结构"章节
- 模板头部包含元数据字段：`id`、`title`、`created_at`
- 主体包含五个章节：
  1. 问题描述
  2. 根因分析（regression 阶段填写）
  3. 修复范围
  4. 修复方案（regression 阶段填写，executing 阶段读取）
  5. 验证标准

### Step 2: 确定模板存放位置
- 将模板保存到 `src/harness_workflow/assets/templates/bugfix.md`
- 更新 `pyproject.toml` 的 `package-data`（如需要）

### Step 3: 验证模板完整性
- 人工检查模板格式
- 确认模板中无 req-* 专属引用

### Step 4: 更新相关引用
- 如 `SKILL.md` 或文档中有模板目录说明，同步更新
