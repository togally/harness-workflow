---
id: chg-02
title: "analyst.md Step A1.5 改造 + adapter 强制门 + mirror 同步"
parent_req: req-56
operation_type: plan
---

## 1. Scope（精确文件 + 改动点）

### F1：`.workflow/context/roles/analyst.md`

- L41-L102 段（**Step A1.5 整段** + adapter + fallback）重写：
  - **Step A1.5 头段**改为：
    ```
    **Step A1.5: gstack /office-hours 强映射执行（按 office_hours_mode 字段直跑）**
    
    本角色与 gstack `/office-hours` 强映射（[req-55:gstack-harness 融合] chg-02 落地，[req-56:--fallback 默认改造] chg-02 改为读字段直跑）。读取本 req 的 `.workflow/state/requirements/{req-id}-{slug}.yaml.office_hours_mode` 决定走向：
    
    - `office_hours_mode == "required"`（默认 / 用户未传 --fallback / agent 兼容）→ 走 path α
    - `office_hours_mode == "fallback"`（用户显式 --fallback / agent 不兼容时 CLI 已自动落字段）→ 跳过 path α 直接进 Step A2，在 batched-report 第一行加一句 `[mode] fallback：office-hours 已 opt-out，本 req requirement.md 由 analyst 手工填实`
    - 字段缺失（老 req 兼容）→ 视同 required
    ```
  - **path α 触发流程**：保留现行 1-4 步骤；删除"询问用户"语义；
  - **Step A1.5.adapter 段头**追加："**必经环节**：office-hours 路径必须经 adapter 重组，不允许 design doc 直接当 requirement.md 使用绕道。"
  - **Step A1.5 退出门**新增（adapter 完成后）：
    ```
    **Step A1.5 退出门（office-hours 路径必经）**：
    
    adapter 完成后立即跑：
    - `harness validate --human-docs`（exit 0）
    - `harness validate --contract artifact-placement`（exit 0）
    
    任一非 0 → ABORT 不得推进；analyst 必须修正 requirement.md 直到双绿才离开 Step A1.5。
    ```
  - **Step A1.5.fallback 子段**改名为 **Step A1.5.escape**，触发场景缩为单一：
    ```
    **Step A1.5.escape: 用户/主 agent 中途拒派发**
    
    触发场景：office_hours_mode == required，但主 agent / 用户在执行中明确拒绝跑 /office-hours。
    
    行为：
    - 不阻塞推进；analyst 转 Step A2 手工填实
    - batched-report 写入：`/office-hours 派发被拒，本 req requirement.md 由 analyst 手工填实（escape 路径，与 fallback 模式同效果）`
    - 不修改 office_hours_mode 字段（保持 required，作 lineage 留底）
    
    （原场景 1 / 场景 2 — agent_kind_compatible=false / gstack_status 不存在 — 已由 chg-01 在 CLI 入口自动兜底为 fallback 模式，analyst 此处不再判断）
    ```

### F2：`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md`

- 与 F1 1:1 同步（硬门禁五）。

## 2. 实施步骤

1. **Step 1**：F1 改 live analyst.md（4 块编辑：Step A1.5 头段重写 / adapter 段头加"必经" / 退出门新增 / fallback 改名 escape + 内容缩窄）。
2. **Step 2**：F2 mirror 同步（一次性 cp 或同等 Edit 全文一致）。
3. **Step 3**：自检：
   - 3.1 `diff -q .workflow/context/roles/analyst.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md` silent
   - 3.2 grep 退出门字面命中
   - 3.3 grep "请选择.*office-hours" / "是否.*office-hours" 不命中（offer 已删）
   - 3.4 grep `office_hours_mode` Step A1.5 内 ≥ 1
4. **Step 4**：`harness validate --human-docs` exit 0；`harness validate --contract artifact-placement` exit 0；`harness validate --contract role-stage-continuity`（如存在）不恶化。

## 3. 依赖

- 上游：chg-01（state schema `office_hours_mode` 字段已落地）。
- 下游：chg-03（skill 文档说明对 analyst 的引用与 dogfood TC 联动）。

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - .workflow/context/roles/analyst.md
> - src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md

本 chg 为文档改动，主要靠 grep / diff 静态校验 + 后续 chg-03 dogfood TC 端到端覆盖（不在本 chg 强行重复造 dogfood，避免与 chg-03 责任重叠）。

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | grep `office_hours_mode` analyst.md Step A1.5 块 | 命中 ≥ 1 | AC-01 | P0 |
| TC-02 | grep `必经环节` analyst.md Step A1.5.adapter 段 | 命中 ≥ 1 | AC-07 | P0 |
| TC-03 | grep `harness validate --contract artifact-placement` Step A1.5 退出门段 | 命中 ≥ 1 | AC-07 | P0 |
| TC-04 | grep `请选择.*office-hours\|是否.*office-hours` analyst.md | 命中 == 0（offer 句式已删） | AC-01 | P0 |
| TC-05 | grep `Step A1.5.escape` analyst.md | 命中 ≥ 1（fallback 改名 escape） | AC-02 | P0 |
| TC-06 | diff -q live mirror | silent | AC-07 | P0 |
| TC-07 | `harness validate --human-docs` | exit 0 | AC-06 | P0 |

## 5. 验收 lint 命令字面

```bash
# AC-01：office_hours_mode 字段被 analyst 读取
grep -c 'office_hours_mode' .workflow/context/roles/analyst.md   # 期望 ≥ 1
grep -c '请选择.*office-hours\|是否.*office-hours' .workflow/context/roles/analyst.md   # 期望 == 0

# AC-07：adapter 必经 + 退出门
grep -c '必经环节' .workflow/context/roles/analyst.md   # 期望 ≥ 1
grep -c 'harness validate --contract artifact-placement' .workflow/context/roles/analyst.md   # 期望 ≥ 1

# AC-02：escape 改名（原 fallback 子段重定义）
grep -c 'Step A1.5.escape' .workflow/context/roles/analyst.md   # 期望 ≥ 1

# mirror 同步
diff -q .workflow/context/roles/analyst.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md   # silent

# AC-06：human-docs
harness validate --human-docs   # exit 0
harness validate --contract artifact-placement   # exit 0
```

## 6. scaffold_v2 mirror 同步清单

| Live 文件 | Mirror 路径 | 同步语义 |
|-----------|-----------|---------|
| `.workflow/context/roles/analyst.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md` | 全文一致 |

实施约束：live + mirror **同 commit** 落地（硬门禁五）。
