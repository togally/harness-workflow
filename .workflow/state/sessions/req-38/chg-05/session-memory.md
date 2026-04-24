# Session Memory — req-38（api-document-upload 工具闭环）/ chg-05（存量项目同步验证 + _template 可选段 + 契约合规）

## 1. Current Goal

chg-05（存量项目同步验证 + _template 可选段 + 契约合规）：验证 chg-01（protocols 目录 + catalog 单行引用）~chg-04（ProjectProfile.mcp_project_ids 多 provider map）产出通过 harness install 传播到存量项目；_template.md 新增前置检查可选段；契约 7 自检。

## 2. Current Status

全部 Step 已完成。2 条新增 pytest 用例全绿，全量 pytest 340 passed / 39 skipped，零回归。req-38 scope AC-11 裸 id = 0。

## 3. Execution Log

### Step 1 ✅ _template.md 新增可选前置检查段
- 文件：`.workflow/tools/catalog/_template.md`
- 在 `## 注意事项` 后插入 `## 前置检查（依赖 MCP/外部服务时）` 段 + 注释性占位
- 行数：19 → 23（增量 4，≤ 10 满足）
- `grep -c "protocols/mcp-precheck.md"` → 1（≥ 1）

### Step 2 ✅ scaffold_v2 mirror 同步 _template.md
- `cp .workflow/tools/catalog/_template.md src/harness_workflow/assets/scaffold_v2/.workflow/tools/catalog/_template.md`
- `diff` 无输出，零 diff 确认

### Step 3 ✅ pytest 新增 install_repo_protocols 用例
- 文件：`tests/test_install_repo_protocols.py`
- `test_install_repo_propagates_protocols_dir`：tmp 存量项目 install 后，`mcp-precheck.md` 被创建，内容与 scaffold_v2 一致 → PASSED
- `test_scaffold_v2_mirror_whitelist_excludes_protocols`：`"tools/protocols/"` 不在 `_SCAFFOLD_V2_MIRROR_WHITELIST` → PASSED

### Step 4 ✅ review-checklist 补 protocols/ 同步完整性条款
- 文件：`.workflow/context/checklists/review-checklist.md`
- 新增条款：`git diff --name-only` 命中 `.workflow/tools/protocols/` 时必须同时命中 scaffold_v2 对应文件
- scaffold_v2 mirror 同步：零 diff

### Step 5 ✅ AC-8 mock 验证（/tmp/req38-install-sandbox）
- 在 `/tmp/req38-install-sandbox` 跑 `install_repo`（rc=0）
- `diff -rq protocols/` → ZERO_DIFF
- `diff -rq catalog/_template.md` → ZERO_DIFF
- `diff -rq catalog/api-document-upload.md` → ZERO_DIFF
- 使用方案：方案 2（临时 mock 存量项目，全新 git init + install_repo）

### Step 6 ✅ AC-11 契约合规自检
- 扫 req-38 artifacts + session 段，发现裸 id 引用多处（chg-01~05 title 行、plan.md 历史段落等）
- 逐一修正：在首次引用处补 `（≤15字描述）`
- 修正的文件清单（最小修改）：
  - `requirement.md`：chg-01 首引补 title；req-38 自引补描述；§5 候选段改为 chg-XX（title）形式
  - `chg-01/change.md`：title 行 + Excluded chg-02/03/04/05 补 title
  - `chg-01/plan.md`：chg-03/02/04/05 依赖说明补 title
  - `chg-01/实施说明.md`：title 行补括号
  - `chg-02/change.md`：title 行 + Excluded chg-01/03/04/05 补 title
  - `chg-02/实施说明.md`：title 行补括号
  - `chg-02/plan.md`：chg-03 依赖说明补 title
  - `chg-03/change.md`：title 行 + Included chg-01 + Excluded chg-02/04/05 补 title
  - `chg-03/实施说明.md`：title 行补括号
  - `chg-03/plan.md`：chg-01/04/02 首引补 title
  - `chg-04/change.md`：title 行 + chg-01/05/02/03 首引补 title
  - `chg-04/实施说明.md`：title 行补括号
  - `chg-04/plan.md`：chg-01 首引补 title
  - `chg-05/change.md`：title 行 + chg-01/req-34/36/02/37 首引补 title；Excluded 段补 title
  - `chg-05/plan.md`：chg-01/04 首引补 title
  - `.workflow/state/sessions/req-38/session-memory.md`：req-34/chg-01/req-36 首引补 title
  - `.workflow/state/sessions/req-38/chg-04/session-memory.md`：标题行 + chg-02 首引补 title
  - `.workflow/state/sessions/req-38/chg-03/session-memory.md`：标题行补括号
- 验证：`grep "req-38\|sessions/req-38" /tmp/validate_output4.txt` → 空（零命中）

### Step 7 ✅ 全量 pytest + 最终验证
- `pytest tests/` → 340 passed, 39 skipped（零回归）
- `grep -c "protocols/mcp-precheck.md" .workflow/tools/catalog/_template.md` → 1
- `diff .workflow/tools/catalog/_template.md scaffold_v2/...` → ZERO_DIFF
- `diff -rq .workflow/tools/protocols/ scaffold_v2/.../protocols/` → ZERO_DIFF

## 4. Default-Pick 决策列表

- **AC-8 人工复现替代**：plan.md Step 5 要求沙盒 executing stage 真实触发"帮我上传接口文档"，本 chg 以 pytest mock + diff 零输出替代；理由：agent 运行时行为无法在 subagent 内自动化执行，核心 propagate 机制已由 pytest 覆盖。

## 5. 关键 stdout 证据

```
# AC-10 验证
$ grep -c "protocols/mcp-precheck.md" .workflow/tools/catalog/_template.md
1

$ wc -l .workflow/tools/catalog/_template.md
      23 (baseline=19, 增量=4)

$ diff .workflow/tools/catalog/_template.md src/.../scaffold_v2/.../_template.md
(无输出)

# AC-8 mock 验证
$ diff -rq /tmp/req38-install-sandbox/.workflow/tools/protocols/ scaffold_v2/.../protocols/
(无输出 → ZERO_DIFF)

$ diff -rq /tmp/req38-install-sandbox/.workflow/tools/catalog/_template.md scaffold_v2/.../_template.md
(无输出 → ZERO_DIFF)

# AC-8 pytest
$ pytest tests/test_install_repo_protocols.py -v
test_install_repo_propagates_protocols_dir PASSED
test_scaffold_v2_mirror_whitelist_excludes_protocols PASSED
2 passed in 0.59s

# AC-11 契约合规
$ grep "req-38\|sessions/req-38" /tmp/validate_output4.txt
(无输出 → req-38 scope 零命中)

# Step 7 全量 pytest
pytest tests/ → 340 passed, 39 skipped
```

## 6. AC-8 mock 方案实际使用

采用**方案 2（临时 mock）**：在 `/tmp/req38-install-sandbox` 新建空 git 仓库（全新 `git init`），跑 `install_repo(Path("/tmp/req38-install-sandbox"), force_skill=True, check=False)` 模拟存量项目升级，再 `diff -rq` 验证 protocols/ + _template.md + api-document-upload.md 零差异。

pytest `test_install_repo_propagates_protocols_dir` 进一步验证：先创建只有旧版 tools/ 但无 protocols/ 的存量结构，跑 install_repo 后断言 protocols/mcp-precheck.md 被创建且内容与 scaffold_v2 mirror 一致。

## 7. 模型自检降级留痕

- expected_model: sonnet（briefing 指定）
- 实际运行：claude-sonnet-4-6
- 无法程序化自省 model ID，以系统提示中的 `claude-sonnet-4-6` 标注为准
- 降级：无需降级

## 8. Failed Paths

无。

## 9. Open Questions

无。
