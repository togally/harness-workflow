# Session Memory — req-33（install 吸收 update 的 CLI 职责 + harness update 契约层重定义为触发 project-reporter）

## 1. Current Goal

- 本 stage（requirement_review）目标：把用户在 reg-02（req-32 跑偏诊断 / pending-title）中追加的指示（"先融合 install+update 到 install，再把 harness update 改成召唤 project-reporter；只改角色/契约文档，不动 Python 业务逻辑"）翻译为可执行的 requirement.md、对人 `需求摘要.md` 与本 session-memory，三件套齐全即可交付 planning。

## 2. Context Chain

- Level 0：主 agent（technical-director / opus）→ stage = requirement_review
- Level 1：Subagent-L1（requirement-review / opus 4.7，即本 agent）→ 任务 = 写 requirement.md + 需求摘要.md + session-memory.md

## 3. Completed Tasks

- [x] 读取硬门禁三件套：`WORKFLOW.md` / `.workflow/context/index.md` / `.workflow/state/runtime.yaml`（确认 stage = requirement_review、current_requirement = req-33、conversation_mode = open）
- [x] 读取角色三件套：`base-role.md` / `stage-role.md` / `requirement-review.md`
- [x] 读取契约关键文档：`.workflow/context/roles/harness-manager.md`（§A.1 / §A.3 / §3.5.1）、`.workflow/context/roles/project-reporter.md`
- [x] 抽样只读 `src/harness_workflow/workflow_helpers.py`：
  - L3095 `def install_repo(root, force_skill=False)`
  - L3281 `def update_repo(root, check=False, force_managed=False, force_all_platforms=False, agent_override=None)`
  - L6234 `def install_agent(root, agent)`
  - L6409 `def scan_project(root)`
- [x] 抽样 `CLAUDE.md` L23-24 / `AGENTS.md` L23-24 确认 `harness install` / `harness update` 并列为主入口
- [x] 抽样 `.claude/skills/harness/SKILL.md` L38-40 / L85 确认 `harness update` 三条 CLI 描述 + `install / update` 并列描述
- [x] 产出 `artifacts/main/requirements/req-33-.../requirement.md`（§1..§9，含 §4.1 / §4.2 / §4.3 / §5 AC / §6 Split / §7 E-1..E-6 default-pick）
- [x] 产出 `artifacts/main/requirements/req-33-.../需求摘要.md`（对人 ≤ 1 页，frontmatter `delivery_link` 已挂）
- [x] 产出本 `session-memory.md`

## 4. Results

- **产出路径**：
  - `artifacts/main/requirements/req-33-install-吸收-update-的-cli-职责-harness-update-契约层重定义为触发-project/requirement.md`
  - `artifacts/main/requirements/req-33-install-吸收-update-的-cli-职责-harness-update-契约层重定义为触发-project/需求摘要.md`
  - `.workflow/state/sessions/req-33/session-memory.md`（本文件）
- **范围裁定关键点**：
  - 严格两阶段：chg-01（CLI 融合，install_repo 吸收 update_repo）→ chg-02（角色契约层重定义 + handler 改打印引导 + exit 0）→ chg-03（可选端到端自证）。
  - R1 豁免**显式收口**到 §4.3：`src/harness_workflow/workflow_helpers.py::install_repo/update_repo` + `src/harness_workflow/cli.py` subcommand 映射 + `tests/test_install_*` / `tests/test_update_*` 断言同步；其余一律不越界。
  - chg-02 只改**契约文档**（harness-manager.md §A.3、CLAUDE.md、AGENTS.md、.claude/.codex/.qoder 的 SKILL.md）+ `harness update` CLI handler 一处；不重做 project-reporter、不改 10 节模板。
- **契约 7 合规**：requirement.md / 需求摘要.md 首次引用 req-32 / req-33 / reg-02 / chg-01..03 / req-31 均带 title；后续同上下文简写。
- **退出条件自检**：
  - [x] 背景（§2 Background）
  - [x] 目标（§3 Goal）
  - [x] 范围（§4，包含 + 不包含 + R1 豁免）
  - [x] 验收标准（§5 AC-A1..A4 / AC-B1..B4 / AC-F1..F3）
  - [x] 对人文档 `需求摘要.md` 字段齐全（目标 / 范围 / 验收要点 / 风险），frontmatter 含 `delivery_link`
  - [x] `harness validate --contract all`（本文本未调；由主 agent 在推进 planning 前自检）

## 5. default-pick 决策清单（stage-role.md "同阶段不打断 + default-pick 记录" 强制留痕）

本 stage 按 base-role.md 硬门禁四 + stage-role.md Session Start 同阶段不打断原则全部按默认推进，未反问用户。清单：

| # | 决策点 | default-pick | 理由（一句话） |
|---|---|---|---|
| E-1 | 合并后函数命名 | 保留 `install_repo`（不改名） | 改名 `sync_repo` 要连锁改所有 import 点，收益远小于成本 |
| E-2 | chg-01 阶段 `update` subcommand 行为 | 等价于 `install` | 为 chg-02 接管作平滑准备，不出现中间混合态 |
| E-3 | 幂等化检测实现策略 | 复用 `migrate_legacy_docs_to_workflow` 返回空判跳 + AGENTS.md/CLAUDE.md 内容一致判跳 | 既有函数已有语义，零新路径；比 `os.path.exists('.workflow')` 判别更细 |
| E-4 | 测试断言调整归属 | 在 chg-01 同 commit 内落 | 参照 req-31（角色功能优化整合与交互精简）/ P-1 惯例，避免碎片 commit |
| E-5 | chg-02 `harness update` CLI handler 新行为 | 打印引导文案 + `exit 0` | 不直接调 AI（CLI 不应直接触发 AI 召唤）；`exit 0` 保护存量脚本链 |
| E-6 | chg-03 端到端自证是否独立 | 列入为独立 chg-03 | 符合用户"严格顺序"意图；planning 有权合并到 chg-02 尾步 |

全部决策在 requirement.md §7 同步留痕；planning 阶段若有相反意见，可直接覆盖。

## 6. Next Steps

- **建议**：`harness next` 推进到 planning。
- **planning 关注点**（供下一 stage 参考）：
  - chg-01 的 Python 合并实现细节：`install_repo` 吸收 `update_repo` 的四组职责（skill 刷新 / managed 文件同步 / legacy artifacts 清理 + feedback.jsonl 迁移 / state 迁移 + experience index），需在 plan.md 中列出被吸收函数的调用链与参数透传策略。
  - chg-02 的"handler 改打印引导 + exit 0"需在 plan.md 中给出具体文案（含"请改用 `harness install`"提示 + 四触发词清单）。
  - chg-03 是否独立，由 planning 按 E-6 与实际工作量决定；若合并则 AC-F1 的 commit 数下调到 ≥ 2。
- **潜在风险点**（需在 planning 中进一步拆解）：
  - R-1（CLI 行为突变 / 存量脚本失效）→ chg-02 必须在 handler 文案中显式提示迁移路径，`exit 0` 硬约束落入 AC-B4。
  - R-2（幂等化漏洞）→ chg-01 的 testing 阶段必须做 dual-run（第二次运行无产物变动）验证。

## 7. 待处理捕获问题

- 无（本 stage 所有边界问题已在 requirement.md §4 / §7 中处理完毕）。

## 端到端自证 req-33（install 吸收 update 的 CLI 职责 + harness update 契约层重定义为触发 project-reporter）

> 执行于：chg-03（端到端自证：用户说 harness update → project-reporter 跑 → project-overview.md → session-memory）
> 硬前置：chg-01（commit a464649）+ chg-02（commit b9869b2）均已 merged。

### ① 触发词

`生成项目现状报告`（§3.5.1 四触发词第一条）

### ② 召唤链路

1. CLI 旁证（Step 1 抓取，rc=0 实测）：
   `harness update 已重定义为角色契约触发。 / 请在 Claude Code / Codex 会话中说 '生成项目现状报告' 召唤 project-reporter。 / CLI 同步职责已迁到 harness install。`
2. harness-manager 识别触发词 → §3.5.1 → role-model-map.yaml → briefing.model = opus
3. 派发 project-reporter（Opus 4.7）内联完成（E-4 默认：executing Sonnet 代跑）
4. 产出：`artifacts/main/project-overview.md` 覆写（10 节全齐，mtime 2026-04-23T00:51Z，15905 bytes）

### ③ AC-B3 命中

- 触发词 ✅ / 召唤链路 ✅ / 产物时间戳 2026-04-23T00:51Z ✅ / session-memory 留痕 ✅
