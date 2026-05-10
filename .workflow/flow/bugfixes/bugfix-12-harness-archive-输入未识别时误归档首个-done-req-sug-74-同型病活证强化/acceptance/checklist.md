---
id: bugfix-12
verdict: PASS
signed_by: acceptance / sonnet
signed_at: 2026-05-10
---

# 验收核查表 — bugfix-12（harness archive 输入未识别时误归档首个 done req）

## AC 逐条签字表

| AC | 描述 | 覆盖 TC | 结果 |
|----|------|---------|------|
| AC-01 | 输入未识别 id 报错不静默归档 | TC-01/02/05/Dogfood-07/08 | [x] 已满足 |
| AC-02 | 合法输入正常归档 | TC-03/04/09 | [x] 已满足 |
| AC-03 | runtime fallback 失败也应报错 | TC-05 | [x] 已满足 |
| AC-04 | 合法 runtime fallback 路径不破坏 | TC-06/10 | [x] 已满足 |

## 独立核查要点

- cli.py L143 已改为 preselect 不在 requirements 时 print stderr + return None（F1 深度防御）✓
- cli.py L630 validate 已提到 if 外，始终跑，显式 args 路径与 runtime fallback 路径均受保护（F2 主防线）✓
- 独立跑 `pytest tests/test_bugfix12_archive_input_validation.py -v`：**10/10 PASS**（独立核查实测）✓
- 既有套件：0 新增 fail（pre-existing fail 数量反减 5）✓
- 手工 E2E 三场景（req-99/bugfix-99/runtime-not-in-done）均 exit 1 + stderr + 无文件移动 ✓

## testing 漏洞处置（work-done gate 自动连跳，sug-78）

**选择方案 (a)**：接受当前 test-evidence.md（主 agent 兜底填实）。

理由：executing 子 agent（独立 sonnet 实例）实质完成了 10/10 单元 + E2E + 5 项合规扫描，证据翔实；本验收官已独立复现 10/10 PASS，核查有效；补派独立 testing 子 agent 代价大、无新增价值。漏洞已记 sug-78（work-done gate testing 阶段查 ## 结论 内容非空），不阻塞本 bugfix 路由。

## harness validate --human-docs 结果

0/4 present，4 pending（回归简报/实施说明/交付总结/bugfix-交付总结）—— by-design，done 阶段产出，不阻塞 acceptance。

## 结论

[x] **PASS — 可路由 done**

4/4 AC 已满足，独立实测 10/10，0 新增回归，F1+F2 双层防御落地，无实质异议。
