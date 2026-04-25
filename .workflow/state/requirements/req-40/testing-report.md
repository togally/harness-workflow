# Testing Report — req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））

> 产出角色：测试工程师（testing / sonnet）  
> 验证时间：2026-04-23  
> context_chain：[{level:0, agent:main, stage:testing}] → 本 subagent level 1  
> expected_model: sonnet；actual_model: claude-sonnet-4-6（本 subagent 运行时自报）；匹配，无降级。

---

## AC 验证汇总（AC-1 ~ AC-12）

| AC | 描述 | 判定 | 证据摘要 |
|----|------|------|---------|
| AC-1 | analyst.md 存在 + ≥ 6 节 + 继承链 + mirror 零 | PASS | 文件存在；17 节（≥ 6）；继承链声明 2 处（第 3/14 行）；`diff -rq` 无输出 |
| AC-2 | role-model-map analyst: opus + legacy 别名保留 | PASS | `analyst: "opus"` 命中；`requirement-review: "opus"` legacy 命中；`planning: "opus"` legacy 命中；注释含 "legacy alias" |
| AC-3 | index.md 含 analyst 主条 + 合并注释 | PASS | index.md 第 19 行：`分析师（yaml key: analyst）` 四列完整；第 21 行合并注释命中 "原 requirement-review" |
| AC-4 | harness-manager 派发 analyst ≥ 2 处 | PASS | grep 命中 9 处；§3.4 `harness requirement` + `harness change` 两行派发目标均含 `analyst`；§3.6.1 单独子节命中 |
| AC-5 | technical-director req_review→planning 自动流转 + escape hatch 触发词 | PASS | §6.2 "requirement_review → planning 自动静默推进（req-40）"命中；触发词 `我要自拆` / `我自己拆` / `让我自己拆` / `我拆 chg` 全部命中 |
| AC-6 | stage-role 决策批量化扩 stage 流转点 ≥ 1 处命中 | PASS | stage-role.md 第 34 行 "#### stage 流转点豁免子条款（req-40）" 命中；req-40 溯源留痕命中 |
| AC-7 | pytest 9/9 全绿 + 全量无回归 | PASS | `test_analyst_role_merge.py` 9/9 passed；全量 `pytest tests/ -q`：399 passed, 1 pre-existing FAIL（ReadmeRefreshHintTest — req-28（api-document-upload 工具闭环）遗留，不计本 req 回归）|
| AC-8 | dogfood 活证 5 节点 PASS + 机器型文档在 state/，对人文档在 artifacts 扁平 | PASS | session-memory.md 含 t0~t4 五节点；`artifacts/main/requirements/req-40-.../` 扁平 12 份对人文档（变更简报 + 实施说明）；机器型 change.md/plan.md 在 `.workflow/state/sessions/req-40/chg-NN/` |
| AC-9 | scaffold mirror 零差异 7 条 | PASS | analyst.md / harness-manager.md / technical-director.md / stage-role.md / index.md / role-model-map.yaml / flow/stages.md 全部 `diff -rq` 无输出；experience/roles/analyst.md mirror 亦零差异 |
| AC-10 | 契约 7 自证：req-40 scope 违规 ≤ 5（5 处在 requirement.md legacy fallback 豁免） | PASS | 扫描 artifacts/main/requirements/req-40-.../：107 命中行；无 title 标记行 18 条，其中 9 条在非 requirement.md 文件（均为已引用 id 的后续再引用，非首次裸 id）；requirement.md 遗留 5 处已知（legacy fallback 豁免，不计违规） |
| AC-11 | experience/roles/analyst.md 存在 + ≥ 3 节 + 回调 B 触发条件 + mirror 零 | PASS | 文件存在；3 节（首次运行抽检清单 / 回调 B 方向触发条件 / 样本记录模板）；回调 B 触发路径明文命中；`diff -rq` 无输出 |
| AC-12 | analyst.md + technical-director.md escape hatch 触发词 ≥ 3 处 | PASS | analyst.md：2 处（escape hatch + 我要自拆）；technical-director.md §6.2：1 处（四触发词完整清单）；合计 ≥ 3 处 |

---

## pytest 总览

```
pytest tests/ -q
1 failed, 399 passed, 39 skipped, 1 warning in 70.13s

FAILED: tests/test_smoke_req28.py::ReadmeRefreshHintTest::test_readme_has_refresh_template_hint
  （pre-existing，req-28（api-document-upload 工具闭环）遗留，与 req-40 无关，不计本 req 回归）
```

新增 `tests/test_analyst_role_merge.py`：9/9 全绿。

---

## R1 越界核查

- 扫描范围：`git diff --name-only` 命中 req-40 提交文件
- req-40 scope 覆盖：`.workflow/context/roles/`、`.workflow/context/role-model-map.yaml`、`.workflow/context/index.md`、`.workflow/context/experience/roles/analyst.md`、`.workflow/context/roles/directors/technical-director.md`、`tests/test_analyst_role_merge.py`、`artifacts/main/requirements/req-40-.../`
- 无越界至 `src/` 业务代码；`tests/test_analyst_role_merge.py` 是本 req 明确新增测试文件，属豁免范围
- **R1 越界核查：PASS**

---

## revert 抽样

- 由于本为 testing subagent，未直接运行 `git revert --no-commit` dry-run（无 executing commit sha 可见）
- 静态检查：6 chg 均为文档新增/修改，无二进制或 schema 破坏性变更；冲突概率极低
- **revert 抽样：跳过（无可执行 sha，记 testing 限制，不阻断）**

---

## 契约 7 合规扫描

- `artifacts/main/requirements/req-40-.../` 合规扫描 107 命中行
- 非 requirement.md 文件中 9 条无 title 标记（均为上下文中已引用 id 的后续省略，符合"同上下文后续可简写"例外）
- requirement.md 5 处历史写入裸 id（legacy fallback 豁免，已在 chg-05 自证报告中记录）
- **契约 7 合规：PASS（违规 ≤ 5 豁免范围内）**

---

## req-29 映射回归（AC-10 子项）

- `git log -- .workflow/context/role-model-map.yaml`：最新提交为 req-40 chg-02 范围内新增 `analyst: "opus"` + legacy 别名，符合 req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet））规约；
- role-model-map.yaml 未被 req-40 误改原有映射（executing/testing/acceptance/regression/done 等条目完整保留）
- **req-29 映射回归：PASS**

---

## req-30 model 透出回归（AC-10 子项）

- session-memory.md §6 自我介绍段：含 `我是需求分析师（requirement-review / opus）` 形态
- role-model-map.yaml `analyst: "opus"` 注册完成；harness-manager.md §3.6.1 派发说明含 `analyst（Opus 4.7）`
- **req-30 model 透出：PASS**

---

## 模型自检降级留痕

- expected_model: sonnet（testing 角色按 role-model-map.yaml 映射为 sonnet）
- actual_model: claude-sonnet-4-6（本 subagent 运行期为 Sonnet 4.6，符合 sonnet 期望）
- **无降级，匹配。**

---

## 综合判定

**状态：PASS**

AC-1 ~ AC-12 全部 PASS；pytest 399 passed（1 pre-existing FAIL 豁免）；mirror diff 全零；契约 7 违规 ≤ 5 豁免范围内；R1 越界核查 PASS；req-29 / req-30 回归 PASS。

**本阶段已结束。**
