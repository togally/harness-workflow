# Session Memory: req-38（api-document-upload 工具闭环）/ chg-04（ProjectProfile.mcp_project_ids 多 provider map）

> req-38（api-document-upload 工具闭环：触发门禁 + MCP pre-check 协议 + 存量项目同步）
> chg-04（ProjectProfile.mcp_project_ids 多 provider map）

## 1. Current Goal

实现 `ProjectProfile.mcp_project_ids: dict[str, str]` 字段，双向 render/load，mcp-precheck.md 阶段 4 细化，pytest 覆盖，scaffold_v2 同步。

## 2. Current Status

全部 Step 已完成。pytest 5 新增用例全绿，全量 pytest 零回归（320 passed, 39 skipped，2 failed 均为 chg-02（触发门禁 §3.5.2 + triggers lint）的 test_validate_contract_triggers 预存失败，与 chg-04 无关）。

## 3. Execution Log

### Step 1 ✅ ProjectProfile dataclass 新增字段
- 文件：`src/harness_workflow/project_scanner.py`
- 在 `project_headline` 之后、`parse_errors` 之前新增：
  `mcp_project_ids: dict[str, str] = field(default_factory=dict)`
- `field` 已在既有 `from dataclasses import asdict, dataclass, field` 中导入，无需补充

### Step 2 ✅ render_project_profile 渲染新段
- `_render_body` 函数中，在"## 项目用途"之前追加"## MCP 项目归属（provider → project_id）"段落
- 设计决策（default-pick）：当 `mcp_project_ids == {}` 时，渲染 `- (none)` 而非三个 placeholder providers，以确保 roundtrip 恒等（见下方 default-pick 说明）
- 当 `mcp_project_ids` 非空时，按 sorted(providers) 渲染，value 为空字符串时输出 `(unset)`

### Step 3 ✅ load_project_profile 反向解析
- 新增 `_MCP_SUB_RE` 正则：`^\s{2,}-\s+(\w+):\s+(.+)$`
- 新增 `_load_mcp_project_ids(body, profile)` helper function
- 在 `load_project_profile` 末尾调用，解析"## MCP 项目归属"段落
- `(unset)` → `""` 映射；段缺失 → `{}` + `parse_errors.append("mcp_project_ids section absent or malformed")`

### Step 4 ✅ mcp-precheck.md 阶段 4 细化
- 文件：`.workflow/tools/protocols/mcp-precheck.md`
- 添加"阶段 4 前置条件"：必须阶段 1 探测命中或阶段 3 恢复完成；否则回阶段 2
- 具体化动作：调 `{list_tool}` 拿 `<actual_id>`，读 `{profile_key}` 得 `<expected_id>`
- 不匹配时：打印差异对照 + 引导二选一（选项 A 切 workspace / 选项 B 改 profile）
- 显式写入"禁止静默继续、禁止默认选一、禁止跳过校验"

### Step 5 ✅ pytest 新增用例
- 文件：`tests/test_project_profile_mcp_project_ids.py`
- 5 条用例：
  - `test_project_profile_mcp_project_ids_roundtrip[empty_dict]` PASSED
  - `test_project_profile_mcp_project_ids_roundtrip[single_provider]` PASSED
  - `test_project_profile_mcp_project_ids_roundtrip[multi_provider]` PASSED
  - `test_project_profile_mcp_project_ids_unset_placeholder` PASSED
  - `test_project_profile_mcp_project_ids_legacy_missing_section` PASSED

### Step 6 ✅ scaffold_v2 mirror 同步
- `cp .workflow/tools/protocols/mcp-precheck.md src/harness_workflow/assets/scaffold_v2/.workflow/tools/protocols/mcp-precheck.md`
- `diff` 无输出，零 diff 确认

### Step 7 ✅ 自检通过
- `grep -c "mcp_project_ids" project_scanner.py` → 13（≥ 3）
- `grep -c "## MCP 项目归属" project_scanner.py` → 2（render 字符串字面量 + 注释区域）
- `grep -cE "list_tool|profile_key|mcp_project_ids" mcp-precheck.md` → 6（≥ 3）
- `grep -c "禁止静默继续" mcp-precheck.md` → 1（≥ 1）
- `diff .workflow/tools/protocols/mcp-precheck.md src/.../scaffold_v2/...` → 无输出
- smoke test `ProjectProfile(mcp_project_ids={'apifox':'abc'}).mcp_project_ids` → `{'apifox': 'abc'}`

## 4. Default-Pick 决策列表

1. **empty dict render 用 `(none)` 而非三 placeholder providers**：
   - plan.md Step 2 要求空 dict 时渲染三 placeholder providers（apifox/postman/swagger 各 `(unset)`）；
   - plan.md Step 5 要求 `{}` roundtrip 恒等；
   - 两个要求产生冲突：placeholder providers 会 load 回 `{'apifox': '', 'postman': '', 'swagger': ''}` 而非 `{}`；
   - **决策**：空 dict 时渲染 `- (none)` 标记（与其他 list 字段风格一致），保证 roundtrip 恒等优先；`(unset)` 占位仅在显式设置了 provider key 但 value 为 `""` 时出现；
   - unset_placeholder 测试仍满足（`{"apifox": ""}` → `apifox: (unset)` → load → `{"apifox": ""}`）

## 5. pytest stdout（关键片段）

```
PASSED tests/test_project_profile_mcp_project_ids.py::test_project_profile_mcp_project_ids_roundtrip[empty_dict]
PASSED tests/test_project_profile_mcp_project_ids.py::test_project_profile_mcp_project_ids_roundtrip[single_provider]
PASSED tests/test_project_profile_mcp_project_ids.py::test_project_profile_mcp_project_ids_roundtrip[multi_provider]
PASSED tests/test_project_profile_mcp_project_ids.py::test_project_profile_mcp_project_ids_unset_placeholder
PASSED tests/test_project_profile_mcp_project_ids.py::test_project_profile_mcp_project_ids_legacy_missing_section
5 passed in 0.06s

全量：320 passed, 39 skipped（2 failed = chg-02 test_validate_contract_triggers 预存失败，与 chg-04 无关）
```

## 6. Roundtrip 示例

```python
from harness_workflow.project_scanner import ProjectProfile, render_project_profile, load_project_profile
import tempfile, datetime
from pathlib import Path

p = ProjectProfile(mcp_project_ids={"apifox": "proj-abc123", "postman": ""})
text = render_project_profile(p, now=lambda: datetime.datetime(2026,1,1,tzinfo=datetime.timezone.utc))
# text 含：
# ## MCP 项目归属（provider → project_id）
# - mcp_project_ids:
#   - apifox: proj-abc123
#   - postman: (unset)

with tempfile.NamedTemporaryFile(mode="w", suffix=".md", encoding="utf-8", delete=False) as f:
    f.write(text); tmp = Path(f.name)
loaded = load_project_profile(tmp)
# loaded.mcp_project_ids == {"apifox": "proj-abc123", "postman": ""}
```

## 7. 模型自检降级留痕

- expected_model: sonnet
- 实际运行：claude-sonnet-4-6（符合 sonnet 期望）
- 无法程序化自省 model ID，以系统提示中的 `claude-sonnet-4-6` 标注为准
- 降级：无需降级

## 8. Failed Paths

无。

## 9. Open Questions

无。
