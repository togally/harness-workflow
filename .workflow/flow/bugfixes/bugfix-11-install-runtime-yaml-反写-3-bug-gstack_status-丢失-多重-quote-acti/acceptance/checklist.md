---
id: bugfix-11
title: "install runtime.yaml 反写 3 bug：gstack_status 丢失 + 多重 quote + active_requirements 清空"
created_at: 2026-05-08
operation_type: bugfix
stage: acceptance
---

## 验收对照表

| # | bug | 期望行为 | 实测结果 | 验收 |
|---|---|---|---|---|
| B1 | runtime.yaml 字段值多重 quote 累积 | install N 次后字段 escape 不累积 | `locked_requirement: ""`（清洁标准 yaml） | ✅ PASS |
| B2 | gstack_status 字段消失 | install 后 runtime.yaml 含完整 gstack_status 4 子字段 | 4 子字段齐全 + 46 个 installed_skills 列表 + vendor_version=c7aefc1 + last_install=ISO8601 + agent_kind_compatible=true | ✅ PASS |
| B3 | active_requirements 跨 req 清空 | install 后保留原 active_requirements | `[bugfix-11]` 保留 | ✅ PASS |

## 用户拍板的 4 条决策落地核查

| # | 决策点 | 拍板结果 | 落地状态 |
|---|---|---|---|
| 1 | 修复方案 | B（统一 writer） | ✅ `_write_gstack_status` 改走 `load_requirement_runtime` → 修改 → `save_requirement_runtime` 单一管线；grep guard 验证 yaml.dump 不再直写 runtime |
| 2 | contract lint 扩展 | 否 | ✅ 不在本 bugfix 范围（已记入 sug 候选） |
| 3 | retroactive 重 archive req-55 | **否（用户覆盖）** | ✅ 不重 archive；chg-01 真活证由本 bugfix 兑现（早于 chg-05 候选 P deferred 路径） |
| 4 | _parse_simple_yaml_scalar self-heal | 是 | ✅ 已加成对单引号剥层逻辑；历史污染 runtime 自动恢复 |

## 测试覆盖

- 新增 10 用例（P0×6 + P1×4）：tests/installer/test_install_runtime_writer.py
- 既有 chg-01 测试 0 回归：tests/installer/test_gstack_skills_push.py 8/8 + tests/integration/test_install_pushes_gstack.py 7/7
- 合计 25/25 实质用例通过

## 端到端真活证

- `pipx install --force` + `harness install --agent claude` 真跑通过
- [gstack] Pushed 46 skills 真活（chg-01 vendor 推送验证）
- runtime.yaml 端到端读写无污染

## 风险残留 / 后续 sug

- **B1 self-heal 仅剥单引号**：未覆盖嵌套双引号场景；如有跨平台 yaml writer 引入双引号污染需另案处理（pre-existing 风险，不计本次）
- **runtime-yaml-shape 契约 lint** 可作 sug（用户决策 2 = 否，留 sug 候选）
- /usr/local/bin/harness 残留（PEP 668 阻止 pip uninstall；不影响功能）

## 结论

- **验收判定：PASS**
- **verdict 路由：done**
- 简要理由：3 bug 端到端实测验证全 PASS；25/25 测试通过 0 回归；4 条用户拍板决策全部落地；chg-01 真活证此次兑现。
- 推荐执行步骤：harness next 推到 done → commit + push → archive bugfix-11
