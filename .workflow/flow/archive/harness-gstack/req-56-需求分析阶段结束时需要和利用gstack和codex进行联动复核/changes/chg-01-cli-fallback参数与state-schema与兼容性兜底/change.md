---
id: chg-01
title: "CLI --fallback 参数 + req-state.yaml office_hours_mode schema + agent 兼容性兜底"
created_at: 2026-05-09
operation_type: change
requirement_id: "req-56"
---

# Change

## 1. Title

CLI --fallback 参数 + req-state.yaml office_hours_mode schema + agent 兼容性兜底

## 2. Goal

- 在 `harness requirement` CLI 入口加 `--fallback` 标志，把"office-hours 默认/fallback opt-out"的用户决策落盘到 req-state.yaml 顶层 `office_hours_mode` 字段，供 analyst 跨 session 一致读取。
- 检测 `runtime.yaml.gstack_status.agent_kind_compatible == false` 时即使无 flag 也强制 fallback + stdout 警告，避免非 Claude Code 用户被卡住。

## 3. Requirement

- `req-56`

## 4. Scope

### Included

- `src/harness_workflow/cli.py`：`req_parser` argparse 加 `--fallback` action='store_true'；dispatch 块透传到 `harness_requirement.py`。
- `src/harness_workflow/tools/harness_requirement.py`：argparse 加 `--fallback`；透传给 `create_requirement(...)` 新参 `fallback: bool = False`。
- `src/harness_workflow/workflow_helpers.py`：
  - `create_requirement` 新参 `fallback: bool = False`
  - 读取 `runtime.yaml.gstack_status.agent_kind_compatible`（缺失/false → 兜底）
  - 计算最终 mode: `fallback OR not agent_kind_compatible → "fallback"; else "required"`
  - state yaml 新增 `office_hours_mode` 字段写入 + ordered_keys 同步
  - 兜底走兼容路径时 stdout 打印 `[gstack] agent 不兼容，本 req 自动 fallback 模式`
  - 显式 `--fallback` 时 stdout 打印 `[mode] fallback`
- 老历史 req（state 文件无 `office_hours_mode`）兼容：read 时缺字段返回 `"required"` 默认。
- 单元测试 `tests/installer/test_requirement_fallback_flag.py`：覆盖 4 种 (flag × 兼容性) + 老 req 缺字段兼容场景。

### Excluded

- 不动 analyst.md（chg-02 负责）
- 不动 skill 文档（chg-03 负责）
- 不动 /office-hours skill 自身
- 不写集成 dogfood TC（chg-03 负责）

## 5. Acceptance

- 覆盖 requirement.md 的 **AC-01 / AC-02 / AC-03 / AC-04 / AC-05（单元部分）/ AC-06**：
  - 无 flag + 兼容 → state.office_hours_mode=required；无 stdout 警告
  - 无 flag + 不兼容 → state.office_hours_mode=fallback；stdout 含 `[gstack] agent 不兼容` 字样
  - --fallback + 兼容 → state.office_hours_mode=fallback；stdout 含 `[mode] fallback`
  - --fallback + 不兼容 → state.office_hours_mode=fallback；stdout 含两条提示
  - 老 req（缺字段）→ load 时返回 required，不破坏 archived
  - `harness validate --human-docs` exit 0 / `harness validate --contract artifact-placement` exit 0

## 6. Risks

- **risk-1 simple_yaml ordered_keys 漏配** → state.yaml 反写丢字段（前车之鉴 bugfix-11 B2）：缓解 = ordered_keys 显式追加 `office_hours_mode`；新增 round-trip 测试断言字段存活。
- **risk-2 老历史 req archive 后被重新读** → 缺字段崩溃：缓解 = `load_requirement_state` 缺字段 default `required`，不抛异常。
- **risk-3 gstack_status 字段本身不存在**（早期版本 / install 未跑）：缓解 = 视同 agent_kind_compatible=false → 自动 fallback；与 chg-01 of req-55 fallback 场景 2 同语义。
