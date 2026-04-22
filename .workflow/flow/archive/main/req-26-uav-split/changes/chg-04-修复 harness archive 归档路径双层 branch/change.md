# Change

## 1. Title

修复 `harness archive`：归档路径不再出现双层 `{branch}`

## 2. Goal

消除 `harness archive` 在生成归档目录时把 `{branch}` 段重复拼接（形成 `archive/main/main/...`）的缺陷。修复后，归档路径中每一个 `{branch}` 段只出现一次，对已存在的历史双层路径保持不动（属 Excluded 的历史清洗）。

## 3. Requirement

- `req-26`

## 4. Scope

### Included

- 修 `harness archive` 子命令中归档路径拼接逻辑：
  - 现状：`archive_root = .workflow/flow/archive/{branch}`，再拼 `{branch}/{req-id}-{slug}/` → 重复；
  - 目标：`archive_root = .workflow/flow/archive/{branch}`，直接拼 `{req-id}-{slug}/`（只出现一次 branch）。
- 对历史已错位归档（含 `archive/main/main/...`）**不做**任何迁移或清洗。
- 新增单元测试验证路径格式。

### Excluded

- 不改 archive 的功能范围（只修路径拼接）；
- 不清洗历史脏数据；
- 不改 archive 与 migrate 子命令的关系。

## 5. Acceptance

- 覆盖 requirement.md 的 **AC-05**：归档路径中每个 `{branch}` 段只出现一次。

## 6. Risks

- 需区分"新归档路径"与"历史归档路径"：migrate / 查找历史归档产物时，代码仍需能读旧的双层 branch 路径（向后兼容）；
- 路径拼接逻辑如果散落在多个 helper 中，容易改漏。实施前需全局 grep `archive` + `{branch}` 相关调用。
