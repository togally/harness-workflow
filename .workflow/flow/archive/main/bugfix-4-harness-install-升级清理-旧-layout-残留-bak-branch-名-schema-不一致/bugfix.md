---
id: bugfix-4
title: harness install 升级清理：旧 layout 残留 / .bak / branch 名 / schema 不一致
created_at: 2026-04-25
diagnosed_at: 2026-04-25
diagnosed_by: regression / opus
---

# Problem Description

存量项目（样本：`/Users/jiazhiwei/claudeProject/PetMallPlatform/`）多次 `harness install` 后留下四类残留，install 屡次执行均无法自我清理：

1. **双 layout 共存**：`.workflow/flow/artifacts-layout.md`（req-39（对人文档家族契约化 + artifacts 扁平化）旧契约）+ `.workflow/flow/repository-layout.md`（req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））新契约）。
2. **req schema 不一致**：`.workflow/state/requirements/req-03.yaml` + `req-03.yaml.bak`（schema 迁移产生的备份永久驻留）；`req-06/`（folder 形态，无 yaml，仅含 `testing-report.md` / `acceptance-report.md`，属早期 legacy schema）。
3. **branch 多形态**：`artifacts/main/` + `artifacts/member/` + `artifacts/v1.0.0/`；归档目录 `flow/archive/member-v1.0.0/` 形态。installer 无 branch 命名规约校验。
4. **flow/requirements 空**：尚无 req-id ≥ 41 的新 req 落地，install 同步契约迁移逻辑没回填存量 req。

# Root Cause Analysis

详见 `regression/diagnosis.md`，三层根因摘要：

- **install 设计层（只增不删）**：`install_repo` 末尾 `cleanup_legacy_workflow_artifacts` 仅按 `LEGACY_CLEANUP_TARGETS` 硬编码白名单清 req-02 ~ req-30 期残留；`_sync_scaffold_v2_mirror_to_live` 是 mirror→live 单向 push，旧 layout 文件（如 `artifacts-layout.md`）在 mirror 中已删却**无任何机制**把存量项目 live 端的旧文件 prune 掉。
- **schema 演进层（升级不收尾）**：`_migrate_state_files` 在升 schema 时 `shutil.copy2` 写 `.bak` 主备份，**没有任何后续清理步骤**；schema 探测面只扫 `*.yaml`，对早期 folder 形态（req-id ≤ 38 legacy）完全无识别能力。
- **branch 命名层（契约抽象但无规约）**：`repository-layout.md` `{branch}` 抽象占位但未明示命名空间；installer 接受任何 branch 字符串不做格式校验。属用户设计自由，但契约应明示规约——**不在本 bugfix install 修复范围**，应 spawn 独立工作项。

# Fix Scope

**范围内**：
- `src/harness_workflow/workflow_helpers.py`：扩展 `LEGACY_CLEANUP_TARGETS` + 新写 `cleanup_state_bak_files` + `_migrate_state_files` 加 folder-skip 分支 + 加 audit 报告 stdout。
- `tests/test_install_cleanup.py`（新增或扩展）：fixture 模拟存量项目残留，断言清理生效。
- 端到端：在 `/Users/jiazhiwei/claudeProject/PetMallPlatform/` 跑一次 `harness install` 活证。

**范围外**（明确声明）：
- branch 命名规约设计：另起 sug / req（独立工作项）。
- req-39 → req-41 演进期更多文件残留盘点：由 chg-3 audit 报告产出后再另起 sug。
- schema 全静默迁移（diagnosis.md §4 方向 C）：违反硬门禁四例外 (i) "数据丢失风险"，本 bugfix 不采纳。

# Fix Plan

**chg DAG（4 chg，详见 diagnosis.md §5.2）**：

| chg | 标题 | 主要改动 |
|-----|------|---------|
| **chg-1（install_repo cleanup 扩 layout 残留）** | layout 残留扫描 | `LEGACY_CLEANUP_TARGETS` 加 `flow/artifacts-layout.md` + 后续 req-39 → req-41 演进残留候选；`cleanup_legacy_workflow_artifacts` 自动归档到 `.workflow/context/backup/legacy-cleanup/` |
| **chg-2（state .bak 残留清理 helper）** | `.bak` 自动归档 | 新 helper `cleanup_state_bak_files`：扫 `state/requirements/*.yaml.bak` + `runtime.yaml.bak`；同名主文件存在且新 schema 完整时归档 `.bak`，主文件缺失时 stderr 告警保留 |
| **chg-3（schema 探测扩 folder 形态 + audit 报告）** | folder schema 识别 | `_migrate_state_files` 加分支扫 `requirements/req-XX/`（folder）；stdout 列 legacy folder 清单，**不迁移**（历史豁免规则 / `repository-layout.md` §4） |
| **chg-4（pytest fixture + PetMallPlatform 跑一次活证）** | 端到端验证 | 加 fixture 模拟双 layout / .bak / req-XX folder 三类残留；断言 install 后 `artifacts-layout.md` 已迁 backup、`.bak` 已迁、folder 列入 audit；PetMallPlatform 实操跑 |

**DAG**：chg-1 / chg-2 互不依赖可并行 → chg-3（探测扩展）→ chg-4（活证收尾）。

# Validation Criteria

- pytest 全绿；新增 `test_install_cleanup.py` 至少 3 类残留 fixture 全 PASS。
- PetMallPlatform 跑 `harness install` 后实地校验：
  - `.workflow/flow/artifacts-layout.md` 已归档到 `.workflow/context/backup/legacy-cleanup/flow/artifacts-layout.md`；
  - `.workflow/state/requirements/req-03.yaml.bak` 已归档到 `.workflow/context/backup/legacy-cleanup/state-bak/req-03.yaml.bak`；
  - `.workflow/state/requirements/req-06/`（folder）原位保留（历史豁免）但 install stdout 报告列出 "schema legacy folder: req-06"；
  - `repository-layout.md` 不动；`artifacts/{main,member,v1.0.0}/` 三 branch 全部不动（不在 install cleanup 范围）。
- `harness validate --contract all` 得绿；contract 7 / 硬门禁六 / 硬门禁七 自检无回归。

# Routing

- [x] Real issue（部分真实）→ proceed to fix
- 下一阶段：**executing**（按 chg DAG 实施）。
- 不转 requirement_review（问题聚焦在 `install_repo` 函数级闭环缺口，无需契约重写）。
