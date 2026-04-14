# chg-06 执行计划

## 依赖
依赖 chg-02（context/rules/ 删除后，lint 检查才能准确反映新状态）

## 步骤

### Step 1：读取 lint 脚本现状
Read `src/harness_workflow/assets/skill/scripts/lint_harness_repo.py`

### Step 2：更新 REQUIRED_DIRS 和 REQUIRED_FILES
更新为新架构实际存在的目录和文件，保留 `.workflow/versions` 检查（chg-07 完成后移除）。

### Step 3：处理 test_harness_cli.py
为引用旧路径（versions/active/{version}/requirements/ 等）的测试添加 skip 注解，注明原因。

### Step 4：验证
Bash: `python src/harness_workflow/assets/skill/scripts/lint_harness_repo.py`

## 产物
- `lint_harness_repo.py`（已更新）
- `test_harness_cli.py`（旧路径测试已 skip）
