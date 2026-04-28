# Regression Stage Experience

## 经验一：requirement_review 阶段的 regression 通常是需求范围遗漏

### 场景

在需求评审阶段（requirement_review），用户提出"好像有问题"类的反馈，触发 harness regression。

### 经验内容

需求评审阶段尚无实现，不存在"代码 bug"或"测试失败"。此阶段触发的 regression 绝大多数情况是：

1. **需求范围遗漏**：用户发现某个问题点未被纳入需求文档
2. **分析误判**：分析者对现有结构的描述有误，用户来纠正

诊断流程应以"是否真实存在实现/结构问题"为核心，而非走完整的 regression 流程。通常结论是 `--reject`（误判），然后更新 requirement.md。

### 反例

将 requirement_review 阶段的用户纠正当成真实 regression 处理，创建完整的 diagnosis 流程，反而拖慢了需求确认节奏。

### 来源

req-02 / requirement_review 阶段两轮 regression

---

## 经验二：用户说"多了/少了"时，先确认语义

### 场景

用户说某个目录"多了"（extra）或内容不对，可能有两种完全相反的含义：

- A. 这个目录不该存在（真正多余）
- B. 这个目录存在是对的，但它的**内容缺失**导致它看起来没价值

### 经验内容

收到"多了 X 目录/层"类反馈时，诊断第一步不是"判断该目录是否合理"，而是：

1. 查看该目录的实际内容（是否为空/占位符）
2. 查看旧版本/备份中是否有对应的内容
3. 对比新旧结构，判断是"目录多余"还是"内容迁移遗漏"

两种情况处理方向完全相反：
- 目录多余 → 迁移/删除/合并
- 内容迁移遗漏 → 恢复内容

### 反例

本次 req-02 中，看到 `context/experience/tool/harness.md` 是空占位符，就得出"tool/ 层价值存疑"的结论。实际上是旧系统的 `tools/` 整层（含 catalog、stage-tools、selection-guide）在迁移中丢失，`context/experience/tool/` 本身位置是正确的。

### 来源

req-02 regression 第二轮，用户纠正："你对 context/experience/tool/ 价值存疑是因为在 workflow 下丢失了 tools 工具层"

---

## 经验三：结构性评估要区分"职责语义"与"内容存在"

### 场景

对 .workflow/ 目录结构进行合理性评估时。

### 经验内容

目录评估需同时检查两个维度：

| 维度 | 问题 | 诊断方式 |
|------|------|---------|
| 职责语义 | 这个目录放在这里合不合理？ | 对比设计理念（知识层/状态层/工具层） |
| 内容存在 | 这个目录有没有实际内容？ | 检查文件是否为空/占位符，对比旧版本 |

一个目录可以：
- 语义正确 + 内容完整（正常）
- 语义正确 + 内容缺失（迁移遗漏，需补充内容）
- 语义错误 + 内容存在（需迁移/重组）
- 语义错误 + 内容缺失（需删除）

不能因为内容缺失就判定语义错误。

### 来源

req-02 结构性评估过程

---

## 经验四：backup 目录是诊断的重要证据源

### 场景

判断当前结构是否有迁移遗漏时。

### 经验内容

`.workflow/context/backup/` 中保存了旧系统完整结构。在进行结构合理性评估时：

1. **先读 backup 中对应目录的结构**，了解旧系统该模块包含什么
2. 与当前 `.workflow/` 结构对比
3. 差异项 = 迁移遗漏候选

backup 是诊断"迁移遗漏"类问题的第一手证据，不要跳过。

### 反例

在评估 `context/experience/tool/` 时，没有先查 backup 中的对应目录（`workflow/tools/` 和 `workflow/context/experience/tool/`），导致错误判断该层"价值存疑"。

### 来源

req-02 regression 根因分析

---

## 经验五：bugfix 模式下 regression 是流程入口

### 场景

使用 `harness bugfix "<issue>"` 创建的快速修复流程。

### 经验内容

bugfix 模式采用四阶段快速流转：`regression → executing → testing → acceptance → done`。此时 `regression` 不仅是问题诊断，更是流程入口，承担以下职责：

1. **确认问题真实性**：判断该 issue 是否为真实 bug，而非配置/环境问题
2. **锁定最小修复范围**：在 `bugfix.md` 中明确根因、修复方案、验证标准
3. **跳过 planning**：`technical-director` 在识别到 `current_requirement` 以 `bugfix-` 开头时，不加载 `planning` 角色

诊断完成后，直接 `harness next` 进入 `executing` 开始修复。不要为 bugfix 创建额外的 `plan.md` 或变更拆分。

### 反例

在 bugfix 模式下仍尝试走标准需求的六阶段流（requirement_review → changes_review → planning），导致流程冗余、角色文件缺失报错。

### 来源

req-23 bugfix 快速修复与验证端到端测试

---

## 经验六：regression 命令的 --confirm 会消费 regression，导致 --testing 无法使用

### 场景

req-25 验收阶段发现 core.py 尚未删除，需要通过 regression 回滚到 testing 继续修复。

### 经验内容

执行 `harness regression "<title>" && harness regression --confirm && harness regression --testing` 时：
- `--confirm` 会将 regression 状态从 `analysis` 改为 `confirmed`，并清空 `current_regression`
- 导致 `--testing` 找不到活跃的 regression，报 "No active regression"

**原因**：`--confirm` 在执行后立即消费了 regression，而非等待 `--testing` 使用。

** workaround**：分步执行，每次创建新的 regression。

**建议**：修复 harness regression 的状态管理逻辑，支持 `--confirm --testing` 组合，或在 `--confirm` 时检查是否有 `--testing` 标志。

### 状态

req-26 / chg-01 已修复（AC-01）：`--confirm` 只做"确认问题真实"一步，
`runtime.current_regression` 保留，`regression/meta.yaml` 的 `status` 被更新为
`confirmed`；后续 `--testing` / `--change` / `--requirement` 仍能正常消费 regression。

### 来源

req-25 验收阶段多次尝试回滚 testing 失败；req-26 / chg-01 修复

---

## 经验七：regression 产出目录必须 kebab-case 且以 reg-NN- 前缀开头

### 场景

`harness regression "<issue>"` 创建 regression 工作区时的目录命名约定。

### 经验内容

产出目录 **一定** 满足：

1. 以 `reg-NN-` 前缀开头，NN 在当前 `regressions_base` 内顺序递增（01、02…），
   与 `runtime.current_regression` 写入的纯 id 一致，便于 `--confirm` / `--testing`
   按 id 前缀反查目录。
2. 非 id 部分使用 `slugify_preserve_unicode`：
   - 英文小写化，空格 / 标点折叠为 `-`；
   - 中文等非 ASCII 字母保留原字符（不拼音化，与仓库既有 `req-26-uav-split`
     / `bugfix-3-...` 的中英文混合命名惯例一致）；
   - 非法路径字符（`/`、`\`、`:`、`？`、`*` 等）一律剔除；
3. 不得出现裸空格、全角冒号、`regression xxx/` 这类不带前缀的目录名。

### 反例

- `regressions/issue with spaces/` ❌（含空格、无前缀）
- `regressions/req-25-6-p0/` ❌（id 命名走错位：req 前缀被复用成 regression 目录名）
- `regressions/reg-01-issue-with-spaces/` ✅

### 来源

req-25 P1-new-03 遗留；req-26 / chg-01 修复（AC-04）

---

## 经验八：契约层 vs 实现层失配诊断模板

### 场景

主 agent 在某 stage 流转点输出契约明文禁止的话术（如"是否进入 planning"），或 acceptance verdict 已定路由后仍向用户暴露"是否进 done"决策点；用户反馈后触发 regression。

### 经验内容

**症状识别**：契约文档（role md / Director md / harness-manager md / stage-role.md）有明文规约（如"默认静默自动推进 / verdict 已定路由 / 同角色 stage 不暴露决策点"），但实际行为仍向用户暴露决策点。

**诊断三步**：

1. **L1 表象**：定位话术违反契约的具体位置（哪个 stage 流转点、哪段输出、grep 行号）。
2. **L2 中层**：grep 实现层是否有对应代码 / lint 强制——若无，说明契约只在自然语言层面存在；查 `workflow_helpers.py::workflow_next` 是否 `idx + 1` 直推无策略；查 `harness validate` 是否有对应 lint 规则。
3. **L3 一句根本**：契约的"权威源"挂在哪？若三处文档分散记录、CLI 无法读、reviewer 无法 lint，则**单一权威源缺失**就是根本根因。

**修复模式**：

- 在 `role-model-map.yaml` 等 SSOT yaml 加结构化字段（如 `stages: [...]` / `stage_policies: {...}`），文档侧三处镜像但标注"以 yaml 为准"；
- CLI（workflow_next）从 SSOT 读 → 自动行为；harness validate 加话术 lint 规则双门禁；
- reviewer.md checklist 加"三处镜像 + lint 抽样"两条检查项；
- scaffold_v2 mirror 同步硬门禁五一并扫描。

**充分非必要警示**：诊断初次产出方案时，警惕"覆盖典型样本但漏边界"——本次 bugfix-5 一次诊断的"同角色跨 stage"只是"无用户决策点"的**充分条件**之一，acceptance → done（不同角色但 verdict 已定路由）属漏覆盖；应主动穷举"同/不同角色 × 有/无用户决策"四象限矩阵，避免 scope 二次扩展。

### 反例

bugfix-5（同角色跨 stage 自动续跑硬门禁）一次诊断只覆盖"同角色"特例，acceptance PASS-with-followup 后用户反馈 acceptance → done 也应自动跳，触发 regression 二次进入 + 修复点 6 追加。若初次诊断穷举四象限矩阵，可一次闭环。

### 来源

bugfix-5（同角色跨 stage 自动续跑硬门禁） regression 一次 + 二次（scope 扩展）

---

## 经验九：bugfix 模式中 diagnosis.md 担纲 planning 等价职责的边界（bugfix-6 引入，事项 C）

### 场景

bugfix 流程跳过 requirement_review + planning 直接走 regression → executing → testing → acceptance → done（见经验五）。bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） 事项 B 把"测试用例设计"权责前移到 planning 后，bugfix 流程出现"无 planning 即无测试设计载体"的契约空洞。

### 经验内容

**default-pick 模式（bugfix-6 D-B1 落地）**：bugfix 流程的 **regression 阶段** 担纲 planning 等价职责——`regression/diagnosis.md` 在 §修复方案末尾**新增 §测试用例设计** 章节（结构同 plan.md §测试用例设计），testing 直接消费。

**职责边界（regression.md Step 4.5）**：

1. **bugfix 模式必填**：bugfix 流程 regression subagent 在 Step 4「产出诊断文档」与 Step 5「交接」之间，必须完成 §测试用例设计 段（`regression_scope` + 波及接口清单 + 用例表）；
2. **req 模式跳过**：req 流程 regression（如 acceptance FAIL → regression 重新触发）跳过 Step 4.5——plan.md 已由 analyst 产出，不重复；
3. **不跨职**：regression 不应改业务代码（即使是 lint 命中的违规也只在 diagnosis 中标注"活体证据"，留给 executing 修复）；测试用例设计是诊断 + 修复方案的自然延伸，不算跨职。

**与"诊断不修复"硬门禁的关系**：

- §测试用例设计 是**对修复方案的可验证性表达**，不是"在诊断阶段写代码"；属诊断 + 修复方案产出的形式化延伸，与"诊断不修复"硬门禁兼容。
- bugfix 自身是"测试契约重塑"主体（dogfood 边界）时，regression 完成时刻 §测试用例设计 段可能不存在（旧契约空缺），由 executing 后补加 + testing 走 dogfood fallback 路径（详见 testing.md 经验"dogfood fallback 处理"）。

### 反例

- bugfix 流程 regression 跳过 Step 4.5 → testing subagent 无设计单可读，回退到独立设计 → 与事项 B 契约打架（B2 testing.md Step 2"读取 plan.md / diagnosis.md §测试用例设计"语义被破坏）。
- regression 在 Step 4.5 改业务代码（如直接修 lint 命中的违规）→ 跨职，违反"诊断不修复"硬门禁；正确做法是在 diagnosis 中标注"活体证据 + 修复点路由到 executing"。

### 来源

bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））— C1 修复点（regression.md Step 4.5）+ default-pick D-B1（事项 C 路由）+ bugfix-6 自身 diagnosis.md §测试用例设计 18 条用例样本

---

## 经验十：三维失配（契约层 / 源代码层 / 部署二进制层）诊断模板

### 场景

声称已修复的 bug 在新会话内再次复发；grep src/ 确认 helper 存在且逻辑正确，但 CLI 行为依然错误。触发 regression 诊断后，发现契约 / 源码 / 部署三个维度中存在"部分维度修了但未同步"的失配。

### 经验内容

**症状识别**：repo commit 已含修复代码（源码层 ✓），role 文档 / WORKFLOW.md 行为说明正确（契约层 ✓），但 `harness next` / `harness install` 等 CLI 命令实际行为与修复不一致（部署层 ✗）——最常见的根因是 pipx venv site-packages 未刷新，运行时二进制仍是旧版本。

**三维核查模板**：

| 维度 | 检查方式 | 失配症状 |
|------|---------|---------|
| 契约（role md / WORKFLOW.md / role-model-map.yaml） | 读文档 + grep 行为说明 | 行为说明 vs 实际输出对不上 |
| 源代码层（src/） | grep 函数定义 + 单元测试直调 | helper 缺失或逻辑错（pytest 直调 src/ 路径） |
| 部署二进制层（pipx / npm / docker site-packages） | grep 部署路径 + mtime 对比 + CLI 子进程行为 | helper 在 src/ 存在但 deploy 路径缺失 / 旧版本 |

**诊断三步**：

1. **L1 表象**：`harness next` 等 CLI 行为异常，复现步骤 + feedback.jsonl 截图。
2. **L2 中层**：分别 grep src/ 和 pipx venv site-packages 下同文件——`grep "_is_stage_work_done" ~/.local/pipx/venvs/harness-workflow/lib/python*/site-packages/harness_workflow/workflow_helpers.py`；对比 src/ mtime vs venv mtime。
3. **L3 根本**：若 src/ 有函数但 venv 无命中，根因 = **部署未刷新**。修复：`pipx install --force <repo-path>`。

**修复模式**：

- 部署层修复：`pipx install --force <repo-path>` 强制重装；
- dogfood 必须**子进程真跑 CLI 命令**（`subprocess.run([sys.executable, '-m', 'harness_workflow.cli', ...])`），不能只调 helper 函数——`pytest` 直调 helper = src/ 版本验证；subprocess CLI = 部署版本验证；**二者并列必跑**；
- acceptance.md 加"部署同步检查"硬条目（本 chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood） 落地）；testing.md 加"子进程 dogfood 红线"段。

**应用案例**：reg-02（over-chain bug 第三次本会话内实证（harness next --execute 4 跳跨 executing→done））——契约层（role-model-map.yaml stage_policies）✓ + 源码层（workflow_helpers.py _is_stage_work_done commit b64bcd7）✓ + 部署层（pipx venv mtime = 2026-04-26，早于 commit 2026-04-27，grep 无命中）✗；`pipx install --force` 后 CLI 行为立即正确。

### 来源

reg-02（over-chain bug 第三次本会话内实证（harness next --execute 4 跳跨 executing→done）— sug-46（req-44 二次实证 over-chain）/ sug-50（gate gap 实为部署 gap）/ sug-53（usage-log 缺失 + over-chain 副作用）同根因复发） + chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）

---

## 经验十一：install 反向清理盲区诊断（mirror 已删 + managed-files 仍登记）

### 场景

用户报告"多次 `harness install` 后目标项目 `.workflow/` 下永久残留 scaffold 已删的旧文件"（如 `usage-reporter.md` 在 req-42 archive 时被 scaffold 删除，但 PetMall 历经多轮 install 仍保留）。诊断需要识别 install 同步契约的反向缺位。

### 经验内容

**症状识别**：`diff -rq venv/scaffold_v2 vs target/.workflow/` 命中"only in target"非空，且这些文件**不在用户业务态白名单**（`flow/requirements/` / `state/sessions/` / `context/experience/regression/` 等）→ 是 scaffold 残留多余，非业务态。

**诊断三步**：

1. **L1 表象**：在目标项目跑 `find .workflow -type f` + `comm -23` 与 venv scaffold_v2 mirror 比对，列"只在 target 不在 mirror"清单；
2. **L2 中层**：grep `_install_self_audit` + `_sync_scaffold_v2_mirror_to_live`——install 同步契约只覆盖**正向**（mirror 有 → live 写入）和**覆盖**（mirror ≠ live → 写覆盖），**没有反向**（mirror 无但 managed-files 有 → 删除）；`LEGACY_CLEANUP_TARGETS` 是硬编码白名单，依赖人工维护，scaffold 删一个文件就要手工加一条；
3. **L3 根本**：`set(managed_state.keys()) - set(mirror.keys())` = dead entries 集合；这才是反向清理应当遍历的真候选。

**修复模式**：

- 在 `_sync_scaffold_v2_mirror_to_live` 加反向遍历分支：对 dead entries 中**不在业务态白名单**的文件，move 到 `LEGACY_CLEANUP_ROOT` 备份（不直删，留 git 可恢复路径）+ 同步从 `managed_state` 删除该 key；
- `_install_self_audit` drift > 0 时输出 ANSI 黄色 WARNING（非静默）；
- `LEGACY_CLEANUP_TARGETS` 从硬编码迁移到 mirror diff 自动派生（去掉手工维护负担）。

**反例**：把多余文件归到"用户业务态"忽略——业务态白名单（state/, flow/archive/, flow/requirements/ 等）外的"managed-files 登记过且 mirror 已无"才是真残留；只看文件名而不查 managed_state ↔ mirror 的差集会漏判。

**应用案例**：bugfix-7（pipx reinstall + harness install 后目标项目未更新到最新且残留多余文件） chg-01（反向清理 + check 对比）+ TC-01 dogfood 实证：tmpdir 模拟"mirror 已删 + managed-files 仍登记"双状态，跑 `harness install --agent claude` 后文件被 archive 到 `LEGACY_CLEANUP_ROOT`，managed-files.json 移除该 key。

### 来源

bugfix-7（pipx reinstall + harness install 后目标项目未更新到最新且残留多余文件） / chg-01（反向清理 + check 对比） — diagnosis.md §3 根因 A/B/D + §8 经验沉淀候选 + test-evidence.md TC-01

---

## 经验十二：pipx git URL 安装 vs 本地 HEAD 部署链条断裂诊断

### 场景

开发者本地仓库做 chg、commit，但**未 push 到 GitHub 远程**，然后让用户跑 `pipx reinstall harness-workflow`——用户拿不到本地未 push 的 commit。用户报告"reinstall 完了 install 没生效"，开发者 grep src/ 看到代码已修，断定"已修复"，实际 venv 还在远程旧 commit 上。

### 经验内容

**症状识别**：`pipx_metadata.json::main_package.package_or_url` = `git+https://github.com/.../...git`（git URL 安装源） + 用户报告 install 行为与 src 不一致 → 大概率是部署链条断裂（L2 失配）。

**诊断三步**（扩展经验十"三维失配"L2 部署层）：

1. **venv 安装 commit**：读 `~/.local/pipx/venvs/{pkg}/lib/python*/site-packages/{pkg}-*.dist-info/direct_url.json::vcs_info.commit_id`——这是 venv 实际安装时的远程 commit；
2. **本地 HEAD commit**：在仓库根目录跑 `git rev-parse HEAD`；
3. **diff hint**：`git log {venv_commit}..HEAD --oneline`——列出本地有但远程没有的 commit；非空 = 部署链条断裂。

**修复路径**：

- **正路**：开发者 `git push origin main` 把 commit 推到远程 → 用户 `pipx reinstall` 拿到新 commit；
- **快路**（绕过远程）：用户 `pipx install --force /path/to/local/repo`——`package_or_url` 改为本地路径，不依赖远程。

**反例**：直接 grep src/ 看到代码已修就断定"已修复"——忽略 pipx venv 还在远程旧 commit 上，用户跑出来的还是旧版本；这是反复制造"看起来修了但用户还在踩坑"的根源。

**配套契约（chg-04（文档强提示 check stdout）落地）**：`harness install --check` stdout 必含 venv 安装源 commit + 本地 HEAD commit + diff hint；旧版 venv 缺 helper 时由 CLI 子进程独立跑 `git log` 兜底（不依赖 venv 含 helper）。

**应用案例**：bugfix-7（pipx reinstall + harness install 后目标项目未更新到最新且残留多余文件） §诊断 / 根因 E/F/G——pipx venv `direct_url.json::commit_id = a801820`（远程 main 头部），本地 `git rev-parse HEAD = 83bb612`，`git log a801820..HEAD --oneline` 命中 1+ 个 archive commit；用户跑 `pipx reinstall` 永远拿不到 chg-01 / chg-02 改动，必须先 push。

### 来源

bugfix-7（pipx reinstall + harness install 后目标项目未更新到最新且残留多余文件） / regression / diagnosis.md §3 根因 E/F/G + §8 经验沉淀候选 + chg-04（文档强提示 check stdout）

---

## 经验十三：模式差异化（gate / lint / 契约扩展时三模式覆盖）

### 场景

reg-02 严格化 `_is_stage_work_done` 的 executing gate 时，只考虑 requirement 模式（`changes/` 子目录 + `test-report.md`）；bugfix-7 自身落地时立即触发 chg-07 紧急修复——bugfix 模式既无 `changes/` 也无 `test-report.md`，gate 永远 False，bugfix 周期被卡死。testing 阶段又复发一次（`testing` 分支只认 `test-report.md`，bugfix 用 `test-evidence.md`）。

### 经验内容

**核心规约**：凡是新增 gate / lint / 契约 / 路径 / artifact 自检，**必须**主动核对 BUGFIX_SEQUENCE / SUGGESTION_SEQUENCE / REQUIREMENT_SEQUENCE 三模式覆盖：

| 维度 | requirement 模式 | bugfix 模式 | suggestion 模式 |
|------|-----------------|------------|---------------|
| 拆分载体 | `changes/{chg-id}/` | 无（diagnosis.md 直驱） | 无（直接处理 OR 转 req） |
| 工件根目录 | `.workflow/flow/requirements/{req-id}-{slug}/` | `.workflow/flow/bugfixes/{bugfix-id}-{slug}/` | `.workflow/flow/suggestions/{sug-id}-{slug}.md` |
| executing 完成态 | `changes/` 各 `chg-id/session-memory.md` ✅ | `session-memory.md` ✅（顶层） | N/A |
| testing 报告 | `test-report.md` | `test-evidence.md` | N/A |
| acceptance 报告 | `acceptance-report.md` | `acceptance/checklist.md` + `bugfix-acceptance-report.md` | N/A |
| done 对人产物 | `交付总结.md`（done.md 完整模板） | `bugfix-交付总结.md`（精简版） | `交付总结.md`（轻量 3 段） |

**reg-02 盲区扩展**：严格化 `_is_stage_work_done` 时若只测试 requirement 模式 dogfood，bugfix 模式会被永久卡死；本 bugfix-7 chg-07 + testing 分路扩展是同根因复发的 hot-fix。

**修复模式**：

- 新增 gate 函数加 `operation_type` 参数 + 三分支显式判定；
- 新增 lint 时 dogfood 至少覆盖 requirement / bugfix 两模式（suggestion 直接处理路径按需）；
- `harness validate --contract` 各 lint 在 review checklist 中标注"已覆盖三模式"；
- review checklist 加"每新增门禁须三模式 dogfood"硬条目。

**反例**：reg-02 chg-02 严格化 gate 时只测 requirement 模式，bugfix-7 落地时 executing gate 永远 False，必须临时插 chg-07 + testing 阶段又插一次 testing 分路；本可在 reg-02 落地时一次闭环。

### 来源

reg-02（over-chain bug） + bugfix-7（pipx reinstall + harness install 后目标项目未更新到最新且残留多余文件） chg-07（executing gate bugfix 模式支持） + testing 阶段就地 testing 分路修复（session-memory.md §Testing Stage 附加）

