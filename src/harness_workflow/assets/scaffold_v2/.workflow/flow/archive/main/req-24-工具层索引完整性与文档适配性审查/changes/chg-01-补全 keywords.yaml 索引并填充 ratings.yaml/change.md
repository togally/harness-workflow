# Change

## 1. Title

补全 keywords.yaml 索引并填充 ratings.yaml

## 2. Goal

让 toolsManager 在本地索引中能够命中 catalog/ 下已定义的所有工具，并具备基于评分的优先级排序能力。

## 3. Requirement

- `req-24`

## 4. Scope

**包含：**
- 读取 `catalog/` 下所有现有工具定义文件
- 为每个工具提取合适的 keywords，写入 `keywords.yaml`
- 为每个工具赋予初始评分，写入 `ratings.yaml`
- 确保 keywords 覆盖各 stage 角色的常见操作意图

**不包含：**
- 新增 catalog 工具定义
- 修改 toolsManager 角色的匹配算法

## 5. Verification

- `keywords.yaml` 包含 catalog/ 中所有已定义工具的完整条目
- `ratings.yaml` 包含所有工具的有效评分（1-5 分）
- 用模拟查询验证 toolsManager 能为 "读取文件"、"编辑文件"、"执行命令"、"搜索内容" 等意图返回匹配结果
