# Change Plan

## 1. Development Steps

### Step 1：定位 sug 操作三函数

- 在 `src/harness_workflow/workflow_helpers.py` 中定位 `apply_suggestion` / `delete_suggestion` / `archive_suggestion`，记录当前解析 sug-id 的逻辑（读 frontmatter `id:` 字段）。
- 同步定位 `create_suggestion`，记录其当前决定下一个编号的代码段。

### Step 2：实现 filename fallback

- 在三个操作函数中：按 frontmatter 解析失败或匹配不到目标 sug-id 时，转入 fallback 分支——用正则 `^sug-(\d+)` 从文件名提取 id 进行匹配。
- 保持原 frontmatter 优先路径不变，仅追加 fallback；对外 API 签名不变。

### Step 3：实现跨 archive 编号单调递增

- 在 `create_suggestion` 中，列出 `.workflow/flow/suggestions/*.md` 与 `.workflow/flow/suggestions/archive/**/*.md` 两份文件清单。
- 聚合所有文件的 `sug-NN` 最大编号 max_n，下一编号取 `max_n + 1`；若两处皆无匹配文件则从 01 开始。

### Step 4：done 阶段 frontmatter 硬门禁

- 在 `create_suggestion` 写入前校验 frontmatter：缺失 `id` / `title` / `stage` / `created_at` 任一必填字段即抛异常并报错退出；错误信息引导调用方补齐 frontmatter。
- 在 `.workflow/context/roles/done.md` 与 `.workflow/context/roles/stage-role.md` 的对人文档契约章节追加一条 SOP："done 阶段新增 sug 必带 YAML frontmatter（必含 id / title / stage / created_at），否则拒绝写入。"

### Step 5：scaffold_v2 同步

- 将 Step 4 中对 `done.md` / `stage-role.md` 的补丁复制到 `src/harness_workflow/scaffold_v2/roles/done.md` 与 `scaffold_v2/roles/stage-role.md`（或实际骨架路径，按仓库现状定位）。
- diff 校验：两份骨架与源文件的关键 SOP 段落逐行一致。

### Step 6：新增测试 `tests/test_suggest_cli.py`

- 覆盖 3 个断言：
  - (a) 用 tempdir 构造一个无 frontmatter 的 `sug-99-foo.md`，调用 `apply_suggestion("sug-99")` 成功；`delete_suggestion` / `archive_suggestion` 同理。
  - (b) tempdir 下 `archive/` 放 `sug-03-x.md`，当前目录空；`create_suggestion(...)` 新建出 `sug-04-*.md`。
  - (c) 直接调用 `create_suggestion` 但传入缺失 frontmatter 的内容，断言抛异常。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `pytest tests/test_suggest_cli.py -v` 全绿。
- `grep -n "sug 必带 YAML frontmatter" .workflow/context/roles/done.md` 非空。
- `grep -n "sug 必带 YAML frontmatter" .workflow/context/roles/stage-role.md` 非空。
- `diff src/harness_workflow/scaffold_v2/roles/done.md .workflow/context/roles/done.md`（关键 SOP 段落一致）。

### 2.2 Manual smoke / integration verification

- 在 tempdir 下：
  1. 手写一个无 frontmatter 的 `.workflow/flow/suggestions/sug-77-demo.md`
  2. 运行 `harness suggest --delete sug-77`，预期成功且文件消失。
  3. 运行 `harness suggest` 新建一条 sug，预期返回的 sug-id 不与 `archive/` 下任何 sug 冲突。

### 2.3 AC Mapping

- AC-15 -> Step 2/3/4/5/6 + 2.1 + 2.2

## 3. Dependencies & Execution Order

- 本 change 为 req-28 的拓扑起点，无前置依赖。
- 后续 chg-02 / chg-03 会同样编辑 `workflow_helpers.py`，要求先合入本 change 以减少 merge 冲突。
