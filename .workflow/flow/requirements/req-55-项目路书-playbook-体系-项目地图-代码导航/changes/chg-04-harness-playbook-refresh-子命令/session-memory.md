# Session Memory — chg-04（harness playbook-refresh 子命令）

## 1. Current Goal

新增 `harness playbook-refresh` 子命令，扫描 / 写入路径全部 `artifacts/project/playbooks/`（OQ-1=B），仅刷新 HTML 注释定界的 `<!-- AUTO:* -->` 自动区段，人工写入区零变化；marker 破损时 abort。

## 2. Context Chain

- Level 0: 主 agent（harness-manager）→ analysis stage 编排
- Level 1: Subagent-L1（analyst / opus）→ req-55 analysis stage
- 后续 Level 1（executing / sonnet）：执行本 chg

## 3. Completed Tasks（executing / sonnet，2026-04-30）

- [x] 新建 `src/harness_workflow/tools/harness_playbook_refresh.py`（317 行）
  - `playbook_refresh(root, dry_run=False) -> int` 主函数
  - `replace_auto_section(content, marker, new_content) -> (str, bool, str)` helper
  - 5 类扫描函数：`_scan_stack` / `_scan_scripts` / `_scan_layout` / `_scan_domain_files` / `_scan_domain_list`
  - 路径锁定 `artifacts/project/playbooks/`（OQ-1=B）
  - C-01 字节一致校验 + C-04 配对校验（warn + 跳过）
  - dry_run 模式：打印 unified diff，不落盘
- [x] 改 `src/harness_workflow/cli.py`（注册 `playbook-refresh` 子命令，紧接 install_parser 之后）
  - subparser 名：`playbook-refresh`，参数：`--root` / `--dry-run`
  - handler 调 `playbook_refresh(root, dry_run)` + 返回 exit code
- [x] 新建 `tests/test_playbook_refresh.py`（10 TC 含 dogfood subprocess）
- [x] pytest tests/test_playbook_refresh.py：**10 passed / 0 failed**
- [x] 全量回归 pytest tests/：**57 failed / 777 passed**（与 chg-03 基线 57 failed 完全一致，引入 +0）
- [x] harness validate --contract artifact-placement：exit 0 PASS
- [x] 自检 7 条全过

## 4. Results

### 产出文件

- `src/harness_workflow/tools/harness_playbook_refresh.py`（新增，5 类 AUTO 区段刷新 + dry-run + 配对校验）
- `src/harness_workflow/cli.py`（注册 `playbook-refresh` 子命令，+14 行）
- `tests/test_playbook_refresh.py`（新增，10 TC，含 TC-01~07 + replace_auto_section 3 条单元测试）

### 测试数字

- `pytest tests/test_playbook_refresh.py -v`：10 passed / 0 failed
- `pytest tests/ -q`：57 failed / 777 passed（基线 57，+0 regression）

### 关键实现决策

- `replace_auto_section` 使用 `re.DOTALL` 正则匹配，支持多行区段内容
- dry_run 使用 `difflib.unified_diff` 打印标准 diff 格式
- DOMAIN_FILES 刷新分两步：先刷各 `domains/*/code.md`，再汇总写 `code-map.md`
- 标记配对检测：开标记 / 闭标记各自独立检查，精确定位破损位置
- 不调 LLM（纯静态分析，spec §四明示）

## 5. Open Questions / default-pick

- OQ-1 已用户拍定 = B（`artifacts/project/playbooks/`）→ 本 chg 扫描 / 写入路径已对齐。
- 详见 req 主 session-memory.md `## 9`。

## 6. 经验沉淀候选

### 候选 A（executing → experience/roles/executing.md）

**场景**：AUTO 区段替换 helper 的 byte-identical 校验方式。

**经验**：用 `re.sub(r"<!-- AUTO:\w+ -->.*?<!-- /AUTO:\w+ -->", "", text, flags=re.DOTALL)` 剥离所有 AUTO 区段后对比剩余内容，是验证"区段外 byte-identical"约束的最可靠方式；不依赖文件 hash（hash 只能整体对比，无法定位区段边界）。

**来源**：req-55（项目路书Playbook体系）/ chg-04（harness playbook-refresh 子命令）TC-04

### 候选 B（known-risks）

**场景**：dry_run 模式下 capsys / subprocess 捕获 diff 输出的测试策略。

**经验**：dry_run 输出可能在 stdout 或 stderr，TC 用 `combined = out + err` 做宽泛断言（`"dry-run" in combined or "diff" in combined or "已是最新" in combined`），避免因输出渠道变化导致脆弱断言；文件内容用字节对比（`read_bytes()`）更可靠，不受文件 mtime 竞态影响。

---

## 完成态

本 chg executing stage 完成 ✅
