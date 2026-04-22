# Change

## 1. Title

修 `harness rename` 并统一 CLI 产出目录命名规范（`rename` + `change` 共用 slugify）

## 2. Goal

在同一套"CLI 产出目录命名规范"下，一次性解决两个相互关联的缺陷：

1. `harness rename` 在重命名 requirement / change / bugfix 时存在两个老问题：
   - 目录名丢失 `{id}-` 前缀（应为 `req-26-uav-split`，而非 `uav-split`）；
   - 重命名后 `.workflow/state/requirements/{id}.yaml` 的 title/slug 字段、以及 `.workflow/state/runtime.yaml` 的 `current_requirement` / `active_requirements` 字段未自动同步，需要人工补齐。
2. `harness change` 新建变更时，生成的目录名直接拼接原始 title（见 `workflow_helpers.py` 里 `dir_name = f"{chg_num_id}-{change_title}"`），**未做 kebab-case 清洗**，导致目录名中保留空格与中文冒号等特殊字符（如 `chg-02-修复 harness rename ...`），与 sug-04 对 regression 产出目录的规范不一致。

修复后，`harness rename` 一次成功、无需人工改任何 yaml；同时 `harness change` 生成的目录经 slugify 与 regression 目录使用相同的命名规范，彻底消除"不同 CLI 命令产出目录风格分裂"的问题。

**明确边界**：本 change **不改 sug-04 对 regression 目录的修法**（sug-04 归属 chg-01 regression 命令簇），这里只把 `harness change` 命令也纳入同一 slugify 规范，与 sug-04 在 util 层共享实现。

## 3. Requirement

- `req-26`

## 4. Scope

### Included

- 修 `harness rename` 子命令的目录重命名逻辑：新目录名必须拼接 `{id}-{new-slug}` 形式；
- 在 rename 流程中增加状态同步：
  - `.workflow/state/requirements/{id}.yaml` 的 `title` / `slug` 字段更新；
  - `.workflow/state/runtime.yaml` 的 `active_requirements` 中 id 不变，但如 schema 存在 title 缓存字段则同步；
  - 同一规则覆盖 change / bugfix 子类（若 CLI 支持）。
- **`harness change` 生成的目录命名也需做 kebab-case 清洗**（去空格、去中文冒号 / 括号 / 书名号等特殊字符），与 sug-04 对 regression 产出目录的规范保持一致；
- 复用 / 抽取共享 slugify util：若 `workflow_helpers.py` 中已有 `slugify()` / `resolve_artifact_id()` 等函数，则直接复用；若 regression（chg-01 / sug-04）与 change（本 change）两处实现不同，抽一个共享 util 供所有 CLI 产出目录的命令使用；
- 新增单元测试覆盖：rename req / rename chg / rename bugfix 三条路径，以及 `harness change` 目录名 slugify 路径。

### Excluded

- 不改变 `{id}` 的分配与生成逻辑；
- 不允许在 rename 时修改 requirement/change/bugfix 的 id；
- 不处理历史脏数据（已有的带空格 / 中文标点的目录不回填，属 Excluded 的历史清洗——req-26 自身 chg-02 / chg-05 的目录名脏数据也不回填，留给后续独立清洗）；
- 不改 sug-04 对 regression 的修法实现（仅在共享 util 层打通）。

## 5. Acceptance

- 覆盖 requirement.md 的 **AC-02**：
  - rename 后目录保留 `{id}-` 前缀；
  - rename 后 state yaml / runtime yaml 字段与磁盘目录一致，无需人工补齐；
  - **`harness change` 新建变更时，生成的目录名经 slugify（kebab-case、仅保留 `[a-z0-9-]` 字符、保留 `chg-XX-` 前缀），不得包含空格或中文标点**。该条作为 AC-02"目录名保留 id 前缀"的隐含命名规范扩展，不新增独立 AC。
- 反例断言：新生成的 change 目录下**不允许**出现空格、`:`、`：`、`（）`、`《》` 等特殊字符；`chg-XX-` 前缀保留。

## 6. Risks

- rename 过程若中途失败可能导致磁盘与 state yaml 不一致，需要采用"先写 state → mv 目录 → 失败回滚"的策略；
- slug 重名处理：若目标 slug 已被其他同类资源占用（不同 id），应报错而非静默覆盖；
- **与 chg-01（regression 命令簇）的 util 协同**：两处若同时需要 slugify util，需统一放在同一模块（建议 `workflow_helpers.py` 已有的 `slugify()`），避免各自实现导致规则漂移；
- 本 change 落地后，老目录（包括 req-26 自身的 chg-02 / chg-05）仍保留脏名字，需向用户说明"只对新建生效，历史不回填"。
