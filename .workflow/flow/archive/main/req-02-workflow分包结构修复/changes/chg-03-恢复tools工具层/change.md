# chg-03 恢复 tools/ 工具层

## 目标

在 `.workflow/tools/` 下建立完整工具层，从 backup 迁移内容并更新路径引用，同时将角色文件的 `## 可用工具` 改为引用 `tools/stage-tools.md`。

## 范围

### 创建文件
- `.workflow/tools/index.md`（工具系统总览，从 backup 迁移，路径无需更新）
- `.workflow/tools/stage-tools.md`（各 stage 工具白名单，从 backup 迁移）
- `.workflow/tools/selection-guide.md`（工具选择指南，从 backup 迁移，更新路径引用）
- `.workflow/tools/maintenance.md`（工具维护规范，从 backup 迁移，路径无需更新）
- `.workflow/tools/catalog/_template.md`（从 backup 迁移）
- `.workflow/tools/catalog/agent.md`（从 backup 迁移）
- `.workflow/tools/catalog/bash.md`（从 backup 迁移）
- `.workflow/tools/catalog/edit.md`（从 backup 迁移）
- `.workflow/tools/catalog/grep.md`（从 backup 迁移）
- `.workflow/tools/catalog/read.md`（从 backup 迁移）

### 修改文件
- `.workflow/context/roles/requirement-review.md`：`## 可用工具` 改为引用 stage-tools.md
- `.workflow/context/roles/planning.md`：同上
- `.workflow/context/roles/executing.md`：同上
- `.workflow/context/roles/testing.md`：同上
- `.workflow/context/roles/acceptance.md`：同上
- `.workflow/context/roles/regression.md`：同上

### 路径更新（selection-guide.md 中）
- `workflow/context/roles/{stage}.md` → `.workflow/context/roles/{stage}.md`
- `state/requirements/{req-id}.yaml` → `.workflow/state/requirements/{req-id}.yaml`
- `state/sessions/{req-id}/...` → `.workflow/state/sessions/{req-id}/...`
- `state/experience/index.md` → `.workflow/state/experience/index.md`
- `context/experience/` → `.workflow/context/experience/`

### 不修改
- `context/experience/tool/`（工具经验层，独立存在，正确）
- backup 中的原始文件

## 验收标准

- [ ] `.workflow/tools/` 目录结构完整（index.md、stage-tools.md、selection-guide.md、maintenance.md、catalog/）
- [ ] `selection-guide.md` 中所有路径引用已更新为 `.workflow/` 前缀
- [ ] 各角色文件的 `## 可用工具` 已改为一行引用语句，不再内联白名单
- [ ] `tools/stage-tools.md` 的白名单内容与各角色文件原有内联内容一致
