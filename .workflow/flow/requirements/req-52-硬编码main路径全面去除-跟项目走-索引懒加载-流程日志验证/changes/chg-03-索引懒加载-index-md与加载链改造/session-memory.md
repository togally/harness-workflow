# Session Memory — chg-03（索引懒加载：项目级子目录 index.md 模板 + role-loading-protocol Step 7.6 改按需加载 + _load_project_level_index helper）

## 1. Current Goal

req-52 / chg-03：项目级子目录加 index.md 索引清单 + 加载链改为按需加载；token 消耗下降。

## 2. Context Chain

- Level 0: 主 agent → analysis stage
- Level 1: Subagent-L1 (analyst / opus) → req-52 Phase 1+2+3

## 3. Completed Tasks

- [x] 6 份 index.md 模板 schema 落 plan.md §1.1（YAML frontmatter + Markdown 表，含 path / title / scope / when_load 字段，OQ-B = A）
- [x] `_load_project_level_index(root, scope)` + `_parse_index_md(idx_path, source)` 完整代码落 plan.md §1.2
- [x] role-loading-protocol Step 7.6.1 索引懒加载子段落 plan.md §1.3
- [x] `tests/test_req52_lazy_index_loading.py` 5 用例完整代码落 plan.md §1.5
- [x] 7 条 lint 命令 + 7 条测试用例写入 plan.md §3 / §4

## 4. Results

- change.md / plan.md / session-memory.md 三件套写入 chg-03 目录
- chg-03 单独落地后下游可在 `artifacts/project/{scope}/index.md` 维护清单，agent 按需加载（但接入主流程仍归 chg-04）

## 5. Default-pick 决策清单

- index.md schema = YAML frontmatter + Markdown 表（OQ-B = A）：理由——与现有 `.workflow/state/experience/index.md` 同源，下游学习成本低；
- when_load 三种形态（always / on-stage / on-keyword）：覆盖常见加载控制场景，agent 自判；
- helper 不读取条目内容仅返回路径清单：职责分离，agent 按 when_load 决定后续加载。

## 6. Next Steps

- 用户拍板后，主 agent harness next 推进到 executing；
- chg-03 与 chg-02 实施可并行（不互依），但建议串行（chg-02 → chg-03 → chg-04）降低风险。

## 7. 待处理捕获问题

- `_parse_index_md` 当前为简单 markdown 表格解析（按 `|` 分隔），未用 markdown 库（避免新增依赖）；如未来 schema 复杂化（如多行单元格），需引入 `marko` / `markdown-it-py`，本 chg 内不做防御性扩展。

---

## Executing Stage — chg-03 实施结果（Subagent-L1 / executing / Sonnet）

### 实施步骤完成情况

- ✅ Step 1：6 份 `index.md` 模板创建（constraints + experience/{roles,tool,risk,regression,stage}）
- ✅ Step 2：`_load_project_level_index` + `_parse_index_md` helper 新增到 workflow_helpers.py（~8330行）
- ✅ Step 3：`role-loading-protocol.md` Step 7.6.1 索引懒加载子段新增
- ✅ Step 4：scaffold_v2 mirror 同步（diff -q silent）
- ✅ Step 5：`tests/test_req52_lazy_index_loading.py` 新建，5 用例全 PASS

### lint stdout（完整）

**L1：索引懒加载单测全 PASS**

```
pytest tests/test_req52_lazy_index_loading.py -v
5 passed in 0.17s

test_index_parsing PASSED
test_when_load_filter PASSED
test_fallback_main_to_legacy PASSED
test_empty_when_no_index PASSED
test_skip_placeholder_row PASSED
```

**L2：helper 注册确认**

```
grep -n "^def _load_project_level_index" src/harness_workflow/workflow_helpers.py
8330:def _load_project_level_index(

grep -n "^def _parse_index_md" src/harness_workflow/workflow_helpers.py
8377:def _parse_index_md(idx_path: Path, source: str) -> list[dict]:

python3 -c "from harness_workflow.workflow_helpers import _load_project_level_index, _parse_index_md; print('OK')"
OK
```

**L3：role-loading-protocol Step 7.6.1 段**

```
grep -n "Step 7.6.1：索引懒加载" .workflow/context/roles/role-loading-protocol.md
162:#### Step 7.6.1：索引懒加载...

grep -n "_load_project_level_index" .workflow/context/roles/role-loading-protocol.md
168: + 174:（2 命中）
```

**L4：6 份 index.md 模板存在（全 OK）**

```
test -f artifacts/project/constraints/index.md → OK
test -f artifacts/project/experience/roles/index.md → OK
test -f artifacts/project/experience/tool/index.md → OK
test -f artifacts/project/experience/risk/index.md → OK
test -f artifacts/project/experience/regression/index.md → OK
test -f artifacts/project/experience/stage/index.md → OK
```

**L5：scaffold mirror 同源**

```
diff -q .workflow/context/roles/role-loading-protocol.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md
(silent)
```

✅ chg-03 完成
