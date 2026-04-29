---
id: bugfix-2
title: pre-existing pytest 3 failures：test_chg03_title_contract.py 与 test_smoke_req29.py 硬编码 req-29 / req-30 旧目录名（req-29 实际归档为 角色-模型映射-... 而非 批量建议合集）
created_at: 2026-04-23
---

# Problem Description

3 pytest fail（pre-existing，跨 req-29/30/31..36 持续红）：
- `tests/test_chg03_title_contract.py::TestReq30SelfCertification::test_req_30_implementation_docs_first_reference_has_title`
- `tests/test_chg03_title_contract.py::TestReq30SelfCertification::test_req_30_implementation_docs_exist_for_each_completed_change`
- `tests/test_smoke_req29.py::HumanDocsChecklistTest::test_human_docs_checklist_for_req29`

触发：`PYTHONPATH=src python3 -m pytest`

错误样本（test_smoke_req29）：
```
AssertionError: req-29 dir not found in active or archive:
  /Users/jiazhiwei/claudeProject/harness-workflow/artifacts/main/requirements/req-29-批量建议合集（2条）
  /Users/jiazhiwei/claudeProject/harness-workflow/artifacts/main/archive/requirements/req-29-批量建议合集（2条）
```

**实际目录名**（已查）：
- req-29 实际归档：`req-29-角色-模型映射-开放型角色用-opus-4-7-执行型角色用-sonnet`
- req-30 实际归档：`req-30-角色-model-对用户透出-自我介绍-派发说明补-model-字段`

# Root Cause Analysis

测试硬编码 req-29 / req-30 的目录名，但这两个 req 在生命周期内被 rename（原 "批量建议合集（2条）" → 当前 "角色-模型映射-..."；req-30 同样 rename 过）。测试没有跟随 rename 更新，归档后断红。

非真问题（功能没坏），是测试 fixture 漂移。

# Fix Scope

- `tests/test_chg03_title_contract.py`：更新 `REQ_DIR_NAME` / 等价常量为实际归档目录名
- `tests/test_smoke_req29.py`：更新 `REQ_DIR_NAME` 常量为实际归档目录名
- **不动**业务代码

# Fix Plan

1. 读两个测试文件找硬编码常量
2. grep 出实际归档目录名（命令：`ls artifacts/main/archive/requirements/ | grep -E "^req-(29|30)"`）
3. 替换硬编码字符串
4. 跑 pytest 确认 308 → 311 全绿

# Validation Criteria

- `PYTHONPATH=src python3 -m pytest -q` 退出 0
- 失败数从 3 → 0
- 通过数从 308 → 311（或同等 +3）
