# Requirement

## 1. Title

apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）

## 1.5 Background

bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） 落地后，`harness requirement` / `harness change` / `harness bugfix` 等命令把 `requirement.md` 移到 `.workflow/flow/requirements/{req-id}/requirement.md`（机器型）。但 `harness suggest --apply-all` 路径校验没跟上，仍按旧路径 `artifacts/main/requirements/{req-id}/requirement.md` 找，找不到 → log ERROR → "aborting before unlink" → req 创建后 requirement.md 是空模板，sug 文件没被删，状态半挂。

**触发原因**：本周期 `harness suggest --apply-all` 实证 abort，回滚后追加 sug-43（apply-all artifacts/ 旧路径检查）+ sug-44（apply 取 content 头当 title / rename 不同步 runtime）。

**关联 sug**：
- sug-43：apply-all artifacts/ 旧路径校验导致 abort（本 req 直接修复）
- sug-44：apply 取 content 头当 title + rename 不同步 runtime current_requirement_title（本 req 顺便修）
- 新观察：`harness suggest --apply <id>` 单 sug 路径**不真填 requirement.md 内容**（apply 只创建空模板就喊 success）；**rename 漏 `.workflow/flow/requirements/` 新目录**——本次实证两条会在 done 阶段补 sug。

## 2. Goal

- 修复 `harness suggest --apply-all` 在 bugfix-6 后路径不匹配导致 abort 的 bug，让批量 apply 真正可用。
- 顺带修 `harness suggest --apply <id>` 单 sug 路径校验 + 内容填充 + title 取值。
- 顺带修 `harness rename` 同步范围扩到 `.workflow/flow/requirements/` 新目录 + runtime current_requirement_title 字段。

## 3. Scope

### 3.1 IN

- `src/harness_workflow/tools/harness_suggest.py`（或 workflow_helpers 中 apply / apply_all 实现）：路径校验从 artifacts/ 改为 `.workflow/flow/requirements/`。
- apply 单 sug：取 sug.title 字段当 req title（不是 content 头），把 sug.content 写入 requirement.md §背景或 §goal。
- apply-all：路径正确后，正常 unlink 所有 sug，把所有 sug content 合并写到 req requirement.md。
- `harness rename` 同步：补 `.workflow/flow/requirements/` 目录重命名 + runtime current_requirement_title / locked_requirement_title 字段同步。
- 补 e2e 测试：apply / apply-all / rename 三类各覆盖正常路径 + 后 bugfix-6 路径。

### 3.2 OUT

- 不动 bugfix-6 已落地的关注点分离契约本身。
- 不重构 sug 池整体 schema。
- 不改 record_subagent_usage / token 渲染等其他链路（属 sug-39 / sug-41 / sug-42）。

## 4. Acceptance Criteria

- **AC-01**：`harness suggest --apply-all` 在当前仓库（bugfix-6 已落地）能成功跑完，sug 全部 unlink，req requirement.md 含合并后的 sug 内容（§goal / §scope 形式自决）。
- **AC-02**：`harness suggest --apply <id>` 单 sug 创建 req 时，req title = sug.title（不是 content 头）；requirement.md content 段含 sug.content。
- **AC-03**：`harness rename requirement <old> <new>` 同步重命名 `.workflow/state/requirements/`、`artifacts/main/requirements/`、`.workflow/flow/requirements/` 三处目录 + 同步 runtime.yaml 的 current_requirement_title / locked_requirement_title（如设了）字段。
- **AC-04**：scaffold_v2 mirror 同步（如有 .workflow/ 文档改动）。
- **AC-05**：补 e2e pytest 用例：apply / apply-all / rename 三类各 ≥ 2 用例（正常 + 后 bugfix-6 路径）。

## 5. Split Rules

- 拆分原则：按 CLI 子命令拆 chg（apply / apply-all / rename 三个 chg），各自独立 + e2e 测试。
- 或合并为单 chg（scope 小）。analyst 自决。
- 完成时填 `completion.md` 并验证项目启动成功。
