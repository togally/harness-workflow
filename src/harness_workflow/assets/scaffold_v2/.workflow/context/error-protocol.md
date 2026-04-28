# HARNESS_BLOCK 错误协议契约

> req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）/ chg-01（错误协议契约 + base-role 抛错门禁 + harness-manager 捕获路由）

## §1 目的与范围

本协议定义 Harness Workflow 中**任意 stage 角色检测到任务阻塞时**的标准化抛错行为，以及 harness-manager 的统一捕获与修复路由规则。所有 stage 角色（executing / testing / acceptance / regression / done 等）遇到以下阻塞场景时**强制**按本协议处理：

- contract 校验 FAIL（如 `artifact-placement` / `schema-audit` / `missing-document` 等）
- 必需文档缺失（如 plan.md / change.md 缺失）
- 旧目录残留（如 `req-XX/` 数字目录仍在 state/requirements/ 下）
- 其他无法在当前角色职责范围内自行修复的系统性阻塞

## §2 三层载体形式

| 层 | 形式 | 必填 |
|----|------|------|
| **stderr 文本** | 三行固定格式（见下方 schema）| 是 |
| **退出码** | `64`（FAIL）/ `65`（ABORT）/ `0`（WARN）| 是 |
| **状态文件** | `.workflow/state/runtime-block.yaml` 写入结构化字段 | 是 |

stderr 三行格式：
```
HARNESS_BLOCK: {error_type}
fix-checklist: {fix_checklist_path}
severity: {severity}
```

## §3 error_type 命名规范 + 已知类型表

**命名规范**：kebab-case，与 contract 名同字面。`fix-{error-type}.md` 是对应的 fix-checklist 路径。

| error_type | 对应 contract | fix-checklist |
|-----------|--------------|---------------|
| `artifact-placement` | `check_artifact_placement` | `.workflow/context/checklists/fix-artifact-placement.md` |
| `schema-audit` | `check_schema_audit` | `.workflow/context/checklists/fix-schema-audit.md` |
| `missing-document` | `check_missing_document` | `.workflow/context/checklists/fix-missing-document.md` |
| `user-write-protected-zones` | `check_user_write_protected_zones` | `.workflow/context/checklists/fix-user-write-protected-zones.md`（留尾，req-49）|
| `build-cache-freshness` | `check_build_cache_freshness` | `.workflow/context/checklists/fix-build-cache-freshness.md`（留尾，req-49）|
| `self-audit-drift` | `check_role_stage_continuity` | `.workflow/context/checklists/fix-self-audit-drift.md`（留尾，req-49）|

## §4 错误结构字段表

| 字段 | 类型 | 说明 |
|------|------|------|
| `error_type` | str | kebab-case 错误类型（§3 字面表） |
| `fix_checklist_path` | str | 对应 fix-checklist 文件路径 |
| `retry_context` | dict | 触发时的上下文快照（由检测函数填入）|
| `severity` | str | `FAIL`（可修复中断）/ `ABORT`（不可修复）/ `WARN`（仅记录）|
| `detected_by` | str | 检测该错误的角色或函数名 |
| `timestamp` | str | ISO 8601 UTC 时间戳 |
| `recovery_attempts` | int | 本次运行内同 error_type 的累计修复尝试次数 |

## §5 runtime-block.yaml schema + 样例

路径：`.workflow/state/runtime-block.yaml`

```yaml
error_type: "artifact-placement"
fix_checklist_path: ".workflow/context/checklists/fix-artifact-placement.md"
retry_context:
  task: "executing chg-01"
  violations: "artifacts/main/requirements/req-99-x/planning/session-memory.md"
severity: "FAIL"
detected_by: "check_artifact_placement"
timestamp: "2026-04-28T14:00:00+00:00"
recovery_attempts: 1
```

**状态清空规则**：harness-manager 在修复 subagent 成功返回 exit 0 后，必须将 runtime-block.yaml 清空（写入空 `{}`）或删除，表示阻塞已解除。

## §6 harness-manager 捕获语义 + 重试边界

harness-manager 在以下条件触发捕获路由：
1. subagent 返回 exit code ≥ 64；**或**
2. runtime-block.yaml 非空（含有效 `error_type` 字段）

捕获后的标准流程：
1. 解析 `error_type` → 查找对应 `fix_checklist_path`；
2. 校验 fix-checklist 文件存在；
3. 按 §3.6 派发协议派发 fix-subagent（model 默认 sonnet）；
4. 修复完成后清空 runtime-block.yaml + 重试原任务（最多 1 次）。

**升级条件**（任一满足即升级为用户通知）：
- fix-checklist 文件不存在；
- 同 `error_type` `recovery_attempts` ≥ 3；
- fix-subagent 返回 exit 65（ABORT）。

## §7 fix-checklist 命名规范

- 路径：`.workflow/context/checklists/fix-{error-type}.md`
- 内容结构（5 节）：触发条件 / 修复步骤 / 验证步骤 / 回退路径 / dogfood 样本
- 修复步骤必须使用编号化 shell 命令清单，不允许模糊描述
- 新增任何 contract（`check_*` 函数）时，**必须同步新建**对应 fix-checklist，否则视为硬门禁违反
