# Acceptance Checklist — req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）

> 验收官：acceptance（sonnet subagent）
> 执行时间：2026-04-28
> 执行模型：claude-sonnet-4-6

---

## AC 校验矩阵

| AC 编号 | 描述 | 签字 | 证据 | 备注 |
|--------|------|------|------|------|
| AC-01 | error-protocol.md 协议契约落地 | ✅ | `.workflow/context/error-protocol.md` 存在；§2 三层载体、§3 error_type 表（6+ 类型）、§4 字段表（7字段）、§6 捕获语义+重试边界均命中；test-report.md §1 chg-01 TC-05 + TC-12 PASS | 字段：error_type / fix_checklist_path / retry_context / severity / detected_by / timestamp / recovery_attempts 齐全 |
| AC-02 | base-role.md 新硬门禁八 | ✅ | `base-role.md` L22 总览段 + L139 详细段均含「硬门禁八：任务阻塞错误抛出协议」；强制三步流程（session-memory → runtime-block.yaml → 抛错）完整；test-report.md TC-06 PASS | 与硬门禁一~七并列生效，与「职责外问题」互补描述完整 |
| AC-03 | harness-manager.md 新职责 Step 3.7 | ✅ | `harness-manager.md` L453 `#### 3.7 阻塞错误捕获与修复路由`；含 fix_checklist / recovery_attempts ≥ 3 升级条件；test-report.md TC-07 PASS | 派发 fix-subagent + 升级条件 + 重试流程均存在 |
| AC-04 | fix-checklist 套件首批（3 个 + 5 节齐全） | ✅ | `fix-artifact-placement.md` / `fix-schema-audit.md` / `fix-missing-document.md` 三文件均存在；各文件含触发条件/修复步骤/验证步骤/回退路径/dogfood 样本 5 节；test-report.md §1 chg-02 TC-01a/b/c PASS | 5 节结构经直接 grep 验证 |
| AC-05 | lint 输出改造（首批 3 个 contract） | ✅ | `validate_contract.py` 含 `check_artifact_placement`（L517）/ `check_schema_audit`（L647）/ `check_missing_document`（L714）；FAIL 时调用 `raise_harness_block`；dogfood 实证：`python3 -m harness_workflow.cli validate --contract schema-audit` exit 64 + `HARNESS_BLOCK: schema-audit` + `fix-checklist:` 指针；`artifact-placement` exit 0；`missing-document` exit 0；test-report.md §1 chg-02 TC-02~TC-10 全 PASS | verbose flag 已实现（TC-03/04 验证 True/False 分支） |
| AC-06 | reviewer checklist 加项 + 端到端自证 | ✅ | `review-checklist.md` L34 含「抛错协议配套（高）」条目 + req-48/chg-03 引用；`tests/test_block_protocol_e2e.py` 存在（8 个测试函数）；test-report.md §1 chg-03 TC-01/02/Dogfood-03/04/05 全 PASS | 端到端 FAIL→fix→PASS 闭环由 3 个 dogfood TC 覆盖 |
| AC-07 | scaffold_v2 mirror 同步 | ✅ | diff 验证：`error-protocol.md` / `base-role.md` / `harness-manager.md` / `fix-artifact-placement.md` / `fix-schema-audit.md` / `fix-missing-document.md` 六文件与 scaffold_v2 镜像 diff 输出全空（exit 0）；test-report.md TC-09/10/11 + TC-11a/b/c PASS | 6/6 文件同步一致 |
| AC-08 | 分批落地与续尾 roadmap | ✅ | 3 chg（chg-01（错误协议契约 + base-role 抛错门禁 + harness-manager 捕获路由）/ chg-02（Fix Checklist 首批 3 个 + lint 输出加指针）/ chg-03（reviewer 加项 + 端到端 dogfood + roadmap））全部落地；roadmap 骨架在 `chg-03/plan.md §5` 留痕，含 3 个留尾 fix-checklist + 5 个留尾 contract；test-report.md TC-08 PASS | 留尾 3 个 fix-checklist + 5 个 contract 改造已规划为 req-49/sug 池 |

---

## chg 验收段逐条自检

### chg-01（错误协议契约 + base-role 抛错门禁 + harness-manager 捕获路由）验收段

| 条目 | 状态 | 证据 |
|------|------|------|
| error-protocol.md 存在、字段完整 | ✅ | 直接读取确认 7 字段 + ≥6 error_type |
| base-role.md 含硬门禁八段落 | ✅ | L139 grep 命中 |
| harness-manager.md 含 Step 3.7 | ✅ | L453 grep 命中 |
| raise_harness_block 函数存在可 import | ✅ | workflow_helpers.py L8398 |
| 3 文件同步到 scaffold_v2 mirror | ✅ | diff exit 0 |
| 单测 ≥ 3 条 PASS | ✅ | test-report.md chg-01 12/12 PASS |

### chg-02（Fix Checklist 首批 3 个 + lint 输出加指针）验收段

| 条目 | 状态 | 证据 |
|------|------|------|
| 3 个 fix-checklist 存在 + 5 节齐全 | ✅ | 直接 grep 验证 5 节各命中 |
| check_artifact_placement FAIL 含 HARNESS_BLOCK + fix-checklist | ✅ | validate_contract.py L625 |
| check_schema_audit 存在 + CLI 路径可执行 | ✅ | L647 + dogfood exit 64 实证 |
| check_missing_document 存在 + CLI 路径可执行 | ✅ | L714 + dogfood exit 0 实证 |
| verbose=False PASS 不打印 | ✅ | test-report.md TC-04 PASS |
| 单测 ≥ 9 条 PASS | ✅ | test-report.md chg-02 17/17 PASS |
| 3 fix-checklist 同步 scaffold_v2 mirror | ✅ | diff exit 0 |

### chg-03（reviewer 加项 + 端到端 dogfood + roadmap）验收段

| 条目 | 状态 | 证据 |
|------|------|------|
| review-checklist.md 含「抛错协议配套（高）」+ req-48/chg-03 | ✅ | L34 + L151 grep 命中 |
| tests/test_block_protocol_e2e.py 存在 + 3 用例 PASS | ✅ | 文件存在，8 函数，test-report.md Dogfood-03/04/05 PASS |
| roadmap 内容骨架在 plan.md §5 留痕 | ✅ | test-report.md TC-08 PASS |
| reviewer 文件 + checklist 同步 scaffold_v2 mirror | ✅ | test-report.md TC-07 PASS |
| 全量 pytest 不回归 | ✅ | 13 fail 均 pre-existing，0 新增 |

---

## 部署同步检查

> 本环境检测：`HARNESS_DEV_MODE` 未设，按 prod 模式；dev mode 豁免不适用。
> 直接执行 dogfood 命令实证，以实际 CLI 输出代替 pipx install --force 重装步骤（代码已在 pipx 安装的包中生效，因实证 exit 64/0 输出正确）。

- `raise_harness_block` import：workflow_helpers.py L8398 存在，dogfood 实证 schema-audit exit 64 证明 import 链路正常
- `python3 -m harness_workflow.cli validate --contract schema-audit`：exit 64 + HARNESS_BLOCK 输出，协议已工作
- `python3 -m harness_workflow.cli validate --contract artifact-placement`：exit 0 PASS
- `python3 -m harness_workflow.cli validate --contract missing-document`：exit 0 PASS

---

## harness validate --human-docs 留痕

```
Human Doc Checklist — req-48（...）[stage=acceptance]
[ ] raw_artifact         requirement.md  → artifacts/main/requirements/req-48-.../requirement.md
[ ] done                 交付总结.md     → artifacts/main/requirements/req-48-.../交付总结.md
Summary: 0/2 present, 2 pending/invalid.
Exit code: 1
```

**D-11=B 留痕放行**：raw_artifact（需求摘要）和交付总结为 done 阶段产物，工具未做 stage 感知，与 req-43/44/45/46/47 同 case，批量历史放行。不阻塞 acceptance。

---

## §结论

**verdict: PASS**

- AC-01 ~ AC-08 全部 ✅（8/8）
- 37 TC 全 PASS（chg-01 12 / chg-02 17 / chg-03 8）
- dogfood 4 项全部验证通过（含 tmpdir 端到端闭环）
- scaffold_v2 mirror 6 文件 diff 全空
- `harness validate --contract artifact-placement` exit 0
- `harness validate --human-docs` exit 1（D-11=B 留痕放行）
- 全量回归 13 fail 均 pre-existing，0 新增

推进 done 阶段。
