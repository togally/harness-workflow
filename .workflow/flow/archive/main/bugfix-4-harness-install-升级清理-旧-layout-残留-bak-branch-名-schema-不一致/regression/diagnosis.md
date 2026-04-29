# Regression Diagnosis — bugfix-4（harness install 升级清理：旧 layout 残留 / .bak / branch 名 / schema 不一致）

> 角色：诊断师（regression / opus）
> expected_model：opus；本次 subagent 自省返回：opus（一致，无降级）
> 现场样本：`/Users/jiazhiwei/claudeProject/PetMallPlatform/`（用户存量项目，已多次 `harness install`）
> 主诊断对象：`src/harness_workflow/workflow_helpers.py::install_repo` + `cleanup_legacy_workflow_artifacts` + `_migrate_state_files` + `_sync_scaffold_v2_mirror_to_live`

---

## 1. Issue（问题陈述）

PetMallPlatform 跑过若干次 `harness install` 后，`.workflow/` 与 `artifacts/` 出现以下持久残留，install 屡次执行均无法自我清理：

| # | 残留 | 路径样本 | 性质 |
|---|------|---------|------|
| 1 | 双 layout 共存 | `.workflow/flow/artifacts-layout.md` + `.workflow/flow/repository-layout.md` | 旧 req-39（对人文档家族契约化 + artifacts 扁平化）契约文件 + 新 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））契约文件并存（旧的应被替代） |
| 2 | req schema 不一致 | `.workflow/state/requirements/req-03.yaml` + `req-03.yaml.bak`；`req-06/`（folder，仅含 `testing-report.md` / `acceptance-report.md`，无 `.yaml`） | `_migrate_state_files` 在升级 schema 时**只生成 .bak、不删**；早期 folder 形态 req（req-id ≤ 38）schema 与新 yaml schema 共存 |
| 3 | branch 多形态 | `artifacts/main/`（标）+ `artifacts/member/` + `artifacts/v1.0.0/`；归档 `flow/archive/member-v1.0.0/`（hyphenated） | 用户用 git 分支名（`member`）、版本号（`v1.0.0`）、混写（`member-v1.0.0`）三种命名，installer 无 branch 命名规约校验 |
| 4 | flow/requirements 空 | `.workflow/flow/requirements/` 空目录 | 没有 req-id ≥ 41 的新 req 落地，没有触发新 layout 路径写入；早期 req-03 / req-04 / req-05 / req-06 全在 legacy / state-flat 路径，install 无回填迁移 |

---

## 2. 判决

**真实问题（部分真实）**。install_repo 当前对 layout 演进残留的清理面**显著不足**，但 branch 命名层属于设计自由（不应纳入 cleanup 范畴）。

一行判决：**install_repo 只增不删、schema 迁移只升不清、layout 演进无淘汰链——存量项目一次升级即留疤、多次 install 永不自愈**。

---

## 3. 根因分析（三层）

### 3.1 install 设计层 —— 只增不删

**事实链**：
- `install_repo`（`workflow_helpers.py` L3532-L3702）末尾顺序：`_sync_requirement_workflow_managed_files` → `cleanup_legacy_workflow_artifacts` → `_migrate_state_files` → `_refresh_experience_index` → `_write_project_profile_if_changed` → `_sync_scaffold_v2_mirror_to_live` → `_install_self_audit`。
- `cleanup_legacy_workflow_artifacts`（L3407-L3453）只处理 `LEGACY_CLEANUP_TARGETS` 白名单（L86-L107），白名单内是 req-02 ~ req-30 期固化下来的**陈旧目录**（`flow/`、`memory/`、`decisions/`、`runbooks/`、`templates/`、`hooks/`、`rules/`、`mcp-registry.yaml`、`business/`、`architecture/`、`debug/`、`playwright.md`、`mysql-mcp.md`、`nacos-mcp.md`、`constitution.md`），归档到 `.workflow/context/backup/legacy-cleanup/`。
- 白名单**未覆盖**：
  - `.workflow/flow/artifacts-layout.md`（req-39 旧契约文件，应在 req-41 升格 `repository-layout.md` 后淘汰）；
  - `.workflow/state/requirements/*.yaml.bak`（`_migrate_state_files` 自身产生的备份，无后续清理任务）；
  - `.workflow/state/requirements/req-XX/`（早期 folder schema，应迁 yaml 或归档，但 cleanup 完全不识别）。
- `_sync_scaffold_v2_mirror_to_live`（L3287-L3382）方向是 **mirror→live 单向 push**：mirror 里有的 push 到 live；mirror 里没有但 live 里仍存在的旧文件（如 `artifacts-layout.md`）**完全不在视野内**，所以新版 mirror 删了 `artifacts-layout.md` 也无济于事，存量项目永远留旧文件。

**根因**：install_repo 缺一个 **"对照 mirror 反向 prune live 中的过期文件"** 的清理通道（与 `_sync_scaffold_v2_mirror_to_live` 互补）；同时 `LEGACY_CLEANUP_TARGETS` 是手工硬编码、按 req-02~30 期沉淀，**没有 req-39 → req-41 的 layout 演进沉淀**。

### 3.2 schema 演进层 —— 升级不收尾

**事实链**：
- `_migrate_state_files`（L3705-L3759）做了两件事：迁 runtime.yaml 字段（加 `ff_mode` / `ff_stage_history`） + 迁 `requirements/*.yaml` 字段（`req_id` → `id`、`created` → `created_at`、补 `started_at` / `stage_timestamps`）。
- 每次迁移**先 `shutil.copy2(req_file, req_file.with_suffix('.yaml.bak'))`**（L3721-L3722、L3752-L3753）作为安全副本，然后 `save_simple_yaml` 覆写主文件。
- **没有任何后续步骤**清理这些 `.bak`：不限定保留时长、不在下次 install 时检查 main 文件是否已在新 schema、不归档到 `legacy-cleanup/`。`.bak` 一旦产生即永久驻留。
- `req-XX/` folder 形态（PetMallPlatform 的 `req-06/`）属于 **req-id ≤ 38 legacy 路径**：legacy 期的机器型工件落 `artifacts/{branch}/requirements/{req-id}-{slug}/`，state 侧不一定有 yaml；`_migrate_state_files` 只 `rglob("*.yaml")` 扫 yaml，**完全无视 folder 形态**。结果：req-03（已升级到 yaml）+ req-06（仍是 folder + 散落 testing-report.md / acceptance-report.md）schema 共存，install 既不报警也不归一。

**根因**：schema 迁移的 **"产出 .bak 但无后续清理"** 是闭环缺口；同时 schema 版本探测面**只覆盖 yaml**，对早期 folder schema 无识别能力。

### 3.3 branch 命名层 —— 契约抽象但无规约

**事实链**：
- `repository-layout.md` §1 / §3 / §4 一律使用 `{branch}` 抽象占位符，未明示 `{branch}` 的命名空间（git branch 名? 版本号? 混写?）。
- installer / archive helper 接受 `branch` 参数（`workflow_helpers.py` L4394、L4488）但**不做任何格式校验**——传什么写什么。
- PetMallPlatform 实地：`artifacts/main/`（git 分支主线）+ `artifacts/member/`（git feature 分支）+ `artifacts/v1.0.0/`（git tag / 版本号）+ `flow/archive/member-v1.0.0/`（merged 后 hyphenated 归档）。这是用户的合理使用场景：跨分支多线开发 + 版本号当 release branch。
- 但 layout 契约的 `{branch}` 抽象在多形态混用时**对 audit / cleanup / 工具 grep 是不可读的**：installer 不知道 `member-v1.0.0` 是历史归档目录还是活跃 branch，cleanup 也无规则可依。

**根因**：`{branch}` 是设计自由（属用户决定，不应在 install 强制），但 layout 契约**应明示 branch 命名规约（推荐形态 + 多形态混用规则 + 归档命名约定）**，否则 audit 工具与 cleanup 逻辑无依据。**这一层不在本 bugfix 的 install 修复范围内**，但应 spawn 一个独立 sug / req（详见路由 §5）。

---

## 4. 修复路径（三方向，可叠加）

### 方向 A：install_repo 加 cleanup phase（推荐）

**作用范围**：在 `install_repo` 现有 cleanup 链上扩两类清理动作：

1. **layout 残留扫描**（A1）：检测并归档 `.workflow/flow/artifacts-layout.md` 等已废弃契约文件（白名单驱动，与 `LEGACY_CLEANUP_TARGETS` 同机制）。
2. **`.bak` 残留清理**（A2）：扫描 `.workflow/state/requirements/*.yaml.bak`，若同名 `.yaml` 存在且新 schema 字段完整，则归档 `.bak` 到 `legacy-cleanup/state-bak/`（保留可回溯，与 cleanup 既有归档语义一致）；若 `.yaml` 不存在则保留 `.bak` 并 stderr 告警（用户手工恢复）。
3. **schema 探测扩 folder 形态**（A3）：`_migrate_state_files` 增加分支：扫 `requirements/req-XX/`（folder 无 `.yaml`），按 legacy 路径标准识别为 req-id ≤ 38 历史目录；不修改、不迁移（历史豁免规则），但 stdout 列入 "schema legacy" 报告，避免 audit 误报。

- **改动量**：中。`workflow_helpers.py` 扩 `LEGACY_CLEANUP_TARGETS` + 写新 helper `cleanup_state_bak_files` + `_migrate_state_files` 加 folder-skip 分支；pytest 加 fixture 覆盖。
- **可逆性**：高（cleanup 走 backup 归档，与现有机制一致；无破坏性 mv / rm）。
- **推荐度**：★★★★★（聚焦 install_repo 闭环缺口，与现有架构无冲突，PetMallPlatform 跑一次即可见效）。

### 方向 B：install_repo 加 audit phase（不修复，只报告）

**作用范围**：install 末尾跑一次只读扫描，输出 "残留检测报告"：列出 `artifacts-layout.md` / `*.bak` / folder schema / 多 branch 形态等异常，**不动文件**，由用户手工清理。

- **改动量**：小。新写 `_audit_install_residuals` helper + stdout 渲染。
- **可逆性**：极高（只读）。
- **推荐度**：★★★（安全但需人工介入，存量项目随时间膨胀脏数据；适合作 A 的 fallback 或预热）。

### 方向 C：schema 全静默迁移

**作用范围**：install 自动 `git mv` / `git rm` 完整迁移到最新 layout（删 `artifacts-layout.md`、清 `.bak`、folder→yaml 强转）。

- **改动量**：大。需写完整 schema graph 推断 + git 操作 + 失败回滚。
- **可逆性**：低（git mv / rm 风险大，可能误删用户文件；harness 项目本身不持有用户业务数据，但 schema 推断错误的影响是用户 req 历史不可读）。
- **推荐度**：★（违反硬门禁四例外条款 (i) "数据丢失风险"，需用户每个 case 显式确认；不适合 install 自动跑）。

---

## 5. 路由建议

### 5.1 真实问题 → 走 executing 修 install_repo（**不**转 req）

理由：
- 问题已聚焦在 `install_repo` 函数级别的 cleanup 闭环缺口；
- 不涉及契约重写或新 layout 设计，无需 requirement_review / planning 反复迭代；
- bugfix sequence（regression → executing → testing → acceptance → done）足够承载。

### 5.2 chg 拆分（推荐 4 chg DAG）

| chg | 标题（≤ 15 字描述） | 改动量 | 可逆性 | 范围 |
|-----|--------------------|-------|-------|------|
| **chg-1** | install_repo cleanup 扩 layout 残留 | 中 | 高 | `LEGACY_CLEANUP_TARGETS` 加 `flow/artifacts-layout.md` 等 req-39 → req-41 演进残留；`cleanup_legacy_workflow_artifacts` 自动归档 |
| **chg-2** | state .bak 残留清理 helper | 小 | 高 | 新 helper `cleanup_state_bak_files`：扫 `state/requirements/*.yaml.bak` + `runtime.yaml.bak`，归档到 `legacy-cleanup/state-bak/` |
| **chg-3** | schema 探测扩 folder 形态 + audit 报告 | 小 | 极高 | `_migrate_state_files` 加 folder-skip 分支 + stdout 列 legacy folder 清单（不迁移） |
| **chg-4** | pytest fixture + PetMallPlatform 跑一次活证 | 小 | 极高 | tests/test_install_cleanup.py 加 fixture（双 layout / .bak / req-XX folder）；手动跑 `harness install` 在 PetMallPlatform 验证清理生效 |

**DAG**：chg-1（layout 残留）/ chg-2（.bak 清理）→ chg-3（探测扩展）→ chg-4（活证）；chg-1 / chg-2 互不依赖可并行。

### 5.3 不在本 bugfix 范围（spawn 独立工作项）

- **branch 命名规约**：建议另起 sug 或 req-NN，扩展 `repository-layout.md` 加 §branch 命名规约段（推荐形态 / git 分支 vs release 版本 / merged 归档命名 / cleanup 不介入声明）。本 bugfix 不动 branch 层。
- **req-39 → req-41 演进残留的全量盘点**：本 bugfix 只覆盖 `artifacts-layout.md`；如有更多 req-39 → req-41 演进期文件（agent 过程文档迁路径残留等），由 chg-3 audit 报告产出后另起 sug。

---

## 6. Required Inputs（无）

- 本 bugfix 不需要用户额外输入；PetMallPlatform 现场已提供完整证据链；executing 阶段按 chg-1~4 即可推进。

---

## 7. 路由决定

- [x] **真实问题（部分真实）→ proceed to fix**
- [ ] False positive
- 路由方向：**executing**（修 install_repo / cleanup helper），不转 requirement_review。
- 推荐 chg DAG：chg-1（layout 残留）+ chg-2（.bak 清理）+ chg-3（探测扩展）+ chg-4（活证），4 chg 顺序见 §5.2。
