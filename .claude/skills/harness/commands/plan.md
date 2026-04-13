# harness plan "<chg-id>"

## 前置条件
- 当前 stage 是 `planning`
- 指定的 change 存在

## 执行步骤
1. 读取对应 `change.md` 了解变更范围
2. 创建 `plan.md` 于变更目录下
3. 引导架构师填写执行步骤、产物和依赖

## plan.md 初始模板
```markdown
# 执行计划：{chg-id}

**状态:** draft

## 执行步骤
### Step 1
### Step 2

## 产物清单
| 文件 | 操作 |
|------|------|

## 依赖
```
