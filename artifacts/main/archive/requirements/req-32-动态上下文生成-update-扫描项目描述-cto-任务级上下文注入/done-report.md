# Done Report: req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）

## 基本信息

- **需求 ID**：req-32
- **需求标题**：动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入
- **归档日期**：2026-04-22

## 实现时长（数据源：`state/requirements/req-32-...yaml::stage_timestamps`）

- **总时长**：约 12h（2026-04-21 对话起至 2026-04-22 02:43 done，含夜间离线）
- **requirement_review → plan_review**：跨日对话为主，无法精确切分（state yaml 未记录 requirement_review / changes_review 时间戳，沿用 req-31（批量建议合集（20条））sug-16（stage_timestamps 白名单 + 总是初始化）白名单之前的语义）
- **plan_review → ready_for_execution**：2m 17s
- **ready_for_execution → executing**：38s
- **executing**：1h 37m 27s（00:23:35 → 02:01:02，含 chg-01（项目描述扫描器 + project-profile 落地）、chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）、chg-03（CTO 派发 briefing 注入 task_context_index + 快照落盘） 及 chg-03 扩展 4 轮 TDD）
- **testing**：37m 38s（02:01:02 → 02:38:40，含收口修复 P1-01/P2-01）
- **acceptance**：4m 55s（02:38:40 → 02:43:35）
- **done**：进行中

## 1. 执行摘要

req-32 把 harness workflow 从"静态 scaffold 同步"升级为"按任务内容动态生成上下文索引 + 项目画像"。核心交付：

- **chg-01（项目描述扫描器 + project-profile 落地）**：新 `src/harness_workflow/project_scanner.py`（509 行），覆盖 pyproject / package.json / pom / go.mod / Cargo / README / CLAUDE.md / AGENTS.md 8 类描述文件静态解析，生成 `.workflow/context/project-profile.md`（结构化字段 + LLM 占位 section + sha256 content_hash + ISO 时间戳）
- **chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）**：扩 `workflow_helpers.py::update_repo` 接入 scanner（+82 行），实现首次生成 / 无漂移 / 有漂移三态 stderr 反馈；复用 req-31（批量建议合集（20条））sug-14（用户自定义 CLAUDE/AGENTS/SKILL 保护）`_is_user_authored` 保护 CLAUDE.md / AGENTS.md / SKILL.md
- **chg-03（CTO 派发 briefing 注入 task_context_index + 快照落盘）**：`_build_subagent_briefing` 扩展 3 kwarg（root / regression_id / regression_title），新增 `_build_task_context_index` 索引构建器（硬上限 8 + 截断 warn）+ `_write_task_context_snapshot` 快照写盘（frontmatter + 正文）；派发路径覆盖 `harness next --execute` + `harness ff --auto` + `harness regression`
- **testing 收口（P1-01 / P2-01）**：chg-01 session-memory bare id 修正 + workflow_helpers 新增 `skipping user-modified file` stderr 对齐 AC-05 spec

测试基线：253 → 288（+35 新 TDD，零回归），contract-7 req-32 范围 0 违规，acceptance PASS。

## 2. 六层检查结果

### 第一层：Context（上下文层）

- [x] **角色行为**：requirement-review / planning / executing / testing / acceptance / done 角色均按 SOP 执行，未越界
- [x] **经验文件更新**：本轮未新增 `.workflow/context/experience/*` 专属教训条目（多数为既有机制的正常使用），但以下教训值得沉淀（已在下方 `改进建议` 提取为 sug）：
  - `git stash pop + git checkout HEAD --` 可能污染 runtime.yaml（chg-02 subagent 已经亲历）
  - subagent 派发前主 agent 裁剪的 "澄清结论" 可降低 TDD 返工
- [x] **上下文完整性**：本仓首次落盘 `.workflow/context/project-profile.md`（chg-01/02 产物 + 主 agent 填 LLM 占位），后续 req 的 CTO 派发可直接复用

### 第二层：Tools（工具层）

- [x] **工具使用顺畅度**：`harness requirement` / `harness next` / `harness next --execute` / `harness status` / `harness validate --contract 7` / `pytest -q` / `git log`、`git status`、`git push` 均顺畅
- [x] **CLI 适配发现**：
  - **痛点**：contract-7 全仓扫描产出 319 条历史违规混入信号（req-32 范围噪声），必须手工 grep 过滤 req-32 范围目录 → sug 建议加 `--scope <req-id>` flag 做范围限定
  - **发现**：`harness next --execute` 和 `harness next` 语义容易混淆（前者推进 + 打 briefing，后者仅推进），sug 建议明确分两个命令或完全合并
- [x] **MCP 适配发现**：无新发现；本项目未使用 MCP 工具

### 第三层：Flow（流程层）

- [x] **阶段流程完整性**：requirement_review → changes_review → plan_review → ready_for_execution → executing → testing → acceptance → done 八个阶段全部执行，未跳过
- [x] **阶段跳过检查**：无跳过。executing 内部严格按 chg-01 → chg-02 → chg-03 → chg-03 扩展串行，每 chg TDD 红绿独立 commit
- [x] **流程顺畅度**：中途 1 次阻塞 —— runtime.yaml 被 chg-02 subagent 的 `git checkout HEAD --` 污染回 req-31 done 状态；主 agent 手工修复 runtime.yaml（按 CLAUDE.md 硬门禁"修复 runtime 而非开平行工作流"条款）。**非阶段问题**，但值得经验沉淀

### 第四层：State（状态层）

- [x] **runtime.yaml 一致性**：当前 `.workflow/state/runtime.yaml` 与 `.workflow/state/requirements/req-32-....yaml` 一致（stage=done，current_requirement=req-32）
- [x] **需求状态**：req-32 status=done，completed_at=2026-04-22
- [x] **状态记录完整性**：stage_timestamps 含 plan_review / ready_for_execution / executing / testing / acceptance / done 6 条；requirement_review 和 changes_review 未记录（req-31 sug-16 白名单未涵盖前置 review 阶段，可作为后续 sug）
- [x] **task-context 快照**：`.workflow/state/sessions/req-32/task-context/` 生成 2 份（testing-001.md + acceptance-001.md） —— 只有 `harness next --execute` 触发产出，plan_review / changes_review 因用普通 `harness next` 未落快照（符合 chg-03 设计）

### 第五层：Evaluation（评估层）

- [x] **testing 独立性**：testing subagent 独立派发，不共享 executing 的 context；产出 `test-report.md`（138 行）+ `测试结论.md`，发现 P1-01 + P2-01/02/03 共 4 条 issue，P1-01 阻塞项已回流修复
- [x] **acceptance 独立性**：acceptance subagent 独立派发，对照 requirement.md 逐条核查 7 条 AC + Scope 不包含项 + 3 条 Risks；产出 `acceptance-report.md`（94 行）+ `验收摘要.md`（21 行），结论 PASS
- [x] **评估标准达成**：AC-01 ~ AC-07 全部 PASS，Scope 不包含零越界，Risks 防御 R1/R2/R3 全落实

### 第六层：Constraints（约束层）

- [x] **边界约束**：无越界。所有节点任务均派发 subagent（未主 agent 直接写代码）
- [x] **契约 7 硬门禁**：本轮修 P1-01 后 contract-7 req-32 范围 0 违规
- [x] **契约 6 对人文档**：`需求摘要.md` / `变更简报.md`×3 / `测试结论.md` / `验收摘要.md` / `交付总结.md`（即将产）链条完整，每份 ≤ 1 页
- [x] **TDD 红绿纪律**：除 chg-02 与 testing 收口外每步红绿独立 commit，chg-02 / 收口将多步合并（subagent 自述偏离，AC 覆盖完整可接受）
- [x] **新风险**：无需更新 `risk.md`，`git stash pop` 污染 runtime 属操作教训（转 sug 沉淀，非系统性风险）

## 3. 工具层适配性问题记录

| 痛点 | 建议 | 预期收益 |
|---|---|---|
| `harness validate --contract 7` 噪声大 | 加 `--scope <req-id>` / `--since <git-ref>` flag | 过滤历史违规，只报本轮 |
| `harness next` vs `harness next --execute` 语义易混 | 文档或 CLI help 明示差异 | 减少误调产生空 briefing |
| 本仓 ADBI 整体 contract-7 violations 基线 319 | legacy sweep 独立 bugfix | 长期去噪 |

## 4. 经验沉淀情况

本轮未新增 `experience/` 条目（既有机制运转良好）。**值得沉淀**为经验的两条通用教训已转 sug：

1. subagent 使用 `git stash pop + git checkout HEAD --` 会误伤 runtime.yaml / managed files —— 建议在 executing 角色 SOP 中加入 `禁止 git stash / git checkout HEAD --` 条款
2. 主 agent 在 subagent 派发前把用户澄清结论（决策表 + 偏离豁免）明确写进 briefing，显著降低 TDD 返工率（本轮 4 轮 subagent 派发零返工）

## 5. 流程完整性评估

- 阶段执行：全部 8 阶段实际走完，无跳过 / 短路 / 重复
- 异常：1 次 runtime.yaml 污染（已即时修复）
- 对人文档：需求摘要 / 3 份变更简报 / 测试结论 / 验收摘要 俱全，交付总结.md 本 stage 待产
- commit 规模：12 commits，+2,500 lines code / +35 tests，零回归

## 6. 改进建议（将转为 sug）

- **sug-A（high）**：`experience/roles/executing.md` 补一条硬条款 —— "禁止 `git stash pop` / `git checkout HEAD --` 组合操作（会污染 runtime.yaml 与 managed 文件）"
- **sug-B（medium）**：`harness validate --contract 7` 新增 `--scope <req-id>` / `--since <git-ref>` flag，过滤历史噪声
- **sug-C（medium）**：AC-05 的 stderr 文案 spec 在 requirement / change.md 中回写，承认"authored"与"modified"两种场景双文案并存
- **sug-D（medium）**：`tests/` 加 `conftest.py` 注入 sys.path，让单测可独立文件执行（而非必须 `pytest -q`）
- **sug-E（low）**：`harness update --scan-profile-only` flag —— 只刷 project-profile.md，不刷其他 managed 文件
- **sug-F（low）**：project-profile.md 的 gitignore / commit 策略决策（当前 `.workflow/` gitignored）
- **sug-G（low）**：多语言混合仓的 stack_tags 权重单测（pyproject + package.json 双语并存时优先级）
- **sug-H（high）**：requirement_review / changes_review 加入 state yaml 的 stage_timestamps 白名单（req-31 sug-16 遗漏），保证前置评审阶段耗时可统计
- **sug-I（medium）**：`harness next` 与 `harness next --execute` 的 CLI help / 文档明示差异（后者打 briefing + 落 snapshot）
- **sug-J（low）**：CTO 派发时为 regression 场景加入 regression-specific index 默认集（`experience/roles/regression.md` 等）

## 7. 下一步行动

- **行动 1（主 agent）**：将上述 10 条 sug-A ~ sug-J 落盘 `.workflow/flow/suggestions/` 带 frontmatter
- **行动 2（主 agent）**：产出 `交付总结.md` 对人文档
- **行动 3（主 agent）**：更新 `session-memory.md` 加 `## done 阶段回顾报告` 区块
- **行动 4（主 agent / 用户）**：确认推进 `harness archive req-32` 归档
- **行动 5（未来 req）**：针对 sug-H / sug-B / sug-A 组合开 req（流程 / CLI / 经验沉淀三路）
