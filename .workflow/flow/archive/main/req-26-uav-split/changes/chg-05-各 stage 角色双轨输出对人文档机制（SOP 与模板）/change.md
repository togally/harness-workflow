# Change

## 1. Title

各 stage 角色双轨输出：对人文档 SOP 与最小字段模板（AC-06 核心） + scaffold_v2 / change 模板同步中文化

## 2. Goal

在**不迁移任何现存 agent 过程文档**的前提下，为 7 个 stage 角色（requirement_review / planning / executing / testing / acceptance / regression / done）建立"对人文档"双轨输出机制。每个 stage 角色在完成自身业务后，除既有 agent 过程产物外，额外按统一契约产出一份面向用户的精炼中文文档，落到 `artifacts/{branch}/...` 同构路径下。

同时顺手做两件配套同步，保证"双轨对人文档"落地后**上下游文件风格一致**：

1. `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` 下的角色文件与本 change 对 `.workflow/context/roles/` 的中文化 / 双轨 SOP 扩充保持一致，避免 `harness install` 到下游仓库后"本地新、下游旧"；
2. `harness change` 生成的 change.md / plan.md 模板也由英文极简版（或中文极简版）升级为中文完整版（含 Title / Goal / Scope / Out-of-Scope / Acceptance / Risks 等必备节），与本 change 新增的对人文档模板风格对齐——让架构师下一次用 `harness change` 时，拿到的就是本 req-26 这样的完整骨架，而不是 "Describe what is included" 这种 placeholder。

本 change 是 req-26 中体量最大、影响面最广的机制类变更，不改任何 harness CLI 行为（对人文档由 agent 在执行阶段写，不走 CLI 生成），但**会改 CLI 使用的模板文件**（静态字符串，非代码逻辑）。

## 3. Requirement

- `req-26`

## 4. Scope

### Included

- **角色文件更新（本仓库在用）**：为以下 7 个角色分别追加"对人文档输出"SOP 与退出条件：
  - `.workflow/context/roles/requirement-review.md`（产 `需求摘要.md`）
  - `.workflow/context/roles/planning.md`（产 `变更简报.md`，change 级）
  - `.workflow/context/roles/executing.md`（产 `实施说明.md`，change 级）
  - `.workflow/context/roles/testing.md`（产 `测试结论.md`，req 级）
  - `.workflow/context/roles/acceptance.md`（产 `验收摘要.md`，req 级）
  - `.workflow/context/roles/regression.md`（产 `回归简报.md`，regression 级）
  - `.workflow/context/roles/done.md`（产 `交付总结.md`，req 级）
- **统一契约写入公共父类**：在 `.workflow/context/roles/stage-role.md` 中新增一节"对人文档输出契约"，集中定义：
  - 命名表（中文文件名固定，不得擅自改名）；
  - 路径规则（req 级 / change 级 / bugfix 级 / regression 级的同构路径）；
  - 最小必备字段模板（本 plan.md 第 1.4 节）；
  - 不迁移原则（严禁从 `.workflow/flow/` 搬任何现存文件，严禁清洗 `artifacts/` 历史脏数据）。
- **下游角色模板同步**：将上述角色文件与 `stage-role.md` 的变更同步到 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` 下同名文件，确保 `harness install` 生成新仓库时拿到的是已带双轨 SOP 的版本。
- **`harness change` 生成的 change.md / plan.md 模板中文完整化**（新增，本轮并入）：
  - 把 `src/harness_workflow/assets/skill/assets/templates/change.md.tmpl` 与 `change-plan.md.tmpl` 升级为中文完整版，字段与本 req-26 实际在用的 change.md / plan.md 对齐（含 Title / Goal / Scope /（可选）Out-of-Scope / Acceptance / Risks 等必备节）；
  - 对应的 `.en.tmpl` 英文版同步升级为对称的英文完整版，避免语言开关切换时模板规模断裂；
  - 若 scaffold_v2 / 其他路径下也存在同名模板，一并同步。
- **示例对人文档（可选）**：在 req-26 自身的 `artifacts/main/requirements/req-26-uav-split/` 下，由后续 requirement_review 阶段先手动产出一份 `需求摘要.md` 作为样例（本 change 只制定机制，不强制先写示例）。

### Excluded

- **不改任何 harness CLI 代码逻辑**。对人文档由 agent 在执行对应 stage 时写入，不走 CLI 生成、不加 `harness doc` 子命令、不改 scaffold 的 python 生成脚本。模板文件（`*.tmpl`）虽属于 CLI 资产，但仅为静态字符串更新，不动代码路径。
- **不迁移 `.workflow/flow/` 下历史文档**。sug-06 契约 1 明示：现存 requirement.md / change.md / plan.md / session-memory.md / regression 文档维持原路径。
- **不清洗 artifacts/ 下历史脏数据**。`artifacts/bugfixes/bugfix-2/`、`artifacts/main/bugfixes/bugfix-{3,4,5}/` 下混入的 session-memory 等文件，本 change 一概不动，留作后续独立 bugfix。
- 不扩展 runtime.yaml schema。

## 5. Acceptance

- 覆盖 requirement.md 的 **AC-06**：
  - 契约 1（双轨不迁移）：本 change 仅追加 SOP 与新文档约束，不移动 / 删除 / 重写任何现存文档；
  - 契约 2（路径同构）：在 stage-role.md 中以表格形式固化路径规则，与 requirement.md AC-06 契约 2 完全一致；
  - 契约 3（中文命名、按阶段粒度）：命名表与 requirement.md AC-06 契约 3 完全一致（允许后续 planning 微调表述的空间写进 stage-role.md 备注，但本 plan.md 第 1.4 节给出首版定稿）；
  - 反例核对：在 stage-role.md 中明确"禁止迁移 `.workflow/flow/`"与"禁止清洗 `artifacts/` 历史脏数据"两条硬禁项。
- **AC-06 契约 1"双轨机制"的隐含扩展（本轮并入，不新增独立 AC）**：
  - `harness change` 新建的 change 默认产出**中文完整模板**的 change.md 和 plan.md，含 Title / Goal / Scope / Out-of-Scope / Acceptance / Risks 等必备节，不再是 "Describe what is included" / "Add implementation steps here" 这种极简 placeholder；
  - `src/harness_workflow/assets/scaffold_v2/` 下的 role / stage-role / 模板文件全面中文化并与本 change 对 `.workflow/context/roles/` 的改动一致，保证 `harness install` 到下游仓库后角色文件与本仓库 `.workflow/context/roles/` 文本一致；
  - 上两条作为 AC-06 契约 1（双轨机制）的内部落地细节，不占独立 AC。

## 6. Risks

- **角色文档被 agent 忽略**：SOP 若只是描述性语言，agent 可能跳过。必须以"退出条件清单 + 硬门禁"的形式写入，不能只写"建议"。
- **字段模板过度膨胀**：对人文档目标是"精炼"，字段多则失焦。严格执行"每个模板 ≤ 6 行字段、≤ 1 页篇幅"的上限。
- **下游模板漂移**：`scaffold_v2/` 下同步若遗漏，新仓库 `harness install` 后拿不到新机制。实施时必须对两棵目录同步比对。
- **`harness change` 模板升级带来的语义冲击**：中文完整模板字段更多，若 agent 在 planning 阶段直接粘贴 placeholder 而不填实际内容，反而比英文极简版"看上去更糟"。缓解：模板里所有 placeholder 用显眼的 `{{…}}` 中文说明，规定 planning 角色必须通读并替换，不得原样提交。
- **命名冲突**：若未来英文仓库需要，"中文命名"策略可能冲突。本 change 仅覆盖当前双语缺省；跨语言策略留作后续需求。
