---
id: bugfix-12
verdict: PASS
signed_by: acceptance / sonnet
signed_at: 2026-05-10
---

# 验收报告 — bugfix-12（harness archive 输入未识别时误归档首个 done req）

## AC 签字

| AC | 描述 | 结果 |
|----|------|------|
| AC-01 | 输入未识别报错不静默归档 | [x] PASS |
| AC-02 | 合法输入正常归档 | [x] PASS |
| AC-03 | runtime fallback 失败也应报错 | [x] PASS |
| AC-04 | 合法 runtime fallback 路径不破坏 | [x] PASS |

异议数：0

## 独立核查

独立执行 `pytest tests/test_bugfix12_archive_input_validation.py -v`：**10/10 PASS**。F1+F2 双层防御代码落地核实。

## 开放问题 / default-pick

- testing 漏洞：default-pick (a)，接受兜底 test-evidence，executing 子 agent 实质完成 testing，sug-78 已记。
- human-docs：0/4 present，4 pending by-design（done 阶段产出），不阻塞。

## 路由建议

`harness next` → **done**
