# chg-01 修复主加载链

## 目标

将 `evaluation/`、`team/`、`project/`、`tools/` 的加载时机写入 `context/index.md`，消除主加载链断点。

## 范围

### 修改文件
- `.workflow/context/index.md`：补充 Step 的加载规则
- `.workflow/context/project/project-overview.md`：填写实际项目内容

### 不修改
- 其他任何文件

## 验收标准

- [ ] `context/index.md` 中新增 tools/index.md 的 session-start 加载规则
- [ ] `context/index.md` 中 Step 2 或新增步骤说明 testing/acceptance/regression 阶段需加载对应 `evaluation/{stage}.md`
- [ ] `context/index.md` 中有 `team/development-standards.md` 的加载时机说明
- [ ] `context/index.md` 中有 `project/project-overview.md` 的加载时机说明
- [ ] `context/project/project-overview.md` 有实际内容（非空模板）
- [ ] `context/index.md` 与实际目录结构一致，无悬空引用
