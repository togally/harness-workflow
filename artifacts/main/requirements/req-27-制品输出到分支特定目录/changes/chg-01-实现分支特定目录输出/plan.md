# Plan: 实现分支特定目录输出

## Change ID
chg-01

## Step 1: 添加辅助函数 `_get_branch_name`
**文件**: `src/harness_workflow/workflow_helpers.py`

### 实现
```python
def _get_branch_name(root: Path) -> str:
    """获取当前 git 分支名称，返回 'main' 作为默认值。"""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=5
        )
        branch = result.stdout.strip()
        if not branch:
            return "main"
        # Sanitize: 替换 / 为 -，去除空白
        return branch.replace("/", "-").strip()
    except Exception:
        return "main"
```

### 验证
```bash
python -c "from harness_workflow.workflow_helpers import _get_branch_name; print(_get_branch_name(Path('.')))"
# 应输出当前分支名
```

## Step 2: 修改 `create_requirement` 函数
**文件**: `src/harness_workflow/workflow_helpers.py`
**位置**: ~line 3161

### 变更
```python
# 当前
requirement_dir = root / ".workflow" / "flow" / "requirements" / dir_name

# 改为
requirement_dir = root / "artifacts" / _get_branch_name(root) / "requirements" / dir_name
```

### 验证
创建新需求后检查目录位置。

## Step 3: 修改 `create_bugfix` 函数
**文件**: `src/harness_workflow/workflow_helpers.py`
**位置**: ~line 3222

### 变更
```python
# 当前（bugfix-2 修改后）
bugfix_dir = root / "artifacts" / "bugfixes" / dir_name

# 改为
bugfix_dir = root / "artifacts" / _get_branch_name(root) / "bugfixes" / dir_name
```

### 验证
创建新 bugfix 后检查目录位置。

## Step 4: 修改 `create_change` 函数
**文件**: `src/harness_workflow/workflow_helpers.py`
**位置**: ~line 3326

### 变更
```python
# 当前（bugfix-2 修改后）
req_dir = resolve_requirement_reference(
    root / "artifacts" / "requirements", req_ref, config["language"]
)

# 改为
req_dir = resolve_requirement_reference(
    root / "artifacts" / _get_branch_name(root) / "requirements", req_ref, config["language"]
)
```

### 验证
创建新 change 后检查目录位置。

## Step 5: 修改 `generate_requirement_artifact` 函数
**文件**: `src/harness_workflow/workflow_helpers.py`
**位置**: ~line 3665

### 变更
```python
# 当前
out_dir = root / "artifacts" / "requirements"

# 改为
out_dir = root / "artifacts" / _get_branch_name(root) / "requirements"
```

### 验证
归档需求后检查制品位置。

## Step 6: 集成测试
```bash
# 在 main 分支
harness requirement "测试分支输出"
# 应在 artifacts/main/requirements/req-XX-测试分支输出/ 创建

harness bugfix "测试 bugfix"
# 应在 artifacts/main/bugfixes/bugfix-X-测试 bugfix/ 创建
```

## Dependencies
- 无外部依赖

## Risks
- 分支名为空时回退到 "main"
- subprocess 可能失败（已捕获异常）
