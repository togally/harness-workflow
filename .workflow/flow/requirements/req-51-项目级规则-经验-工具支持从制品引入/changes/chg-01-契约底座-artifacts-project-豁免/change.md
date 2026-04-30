---
id: chg-01
title: "契约底座：artifacts/{branch}/project/ 豁免段 + 硬门禁五例外白名单 + scaffold_v2 mirror 同步"
requirement: req-51
operation_type: change
---

# Change Definition

## Why（动机）

req-51（项目级规则-经验-工具支持从制品引入）OQ Verdicts 已锁定 `{project-path}` = `artifacts/{branch}/project/{constraints,experience,tools}/`（OQ-1 = B-modified）。本路径与 `repository-layout.md` §1 / §3 现有"机器型不入 artifacts/"契约**正面冲突**，必须先在契约底座层显式开**唯一三类豁免**，否则下游 helper / 加载层 / dogfood 全链路改动失去契约依据；同时硬门禁五（跨 repo scaffold mirror 同步）例外白名单必须配套扩展，否则下游用户在 `artifacts/{branch}/project/` 写文件会被 reviewer / done 阶段误判 mirror 漂移。

本 chg 是后续 chg-02 / chg-03 / chg-04 的**契约前置**：未先落契约底座，helper 改动 / 加载层改动均无锚点。

## Scope（范围）

### In Scope

1. **`repository-layout.md` §2 白名单段新增 1 段**：`artifacts/{branch}/project/{constraints,experience,tools}/` 三类项目级机器型文档豁免；声明语义 / 产出者 / 消费者；
2. **`repository-layout.md` §3 / §3.2 顶部新增豁免说明段**：项目级三类豁免不破坏全局"机器型不入 artifacts/"原则；其他机器型文档严禁入 artifacts/ 不变；
3. **`harness-manager.md` 硬门禁五例外白名单新增 1 条**：`artifacts/{branch}/project/`；与现有 `artifacts/` 例外、 `.workflow/context/team/` / `.workflow/context/project/` 等条目并列生效；
4. **scaffold_v2 mirror 同步**（硬门禁五本身的合规要求）：`src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` 与 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` 必须在**同一 commit** 同步；
5. **artifacts/{branch}/project/ 占位 README**：在仓库根 `artifacts/main/project/` 下创建占位 README.md 与三个空子目录占位（`constraints/.gitkeep` / `experience/.gitkeep` / `tools/.gitkeep`），声明本目录是 req-51 项目级承载层；不写入任何机器型契约内容，仅作示范。

### Out of Scope

- helper 层改动（`workflow_helpers.py::install_repo` / `update_repo` / `_install_self_audit` / `_managed_file_contents` / `_scaffold_v2_file_contents`）→ 归 chg-02（升级保护-mirror-protected-双豁免）；
- 加载层改动（`role-loading-protocol.md` / `tools-manager` 加载链）→ 归 chg-03（加载层覆盖-tools-项目级合并）；
- 端到端 dogfood TC + PetMallPlatform 真实验证 → 归 chg-04（dogfood端到端-ac07-08验证）；
- `roles/` 项目级化、`role-model-map.yaml` 项目级覆盖 → req-51 OQ-3 = A 已明确不在范围；
- 项目级"不得删全局硬门禁字段" lint → req-51 OQ-5 = A 拍板入 sug 池，不在本 req。

## 接口面（对外约束）

- **`repository-layout.md`**：契约底座（version: 2 不动；新增段落不破坏现有 §1/§3 既定子树语义）；
- **`harness-manager.md` 硬门禁五例外白名单**：新增条目必须可被 grep `artifacts/{branch}/project/` / `artifacts/main/project` 直接命中；
- **scaffold_v2 mirror**：`src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` / `harness-manager.md` 与 live 同 commit。

## 影响面

- **直接影响**：repository-layout.md / harness-manager.md / scaffold_v2 mirror 副本（4 个文件 + 1 个 README + 3 个 .gitkeep）；
- **间接影响**：chg-02 / chg-03 / chg-04 全部以本 chg 落地的契约段为锚点；
- **下游用户感知**：本 chg 单独落地后，下游用户读 `repository-layout.md` 即可知 `artifacts/main/project/` 是合法承载层，但此时 `harness install --force-managed` 仍会刷新该目录（helper 层改动归 chg-02）—— 必须 chg-01 + chg-02 一起 ship 才有完整保护。

## 验收边界（chg 级 PASS 条件）

- AC-01（路径承载与契约定义）部分：`repository-layout.md` 含项目级承载段，`harness validate --human-docs` exit 0；
- AC-04（mirror 同步豁免）部分：`harness-manager.md` 硬门禁五例外白名单 grep `artifacts/{branch}/project/` 命中；
- scaffold_v2 mirror 与 live 完全一致（`diff -rq .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` 无差）；
- `harness validate --contract all` exit 0（确认未误伤其他契约）。

完整 AC 验证（含 AC-02 / AC-03 / AC-05 / AC-06 / AC-07 / AC-08）依赖 chg-02 / chg-03 / chg-04 联合落地。
