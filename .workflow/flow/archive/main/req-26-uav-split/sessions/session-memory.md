# Session Memory — req-26 changes_review

## 1. Current Goal

在 `changes_review` 阶段将 req-26（uav-split）拆分为独立可交付的 changes，每个 change 产出 `change.md` + `plan.md`，不执行实施。

## 2. Context Chain

- Level 0: 主 agent（technical-director）→ changes_review
- Level 1: Subagent-L1（planning 角色，本 session）→ 拆分 req-26

## 3. Completed Tasks

- [x] 按 role-loading-protocol 完成前置加载（runtime.yaml、tools/index.md、project-overview.md、context/index.md、base-role.md、stage-role.md、planning.md）
- [x] 读取 req-26 requirement.md（AC-01~AC-07）
- [x] 执行 6 次 `harness change --requirement req-26`，创建 chg-01 ~ chg-06 骨架
- [x] 按 AC 范围填充所有 change.md（Title / Goal / Scope / Acceptance / Risks）
- [x] 按 plan-to-execute 粒度填充所有 plan.md（开发步骤 / 验证步骤 / 依赖顺序）
- [x] chg-05 的 plan.md 给出对人文档最小字段模板定稿

## 4. Results

### 4.1 最终拆分方案（6 个 change）

| Change | 标题（短） | 覆盖 AC | 与建议方案的差异 |
|--------|-----------|---------|----------------|
| chg-01 | harness regression 命令簇 | AC-01 + AC-04 | 按建议合并，不再拆开 |
| chg-02 | harness rename 保留前缀 + 同步 yaml | AC-02 | 无差异 |
| chg-03 | harness next 写回 stage yaml | AC-03 | 无差异 |
| chg-04 | harness archive 双层 branch | AC-05 | 无差异 |
| chg-05 | 各角色双轨对人文档 SOP + 模板 | AC-06 | 无差异；作为最重的一个 change |
| chg-06 | 端到端 smoke | AC-07 | 无差异；放最后 |

### 4.2 拆分方案说明

- **维持建议方案，未做调整**。理由：
  1. AC-01 与 AC-04 都在 regression CLI 命令簇内，共享入口代码与回归用例脚手架，合并后便于一次性修完与回归，避免同一命令簇改两次的风险；
  2. AC-02 / AC-03 / AC-05 是独立命令（rename / next / archive），各自独立成 change；
  3. AC-06 是纯文档 / SOP 类变更，不涉及 CLI 代码，单独成 chg-05，防止与代码 change 混合污染；
  4. AC-07 端到端 smoke 依赖前 5 个 change 合入，天然是压轴 change。

### 4.3 关键设计决策

- **chg-05 不改任何 harness CLI 代码**：对人文档由 agent 在各 stage 执行阶段写入，不走 CLI 生成。此决策来自 req-26 requirement.md Excluded 条款与 chg-05 plan.md 1.1 先行原则。
- **chg-05 双写目标**：`.workflow/context/roles/` + `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/`，两棵树必须一致。
- **chg-05 对人文档最小字段模板**已在 plan.md 1.4 节定稿，给出 7 份模板（需求摘要/变更简报/实施说明/测试结论/验收摘要/回归简报/交付总结）。
- **chg-01 与 chg-02 共享 slug util**：两者都需要 kebab-case 规范化函数，建议 executing 阶段协调接口。

### 4.4 CLI 行为观察（重要）

- `harness change --requirement req-26` 运行 6 次均成功，但：
  - **产出位置**：`artifacts/main/requirements/req-26-uav-split/changes/` 而非 `.workflow/flow/`。用户已在 briefing 中说明"照现状用，不要手修 CLI"，此为 req-26 后续迭代的工作。
  - **目录命名**：携带 `chg-XX-` 前缀，但 title 中的空格 / 中文冒号未做 kebab-case 转换，导致目录名里有空格与中文标点。这正是 AC-04 类缺陷在 change 层的体现（AC-04 只针对 regression 目录）。本 planning 阶段未主动修复，按"照现状用"原则处理。
  - **模板内容**：生成的 change.md 带英文 placeholder（"Describe what is included"），plan.md 极简（只有 "Add implementation steps here"），需要本角色手工改写为中文完整版，已完成。
- 结论：`harness change` 行为未报错，但产出质量低，形成下游负担。建议主 agent 在 req-26 后续需求中考虑增强 change scaffold（独立于 req-26 范围）。

## 5. Next Steps

- 主 agent 审阅本 session-memory 与 6 个 change.md / plan.md；
- 主 agent 决定是否进入 changes_review 的确认环节，然后 `harness next` 推进到 executing；
- 不由 subagent 跑 `harness next`（按 briefing 约束）。

## 6. 待处理捕获问题

- （潜在）`harness change` 目录命名未做 kebab-case 转换，与 req-26 所要修的 AC-04（针对 regression 目录）属同类问题但范围不同。建议在 req-26 后续迭代 / 新需求中纳入 `harness change` 的命名规整。本 session 不自作主张登记 suggestion，留给主 agent 决策。
- （潜在）scaffold 生成的 change.md / plan.md 模板极简且英文，影响双轨对人文档写作效率。同上，建议后续单独 change 处理。

## 7. 上下文消耗评估

- 本 session 为典型 planning 产出，读取约 10 个角色 / 状态 / 需求文件，写入 12 份 markdown，估计消耗 ≤ 30% 上下文窗口，远低于 70% 评估阈值，无需 /compact 或 /clear。

## 8. 修订记录

### 8.1 2026-04-19 — 并入两条待评估问题（B / C），不新开 change、不新增 AC

用户在首轮 changes_review 结束后，把本 session 上报的"两条潜在问题"（见第 6 节）拍板并入现有 change：

- **B → 并入 chg-02**：`harness change` 生成目录未做 kebab-case 清洗（空格、中文冒号），与 sug-04 对 regression 目录的规范分裂。本轮把该缺陷作为 chg-02 **Scope 与 Acceptance 的内部扩展**：
  - `change.md` Title 改为"修 `harness rename` 并统一 CLI 产出目录命名规范（`rename` + `change` 共用 slugify）"；
  - `change.md` Scope Included 追加"`harness change` 目录 kebab-case 清洗"；Acceptance 在 AC-02 下追加隐含命名规范条（不新增独立 AC）；
  - `plan.md` 新增 Step 3 "修 `harness change` 的目录命名逻辑"，并新增 Step 6 change CLI 测试子节与 2.2.2 手工 smoke；涉及文件清单追加 `workflow_helpers.py:create_change()`（line 3345，bug 点在 line 3370 `dir_name = f"{chg_num_id}-{change_title}"`）与共享 util `slugify()`（line 2152）；
  - **不改 sug-04 对 regression 的修法**，仅在 util 层与 chg-01 的 regression 链路共享 `slugify` / 新增的 `sanitize_artifact_dirname()`。

- **C → 并入 chg-05**：scaffold_v2 角色文件与 `harness change` 生成的 change.md / plan.md 模板由英文极简 / 中文极简升级为中文完整版。本轮把该事项作为 chg-05 **Scope 与 Acceptance 的内部扩展**：
  - `change.md` Title 追加"+ scaffold_v2 / change 模板同步中文化"；Scope Included 追加"`harness change` 模板中文完整化（change.md.tmpl / change-plan.md.tmpl 及 .en 镜像）"；Acceptance 在 AC-06 契约 1 下追加两条隐含扩展（不新增独立 AC）；
  - `plan.md` 新增 1.6 扩写 `harness change` 模板、1.7 同步 scaffold_v2 镜像、2.2 `harness install` 集成验证、2.3 `harness change` 模板验证；
  - 模板实际位置为 `src/harness_workflow/assets/skill/assets/templates/change.md.tmpl`（及 `change-plan.md.tmpl`、对应 `.en.tmpl`），由 `workflow_helpers.py:create_change()` 通过 `render_template()` 读取。

### 8.2 合并理由（用户已确认）

- **不新增 change**：两条问题本质上分别是 chg-02（AC-02）与 chg-05（AC-06）的自然子集，拆独立 change 会让 req-26 从 6 个膨胀到 8 个，且 executing 阶段对同一批文件（`workflow_helpers.py` / scaffold_v2）产生并发冲突。
- **不新增 AC**：AC-02 原文即"目录名保留 id 前缀"，其语义隐含"目录名命名规范"，本次只是把命名规范的覆盖范围从 regression 扩到 change；AC-06 契约 1"双轨机制"隐含要求上下游（scaffold_v2）与 CLI 生成物（change 模板）风格一致，属契约 1 的落地细节。
- **对应 AC 未动**：requirement.md 的 AC-02 / AC-06 文本本轮**零修改**。

### 8.3 源码实现路径核查（无意外）

- `harness change` CLI 路径如预期可定位：
  - CLI 入口 `src/harness_workflow/tools/harness_change.py`（31 行，仅做参数转发）；
  - 核心实现 `src/harness_workflow/workflow_helpers.py:create_change()`（line 3345~3388）；
  - Bug 点 line 3370 `dir_name = f"{chg_num_id}-{change_title}"`，直接拼接原始 title 未 slugify；
  - 共享 util `slugify()` 已存在（line 2152），regression 命令簇的 `resolve_title_and_id()`（line 2170）也在同文件；本 change 可直接复用或在其基础上新增 `sanitize_artifact_dirname()`。
- `harness change` 模板路径也如预期：`src/harness_workflow/assets/skill/assets/templates/change.md.tmpl` 与 `change-plan.md.tmpl`，另有 `.en.tmpl` 英文镜像。读出当前内容：中文版是 5-6 节的"极简中文"，英文版是与 session-memory 第 4.4 节记录一致的 "Describe what is included" / "Add implementation steps here" 英文 placeholder。

### 8.4 本轮动作边界

- 仅修改 4 份文件：chg-02 的 change.md / plan.md、chg-05 的 change.md / plan.md；
- 追加本节（第 8 节）到 session-memory；
- **未** 修改 requirement.md；
- **未** 跑 `harness next` 或任何 stage 推进命令；
- **未** 触碰生产代码或模板文件本身（仅在 plan 文档中描述如何改）。
