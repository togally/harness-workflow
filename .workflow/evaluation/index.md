# 评估与观测层

## 核心原则：生产者与评估者必须独立

执行 subagent 和评估 subagent 不能是同一个实例。只有独立的评估者才能形成有效的反馈闭环。

## 第五层管辖的 Stage

| Stage | 规则文件 | 角色 |
|-------|---------|------|
| `testing` | `evaluation/testing.md` | 测试工程师 |
| `acceptance` | `evaluation/acceptance.md` | 验收官 |
| `regression` | `evaluation/regression.md` | 诊断师 |

## 进入第五层的时机

```
第三层 executing 完成
    ↓ harness next
第五层 testing 开始（主 agent 派发独立测试 subagent）
    ↓ 全部通过
第五层 acceptance 开始（主 agent 派发独立验收 subagent）
    ↓ 人工判定通过
done
```

## 回归路由规则

```
任意阶段发现问题 → regression
    ↓ 诊断后
    ├── 需求/设计层面问题 → requirement_review
    └── 实现/测试层面问题 → testing
```

## 加载规则

进入 testing / acceptance / regression 时：
1. 加载对应角色文件（`context/roles/{stage}.md`）
2. 加载本层对应规则文件（`evaluation/{stage}.md`）
3. 加载经验：`context/experience/stage/testing.md` / `context/experience/stage/acceptance.md` + `context/experience/risk/known-risks.md`（regression时）
