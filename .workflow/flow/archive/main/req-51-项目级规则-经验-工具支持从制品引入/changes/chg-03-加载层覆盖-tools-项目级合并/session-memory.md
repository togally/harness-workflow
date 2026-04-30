# Session Memory — req-51（项目级规则-经验-工具支持从制品引入）/ chg-03（加载层覆盖：role-loading-protocol 项目级合并段 + tools-manager 项目级合并/优先匹配）

> 本 session-memory.md 由 analyst Phase 3 占位创建；executing 阶段接手时按 `## 1. Current Goal` 与 plan.md 步骤填充实施记录。

## 1. Current Goal

按 chg-03 plan.md §1 / §2：在 `role-loading-protocol.md` 加 Step 7.6（项目级覆盖加载段）+ `tools-manager.md` Step 2.0（项目级合并段）+ scaffold_v2 mirror 同步两文件 + 新增 helper `_merge_project_level_files` + 新增 `tests/test_req51_project_level_loading.py`（≥ 6 个 TC）。

## 2. Context Chain

- Level 0: 主 agent → req-51 / executing stage（待派发）
- Level 1: analyst（opus）→ Phase 2 + Phase 3 落盘（已完成）
- Level 2: executing（sonnet）→ 按 plan.md 实施（待派发，本 chg 与 chg-02 可平行落，依赖 chg-01 已 ship）

## 3. Completed Tasks

- Step 1: 编辑 live `role-loading-protocol.md`：插入 Step 7.6 项目级覆盖加载段 + 更新流程速查图（加 "项目级覆盖加载" 节点）
- Step 2: 编辑 live `tools-manager.md`：Step 2 标题后插入 Step 2.0 项目级合并段（表格使用 main 分支明确路径）
- Step 3: 同步两文件到 scaffold_v2 mirror（硬门禁五合规）
- Step 4: 新增 helper `_merge_project_level_files`（workflow_helpers.py 末尾追加，约 30 行）
- Step 5: 写新测试 `tests/test_req51_project_level_loading.py`（7 个 TC）

## 4. Results（完整 lint stdout）

```
=== L1: role-loading-protocol Step 7.6 落地 ===
grep -n "Step 7.6：项目级覆盖加载" .workflow/context/roles/role-loading-protocol.md
125:（命中 1 行）

grep -c "artifacts/{branch}/project/" .workflow/context/roles/role-loading-protocol.md
4

grep -nE "OQ-2 = A|OQ-3 = A" .workflow/context/roles/role-loading-protocol.md
127: OQ-2 = A / OQ-3 = A（命中 2+ 行）

=== L2: tools-manager Step 2.0 项目级合并段 ===
grep -n "项目级合并" .workflow/context/roles/tools-manager.md
16:（命中 1 行）

grep -c "artifacts/main/project/tools/" .workflow/context/roles/tools-manager.md
6

=== L3: scaffold mirror 字节级同源 ===
diff -q role-loading-protocol.md mirror/role-loading-protocol.md
(silent)
diff -q tools-manager.md mirror/tools-manager.md
(silent)

=== L4: helper 落地 ===
grep -n "def _merge_project_level_files" src/harness_workflow/workflow_helpers.py
8278:（命中 1 行）

python3 -c "from harness_workflow.workflow_helpers import _merge_project_level_files; assert callable(_merge_project_level_files)"
callable: OK

=== L5: 新测试全 PASS ===
pytest tests/test_req51_project_level_loading.py -v
7 passed in 0.07s
```

## 5. Next Steps

chg-04（dogfood 端到端）接手。

## 6. default-pick 决策清单

| 决策点 | 结果 | 理由 |
|------|------|------|
| 决策点 1：tools-manager.md 表格使用 main 还是 {branch} | 使用 main（同时保留注释说"按 branch 名称替换"） | plan.md L2 lint 明确 grep artifacts/main/project/tools/，表格必须含 main |

✅ chg-03 完成
