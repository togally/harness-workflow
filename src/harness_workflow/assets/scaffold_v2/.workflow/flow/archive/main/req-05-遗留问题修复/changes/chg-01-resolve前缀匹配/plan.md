# Plan: resolve_change_reference 前缀匹配

## 执行步骤

### Step 1: 修改 resolve_change_reference

文件：`src/harness_workflow/core.py`，约第 2410-2417 行

在 `derived` 匹配失败后、`return None` 之前，添加前缀匹配逻辑：

```python
# Prefix match: "chg-01" matches "chg-01-xxx"
if changes_dir.exists():
    for child in sorted(changes_dir.iterdir()):
        if child.is_dir() and child.name.startswith(reference + "-"):
            return child
```

逻辑与 `resolve_requirement_reference`（第 2400-2403 行）完全一致。

### Step 2: 验证

- 确认修改后的函数与 `resolve_requirement_reference` 的三段式匹配一致：direct → derived → prefix
- 手动测试 `harness archive req-xx` 和 `harness change --requirement req-xx` 是否正常

## 产物

- `src/harness_workflow/core.py`（修改）

## 风险评估

低风险：可逆、范围小（1 个函数，<10 行变更）、有参照实现
