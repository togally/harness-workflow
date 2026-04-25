## 验收报告 — req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））

### AC 签字表

| AC 编号 | 签字 | 证据（测试记录 / 产物路径） | 备注 |
|--------|------|---------------------------|------|
| AC-01（repository-layout 契约底座） | ✅ | testing-report.md §1 — 文件存在，6 节，三大子树覆盖，活动文件 grep artifacts-layout.md = 0 | 历史引用豁免 |
| AC-02（六角色去路径化） | ✅ | testing-report.md §1 — analyst/executing/regression/done/testing/acceptance grep `→ artifacts/` = 0 | |
| AC-03（CLI flow layout 常量） | ✅ | testing-report.md §1 — workflow_helpers.py L84 + L3973；pytest test_use_flow_layout 23 passed | |
| AC-04（create_* 路径校验） | ✅ | testing-report.md §1 — pytest test_create_*_flow_layout_req_41 全 PASS | |
| AC-05（归档路径 + state 无 req-41） | ✅ | testing-report.md §1 — state/sessions/req-41 不存在；test_archive_requirement_flow_layout_req_41 PASS | |
| AC-06（全量 pytest 不破坏回归） | ✅ | testing-report.md §2 — 441 passed，1 pre-existing FAIL（test_readme_has_refresh_template_hint，与 req-41 无关，豁免） | |
| AC-07（repository-layout 删四类 brief） | ✅ | testing-report.md §1 — grep = 0；stage-role.md 唯一命中为废止公告 | |
| AC-08（validate_human_docs 重写） | ✅ | testing-report.md §3 — BRIEF_DEPRECATED_FROM_REQ_ID=41，exit 0，2/2 present | |
| AC-09（pytest brief deprecated） | ✅ | testing-report.md §1 — test_validate_human_docs_brief_deprecated_req_41 1 passed | |
| AC-10（harness-manager 硬门禁） | ✅ | testing-report.md §1 — grep 命中 3 次，L372 明确"每次 Agent 工具返回后，主 agent 必调 record_subagent_usage" | |
| AC-11（done.md 效率与成本段） | ✅ | testing-report.md §1 — done.md L123 含 `## 效率与成本`；L47-52 含聚合逻辑 | |
| AC-12（usage-reporter 废止） | ✅ | testing-report.md §1 — 文件不存在；role-model-map grep = 0；harness-manager.md 召唤词 grep = 0 | |
| AC-13（dogfood 活证四项） | ✅ | testing-report.md §1 — (a) flow/ 下工件齐全 (b) artifacts/ 无四类 brief (c) usage-log ≥1 真实 entry (d) 交付总结 §效率与成本 grep ⚠ = 0 | |
| AC-14（契约 7 + 硬门禁六自证） | ✅ | testing-report.md §4 — executing 修复 107 个违规后最终 0 violations；首次引用均带描述；DAG 表无裸数字扫射 | |
| AC-15（scaffold_v2 mirror 同步） | ✅ | testing-report.md §1 — diff = 0；scaffold_v2 pytest 4 passed | |
| AC-16（本阶段已结束覆盖 ≥ 4） | ✅ | testing-report.md §1 — 16 命中，12 文件 | |

### lint 门禁

```
harness validate --human-docs --requirement req-41
→ [✓] raw_artifact requirement.md
→ [✓] done 交付总结.md
→ Summary: 2/2 present. All human docs landed.
→ exit 0
```

### 契约 7 自检

req-41 scope 内 `.md` 文件 grep `(req|chg|sug|bugfix|reg)-[0-9]+` 命中行均含 `（...）` 描述；代码块 / 路径片段 / 范围引用（如 `req-02 ~ req-40`）按 legacy fallback 豁免。**命中违规数 = 0。**

### 异议流转建议

无 ❌ 条目，无需流转。

### 最终 gate（由人工填写）

通过 / 驳回 + 原因：_________________
