# Change

## 1. Title

修 resolve_archive_root 判据以 primary 优先

## 2. Goal

- 修复 `resolve_archive_root` 的降级判据：无论 legacy `.workflow/flow/archive/` 是否非空，新归档默认先返回 primary `artifacts/{branch}/archive/`；只有显式指定 legacy（flag 或环境变量）时才走 legacy，确保归档默认落新路径。

## 3. Requirement

- `req-29`

## 4. Scope

### Included

- 修改 `src/harness_workflow/workflow_helpers.py` 中 `resolve_archive_root` 函数（约 4280 行附近）的判据分支顺序：移除"legacy 非空即降级"的自动行为，默认优先返回 primary。
- 保留"legacy 非空"时的 stderr 告警信息，但改为"提示用户运行 `harness migrate archive`"而非默认降级。
- 设计并暴露一个 opt-in 机制让调用方显式请求 legacy（可选方案：新增关键字参数 `prefer_legacy: bool = False`，或识别环境变量 `HARNESS_ARCHIVE_LEGACY=1`；由 executing 阶段最终敲定）。
- 扩展现有 `tests/test_archive_path.py`：新增"legacy 非空 + primary 空"场景下新归档仍落 primary 的断言；新增"显式 opt-in legacy"回归用例。

### Excluded

- 不实施 `harness migrate archive` 子命令本身（由 chg-02 负责）。
- 不修改 `resolve_requirement_root` / `resolve_bugfix_root` 的判据（保持现有 legacy-降级语义，避免牵扯过多）。
- 不迁移 legacy 目录下已有数据。

## 5. Acceptance

- Covers requirement.md **AC-03**：`resolve_archive_root` 默认优先返回 primary；仅显式 opt-in 时才返回 legacy。单元测试覆盖"legacy 非空时新归档仍落 primary"的 happy path + "显式 legacy 时返回 legacy"的对照用例。
- 运行 `harness status` / `harness archive` 时，若检测到 legacy 非空，stderr 打印一次迁移提示（`run harness migrate archive to consolidate`）而不再降级路径。

## 6. Risks

- **R1 兼容性破坏**：已有仓库若依赖"legacy 非空自动走 legacy"的旧行为，升级后新归档会落到 primary，可能出现"老归档在 legacy、新归档在 primary"的双轨状态 → 通过 stderr 告警引导用户跑 `harness migrate archive` 收敛（chg-02 负责），本 change 不消除双轨，但告警必须保留。
- **R2 测试脆弱**：`tests/test_archive_path.py` 可能已有对"legacy 非空时返回 legacy"的断言 → 执行阶段先 grep 核对旧断言语义，按新契约更新，不盲改。
