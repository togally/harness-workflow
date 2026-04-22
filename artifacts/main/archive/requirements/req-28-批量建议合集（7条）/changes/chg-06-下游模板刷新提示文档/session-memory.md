# Session Memory

## 1. Current Goal

- 执行 chg-06：在 README 追加"下游模板刷新提示"（覆盖 AC-10，小改）。

## 2. Current Status

- ✅ Step 1：定位 README 位置——英文 `README.md` 的 `## Installation` 节、中文 `README.zh.md` 的 `## 安装` 节均为现成合适插入点，无需新建文件。
- ✅ Step 2：在 README.md（英文）与 README.zh.md（中文）分别插入"Refreshing change / plan templates"/"刷新 change / plan 模板到最新版本"小节，内容包含 `pip install -U harness-workflow` 与"历史 change 是一次性快照"提示。
- ❌ Step 3：跳过（硬约束"不碰代码/CLI" + plan 标注为可选）。
- ✅ Step 4：无新增测试，按 plan 要求以 grep 静态检查。
- ✅ Verification 2.1：`grep "pip install -U harness-workflow" README*.md` 命中 README.md:64 与 README.zh.md:77。
- ✅ 对人文档 `实施说明.md` 已产出。

## 3. Validated Approaches

- 直接使用 Edit 工具在 Installation/安装 节的 "--force / harness install" 说明后插入小节，保持与既有 ### 三级标题风格一致。
- 双语项目同步更新英文/中文两个 README，内容对齐。
- Grep 静态校验替代单测，覆盖 AC-10。

## 4. Failed Paths

- 无。

## 5. Candidate Lessons

```markdown
### 2026-04-19 文档类 change 的最小交付面
- Symptom: 文档小改容易"顺手扩围"，可能误触 CLI help / 其他 md。
- Cause: plan 中存在"可选 Step"，执行时需显式对齐本轮硬约束。
- Fix: 把 plan 可选步骤 + 本轮硬约束一并写进 session-memory Step 对齐表，避免越界。
```

## 6. Next Steps

- 等待 testing 阶段 subagent 执行 Verification 2.1（grep）与 2.2（可选的下游 smoke，若需要由 chg-07 负责）。

## 7. Open Questions

- 无。
