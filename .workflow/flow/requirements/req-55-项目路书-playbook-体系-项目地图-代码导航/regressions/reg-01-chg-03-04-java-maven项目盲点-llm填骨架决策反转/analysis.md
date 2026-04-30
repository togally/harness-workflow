---
id: reg-01
title: "chg-03/04 Java/Maven项目盲点 + LLM填骨架决策反转"
created_at: 2026-04-30
operation_type: regression
stage: regression
linked_requirement: req-55
linked_changes: [chg-03, chg-04, chg-02, chg-05]
---

> 关联：req-55（项目路书Playbook体系——项目地图+代码导航）/ chg-03（harness install 追加路书初始化）/ chg-04（harness playbook-refresh 子命令）/ chg-02（baseRole代码加载规则与CLAUDE索引）/ chg-05（harness playbook-check 子命令）。

## 1. Problem Assessment（真实性核查）

| 维度 | 类型 | 证据 | 是否真实 |
|------|------|------|---------|
| A | 真实问题（real issue） | grep `domain_inference.py` 0 命中 Java/Maven 关键字 + dogfood fixture 复现 `matched 'app/*' (logs, temp)` 与用户报告输出一致 | 是 |
| B | 真实问题（real issue） | grep `harness_playbook_refresh.py::_scan_scripts` 只支持 pyproject/package.json/Makefile，0 命中 mvn / gradle / cargo / dotnet | 是 |
| C | 决策反转（spec change） | spec §四 / requirement.md Excluded 第 30-31 行明确"不让脚本调 LLM"，用户基于 dogfood 反转 | 是（用户拍板，非误判） |
| D | 语义松动（contract drift） | base-role.md 硬门禁十 §4 "不要修改 `artifacts/project/playbooks/` 下任何文件"与维度 C 反转结论冲突 | 是（与 C 互锁） |

**结论**：4 维度均为真实问题，dogfood 数据真实性独立验证通过（在本 worktree 内重现 PetMallPlatform 推断结果，与用户报告完全一致）。

## 2. 维度 A 根因分析：chg-03 推断器 Java/Maven 盲点

### 2.1 根因（L3 一句根本）

**chg-03 4 级降级链的核心假设是"Python/JS 单仓 / 单包项目结构"，未涵盖"Java/Maven 多模块顶层平级根"惯例**——这是 OQ-4 决策时**遗漏**的领域，不是 chg-03 实施时偏离 OQ-4。

### 2.2 与 req-55 设计的对比

| 项 | req-55 设计 | dogfood 实测 | 偏差类型 |
|----|-----------|------------|---------|
| OQ-4 拍板 | B-modified（4 级降级 `src/modules/* → src/domains/* → app/* → src/{pkg}/*次级模块`） | 实施完全对齐 | 无偏离 |
| 风险 R-1 | "harness-workflow 自身 single-package 不适用 → 4 级降级兜底" | 兜底只对 Python single-package 友好；Java/Maven 多模块不在覆盖面 | 设计遗漏（未列 Java/Maven 风险条目） |
| 测试覆盖 | TC-07~10 4 级降级各 1 fixture + TC-11 自身仓第 4 级命中 | 全部覆盖 Python fixture，**无 Java fixture** | 测试盲点（验证范围 = 设计范围 = Python） |

**核心证据**：grep `tests/test_playbook_install.py` 等 5 个测试文件，**0 处** mention `pom.xml` / `mvn` / `Maven` / `build.gradle`。设计 + 实施 + 测试三层一致地把 Java/Maven 排除在外，是**设计层面的遗漏**而不是实施偏离。

### 2.3 同源问题（推测，未实测）

按相同模式判断，以下项目类型也会在 chg-03 推断器上失败：
- **Gradle 多模块**（`settings.gradle` 含 `include` 列表 + 顶层平级模块根）
- **Kotlin/Multiplatform**（同 Gradle）
- **.NET 多项目解决方案**（`*.sln` + 顶层 `<ProjectName>/` 平级目录）
- **Cargo workspace**（`Cargo.toml [workspace] members` + 顶层 `crates/*` 或平级）

### 2.4 修复方案候选（>= 2 条 + default-pick）

#### 候选 A1（顶层目录命名模式）

扫顶层平级目录名形如 `*-{module,common,admin,core,server,api,web,...}/` 的子目录，命中即作领域。

- 优：实现简单，零依赖，覆盖 PetMallPlatform 这类约定俗成的命名；
- 劣：依赖命名风格猜测，对不按惯例命名的 Java/Maven 项目无效。

#### 候选 A2（pom.xml `<modules>` 字段识别）— default-pick

扫顶层 `pom.xml`，正则提取 `<module>...</module>` 子项作为领域；如果是 BOM/parent pom（无 `<modules>` 但有子目录含 pom.xml），fallback 到 A3。

- 优：基于 Maven 官方契约，**精确无猜测**；与维度 B 修复同源（都扫 `pom.xml`）；
- 劣：要解析 XML（可用简单正则避免引 lxml 依赖），单模块 Maven 项目不命中需 fallback。

#### 候选 A3（Maven 标准约定扫描）

扫每个顶层目录下是否有 `pom.xml` + `src/main/java/`，命中即作领域。

- 优：覆盖未在父 pom 列 `<modules>` 的子项目（Aggregator pom 缺失场景）；
- 劣：性能稍差（需扫 N 个顶层目录），对超大仓可能变慢。

#### 候选 A4（用户配置兜底）

`harness install --domains <list>` 显式指定，自动失败时手动指定。

- 优：永远有逃生口；
- 劣：违反"开箱即用"承诺，应作为 last-resort 而非 default。

**推荐组合**：A2 主 + A3 fallback + A4 last-resort，按"5 级降级链"扩展（Level-5 = Java/Maven 多模块）。**default-pick = 组合（A2+A3+A4）**。

## 3. 维度 B 根因分析：chg-04 SCRIPTS 检测器 Maven 盲点

### 3.1 根因（L3 一句根本）

**chg-04 `_scan_scripts` 与 chg-03 推断器同源——默认 Python/JS 项目假设**；STACK detector 已经能识别 Maven（第 134-138 行抽 artifactId），但 SCRIPTS detector 没有对应 Maven 命令清单。

### 3.2 与 req-55 设计的对比

| 项 | req-55 设计 | dogfood 实测 | 偏差类型 |
|----|-----------|------------|---------|
| spec §四 AUTO:SCRIPTS 描述 | "技术栈、scripts、顶层目录树" | 实施只覆盖 pyproject scripts / npm scripts / Makefile | 设计颗粒度过粗（"scripts"未具体到语言） |
| 风险列表 | R-1~R-4，无 Maven/Gradle 风险 | 同 A 维度，与设计同源 | 设计遗漏 |
| chg-04 测试 | TC-01~03 各 1 AUTO 区段替换断言 | 全部 Python fixture，**无 Maven/Gradle** | 测试盲点 |

### 3.3 修复方案候选

#### 候选 B1（按文件类型 detector 注册化）— default-pick

把 `_scan_scripts` 改成**注册器模式**：按文件存在性分发不同 detector：
- `pom.xml` -> Maven detector（提取 lifecycle 命令 + `<plugin>` 自定义目标）
- `build.gradle` / `gradlew` -> Gradle detector
- `Cargo.toml [bin]` -> Cargo detector
- `*.csproj` / `*.sln` -> .NET detector
- 既有 pyproject / package.json / Makefile detector 不变

- 优：可扩展，未来加新语言只加一个 detector；
- 劣：实现复杂度上升（需重构 `_scan_scripts`）。

#### 候选 B2（Maven/Gradle 硬编码补丁）

直接在 `_scan_scripts` 末尾追加 if-elif 分支识别 `pom.xml` / `build.gradle`，最小改动。

- 优：改动小，立即可用；
- 劣：每加一个语言就重复 if-elif，未来可维护性差。

#### 候选 B3（LLM 调用兜底）

如果维度 C（LLM）落地，SCRIPTS 检测可让 LLM 看 README + project file 后给出常用命令清单。

- 优：覆盖任意冷门语言/工具；
- 劣：依赖 LLM provider，违反原 spec "可在 CI 跑"承诺（除非加 `--no-llm` 兼容旗）。

**推荐**：B1 + B3 组合（detector 注册化 + LLM 兜底），常见语言走 B1 静态规则，长尾走 B3 LLM。**default-pick = B1 主 + B3 兜底**。

## 4. 维度 C 根因分析：spec "不调 LLM" 决策反转

### 4.1 根因（L3 一句根本）

**原 spec 决策的合理性边界**是"CI 可重复 + 不依赖外部 API + 零成本"，**但**忽略了"对人友好性"维度——纯静态填出来的骨架 90% 是 `<!-- TODO -->`，对人不友好；用户首装期望看到有意义的初稿。

### 4.2 与 req-55 设计的对比

| 维度 | spec / requirement.md 原文 | 反转后立场 | 冲突点 |
|------|--------------------------|-----------|--------|
| 实现要点 | "不调 LLM，纯静态分析" | LLM 可选，默认调 | 直接反转 |
| Excluded | "不让脚本调 LLM" | 反转为"可让脚本可选调 LLM" | 直接反转 |
| 12 条 AC | 全部基于"静态分析"前提 | 需重写 AC（CI 模式 / LLM 模式分别验证） | AC 重构 |
| chg-04 注释 | `harness_playbook_refresh.py` 第 13 行 "不调 LLM（纯静态分析，spec §四实现要点明示）" | 注释作废 | 文档同步 |

### 4.3 不冲突的实现路径候选

#### 候选 C1（LLM 仅在首装时调用，refresh 不调）

- `harness install --playbook-only` 默认调 LLM 填初始骨架；
- CI 模式 `--no-llm` 跳过；
- `playbook-refresh` 仍纯静态（CI 兼容）。

优：保留 chg-04 CI 兼容性；劣：refresh 后内容质量未提升。

#### 候选 C2（LLM 全程可选）— default-pick

- 所有路径都支持 `--with-llm` / `--no-llm` flag；
- 默认开启（local 用户友好）；
- CI 显式关闭（保 spec 原承诺）；
- 通过 `~/.config/harness/llm.yaml` 配置 provider（OpenAI / Anthropic / Ollama 本地）。

优：用户全场景受益 + CI 兼容 + provider 可选；劣：实现复杂度最大（需 LLM provider 抽象层）。

#### 候选 C3（LLM 仅 refresh 调用，install 仍静态）

反向于 C1。

优：install 保 CI 兼容；劣：首装初稿仍是 TODO 海。

#### 候选 C4（LLM 通过新独立子命令）

新增 `harness playbook-llm-fill` 子命令，install / refresh 不动。

优：彻底隔离，零回归；劣：用户需多记一个命令，违反"首装即可用"承诺。

**推荐**：C2（全程可选 + provider 抽象 + 默认 on local / off CI）。**default-pick = C2**。

### 4.4 LLM provider 抽象层架构候选

新增 `src/harness_workflow/playbook/llm.py`：
- 抽象基类 `LLMProvider`（`generate(prompt: str) -> str`）；
- 具体实现：`AnthropicProvider` / `OpenAIProvider` / `OllamaProvider` / `NoopProvider`（CI 跳过）；
- 配置加载：`~/.config/harness/llm.yaml` 优先 -> 项目本地 `.harness/llm.yaml` -> 环境变量 -> NoopProvider 兜底；
- 提示词模板：`src/harness_workflow/playbook/prompts/` 下按章节分模板（overview / domain-readme / code-map-keywords / architecture-tech-decisions）。

## 5. 维度 D 根因分析：OQ-5 路书"只读"约束语义松动

### 5.1 根因（L3 一句根本）

**OQ-5 决策时假设"路书内容由脚本生成 + 用户偶尔手工补"**，未预见"LLM 填的内容用户经常要修"的场景；硬门禁十 §4 "不要修改任何文件"的字面义在维度 C 反转后**不再成立**。

### 5.2 现有技术现状（已天然支持区段级只读）

- chg-04 `replace_auto_section`（第 43-79 行）只替换 `<!-- AUTO:X --> ... <!-- /AUTO:X -->` 区段；
- chg-05 playbook-check AUTO 区段哈希漂移检测只检 AUTO 区段；
- 区段外人写区域天然不被脚本碰、不被 check 检 -> 已经是"区段级只读"实现。

**问题**：base-role.md 硬门禁十 §4 文字 lag——只更新文字，不动代码。

### 5.3 修复方案候选

#### 候选 D1（区段级只读，文字精修）— default-pick

- `<!-- AUTO:* -->` 区段为脚本/LLM 生成，agent 与用户均不应直接编辑（要改跑 refresh）；
- 区段外（TODO + 人写部分）用户可任意改 + agent 默认不改（安全） + 用户 explicit 在任务里说"修路书 X 章节"时 agent 才允许写。
- chg-05 playbook-check 行为不变（AUTO 区段漂移检 + 区段外不检）。

#### 候选 D2（任务级只读）

agent 默认只读，用户 explicit 任务才允许写——不分区段。

劣：与维度 C 的 LLM 填充冲突（LLM install 写的就是 AUTO 区段，但 D2 把"agent 写"全锁）。

#### 候选 D3（双面策略）

- CI 漂移检测仍兜底（chg-05 检 AUTO 区段哈希）；
- agent 改 TODO 区段不报警（区段外不锁）；
- 文字 + chg-05 行为同步细化。

实质上等于 D1 但表述更宽松，可作为 D1 的扩展说明。

**推荐 D1**（区段级只读 + 文字精修 + chg-05 行为不变），D3 作为 D1 的扩展条款。**default-pick = D1**。

## 6. 影响半径（修复体量估算）

### 6.1 文件 / 行数 / 测试用例数估算

| 修复维度 | 新增文件 | 修改文件 | 估算 LOC | 估算 TC 数 |
|---------|---------|---------|---------|----------|
| A（推断器扩 Java/Maven 多模块） | 0 | `domain_inference.py`（核心算法重构 / 5 级降级 / 探测器注册化）+ `skeleton.py`（领域命名传递） | +120~180 LOC | +5~8 TC（Maven `<modules>` / Gradle / Cargo workspace / .NET sln / 兜底） |
| B（SCRIPTS detector 注册化） | 0 | `harness_playbook_refresh.py::_scan_scripts` 重构 | +80~120 LOC | +4~6 TC（Maven lifecycle / Gradle / Cargo bin / .NET） |
| C（LLM provider 层） | `playbook/llm.py` + `playbook/prompts/*.md`（3-5 提示词模板） | `playbook/init.py` + `harness_playbook_refresh.py` 集成调用 + `cli.py` 加 `--with-llm` / `--no-llm` flag + 配置文件读取 | +200~300 LOC | +8~12 TC（provider mock / no-llm 兼容 / 配置加载 / fallback） |
| D（base-role + chg-05 兼容） | 0 | `base-role.md` 硬门禁十 §4 精修 + `harness_playbook_check.py` 注释（行为不变） | +20~40 LOC | +2~3 TC（文字 lint + 区段外允许写） |
| 文档 / spec | 0 | `playbook-layout.md`（"不调 LLM"段为"可选 LLM 填充"）+ `requirement.md` AC 重构（C 反转留 history） | +50~100 LOC | +0 TC（文档） |

**汇总**：
- **新增文件**：3-5 个（`playbook/llm.py` + 3-5 个 prompt 模板）
- **修改文件**：6-10 个（chg-03 / chg-04 / chg-05 实现 + base-role.md + spec / requirement.md + cli.py + tests/）
- **新增 TC**：19-29 条（每维度 >= 2 + dogfood TC >= 2 个）
- **总 LOC**：+470~740 LOC

### 6.2 对 req-55 已落地 5 chg 的影响

| chg | 是否需要二次改动 | 影响内容 |
|-----|-----------------|---------|
| chg-01（路书目录骨架契约） | 是（小） | `playbook-layout.md` 更新"不调 LLM"段 |
| chg-02（baseRole 代码加载规则与 CLAUDE 索引） | 是（中） | base-role.md 硬门禁十 §4 区段级只读语义 |
| chg-03（harness install 追加路书初始化） | **是（大）** | 5 级降级 + LLM 集成 + cli flag |
| chg-04（harness playbook-refresh 子命令） | **是（大）** | SCRIPTS detector 注册化 + LLM 集成 |
| chg-05（harness playbook-check 子命令） | 是（小） | 区段级只读语义注释 |

**结论**：4/5 chg 需要二次改动，且 chg-03 / chg-04 是"大改"——超出"加单一 chg 修复"的体量边界。

### 6.3 测试基线影响

- 现有 41/41 TC PASS 不应破坏，但实现重构后 **5+ TC 可能需要更新断言**（如 stdout 命中级别从 4 级扩 5 级）；
- 新增 19-29 TC，全量 TC 数会从 41 升到 ~60-70；
- dogfood TC 需新增 Java/Maven fixture（PetMallPlatform-like），并跑端到端 subprocess 验证。

## 7. 综合判断

### 7.1 维度真实性 + 严重性

- **A：真实 P0**（Java/Maven 项目主流栈不可用）
- **B：真实 P1**（功能未崩，runbook 空）
- **C：真实 P0 + spec 反转**（影响 chg-03/04 整体实现）
- **D：真实 P1 + 与 C 互锁**（语义松动需配套修订）

### 7.2 修复体量

- **3-5 新文件 + 6-10 修改文件 + 19-29 新 TC + 470-740 LOC**
- **4/5 现有 chg 需要二次改动**（chg-03 / chg-04 大改）
- **spec 重大决策反转**（"不调 LLM" -> "可选 LLM"）

### 7.3 对 req-55 baseline 的影响

- req-55 已 done verdict=PASS / 12 AC PASS / 5 OQ 拍板；
- 加 chg 会破坏 done 终局（违反 "done = terminal" 约定）；
- 维度 C 是 spec 反转，理应走 analyst 重新拆 chg（DAG 制定）；
- **结论**：体量 + 反转性质 + 多维度叠加 -> 应**转新 req（req-56）走完整 analysis**。

详见 `decision.md` 5 候选路由分析。

## 8. 经验沉淀候选（待 done 阶段回写）

### 候选 1（known-risks 新增）：路书引擎多语言项目盲点

- **场景**：路书 / 项目地图 / 代码导航类工具默认按"Python/JS 单仓"假设建模时，会在 Java/Maven 多模块 / Gradle 多模块 / .NET 多项目 / Cargo workspace 等"多模块顶层平级根"惯例上推断错误。
- **沉淀位置**：`.workflow/context/experience/risk/known-risks.md`
- **触发**：req-56（如果选 R4）落地后回写。

### 候选 2（analyst 经验）：spec 决策反转后的 reg -> req 转化模板

- **场景**：req done 后 dogfood 暴露 spec 重大决策反转 + 多维度叠加修复体量超出"加 chg"边界。
- **沉淀位置**：`.workflow/context/experience/roles/analyst.md` 或 `regression.md`
- **内容**：reg 诊断 -> R4 转新 req -> analyst 重新拆 chg DAG 引用原 req baseline + reg 触发器的标准化路径。
- **触发**：req-56 落地后回写。

### 候选 3（regression 经验）：dogfood 真实数据独立复现

- **场景**：诊断师收到用户报告的 dogfood 数据后，应在 worktree 内构造 fixture 独立复现，确认数据真实性而非盲信用户描述。
- **本 reg 实证**：在 worktree fixture 内重现 PetMallPlatform 推断 `matched 'app/*' (logs)` 输出，与用户报告完全一致。
- **沉淀位置**：`.workflow/context/experience/roles/regression.md`
- **触发**：本 reg 完成后即可沉淀（独立于 req-56 走向）。
