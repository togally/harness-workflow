# Session Memory — req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））testing 阶段

## 1. Current Goal

独立验证 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））AC-01~16，端到端覆盖，非 executing 自证。

## 2. Context Chain

- Level 0: 主 agent / technical-director（opus）
- Level 1: testing subagent（sonnet）— 本文件作者

## 3. 模型自检

- **expected_model**：sonnet（role-model-map.yaml `testing: "sonnet"`）
- **实际运行模型**：claude-sonnet-4-6（Sonnet 4.6）
- **映射一致性**：PASS

## 4. Completed Tasks

- [x] 加载硬前置：runtime.yaml / base-role.md / stage-role.md / testing.md / evaluation/testing.md / role-model-map.yaml
- [x] 定位 req-41 requirement.md（路径：`.workflow/flow/requirements/req-41-机器型工件回-flow-requirements-关注点分离-废四类-brief-方向-c/requirement.md`）
- [x] 读取 AC-01~16 全文
- [x] AC-01（repository-layout 契约底座）验证 — PASS
- [x] AC-02（六角色去路径化）验证 — PASS
- [x] AC-03（CLI flow layout 常量 + helper）验证 — PASS（23 pytest cases passed）
- [x] AC-04（create_* 路径校验）验证 — PASS
- [x] AC-05（归档路径 + state 无 req-41）验证 — PASS
- [x] AC-06（全量 pytest 不破坏回归）验证 — PASS（441 passed，1 pre-existing 豁免）
- [x] AC-07（repository-layout 删四类 brief + 角色文件同）验证 — PASS
- [x] AC-08（validate_human_docs 重写 + exit 0）验证 — PASS
- [x] AC-09（pytest brief deprecated test）验证 — PASS
- [x] AC-10（harness-manager Step 4 硬门禁）验证 — PASS（3 grep 命中）
- [x] AC-11（done.md 交付总结扩 §效率与成本）验证 — PASS
- [x] AC-12（usage-reporter 废止）验证 — PASS（文件不存在；role-model-map / index / harness-manager 均 0）
- [x] AC-13a（dogfood 机器型工件在 flow/）验证 — PASS
- [x] AC-13b（artifacts/ 无四类 brief）验证 — PASS（仅 requirement.md + 交付总结.md）
- [x] AC-13c（usage-log.yaml 含真实 entry）验证 — PASS（≥ 1 条，完整字段）
- [x] AC-13d（交付总结 §效率与成本 无 ⚠）验证 — PASS
- [x] AC-14（契约 7 + 硬门禁六 自证）验证 — PASS（首次引用均带描述；DAG 表无裸数字扫射）
- [x] AC-15（scaffold_v2 mirror 同步）验证 — PASS（diff = 0；4 scaffold_v2 pytest passed）
- [x] AC-16（本阶段已结束 ≥ 4）验证 — PASS（16 命中，12 文件）
- [x] R1 越界核查 — PASS
- [x] revert 抽样 — PASS（说明：uncommitted 状态，skip dry-run）
- [x] 契约 7 合规扫描 — PASS
- [x] req-29（角色→模型映射）回归 — PASS
- [x] req-30（用户面 model 透出）回归 — PASS
- [x] 写 testing-report.md 到权威位置（flow/requirements/req-41-.../testing-report.md）
- [x] 写本 session-memory.md

## 5. 关键发现

### AC-01 注释（artifacts-layout.md 引用数）

严格 grep `.workflow/ -r` 命中 52 处，但分布如下：
- `.workflow/state/`（历史文档 req-39 era）：22 处 — 历史存量豁免，不要求迁移
- `.workflow/flow/requirements/req-41-.../`（req-41 内部 change.md/plan.md 描述重命名操作的史志文件）：28 处 — meta-documentation 豁免
- `.workflow/flow/repository-layout.md`（migrated_from frontmatter + 历史注记）：2 处 — 来源声明豁免
- `.workflow/context/`（活动角色文件）：**0 处** — 满足 AC-01 核心约束

活动工作流文件层面 artifacts-layout.md refs = 0，AC-01 PASS。

### stage-role.md AC-07 注释

stage-role.md grep 命中 1 处为 req-41 废止公告："requirement_review / planning / executing / regression 四类对人 brief ... 已由 req-41 废止，req-id ≥ 41 起不再产出"。这是废止声明，非要求产出，AC-07 PASS。

### AC-14 注释

requirement.md 中 `req-02 ~ req-40` 为范围引用（表达历史存量），非单个 ID 首次引用，不要求逐一带 title。chg-01 在 AC-16 spec 本文中出现但其完整标题在 §5.2 中已有。PASS。

### pre-existing FAIL

`test_readme_has_refresh_template_hint`（test_smoke_req28.py）检查 README.md 含 `pip install -U harness-workflow` 字段，当前 README 已精简重构不含该行，与 req-41 无关，按 "1 pre-existing ReadmeRefreshHintTest 不算" 豁免。

## 6. 开放问题 / default-pick

- 无阻断性问题

## 7. 判定

**PASS** — 推进 acceptance。

本阶段已结束。
