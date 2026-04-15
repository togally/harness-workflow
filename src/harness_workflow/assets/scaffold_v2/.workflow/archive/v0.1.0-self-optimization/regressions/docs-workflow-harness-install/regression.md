# Regression Intake

## 1. Issue Title

业务项目升级后 docs/ 旧数据与新生成的 workflow/ 目录共存，harness install 未提供迁移路径

## 2. Reported Concern

业务项目升级到新版 harness 后，`harness install` 在项目根目录新建了 `workflow/` 目录（空状态），但现有的工作流数据仍在 `docs/` 下（含版本 uav-split 的需求、变更、计划）。`AGENTS.md` 和 `CLAUDE.md` 被更新后指向 `workflow/` 路径，导致 Agent 读不到旧数据，工作流断掉了。

## 3. Current Behavior

- **复现路径**：在已有 `docs/` 工作流数据的旧项目中运行 `harness install`（或 `harness update`）
- **实际表现**：
  - 新建 `workflow/` 目录结构（空 runtime、空版本目录）
  - 更新 `AGENTS.md` 和 `CLAUDE.md` 中的路径引用至 `workflow/`
  - 不检测、不迁移已有的 `docs/` 数据
  - Agent 按新配置读 `workflow/context/rules/workflow-runtime.yaml`，看到空 runtime，提示 `harness active "<version>"`，但版本数据根本不在 `workflow/versions/` 下
- **代码根因**：
  - `WORKFLOW_RUNTIME_PATH = Path("workflow") / ...`（`core.py:21`）硬编码为新路径
  - `_required_dirs` 和 `_managed_file_contents` 只创建 `workflow/` 下的结构
  - `init_repo` / `install_repo` / `update_repo` 均无 `docs/` 检测或迁移逻辑
- **影响**：已有版本（uav-split）的全部数据滞留在 `docs/`，对工具不可见；用户被迫手动迁移

## 4. Expected Outcome

`harness install` 或 `harness update` 应检测已有的 `docs/` 目录：
- 若 `docs/versions/`、`docs/context/` 等子目录存在，自动将数据迁移至 `workflow/` 对应结构
- 或打印明确警告，告知用户如何手动迁移，并拒绝覆盖 `AGENTS.md`/`CLAUDE.md` 直到迁移完成

## 5. Next Step

确认为真实问题，转为新 change：**"harness install/update 支持 docs/ → workflow/ 自动迁移"**
