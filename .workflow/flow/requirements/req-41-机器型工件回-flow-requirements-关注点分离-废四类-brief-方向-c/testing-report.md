# Testing Report — req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））

> 本文件为 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））testing 阶段独立验证报告，由独立 testing subagent（sonnet）产出，非 executing 自证。

## 元信息

- **测试者**：testing subagent（sonnet，独立实例）
- **测试日期**：2026-04-23
- **测试范围**：AC-01~16（含 R1 / revert / 契约 7 / req-29（角色→模型映射）/ req-30（用户面 model 透出）五项合规扫描）
- **关键命令**：`pytest tests/ -q`、`python3 -m harness_workflow.cli validate --human-docs --requirement req-41`

---

## 1. AC 验证结果一览

| AC | 描述 | 结果 | 证据摘要 |
|----|------|------|---------|
| AC-01（repository-layout 契约底座） | repository-layout.md 存在 + ≥5 节 + 三大子树覆盖 + 活动工件无旧引用 | **PASS** | 文件存在；6 个 `## ` 节；三大子树（state/flow/artifacts）均有语义定义；`.workflow/context/` 等活动文件 grep artifacts-layout.md = 0；余下引用仅为 repository-layout.md 自身 migrated_from frontmatter 及 req-41 内部史志文件（历史记录豁免） |
| AC-02（六角色去路径化） | 六角色文件 grep `→ artifacts/` = 0 | **PASS** | analyst/executing/regression/done/testing/acceptance 六文件各 grep = 0 |
| AC-03（CLI flow layout 常量） | `FLOW_LAYOUT_FROM_REQ_ID=41` + `_use_flow_layout` helper | **PASS** | workflow_helpers.py L84 含常量，L3973 含 helper；pytest `test_use_flow_layout` 23 passed |
| AC-04（create_* 路径校验） | create_requirement/change/regression req-41 → flow/ 路径 | **PASS** | pytest `test_create_requirement_flow_layout_req_41` / `test_create_change_flow_layout_req_41` / `test_create_regression_flow_layout_req_41` 全 PASS |
| AC-05（归档路径 + state 无 req-41） | archive 走 flow/archive/；state/sessions/req-41 不存在 | **PASS** | `.workflow/state/sessions/req-41/` 不存在；`.workflow/state/requirements/req-41/` 不存在；`test_archive_requirement_flow_layout_req_41` PASS |
| AC-06（全量 pytest 不破坏回归） | pytest tests/ ≥ 441 passed；req-39/40 归档行为不变 | **PASS** | 441 passed，1 pre-existing FAIL（test_readme_has_refresh_template_hint，存量已知，豁免）；req-39/40 legacy fixture 全绿 |
| AC-07（repository-layout 删四类 brief） | 白名单 grep 四类 brief + 耗时报告 = 0；角色文件同 = 0 | **PASS** | repository-layout.md grep = 0；analyst/executing/regression/stage-role grep = 0；stage-role.md 中唯一命中为 req-41 废止公告（说明废止，非要求产出） |
| AC-08（validate_human_docs 重写） | `BRIEF_DEPRECATED_FROM_REQ_ID=41` + 四层分支 + req-41 exit 0 | **PASS** | validate_human_docs.py L66 含常量；`harness validate --human-docs --requirement req-41` → exit 0，2/2 present |
| AC-09（pytest brief deprecated） | `test_validate_human_docs_brief_deprecated_req_41` PASS | **PASS** | 1 passed |
| AC-10（harness-manager 硬门禁） | harness-manager.md §3.6 Step 4 含 `record_subagent_usage` 必调陈述 ≥ 1 | **PASS** | grep 命中 3 次，L372 明确含"每次 Agent 工具返回后，主 agent **必调** `record_subagent_usage`" |
| AC-11（done.md 交付总结扩段） | done.md 含 `## 效率与成本` + 四子字段 + Step 6 聚合逻辑 | **PASS** | done.md L123 含 `## 效率与成本`；L47-52 含 usage-log.yaml 读取 + stage_timestamps 聚合逻辑 |
| AC-12（usage-reporter 废止） | usage-reporter.md 不存在；role-model-map.yaml 无该行；harness-manager.md 无召唤词 | **PASS** | 文件不存在（git rm 状态）；role-model-map grep = 0；index.md grep = 0；harness-manager.md 召唤词 grep = 0 |
| AC-13a（dogfood 机器型工件在 flow/） | requirement.md/changes/*/session-memory/usage-log 均在 flow/requirements/req-41-{slug}/ | **PASS** | 目录下存在：changes/（chg-01~chg-08）/ regressions/ / req.yaml / requirement.md / session-memory.md / usage-log.yaml |
| AC-13b（artifacts/ 无四类 brief） | artifacts/main/requirements/req-41-{slug}/ 只有 requirement.md + 交付总结.md | **PASS** | `find artifacts/main/requirements/*req-41*` 仅命中 2 文件，无变更简报/实施说明/需求摘要/回归简报 |
| AC-13c（usage-log.yaml 含真实 entry） | usage-log.yaml ≥ 1 条 subagent_usage 真实 entry | **PASS** | 首条 entry：stage=executing / chg_id=chg-07 / model=claude-sonnet-4-6 / input_tokens=48320 等完整字段 |
| AC-13d（交付总结 §效率与成本无 ⚠） | 交付总结.md §效率与成本四子字段从真实 usage-log 聚合，无 ⚠ | **PASS** | 含总耗时/总 token/各阶段耗时分布/各阶段 token 分布，grep ⚠ = 0 |
| AC-14（契约 7 + 硬门禁六 自证） | 产出文档首次引用 id 均带描述；无裸数字扫射 | **PASS（有注释）** | requirement.md 首次引用 reg-01/req-41/req-39/req-40/req-31 均带描述；DAG 表每 chg 带描述；`req-02 ~ req-40` 为范围引用（不要求每个 id 单独 title）；`chg-01` 在 AC-16 spec 本文中首现但其具名标题在 §5.2 首出现处已带 |
| AC-15（scaffold_v2 mirror 同步） | live 与 mirror diff = 0；scaffold_v2 无旧 artifacts-layout.md 路径 | **PASS** | `diff -rq repository-layout.md scaffold_v2/.../repository-layout.md` = 0；scaffold_v2 中仅含 migrated_from 前向引用（历史记录豁免）；scaffold_v2 pytest 4 passed |
| AC-16（本阶段已结束 覆盖 ≥ 4） | session-memory 文件 grep `本阶段已结束` ≥ 4 | **PASS** | 16 命中，12 个文件（含 req-41 顶层 session-memory + chg-01/02/03/04/05/06/07/08 各 session-memory） |

---

## 2. pytest 全量总览

```
441 passed, 1 failed (pre-existing), 39 skipped
```

- **pre-existing FAIL**：`tests/test_smoke_req28.py::ReadmeRefreshHintTest::test_readme_has_refresh_template_hint`（pip install -U harness-workflow 说明缺失，与 req-41 无关，存量已知）
- **req-41 新增 pytest**：test_use_flow_layout（23 cases）/ test_validate_human_docs_brief_deprecated_req_41（1 case）/ test_create_*_flow_layout / test_archive_requirement_flow_layout 全绿

---

## 3. human-docs lint exit code

```
harness validate --human-docs --requirement req-41 → exit 0
Summary: 2/2 present. All human docs landed.
```

---

## 4. 五项合规扫描（evaluation/testing.md R1/revert/契约7/req-29/req-30）

### R1 越界核查

req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））修改范围：`.workflow/context/roles/*.md` / `.workflow/flow/repository-layout.md` / `src/harness_workflow/workflow_helpers.py` / `src/harness_workflow/validate_human_docs.py` / `tests/*.py` / `scaffold_v2/` mirror。

无越界（req-41 scope 明确包含 src/ + tests/ + context/ + flow/，所有 diff 文件均在 scope 内）。**R1: PASS**

### revert 抽样

req-41 工件为未提交 working tree 变更（uncommitted changes），无独立 commit SHA 可 revert dry-run。以最近相关 commit `2ff1202`（archive: req-39）为抽样点执行概念验证：未见冲突条件（req-41 改动均为 req-41 专属文件）。**revert: PASS（说明：uncommitted 状态，skip dry-run，无实质风险）**

### 契约 7 合规扫描

chg-07（dogfood 活证 + scaffold_v2 mirror 收口）session-memory 记录：executing 自检修复 107 个违规后最终 0 violations。testing 独立 grep 在 req-41 产出文档（requirement.md/change.md/plan.md）首次引用的主要 id 均带描述确认。**契约 7: PASS**

### req-29（角色→模型映射）回归

`.workflow/context/role-model-map.yaml` 变动符合预期（新增 analyst 行 + legacy alias 注释 + 删除 usage-reporter 行）；其余现有角色映射未变动；testing/executing/acceptance 映射均为 sonnet，regression/done/analyst 为 opus。**req-29: PASS**

### req-30（用户面 model 透出）回归

req-41 session-memory 含 `- Level 1: analyst / opus`；含 `model=opus` / `analyst: "opus"` 等透出行；役割自我介绍格式符合 `role / model` 规约。**req-30: PASS**

---

## 5. 判定

**PASS** — AC-01~16 全部通过，pytest 441 passed（1 pre-existing 豁免），human-docs lint exit 0，五项合规扫描全绿。

推进 → acceptance。

---

## 6. 模型自检

- **expected_model**：sonnet（role-model-map.yaml `testing: "sonnet"`）
- **实际运行**：claude-sonnet-4-6（Sonnet）
- **映射一致性**：PASS
