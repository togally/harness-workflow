# Change Plan

## 1. Development Steps

### Step 1：定位 rename CLI、change CLI 与状态读写点

- 读 `src/harness_workflow/tools/harness_rename.py`（CLI 入口）与 `src/harness_workflow/workflow_helpers.py` 下 rename 相关实现，定位目录重命名分支与 state yaml 写入分支。
- 读 `src/harness_workflow/tools/harness_change.py`（CLI 入口，已确认仅做参数转发）与 `src/harness_workflow/workflow_helpers.py` 的 `create_change()`（已确认在 `workflow_helpers.py:3345`，line 3370 处 `dir_name = f"{chg_num_id}-{change_title}"` 为 bug 点：直接拼接原始 title，未做 slugify）。
- 读 `src/harness_workflow/workflow_helpers.py` 中 `slugify()`（line 2152）、`resolve_artifact_id()`（line 2159）、`resolve_title_and_id()`（line 2170）——这是 regression 命令簇已经在用的共享 util，本 change 应直接复用，不要另起一套。
- 盘点当前 rename 命令对 runtime.yaml 做了什么（预期：几乎什么都没做，需要补 title 同步）。

### Step 2：修 rename 的目录命名逻辑

- 抽取 / 复用 slug 生成函数（直接引用 `workflow_helpers.slugify` / `resolve_artifact_id`，与 chg-01 的 regression 命令簇共用同一套规则）。
- 新目录名统一为 `{id}-{new-slug}`，id 取自原目录前缀或 state yaml，不允许改变。
- 在 rename 前校验目标路径是否已存在，存在则报错退出。

### Step 3：修 `harness change` 的目录命名逻辑（与 rename 共用 slugify）

- 在 `workflow_helpers.py:create_change()` 中，把 line 3370 附近的 `dir_name = f"{chg_num_id}-{change_title}"` 改为先对 `change_title` 走 `slugify()` / `resolve_artifact_id()`（与 regression 命令簇使用同一函数），再拼接 `{chg_num_id}-{slug}`。
- 当前语言为 cn 时，`resolve_artifact_id()` 会直接返回中文 title；本 change 需保证目录名**始终**走一层"移除空格 / 中文标点 / 连字符化"的清洗，**不受语言开关影响**（即使中文也要去空格、去中文冒号等）。因此建议：
  - 新增一个轻量 util `sanitize_artifact_dirname(title)`，在 `resolve_artifact_id()` 之后再做一次硬清洗（去空格、替换 `:`、`：`、`（）` 等为 `-`，合并连字符、裁剪首尾 `-`）；
  - `harness change` 与 `harness rename`、`harness regression` 三处目录命名都走该 util，彻底对齐 sug-04 对 regression 的规范。
- **不改 sug-04 对 regression 的修法**：sug-04 / chg-01 已处理 regression 目录命名；本 change 仅在共享 util 层打通，不改动 regression 侧既有代码路径。

### Step 4：补 state yaml 同步（rename 专属）

- rename requirement：
  - 更新 `.workflow/state/requirements/{id}.yaml` 的 `title` / `slug`；
  - 如 runtime.yaml 中有 `requirement_title` 缓存字段，同步更新；
  - `active_requirements` 元素是 id，不改。
- rename change：
  - 更新 `.workflow/state/requirements/{req-id}.yaml` 下 changes 列表对应项的 title / slug；
  - 更新 change 目录父路径下子目录名。
- rename bugfix：
  - 更新 `.workflow/state/bugfixes/{id}.yaml` 的 title / slug；
  - 如 runtime.yaml 中存在 bugfix 当前指向字段，同步。
- 涉及文件（预期，需 executing 阶段精确定位）：
  - `src/harness_workflow/tools/harness_rename.py`（CLI 入口）
  - `src/harness_workflow/tools/harness_change.py`（CLI 入口，可能无需改动，仅转发）
  - `src/harness_workflow/workflow_helpers.py`（核心改动：`create_change()` line 3345~3388、`slugify()` line 2152、新增 `sanitize_artifact_dirname()` 以及 rename 相关函数）
  - `src/harness_workflow/state/requirements.py`（若存在独立 state 读写封装）
  - `src/harness_workflow/state/runtime.py`（若存在）

### Step 5：失败回滚

- 采用"先备份旧 state → 写新 state → mv 目录 → 验证；异常时还原 state + 还原目录名"的模式。
- 若仓库已有 `pathlib` 与原子写入工具，优先复用。

### Step 6：单元测试

- `tests/test_rename_cli.py`（新增或扩写）：
  - `test_rename_requirement_keeps_id_prefix`；
  - `test_rename_requirement_syncs_state_yaml`；
  - `test_rename_change_updates_parent_requirement_yaml`；
  - `test_rename_bugfix_updates_bugfix_yaml`；
  - `test_rename_target_slug_collision_raises`。
- `tests/test_change_cli.py`（新增或扩写）：
  - `test_harness_change_slugifies_title_with_spaces`：输入 `"测试: 有 空格 的 名字"`，断言生成目录形如 `chg-XX-测试-有-空格-的-名字`（或等价 slug），不含空格 / `:` / `：`；
  - `test_harness_change_keeps_chg_id_prefix`：断言 `chg-XX-` 前缀保留；
  - `test_harness_change_and_regression_share_slugify`：构造同一 title，断言 `harness change` 与 `harness regression` 走出来的 slug 一致（防止将来分裂）。

### Step 7：文档与经验沉淀

- 在 `.workflow/context/experience/roles/planning.md` 或 `tool/harness-cli.md` 下补"rename 的原子性约定"以及"CLI 产出目录命名统一规范（rename / change / regression 共用 slugify）"。

## 2. Verification Steps

### 2.1 单元测试

- 运行 pytest，新增用例全部通过（rename 5 条 + change 3 条），老用例零回归。

### 2.2 手工 smoke（在沙盒仓库）

#### 2.2.1 rename 链路

1. `harness requirement "old title"` → 假设分到 `req-99`，目录 `req-99-old-title/`；
2. `harness rename req-99 "new title"`；
3. 检查磁盘：目录名为 `req-99-new-title/`；
4. 检查 `.workflow/state/requirements/req-99.yaml`：title/slug 已更新；
5. 检查 `.workflow/state/runtime.yaml`：无错位字段；
6. 对 change、bugfix 重复上述步骤。

#### 2.2.2 change 链路（新增）

1. 在已有 `req-99` 下执行 `harness change "测试: 有 空格 的 名字"`；
2. 断言生成目录形如 `chg-01-测试-有-空格-的-名字`（或等价 slug，视语言配置而定），且：
   - 前缀 `chg-01-` 保留；
   - 不含空格；
   - 不含中文冒号 `：` / 英文冒号 `:`；
   - 不含 `（）` / `《》` 等标点；
3. 再执行 `harness regression "测试: 有 空格 的 问题"`，断言其目录采用与 step 2 相同的 slugify 规则，两者产出的 slug 片段一致（除 id 前缀外）。

### 2.3 AC 映射

- AC-02 第一条（保留 id 前缀）：Step 2 + 2.2.1 步骤 3；
- AC-02 第二条（同步 state yaml）：Step 4 + 2.2.1 步骤 4-5；
- AC-02 隐含命名规范扩展（`harness change` 目录 slugify）：Step 3 + Step 6 change 测试 + 2.2.2 全部。

## 3. 依赖与执行顺序

- 独立 change，与 chg-01 / 03 / 04 / 05 可并行；
- **slugify util 与 chg-01 共享**：两个 change 都需要 kebab-case 规范化函数。建议：
  - 以 `workflow_helpers.py` 中已有的 `slugify()` / `resolve_artifact_id()` 为准；
  - 本 change 若新增 `sanitize_artifact_dirname()`，chg-01 的 regression 链路同步迁移过去，避免规则漂移；
  - 两个 change 的实施者在 executing 阶段需要对接口做一次对齐（谁先合入，另一方 rebase）。
