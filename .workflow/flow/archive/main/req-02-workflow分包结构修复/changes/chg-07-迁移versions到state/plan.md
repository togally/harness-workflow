# chg-07 执行计划

## 依赖
无（chg-02 依赖本变更）

## 步骤

### Step 1：读取 core.py 关键区段
分段读取常量区、版本函数区、archive_requirement、workflow_next、cli.py 命令注册。

### Step 2：删除版本相关常量
- 删除 `Path(".workflow") / "versions"` 常量
- 停止写入 `LEGACY_WORKFLOW_RUNTIME_PATH`

### Step 3：逐一删除版本函数
按依赖顺序删除约 15 个函数，每次删除后确认无悬空引用。

### Step 4：重写 archive_requirement()
新签名：`archive_requirement(root, requirement_name, folder="")`
- 归档到 `flow/archive/<folder>/` 或 `flow/archive/`
- 目标不存在则新建，存在则合并

### Step 5：清理 workflow_next() 中的版本引用
移除所有 version_meta 读写逻辑，保持功能等效。

### Step 6：更新 cli.py
- 删除 `harness version`、`harness active`、`harness use` 子命令
- 删除 `harness plan` 子命令（用户不手动创建，由 subagent 编排产出）
- 更新 `harness archive` 参数为 `<req-id> [--folder <name>]`

### Step 7：删除命令文件
- `rm .claude/commands/harness-version.md`
- `rm .claude/commands/harness-active.md`
- `rm .claude/commands/harness-use.md`
- `rm .claude/commands/harness-plan.md`（用户不直接调用）

### Step 8：删除 .workflow/versions/
Bash: `rm -rf .workflow/versions/`

### Step 9：重装并验证
```bash
pip install -e .
harness status
harness archive --help
```

## 产物
- `src/harness_workflow/core.py`（版本概念已清除）
- `src/harness_workflow/cli.py`（version/active/use/plan 命令已移除）
- `.claude/commands/`（version/active/use/plan 命令文件已删除）
- `.workflow/versions/`（已删除）
- 包已重装
