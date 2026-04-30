# Session Memory — chg-01（CLI 入口 harness pad + 反非法 lint）

## 1. Current Goal

为 chg-01 落 plan.md（§1~§5），确定文件 / 行号 / 函数名 / 测试用例 / 验收 lint 字面。

## 2. Context Chain

- Level 0: 主 agent（technical-director / opus）
- Level 1: analyst / opus（本次 subagent，Phase 2 + Phase 3 一气完成）

## 3. 关键决策（chg-01 范围内）

- **PAD_KINDS 常量位置**：`workflow_helpers.py` 顶层，紧邻 `_SCAFFOLD_V2_MIRROR_WHITELIST`（约 line 209）。理由：与既有"模块级常量"约定一致，便于 chg-02/03/04 import；不放 cli.py 是因为 chg-04 dogfood 要在 helper 层独立测试。
- **`tool` kind 不分 scope 的位置参数 normalize**：`harness pad tool "title"` 在 dispatch 层把 scope_raw 当 title。理由：保持 CLI 形态对称（`pad <kind> [<scope>] <title>` 在 user 视角下），不强制 user 写 `pad tool "" "title"`。
- **stub helper 同时落地**：`_pad_add` / `_pad_list` / `_pad_interactive` 三 stub 在 chg-01 落地（exit 0 + 占位 stdout），让 dispatch 链路在 chg-01 即闭环；chg-02/03/04 替换 helper 实现而非新加 helper。理由：降低 chg 间耦合 + 让 chg-01 单独可测。
- **测试入口**：`tests/test_req53_pad_cli.py` 用 subprocess 跑，避免 argparse SystemExit 干扰 pytest。

## 4. 未做（chg-01 边界）

- 不真实落位文件（chg-02 做）
- 不真实登记 index.md（chg-03 做）
- 不调 git add（chg-03 做）
- 不真实 questionary 引导（chg-04 做）
- 不真实扫描 list（chg-04 做）

## 5. 待沉淀经验（chg 完成后回填）

- "命令分流：list 复用 kind 位置参数 vs 加 `--list` flag 取舍"
  - 取舍依据：requirement.md OQ-Verdicts 已定 `add`（默认）+ `list` 两子命令；list 复用 kind 位置参数（`pad list`）比 `--list` 更接近 git/docker subcommand 风格，与 `harness suggest --list` 不同（suggest 是 flag），原因是 suggest 还有 --apply / --delete 多 flag 需共存，pad 仅 add+list 两路径。
- "stub-then-replace 渐进策略"：chg-01 落 stub 让 dispatch 闭环，chg-02/03/04 替换 helper 实现，避免 chg 间循环依赖。

## Executing Stage 完成记录

- PAD_KINDS 常量已落 line 214（紧邻 _SCAFFOLD_V2_MIRROR_WHITELIST）
- 5 helper（_validate_pad_kind / _validate_pad_scope + 3 stub）全部落地
- cli.py pad subparser + dispatch 分支已加
- 修复：tool kind normalize 必须在 _validate_pad_scope 前（否则 scope_raw 被误判为 scope 而 ABORT）
- 测试：8 TC 全 pass（test_req53_pad_cli.py）
- 契约：artifact-placement PASS / user-write-protected-zones PASS

✅ chg-01 完成
