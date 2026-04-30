# Session Memory — chg-02（trivial 准入判据 + 自动识别 hint）

## 实施摘要

### Steps ✅

- ✅ Step 1：classify_diff_change_types（8 类型：typo/doc/config_constant/comment/dead_code/lint/string/other）
- ✅ Step 2：validate_trivial_eligibility（5 步组合判据）
- ✅ Step 3：harness_bugfix.py hint + --force-full
- ✅ Step 4：harness_requirement.py hint + --force-full
- ✅ Step 5：硬门禁六 / 七 自检

## 关键决策

1. **import 检测顺序**：新增 `import os` 时，如果整个文件也有其他非白名单改动，会先触发 "other"，而不是 "新增 import"。两种情况均导致 ok=False，符合需求。
2. **hint 不阻塞**：所有 hint 输出完后继续调原命令，返回码跟随原命令。

## 测试结果

17 tests passed（全绿）
