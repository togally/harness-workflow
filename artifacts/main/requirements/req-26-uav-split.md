# uav-split

> req-id: req-26 | 完成时间: 2026-04-19 | 分支: main

## 需求目标

系统化处理 req-25 及此前遗留的 6 条合并建议（sug-01~sug-06）：其中 sug-01~sug-05 修复 regression / rename / next / archive 四条命令的具体缺陷，sug-06 在不迁移历史文档的前提下，为各 stage 角色建立面向用户的精炼文档双轨输出机制，让用户能够只读"对人产出"就掌握当前需求/变更/bugfix 的关键结论。

## 交付范围

### Included（本需求覆盖）

- **sug-01**：修复 `harness regression` 命令中 `--confirm` 会错误消费 regression 标记，导致 `--testing` 模式不可用的问题。
- **sug-02**：修复 `harness rename` 在改名时丢失 `{id}-` 前缀、且未同步更新 `.workflow/state/requirements/{id}.yaml` 和 `runtime.yaml` 的问题（req-25 final regression P1-new-01）。
- **sug-03**：让 `harness next` 在推进 stage 时自动写回 `.workflow/state/requirements/{id}.yaml` 的 `stage` / `status` 字段，使 archive 不再依赖人工改 yaml（req-25 P1-new-02）。
- **sug-04**：修复 `harness regression` 产出目录命名含空格、且无 `{id}-` 前缀的问题，产出目录必须使用 kebab-case 并携带 regression id 前缀（req-25 P1-new-03）。
- **sug-05**：修复 `harness archive` 把归档路径写成 `archive/main/main/...` 双层 branch 的问题，归档路径必须保证每个 branch 段只出现一次（req-25 P1-new-04）。
- **sug-06**：在不动现有 agent 过程文档的前提下，为每个 stage 角色额外产出一份面向用户的精炼文档，统一落到 `artifacts/{branch}/...` 对应制品目录下，使用中文命名、按阶段粒度命名（详见"4. Acceptance Criteria"中 sug-06 的三个契约条目）。

### Excluded（本需求明确不做）

- **不做 `.workflow/flow/` 下历史文档的改写、迁移或删除**。`requirement.md`、`change.md`、`plan.md`、`session-memory.md`、`regression/diagnosis.md`、`regression/required-inputs.md`、`done-report.md` 等现存 agent 过程文档维持原路径、原形态、原职责。
- **不做 `artifacts/` 下已有历史脏数据的清洗**。当前 `artifacts/bugfixes/bugfix-2/` 以及 `artifacts/main/bugfixes/bugfix-{3,4,5}/` 下混入的 `session-memory.md`、`regression/diagnosis.md`、`regression/required-inputs.md` 等文件是历史产物，本需求**不做任何清洗或重分配**，留作后续独立 bugfix。
- **不重新分配"哪个文件放哪里"**。sug-06 不是文件搬迁任务，只是在现有制品树上追加"对人文档"这一新输出，不得把任何现存文件从 `.workflow/flow/` 搬到 `artifacts/`，也不得把任何现存文件从 `artifacts/` 搬到 `.workflow/flow/`。
- 不覆盖 req-25 之外其他需求的已归档产物。
- 不修改 `.workflow/state/runtime.yaml` 的 schema（各 stage yaml schema 的补齐由 sug-03 的 AC 界定，不做扩展性重构）。

## 验收标准

### AC-01（对应 sug-01）
- [ ] `harness regression --confirm <issue>` 执行后，regression 标记仍可被后续 `harness regression --testing` 正确识别与消费；回归用例覆盖"先 --confirm、后 --testing"的连续场景且通过。

### AC-02（对应 sug-02）
- [ ] `harness rename` 在重命名需求/变更/bugfix 时，目标目录名必须保留 `{id}-` 前缀（例如 `req-26-uav-split`，而不是 `uav-split`）。
- [ ] `harness rename` 完成后，`.workflow/state/requirements/{id}.yaml` 中的 title / slug 字段与 `.workflow/state/runtime.yaml` 中的 `current_requirement` / `active_requirements` 保持一致，无需人工补齐。

### AC-03（对应 sug-03）
- [ ] `harness next` 推进 stage 后，`.workflow/state/requirements/{id}.yaml` 的 `stage` / `status` 字段自动写回为新 stage，`harness archive` 不再依赖用户手动改 yaml 即可成功归档。
- [ ] 回归用例覆盖"requirement_review → planning → ... → done → archive"完整链路，中途不手工干预 yaml。

### AC-04（对应 sug-04）
- [ ] `harness regression "<issue>"` 生成的产出目录命名不得含空格，必须使用 kebab-case 并以 regression id 前缀开头（例如 `reg-07-xxx/` 而非 `regression xxx/` 或 `xxx/`）。

### AC-05（对应 sug-05）
- [ ] `harness archive` 生成的归档路径中每一个 `{branch}` 段只出现一次，不得出现 `archive/main/main/...` 这类双层 branch；对已存在的双层 branch 路径保持不动（属 Excluded 的历史清洗）。

### AC-06（对应 sug-06，双轨输出机制）

sug-06 收敛为三个契约，全部作为可核对条目：

- [ ] **契约 1 —— 双轨不迁移**：`.workflow/flow/` 和 `.workflow/state/` 下现存的所有 agent 过程文档（requirement、change、plan、session-memory、regression/diagnosis、required-inputs、done-report 等）维持原路径不变；sug-06 只**新增**"对人产出"，不移动、不删除、不重写任何现存文档。
- [ ] **契约 2 —— 路径同构**：每个 stage 角色新产出的对人文档统一落到 `artifacts/{branch}/...` 下，按现有制品树同构：
    - 需求级：`artifacts/{branch}/requirements/{req-id}/`
    - 变更级：`artifacts/{branch}/requirements/{req-id}/changes/{chg-id}/`
    - Bugfix 级：`artifacts/{branch}/bugfixes/{bugfix-id}/`
- [ ] **契约 3 —— 中文命名、按阶段粒度**：对人文档采用中文文件名，按阶段粒度落盘。初始命名表（允许 planning 阶段微调表述，但不得偏离契约 1/2）：
    - `需求摘要.md`（requirement_review 阶段产出，req 级）
    - `变更简报.md`（planning 阶段产出，change 级）
    - `实施说明.md`（executing 阶段产出，change 级）
    - `测试结论.md`（testing 阶段产出，req 级）
    - `验收摘要.md`（acceptance 阶段产出，req 级）
    - `回归简报.md`（regression 阶段产出，regression 级）
    - `交付总结.md`（done 阶段产出，req 级）
- [ ] **反例核对**：Exclude 章节中"不迁移历史文档""不清洗 artifacts 历史混杂文件"两项反例能在实施完成后逐条核对，确认未触碰 `.workflow/flow/` 下现存文档，也未触碰 `artifacts/bugfixes/bugfix-2/`、`artifacts/main/bugfixes/bugfix-{3,4,5}/` 下的历史脏数据。

### AC-07（整体）
- [ ] 六条 sug 的修复/机制落地后，在一次端到端 smoke（新建需求 → planning → executing → testing → acceptance → done → archive，含一次 regression --confirm 和一次 rename）中，全部命令无需人工改 yaml、无目录命名异常、无路径双层 branch，且每个阶段都产出对应的对人文档。

## 变更列表

- **chg-01** 修复 harness regression 命令簇：`--confirm` 不消费 regression 状态 + 产出目录 kebab-case 带 id 前缀：一次性修好 `harness regression` 命令簇中两处缺陷：
- **chg-02** 修 `harness rename` 并统一 CLI 产出目录命名规范（`rename` + `change` 共用 slugify）：在同一套"CLI 产出目录命名规范"下，一次性解决两个相互关联的缺陷：
- **chg-03** 修复 `harness next`：自动写回 `.workflow/state/requirements/{id}.yaml` 的 `stage` / `status`：让 `harness next` 在推进 stage 时，除了修改 `.workflow/state/runtime.yaml` 之外，**同时**自动写回 `.workflow/state/requirements/{id}.yaml`（以及 `bugfixes/{id}.yaml`，如适用）的 `stage` / `status` 字段，消除 `harness archive` 对人工改 yaml 的依赖。
- **chg-04** 修复 `harness archive`：归档路径不再出现双层 `{branch}`：消除 `harness archive` 在生成归档目录时把 `{branch}` 段重复拼接（形成 `archive/main/main/...`）的缺陷。修复后，归档路径中每一个 `{branch}` 段只出现一次，对已存在的历史双层路径保持不动（属 Excluded 的历史清洗）。
- **chg-05** 各 stage 角色双轨输出：对人文档 SOP 与最小字段模板（AC-06 核心） + scaffold_v2 / change 模板同步中文化：在**不迁移任何现存 agent 过程文档**的前提下，为 7 个 stage 角色（requirement_review / planning / executing / testing / acceptance / regression / done）建立"对人文档"双轨输出机制。每个 stage 角色在完成自身业务后，除既有 agent 过程产物外，额外按统一契约产出一份面向用户的精炼中文文档，落到 `artifacts/{branch}/...` 同构路径下。
- **chg-06** 端到端 smoke：验证 sug-01~sug-06 集成后的闭环无回退：在 chg-01 ~ chg-05 全部合入后，通过**一次完整的 requirement 生命周期**验证 sug-01~sug-06 集成效果：
