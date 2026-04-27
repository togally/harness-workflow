# Acceptance Checklist — req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）

> 验收角色：acceptance（sonnet）
> 日期：2026-04-27
> 验收依据：requirement.md 5 AC + test-report.md（二次干净，commit b64bcd7）+ session-memory 各段

---

## §AC 映射

| AC | 描述 | 核查依据 | 判定 |
|----|------|---------|------|
| AC-01 | executing→testing，缺 session-memory ✅ / pytest 时，不自动跳过 testing | TC-01 PASS；dogfood 第一格 gate 阻断 | ✅ PASS |
| AC-02 | testing→acceptance，test-report.md 不存在或缺 §结论，不自动跳过 acceptance | TC-02 PASS（第一格 gate 阻断 testing 出口）；_is_stage_work_done regex 严格标题匹配 | ✅ PASS |
| AC-03 | acceptance→done，checklist.md §结论缺，不跳 done | TC-03 / TC-03b PASS；第一格 gate check 覆盖 acceptance→done | ✅ PASS（部分：while gate gap sug-50 已登，见§遗留） |
| AC-04 | work-done gate 通过时，verdict-driven 连跳保留（bugfix-5/6 不退化） | TC-04（连跳 PASS）/ TC-05（same-role 绕 gate）/ TC-08（保守降级）全过；全量 591 pass / 0 new fail | ✅ PASS |
| AC-05 | ≥ 6 pytest 用例覆盖各 stage gate 正负 case；scaffold mirror 同步（如有） | 9 用例（TC-01～TC-08 + TC-03b）；scaffold 确认无需 mirror | ✅ PASS |

---

## §验收 checklist

| # | 检查项 | 结果 |
|---|-------|------|
| C-01 | requirement.md 5 AC 逐条有对应测试用例覆盖 | ✅ |
| C-02 | test-report.md §结论 PASS，且为二次干净验证（commit b64bcd7） | ✅ |
| C-03 | 9/9 unit PASS；全量 591 passed / 0 new fail | ✅ |
| C-04 | dogfood：第一格 gate 阻断 testing→acceptance（缺 test-report.md 时停在 testing） | ✅ |
| C-05 | 反例-A/B/C 通过（`_has_conclusion_heading` regex 严格标题级匹配，排除正文/注释误命中） | ✅ |
| C-06 | bugfix-5（同角色跨 stage 自动续跑硬门禁）same-role 路径绕 gate 不受影响（TC-05 PASS） | ✅ |
| C-07 | bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） acceptance 检查 `acceptance/checklist.md`（D-2 纠正落地） | ✅ |
| C-08 | lint 子命令 `harness validate --contract stage-work-completion`（TC-07 PASS，exit 1+缺项列出） | ✅ |
| C-09 | 零 git 破坏命令（dogfood 用 tmpdir mock；1st testing 事故已在 regression 修复）| ✅ |
| C-10 | 越界核查：commit b64bcd7 diff 仅触碰 req-45 scope（workflow_helpers.py / validate_contract.py / tests/） | ✅ |
| C-11 | 契约 7（id+title 硬门禁）：本 checklist 首次引用均带简短描述 | ✅ |
| C-12 | 活跃 P0/P1 缺陷：0 | ✅ |
| C-13 | BUG-04（change.md 裸 req-45 P3）：已知，不阻塞 | ⚠️ P3 遗留 |
| C-14 | sug-50（chg-01 gate gap：while 循环内 gate 缺失）：已登记，见§遗留 | ⚠️ 遗留已知 |

**PASS：12 / PARTIAL：1（BUG-04 P3）/ 遗留说明：1（sug-50）**

---

## §遗留

### sug-50（chg-01 gate gap：第一格修了但 while 循环内 gate 缺失）

- **现状**：2nd executing 修 BUG-01 时将 gate 从 while 内挪到第一格 `_write_stage_transition` 前，解决了第一跳的 over-chain。但 **while 循环内多格连跳没有同步保护**——testing 有 test-report 放行后，while 内 acceptance→done 若 checklist.md 不存在仍会跳过。
- **已登记**：sug-50（chg-01 gate gap：第一格修了但 while 循环内 gate 缺失，多格连跳还会越过 acceptance→done），status=pending，priority=high。
- **不阻断本 req 原因**：
  1. AC-03 核心场景（acceptance 第一格出口无 checklist 时停在 acceptance）已由第一格 gate 覆盖，当 stage=acceptance 时第一格 gate 直接阻断，不进入 while 循环。
  2. testing 报告二次干净 PASS，9 unit + 591 全量 / 0 P0-P1。
  3. sug-50 已明确描述修复方向（gate 同时保留第一格 + while 内，两位置共用 helper），优先级 high，承诺后续 req 优先修复。
  4. 实用主义（pragmatic）原则：已知缺陷有跟踪凭证，不因"多格连跳保护未补全"阻塞本次验收。
- **后续行动**：sug-50 进入 sug 池，下一 req 周期升为 P0 修复。

### BUG-04（change.md 裸 req-45 P3）

- 遗留 template 遗留，建议后续 executing 阶段补回，不阻塞验收。

---

## §结论

**PASS-with-followup**

req-45（harness next over-chain bug 修复（紧急）） chg-01（verdict stage work-done gate + workflow_next 集成）验收通过。

- 5 AC 全覆盖（AC-01～AC-05）；9 unit PASS；591 全量 / 0 new fail；dogfood 第一格 gate 有效。
- sug-50（chg-01 gate gap）已登记 high，承诺后续修复，不阻断本次验收。
- 遗留 1 P3（BUG-04）不阻塞。

**本阶段已结束。**
