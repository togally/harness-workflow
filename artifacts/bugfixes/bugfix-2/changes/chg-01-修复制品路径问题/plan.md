# Plan: 修复制品路径问题

## Change ID
chg-01

## Step 1: 修改 `create_bugfix` 函数路径
**文件**: `src/harness_workflow/workflow_helpers.py`
**位置**: line ~3222

### 变更内容
```python
# 修改前
bugfix_dir = root / ".workflow" / "flow" / "bugfixes" / dir_name

# 修改后
bugfix_dir = root / "artifacts" / "bugfixes" / dir_name
```

### 验证方法
创建新的 bugfix，验证其在 `artifacts/bugfixes/` 下创建。

## Step 2: 修改 `create_change` 函数的需求查找路径
**文件**: `src/harness_workflow/workflow_helpers.py`
**位置**: line ~3326

### 变更内容
```python
# 修改前
req_dir = resolve_requirement_reference(
    root / ".workflow" / "flow" / "requirements", req_ref, config["language"]
)

# 修改后
req_dir = resolve_requirement_reference(
    root / "artifacts" / "requirements", req_ref, config["language"]
)
```

### 验证方法
运行 `harness change <title>` 验证能找到 `artifacts/requirements/` 下的需求。

## Step 3: 确认 `create_change` 的输出路径
**文件**: `src/harness_workflow/workflow_helpers.py`
**位置**: line ~3333

### 变更内容
由于 Step 2 已经将 `req_dir` 指向 `artifacts/requirements/`，因此:
```python
change_dir = req_dir / "changes" / dir_name
```
会自动输出到 `artifacts/requirements/<req>/changes/<change>/`

### 验证方法
创建新的 change，验证其在 `artifacts/requirements/<req>/changes/` 下创建。

## Step 4: 测试验证
### 测试用例 1: 创建新的 bugfix
```bash
harness bugfix "测试路径修复"
```
**预期**: bugfix 在 `artifacts/bugfixes/bugfix-X-测试路径修复/` 创建

### 测试用例 2: 创建新的 change
```bash
harness requirement "测试需求"
harness change "测试变更"
```
**预期**: change 在 `artifacts/requirements/req-XX-测试需求/changes/chg-XX-测试变更/` 创建

## Dependencies
- 无外部依赖

## Risks
- 现有 bugfix/change 可能位于旧路径，需要迁移（但当前 task 不涉及迁移）
