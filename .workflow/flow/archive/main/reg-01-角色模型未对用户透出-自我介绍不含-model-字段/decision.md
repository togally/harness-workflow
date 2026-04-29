# Regression Decision — reg-01（角色模型未对用户透出：自我介绍不含 model 字段）

## 1. Decision Status

- **analysis** ← 当前（等待主 agent 与用户确认路由）
- `confirmed`（真实问题，是某个已存在 requirement 的 bug 需要回到 testing / requirement_review 修复）
- `rejected`（误判）
- `converted:--requirement`（转新需求）
- `converted:--change`（转已有需求的新变更）

## 2. Final Notes

- 诊断结论：**真实问题**，不是 req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet））的 bug，而是 req-29 的 **Scope 盲区**。req-29 已归档全绿（288 tests passed），不应被判定为回归。
- 问题本质：req-29 锁定了后台配置面 + dispatch 面的 model 映射，但缺少"用户面"——subagent 自我介绍模板不含 model 字段，主 agent 派发说明文案也不显式透出 model，用户观察不到映射生效。
- 诊断师推荐方案：**方案 B**（自我介绍模板 + 派发说明文案双面加 model 字段）。详见 `analysis.md` §4~7。

## 3. Follow-Up — 路由建议

### 排除项

- **`--confirm`（路由回 testing / requirement_review）**：不适用。这不是 req-29 实现偏离 AC 或 requirement 覆盖不全，而是 req-29 AC 本身就不含"对用户透出 model"，Scope 外新增诉求 confirm 后没有可回的 stage。
- **`--reject`**：不适用。用户诉求合理，确实存在用户面空白。
- **`--change <title>`**：不适用。req-29 已归档，没有 active requirement 可挂 change；若重开 req-29 加 chg 会破坏归档的 done 状态，不建议。

### 推荐项

**`--requirement <title>`** — 转为新需求。

- 建议标题：**`角色 model 对用户透出：自我介绍 + 派发说明补 model 字段`**。
- 理由：
  - req-29 已归档，没有 active requirement 可挂 change；
  - 修复面涉及 2-3 个契约文件（`base-role.md` / `stage-role.md` / `ROLE-TEMPLATE.md`）+ 若干 role 文件（`harness-manager.md` / `technical-director.md`）+ 派发协议文案调整，粒度够一个小 req；
  - 走完整 harness 流程（requirement_review → planning → executing → testing → acceptance → done）可把这个用户面锁进契约与测试，避免下次又漏。

### 建议的 requirement 骨架（供 requirement-review 阶段参考）

- **AC-1**：`base-role.md` 硬门禁三模板在 `[角色名称]` 后形如 `（role-key / model）`，示例 2 条全部含 model 字段。
- **AC-2**：`harness-manager.md` Step 0 自我介绍含 model；3.6 派发协议追加"派发说明文案首次提到 subagent 必须形如 `派发 {role}（{model}）执行 {task_short}`"规则。
- **AC-3**：`technical-director.md` Step 0 自我介绍含 model；Step 4 briefing 模板说明同步"对用户说明文案必须透出 model"。
- **AC-4**：`stage-role.md` 公共父类清单第 3 项说明同步；Session Start 约定段点一句子 agent 自我介绍模板 `我是 Subagent-L{N}（{role} / {model}）`。
- **AC-5**：`ROLE-TEMPLATE.md` 硬门禁三示例同步。
- **AC-6**：端到端自证 — 任意发起一次派发（如 `harness next` 触发 executing 派发），主 agent 文案 + subagent 自我介绍都能在 stdout 看到 model 字段，用户一眼可辨 Opus / Sonnet。
- **AC-7（可选）**：在 `experience/tool/harness.md` 追加一小节"model 对用户透出的 3 个面"（配置面 / dispatch 面 / 用户面），把本 reg 的诊断结论沉淀为经验。

### 交接给主 agent 的决策点

主 agent 需要向用户确认：

1. **方案决策**：采纳 A（仅自我介绍）/ B（自我介绍 + 派发文案，推荐）/ C（升契约 + lint，重）中的哪一个？
2. **路由决策**：按推荐走 `harness regression --requirement "角色 model 对用户透出：自我介绍 + 派发说明补 model 字段"`，还是另有意图（如重开 req-29 加 chg）？

收到用户回复后，由主 agent 调用对应 `harness regression --*` 命令完成路由。诊断师**不**自行执行该命令。
