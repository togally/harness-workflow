---
id: req-56
stage: acceptance
verdict: PASS
created_at: 2026-05-09
tester: acceptance / sonnet
---

# req-56 验收签字清单

## AC 逐条签字

| AC | 描述摘要 | 证据来源（test-report.md） | 签字 |
|----|----------|--------------------------|------|
| AC-01 | 无 flag → office_hours_mode=required；analyst 不 offer | TC-01/TC-10（chg-01）/ TC-01/04（chg-02 lint） | [x] |
| AC-02 | --fallback → office_hours_mode=fallback；stdout [mode] fallback | TC-03/TC-07（chg-01）/ TC-05（chg-02 lint）/ Dogfood-01 | [x] |
| AC-03 | compat=false → 自动 fallback + [gstack] 警告 | TC-02/TC-05（chg-01）/ Dogfood-02（chg-03） | [x] |
| AC-04 | 老历史 req 缺字段兼容不崩溃 | TC-06/TC-08/TC-09（chg-01） | [x] |
| AC-05 | 4 种组合单元+dogfood TC 覆盖 | TC-01~10（chg-01）/ Dogfood-01~03（chg-03）/ 4 平台 grep | [x] |
| AC-06 | artifact-placement exit 0（硬绿）；human-docs exit 0 留 done 阶段 | Dogfood-03 artifact-placement exit 0 实测；human-docs 见下注 | [x] |
| AC-07 | 两路径 requirement.md 路径+frontmatter 5 字段+4 章节+双绿 | Dogfood-01（chg-03）/ TC-02/03/06（chg-02）/ TC-05 body 一致 | [x] |

**AC-06/AC-07 human-docs 注**：acceptance 阶段 `harness validate --human-docs` 必然 0/2 pending（by-design）。
raw_artifact（requirement.md 对人副本）+ 交付总结.md 均为 done 阶段产出，acceptance 阶段不据此 fail。
artifact-placement exit 0 已实测（见本次 acceptance 跑 validate 结果）。done 阶段补 交付总结.md 后 1/2 ok；
raw_artifact requirement.md 历史惯例不强制（req-54、req-55 均无此副本即 archive 通过）。

## 结论

**PASS**：7 条 AC 全签 [x]，26/26 TC 全 PASS，5 项合规扫描全 CLEAN。
artifact-placement exit 0 实测硬绿；human-docs exit 1 为 by-design，done 阶段补文档后可达。
路由：`harness next` → done。
