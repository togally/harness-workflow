# chg-02 执行计划

## 依赖
无（versions/ 由 chg-07 负责删除）

## 步骤

### Step 1：确认 context/rules/ 内容
Read `.workflow/context/rules/workflow-runtime.yaml` 排除误删风险。

### Step 2：扫描引用
Grep 搜索 `context/rules` 在整个项目中的引用。

### Step 3：执行删除
- Bash: `rm -rf .workflow/context/rules`

### Step 4：验证
确认 `context/` 下无 CLI 运行时状态文件。

## 产物
- `.workflow/context/rules/` 已删除
