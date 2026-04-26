# Regression 规则

## 核心要求
- 诊断优先于修复：确认是真实问题后才能转入修复
- 诊断师独立于执行者，不带实现偏见
- 需要人工信息时，先填 `required-inputs.md`，再请人工补充

## 诊断流程

```
触发：harness regression "<issue描述>"
    ↓
Step 1  收集证据
        → 读相关日志、报错信息、代码
        → 复现问题（如可复现）

Step 2  根因分析
        → 问题根因是什么？（不只是现象）
        → 是否真实存在？（排除误报）

Step 3  判断问题类型
        ├── 需求/设计有误 → 路由 requirement_review
        └── 实现/测试有误 → 路由 testing

Step 4  产出 diagnosis.md
Step 5  执行路由命令
```

## diagnosis.md 格式

```markdown
## 问题描述
（触发 regression 的现象）

## 证据
（日志、报错、截图描述）

## 根因分析
（为什么会发生，不是"因为代码有bug"这种废话）

## 结论
- [ ] 真实问题 / [ ] 误判

## 路由决定
- 问题类型：需求/设计 或 实现/测试
- 目标阶段：requirement_review 或 testing

## 需要人工提供的信息
（如有，详见 required-inputs.md）

## 测试用例设计
> （**bugfix 模式必填**，req 模式可选；bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） C2）
> regression_scope: targeted
> 波及接口清单：
> - {file1}

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | ... | ... | AC-01 | P0 |
```

## 测试用例设计契约（bugfix 模式，C2）

> bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） B5 lint 在 bugfix 流程的覆盖（C3 确认）。

**bugfix 模式 diagnosis.md 必须包含 §测试用例设计 章节**：
- `regression_scope` 字段（默认 `targeted`）；
- 波及接口清单（`git diff --name-only` + 修复方案人工补全）；
- 用例表（每个波及接口至少 1 条用例，`对应 AC` 字段非空）；

验证方式：`harness validate --contract test-case-design-completeness`（B5 lint 规则 3 / C3）；
缺段或用例数=0 → FAIL，阻断 regression 阶段退出。

## 路由命令

```
确认真实问题 → harness regression --confirm
               主 agent 根据诊断结论更新 stage

误判         → harness regression --reject
               回到触发前的 stage

取消诊断     → harness regression --cancel
               回到触发前的 stage
```
