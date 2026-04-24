# Requirement

## 1. Title

对人文档家族契约化 + artifacts 扁平化

## 2. Goal

把"对人文档必须产出"从**规约文字级自述**升级为**命令级执行兜底**，并把 `artifacts/` 仓库语义从"混装制品树"重定义为"**对人文档仓库 + 按需求扁平组织**"。

> **溯源问题现场**：req-38（api-document-upload 工具闭环：触发门禁 + MCP pre-check 协议 + 存量项目同步）走完 requirement_review + planning 两阶段后，到 acceptance 才被 `harness validate --human-docs` 发现：缺 1 份 `需求摘要.md`（req 级）+ 6 份 `变更简报.md`（chg-01（protocols 目录扩展）/ chg-02（触发门禁 lint）/ chg-03（runtime pending + gate）/ chg-04（mcp_project_ids 多 provider）/ chg-05（存量同步 + 契约合规）/ chg-06（硬门禁六 + 契约 7 补丁）各 1）。reg-02（对人文档家族缺失 + artifacts 扁平化重构）诊断确认：`stage-role.md` 契约 4 硬门禁**两次**未拦截，根因是"退出条件只有自述、没有命令级自检闭环"；同时用户在反馈中叠加新架构方向："制品仓库里只放对人文档，文件夹按照需求分就行了不用子文件夹，sql、部署文档等需要人执行和看的都是对人文档"。

三线合一修复（缺一不可）：

- **契约加固（根因治本）**：`requirement-review.md` / `planning.md` 退出条件加"命令级自检硬门禁"（subagent 交接前必须跑 `harness validate --human-docs` 且全绿，未绿 ABORT）；`.workflow/evaluation/acceptance.md` 的 gate 条款从"文档约束"升级为"代码阻塞 + 非零退出码"；`validate_human_docs.py` 同步 req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界））/ chg-04（S-D 对人文档缩减）精简，移除 `测试结论.md` / `验收摘要.md` 扫描噪音。
- **架构重构（新规落地）**：新建 `.workflow/flow/artifacts-layout.md` 定义扁平结构 + 对人文档白名单（需求摘要 / 变更简报 / 实施说明 / 回归简报 / 交付总结 / 决策汇总 / sql 脚本 / 部署文档 / 接入配置说明 / runbook 等）；机器型文档（requirement.md / change.md / plan.md / testing-report.md / acceptance-report.md / session-memory.md / regression/{analysis,decision}.md 等）迁离到 `.workflow/state/requirements/{req-id}/` + `.workflow/state/sessions/{req-id}/{chg-id or stage}/`；CLI 同步。
- **当次追补（活证试点）**：按新扁平结构直接补齐 req-38 的 7 份对人文档，作为新规落地的第一份试点 + 契约加固的自证样本；不迁移 req-02（湖南 UAV MQTT 接入）~ req-37（阶段结束汇报简化：周转时不给选项，只停下 + 报本阶段结束 + 报状态）历史 artifacts（git log 自带分水岭）。

## 3. Scope

本需求三合一 scope，**缺一即不完整**。

### Scope-A：对人文档契约加固

- `requirement-review.md` / `planning.md` 退出条件加"subagent 交接前必须执行 `harness validate --human-docs`（或等价 `harness status --lint`）且全绿"硬门禁，未绿立即 ABORT + session-memory.md 留痕，不得主 agent 自主放行。
- `.workflow/evaluation/acceptance.md` 的 "调用 `harness validate --human-docs`"（当前为文档约束）升级为 acceptance subagent 在 AC 签字前**必须**跑 lint，未绿则 FAIL 不通过、退回 planning 或 executing 补写。
- `src/harness_workflow/validate_human_docs.py` 精简：移除 `测试结论.md` / `验收摘要.md` 扫描项（req-31 / chg-04 已豁免）；`HUMAN_DOC_CONTRACT` / `REQ_LEVEL_DOCS` / `CHANGE_LEVEL_DOCS` 逻辑重写为新扁平结构；pytest 覆盖。
- 各角色 role.md 的"对人文档输出"段路径模板同步新扁平结构；`stage-role.md` 契约 2（路径同构）+ 契约 3（中文命名表）改写或新增引用 `.workflow/flow/artifacts-layout.md`。

### Scope-B：artifacts 扁平化 + 白名单扩展

- 新建 `.workflow/flow/artifacts-layout.md`，定义：
  - `artifacts/{branch}/requirements/{req-id}-{slug}/` **扁平语义**（只装对人文档，不出现 `changes/` / `regressions/` 子目录）；
  - 对人文档**白名单**：`需求摘要.md / 变更简报.md / 实施说明.md / 回归简报.md / 交付总结.md / 决策汇总.md / *.sql / 部署文档.md / 接入配置说明.md / runbook-*.md` 等（列至少 8 类，planning 可扩）；
  - 变更级对人文档命名前缀约定：`chg-NN-变更简报.md` / `chg-NN-实施说明.md` / `reg-NN-回归简报.md`，保留 chg-id / reg-id 前缀避免同名冲突；
  - 机器型文档**迁移目标位**：
    - req 级：`.workflow/state/requirements/{req-id}/{requirement,testing-report,acceptance-report}.md`；
    - chg 级：`.workflow/state/sessions/{req-id}/{chg-id}/{change,plan}.md`；
    - stage / session 级：`.workflow/state/sessions/{req-id}/{stage or chg-id}/{session-memory.md, regression/{analysis,decision,regression,meta.yaml}}`。
- CLI 行为对齐：`harness requirement` / `harness change` / `harness regression` 新建时**直接**落扁平路径 + 机器型文档落 state；`src/harness_workflow/workflow_helpers.py::create_change` / `create_regression` / `archive_requirement` 路径硬编码清理；pytest 覆盖。
- `src/harness_workflow/assets/scaffold_v2/.workflow/flow/artifacts-layout.md` 同步 mirror；角色契约文件（`requirement-review.md` / `planning.md` / `acceptance.md` / `stage-role.md`）改动同步 mirror。

### Scope-C：req-38 对人文档按新结构追补（试点活证）

- 按 Scope-B 的新扁平结构，在 `artifacts/main/requirements/req-38-api-document-upload-工具闭环-触发门禁-mcp-pre-check-协议-存量项目同步/` 下直接补齐：
  - 1 × `需求摘要.md`（req 级，摘 req-38 的 Goal / Scope / AC）；
  - 6 × `chg-NN-变更简报.md`（chg-01（protocols 目录扩展）/ chg-02（触发门禁 lint）/ chg-03（runtime pending + gate）/ chg-04（mcp_project_ids 多 provider）/ chg-05（存量同步 + 契约合规）/ chg-06（硬门禁六 + 契约 7 补丁） 各 1 份）。
- **不迁移** req-38 已有的 `changes/chg-NN/` 子目录下历史产物（那批按旧规产出，原地留档；新对人文档按新规平铺在上层）。
- **不迁移** req-02（湖南 UAV MQTT 接入）~ req-37（阶段结束汇报简化：周转时不给选项，只停下 + 报本阶段结束 + 报状态）的历史 artifacts，git log 自带分水岭。

### Excluded（明确不做）

- 不改 req-02 ~ req-37 历史 artifacts 结构；不补历史缺失对人文档。
- 不改 req-38 acceptance-report / testing-report / 6 份 `change.md` / 6 份 `plan.md` 等机器型文档的当前内容；若本 req 机器型文档迁移策略要求搬离，仅**搬**不**改**。
- 不改 `assets/scaffold_v2/` 以外的其他 mirror（本仓库仅此一处 scaffold mirror）。
- 不在本 req 内回补 req-38 的 acceptance 签字 —— req-38 acceptance 解锁作为 TODO 留给本 req 完成后手动回归（见 session-memory TODO）。

## 4. Acceptance Criteria

> **planning-ready 量化版**：AC-1~12 每条给出可 grep / 可 pytest / 可文件路径比对 / 可 CLI 退出码的判定条款，让 planning 可直接拆 chg。

### AC-1（artifacts 扁平结构落位，依赖 AC-2）

- **验证动作**：对**新创建**的 req（本 req-39 自身 + req-40+ 未来）执行 `find artifacts/main/requirements/{req-id}-{slug}/ -type d -name "changes" -o -name "regressions"`，命中行数 = 0（除 req-02 ~ req-38 历史存量目录）。
- **量化判据**：`artifacts/main/requirements/req-39-对人文档家族契约化-artifacts-扁平化/` 下仅含平铺 `.md` + `.sql` 等白名单后缀文件，无子目录。
- **契约 7 合规**：本 AC 扫描脚本自身若引用 id 需带 title。

### AC-2（对人文档白名单 + layout 契约落位）

- **验证动作**：
  - `test -f .workflow/flow/artifacts-layout.md` → 退出码 0；
  - `grep -c "^## " .workflow/flow/artifacts-layout.md` ≥ 5（对应 5 节：`## 1. 扁平结构定义` / `## 2. 对人文档白名单` / `## 3. 机器型文档迁移位` / `## 4. 命名前缀约定` / `## 5. 历史存量豁免`）；
  - `grep -E "需求摘要|变更简报|实施说明|回归简报|交付总结|决策汇总|sql|部署文档|接入配置说明|runbook" .workflow/flow/artifacts-layout.md` 命中 ≥ 8 行（白名单至少 8 类）。
- **scaffold_v2 mirror**：`src/harness_workflow/assets/scaffold_v2/.workflow/flow/artifacts-layout.md` 同步存在，`diff` live 与 mirror 为空（硬门禁五）。

### AC-3（requirement-review 自检硬门禁代码化）

- **验证动作**：
  - `grep -nE "harness validate --human-docs|harness status --lint" .workflow/context/roles/requirement-review.md` 命中 ≥ 1 行（退出条件段）；
  - `requirement-review.md` 退出条件第 N 条新增（或改写）："subagent 交接前必须执行 `harness validate --human-docs`，未绿 ABORT 并留痕 session-memory.md"；
  - pytest 新增用例 `test_requirement_review_exit_requires_human_docs_lint`，模拟缺 `需求摘要.md` 场景时 stage subagent 的退出路径被阻塞。
- **scaffold_v2 mirror**：`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/requirement-review.md` 同步。

### AC-4（planning 自检硬门禁代码化）

- **验证动作**：
  - `grep -nE "harness validate --human-docs|每 chg 一份 变更简报" .workflow/context/roles/planning.md` 命中 ≥ 1 行；
  - planning 退出条件新增"每 chg 一份 `chg-NN-变更简报.md` + subagent 交接前 `harness validate --human-docs` 全绿"硬门禁；
  - pytest 新增用例 `test_planning_exit_requires_per_chg_brief_lint`。
- **scaffold_v2 mirror**：`planning.md` mirror 同步。

### AC-5（acceptance gate 强执行，依赖 AC-3 + AC-4）

- **验证动作**：`.workflow/evaluation/acceptance.md` "调用 `harness validate --human-docs`" 条款改写为命令级强执行描述（非仅"应调用"）；acceptance subagent 行为上若 lint 未绿，汇报字段 2 状态**必须**为 FAIL；不得 PASS 放行。
- **量化判据**：
  - `grep -nE "必须执行|未绿 ABORT|非零退出码" .workflow/evaluation/acceptance.md` 命中 ≥ 1 行；
  - pytest 新增用例 `test_acceptance_gate_fails_on_missing_human_docs`，模拟缺 `需求摘要.md` 时 acceptance 流程拒 PASS。
- **scaffold_v2 mirror**：`assets/scaffold_v2/.workflow/evaluation/acceptance.md` 同步（若 scaffold 有镜像；无则 skip，planning 阶段查证）。

### AC-6（validate_human_docs.py 重写 + 精简，依赖 AC-2）

- **验证动作**：
  - `src/harness_workflow/validate_human_docs.py` 的 `REQ_LEVEL_DOCS` / `CHANGE_LEVEL_DOCS` 常量**不再**含 `测试结论.md` / `验收摘要.md`（req-31 / chg-04 废止项，见 `analysis.md` §2.2 层 2）；
  - 扫描逻辑支持新扁平路径（req 级扫 `artifacts/{branch}/requirements/{req-id}-{slug}/{需求摘要,交付总结,决策汇总}.md` + chg 级扫 `{req-id}-{slug}/chg-NN-{变更简报,实施说明}.md` + reg 级扫 `{req-id}-{slug}/reg-NN-回归简报.md`）；
  - `harness validate --human-docs` 在新结构下对 req-39 自身扫描输出 `Summary: N/N present, 0 pending/invalid.`（具体 N 以 planning 落地为准）。
- **量化判据**：
  - `pytest tests/test_validate_human_docs.py` 通过率 100%，新增用例 ≥ 4 条（覆盖新扁平路径 + 精简项 + ABORT 退出码 + 历史存量豁免）；
  - `grep -cn "测试结论\|验收摘要" src/harness_workflow/validate_human_docs.py` = 0。

### AC-7（机器型文档迁离 artifacts 树，依赖 AC-1 + AC-2）

- **验证动作**：
  - 对**新创建**的 req（req-39 + req-40+），`find artifacts/main/requirements/{req-id}-{slug}/ -name "requirement.md" -o -name "change.md" -o -name "plan.md" -o -name "testing-report.md" -o -name "acceptance-report.md" -o -name "session-memory.md" -o -name "meta.yaml"` 命中行数 = 0；
  - 对应机器型文档存在于：
    - `.workflow/state/requirements/{req-id}/` 下 `requirement.md` / `testing-report.md` / `acceptance-report.md`；
    - `.workflow/state/sessions/{req-id}/{chg-id}/` 下 `change.md` / `plan.md`；
    - `.workflow/state/sessions/{req-id}/{stage or chg-id}/` 下 `session-memory.md`；
    - `.workflow/state/sessions/{req-id}/regressions/{reg-id}/` 下 `regression.md` / `analysis.md` / `decision.md` / `meta.yaml`。
- **量化判据**：`pytest tests/test_create_change.py` / `test_create_regression.py` / `test_archive_requirement.py` 新增或改写用例 ≥ 6 条，断言新路径存在 + 旧路径不存在（对新 req）。

### AC-8（CLI 行为对齐新结构，依赖 AC-1 + AC-7）

- **验证动作**：
  - `harness requirement "<title>"` 创建 req 时：对人文档 placeholder 落 `artifacts/main/requirements/{req-id}-{slug}/需求摘要.md`（若 CLI 本身写占位）+ 机器型 `requirement.md` 落 `.workflow/state/requirements/{req-id}/requirement.md`；
  - `harness change "<title>"` 创建 chg 时：机器型 `change.md` + `plan.md` 落 `.workflow/state/sessions/{req-id}/{chg-id}/`；对人文档 placeholder（若有）落扁平 `artifacts/.../chg-NN-变更简报.md`；
  - `harness regression "<issue>"` 创建 reg 时：机器型 `regression.md` + `analysis.md` + `decision.md` + `meta.yaml` 落 `.workflow/state/sessions/{req-id}/regressions/{reg-id}/`；对人文档 `reg-NN-回归简报.md` 落扁平 `artifacts/.../`。
- **量化判据**：`src/harness_workflow/workflow_helpers.py` 的 `create_change` / `create_regression` / `archive_requirement` 函数 diff 命中路径硬编码清理 ≥ 6 处；pytest 新增 / 改写用例 ≥ 8 条全过。

### AC-9（req-38 试点追补，依赖 AC-1 + AC-2）

- **验证动作**：
  - `ls artifacts/main/requirements/req-38-api-document-upload-工具闭环-触发门禁-mcp-pre-check-协议-存量项目同步/*.md | wc -l` ≥ 8（`需求摘要.md` + `chg-01-变更简报.md` + `chg-02-变更简报.md` + `chg-03-变更简报.md` + `chg-04-变更简报.md` + `chg-05-变更简报.md` + `chg-06-变更简报.md` + 既有 `requirement.md` 等）；
  - `grep -l "变更简报" artifacts/main/requirements/req-38-.../*.md` 命中 ≥ 6 个文件；
  - 每份变更简报 ≤ 1 页（按显示行数 ≤ 80 行近似）、字段顺序按 `planning.md` 最小模板。
- **量化判据**：`harness validate --human-docs` 对 req-38 扁平目录扫描输出 `Summary: ≥7/7 present, 0 pending/invalid.`（具体条目数以 req-38 对人文档家族完整度为准）；**契约 7 / 硬门禁六合规**：每份变更简报首次引用 id 带 title 或 ≤ 15 字描述，lint 命中 0。

### AC-10（历史存量不迁移）

- **验证动作**：
  - `git log --name-status --diff-filter=D -- 'artifacts/main/requirements/req-0[2-9]*' 'artifacts/main/requirements/req-1[0-9]*' 'artifacts/main/requirements/req-2[0-9]*' 'artifacts/main/requirements/req-3[0-7]*'` 在本 req 的合并 commit 中输出行数 = 0（即无删除 / 移动）；
  - `diff -rq artifacts/main/requirements/req-37-阶段结束汇报简化-周转时不给选项-只停下-报本阶段结束-报状态/ <切换前快照>/`（抽样 1 个）无差异；
  - 对 req-02 ~ req-37 的 artifacts 结构扫描，`changes/` 子目录仍存在（允许保留）。
- **量化判据**：本 req 落地后 git diff 不含 `artifacts/main/requirements/req-0[2-9]*` / `req-1[0-9]*` / `req-2[0-9]*` / `req-3[0-7]*` 路径的重命名 / 删除。

### AC-11（契约 7 + 硬门禁六自证，横跨全需求）

- **验证动作**：`harness validate --contract all` 扫 `artifacts/main/requirements/req-39-对人文档家族契约化-artifacts-扁平化/` 下所有 `.md` + `.workflow/state/sessions/req-39/` 下所有 session 段，首次引用 `req-38` / `req-31` / `chg-04` / `reg-02` / `chg-NN` 等时均带完整 title 或 ≤ 15 字简短描述（base-role 硬门禁六 + 契约 7 批量列举子条款），退出码 0。
- **量化判据**：扫描脚本命中裸 id 的行数 = 0（不含历史归档目录）。

### AC-12（scaffold_v2 mirror 同步，跨越 AC-2 / AC-3 / AC-4 / AC-5 / AC-8）

- **验证动作**：
  - `diff -rq .workflow/flow/artifacts-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/artifacts-layout.md` 退出码 0；
  - `diff -rq .workflow/context/roles/requirement-review.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/requirement-review.md` 退出码 0；
  - `diff -rq .workflow/context/roles/planning.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/planning.md` 退出码 0；
  - `diff -rq .workflow/context/roles/stage-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md` 退出码 0（若契约 2 / 3 改动）；
  - `diff -rq .workflow/evaluation/acceptance.md src/harness_workflow/assets/scaffold_v2/.workflow/evaluation/acceptance.md` 退出码 0（若 scaffold 有该文件）。
- **量化判据**：`validate_human_docs.py` 属 Python 源码**不需** mirror（sys.path 下由 installed pkg 统一加载）；跨 mirror 文件 diff 命中数 = 0。

## 5. Split Rules

- Split the requirement into independently deliverable changes
- Each change should cover one clear unit of delivery
- When the requirement is complete, fill `completion.md` and record successful project startup validation

**planning-ready 拆分建议**（候选 chg-a ~ chg-f，planning 可合并 / 再切分；溯源 `regressions/reg-02-对人文档家族缺失-artifacts-扁平化重构/decision.md §3.1`）：

- **chg-a 候选（artifacts-layout 契约新建 + stage-role 契约 2/3 改写）** → 覆盖 AC-1 / AC-2 / AC-7
  新建 `.workflow/flow/artifacts-layout.md`；`stage-role.md` 契约 2（路径同构）+ 契约 3（中文命名表）改写或加引用段；scaffold_v2 mirror 同步。
- **chg-b 候选（validate_human_docs 重写 + 精简）** → 覆盖 AC-5 / AC-6
  `src/harness_workflow/validate_human_docs.py` 逻辑重写支持新扁平路径 + 删 `测试结论.md` / `验收摘要.md` 扫描项；pytest ≥ 4 条。
- **chg-c 候选（requirement-review / planning 自检硬门禁代码化）** → 覆盖 AC-3 / AC-4
  `requirement-review.md` + `planning.md` 退出条件段加"subagent 交接前必须 `harness validate --human-docs` 全绿，未绿 ABORT"；scaffold_v2 mirror 同步；pytest ≥ 2 条。
- **chg-d 候选（acceptance gate 强执行）** → 覆盖 AC-5（强化）
  `.workflow/evaluation/acceptance.md` gate 条款从"应调用"升级为"必须执行 + 未绿 FAIL"；pytest ≥ 1 条；若 scaffold 有镜像则同步。
- **chg-e 候选（CLI 行为对齐新结构 + scaffold_v2 mirror 全量同步）** → 覆盖 AC-8 / AC-12
  `workflow_helpers.py::create_change` / `create_regression` / `archive_requirement` 路径硬编码清理；`ff_auto.py` / `decision_log.py` 若命中亦同步；pytest ≥ 8 条；scaffold_v2 mirror 跨文件 diff 归零。
- **chg-f 候选（req-38 对人文档按新扁平结构追补，试点活证）** → 覆盖 AC-9
  按新扁平结构在 `artifacts/main/requirements/req-38-.../` 下直接产出 `需求摘要.md` + `chg-01-变更简报.md` ~ `chg-06-变更简报.md` 共 7 份；不迁 req-38 既有 `changes/chg-NN/` 子目录历史产物。

**DAG 依赖**（强弱序）：

```
chg-a（契约底座）
  ├── chg-b（lint 重写，读 layout 定义）
  ├── chg-c（角色退出条件，读 layout 路径）
  ├── chg-d（acceptance gate，读 lint 行为）
  └── chg-e（CLI 行为，读 layout 路径）
        │
        └── chg-f（试点追补，依赖全部前置契约 + CLI 行为就绪）
```

- chg-a 先行（契约底座）；
- chg-b / chg-c / chg-d / chg-e 读 chg-a 产出，**可并行**（但 chg-d 语义依赖 chg-b 的 lint 行为，串行次之）；
- chg-f 最后（试点 = 活证 = 本 req 契约自证）。

> 以上为候选粒度，planning 角色可合并（如 chg-c + chg-d 合为"退出条件 + gate 代码化"单 chg）/ 再切分（如 chg-e 拆出 scaffold mirror 同步为独立 chg）/ 重排序。
