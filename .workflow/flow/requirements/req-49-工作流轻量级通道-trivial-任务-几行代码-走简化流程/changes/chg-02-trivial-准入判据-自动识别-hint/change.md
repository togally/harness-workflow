---
id: chg-02
title: trivial 准入判据 + 现有命令主动识别 hint
req: req-49（工作流轻量级通道：trivial 任务（几行代码）走简化流程）
trivial: false
---

# chg-02（trivial 准入判据 + 自动识别 hint）

## 1. Goal

实现 trivial 通道的 machine-checkable 准入判据 + `harness bugfix` / `harness requirement` 入口主动扫 git diff 输出 hint，让"trivial 与否"由工具客观判定 + 用户最终决策，避免主观滥用与漏用。

## 2. Scope

### In-Scope

1. **trivial 准入判据 helper**：在 `workflow_helpers.py` 新增 `validate_trivial_eligibility(repo_path: Path) -> tuple[bool, str]`：
   - 返回 `(True, "")` 或 `(False, reason)`；
   - 组合判据（4 维度全通过才算 trivial）：
     - **行数阈值**：`git diff --shortstat` ≤ 10 行（含新增 + 删除）；
     - **文件数阈值**：≤ 2 个非测试文件（含新增 + 删除）；
     - **改动类型白名单**：仅命中以下之一——string 字面量 / typo / 注释 / 文档（`.md` / `.txt`）/ 配置常量 / 删过期代码 / lint 修复；
     - **影响面零增**：grep `^import |^from .* import` 与基线对比无新增；无新增 API 签名；无新增 if/else 分支逻辑（启发式）。
2. **改动类型分类 helper**：新增 `classify_diff_change_types(diff_output: str) -> set[str]`，返回改动类型集合（typo / string / comment / doc / config_constant / dead_code / lint / other）；分类逻辑用正则启发式（如 typo = 单字符 / 单词替换；doc = `.md` 文件改动；config_constant = `=` 右侧字面量替换且无函数调用）；命中 `other` 时一票否决。
3. **`harness bugfix` 入口 hint**：在 `cli.py` 的 `bugfix` 子命令开头扫 `git diff` → 调 `validate_trivial_eligibility`：
   - 若 `(True, "")` → stdout 输出 hint：
     ```
     检测到改动量 = {n} 行 / {m} 文件 / 仅 {types} 类改动，建议改用 `harness trivial "<title>"` 通道（节省 ~80% 流程节拍）。
     继续走 bugfix 输入 `--force-full` 抑制本提示。
     ```
   - 若 `--force-full` flag 或 `(False, _)` → 跳过 hint 直接走 bugfix。
4. **`harness requirement` 入口 hint**：与 bugfix 同形态扩展。
5. **`--force-full` flag 注册**：`harness bugfix` / `harness requirement` 加 `--force-full` argparse flag，default=False。
6. **fix-checklist 类指针**：hint 文案不仅给"切 trivial"建议，还附带 trivial 通道的 fix-checklist 速查（≤ 3 行 inline 文本：① 仅改 ≤ 10 行 / ② 不引入新依赖 / ③ 不改 API 签名）；fail-fast 给用户"是否符合"自检线索。
7. **stdout 不阻塞**：hint 仅 stdout 提示，命令继续按用户原选择执行；exit code 不变。

### Out-of-Scope

- chg 级 trivial flag 在 change.md frontmatter（chg-03）；
- trivial 工件模板压缩（chg-03）；
- trivial-guard 自动升级护栏（chg-04）。

## 3. Acceptance（对应 req-49 AC）

- AC-03（`validate_trivial_eligibility` helper + 单测覆盖 5 类正例 + 5 类反例）；
- AC-N2（`harness bugfix` / `harness requirement` 入口扫 git diff 命中阈值时 stdout 输出 hint + `--force-full` flag 抑制 + hint 不阻塞命令）。

## 4. Dependencies

- 前置：chg-01（task_type 枚举 + TRIVIAL_SEQUENCE 已落）；
- 后续：chg-03 依赖本 chg 的 hint 行为（chg-03 在 change.md frontmatter 加 trivial flag 时复用 `validate_trivial_eligibility`）。

## 5. Risk

- **风险**：改动类型启发式分类误判（如 typo 改动可能命中 `other` 因正则不全）。**缓解**：单测覆盖 ≥ 5 类正例 + 5 类反例；保留 conservative bias（漏判 trivial 比误判要安全，"非 trivial 标 trivial"风险高于"trivial 标非 trivial"）；用户始终可用 `harness trivial` 显式入口绕过启发式。
- **风险**：`git diff --shortstat` 在 git 状态非常干净时返回空 → 误判为"改动量 = 0 行"满足 trivial 阈值 → 输出 hint 误导用户。**缓解**：先判断 diff 非空再扫阈值；空 diff 跳过 hint。
