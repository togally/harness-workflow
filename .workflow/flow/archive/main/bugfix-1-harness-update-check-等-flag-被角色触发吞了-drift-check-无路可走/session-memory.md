# Session Memory — bugfix-1

## 1. Current Goal

- bugfix-1（harness update --check 等 flag 被角色触发吞了，drift check 无路可走）在 regression stage 完成诊断 + 产出 bugfix.md / diagnosis.md。

## 2. Current Status

- diagnosis.md：已落地（代码层根因 / 契约层根因 / routing = real issue → executing）。
- bugfix.md：8 节模板已覆写（问题/复现/根因/3 方案/推荐 A/修复路径/影响面/8 条 AC）。
- required-inputs.md：保持空（用户已授权 ff，无需补输入）。

## 3. Validated Approaches

- `grep "args.command == \"update\""` 定位 cli.py L400-L409 handler severed 段。
- 对照 chg-02 `change.md` L11 / L37-L38 / L95 证实 P-B2 为故意设计；对照 install_parser L160-L163 证实承诺替代路径 `harness install --check` **从未注册 flag**（= scope 盲区非故意简化）。
- 对照 `install_repo` L3095-L3230 + `update_repo` L3387-L3403 空壳委托 + `scan_project(root)`，Python API 侧 drift 能力完整。
- 推荐方案 A 理由：最小改动（1 段 handler + 3 段 md），零 breaking，恢复 drift CLI 入口且保留 chg-02 角色契约。

## 4. Failed Paths

- Attempt: 无（本 regression 为首次诊断，未走过 false-positive 回路）。
- Failure reason: N/A。
- Reminder: executing 阶段需警惕"改 install_parser 扩展 flag"诱惑（= 方案 C，breaking），坚持方案 A 的 update handler 分叉。

## 5. Candidate Lessons

```markdown
### 2026-04-22 CLI 契约重定义务必审视对等入口
- Symptom: req-33 / chg-02 声明"CLI 同步职责已迁到 harness install"，但 install CLI 从未吸收 --check / --scan / --force-managed flag，drift 在 CLI 层彻底 severed。
- Cause: chg-02 聚焦"切 update CLI"+ chg-01 聚焦"helper 合并"，两侧均未审视"install CLI 是否吸收对等 flag"；契约层声明与 CLI 层实现脱节。
- Fix: 未来 CLI 职责迁移类变更（含本 bugfix 修复），plan.md 必做"原 handler 五个 flag × 新承诺入口是否一一对等"对照表，缺一条算不完工。
```

## 6. Next Steps

- 主 agent 汇报（四字段模板）。
- 建议 harness next → executing 按 bugfix.md §6 执行。
- executing 阶段第一件事：读本 session-memory.md §4 / §5 避免走到方案 C / B。

## 8. Testing 验证段（Subagent-L1 / testing / Sonnet 4.6 / 2026-04-22）

- 执行环境：uv venv + project source（HEAD = 1b0ee81）
- pytest 结果：287 passed / 3 failed（pre-existing req-29/req-30）/ 36 skipped；零新增失败
- AC 状态：AC-1~AC-8 全 PASS
- 合规扫描：R1 越界=0 PASS / revert 无冲突 PASS / 契约 7 PASS / req-29 映射未被改 PASS / req-30 透出 PASS
- 产出：`test-evidence.md` 已覆写（含 AC 表格 + 五项合规 + pytest 摘要）
- 建议：harness next → acceptance

## 7. Open Questions

- default-pick 决策清单（chg-05 / S-E 协议）：
  - **决策 1**：方案 A vs B vs C → 推荐默认 A。理由：E 原则，最小改动 + 零 breaking + 保留 chg-02 契约。
  - **决策 2**：scaffold_v2 mirror 是否需同步？→ 推荐默认 "需同步"。理由：req-34 / chg-04 硬门禁五明示，executing 必做。
  - **决策 3**：保不保留 `tools/harness_update.py`？→ 推荐默认 "保留"。理由：chg-02 `change.md` L37 明文不删，import 兼容 + test-only helper。
- 无需用户输入的开放问题：0（全部按默认推进）。
