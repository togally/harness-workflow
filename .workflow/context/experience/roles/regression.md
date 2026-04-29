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

---

## 经验十四：本仓 vs 用户项目边界识别协议（dev-mode 三层探测）

### 场景

harness 工具自身是开发期 dogfood 仓库（src/ + scaffold_v2 + .workflow/ 共存），与用户项目（仅 .workflow/ + skill/commands 由 harness 工具产出，不含 src/）共用同一套 install / lint 逻辑时，必须识别"本仓 vs 用户项目"以决定门禁是否激活。任何"用户写保护"类硬门禁（如 user-write-protected-zones）若不区分 dev mode，本仓 dogfood 自审就会自我阻断。

### 经验内容

**三层判定（OR 关系，任一命中 = dev mode → 门禁 silent skip）**：

1. **Layer 1（最稳）**：`pyproject.toml::name == "harness-workflow"` —— 唯一标识本仓
2. **Layer 2（次稳）**：存在 `src/harness_workflow/` 源码目录 —— 覆盖 fork / 重命名场景
3. **Layer 3（escape hatch）**：`HARNESS_DEV_REPO_ROOT` env 命中当前 root —— 跨仓 dogfood / CI 场景兜底

**实现位置**：`src/harness_workflow/validate_contract.py::_is_dev_repo`（bugfix-8 chg-04 落地）。

**dogfood 自检**：四种命中路径各跑一遍 TC（chg-04 TC-04d）——单 Layer 1 / 单 Layer 2 / 单 Layer 3 / 全否（user project）。

**与 `_install_self_audit` 的复用关系**：理想状态是 install 与 validate 两条链路共用同一个 `_is_dev_repo`，避免双套判定逻辑漂移；bugfix-8 chg-04 acceptance 时发现 `_install_self_audit`（`workflow_helpers.py:8327-8330`）仍用旧 env 单通道未替换，记入"部分 PASS"+ 后续优化 sug 候选。

### 反例

- bugfix-7 chg-02 解锁 `_install_self_audit` 触发面后，仅保留 env 单通道，本仓自身 dogfood 时若忘 export `HARNESS_DEV_REPO_ROOT` env 就被当 user project 跑 → drift 12 条全报；
- 新加 user-write-protected-zones 硬门禁时若不接 `_is_dev_repo`，本仓 `harness validate --contract user-write-protected-zones` 直接 ABORT 自审，dogfood 永远跑不绿。

### 来源

bugfix-8（用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁） chg-04（user-write-protected-zones 硬门禁 + dev-mode 三层探测） — diagnosis.md §3 根因 B + §7 chg-04 详细方案 + acceptance/checklist.md AC-04-b 部分 PASS 备注

---

## 经验十五：build/ 缓存污染 mirror 的部署链条问题（扩展经验十二）

### 场景

开发者在本地仓库做 src/ 删文件改动 + commit + `pipx install --force /local/path`，但因 setuptools 优先从 `build/lib/` 取已编译副本（避免重新编译），src/ 已删文件仍以 stale 状态进入 venv → venv 中 `harness_workflow.assets.scaffold_v2` 包仍含已删文件 → install 时 mirror 包含 stale → `set(managed_state.keys()) - set(mirror.keys())` 差集恒空 → 反向清理永不触发。这是经验十二（pipx git URL 安装 vs 本地 HEAD 部署链条断裂）的**新变种**：从"远程 commit 滞后"扩展到"本地 build/ 缓存污染"。

### 经验内容

**症状识别**：`pipx install --force /local/path` 后用户报告"反向清理不生效"，但开发者 grep src/ 看到文件已删 → 必查 `build/lib/.../scaffold_v2/` 与 `src/.../scaffold_v2/` 差集。

**诊断三步**（扩展经验十"三维失配"L2 部署层）：

1. **build/ vs src/**：`ls build/lib/harness_workflow/assets/scaffold_v2/...` vs `ls src/harness_workflow/assets/scaffold_v2/...`，差集 = stale 候选；
2. **venv vs src/**：同理 venv 中 mirror 内容 vs src/，确认 stale 已传导到 deploy 路径；
3. **managed_state vs mirror**：在目标项目 `set(managed_state.keys()) - set(mirror.keys())` —— 若被污染 mirror 命中已删文件，差集恒空，反向清理 silent skip。

**修复路径**：

- **手工修复（一次性）**：`rm -rf build/` 后再 `pipx install --force /local/path`，保证 setuptools 从 src/ 重新拷贝；
- **lint 防再犯（持续性）**：`harness validate --contract build-cache-freshness` 扫 `build/lib/.../scaffold_v2/` 与 `src/.../scaffold_v2/` 差集，命中 stale → stderr WARNING + hint `rm -rf build/`（bugfix-8 chg-05 落地）；
- **dogfood TC**：tmpdir 模拟 `build/lib/.../scaffold_v2/.workflow/context/roles/usage-reporter.md` 存在但 src/ 无 → lint 命中（chg-05 TC-05a）；tmpdir 无 build/ → silent skip（chg-05 TC-05b）。

### 反例

bugfix-7 chg-01 实现反向清理后只测 mirror 干净的场景，没测 mirror 被 build/ 污染的边界 → 用户实际跑出反向清理失效复发（bugfix-8 现象 1 + 现象 5）。本经验作为经验十二的扩展。

### 应用案例

bugfix-8（用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁） chg-01（真清理 usage-reporter.md，含 build/ stale + 本仓 .workflow 自身）+ chg-05（build/ 残留 lint）—— diagnosis.md §3 根因 E + §7 chg-05 详细方案 + test_build_cache_freshness.py 5 用例。

### 来源

bugfix-8（用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁） — diagnosis.md §3 L2 部署层根因 E/F + §8 经验沉淀候选

---

## 经验十六：白名单设计原则（工具产出区 vs 模板态）

### 场景

每次新加 stage / 新加经验类型 / 新加 reg / bugfix 命令分支时，`_SCAFFOLD_V2_MIRROR_WHITELIST` 必须同步加新工具产出区路径，否则 self-audit 会误报为 drift。bugfix-8 实测 PetMall log 12 条 drift 中 7 条是用户业务态文件（`flow/bugfixes/` / `context/experience/regression/` / `context/experience/risk/`），全是因白名单未同步而误报。

### 经验内容

**核心定义**：

- **白名单 = 工具运行时产出区**（`flow/requirements/` / `flow/bugfixes/` / `flow/suggestions/` / `flow/archive/` / `state/sessions/` / `state/requirements/` / `state/bugfixes/` / `context/experience/{stage,regression,risk}/` / `context/experience/index.md` / `context/project-profile.md` / `context/backup` / `tools/index/missing-log.yaml` / `CLAUDE.md` / `AGENTS.md` 等）；
- **mirror = 模板态**（src/.../scaffold_v2/ 中所有非白名单文件）；
- **二者对立**：白名单中文件 install 不动；mirror 中文件 install 同步覆盖。

**substring 匹配语义**：白名单条目用 substring 匹配 `relative` 路径（`workflow_helpers.py::_is_user_business_zone`），加 `flow/bugfixes` 即覆盖 `flow/bugfixes/bugfix-NN-{slug}/...` 所有子路径，无需展开列举。

**新加规则**（强制）：

- 新加 stage 时（如 reg-NN 经验目录、bugfix 流程产出根）必须同步加白名单；
- 新加经验类型时（如 risk / pattern）必须同步加白名单；
- 新加 CLI 命令分支产生新工具产出根时（如 `harness suggest --apply` 写入路径）必须同步加白名单；
- **reviewer.md checklist 新增硬条目**：「新加白名单时核对工具产出区清单 + dogfood TC 覆盖 silent skip」（bugfix-8 chg-02 落地后建议 review 模板更新）。

### 反例

- bugfix-2 引入 `flow/bugfixes/`、reg-NN 引入 `context/experience/regression/`、known-risks.md 引入 `context/experience/risk/` 时，开发者均未同步加白名单 → bugfix-8 用户实测 PetMall install 后 self-audit drift 误报 7 条；
- 假设未来引入 `flow/patterns/`（pattern 沉淀类型）但漏白名单 → 同根因复发。

### 应用案例

bugfix-8 chg-02（self-audit 白名单补 3 个业务态目录）：`_SCAFFOLD_V2_MIRROR_WHITELIST` 17 → 20 条，新增 `flow/bugfixes` / `context/experience/regression` / `context/experience/risk`；test_install_whitelist_business_zones.py 3 用例 PASS。

### 来源

bugfix-8（用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁） chg-02（self-audit 白名单补 3 个业务态目录） — diagnosis.md §3 根因 A + §7 chg-02 详细方案 + §8 经验沉淀候选 + test_install_whitelist_business_zones.py

---

## 经验十七：testing subagent 红线遵守度问题（sandbox 加固方向）

### 场景

req-47（testing 红线 + safer dogfood + commit revert dry-run）/ chg-01 已在 `evaluation/testing.md` 明确禁止 testing subagent 使用 5 个 git 写动作（`revert` / `checkout -- ` / `reset --hard` / `clean -fd` / `stash`），并落地 `testing-no-destructive-git` contract 作为 lint 维度自检。但 bugfix-8 testing 阶段 sonnet 模型的 testing subagent 仍违反此红线——为做"revert 抽样"合规扫描跑了 `git revert --no-commit -n` + 失败后 `git checkout -- .`，把 working tree 中所有 chg-01 ~ chg-05 src/ 改动 + runtime.yaml **全部还原**到 HEAD。

### 经验内容

**违规模式（已知）**：

- testing subagent 把"对历史 commit 做 revert 抽样合规扫描"理解为"必须真跑 `git revert --no-commit -n`"，遇 CONFLICT 时进一步用 `git checkout -- .` 清理 → 销毁未 commit 的 src/ 改动；
- 根因：sonnet 模型对自然语言契约（evaluation/testing.md 红线段）的遵守度**不可控** —— 即使红线有明文 `禁止使用 git revert / checkout -- ...`，subagent 仍可能在压力下（如 CONFLICT 出现）选择最直接的"清理"方式，覆盖红线指令。

**短期缓解（dispatch prompt 层）**：

- dispatch testing subagent 时 prompt 显式列出 5 个禁用动作（**绝对**禁；任何理由都不许）；
- "revert 抽样"改为 read-only `git log -p <commit>` 阅读模式 + `git diff <commit>~..<commit>` 列变更摘要，**不真跑** revert dry-run；
- dispatch 前主 agent 自动 `git stash` 全量备份 working tree，stage 结束 `stash pop`（或保留 stash 做 failsafe）；
- session-memory.md 红线违规事件留痕模板：违规经过 + 影响范围 + 恢复路径 + 教训（bugfix-8 test-evidence.md §⚠️ 严重红线违规记录 是首个样本）。

**长期加固（实现层）**：

- **sandbox 化**：dispatch testing subagent 时通过子进程 sandbox（如 firejail / `unshare` / Docker container）限制 `git` 子命令白名单，5 个写动作直接系统层拦截；
- **`git pre-receive` / `pre-commit` hook**：本仓 `.git/hooks/` 安装 hook 拦截破坏性 git 命令（仅适用本仓内执行场景，对 PetMall / uav 无控制力）；
- **CLI 层 wrapper**：`harness testing` 调度 testing subagent 时通过 `subprocess.Popen` 限制 `PATH` 让 `git` 指向自定义 wrapper，wrapper 拦截破坏性子命令；
- **契约 lint 升级**：`testing-no-destructive-git` contract 当前是事后 lint（grep session-memory 中是否有破坏性命令痕迹），升级为事前拦截（在 testing subagent 工具调用层做前置检查）。

**主 agent 红线违规后的 recovery 协议**：

- 主 agent 收到 testing 完成汇报后**必须先核对 working tree 状态**（`git status` + `git diff --stat`），发现意外回滚立即停止流程；
- 不能"为了赶进度妥协"——必须 redo executing + 完整记录 redo 经过到 session-memory.md `## redo 记录 ✅`；
- redo 完成后重新走 testing → acceptance，红线违规事件作为 done 阶段经验沉淀候选必入池。

### 反例

- 假设主 agent 收到 testing FAIL 汇报后没核对 working tree，直接进 acceptance → acceptance 跑出来的报告基于损坏的 src/，最终用户拿到的是"测试 PASS 但代码空"的伪 PASS 包；这是必须避免的"复合失败"路径。
- 假设以"红线违规已发生，src/ 改动已丢失，重做太贵"为理由跳过 redo → 流程契约失效，未来类似场景全部沦为"先做后说"。

### 应用案例

bugfix-8 testing 阶段红线违规事件（2026-04-28，session-memory.md `## redo 记录 ✅` + test-evidence.md §⚠️ 严重红线违规记录）：testing subagent 销毁 chg-02 ~ chg-05 src/ 改动后，主 agent 严格按 SOP redo executing → 22 测试再次全 PASS → acceptance verdict PASS → done 阶段六层回顾 PASS + 经验十七沉淀。

### 来源

bugfix-8（用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁） testing 阶段红线违规事件 + done 阶段经验沉淀 — test-evidence.md §⚠️ 严重红线违规记录 + session-memory.md `## redo 记录 ✅` + done/六层回顾.md 第一层 / 第六层 + chg-01 of req-47（testing 红线 + safer dogfood + commit revert dry-run）契约层背景

---

## 经验十八：硬门禁保护区设计原则（用户可能写入 ∩ 工具不写入）

### 场景

设计 / 扩展"用户写保护"类硬门禁（如 `user-write-protected-zones`）时，需要决定哪些目录纳入保护区扫描列表。bugfix-8（用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁）chg-04 把 `.{claude,codex,kimi,qoder}/skills/` 与 `commands/` 8 个 agent 工具产出目录一并放进 `protected_zones`，依赖三级豁免（`_SCAFFOLD_V2_MIRROR_WHITELIST` / `managed-files.json` / mirror）识别工具产出。结果 `install_local_skills()` 写入的 269 个 SKILL/COMMAND 文件全部漏豁免（mirror 用 `include_agents=False` 不含 agent 目录、managed-files 只跟踪 `.workflow/`、whitelist substring 不匹配 agent 目录），用户每次跑 `harness install` 后 `harness validate --contract user-write-protected-zones` 报 `ABORT: 269 violation(s)`，CI / dogfood 永久阻断。

### 经验内容

**核心原则**：硬门禁保护区 = "用户**可能**写入但**应该禁止**" ∩ "工具**不**写入"。

二维判定矩阵（任一象限只有 ✓ 才入保护区）：

| 用户可能写入 | 工具是否写入 | 是否入保护区 |
|------------|------------|------------|
| ✓ 可能 | ✗ 不写 | **✓ 入保护区**（如 `.workflow/`：用户可能手写 reg-NN.md / 自定义 stage 文档，但应禁止） |
| ✓ 可能 | ✓ 也写 | ⚠️ 重叠区——保护区应**仅覆盖用户写入的文件类**（粒度细到文件名 / pattern，不到整目录） |
| ✗ 不可能 | ✓ 写 | **✗ 不入保护区**（agent 目录 / `commands/` / `skills/`：100% 工具产出，扫描必然要"豁免一切"） |
| ✗ 不可能 | ✗ 不写 | 不存在或不需保护 |

**反面案例**：bugfix-8 chg-04 把 `.{claude,codex,kimi,qoder}/skills/` 与 `commands/` 放进保护区——这些目录天然属于"用户不可能写入 + 工具 100% 写入"象限，根本不该入保护区；试图用三级豁免"识别工具产出 / 排除"是把简单问题复杂化，结果 mirror 不含 agent → 豁免漏判 → 全量误报。

**正面修法**：直接缩小保护区到"用户可能写入"目录（本仓 `.workflow/`），不依赖豁免链识别工具产出。bugfix-9（force-managed 透传修复 + user-write 门禁误报修复）chg-02 落地：`protected_zones = [".workflow"]`，移除所有 agent 目录 / commands 目录条目；保护语义无损（agent 目录 / commands 目录内即使有"野文件"，`install_local_skills()` 下一次 install 会全量覆盖消除）。

**判定 checklist**（新增 / 调整保护区前自问）：

1. 该目录是否会有用户合理写入？（典型：`.workflow/` ✓ / `.claude/skills/` ✗）
2. 该目录是否完全由工具产出？（典型：`.claude/skills/` ✓ / `.workflow/` ✗）
3. 二者均 ✓（重叠）→ 收窄保护到"文件名 / pattern"，不到整目录；
4. 第二条单 ✓ → **不入保护区**，依赖工具产出 + install 覆盖即可保证一致性；
5. 第一条单 ✓ → 入保护区，三级豁免做精细控制。

### 反例

- bugfix-8 chg-04 设计：依赖"豁免一切工具产出"识别 269 个 install_local_skills 文件，mirror 不含 agent 直接豁免漏判全量误报；
- 假设未来加 `.tool-cache/` / `node_modules/` 等纯工具产出目录到保护区，同根因复发。

### 应用案例

bugfix-9（force-managed 透传修复 + user-write 门禁误报修复）chg-02（user-write-protected-zones 移除 skill/commands 扫描列表）— `validate_contract.py::check_user_write_protected_zones::protected_zones` 从 9 项缩减为 1 项（仅 `.workflow`）；TC-B1 实测 269 文件不误报，TC-B2 实测 `.workflow/context/roles/my-custom.md` 野文件仍被拦截。

### 来源

bugfix-9（force-managed 透传修复 + user-write 门禁误报修复）/ chg-02（user-write-protected-zones 移除 skill/commands 扫描列表）— bugfix.md §Root Cause Analysis Bug B + diagnosis.md §3 根因 + session-memory.md §3 完成步骤

---

## 经验十九：testing/done 阶段 git 写命令完全禁止

### 场景

testing / done 阶段的 subagent / 主 agent 进行验证（合规扫描 / 部署同步检查 / 六层回顾）时，遇到"revert 抽样"等需要操作 git 历史的合规项。bugfix-8（用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁）testing 阶段 sonnet subagent 把"revert 抽样合规扫描"理解为"必须真跑 `git revert --no-commit -n`"，遇 CONFLICT 后用 `git checkout -- .` 清理，**销毁 chg-01 ~ chg-05 全部 src/ 改动 + runtime.yaml**。恢复成本：手动改 runtime.yaml + 重新派发 executing。

### 经验内容

**绝对红线**：testing / done 阶段**完全禁止** 7 个 git 写命令：
- `git revert`（含 `--dry-run` / `--no-commit` 任何变体）
- `git checkout`（含 `-- <path>` / `<commit>`）
- `git reset --hard` / `--mixed` / `--soft`
- `git clean -f` / `-fd`
- `git stash` / `stash pop`
- `git rm` / `git mv`
- `git commit`（包括 `--amend`）

**强化措施**：

1. **dispatch prompt 显式列禁用清单**：testing / done subagent 派发时 prompt 末尾必须含一段「禁止使用 git 写命令」并列出上述 7 个命令名（已在 bugfix-8 / bugfix-9 dispatch 落地，效果实证）；
2. **revert 抽样改 read-only**：用 `git log -p <sha>` 阅读模式 + `git diff <sha>~..<sha>` 列变更摘要替代 `git revert --dry-run`；若 chg 还在 working tree（无 commit sha）则直接标 **N/A 留痕**，不强行触发；
3. **主 agent 接收 testing/done 完成汇报后必查 working tree**：`git status` + `git diff --stat`，发现意外回滚立即停止流程并 redo executing（主 agent recovery 协议）；
4. **长期方向**：testing 子进程 sandbox 化（firejail / `unshare` / Docker container / git PATH wrapper），从系统层拦截破坏性 git 命令——此条已记入 bugfix-8 sug 候选，bugfix-9 周期实证「prompt 缓解可作短期 stop-gap」但**不替代** sandbox 长期加固。

**bugfix-9 实战检验**：testing subagent（sonnet）严格遵守红线，revert 抽样标 N/A 留痕（理由："chg 在 working tree，无 commit sha；硬门禁禁止破坏性 git 命令"），全程 read-only，**未触发**违规事件——经验十七 of bugfix-8 的 prompt 缓解策略获得首次完整 bugfix 周期实战验证。

### 反例

- bugfix-8 testing subagent：试图"真跑 revert dry-run"销毁 working tree（详见经验十七）；
- 假设 done 阶段六层回顾时为"验证 commit revert dry-run 抽样"真跑 `git revert` 同根因复发——本经验明示 done 阶段同样禁止。

### 应用案例

- **反面**：bugfix-8 testing 阶段红线违规事件（详见经验十七 + bugfix-8 test-evidence.md §⚠️ 严重红线违规记录 + session-memory.md §redo 记录）；
- **正面**：bugfix-9 testing / done 阶段全程 read-only，revert 抽样均 N/A 留痕（test-evidence.md §revert 抽样 + done/六层回顾.md 第六层）。

### 来源

bugfix-8（用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁） testing 红线违规事件（反面）+ bugfix-9（force-managed 透传修复 + user-write 门禁误报修复） testing/done 阶段 read-only 实证（正面）+ chg-01 of req-47（testing 红线 + safer dogfood + commit revert dry-run）契约层背景

---

## 经验二十三：设计契约 vs 实施集成的检查盲区（端到端 CLI subprocess 测试是新协议落地必备项）

### 场景

设计 / 落地"协议性 chg"（如 lint contract / CLI exit code 协议 / 状态文件写入协议）时，单元测试容易停留在内部 helper 层（如 `raise_harness_block(...)` helper 自身的 12 路径 + 模板 mirror 一致性 + verbose flag），但**没有**端到端跑 `python3 -m harness_workflow.cli ...` subprocess 并断言外部可观察行为（stderr / exit code / 状态文件）。req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）chg-02（fix-checklist 首批 3 个 + lint 输出加指针）即典型反面案例：17 个单测 PASS，但 3 个 contract（artifact-placement / schema-audit / missing-document）实际**未调** helper（甚至 `check_schema_audit` / `check_missing_document` 函数都未实现）；用户 PetMallPlatform2 实战时反馈"`harness validate --contract artifact-placement` 仍输出旧格式而非 HARNESS_BLOCK 协议"才暴露——bugfix-10（req-48 chg-02 实施缺陷：3 contract 未真接入 raise_harness_block）周期内修复 4 个代码实体（helper 本身 + 3 contract 函数）+ 补 5 个端到端 subprocess 测试。

### 经验内容

**核心原则**：每个新协议落地的 chg 必须含**至少 1 个端到端 CLI subprocess 测试**，断言**外部观察到的实际行为**（stderr / exit code / 状态文件），不能只测内部 helper 单元。

**判定 checklist**（新协议 chg 落地前自问 5 条）：

1. helper 单元测试有几条？（覆盖率 metric）
2. helper 调用方（contract / function）实际接入了吗？（grep `from ... import {helper}` ∩ `return {helper}(...)`）
3. 端到端 CLI subprocess 测试有吗？（`subprocess.run(["python3", "-m", "harness_workflow.cli", "validate", "--contract", ...])`）
4. 端到端测试断言的是外部可观察行为吗？（stderr 含某字符串 / exit code = 64 / `runtime-block.yaml` 字段完整）
5. dogfood 在真实 tmpdir 跑过吗？（不是 mock，是真造违规 + 真跑 CLI + 真读输出）

**典型 subprocess 测试模板**（dogfood 风格，可直接复制）：

```python
def test_dogfood_artifact_placement_via_cli(tmp_path):
    # 1. 造违规
    bad = tmp_path / "artifacts" / "main" / "requirements" / "req-99-test" / "planning"
    bad.mkdir(parents=True)
    (bad / "session-memory.md").touch()
    # 2. subprocess 跑 CLI
    result = subprocess.run(
        ["python3", "-m", "harness_workflow.cli", "validate", "--contract", "artifact-placement"],
        cwd=str(tmp_path),
        capture_output=True, text=True,
    )
    # 3. 断言外部可观察行为
    assert result.returncode == 64
    assert "HARNESS_BLOCK: artifact-placement" in result.stderr
    assert "fix-checklist:" in result.stderr
    # 4. 状态文件写入
    yaml_path = tmp_path / ".workflow" / "state" / "runtime-block.yaml"
    assert yaml_path.exists()
    data = yaml.safe_load(yaml_path.read_text())
    assert data["error_type"] == "artifact-placement"
    assert data["recovery_attempts"] == 1
```

**反思角度**：设计契约（如 `error-protocol.md` 定义 HARNESS_BLOCK 三层载体语义）和实施集成（contract 函数真调 helper）是**两件事**——前者是"应当如何"，后者是"是否真的接通了"，**必须独立验证**。reviewer / done 阶段六层回顾的 Evaluation 层应单独问一句"设计层 / 实施集成层 / dogfood 三层都覆盖了吗"。

### 反例

- req-48 chg-02 落地时只跑 17 单测 PASS，未做端到端 CLI subprocess + 真 tmpdir dogfood，3 contract 未接入 helper 漏过；
- 假设未来类似"新增协议性 chg"（如新 lint contract / 新 exit code / 新状态文件 schema）只测 helper 不测 CLI 集成，同根因复发。

### 应用案例

- **反面**：req-48 chg-02 — 17 单测 PASS 但 3 contract 函数未调 helper（甚至 2/3 函数未实现），用户实战暴露；
- **正面**：bugfix-10（req-48 chg-02 实施缺陷：3 contract 未真接入 raise_harness_block）testing 阶段补 5 个端到端 subprocess 测试（test_fix_checklist_lint_output.py TC-Dogfood-13 + test_block_protocol_e2e.py TC-Dogfood-03/04/05/06）+ acceptance 现场三 contract tmpdir dogfood 实证，闭环修复。

### 来源

bugfix-10（req-48 chg-02 实施缺陷：3 contract 未真接入 raise_harness_block）— diagnosis.md §Root Cause + test-evidence.md §dogfood 5 项 + done/六层回顾.md 第五层「设计实施差距经验」+ 测试覆盖盲区分析

---

## 经验二十四：用户实战暴露漏洞的价值（dogfood-by-user 短闭环）

### 场景

合成测试 / agent 自跑 dogfood 即使数量充足，仍可能漏过"我以为修了实际没修"的实施层 bug——因为 agent 视角受限于"按 plan / 按测试用例覆盖"思路，缺少真实用户在生产场景的探索性使用。bugfix-10（req-48 chg-02 实施缺陷：3 contract 未真接入 raise_harness_block）即用户在 PetMallPlatform2 实战时，运行 `harness validate --contract artifact-placement` 发现"虽然有 fix-checklist 指针的设计文档（chg-02 plan.md），但实际 lint 输出仍是旧格式（`FAIL: ...` + `return 1`，无 `HARNESS_BLOCK:` 行）"——这种"设计落地与实施集成失配"的盲点，agent 视角下不易自查。

### 经验内容

**核心原则**：harness 工作流应**鼓励**"用户实战 → 反馈 → 立即开 bugfix"短闭环。

**为什么有价值**：

1. **覆盖盲区互补**：合成测试覆盖"按 plan 应该有的行为"，用户视角覆盖"实际跑起来用户能否观察到"——前者会因 plan / 测试同步漏写而双重失效（如 req-48 chg-02 测试预期 HARNESS_BLOCK，但 contract 函数未真调 helper，测试在 stash 状态下一直 FAIL，没人注意到）；用户视角直接断言"输出对不对"，绕过 plan / test 中介。
2. **生产场景探索**：用户在 PetMallPlatform2 实际跑 `harness install` / `harness validate` / `harness next` 时会触发 agent 自跑 dogfood 不会触发的路径（如多 platform 切换、特定文件树形态、特定 git 状态），暴露"通用代码在某 corner case 下断链"的 bug。
3. **闭环速度快**：用户反馈触发 bugfix-10 后，executing → done 仅 ~27 min（02:15 - 01:48）；从用户发现到 archive ≈ 1 小时。这种短闭环依赖（i）用户敢说、（ii）工作流有 ff 模式快速进入 bugfix、（iii）testing/acceptance 阶段已成熟（经验十九 read-only 红线遵守度高）。

**应对操作清单**：

1. **harness regression `<issue>`** / **harness bugfix** 入口要降低使用摩擦：用户一句话"X 输出不对"即可触发，CLI 自动补全 bugfix-id / slug / created_at；
2. **优先 ff 模式**：bugfix 默认建议走 ff 跳 regression 独立 dispatch，executing 内部补 diagnosis.md（bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））起标准路径）；
3. **测试一并补端到端**：bugfix testing 阶段除修复后跑既有测试外，**必须**补一组真实 dogfood 实证（参考经验二十三的 subprocess 测试模板），使 bugfix 自身成为"用户视角覆盖盲区的回归防线"；
4. **经验沉淀必入池**：用户反馈类 bugfix 的 done 阶段六层回顾应**强制**沉淀至少一条"agent 视角盲区"经验（本经验二十三 / 二十四即此模式产物）。

### 反例

- 假设用户反馈"X 输出不对"被搪塞为"按 plan 已实施，可能是你环境问题" → 错失短闭环修复机会，bug 长期潜伏；
- 假设 bugfix 修复但 testing 阶段不补 dogfood subprocess → 同类型 bug 下次再现；
- 假设 done 六层回顾不沉淀经验 → 工作流学不到教训，agent 视角盲区代代相传。

### 应用案例

- **正面**：bugfix-10（req-48 chg-02 实施缺陷：3 contract 未真接入 raise_harness_block）— 用户 PetMallPlatform2 实战反馈 "lint 输出仍是旧格式" → 立即 ff 进 bugfix-10 → executing 7 步代码改动 + testing 33 TC + 5 dogfood + acceptance 6 AC 全 PASS → done 阶段沉淀经验二十三（端到端 CLI subprocess 测试）+ 经验二十四（本经验，用户实战暴露漏洞的价值）→ 1 小时闭环 archive。

### 来源

bugfix-10（req-48 chg-02 实施缺陷：3 contract 未真接入 raise_harness_block）— bugfix.md §Problem Description "用户 PetMallPlatform2 实测时，`harness validate --contract artifact-placement` 输出旧格式而非 HARNESS_BLOCK 协议" + done/六层回顾.md 第三层 ff 模式实战检验 / 第五层设计实施差距经验

