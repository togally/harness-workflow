---
id: chg-01
title: "契约层路径迁移：项目级承载层从 artifacts/{branch}/project/ 改为 artifacts/project/（双轨过渡）+ scaffold mirror 同步"
requirement: req-52
operation_type: change
---

# Change Definition

## Why（动机）

req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）OQ-A = D-modified 已锁定 `{project-path}` 主路径 = `artifacts/project/{constraints,experience,tools}/`（**无 branch 维度**）；legacy `artifacts/{branch}/project/` 作为加载链 fallback。本契约改动是**全 req 前置**——不先在契约底座层改路径表 + 加载链描述 + 硬门禁五例外白名单，下游 chg-02（src 改路径常量）/ chg-03（索引懒加载 schema）/ chg-04（接入主流程 + 日志）全部失去契约依据。

req-51（项目级规则-经验-工具支持从制品引入）/ chg-01（契约底座-artifacts-project-豁免）已落契约底座；本 chg 是**对 req-51 契约的 path-only 增量**：仅改主路径 + 加双轨 fallback 段，不动豁免范围（仍是 constraints / experience / tools 三类）。

## Scope（范围）

### In Scope

1. **`repository-layout.md` §2.1 项目级机器型豁免段**：把表内的 `artifacts/{branch}/project/{...}/` 改为 `artifacts/project/{...}/`（无 branch）；新增"双轨过渡 fallback"说明子段，描述 legacy `artifacts/{branch}/project/` 作为加载链 fallback、`harness install` / `update` 全流程跳过、后续 req 退役；
2. **`repository-layout.md` §3 顶部豁免说明段**：同步路径，从 `artifacts/{branch}/project/...` 改为 `artifacts/project/...`；保留 legacy fallback 说明；
3. **`repository-layout.md` §1 注脚**：同步路径；
4. **`harness-manager.md` 硬门禁五例外白名单段**：现有 `artifacts/{branch}/project/` 条目改为 `artifacts/project/`（主路径）+ 保留 `artifacts/{branch}/project/`（legacy fallback）共 2 条；
5. **`role-loading-protocol.md` Step 7.6 项目级承载路径段**：从 `artifacts/{branch}/project/...` 改为 `artifacts/project/...`；新增"加载顺序：先扫主路径，未命中再 fallback 到 `artifacts/{branch}/project/`"描述；
6. **`tools-manager.md` Step 2.0 项目级合并段**：表内 `artifacts/main/project/tools/...` 路径示例改为 `artifacts/project/tools/...`；fallback 描述同步；
7. **scaffold_v2 mirror 同步**（硬门禁五合规要求）：`src/harness_workflow/assets/scaffold_v2/.workflow/{flow/repository-layout.md, context/roles/harness-manager.md, context/roles/role-loading-protocol.md, context/roles/tools-manager.md}` 4 份 mirror 同 commit 镜像；
8. **`artifacts/project/` 占位 README + 三子目录 .gitkeep**：与现 `artifacts/main/project/` 同结构，声明本目录由 req-52 OQ-A = D-modified 开放为新主路径。

### Out of Scope

- src 层硬编码 main 字面值改动（`_SCAFFOLD_V2_MIRROR_WHITELIST` / validate_contract.py / `_next_req_id` 等）→ 归 chg-02（src硬编码main全面去除-branch-aware）；
- 子目录 `index.md` 模板 + `_load_project_level_index` helper → 归 chg-03（索引懒加载-index-md与加载链改造）；
- `_merge_project_level_files` 接入主流程 + stderr 日志 + 端到端 CLI test → 归 chg-04（接入主流程-stderr日志-端到端CLI验证）；
- `artifacts/main/project/` 目录的退役 / 删除 → 后续 req 收口，本 chg 不动。

## 接口面（对外约束）

- **`repository-layout.md`**：契约底座（version: 2 不动；新增"双轨过渡 fallback"子段，不破坏 §1/§3 既定语义）；
- **`harness-manager.md` 硬门禁五例外白名单**：grep `artifacts/project/` / `artifacts/{branch}/project/` 各命中 ≥ 1；
- **`role-loading-protocol.md` Step 7.6**：grep `artifacts/project/{constraints,experience,tools}/` 命中 ≥ 1；
- **`tools-manager.md` Step 2.0**：grep `artifacts/project/tools/` 命中 ≥ 1；
- **scaffold_v2 mirror**：4 份 mirror 与 live 字节级一致（`diff -q` silent）。

## 影响面

- **直接影响**：4 份契约文件 + 4 份 scaffold_v2 mirror + 1 份新建 README + 3 个 .gitkeep（共 12 个文件）；
- **间接影响**：chg-02 / chg-03 / chg-04 全部以本 chg 落地的契约段为锚点；
- **下游用户感知**：本 chg 单独落地后，下游用户可读到 `repository-layout.md` 中"项目级承载层主路径 = `artifacts/project/`"的新契约定义；但此时 `harness install --force-managed` 仍可能刷新该新主路径（helper 层改动归 chg-02）；必须 chg-01 + chg-02 一起 ship 才有完整保护。

## 验收边界（chg 级 PASS 条件）

- AC-01（路径迁移到无 branch 主路径）部分：`repository-layout.md` 含主路径段，`grep -nE "artifacts/project/" .workflow/flow/repository-layout.md` ≥ 3 命中；
- AC-08（scaffold mirror 同步 + contract 全绿）部分：4 份 live + mirror `diff -q` silent；`harness validate --human-docs` exit 0；`harness validate --contract all` exit 0（确认未误伤其他契约）。

完整 AC 验证（AC-02 fallback 行为 / AC-03 src 硬编码去除 / AC-04 反例 lint / AC-05 索引懒加载 / AC-06 接入主流程 / AC-07 端到端 CLI 触发）依赖 chg-02 / chg-03 / chg-04 联合落地。
