---
id: reg-01
title: "chg-03/04 Java/Maven项目盲点 + LLM填骨架决策反转"
created_at: 2026-04-30
operation_type: regression
stage: regression
route_to: "requirement"
linked_requirement: req-55
proposed_new_requirement: "req-56（路书引擎升级——Java/Maven 多模块 + LLM 内容填充 + 区段级只读）"
---

> 关联：req-55（项目路书Playbook体系——项目地图+代码导航）/ chg-03（harness install 追加路书初始化）/ chg-04（harness playbook-refresh 子命令）。

## 1. Status

- **analysis -> 待用户拍板 confirm**（建议路由 = R4 转新 req）

## 2. 5 候选路由分析

### 候选 R1（单 reg 修：`harness regression --confirm` + 直接派 executing 修）

- **适用**：体量小，一个 reg 内能改完（如仅修 chg-03 Java 模式 + 不动 LLM 反转）。
- **不适用本 reg**：4 维度叠加 + spec 反转，体量太大（19-29 新 TC + 470-740 LOC + 4/5 现有 chg 二次改动）。
- **判定**：**reject**。

### 候选 R2（拆多 reg：`--confirm` + 后续多个 `harness regression` 平行做）

- **适用**：4 维度互独立可平行。
- **不适用本 reg**：维度 A/B 同源（推断器 / detector 都默认 Python/JS 假设），C/D 互锁（LLM 反转 + 区段级只读语义同步），平行难。
- **判定**：**reject**。

### 候选 R3（转新 chg：`harness regression --change "<title>"` 转到 req-55 下新 chg-06+）

- **适用**：req-55 还没 archive，可以加 chg。
- **不适用本 reg**：
  1. req-55 已 done verdict=PASS / 12 AC PASS / 5 OQ 拍板，加 chg 会**破坏 done 终局**（违反 stage_policies "done = terminal"）；
  2. 4 维度涉及 spec "不调 LLM" 反转 + 既有 chg-02/03/04/05 全部需要二次改动，**超出"加 chg"范围**（chg 单位是"小变更"，不承担 spec 反转 + 多维度重写）；
  3. 维度 C 的 spec 反转应该走 analyst 重新拆 chg（不是 executing 拿一个 chg 头铁干）。
- **判定**：**reject**。

### 候选 R4（转新 req：`harness regression --requirement "<title>"` 转 req-56）— **推荐**

- **适用**：spec 反转 + 多维度修复 + 大量重写，开新 req 走完整 analysis 拆分清晰。
- **推荐理由**：
  1. **spec 反转性质**："不调 LLM" -> "可选 LLM"是 spec 重大决策变更，应该走 analyst 重新拆 chg（DAG 制定）；
  2. **4 维度需要 DAG**：A（推断器扩 Java/Maven）/ B（SCRIPTS detector 注册化）/ C（LLM provider 层）/ D（区段级只读）需要 analyst 制定单向依赖 DAG，不是 executing 头铁推；
  3. **保护 req-55 done 终局**：req-55 已 done verdict=PASS，新 req-56 引用 req-55 作为 **baseline** + reg-01 作为 **触发器**，保留 req-55 的 done commit + acceptance verdict 不被破坏；
  4. **修复体量匹配 req 粒度**：3-5 新文件 + 6-10 修改文件 + 19-29 新 TC + 470-740 LOC，符合 req 体量（chg 是 0.5-1 day，req 是多 chg / 多 day）；
  5. **dogfood 触发模板沉淀**：reg-01 -> req-56 是 spec 反转后的标准化路径，可作为 analyst 经验沉淀样本（详见 analysis.md §8 候选 2）。
- **判定**：**推荐**。

### 候选 R5（reject：`harness regression --reject`）

- **适用**：判定 dogfood 错配是用户使用不当 / 非真实问题。
- **不适用本 reg**：
  - dogfood 在 PetMallPlatform 真实项目上确认产品**对 Java/Maven 主流栈不可用**（推断错领域 + SCRIPTS 空），是产品能力缺口；
  - 用户基于真实 dogfood 反转 spec 决策，是**用户决策权**而不是用户使用不当；
  - 独立复现验证通过（在 worktree fixture 内 `matched 'app/*' (logs, temp)` 与用户报告完全一致）。
- **判定**：**reject**。

## 3. 最终路由建议

### 路由 = **R4（转新 req）**

**新 req 标题草案**：
```
req-56：路书引擎升级——Java/Maven 多模块 + LLM 内容填充 + 区段级只读
```

**新 req 与 req-55 的关系**：
- **baseline**：req-55 5 chg 已落地的契约 / 实现 / 测试作为 req-56 的起点（不重写，只扩展 / 修订）；
- **触发器**：reg-01 dogfood 真实证据 + 4 维度根因分析 + 影响半径估算（见 `regression.md` / `analysis.md`）作为 req-56 spec 输入；
- **不动**：req-55 的 done commit / acceptance verdict / 12 AC / 5 OQ 决策记录（保留 history）；
- **新增**：req-56 自身的 spec / requirement.md / 4-6 chg DAG / acceptance verdict。

## 4. 新 req-56 chg DAG 草案（>= 3 chg + 推荐 5 chg）

```
chg-01（推断器扩 Java/Maven 多模块 + 5 级降级）
   |
   +-- 新增 Level-5: pom.xml <modules> 字段识别（A2 default-pick）
   +-- fallback Level-5b: 顶层目录扫 pom.xml + src/main/java/（A3 fallback）
   +-- last-resort: harness install --domains <list> 显式指定（A4）
   +-- 同步覆盖 Gradle multi-module / Cargo workspace / .NET sln（推测同源）
   +-- pytest +5~8 TC（含 PetMallPlatform-like fixture）

chg-02（SCRIPTS detector 注册化 + Maven/Gradle/Cargo/.NET 命令支持）
   |
   +-- _scan_scripts 重构为按文件类型注册器分发
   +-- Maven detector: 提取 lifecycle 命令 + <plugin> 自定义目标
   +-- Gradle / Cargo / .NET detector
   +-- pytest +4~6 TC

chg-03（LLM provider 抽象层 + install / refresh 集成）
   |
   +-- 新增 src/harness_workflow/playbook/llm.py（LLMProvider 抽象基类）
   +-- 4 个具体 provider：Anthropic / OpenAI / Ollama / Noop（CI 跳过）
   +-- 配置加载：~/.config/harness/llm.yaml -> .harness/llm.yaml -> env -> Noop
   +-- 提示词模板：src/harness_workflow/playbook/prompts/*.md（3-5 模板）
   +-- cli flag：--with-llm / --no-llm（默认 on local / off CI 通过 env CI=true 自动）
   +-- pytest +8~12 TC

chg-04（base-role.md 硬门禁十 §4 区段级只读语义 + chg-05 兼容）
   |
   +-- 硬门禁十 §4 文字精修：AUTO 区段只读 + 区段外可改 + agent 默认不改 + 用户 explicit 后可改
   +-- chg-05 playbook-check 注释更新（行为不变）
   +-- pytest +2~3 TC（文字 lint + 区段外允许写）

chg-05（spec / requirement.md / playbook-layout.md "不调 LLM" 反转留 history）
   |
   +-- playbook-layout.md "不调 LLM" 段更新为"可选 LLM 填充"
   +-- inputs/initial-spec.md 不改写（只读，留 history）
   +-- requirement.md AC 重构（CI 模式 / LLM 模式分别验证）
   +-- README / SKILL.md 文档同步
   +-- pytest +0 TC（文档）
```

**chg DAG 单向依赖**：

```
chg-01（推断器 5 级降级） ─┐
                          ├──> chg-04（区段级只读语义） ──> chg-05（spec 反转留 history）
chg-02（SCRIPTS 注册化） ─┘                                       ↑
                                                                   |
chg-03（LLM provider 抽象） ──────────────────────────────────────┘
```

- chg-01 / chg-02 / chg-03 可并行；
- chg-04 等 chg-01/02/03 落地后再做（区段级语义需要先有 LLM 与 detector 实现）；
- chg-05 最后做（spec 文档同步）。

**估算总量**：5 chg / 6-8 day（线性）/ 4 day（chg-01/02/03 并行）。

## 5. 5 OQ 候选（待 analyst stage 拍板）

新 req-56 analyst stage 应处理以下 5 OQ：

- **OQ-1（推断器 5 级降级 vs 注册器重构）**：A1（5 级降级硬编码）/ B1（注册器架构）。default-pick = B1（与 chg-04 SCRIPTS 注册化同源，未来加新语言低成本）。
- **OQ-2（LLM 调用范围）**：C1（仅 install）/ C2（全程可选）/ C3（仅 refresh）/ C4（独立子命令）。default-pick = C2（用户全场景受益 + CI 兼容）。
- **OQ-3（LLM provider 默认）**：Anthropic / OpenAI / Ollama / 自动检测。default-pick = 自动检测（按 env API key 顺序探测，无 key 则 Noop）。
- **OQ-4（区段级只读 vs 任务级只读）**：D1（区段级）/ D2（任务级）/ D3（双面策略）。default-pick = D1（与现有技术现状对齐）。
- **OQ-5（dogfood TC 是否在 worktree 内跑 PetMallPlatform fixture vs 真实 PetMallPlatform）**：A（worktree fixture 模拟）/ B（真实 PetMallPlatform A/B 测试）。default-pick = A（不离开 worktree，符合本 reg 不离开 worktree 约束；真实 A/B 测试由主 agent 在路由后另起任务做）。

## 6. 给主 agent 的下一步行动指令

### 6.1 立即行动（reg 完成汇报后）

1. **派发 harness-manager 解析 reg-01 路由结果**：route_to = "requirement"，触发 `harness regression --requirement "路书引擎升级——Java/Maven 多模块 + LLM 内容填充 + 区段级只读"`；
2. **harness CLI 自动行为**（基于 reg-01 路由 = requirement）：
   - `runtime.yaml` 写入 `current_requirement: req-56`，`stage: analysis`；
   - 创建 `.workflow/flow/requirements/req-56-路书引擎升级-java-maven-llm内容填充-区段级只读/`（slug 由 CLI 按 slugify_preserve_unicode 生成）；
   - 在 req-56 的 inputs 目录引用 reg-01 作为 trigger reference（链接 regression.md / analysis.md）；
3. **派发 analyst（opus）执行 req-56 analysis stage**：
   - 输入：reg-01 全部 3 份机器型工件 + req-55 baseline（5 chg 已落地实现）+ initial spec history；
   - 任务：写 req-56 requirement.md（Goal / Scope / 12+ AC / Split Rules）+ 5 chg DAG + 5 OQ default-pick；
   - 期望产出：req-56 stage 推到 analysis 等用户拍板。

### 6.2 不要做的事

- **不要直接派 executing**：spec 反转必须走 analyst stage，不能跳过；
- **不要修改 req-55 已落地代码 / 契约 / 测试**：req-55 已 done verdict=PASS，保护 baseline；
- **不要修改 req-55 inputs/initial-spec.md / requirement.md / test-report.md / acceptance/checklist.md**：req-55 历史只读；
- **不要在 reg-01 stage 修代码**：诊断师只诊断 + 路由，不直接改代码；
- **不要去 PetMallPlatform 跑命令**（dogfood A/B 测试由主 agent 决定路由后做）；
- **不要切换 git 分支或离开 worktree**。

### 6.3 上下文消耗评估

- 本次 reg 诊断：读 ~12 文件（含 base-role.md / regression.md role / spec / 5 chg 契约 + 实现 + 测试 + req-55 session-memory + 既有 reg 经验）；
- grep + dogfood subprocess ~5 次；
- 估算消耗 < 30%（远低于 70% 阈值，无需 compact / clear）；
- 无待处理职责外问题。

## 7. Conclusion

- [x] **真实问题确认**：4 维度均为真实产品缺口（独立复现 dogfood 数据通过）。
- [x] **路由方向确定**：R4（转新 req-56）。
- [x] **新 req-56 标题 + chg DAG 草案** 已落地。
- [x] **5 OQ 候选 + default-pick** 已列（待 analyst stage 拍板）。
- [x] **下一步行动指令** 已给主 agent。
- [ ] **路由执行**：等用户对 R4 路由建议拍板（默认推进，按硬门禁四 default-pick；豁免清单不触发，无数据丢失/不可回滚/合规风险）。
