# Session Memory — chg-05（harness playbook-check 子命令）

## 1. Current Goal

新增 `harness playbook-check` 子命令 + `harness validate --contract playbook-layout`；扫描路径 = `artifacts/project/playbooks/`（OQ-1=B）；漂移检测 + 健康报告 + CI 接入；新增"AUTO 区段被改但未跑 refresh"漂移类作为 OQ-5=A 路书只读软约束的兜底闸门；纯静态分析，零 LLM。

## 2. Context Chain

- Level 0: 主 agent（harness-manager）→ analysis stage 编排
- Level 1: Subagent-L1（analyst / opus）→ req-55 analysis stage
- 后续 Level 1（executing / sonnet）：执行本 chg

## 3. Completed Tasks

- [x] 新建 `src/harness_workflow/tools/harness_playbook_check.py` 含 10 类 check 函数（含 AUTO 区段被改但未跑 refresh 的 OQ-5 兜底检测）
- [x] `src/harness_workflow/cli.py` 注册 `playbook-check` 子命令 + `validate --contract playbook-layout` 路由
- [x] `validate --contract playbook-layout` 直接调 `playbook_check(contract_only=True)` 契约子集（C-01/C-03/C-05）
- [x] 新增 `tests/test_playbook_check.py`（13 TC：TC-01～TC-13，含 TC-08 OQ-5 兜底 + TC-10 dogfood + TC-11 validate 集成）
- [x] 全部 13 TC PASS
- [x] harness-workflow 自身仓 baseline check（playbook 目录不存在 → exit 0，符合"无路书无漂移"语义）

## 4. Results

- `src/harness_workflow/tools/harness_playbook_check.py`（新增，10 类 check 函数 + `playbook_check()` 主入口）
- `src/harness_workflow/cli.py`（注册 `playbook-check` 子命令 + `validate --contract` choices 追加 `playbook-layout`）
- `tests/test_playbook_check.py`（新增，13 TC）
- pytest tests/test_playbook_check.py: 13 passed / 0 failed
- 全量回归 pytest tests/: 57 failed / 790 passed（基线 57 failed，本 chg 引入 +0 failed / +13 passed）
- harness validate --contract artifact-placement: exit 0
- harness validate --contract playbook-layout: exit 0（当前仓无路书 → warn + skip）

**关键设计决策**：
- code-map.md AUTO:DOMAIN_FILES 哈希检测被排除（原因：refresh step5 在 step6 之前，code-map 汇总内容依赖 domains/*/code.md 的区段状态，形成顺序依赖，直接对比哈希会产生误报；互引一致性由 D-04/C-05 承担）
- playbook-layout 契约走 `playbook_check(contract_only=True)` 而非注册 validate_contract.py（保持契约路由灵活性）

## 5. Open Questions / default-pick

- OQ-1 已用户拍定 = B（`artifacts/project/playbooks/`）→ 本 chg 扫描 / 漂移检测路径已对齐。
- OQ-5 已用户拍定 = A（仅写规则 + chg-05 漂移检测兜底，本 req 不引入 PreToolUse hook、不改文件系统权限）→ 本 chg 增加"AUTO 区段被改但未跑 refresh" fixture（TC-12），构成事后审计闭环。
- OQ-6（`harness validate --contract playbook-layout` 注册风格）= 沿用 `validate_contract.py` 既有契约注册模式（read-only：实施前由 executing 阶段读现有代码确认，不在 analysis 阶段写定）。
- 详见 req 主 session-memory.md `## 9`。

## 6. 经验沉淀候选

- **沉淀目标**：`.workflow/context/experience/risk/known-risks.md`
- **沉淀条目（待 done 阶段写入）**：
  1. **路书只读软约束 + CI 兜底（OQ-5=A）**：观察项；check 通过 AUTO 区段哈希对比（architecture.md STACK/SCRIPTS/LAYOUT + overview.md DOMAIN_LIST）捕获"agent 手改 AUTO 区段但未跑 refresh"的违规行为；agent 频繁违反则开 reg-NN 升级到 PreToolUse hook（settings.json）或文件系统权限锁。
  2. **refresh step5/step6 顺序依赖**：code-map.md 汇总 AUTO:DOMAIN_FILES 内容依赖 domains/*/code.md 的区段状态（step5 先于 step6），在 check 中重建期望值时须跳过 code-map.md，改由 D-04/C-05 承担互引一致性检测。此为 chg-05 执行中发现的架构细节，值得记录防止后续重犯。
- **沉淀触发条件**：req-55 真实落地 1 次后由 done 阶段（acceptance / done 角色）按真实运行数据回写；本 stage（executing）填写候选内容，done 阶段执行实际写入。
- **当前状态**：executing 阶段已记录候选（done 阶段回写）。

---

## 完成态

本 chg executing stage 完成 ✅
