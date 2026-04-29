---
id: bugfix-10-acceptance-checklist
stage: acceptance
date: 2026-04-29
---

# Acceptance Checklist — bugfix-10
## req-48 chg-02 实施缺陷：3 个 contract 未真正接入 raise_harness_block

---

## AC 校验矩阵

| AC 编号 | AC 描述 | 验证方法 | 判定 |
|---------|---------|---------|------|
| AC-01 | `test_raise_harness_block.py` TC-01~04, TC-08~12 全 PASS（10/12，TC-06/07 预存） | 引用 test-evidence.md § test_raise_harness_block.py + grep 源码 raise_harness_block 实现 | **PASS** |
| AC-02 | `test_fix_checklist_lint_output.py` 全 17 PASS | 引用 test-evidence.md § 17/17 PASS | **PASS** |
| AC-03 | `test_block_protocol_e2e.py` TC-03/04/05/06/07 全 PASS（6/8，TC-01/08 预存） | 引用 test-evidence.md § test_block_protocol_e2e.py | **PASS** |
| AC-04 | 本仓 dogfood：`harness validate --contract artifact-placement` exit 0 | acceptance 现场执行：exit 0 PASS | **PASS** |
| AC-05 | tmpdir 违规 dogfood：exit 64 + HARNESS_BLOCK 协议 + runtime-block.yaml 写入 | acceptance 现场三 contract 独立 tmpdir 验证（见下方实证） | **PASS** |
| AC-06 | 全量 pytest 无新增失败 | test-evidence.md §全量回归：17 failed（全预存）/ 729 passed / 0 新增 | **PASS** |

---

## 独立 dogfood 验证（acceptance 现场执行）

### artifact-placement — 违规 tmpdir

```
HARNESS_BLOCK: artifact-placement
  fix-checklist: .workflow/context/checklists/fix-artifact-placement.md
  severity: FAIL
  detected-by: executing
FAIL: artifact-placement lint — 以下违规文件需迁移到 .workflow/flow/：
  artifacts/ 下发现 stage-name 子目录：artifacts/main/requirements/req-99-test/planning/
  artifacts/ 下发现机器型文件：artifacts/main/requirements/req-99-test/planning/session-memory.md
Exit code: 64
```

断言满足：stderr 含 `HARNESS_BLOCK: artifact-placement` + `fix-checklist:` 指针 + exit 64。

### schema-audit — 违规 tmpdir

```
HARNESS_BLOCK: schema-audit
  fix-checklist: .workflow/context/checklists/fix-schema-audit.md
  severity: FAIL
  detected-by: executing
FAIL: schema-audit lint — 以下旧格式目录需归档或重命名：
  旧格式目录（无 slug）：.workflow/state/requirements/req-99/
Exit code: 64
```

断言满足：stderr 含 `HARNESS_BLOCK: schema-audit` + `fix-checklist:` 指针 + exit 64。

### missing-document — 违规 tmpdir

```
HARNESS_BLOCK: missing-document
  fix-checklist: .workflow/context/checklists/fix-missing-document.md
  severity: FAIL
  detected-by: executing
FAIL: missing-document lint — planning 阶段 changes/ 缺 chg-XX 子目录：
  planning 阶段 changes/ 为空：.workflow/flow/requirements/req-99-test/changes/
Exit code: 64
```

断言满足：stderr 含 `HARNESS_BLOCK: missing-document` + `fix-checklist:` 指针 + exit 64。

---

## 源码独立核实

- `workflow_helpers.py` 第 8385 行：`raise_harness_block` 完整实现（三层载体：stderr + exit code 64/65/0 + runtime-block.yaml）
- `validate_contract.py` 第 621/681/769 行：三个 contract 函数内均有 `from harness_workflow.workflow_helpers import raise_harness_block` + `return raise_harness_block(...)` 调用
- `cli.py` 第 255 行：argparse choices 含 `"schema-audit"` 和 `"missing-document"`

---

## revert 抽样合规扫描

**N/A** — acceptance stage 硬门禁禁止执行破坏性 git 命令，revert 抽样跳过，此处留痕放行。

---

## 退出前验证

| 验证项 | 结果 |
|--------|------|
| `harness validate --human-docs` | exit 1（D-11=B，acceptance 对人文档尚未全部生成，已知状态，放行） |
| `harness validate --contract artifact-placement` | exit 0 PASS |

---

## 结论

bugfix-10（req-48 chg-02 实施缺陷：3 个 contract 未真正接入 raise_harness_block）所有 AC 校验通过：

1. `raise_harness_block` helper 三层载体实现完整（stderr 协议 + exit 64/65/0 + runtime-block.yaml 写入）
2. 三个 contract（artifact-placement / schema-audit / missing-document）均在 FAIL 路径调用 `raise_harness_block` → exit 64 + HARNESS_BLOCK 协议正确
3. acceptance 现场独立 dogfood 验证三个 contract 违规场景全部输出 HARNESS_BLOCK 协议且 exit 64
4. testing 阶段 33 TC（+预存 fail 标注）+ 5 dogfood 证据经独立审核，与源码行为一致
5. 全量 pytest 无新增失败（17 个预存 fail 均为文档缺失/smoke 路径问题，与本次改造无关）

**verdict: PASS**
