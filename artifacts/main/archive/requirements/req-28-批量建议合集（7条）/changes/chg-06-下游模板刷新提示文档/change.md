# Change

## 1. Title

README 或 docs 增补"下游仓库如何刷新 harness change / plan 模板"提示

## 2. Goal

- 在项目根 `README.md` 或 `docs/` 下加 1~3 行提示，说明 harness change / plan 模板由已安装的 `harness_workflow` Python 包动态加载，下游用户升级包即可刷新模板，无需新的 CLI 子命令。

## 3. Requirement

- `req-28`

## 4. Scope

### Included

- 修改 `README.md`（优先）新增一个小节"升级模板"（或合并到既有"Install / Update"章节尾部）：
  - 一句话说明："如需刷新 harness change / plan 模板，升级 `harness_workflow` Python 包即可（`pip install -U harness-workflow` 或等价），无需额外 harness CLI 子命令。老的已落盘 change 是一次性快照，不会被覆盖。"
- 如 README 不合适，则改到 `docs/upgrade-templates.md`（新文件）。
- 不改 CLI。
- 可选：`harness update --help` 的描述文案中也同步这句话（只改 help text，不改行为）。

### Excluded

- 不新增 `harness update --refresh-templates` 类子开关。
- 不动已归档 req 的 change 产物。
- 不考虑从 source 安装（editable mode）场景的额外说明——留作未来 sug。

## 5. Acceptance

- Covers requirement.md **AC-10**：README 或 docs 有对应提示，行数 1~3 行，无 CLI 变更。

## 6. Risks

- 风险 A：README 文案位置与现有风格不搭 → 缓解：先读 README 现有"Install"章节的格式再插入相同风格的小节。
- 风险 B：`harness update --help` 若能无副作用同步这句话就加上；若 help text 由 argparse 描述字段固定则只在 README 补 → 缓解：先查 CLI 描述字段，不可行则跳过。
