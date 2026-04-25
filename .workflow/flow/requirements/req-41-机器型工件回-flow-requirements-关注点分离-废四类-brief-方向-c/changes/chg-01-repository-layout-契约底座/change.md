# Change

## 1. Title

repository-layout 契约底座（git mv + 三大子树 §2 重写）

## 2. Goal

- 把 `.workflow/flow/artifacts-layout.md` 重命名为 `.workflow/flow/repository-layout.md`，语义从"artifacts 子树"升格到"全仓库三大子树"（state/ / flow/ / artifacts/），作为 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））所有后续 chg 的契约底座；白名单段同步删除四类 brief + 耗时与用量报告行、加 raw `requirement.md` 副本声明。

## 3. Requirement

- `req-41`（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））

## 4. Scope

### Included

- `git mv .workflow/flow/artifacts-layout.md .workflow/flow/repository-layout.md`（保留 history）；
- `repository-layout.md` §1 新增"三大子树语义总览"段：一次性定义 `.workflow/state/`（runtime 真实时数据）/ `.workflow/flow/`（权威工作流工件）/ `artifacts/`（对人可读签字执行产物）三大子树职责；
- §2 对人文档白名单：删除 `需求摘要.md` / `chg-NN-变更简报.md` / `chg-NN-实施说明.md` / `reg-NN-回归简报.md` / `耗时与用量报告.md` 五行；保留 raw `requirement.md`（artifacts 副本）/ `交付总结.md` / `决策汇总.md` / SQL / 部署文档 / 接入配置说明 / runbook / 手册 / 合同附件；新增"raw `requirement.md` 副本"说明段；
- §3 原"机器型文档迁移位"段重写为"机器型文档权威落位（`.workflow/flow/requirements/{req-id}-{slug}/`）"，明示 `requirement.md` / `changes/{chg-id}-{slug}/{change.md, plan.md, session-memory.md}` / `regressions/{reg-id}-{slug}/...` / `task-context/` / `usage-log.yaml` / req yaml 全部落位；
- §4 / §5 历史存量豁免段加分水岭说明：req-02（workflow 分包结构修复）~ req-38（api-document-upload 工具闭环）legacy、req-39（对人文档家族契约化）/ req-40（阶段合并与用户介入窄化）flat layout 过渡、req-41+ flow/ 新位；
- 同步 scaffold_v2 mirror：`git mv src/harness_workflow/assets/scaffold_v2/.workflow/flow/artifacts-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` + 内容同步；
- 涉及文件：
  - live：`.workflow/flow/repository-layout.md`（新）
  - mirror：`src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md`（新）

### Excluded

- **不动** CLI 代码（归属 chg-02（CLI 路径迁移 flow layout））；
- **不动** `validate_human_docs.py` 扫描逻辑（归属 chg-03（validate_human_docs 重写删四类 brief））；
- **不动** 角色文件（归属 chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止））；
- **不动** `done.md` 交付总结模板（归属 chg-05（done 交付总结扩效率与成本段））；
- **不动** `harness-manager.md`（归属 chg-06（harness-manager Step 4 派发硬门禁））；
- **不跑** dogfood（归属 chg-07（dogfood + scaffold_v2 mirror 收口））；
- **不改** base-role.md 硬门禁六文字（归属 chg-08（硬门禁六扩 TaskList + stdout + 提交信息））；
- **不迁移、不删除**历史存量 brief（`artifacts/main/requirements/req-02 ~ req-40` 下现存的四类 brief 原地保留，git log 自带分水岭）。

## 5. Acceptance

- Covers requirement.md **AC-01**（Scope-共骨架）：
  - `test -f .workflow/flow/repository-layout.md`（存在）；
  - `test ! -f .workflow/flow/artifacts-layout.md`（旧名不存在）；
  - `grep -c "^## " .workflow/flow/repository-layout.md` ≥ 5（覆盖 §1 总览 / §2 白名单 / §3 机器型落位 / §4 §5 历史豁免）；
  - `grep "artifacts-layout.md" .workflow/ -r` 命中数 = 0（后续 chg 收口，本 chg 不强求）；本 chg 交付时只保证 `.workflow/flow/` 内无旧名引用即可。
- Covers requirement.md **AC-07**（Scope-废 brief 白名单清理起点）：
  - `grep -E "需求摘要|变更简报|实施说明|回归简报|耗时与用量报告" .workflow/flow/repository-layout.md` 命中数 = 0。
- Covers requirement.md **AC-15**（scaffold_v2 mirror 同步起点）：
  - `diff -q .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` 无输出；
  - `test ! -f src/harness_workflow/assets/scaffold_v2/.workflow/flow/artifacts-layout.md`。
- Covers requirement.md **AC-14**（契约 7 + 硬门禁六 + 批量列举子条款自证）：
  - `repository-layout.md` 内首次引用 `req-*` / `chg-*` / `sug-*` / `bugfix-*` / `reg-*` 均带 title 或 ≤ 15 字描述；裸 id 命中数 = 0。

## 6. Risks

- **风险 1：git mv 在某些 setup 下退化为 add+rm 丢 history**。缓解：executing 明确使用 `git mv` 而非 `mv + git add/rm`；commit 后 `git log --follow .workflow/flow/repository-layout.md` 确认 history 贯通。
- **风险 2：后续 chg 引用旧名 `artifacts-layout.md` 漏改导致 CLI / 角色文件引用断裂**。缓解：chg-02 / chg-03 / chg-04 在各自 executing 步骤最后跑 `grep -r "artifacts-layout.md" .workflow/ src/` 自检；chg-07 dogfood 做最终收口 grep。
- **风险 3：§2 白名单删四类 brief 后 req-39（对人文档家族契约化）/ req-40（阶段合并与用户介入窄化）legacy validate 被误伤**。缓解：本 chg 只改契约文档，不动 `validate_human_docs.py` 扫描逻辑；chg-03（validate_human_docs 重写）新增 `BRIEF_DEPRECATED_FROM_REQ_ID = 41` 分水岭常量，req-39/40 维持现行扫描行为。
