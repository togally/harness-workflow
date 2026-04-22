# Session Memory

## 1. Current Goal

- 为 req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界））的 requirement_review 阶段产出 requirement.md + 需求摘要.md，落定 5 条 default-pick。

## 2. Context Chain

- Level 0: 主 agent（harness-manager / Opus 4.7）
- Level 1: Subagent-L1（requirement-review / Opus 4.7）—— 在 §7 完成后 stream idle timeout，核心产出齐全

## 3. Completed Tasks

- [x] 读 runtime.yaml / base-role.md / stage-role.md / requirement-review.md / harness-manager.md / index.md / stages.md
- [x] 只读抽样 src/harness_workflow/workflow_helpers.py 确认 WORKFLOW_SEQUENCE 结构
- [x] 写 requirement.md §1-§7（19430 bytes / 197 行）
- [x] 写 需求摘要.md（4015 bytes / ≤ 1 页）
- [ ] 写本 session-memory（原 subagent 超时，由主 agent 补）

## 4. Results

- `artifacts/main/requirements/req-31-.../requirement.md`
- `artifacts/main/requirements/req-31-.../需求摘要.md`
- 本文件

### 4.1 关键决策留痕（E 原则试点，5 条 default-pick）

- E-1 R1 豁免范围 = A 保守（仅 workflow_helpers.py 的 stage 机器）
- E-2 S-A 落地路径 = B 改 CLI 源码一次到位
- E-3 S-C acceptance 独立 subagent = A 保留
- E-4 S-E 例外条款 = A 只列数据丢失 / 不可回滚 / 法律合规三条
- E-5 chg-06 端到端自证 = A 列入（可选）

详见 requirement.md §7。

### 4.2 planning 阶段 default-pick 决策清单（req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界））/ chg-05（S-E 决策批量化协议）落地证据）

- chg-02 P-3（开放问题条数上限）= A（≤ 3 条）
- chg-02 P-4（汇报模板"无"字面要求）= A（写"无"）
- chg-03 P-5（testing R1 扫描深度）= A（git diff 范围）
- chg-03 P-6（acceptance-report.md 极简上限）= A（≤ 30 行）
- chg-04 P-7（废止对人文档处理方式）= A（保留行 + 标注"不要求"）
- chg-04 P-8（frontmatter 字段名）= A（delivery_link / requirement_link）
- chg-04 P-9（30% 缩减对哪三份 role.md）= A（requirement-review / planning / done）
- chg-05 P-10（硬门禁编号）= A（四）
- chg-05 P-11（例外条款措辞）= A（严格三类）
- chg-05 P-12（Session Start 新条文位置）= A（沿用）
- chg-06 P-13（度量基线选取）= A（req-29 + req-30 平均）
- chg-06 P-14（打断次数统计口径）= A（仅 stage 中途 Q&A）
- chg-06 P-15（commit 数口径）= A（每 chg 一 commit）
- planning 阶段本身新增争议 P-1（tests/ 断言如何修）= C（改测试断言）
- planning 阶段本身新增争议 P-2（chg-06 去留）= A（列入）

### 4.3 executing 阶段 default-pick 决策清单

- chg-02 测试修复：test_each_role_has_exit_condition_for_human_doc 与 scaffold_v2 mirror test 同时修复 = A（在 chg-02 commit 前修复，不拆分）
- chg-04 testing.md 的 TestingMinimalFieldTemplateTest 改写 = A（改为验证废止声明，而非旧字段顺序）
- 六份 role.md scaffold_v2 同步方式 = A（cp 命令批量同步，每个 chg 结束前执行）

### 4.4 testing 阶段 default-pick 决策清单

（由 testing subagent 在 stage 结束前补齐；当前预填：无）

### 4.5 acceptance 阶段 default-pick 决策清单

（由 acceptance subagent 在 stage 结束前补齐；当前预填：无）

### 4.6 done 阶段 default-pick 决策清单

（由主 agent 在 done 六层回顾时补齐；含度量表见 STEP 2 产出）

## 5. Next Steps

- 主 agent 一次性 batched-report 上述 5 条给用户（已完成，在会话文本中）
- 按 E 原则不等回复立即 harness next 推进到 planning
- 派发 planning 架构师 subagent（Opus）一次性写 6 份 change.md + plan.md + 变更简报.md

## [2026-04-22] E 原则修正 + 争议点重写（requirement_review 回炉）

- 用户纠正：E 原则 = "stage 边界 batched-report + **等用户点头**才推进；仅 `harness ff` 模式自动推进"；原表述"不等回复即推进"是误读
- 争议点格式改为"做什么 / 不同意改成什么"两列表格，用户一眼看懂
- 本次只修措辞，不改默认选（E-1..E-5 / P-1..P-15 用户已点头默认推荐）
- 下一步：主 agent 简洁 batched-report 问"是否同意" → 用户点头 → harness next 进 plan_review
