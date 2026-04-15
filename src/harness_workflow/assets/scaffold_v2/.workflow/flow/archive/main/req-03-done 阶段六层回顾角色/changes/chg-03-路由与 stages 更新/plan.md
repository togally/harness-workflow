# Change Plan

## 1. Development Steps

1. **更新 context/index.md 路由表**：
   - 读取 `context/index.md` Step 2 路由表（表格形式）
   - 在表格末尾添加一行：`done → done.md`，并在备注列添加（主 agent 执行）
   - 确保路由表仍然保持正确的 Markdown 表格格式

2. **更新 flow/stages.md done 阶段定义**：
   - 读取 `flow/stages.md`，定位到 done 阶段定义（通常在文件末尾附近）
   - 扩展 done 阶段定义：
     - 角色：主 agent（非 subagent）
     - 动作：读取 `context/roles/done.md` 作为检查清单，执行六层回顾
     - 输出：回顾报告写入 session-memory.md
     - 归档：仍支持 `harness archive` 命令
   - 确保引用 `done.md` 文件路径正确

## 2. Verification Steps

1. **context/index.md 检查**：
   - Step 2 路由表是否包含 `done → done.md` 条目？
   - 是否有标注（主 agent 执行）？
   - 表格格式是否完好？

2. **flow/stages.md 检查**：
   - done 阶段定义是否明确主 agent 执行（非 subagent）？
   - 是否引用 `done.md` 作为检查清单？
   - 是否包含六层回顾动作说明？
   - 是否保持归档命令说明？

3. **一致性检查**：
   - 两处文件的引用是否一致（都指向 `context/roles/done.md`）？
   - 角色定位是否一致（都是主 agent）？
