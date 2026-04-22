# Session Memory — req-28 planning 阶段

## 1. Current Goal

- 作为 Subagent-L1（planning 角色），在 req-28 `changes_review` 阶段把 7 条合并建议（sug-09~15）拆分为 7 个 change，为每个 change 产出 change.md / plan.md / 变更简报.md，不实施生产代码。

## 2. Current Status

- 需求文档（requirement.md）与 `需求摘要.md` 已在上游 requirement_review 阶段定稿，7 个 AC（AC-09~AC-15）编号与建议一一对应。
- 本次 planning 产出：
  - 7 个 change 目录骨架（`harness change --requirement req-28 --id chg-NN` 逐个创建）。
  - 7 份 `change.md`（覆盖 Title / Goal / Scope / AC 映射 / Risks）。
  - 7 份 `plan.md`（覆盖 Development Steps / Verification / AC Mapping / Dependencies）。
  - 7 份 `变更简报.md`（对人文档契约 3 的 planning 阶段粒度=change，每个 change 一份）——AC-11 首次完整示范的关键动作。
- 所有产物路径严格遵循 `stage-role.md` 契约 2 `artifacts/main/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/`。

## 3. Validated Approaches

- 沿用主 agent 给出的建议拆分方案，未做结构性调整，仅在细节上做了落地补强（详见第 5 节"方案调整说明"）。
- 拓扑顺序：**chg-01 → chg-02 → chg-03 → (chg-04 / chg-05 / chg-06 并行安全) → chg-07 收尾**。
- `harness change` CLI 命名行为观察：传入纯中文 + 英文 title 时 slug 全小写化（`CLI` → `cli`），**未发现全角括号问题**——因为本次传入 title 中原本就没有全角括号。req-28 根目录已有 `（7条）` 全角括号属于 `create_requirement` 的历史遗留。

## 4. Failed Paths

- Attempt: 初次 Write chg-02 的 change.md / plan.md 未先 Read，工具报错 `File has not been read yet`。
- Failure reason: `harness change` 生成的模板文件已存在，Edit/Write 需先 Read。
- Reminder: 对 CLI 预生成的模板文件改写时，必须先 Read 再 Write。

## 5. Candidate Lessons

```markdown
### 2026-04-19 planning 阶段"建议拆分 → change 产物"SOP 补强
- Symptom: 建议方案已给出，但 planning subagent 需要把每条建议翻译成 change.md / plan.md / 变更简报.md 三份文档。
- Cause: 对人文档契约 3 要求"每个 change 一份变更简报.md"，与 change.md / plan.md 并列，不可省略。
- Fix: 按"creat 目录骨架 → 填 change.md → 填 plan.md → 填 变更简报.md"固定顺序执行；7 个 change 完成 3 个后存盘报进度，避免超时丢工作。
```

## 6. 拆分结果与方案调整说明

### 6.1 最终 7 个 change

| ID | 中文标题 | 覆盖 AC | 优先级 |
|----|---------|---------|--------|
| chg-01 | 修复 harness suggest CLI: filename fallback + 编号单调递增 + done sug frontmatter 硬门禁 | AC-15 | 档 1 硬阻塞 |
| chg-02 | 修复 harness bugfix / next 闭环: runtime.yaml 持久化 operation_type / operation_target | AC-12 | 档 1 硬阻塞 |
| chg-03 | harness archive 支持 bugfix 目录 + 一次性 sweep bugfix-3/4/5/6 | AC-14 | 档 1 硬阻塞 |
| chg-04 | 恢复 cycle-detection API 符号与完整测试 | AC-13 | 档 1 硬阻塞 |
| chg-05 | 对人文档落盘校验机制 (harness validate --human-docs) | AC-09 | 档 2 必做 |
| chg-06 | README 增补下游模板刷新提示 | AC-10 | 档 2 必做 |
| chg-07 | 对人文档端到端 smoke + req-28 自身首次完整示范 | AC-11 + AC-07 | 档 2 必做 |

### 6.2 相对主 agent 建议的调整

- **完全采纳**：chg-01 ~ chg-07 的拆分边界、依赖拓扑、覆盖 AC 全部按主 agent 建议执行，未合并、未拆细。
- **细节补强 1（chg-01）**：在 `create_suggestion` 门禁基础上显式加"frontmatter 必填字段清单"（id / title / stage / created_at），避免"必带 frontmatter 但字段残缺"的漏洞。
- **细节补强 2（chg-03）**：sweep 脚本默认 `--dry-run`，加 `--force-done` 处理 bugfix-3/4/5 的非 done 状态，降低误归档活跃工作的风险。
- **细节补强 3（chg-04）**：需求里提到 6 个 / 7 个符号差异，按任务要求"以 diagnosis.md 为准"；planning 阶段按 7 个起草，executing 阶段再最终对齐。
- **细节补强 4（chg-05）**：V1 校验只覆盖 req / bugfix 主 6 份路径，regression 层文档的校验留 TODO；acceptance 角色 SOP 同步引用 CLI，补 scaffold_v2 同步。
- **细节补强 5（chg-07）**：smoke 标 `@pytest.mark.slow` 并提供 `--fast` 路径，避免阻塞 CI。
- **不采纳的备选方案**：任务里提到 chg-02 可把"create_requirement 不去全角括号"小遗留并入范围。经权衡后**保持现状**——该遗留属于 slug 处理且不影响 req-28 交付闭环（chg-03 的 sweep 已能正确按目录名匹配），拆入 chg-02 会拉长 scope。记录为后续可新 sug 的候选。

### 6.3 `harness change` CLI 观察

- 对**英文字符 + 中文**混合 title：slug 产出格式为 `{id}-{全小写化合并破折号}`，如 `chg-01-修复-harness-suggest-cli-filename-fallback-与编号单调递增`，可读性尚可。
- **未观察到全角括号问题**——因为本次传入 title 本身无全角字符。
- req-28 父目录名 `req-28-批量建议合集（7条）` 带全角括号，属 `create_requirement` 的遗留；不在本次 planning 的修复范围。
- `harness change` 每次会生成：change.md / plan.md / regression/required-inputs.md / session-memory.md 4 份骨架；`变更简报.md` 不由 CLI 生成，必须 planning 角色手动追加（符合契约 4 的"对人文档不由 agent 过程模板生成"）。

### 6.4 对人文档 AC-11 验证点

- 7 个 change 子目录下 `变更简报.md` 全部产出，以下命令可复核：
  ```
  find artifacts/main/requirements/req-28-批量建议合集（7条）/changes/ -maxdepth 2 -name "变更简报.md" | wc -l
  # 期望: 7
  ```
- req-28 根目录 `需求摘要.md` 已由 requirement_review 阶段产出；后续 executing / testing / acceptance / done 各 stage 将依次补齐其余 5 份。

## 7. Next Steps

- 主 agent 检查并最终确认 7 个 change 的拆分是否合适；若接受则用 `harness next` 推进到 executing。
- executing 阶段按 chg-01 → chg-02 → chg-03 → (chg-04/05/06 并行) → chg-07 的拓扑执行，每个 change 完成后在对应目录下产 `实施说明.md`。
- chg-05 合入后可跑 `harness validate --human-docs --requirement req-28` 做对人文档落盘自检。

## 8. Open Questions

- **问题 1（主 agent 澄清用）**：chg-04 符号清单是 6 个还是 7 个？当前以任务指令里列出的 7 个（`CallChainNode` / `CycleDetector` / `CycleDetectionResult` / `detect_subagent_cycle` / `report_cycle_detection` / `get_cycle_detector` / `reset_cycle_detector`）为准；需求文档 requirement.md 第 19 行也是 7 个但第 46 行描述写"6 个"。chg-04 已在 change.md 中注明"以 diagnosis.md 为权威"，不阻塞 planning 阶段推进，但希望主 agent 在 executing 前确认。
- **问题 2**：chg-06 是否要同步动 `harness update --help` 的 description 字段？当前 chg-06 plan 把它设为可选 Step（argparse 不支持多行就跳过）；是否需要硬性做？如硬性需要，chg-06 的风险需重新评估。
- **问题 3**：chg-03 sweep 时 bugfix-3/4/5 的 yaml 当前 stage 具体是什么？planning 阶段未展开 state yaml；如主 agent 判断数据敏感，executing 前先 `cat .workflow/state/bugfixes/*.yaml` 确认后再决定是否走 `--force-done`。

## 9. 退出条件自检

- [x] 所有 7 个变更都有 `change.md`（目标、范围、AC 映射、Risks 齐备）
- [x] 所有 7 个变更都有 `plan.md`（步骤、验证、AC 映射、依赖齐备）
- [x] 执行顺序已明确（chg-01 → chg-02 → chg-03 → chg-04/05/06 并行 → chg-07）
- [x] 每个 change 目录下都产出 `变更简报.md`（对人文档契约）
- [x] 未触碰 `.workflow/flow/` 下现存过程文档（双轨不迁移）
- [x] 未实施任何生产代码（hard constraint 遵守）
- [x] 未调用 `harness next`（hard constraint 遵守）
- [x] 经验沉淀已检查（本次可沉淀的"planning 阶段对人文档 SOP 补强"记入第 5 节 Candidate Lessons）
- [ ] 用户已确认所有计划（待主 agent 反馈）

## 测试执行记录（Subagent-L1 / testing 阶段，2026-04-19）

### 基线
- 命令：`python3 -m unittest discover tests`
- 结果：**Ran 137 / OK / skipped=36 / fail=0 / error=0**（基线 134 + 本轮新增 3 条独立补测）。

### AC-09~15 覆盖独立评价
| AC | 覆盖文件 | 评价 |
|----|---------|------|
| AC-09 | `tests/test_validate_human_docs.py`（8）+ `test_smoke_req28.ValidateHumanDocsSmokeTest` | 合格 |
| AC-10 | `test_smoke_req28.ReadmeRefreshHintTest` | 合格（静态 grep 即可） |
| AC-11 | `test_smoke_req28.FullLifecycleSmokeTest` + artifacts 目录现场证据 | 勉强（req-28 自身示范仍差 1 份"交付总结.md"，由 done 补齐） |
| AC-12 | `tests/test_bugfix_runtime.py`（4）+ 独立补测 5 次 round-trip | 合格 |
| AC-13 | `tests/test_cycle_detection.py`（24） | 合格 |
| AC-14 | `tests/test_archive_bugfix.py`（4）+ 独立补测 force-done on done | 合格（代码层）；**P1 偏差**见下 |
| AC-15 | `tests/test_suggest_cli.py`（3）+ 独立补测 5 档混合 | 合格 |

### 独立补测
- 新增 `tests/test_req28_independent.py`（3 条）：
  1. `LazyBackfillPersistsAcrossManyRoundTripsTest` — AC-12 5 次 round-trip。
  2. `ForceDoneIdempotentOnDoneBugfixTest` — AC-14 --force-done 对已 done bugfix 的幂等性。
  3. `SuggestNumberingMonotonicAcrossMixedHistoryTest` — AC-15 混合 5 档历史仍取全集 max+1。

### 关键现场核查
- `.workflow/state/runtime.yaml#active_requirements` 仅剩 `req-28`，bugfix-3/4/5/6 已从 active 清理 — AC-14 runtime 侧满足。
- 实际归档路径：`.workflow/flow/archive/main/bugfixes/bugfix-{3,4,5,6}-*` — **与 AC-14 文本"归档产物落在 `artifacts/main/archive/bugfixes/` 下"不一致**。根因：`resolve_archive_root`（workflow_helpers.py:4280）在 legacy 路径非空时降级返回 legacy；chg-03 的 tempdir 单测用空 legacy 无法暴露。**判定：P1 偏差，建议开新 sug 承接（迁移子命令或修改 `resolve_archive_root` 判据），不阻塞 req-28 验收**。
- `harness status` 输出当前 stage=testing，req-28 state yaml requirement_stage=testing — AC-12 扩展的"stage 随推进同步 yaml"已生效。

### 结论
- 交付风险等级：**可上线**。7 条 AC 代码层全部满足，独立补测闭环。唯一需决策的是 AC-14 archive 路径偏差在 acceptance 阶段的处理方式。

## 验收执行记录

### harness validate --human-docs 输出
- 初次运行（验收开始时）：16/18 present，缺 验收摘要.md（本阶段产出）+ 交付总结.md（done 阶段产出）。
- 验收摘要.md 产出后：17/18 present，仅差 done 阶段 交付总结.md。
- 预期 done 完成后：18/18 present。

### AC 核对判定
- AC-09 通过：`harness validate --human-docs` CLI 存在且可运行，缺失文件明确可见。
- AC-10 通过：README.md:64 + README.zh.md:77 含 `pip install -U harness-workflow`。
- AC-11 有条件通过：17/18，仅差 done 阶段 交付总结.md。
- AC-12 通过：bugfix round-trip 持久化 + bugfix yaml stage 同步，测试全绿。
- AC-13 通过：7 符号全部导出，24 条完整用例全绿。
- AC-14 有条件通过：功能目标达成（CLI 支持 bugfix + active 清理），物理归档落 legacy 而非 AC-14 文本要求的 `artifacts/main/archive/bugfixes/`（testing 指出的 P1 偏差）。
- AC-15 通过：filename fallback + 编号单调（sug-08 由 CLI 自动分配验证修复）。

### Excluded 反例核查
- commit aa0a8b8 未触碰 `.workflow/flow/archive/` 历史归档、未触碰 req-26 / bugfix-6 已归档产物。结论 OK。

### 新增 suggest 条目
- sug-08-archive-path-legacy-fallback.md（承接 AC-14 路径偏差，建议改 `resolve_archive_root` 判据 + 可选 `harness migrate --archive` 迁移子命令）。
- 编号 08 由 `harness suggest` CLI 自动跨 archive+current 分配，验证 chg-01 单调递增 bug 已修。

### 整体判定
**有条件通过**。建议动作：起 sug-08 承接 AC-14 路径偏差后进入 done；AC-11 交付总结.md 由 done 阶段同步产出即闭环。

### 产出
- `artifacts/main/requirements/req-28-批量建议合集（7条）/验收摘要.md`（req 级，对人文档）。
- `.workflow/flow/suggestions/sug-08-archive-path-legacy-fallback.md`（新增 suggest 条目）。

## Done 阶段记录

### 六层回顾核心结论

- **L1 Context（需求层）**：7 条 sug 被正确拆解为 7 个 change；AC-09~AC-15 覆盖完整；对人文档契约、sug frontmatter 硬门禁均正确继承到 base-role.md / stage-role.md / done.md。
- **L2 Tools（变更层）**：7 个 change 拆分合理；依赖拓扑 chg-01 → chg-02 → chg-03 → (chg-04/05/06 并行) → chg-07 走通；`harness validate --human-docs` 新 CLI 顺畅；`resolve_archive_root` legacy 降级是 CLI 适配性遗留（sug-08 承接）。
- **L3 Flow（实施层）**：代码质量尚可，**"load 懒回填 + save 白名单"双保策略**漂亮（已沉淀 executing 经验六）；archive 路径偏差遗留属 chg-03 单测盲区。
- **L4 State（测试层）**：134 → 137 条测试全过；AC-11 对人文档产出从 0 → 16 → 17 → 18/18；独立补测 3 条闭环；state/requirement yaml 同步刷新。
- **L5 Evaluation（验收层）**：7 AC 中 5 条完全通过（AC-09/10/12/13/15）+ 2 条有条件通过（AC-11 缺 交付总结、AC-14 path 偏差）；本 done 阶段产出 交付总结.md 后 AC-11 闭环。
- **L6 Constraints（流程层）**：sug-12 修复后 bugfix 闭环正式打通（sweep 了 bugfix-3/4/5/6 4 个历史受害者）；sug-15 修复后 `harness suggest --apply / --delete` 对老 sug 能用；sug-08 的新建本身现场验证了编号单调递增修复。

### 产出清单

- **对人文档**：`artifacts/main/requirements/req-28-批量建议合集（7条）/交付总结.md`（req 级，对人文档，AC-11 最后一片拼图）。
- **done-report**：`.workflow/state/sessions/req-28/done-report.md`（六层回顾报告详版）。
- **经验沉淀**：
  - `.workflow/context/experience/roles/executing.md` 新增经验六（runtime.yaml 新增字段双保策略）。
  - `.workflow/context/experience/tool/harness.md` 新增 `create_suggestion` 跨 archive+current 单调递增经验。

### validate --human-docs 最终结果

- **18/18 present. All human docs landed.**（通过 `harness validate --human-docs --requirement req-28` 核验）

### archive 建议

- **建议先修 sug-08 再归档 req-28**：若先归档，req-28 的归档产物也会落 legacy `.workflow/flow/archive/main/bugfixes|requirements/`，与 primary 路径分歧扩大；先开 bugfix-7 消费 sug-08 修 `resolve_archive_root` 判据后再 `harness archive req-28`，产物才能直接落 `artifacts/main/archive/requirements/` primary 路径。
- 若主 agent 决定不等，立即 archive 亦可接受，代价是未来需在 bugfix-7 中一并迁移 legacy 下的 req-28 归档物。

### 待处理遗留

- sug-01-ff-auto（ff --auto 模式）仍 pending，与 req-28 无依赖，下一轮 apply。
- sug-08-archive-path-legacy-fallback（本周期新增，建议新开 bugfix-7 消费）。
- `create_suggestion` frontmatter 只写 id/created_at/status 三字段，title/priority 缺失（chg-01 已知限制，属 reviewer 软拦截范畴，低优先可新开 sug）。
