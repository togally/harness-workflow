# Regression Analysis

## 1. Problem Assessment

**真实缺陷**：版本升级破坏了现有项目的工作流状态，没有提供向前迁移路径。

## 2. Evidence

- `core.py:21` `WORKFLOW_RUNTIME_PATH = Path("workflow") / "context" / "rules" / "workflow-runtime.yaml"` — 新版硬编码 `workflow/`，旧版使用 `docs/`
- `_required_dirs`（`core.py:1588`）只创建 `workflow/` 下的目录结构，完全忽略 `docs/`
- `init_repo`（`core.py:2455`）：`write_if_missing` 跳过已有文件，但不检测 `docs/` 是否存在旧数据
- `install_repo`（`core.py:2483`）：调用 `install_local_skills` + `init_repo`，均无迁移逻辑
- `update_repo`（`core.py:2491`）：有 managed 文件更新逻辑，但同样无 `docs/` 检测
- 结果：用户运行 `harness install` 后，`AGENTS.md`/`CLAUDE.md` 更新为新路径，旧数据孤立在 `docs/`，Agent 无法找到现有版本

## 3. Discussion Outcome

用户在业务项目中已复现此问题。现有版本（uav-split）数据完整但不可访问。

## 4. Recommended Action

确认为真实问题。修复方案：
1. `install_repo` / `update_repo` 开始时检测 `docs/` 是否存在旧工作流数据（特征：`docs/context/rules/workflow-runtime.yaml` 或 `docs/versions/` 存在）
2. 若存在：自动将 `docs/` 下的目录结构整体移动/复制到 `workflow/`（不覆盖 `workflow/` 中已存在的文件）
3. 迁移完成后打印摘要；若有冲突则列出并跳过
4. 若无法自动迁移（有冲突），则拒绝继续并告知用户手动解决

转为新 change：**"harness install/update 支持 docs/ → workflow/ 自动迁移"**
