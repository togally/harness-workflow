# Session Memory — chg-04（_pad_list + _pad_interactive + dogfood + slash command 同步）

## 1. Current Goal

为 chg-04 落 plan.md，把 chg-01 stub 替换为真实 `_pad_list` / `_pad_interactive`，加 12 + 条端到端 dogfood TC，落 `.claude/commands/harness-pad.md` slash command + README 增补段。

## 2. Context Chain

- Level 0: 主 agent
- Level 1: analyst / opus

## 3. 关键决策（chg-04 范围内）

- **`_pad_list` 严格按 PAD_KINDS 顺序循环 5 个 rule scope + 5 个 experience scope**：保证 list 输出对 user 可读 + 已知顺序；空 scope 段显示 `(无)`，让 user 看到完整可选面板。
- **tool 段单独走 `_parse_tool_list_section`** 而非 `_parse_index_md`：tools/index.md schema 是 markdown 列表段，不是表格，需新解析器；段内项排序按字母序。
- **questionary 三步序列**：kind → scope（仅 rule/experience）→ title；scope 为空 list（tool kind）时跳过；与位置参数一致。
- **非 TTY 守卫**：`sys.stdin.isatty() == False` → exit 2 + stderr 提示；与 `prompt_platform_selection` 一致（line 59）。
- **dogfood 走 subprocess**：禁止直接调 `_pad_add` / `_pad_list` 等内部函数（违反端到端 dogfood 原则）；所有 TC 走 `subprocess.run([sys.executable, "-m", "harness_workflow.cli", ...])`，与 `tests/test_workflow_next_subprocess.py` 同款风格（sug-52 dogfood 模板）。
- **slash command 同款分发风险**：实施时需 grep `install_local_skills` 确认 `.claude/commands/` 是否走目录全量拷贝；如是则 0 改动，如显式 list 则加 1 行。session-memory 记录此判断点供 executing 阶段确认。
- **README 增补 ≤ 30 行**：保持 README 简洁，不夺主流程命令的注意力。
- **WORKFLOW.md 不动**：OQ-Verdicts 已定，pad 是辅助命令，不进 Main Entry。

## 4. 未做（chg-04 边界）

- 不实装 PetMallPlatform 真实仓自验（AC-10 由 user 在 acceptance 阶段手工跑）
- 不动 install_local_skills 主流程（如显式 list 缺失则 executing 阶段加 1 行）
- 不引入 telemetry / feedback.jsonl 事件（TC-Dogfood-05 降级为存在性检查，避免范围溢出）
- 不实装 v2 子命令（remove / show / move）

## 5. 待沉淀经验（chg 完成后回填）

- "**端到端 dogfood 必走 subprocess**"（sug-52 模板已立稳）—— 直接调内部函数会绕开 argparse / dispatch / cwd 解析等真实路径，testing 容易过 acceptance 翻车（req-50 教训）。
- "**list 命令的可读性 vs 紧凑性**" —— 显示空 scope 段（`(无)`）vs 隐藏空段，本 chg 选显示，让 user 看到完整可选 scope 面（教学价值高于紧凑价值）。
- "**questionary monkeypatch 的标准模板**" —— `lambda **kw: SimpleNamespace(ask=lambda: <return_value>)`，可复用到其他 interactive 命令测试。

## 6. Phase 2 + 3 全 chg 收束总结（写入 analysis/session-memory.md 后清掉本节）

- 4 chg 拆分依赖链：chg-01 → chg-02 → chg-03 → chg-04（线性）
- 每 chg 单独可交付（pytest 闭环 + dogfood 闭环）
- chg 间通过 stub-then-replace 策略避免循环依赖
- 范围红线在 4 chg 各 change.md / plan.md / session-memory.md 中重复声明（与硬门禁九"独立核查"配合）

## Executing Stage 完成记录

- _pad_list 真实实现 + _parse_tool_list_section helper 落地
- _pad_interactive 真实 questionary 引导落地（非 TTY 守卫）
- .claude/commands/harness-pad.md slash command 创建
- README.md + README.zh.md 均追加 `## harness pad` 段
- 测试：list 5 TC + interactive 4 TC + dogfood 5 TC = 14 TC 全 pass

✅ chg-04 完成
