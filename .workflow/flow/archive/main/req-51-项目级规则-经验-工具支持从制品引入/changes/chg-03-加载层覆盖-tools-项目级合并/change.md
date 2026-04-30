---
id: chg-03
title: "加载层：role-loading-protocol 项目级合并段 + tools-manager 项目级合并/优先匹配"
requirement: req-51
operation_type: change
---

# Change Definition

## Why（动机）

req-51（项目级规则-经验-工具支持从制品引入）OQ-2 = A 拍板：**项目级覆盖全局**。chg-01（契约底座-artifacts-project-豁免）落契约段、chg-02（升级保护-mirror-protected-双豁免）落升级保护，但 stage 角色加载经验文件时仍只读 `.workflow/context/experience/`、tools-manager 仍只匹配 `.workflow/tools/index/keywords.yaml`——**项目级 constraints / experience / tools 的实际生效语义没有落到加载链**，AC-05（加载顺序与冲突解决）/ AC-06（工具项目级化）会卡在加载层不通。

本 chg 的 scope 覆盖三处加载链改动：

1. `role-loading-protocol.md` Step 7 加项目级合并段（明确加载顺序：项目级 > 全局，同名时项目级覆盖全局，文件级覆盖而非段落级 merge）；
2. `tools-manager.md` SOP Step 2 加项目级合并段（先读项目级 keywords.yaml + ratings.yaml + catalog/，再 fallback 读全局；同名 tool_id 项目级优先）；
3. scaffold_v2 mirror 同步两文件（硬门禁五合规）。

## Scope（范围）

### In Scope

1. **`.workflow/context/roles/role-loading-protocol.md`**：在 Step 7（按需加载附加上下文）后**新增 Step 7.6：项目级覆盖加载段**，定义：
   - 项目级路径 = `artifacts/{branch}/project/{constraints,experience,tools}/`（落 chg-01 OQ-1 = B-modified）；
   - 加载顺序：先全局 → 后项目级（按文件名匹配，同名项目级覆盖全局；不同名两者并存）；
   - 不参与项目级覆盖的子类：`roles/` / `role-model-map.yaml`（OQ-3 = A 已明确不开放）；
   - fallback：项目级路径不存在时静默跳过，不报错（与 task_context_index 回退语义一致）；
2. **`.workflow/context/roles/tools-manager.md`**：在 Step 2（读取本地工具索引）顶部插入项目级合并段：
   - 先读 `artifacts/main/project/tools/index/keywords.yaml` 与 `ratings.yaml`（若存在），合并到全局 `.workflow/tools/index/keywords.yaml` / `ratings.yaml` 之上；
   - 同名 `tool_id` 时项目级覆盖全局（OQ-2 = A）；
   - catalog 路径优先级：先匹配 `artifacts/main/project/tools/catalog/{tool_id}.md`，未命中再 fallback `.workflow/tools/catalog/{tool_id}.md`；
   - protocols 同理：先 `artifacts/main/project/tools/protocols/`，再 `.workflow/tools/protocols/`；
3. **scaffold_v2 mirror 同步**：`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md` + `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/tools-manager.md` 与 live 同 commit（硬门禁五合规）；
4. **新增** `tests/test_req51_project_level_loading.py`：覆盖加载链项目级覆盖语义（≥ 3 个 TC）。

### Out of Scope

- 契约段落（`repository-layout.md`）→ 已归 chg-01；
- helper 升级保护（mirror / protected-zones 豁免）→ 已归 chg-02；
- 端到端 dogfood + AC-07 / AC-08 真实 PetMallPlatform 验证 → 归 chg-04（dogfood端到端-ac07-08验证）；
- `roles/` 项目级化 / role-model-map.yaml 项目级覆盖 → OQ-3 = A 拍板不在范围；
- "项目级不得删全局硬门禁字段" lint → OQ-5 = A 拍板入 sug 池，不在本 req。

## 接口面（对外约束）

- **`role-loading-protocol.md`**：Step 7.6 是 **新增** step，不破坏现有 Step 1 ~ Step 7.5 顺序；所有 stage / 辅助角色按本协议加载（影响面 = 全部角色）；
- **`tools-manager.md`**：Step 2 顶部插入项目级合并段，输入 / 输出格式（"toolsManager 查询结果"）不变；
- **scaffold_v2 mirror**：硬门禁五要求两个文件 live + mirror 同 commit；
- **新测试** `tests/test_req51_project_level_loading.py`：3+ 个 TC，验证加载顺序 / 覆盖语义 / fallback。

## 影响面

- **直接影响**：role-loading-protocol.md / tools-manager.md / 两 mirror 副本 / 1 个新测试文件；
- **间接影响**：所有 stage 角色（按 role-loading-protocol 加载经验 / constraints）+ 所有 tools-manager 调用（catalog / index 匹配）；
- **下游用户感知**：本 chg 落地后，下游用户在 `artifacts/main/project/experience/roles/analyst.md` 写自定义经验，stage 加载链优先读项目级版本；下游用户在 `artifacts/main/project/tools/catalog/my-tool.md` + `index/keywords.yaml` 加自定义工具，`harness tool-search my-tool` 命中。

## 验收边界（chg 级 PASS 条件）

- AC-05（加载顺序与冲突解决）：`role-loading-protocol.md` 含 Step 7.6 项目级合并段；测试断言项目级与全局同名时项目级优先；
- AC-06（工具项目级化）：`tools-manager.md` SOP Step 2 含项目级合并段；测试断言 `harness tool-search` 命中项目级工具；
- mirror 同步合规：`diff -q` live + mirror 字节级一致；
- `pytest tests/test_req51_project_level_loading.py -v` 全 PASS；
- `harness validate --contract all` exit 0。
