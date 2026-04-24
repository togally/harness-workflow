# Acceptance Stage 规则

> **req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界））/ chg-03（S-C testing/acceptance 职责边界精简）收窄**：acceptance 职责已收窄为"对照 requirement.md AC-N 逐条最终签字 + 归档前 gate"，单轮会话完成。技术验证由 testing 阶段 test-report.md 权威覆盖，acceptance 信任 testing 结论。独立 subagent 派发保留（§7 E-3 default-pick = A）。

## 核心要求
- 验收官不参与修复，只判定
- AI 对照 requirement.md AC-N 逐条最终签字，人工做归档前 gate 判定
- 技术验证（R1 / revert / 契约 7 / req-29 / req-30）已由 testing 阶段 test-report.md 覆盖，acceptance 信任 testing 结论，不重跑

## 验收活动

### 1. AC 签字（AI 执行）
- 对照 requirement.md 验收标准逐条核查
- 每条标准直接引用 test-report.md / 变更产物作为证据，给出签字：✅ / ❌ + 一句话说明
- 不重跑技术测试，不独立执行 R1 / revert / 契约 7 扫描（由 testing 负责）

### 2. 归档前 gate
- **[硬门禁]** acceptance 前必须执行 `harness validate --human-docs`；未绿 ABORT，退出码非零（非零退出码）则 `acceptance-report.md` `状态` 字段必须执行 = FAIL、不得 PASS 放行（req-39（对人文档家族契约化 + artifacts 扁平化）/ chg-04（acceptance gate 强执行：lint 阻塞 + 未绿 FAIL）落地升级）；路由建议：
  - 缺 `需求摘要.md` → `harness regression` 回 requirement_review
  - 缺 `chg-NN-变更简报.md` → `harness regression` 回 planning
  - 缺 `chg-NN-实施说明.md` → `harness regression` 回 executing
- 检查 runtime.yaml 与 state/requirements/{req-id}.yaml 状态一致性（sug-05 保留）
- 列出需人工操作验证的项目（如 UI 交付），由用户最终 gate 判定

### 3. 极简 `acceptance-report.md`（≤ 30 行）

```markdown
## 验收报告

### AC 签字表

| AC 编号 | 签字 | 证据（测试记录 / 产物路径） | 备注 |
|--------|------|---------------------------|------|
| AC-XX  | ✅   | test-report.md 第 N 行 / artifacts/... | 短注 |

### 异议流转建议
（若任一 AC 签 ❌，说明建议 harness regression 的路由方向：requirement_review / testing / executing）

### 最终 gate（由人工填写）
通过 / 驳回 + 原因；驳回必须触发 harness regression。
```

## 完成条件

**前置硬门禁**：`harness validate --human-docs` exit code = 0 才进入人工判定；未绿则 FAIL 不走人工 gate。

- 人工判定通过 → `harness next` → `done`
- 人工判定驳回 → `harness regression "<驳回原因>"` → 路由
