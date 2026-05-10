---
id: chg-02
title: "analyst.md Step A1.5 改造（读 office_hours_mode 直跑）+ adapter SOP 强制门 + scaffold_v2 mirror 同步"
created_at: 2026-05-09
operation_type: change
requirement_id: "req-56"
---

# Change

## 1. Title

analyst.md Step A1.5 改造（读 office_hours_mode 直跑）+ adapter SOP 强制门 + scaffold_v2 mirror 同步

## 2. Goal

- 把 analyst Step A1.5 从"offer 选择 + 用户挑"改为"读 chg-01 落地的 `office_hours_mode` 字段直跑"，删除选择句式与争议点列举，降低对话往返。
- adapter SOP 段映射表标"必经"，加 Step A1.5 退出门：office-hours 路径下 `harness validate --contract artifact-placement` exit 0 才能离开 Step A1.5；杜绝 design doc 直接当 requirement.md 用绕道。

## 3. Requirement

- `req-56`

## 4. Scope

### Included

- `.workflow/context/roles/analyst.md` Step A1.5：
  - 触发流程改读 `req-state.yaml.office_hours_mode`（required → 走 path α；fallback → 直接转 Step A2 + warn 留痕）
  - 删除"offer 选择"句式（与 harness-requirement skill focus 的 "discuss whether requirement is correct" 不冲突，仅去掉强映射环节的双向问询）
  - 加 Step A1.5 退出门：office-hours 路径必跑 `harness validate --contract artifact-placement`（exit 0 才能离开）
  - 场景树重写：场景 1（`agent_kind_compatible=false`）+ 场景 2（`gstack_status` 不存在）合并到 chg-01 已落地的"CLI 自动兜底"出口；analyst 只负责 fallback 模式的执行，不再做 fallback 决策；场景 3（用户/主 agent 拒派发）保留作 escape hatch。
  - adapter SOP 段映射表保持原状（office-hours design doc 段 → requirement.md 段映射），但段头加"必经"标注。
- mirror 同步：`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md` 与 live 1:1 同步（硬门禁五）。

### Excluded

- 不动 CLI / state schema（chg-01 负责）
- 不动 skill 文档 / 测试（chg-03 负责）
- adapter SOP 段映射表条目本身不增不减（仅加"必经"标注）
- 不动 Step A2 / A3 / Part B（fallback 路径走原生 SOP，无需修改）

## 5. Acceptance

- 覆盖 requirement.md 的 **AC-01（analyst 不再 offer）/ AC-02（analyst 跳过 path α）/ AC-07（adapter 强制门）**：
  - analyst.md Step A1.5 grep "office_hours_mode" 命中
  - analyst.md Step A1.5 grep "请选择.*office-hours.*fallback\|是否.*office-hours" 不命中（offer 句式已删）
  - analyst.md Step A1.5 grep "harness validate --contract artifact-placement" 命中（退出门）
  - analyst.md Step A1.5.adapter 段头含 "必经" 字面
  - live ↔ mirror diff 静默
  - `harness validate --human-docs` exit 0

## 6. Risks

- **risk-1 mirror 漏同步** → bugfix-13 / req-54 同型病：缓解 = chg-02 实施时 live + mirror 同 commit；diff 自检纳入 plan Step 5。
- **risk-2 退出门误伤 fallback 路径**（fallback 没经 adapter 也被卡）：缓解 = 退出门只挂 office-hours 路径分支（按 mode 判断），fallback 走原 Step A3 末尾验证。
- **risk-3 删 offer 后用户后悔**（这次定 office-hours，跑了一半想转 fallback）：缓解 = 文档加一句 "如需中途转 fallback，先 `harness regression "想换 fallback 模式"` 走 regression 重置 mode"；不在本 chg 实现 mode 切换 CLI（属新 sug 候选）。
