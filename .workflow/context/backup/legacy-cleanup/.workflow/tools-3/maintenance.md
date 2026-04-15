# 工具维护规范

## 新增工具
```
1. 复制 catalog/_template.md → catalog/{tool-name}.md
2. 填写所有字段
3. 在 stage-tools.md 中补充该工具适用的 stage
4. 在 index.md 工具列表中登记
```

## 迭代工具（改进已有工具的用法）
```
使用中发现更好的用法或踩了坑
    ↓
写入 session-memory "待沉淀经验"
    ↓
after-task hook 触发 → 沉淀到 context/experience/tool/{topic}.md
    ↓
经验成熟后（多次验证） → 更新 catalog/{tool}.md 的"迭代记录"区块
```

## 淘汰工具
```
1. 在 catalog/{tool}.md 顶部标记：**[DEPRECATED]** 替代方案：{新工具}
2. 在 stage-tools.md 中移除该工具
3. 不删除文件，保留历史
```

## 工具评估标准
新工具纳入标准：
- 在至少 2 个不同任务中验证有效
- 有明确的适用场景（不是"万能工具"）
- 有不适用场景说明（防止误用）
