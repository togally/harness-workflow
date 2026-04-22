# Change Plan

## 1. Development Steps

### 1.1 先行确认原则（写入实现前必读）

- 本 change **不改任何 harness CLI 代码逻辑**；所有产出都是 markdown / 模板（`*.tmpl`）文件。
- 同一份角色 / stage-role 改动必须在两处落盘：
  - `.workflow/context/roles/...`（本仓库当前生效）
  - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/...`（新仓库 install 后生效）
- `harness change` 模板改动落在 `src/harness_workflow/assets/skill/assets/templates/`（由 `render_template()` 读取），scaffold_v2 若另有镜像模板路径，一并同步（见 1.7）。
- 硬禁项：
  - 禁止从 `.workflow/flow/` 搬任何现存文件到 `artifacts/`；
  - 禁止清洗 `artifacts/bugfixes/bugfix-2/`、`artifacts/main/bugfixes/bugfix-{3,4,5}/` 下的历史脏数据；
  - 禁止在 stage-role.md 或角色文件中留任何"可选 / 建议"表述，所有"对人文档"产出都是硬退出条件。

### 1.2 在 stage-role.md 中新增"对人文档输出契约"

在 `.workflow/context/roles/stage-role.md` 末尾、"流转规则"之前，新增完整章节：

```
## 对人文档输出契约（req-26 / sug-06）

### 契约 1：双轨不迁移
- `.workflow/flow/`、`.workflow/state/` 下现存的所有 agent 过程文档（requirement.md / change.md / plan.md / session-memory.md / regression/diagnosis.md / required-inputs.md / done-report.md 等）维持原路径，不得移动、删除、重写。
- 对人文档是**新增**输出，不是对现存文档的替换。

### 契约 2：路径同构
每个 stage 角色新产出的对人文档必须落到 `artifacts/{branch}/...` 下，与制品树同构：
- 需求级：`artifacts/{branch}/requirements/{req-id}-{slug}/`
- 变更级：`artifacts/{branch}/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/`
- Bugfix 级：`artifacts/{branch}/bugfixes/{bugfix-id}-{slug}/`
- Regression 级：`artifacts/{branch}/requirements/{req-id}-{slug}/regressions/{reg-id}-{slug}/`
  （如 regression 属于 bugfix，路径相应落在 bugfix 子树下）

### 契约 3：中文命名 + 阶段粒度
| 阶段 | 文件名 | 粒度 | 产出角色 |
|------|-------|------|---------|
| requirement_review | 需求摘要.md | req | 需求分析师 |
| planning | 变更简报.md | change | 架构师 |
| executing | 实施说明.md | change | 开发者 |
| testing | 测试结论.md | req | 测试工程师 |
| acceptance | 验收摘要.md | req | 验收官 |
| regression | 回归简报.md | regression | 诊断师 |
| done | 交付总结.md | req | 主 agent（done） |

（命名本身不得变更；planning 阶段可在不偏离契约 1/2 的前提下微调表述措辞。）

### 契约 4：硬门禁
- 每个 stage 角色的"退出条件"清单中必须包含："对人文档已产出且字段完整"。
- 每份对人文档必须 ≤ 1 页（屏幕一屏内读完），字段按各角色文件中的最小模板执行。
- 禁止把对人文档写到 `.workflow/flow/` 或其他位置；禁止用过程文档替代。

### 契约 5：反例核对
实施后必须能在 diff 中逐条证明：
- 未触碰 `.workflow/flow/` 下现存文档；
- 未触碰 `artifacts/bugfixes/bugfix-2/`、`artifacts/main/bugfixes/bugfix-{3,4,5}/` 下历史脏数据。
```

同步写入 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md`。

### 1.3 为 7 个角色文件追加对人文档 SOP

对每个角色文件在"退出条件"前插入 / 追加一节 `## 对人文档输出（req-26）`，内容包含：

1. **产出文件名与路径**（固定，不得改）；
2. **最小字段模板**（1.4 节复制进去）；
3. **退出条件补丁**：在原有"## 退出条件"清单末尾追加一条 `- [ ] 对人文档 {文件名}.md 已在 {路径} 产出，字段完整`。

涉及文件（每个都同时改两处：`.workflow/context/roles/` 和 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/`）：

- `requirement-review.md`
- `planning.md`
- `executing.md`
- `testing.md`
- `acceptance.md`
- `regression.md`
- `done.md`

### 1.4 对人文档最小字段模板（定稿）

以下模板由各角色文件直接嵌入 Markdown 代码块，**agent 在写对人文档时必须按此字段顺序与字段名产出**。每个模板目标 ≤ 1 页、≤ 6 字段。

#### requirement_review → 需求摘要.md（req 级）

```markdown
# 需求摘要：{req-id} {title}

## 目标
- 一句话描述本需求要解决的问题。

## 范围
- 3-5 条列出包含什么、不做什么。

## 验收要点
- 3-5 条引用 AC 编号，描述用户侧可观察的判定条件。

## 风险
- ≤ 2 条，聚焦最可能阻塞交付的点。
```

#### planning → 变更简报.md（change 级，每个 change 一份）

```markdown
# 变更简报：{chg-id} {title}

## 变更名
- 一句话自我介绍。

## 解决什么问题
- 关联上层 AC 编号 + 一句话问题描述。

## 怎么做
- 3-5 条实施要点（不是详细步骤，是决策摘要）。

## 影响范围
- 列涉及的主要文件 / 命令 / 用户路径。

## 预期验证
- 3-5 条用户可自行核对的断言。
```

#### executing → 实施说明.md（change 级，每个 change 一份）

```markdown
# 实施说明：{chg-id} {title}

## 实际做了什么
- 3-5 条交付摘要，对应 plan.md 的步骤编号。

## 未做与原因
- 列出 plan 中未执行的步骤及原因；若无，写"无"。

## 关键文件变更
- 列出主要改动文件路径及一句话说明。

## 已知限制
- ≤ 2 条遗留问题或边界条件。
```

#### testing → 测试结论.md（req 级，每个 req 一份）

```markdown
# 测试结论：{req-id} {title}

## 通过/失败统计
- 用例总数 / 通过 / 失败 / 跳过。

## 关键失败根因
- 列失败用例的根因分类（若全通过，写"无"）。

## 未覆盖场景
- 3-5 条明确未覆盖的场景。

## 风险评估
- 1-2 句总体风险判定（可上线 / 需改进 / 阻塞）。
```

#### acceptance → 验收摘要.md（req 级，每个 req 一份）

```markdown
# 验收摘要：{req-id} {title}

## AC 核对结果
- 表格：AC 编号 | 通过 | 证据 / 备注

## 是否通过
- 一句话判定 + 建议动作（归档 / 回归 / 延期）。

## 未达项处理建议
- 列未通过的 AC，给出明确下一步（谁做、预期完成时间）。
```

#### regression → 回归简报.md（regression 级，每次 regression 一份）

```markdown
# 回归简报：{reg-id} {issue}

## 问题
- 一句话描述用户感知到的问题。

## 根因
- 一句话描述独立诊断后的根因。

## 影响
- 列受影响的需求 / 变更 / 命令。

## 路由决策
- 决定回到哪个 stage 继续（requirement_review / planning / executing / testing / acceptance / 确认无需回退）。
```

#### done → 交付总结.md（req 级，每个 req 一份）

```markdown
# 交付总结：{req-id} {title}

## 需求是什么
- 一句话回顾原始需求。

## 交付了什么
- 3-5 条列出实际交付的 change / bugfix / 文档产物。

## 结果是什么
- 验收是否通过 / 有无遗留 / 影响面。

## 后续建议
- ≤ 3 条，指向下一步改进或新需求线索。
```

### 1.5 同步下游角色模板

- 对 1.2、1.3 的每一处改动，在 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` 下同名文件**一比一**同步。
- 实施完成后用 `diff -r .workflow/context/roles src/harness_workflow/assets/scaffold_v2/.workflow/context/roles` 验证两棵树在对人文档相关段落上一致（无漂移）。

### 1.6 扩写 `harness change` 的 change.md / plan.md 模板（本轮并入）

#### 1.6.1 定位模板位置

- 模板被 `create_change()`（`src/harness_workflow/workflow_helpers.py:3345`）通过 `render_template("change.md.tmpl", ...)` 与 `render_template("change-plan.md.tmpl", ...)` 读取。
- 实际文件位置：
  - 中文：`src/harness_workflow/assets/skill/assets/templates/change.md.tmpl` / `change-plan.md.tmpl`
  - 英文：`src/harness_workflow/assets/skill/assets/templates/change.md.en.tmpl` / `change-plan.md.en.tmpl`
- 定位方式（executing 阶段再核一次）：`Grep "# Change"` 或 `Grep "change.md.tmpl"` 在 `src/` 范围下搜索；若 scaffold_v2 或 archive 目录另有镜像模板，按 1.7 处理。

#### 1.6.2 中文模板字段（与本 req-26 在用的 change.md 对齐）

`change.md.tmpl` 升级为包含以下必备节的中文完整版（每节均带一行 `<!-- 示例：... -->` 类型的填写提示，规避"原样提交占位符"风险）：

```
# Change

## 1. Title
{{TITLE}}

## 2. Goal
- 一句话说明这个 change 要解决的单一功能点 / 缺陷点。

## 3. Requirement
- `{{REQUIREMENT_ID}}`

## 4. Scope
### Included
- …

### Excluded
- …

## 5. Acceptance
- 覆盖 requirement.md 的 **AC-XX**：…

## 6. Risks
- …
```

`change-plan.md.tmpl` 升级为包含以下必备节的中文完整版：

```
# Change Plan

## 1. Development Steps
### Step 1：…
- …

## 2. Verification Steps
### 2.1 单元测试 / 静态核对
- …

### 2.2 手工 smoke / 集成验证
- …

### 2.3 AC 映射
- AC-XX → Step X + 2.X；

## 3. 依赖与执行顺序
- …
```

#### 1.6.3 英文版同步升级

- `change.md.en.tmpl` / `change-plan.md.en.tmpl` 同步升级为**字段结构对称**的英文完整版（Title / Goal / Requirement / Scope / Acceptance / Risks，Development Steps / Verification Steps / AC Mapping / Dependencies），避免语言切换时规模断裂；措辞保持英文，占位提示换成英文。

### 1.7 同步 scaffold_v2 / 其他路径下的同名模板

- 检查 `src/harness_workflow/assets/scaffold_v2/` 下是否存在同名模板镜像（若有，同步替换为 1.6 的新内容）；
- 检查 archive 目录下是否仍在被引用（通常不会）；
- 目标：任一路径下 `harness install` 或 `harness change` 产出的 change.md / plan.md 都走新版模板，风格一致。

### 1.8 反例核对（实施时必做）

在实施完成前执行：

- `git status` / `git diff --stat` 确认：
  - 未有任何 `.workflow/flow/**` 下现存文件被修改；
  - 未有任何 `artifacts/bugfixes/bugfix-2/**`、`artifacts/main/bugfixes/bugfix-{3,4,5}/**` 下文件被修改；
  - 改动仅落在：`.workflow/context/roles/`、`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/`、`src/harness_workflow/assets/skill/assets/templates/change*.tmpl`（及 scaffold_v2 镜像，若有）。
- 如 diff 里出现禁止路径，立即停止并报告主 agent。

## 2. Verification Steps

### 2.1 静态核对

- `diff -r .workflow/context/roles src/harness_workflow/assets/scaffold_v2/.workflow/context/roles` → 两棵树在对人文档相关段落一致；
- 各角色文件的"退出条件"清单都能搜到"对人文档 {文件名}.md 已产出"条目；
- stage-role.md 中"对人文档输出契约"五节完整（契约 1~5）；
- `change.md.tmpl` / `change-plan.md.tmpl`（及 `.en.tmpl`）与 1.6.2 / 1.6.3 定义的字段结构一致。

### 2.2 `harness install` 集成验证（本轮新增）

- 在临时目录 `/tmp/harness-install-smoke-req26/` 跑 `harness install`；
- 对比新仓库 `.workflow/context/roles/` 与本仓库 `.workflow/context/roles/` 下 7 个角色文件 + `stage-role.md`，断言文本一致（可用 `diff -r` 验证）；
- 额外断言：新仓库 `.workflow/context/roles/stage-role.md` 中"对人文档输出契约"章节存在且完整。

### 2.3 `harness change` 模板验证（本轮新增）

- 在上一步的临时仓库里，先 `harness requirement "smoke-req26"`，再 `harness change "smoke chg"`；
- 打开生成的 `change.md`，断言存在 `## 1. Title` / `## 2. Goal` / `## 3. Requirement` / `## 4. Scope` / `## 5. Acceptance` / `## 6. Risks` 六个章节；
- 打开生成的 `plan.md`，断言存在 `## 1. Development Steps` / `## 2. Verification Steps` / `## 3. 依赖与执行顺序` 三个章节；
- 切换语言配置到 `en` 后重复一次，断言英文版字段结构对称。

### 2.4 工作流 smoke（集成验证，放在 chg-06）

- 在 chg-06 端到端 smoke 中，每跑完一个 stage，核对对应路径下生成了正确命名、字段完整的对人文档。
- 本 change 不负责 smoke 执行（放在 chg-06），但提供判定清单。

### 2.5 AC 映射

- AC-06 契约 1 → 1.1 + 1.8 反例核对；
- AC-06 契约 2 → 1.2 契约 2 表格；
- AC-06 契约 3 → 1.2 契约 3 + 1.4 模板；
- AC-06 反例核对 → 1.8 + 2.1 静态核对；
- AC-06 契约 1 隐含扩展（中文完整模板 + scaffold 同步）→ 1.5 + 1.6 + 1.7 + 2.2 + 2.3。

## 3. 依赖与执行顺序

- 本 change 与 chg-01 / 02 / 03 / 04 彼此独立，可并行实施。
- 但对 chg-06 而言，本 change 是前置：chg-06 的 smoke 要验证每个 stage 都产出对人文档，必须先合入本 change。
- 建议 executing 顺序：本 change → chg-06。
- 本 change 内部改动顺序建议：1.2（stage-role.md 契约）→ 1.3（各角色 SOP）→ 1.5（scaffold 角色同步）→ 1.6（change 模板中文完整化）→ 1.7（scaffold 镜像模板同步，如有）→ 1.8（反例核对）。
