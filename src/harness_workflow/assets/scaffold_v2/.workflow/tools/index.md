# 工具系统

## 四项核心能力
1. **注册**：每个工具在 `catalog/` 有独立文件，记录用法和迭代
2. **选择**：`stage-tools.md` 定义各阶段工具白名单；`selection-guide.md` 指导工具选择
3. **维护**：`maintenance.md` 定义新增、更新、淘汰工具的规范
4. **迭代**：使用经验 → session-memory → context/experience/tool/ → catalog 更新

## 文件索引
- `stage-tools.md`：各 stage 的可用工具集合
- `selection-guide.md`：工具选择决策与 subagent 派发规范
- `maintenance.md`：工具维护规范
- `catalog/`：工具详细定义（每工具一文件）
- `catalog/_template.md`：新增工具的标准模板

## 加载规则
- session-start：读本文件了解工具系统结构
- before-task：读 `stage-tools.md` 确认当前 stage 可用工具
- 需要工具选择决策时：读 `selection-guide.md`
- 需要了解具体工具用法时：读 `catalog/{tool}.md`
