# Session Memory — req-56（路书引擎升级——Java/Maven 多模块 + LLM 内容填充 + 区段级只读）

> 关联：req-55（项目路书Playbook体系-项目地图+代码导航）作为 baseline；reg-01（chg-03/04 Java/Maven 项目盲点 + LLM 填骨架决策反转）作为触发器。本文件由 analyst（opus）在 analysis stage 写入，供 executing / testing / acceptance / done 四 stage 续写。

## 1. Current Goal

req-55 路书引擎在 Java/Maven 多模块项目（PetMallPlatform 类）实测零适配 + 纯静态分析骨架对人不友好；req-56 在 req-55 baseline 之上做 4 维度升级：

- 推断器多语言适配（chg-01：domain_inference.py 重构为 detector 注册器，覆盖 Maven / Gradle / Cargo / .NET 多模块 + 兼容 Python 4 级降级）
- SCRIPTS detector 注册化（chg-02：harness_playbook_refresh.py::_scan_scripts 重构为 detector 注册器，覆盖 Maven lifecycle / Gradle / Cargo / .NET 命令）
- LLM provider 抽象 + install/refresh 集成（chg-03 + chg-04：新建 llm.py 4 provider 抽象 + 自动检测 + lazy import；init_playbook / playbook_refresh 调 LLM 填充骨架业务内容；`--no-llm` flag 关闭 + env CI=true 自动 off + 失败 fallback Noop）
- base-role 硬门禁十 §4 区段级只读语义修订 + check 兼容（chg-05：AUTO/LLM 区段只读 + TODO 区域用户可改 + agent 默认不改 / 用户 explicit 后可改 + check 正则扩 LLM 区段）

## 2. Context Chain

- Level 0: 主 agent（harness-manager）→ analysis stage 编排
- Level 1: Subagent-L1（analyst / opus）→ req-56 analysis stage 全流程
  - 输入：reg-01 三份机器型工件（regression.md / analysis.md / decision.md）+ req-55 baseline（5 chg + requirement.md + test-report.md + acceptance/checklist.md + session-memory）+ inputs/initial-spec.md
  - 输出：req-56 requirement.md（12+3 = 13 AC，AC-13 ~ AC-25）+ 5 chg 子目录共 15 文件 + 5 OQ default-pick 清单（本文件 §5）

## 3. Completed Tasks（analysis stage）

- [x] 读 reg-01（chg-03/04 Java/Maven 项目盲点 + LLM 填骨架决策反转） 4 份工件（regression.md 136 行 / analysis.md 298 行 / decision.md 181 行 / meta.yaml）
- [x] 读 req-55（项目路书Playbook体系-项目地图+代码导航） baseline（requirement.md 12 AC + 5 chg × 3 文件 + session-memory.md §9 用户决策记录 + inputs/initial-spec.md §四"不调 LLM"原文）
- [x] 读 chg-03 实现 `domain_inference.py` 152 行 + chg-04 实现 `harness_playbook_refresh.py` 511 行 + chg-05 实现 `harness_playbook_check.py` 713 行 + chg-02 base-role 硬门禁十
- [x] 完善 `requirement.md`：Goal / Scope Included (5 chg) / Scope Excluded (8 项) / 13 AC（AC-13 ~ AC-25）/ Split Rules（chg DAG + 风险 R-5 ~ R-8 + 估算 5.5 day 线性 / 3.5 day 并行）
- [x] 拆 5 chg + DAG 单向依赖（chg-01/02/03 并行 → chg-04 → chg-05）
- [x] 每 chg 落 change.md + plan.md（含 §4 测试用例设计 ≥ 5 + 1 dogfood TC）+ session-memory.md
- [x] 5 OQ default-pick 清单（详见 §5，全部继承自 reg-01 decision.md §5）
- [x] 路径自检：所有产物落 `.workflow/flow/requirements/req-56-路书引擎升级-java-maven-多模块-llm-内容填充-区段级只读/`，无误落 req-55 / artifacts/main/

## 4. Results

### req 级产物

| 产物路径 | 说明 |
|---------|------|
| `requirement.md` | Goal / Scope（5 chg Included + 8 Excluded） / 13 AC（AC-13 ~ AC-25 含 PetMallPlatform fixture / Maven SCRIPTS / 4 LLM provider / `--no-llm` / 默认 LLM 填充 / base-role §4 文字 / check 兼容 / 端到端 dogfood / 41 TC 不破坏 / 全量回归零 fail / LLM 失败兜底 / hardgate 新契约） / Split Rules（chg DAG + 4 风险 + 估算）|
| `session-memory.md` | 本文件（§5 5 OQ default-pick 清单）|

### 5 chg 子目录（共 15 文件）

| chg-id | 子目录 | 文件 |
|--------|--------|------|
| chg-01（推断器多语言注册化） | `changes/chg-01-推断器多语言注册化/` | change.md + plan.md（13 步 + 6 + 1 TC）+ session-memory.md |
| chg-02（SCRIPTS detector 注册化） | `changes/chg-02-scripts-detector-注册化/` | change.md + plan.md（10 步 + 5 + 1 TC + 1 共存 TC）+ session-memory.md |
| chg-03（LLM provider 抽象层） | `changes/chg-03-llm-provider-抽象层/` | change.md + plan.md（13 步 + 8 mock TC + 1 placeholder + 1 dogfood）+ session-memory.md |
| chg-04（install/refresh 集成 LLM） | `changes/chg-04-install-refresh-集成-llm/` | change.md + plan.md（11 步 + 5 + 1 集成 + 1 PetMallPlatform dogfood）+ session-memory.md |
| chg-05（区段级只读语义 + check 兼容） | `changes/chg-05-区段级只读语义-与-check-兼容/` | change.md + plan.md（10 步 + 3 + 1 baseline + 1 lint + 1 dogfood）+ session-memory.md |

## 5. 开放问题（OQ）+ default-pick 清单（一次性 batched-report）

> 全部 5 OQ 由 reg-01（chg-03/04 Java/Maven 项目盲点 + LLM 填骨架决策反转） decision.md §5 草拟 + default-pick；本 analyst 阶段直接继承（无新增争议），完整选项 + 理由 + 风险监控如下。

### OQ-1：推断器架构（5 级降级硬编码 vs detector 注册器）

- **选项 A1（5 级降级硬编码）**：在 req-55 baseline 4 级降级链末尾加第 5 级 Java/Maven detector，硬编码 if-elif。
  - 优：改动小，与 req-55 实现风格一致；
  - 劣：每加新语言（Gradle / Cargo / .NET）就改链尾，未来可维护性差。
- **选项 B1（detector 注册器架构）— default-pick** ✓
  - 优：可扩展，未来加新语言只加一个 detector + 注册；与 chg-02 SCRIPTS detector 注册化同源（一致心智模型）；priority 字段保证 baseline 4 级降级语义不破坏；
  - 劣：实现复杂度上升（需重构 domain_inference.py），但有 chg-02 同源参考可降低风险。
- **理由**：未来扩展面（Kotlin / Multiplatform / Bazel / Buck 等）远多于 Java/Maven 单一，注册器架构是一次到位投资；与 chg-02 同源可统一 detector 模式经验。
- **风险监控**：chg-01 落地时 baseline 兼容 TC（TC-07~10 沿用 req-55 fixture）必须全 PASS，若任一 baseline TC 因优先级排序错命中错误 detector，立即升 reg。

### OQ-2：LLM 调用范围（仅 install / 全程可选 / 仅 refresh / 独立子命令）

- **选项 C1（仅 install 调用，refresh 不调）**
  - 优：refresh 保 CI 兼容；
  - 劣：refresh 后内容质量未提升，用户重复跑命令时不复用 LLM。
- **选项 C2（全程可选 + provider 抽象 + 默认 on local / off CI）— default-pick** ✓
  - 优：用户全场景受益 + CI 兼容（env CI=true 自动 off + `--no-llm` 显式 off） + provider 自动检测；
  - 劣：实现复杂度最大（需 LLM provider 抽象层 chg-03），但是一次到位。
- **选项 C3（仅 refresh 调用，install 不调）**
  - 优：install 保 CI 兼容；
  - 劣：首装初稿仍是 TODO 海，违反 reg-01 维度 C 用户诉求。
- **选项 C4（独立子命令 `harness playbook-llm-fill`）**
  - 优：彻底隔离，零回归；
  - 劣：用户多记一个命令，违反"首装即可用"承诺。
- **理由**：reg-01 用户反转决策核心是"首装看到有意义初稿"，C2 默认开启 + CI 兼容是最大公约数；refresh 也调 LLM 让内容随项目演进自动跟进。
- **风险监控**：chg-04 dogfood TC 必须证明 `--no-llm` flag + env CI=true 双路径都跳过 LLM 调用；mock provider 0 调用断言。

### OQ-3：LLM provider 默认（Anthropic / OpenAI / Ollama / 自动检测）

- **选项 Anthropic 默认**：硬编码默认 Anthropic，需用户配 ANTHROPIC_API_KEY。
  - 优：质量稳定；
  - 劣：付费门槛 + 锁单一供应商。
- **选项 OpenAI 默认**：同上锁单一。
- **选项 Ollama 默认**：本地零成本但需用户预装。
- **选项 自动检测 — default-pick** ✓
  - 优：按 env API key 优先级探测（ANTHROPIC > OPENAI > Ollama localhost > Noop），无 key 退 Noop（CI 友好）；用户零配置即可用；
  - 劣：探测顺序有序（ANTHROPIC 优先可能让有双 key 用户被锁定），但用户可显式 `LLM_PROVIDER=openai` env 强制覆盖。
- **理由**：自动检测最贴用户实际心智（"装了什么用什么"），符合 zero-config 哲学；NoopProvider 兜底保证无 key 也不破坏主流程。
- **风险监控**：chg-03 自动检测 4 TC 必须覆盖 4 路径（Anthropic / OpenAI / Ollama / Noop），Ollama ping 1s timeout 缓解风险 R-13。

### OQ-4：区段级只读 vs 任务级只读

- **选项 D1（区段级只读：AUTO/LLM 只读 + TODO 可改）— default-pick** ✓
  - 优：与 chg-04 LLM 写入面对齐（LLM 填的就是 LLM 区段，自然由 refresh 维护）；与现有技术现状对齐（chg-04 `replace_auto_section` 已天然支持区段级语义）；用户友好（TODO 区段可任意修改）；
  - 劣：语义复杂度上升（agent 需理解"区段内 vs 区段外"边界），但通过 base-role §4 三层语义说明 + 合规/违规示例缓解。
- **选项 D2（任务级只读：agent 默认全文件只读，用户 explicit 任务才允许写）**
  - 优：语义简单；
  - 劣：与 chg-04 LLM 写入面冲突（LLM install 写的就是区段，但 D2 把 agent 写全锁 → install 无法跑）。
- **选项 D3（双面策略：CI 漂移检测兜底 + agent 改 TODO 不报警）**
  - 实质是 D1 的扩展说明，可作为 D1 的实施细节合并。
- **理由**：D1 是技术现状的最自然语义化，且不破坏既有 41 TC（AUTO 区段哈希漂移检测沿用）；D2 与 chg-04 互斥不可选。
- **风险监控**：chg-05 base-role §4 文字 lint TC（grep 三个语义关键词）+ check 行为不变 TC（baseline AUTO 漂移仍检 + TODO 不报警）双向覆盖。

### OQ-5：dogfood TC 在 worktree fixture vs 真实 PetMallPlatform A/B

- **选项 A（worktree fixture 模拟）— default-pick** ✓
  - 优：不离开 worktree，符合派发约束（"不要去 PetMallPlatform 跑命令"）；fixture 严格按 reg-01 regression.md §3 维度 A 原始证据 A-3 描述构造（5 顶层模块 + 父 pom `<modules>` + spring-boot-maven-plugin + app/logs 噪声）；可重复 + CI 跑；
  - 劣：与真实项目可能有偏差。
- **选项 B（真实 PetMallPlatform A/B 测试）**
  - 优：真实数据；
  - 劣：离开 worktree（违反 派发约束）；不可重复 / 不可 CI 跑；fixture 偏差由 reg-01 原始证据控制可降低风险。
- **理由**：A 路径在 fixture 严格按 reg-01 证据构造时，与真实 PetMallPlatform 行为预期等价；B 路径作为路由后另起任务做（main agent 决定），不在本 req 范围内。
- **风险监控**：chg-04 PetMallPlatform-like dogfood TC 必须严格按 reg-01 §3 A-3 fixture 构造（5 模块名 + 父 pom + 噪声），任何 fixture 简化都触发 reg-01 偏差风险。

## 6. 待处理捕获问题（职责外）

无。

## 7. 路径自检（硬门禁九自查）

- [x] req-56 requirement.md 落 `.workflow/flow/requirements/req-56-路书引擎升级-java-maven-多模块-llm-内容填充-区段级只读/`（合规）
- [x] 5 chg 子目录全建（chg-01/02/03/04/05 各含 change.md + plan.md + session-memory.md，共 15 文件）
- [x] grep `'/req-55/'` 在 req-56 子树命中数 = 0（除 baseline 引用文本，符合契约 7 + 硬门禁六）
- [x] 引用 req-55 / reg-01 的 id 首次出现带 ≤ 15 字描述（contract 7 + 硬门禁六合规）

## 8. 下一步

- analysis stage 退出条件检查 → batched-report 给主 agent → 等用户拍板（按硬门禁四 stage 流转点保留用户介入）
- executing stage 派 sonnet 实施（按 chg DAG 单向依赖：chg-01/02/03 可并行 → chg-04 → chg-05）

---

## 9. 用户决策记录（2026-04-30）

用户回应："按照你说的做没问题" → **5 OQ 全部按 default-pick 拍定**：

| OQ | 决策 | 备注 |
|----|------|------|
| OQ-1（推断器架构） | **B1**（detector 注册器） | Python/Java/Gradle/Cargo/.NET 各独立 detector 类，主入口按优先级遍历 |
| OQ-2（LLM 调用范围） | **C2**（全程可选） | install / refresh 默认调 LLM，`--no-llm` flag 关闭（CI 友好） |
| OQ-3（LLM provider 默认） | **自动检测** | 顺序 `ANTHROPIC_API_KEY` > `OPENAI_API_KEY` > Ollama localhost > Noop 降级 |
| OQ-4（路书只读语义） | **D1**（区段级只读） | AUTO 区段（脚本+LLM）只读；TODO 与人写区域用户可任意改；chg-05 playbook-check 仅检 AUTO 区段哈希 |
| OQ-5（dogfood TC 范围） | **A**（worktree fixture） | tmpdir 模拟 PetMallPlatform 结构；真实 A/B ROI 测试由主 agent 在 done 后另起任务（步 2） |

5 OQ 决策与 analyst 草案 default-pick **完全一致**，不触发批量同步任务（chg 文件不改），直接推 executing。
