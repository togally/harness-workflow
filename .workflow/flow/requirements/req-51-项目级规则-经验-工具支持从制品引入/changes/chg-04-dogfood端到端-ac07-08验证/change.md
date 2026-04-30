---
id: chg-04
title: "dogfood 端到端 TC + AC-07/08 验证脚本（tmpdir 完整链路 + PetMallPlatform 真实仓引导）"
requirement: req-51
operation_type: change
---

# Change Definition

## Why（动机）

req-51（项目级规则-经验-工具支持从制品引入）AC-07（dogfood 端到端 TC）+ AC-08（PetMallPlatform 真实验证）需要把 chg-01（契约底座-artifacts-project-豁免）/ chg-02（升级保护-mirror-protected-双豁免）/ chg-03（加载层覆盖-tools-项目级合并）三个 chg 的结果**串联端到端验证**：

- chg-02 的 dogfood TC 仅覆盖单点（install 保留 / force-managed 不覆盖 / self-audit 不报 drift）；
- chg-03 的 TC 仅覆盖加载链合并语义；
- 真正的端到端要验证：tmpdir 模拟一个下游仓 → 同时写项目级 constraints / experience / tools 三类文件 → 跑完整 install / validate / 加载链 → 全部断言通过；
- AC-08 需要 PetMallPlatform 真实仓的引导脚本 / runbook，让用户在自己仓按步骤验证（用户原话："我希望把规则和经验工具等支持从制品引入"是面向 PetMallPlatform / uav 等真实下游的需求）。

本 chg 是 req-51 收口 chg：所有前置 chg 落地后，本 chg 提供端到端活证 + 用户验证手册。

## Scope（范围）

### In Scope

1. **新增** `tests/test_req51_project_level_dogfood.py`：tmpdir 端到端 TC，覆盖：
   - TC-Dogfood-01：tmpdir 同时写 `artifacts/main/project/{constraints/my-rule.md, experience/roles/analyst.md, tools/catalog/my-tool.md, tools/index/keywords.yaml}` 4 个文件；
   - TC-Dogfood-02：跑 `harness install --force-managed` → 4 文件全保留（diff = 0）；
   - TC-Dogfood-03：跑 `harness validate --contract user-write-protected-zones` → exit 0；
   - TC-Dogfood-04：跑 `harness validate --contract all` → exit 0；
   - TC-Dogfood-05：调 `_merge_project_level_files` 验证加载链项目级覆盖（与 chg-03 TC-03 重复，但本 chg 是端到端 fixture 内的串联断言，不重复测试粒度）；
2. **新增** `artifacts/main/project/README.md` 升级**为 PetMallPlatform 引导手册**：在 chg-01 占位 README 基础上，补充 AC-08 的 step-by-step 验证手册（如何在自己仓写 1 条项目级规则 + 1 份项目级经验 + 1 个项目级工具 catalog 条目，如何跑 `harness install --force-managed` 验证保留，如何 grep 项目级规则被加载链命中）；
3. **新增** `tests/test_req51_project_level_dogfood.py::test_petmall_runbook_existence`：仅断言 `artifacts/main/project/README.md` 存在 + 含 AC-08 关键字段（"PetMallPlatform" / "AC-08" / "harness install --force-managed"），保证 runbook 不丢失；
4. **scaffold_v2 mirror 同步**：本 chg **不**触发硬门禁五（src/ + tests/ + artifacts/ 均不在保护面）。

### Out of Scope

- 契约段落（repository-layout / harness-manager 例外白名单）→ 已归 chg-01；
- helper 升级保护 + protected-zones 豁免 → 已归 chg-02；
- 加载层（role-loading-protocol / tools-manager）→ 已归 chg-03；
- PetMallPlatform 自身仓的真实 install 跑 → AC-08 由用户在自己仓执行，本 chg 仅交付 runbook；
- 跨项目共享项目级规则、roles/ 项目级化、role-model-map.yaml 项目级覆盖 → req-51 § Out of scope 明确不在范围。

## 接口面（对外约束）

- **`tests/test_req51_project_level_dogfood.py`**：≥ 5 个 TC，使用 `tmp_path` fixture + `subprocess.run([sys.executable, "-m", "harness_workflow.cli", "install", "--force-managed"], cwd=tmp_path)` 子进程调用，端到端串联；
- **`artifacts/main/project/README.md`**：升级为 AC-08 PetMallPlatform 引导手册（用户面文档），不破坏 chg-01 占位 README 字段（含 `req-51` / `OQ-1` 关键字）；
- **dogfood TC 必填字段**（sug-52 落地）：每个 TC 含 tmpdir fixture / 子进程命令 / stdout 断言 / runtime stage 断言（如适用）/ feedback.jsonl 事件数断言 / 对应 AC 字段非空 / 优先级 P0。

## 影响面

- **直接影响**：1 个新测试文件 + 1 个 README 升级；
- **间接影响**：本 chg 是 chg-01 ~ chg-03 的端到端验证收口，前置 chg 任一未落地 → 本 chg 测试 FAIL；
- **下游用户感知**：本 chg 落地后，用户在 PetMallPlatform 仓按 README 手册操作，可一次性验证项目级规则 / 经验 / 工具的完整生命周期（写 → install → validate → 加载链命中）。

## 验收边界（chg 级 PASS 条件）

- AC-07（dogfood 端到端 TC）：`pytest tests/test_req51_project_level_dogfood.py -v` 全 PASS（≥ 5 个 TC）；
- AC-08（PetMallPlatform 真实验证）：本 chg 交付 runbook（`artifacts/main/project/README.md`）+ 断言 runbook 存在 + 含 AC-08 关键字；用户在自己仓按 runbook 步骤验证由用户 gate（不在本 chg 自动化范围）；
- `harness validate --contract all` exit 0；
- `pytest tests/ -k "req51" -v` 全 PASS（chg-02 + chg-03 + chg-04 联合活证）。
