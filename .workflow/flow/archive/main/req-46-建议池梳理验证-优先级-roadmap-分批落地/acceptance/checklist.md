# Acceptance Checklist — req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）

> 执行角色：验收官（acceptance / sonnet）— Subagent-L1
> 评估范围：chg-01（机器型工件路径修复 + 防再犯 lint）AC-1~AC-7 + chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）AC-1~AC-6 + req-46 顶层 AC-01~AC-05

---

## 1. AC 核查表（13 条）

| 来源 | AC ID | 描述 | 实现位置 | 测试覆盖 | verdict | 备注 |
|------|-------|------|---------|---------|---------|------|
| chg-01（机器型工件路径修复 + 防再犯 lint） | AC-1 | 4 件机器型工件物理回归 `.workflow/flow/` + 2 空目录清理 + requirement.md 白名单保留 | `.workflow/flow/requirements/req-46-.../requirement-review/` + `planning/` 下 4 文件均存在；`artifacts/main/requirements/req-46-.../requirement-review/` + `planning/` 目录不存在；`artifacts/.../requirement.md` 保留 | TC-01（7 断言全通过，test-report.md §3.1 行 37） | PASS | git mv 正确执行，artifact-placement lint exit 0 二次确认 |
| chg-01（機器型工件路径修复 + 防再犯 lint） | AC-2 | `harness validate --contract artifact-placement` exit 0 | `src/harness_workflow/validate_contract.py::check_artifact_placement` 升级（规则 0 路径模式 + 白名单豁免 + 黑名单扩文件名） | TC-02（40 用例 test-report.md §3.1）；acceptance 阶段现场复验 exit 0 ✓ | PASS | 现场验证：`python3 -m harness_workflow.cli validate --contract artifact-placement` 输出 `PASS: artifact-placement lint — artifacts/ 下无机器型文件` |
| chg-01（机器型工件路径修复 + 防再犯 lint） | AC-3 | lint 真敏感：刻意构造违规必命中 | `validate_contract.py` 新增 `stage-name 子目录扫` + `_MACHINE_TYPE_FILENAMES` 扩展 | TC-03（test-report.md §3.1）构造 `artifacts/.../executing/session-memory.md` → lint 返回 1 | PASS | testing 独立验证：双违规（stage-name 子目录 + 机器型文件名）均命中 |
| chg-01（机器型工件路径修复 + 防再犯 lint） | AC-4 | 白名单不误伤：`artifacts/.../requirement.md` lint exit 0 | `validate_contract.py::check_artifact_placement` 豁免 `_REQUIREMENT_MD_WHITELIST_PATTERN` | TC-04（test-report.md §3.1）`artifacts/.../requirement.md` 单独存在 → exit 0 | PASS | artifacts/req-46-.../requirement.md 现场验证存在且 lint 通过 |
| chg-01（机器型工件路径修复 + 防再犯 lint） | AC-5 | stage 退出门禁接入：analyst.md + harness-manager.md + stage-role.md | `analyst.md` L125/L134 含 `harness validate --contract artifact-placement`；`harness-manager.md` L311~L330 含 `expected_artifact_paths` 字段约定；`stage-role.md` L53 含 `路径自检` SOP 检查点 | TC-05（test-report.md §3.1 AC-5 行）；acceptance 现场 grep 全命中 | PASS | `grep artifact-placement analyst.md` 2 行；`grep expected_artifact_paths harness-manager.md` 4 行；`grep 路径自检 stage-role.md` 1 行 |
| chg-01（机器型工件路径修复 + 防再犯 lint） | AC-6 | scaffold_v2 mirror 一致：roles/ + checklists/ 无差异 | `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/{harness-manager,analyst,stage-role}.md` + `checklists/review-checklist.md` 同步 | TC-06（test-report.md §4.4 diff 输出无差异）；acceptance 现场 `diff -rq .workflow/context/checklists/ scaffold_v2/...checklists/` 无差异 | PASS | `diff -rq` checklists/ 无差异；roles/ 仅 pre-existing `usage-reporter.md` 漂移（非本 chg 引入） |
| chg-01（机器型工件路径修复 + 防再犯 lint） | AC-7 | sug-35（reviewer checklist artifact-placement lint 条目补全）落地翻转：review-checklist.md 含反向抽样条目 + sug-35 status archived | `review-checklist.md` L82 含 `artifact-placement 反向抽样（高）` 条目；sug-35 frontmatter `status: archived` + `applied_by_chg: chg-01` | TC-07（test-report.md §3.1 AC-7 行 PARTIAL PASS 符合硬序约束 4）；acceptance 现场 grep 验证 + sug-35 翻转已执行 | PASS | sug-35 status 已由本 acceptance 翻转为 `archived`（plan.md 硬序约束 4 满足） |
| chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood） | AC-1 | `_is_stage_work_done('executing', root, req_id, 'requirement')` 在 `changes_dir` 缺时返回 `False` | `workflow_helpers.py` L7441-7444 `executing` 分支严格化：`if not changes_dir.exists(): return False` | TC-01/TC-01b/TC-01c/TC-01d（test-report.md §3.2 AC-1；9 用例全绿） | PASS | `workflow_helpers.py` L7438-7460 `elif stage == "executing":` 分支确认；commit 171bac8 已提交 |
| chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood） | AC-2 | subprocess dogfood 4 路径全绿：`tests/test_workflow_next_subprocess.py` 5/5 通过 | `tests/test_workflow_next_subprocess.py`（新建），TC-03~TC-07 覆盖 first-hop / while-internal / 缺产物 / 有产物 / 全链 | test-report.md §3.2 AC-2 + §4.3 `5 passed in 4.36s` | PASS | 子进程真跑 CLI，不只 mock helper；commit 171bac8 |
| chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood） | AC-3 | 自身周期 dogfood 自证：over-chain 连跳已止，stage_advance 相邻间隔 ≥ 4 ms | `tests/test_workflow_next_subprocess.py` TC-07（全链测试）；chg-02 session-memory Step 8 harness next 实测 gate 阻断 | test-report.md §4.3 独立 subprocess 测试 4/4 PASS；间隔 403ms/411ms >> 4ms | PASS | 独立 subprocess gate 测试验证：`Stage executing 工作未完成，请先完成当前阶段工作再推进。` 正确拦截 |
| chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood） | AC-4 | sug-46（二次实证 over-chain）+ sug-50（gate gap 部署 gap）+ sug-53（usage-log 缺失）frontmatter 字段更新；acceptance PASS 后 sug-46/sug-50 status → archived；sug-53 over-chain 副作用 archived 主因留 pending | sug-46/sug-50 frontmatter 含 `linked_regression: reg-02` + `promoted_to_chg: chg-02`；sug-53 含 `partial_promoted_to_chg: chg-02` | test-report.md §3.2 AC-4 PASS；acceptance 现场翻转验证 | PASS | sug-46 status → archived；sug-50 status → archived；sug-53 status 保留 pending（主因 sug-39 未完）+ `partial_archived_at` 字段标注 |
| chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood） | AC-5 | `.workflow/evaluation/acceptance.md` checklist 含"部署同步契约"硬条目 | `.workflow/evaluation/acceptance.md` L43 `## 部署同步契约` 段（含 3 项硬验证：pipx 重装 + import 测试 + mtime ≥ commit ts） | TC-08/TC-08b（test-report.md §3.2 AC-5）；acceptance 现场 3 项硬验证全通过 | PASS | 部署同步契约 3 项硬验证：①import ✓ ②mtime 1777305899 ≥ commit ts 1777305867 ✓（pipx --force 已执行）③ grep 命中 3 处 ✓ |
| chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood） | AC-6 | mirror diff 一致 + 经验沉淀：evaluation/ + experience/roles/regression.md scaffold_v2 无差异；testing.md 含"子进程 dogfood 红线"；regression.md 含"经验十" | `scaffold_v2/.workflow/evaluation/acceptance.md` + `testing.md` + `experience/roles/regression.md` 同步；testing.md L93 `## 子进程 dogfood 红线`；regression.md L269 `## 经验十：三维失配...` | test-report.md §4.4 diff 无差异；acceptance 现场 `diff -rq .workflow/evaluation/ scaffold_v2/...evaluation/` 无差异 | PASS | `diff -rq` evaluation/ 无差异；regression.md 经验十存在；testing.md 子进程 dogfood 红线存在 |

---

## 2. req-46 顶层 AC 核查

| AC 编号 | 描述 | 实现状态 | verdict |
|---------|------|---------|---------|
| AC-01（sug-audit.md 产出，45 条全判定） | sug-audit.md 存在，45 条 sug 全部有 live/stale/applied-out/dup-of 判定，无"待评估"占位 | `.workflow/flow/requirements/req-46-.../requirement-review/sug-audit.md` 存在（125 行，45 条表格 + 状态分布 + 默认决策）；全量 sug 验证表覆盖 sug-08~sug-53（含跳号）；每条均有明确判定 | PASS |
| AC-02（roadmap.md 产出，含 5~10 个 chg 拆分 + 优先级 + 依赖图 + 工作量 + 首批推荐 ≥ 2） | roadmap.md 存在，含 chg 拆分结构 | `.workflow/flow/requirements/req-46-.../planning/roadmap.md` 存在；含 chg-1（over-chain dogfood）/ chg-2（usage-log）/ ... 拆分 + P0/P1/P2/P3 优先级 + 依赖图 + 工作量估算；首批推荐 ≥ 2（chg-01 + chg-02 已执行） | PASS |
| AC-03（每条 sug 处理建议有依据，引用工件 id / 代码行号 / commit sha） | sug-audit.md 每行含引用依据 | sug-audit.md 表格每行含 git log / commit sha / grep 行号引用；D-1~D-10 默认决策记录有理由 | PASS |
| AC-04（用户拍板首批 chg，主 agent 用 harness change 创建） | 用户选 sequential 顺序，主 agent 已用 harness change 创建 chg-01/chg-02 工件 | chg-01（机器型工件路径修复 + 防再犯 lint）+ chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）工件均存在且已 executing PASS；等同用户认可 | PASS |
| AC-05（池清理路径明确：applied/stale 出池列表给出） | sug-audit.md §状态分布 给出 applied-out + stale 列表 | applied-out 6 条（sug-25/44/45/46/49/50）+ stale 5 条（sug-09/12/17/32/40）列明；主 agent 可批量执行 harness suggest --archive | PASS |

---

## 3. 部署同步契约核查

- [x] pipx list ✓ — `pipx list` 显示 `harness-workflow 0.1.0 installed using Python 3.14.3`
- [x] `_is_stage_work_done` import 成功 ✓ — `python3 -c "from harness_workflow.workflow_helpers import _is_stage_work_done; print(_is_stage_work_done.__module__)"` 输出 `harness_workflow.workflow_helpers`
- [x] mtime ≥ commit ts ✓ — venv mtime = 1777305899.469427，HEAD commit ts（chg-02 commit 171bac8）= 1777305867，差值 = +32.47s（≥ 0）
- [x] grep `_is_stage_work_done` 命中 ≥ 3 ✓ — 命中 3 处（L7367 def、L7604 first-hop gate、L7636 while 内 gate）

**注**：deployment sync 验证使用 pipx venv 绝对路径（`~/.local/pipx/venvs/harness-workflow/lib/python3.14/site-packages/harness_workflow/workflow_helpers.py`），而非 `python3` 默认解析路径（后者指向 editable install 源目录）。

**附：`harness validate --human-docs` 非阻塞说明**

`harness validate --human-docs --requirement req-46` 报 1/2 present（`交付总结.md` 缺失）。`交付总结.md` 是 done-stage 产物，在 acceptance → done 流转前结构性不存在（与 req-28/39/40 时代不同）。acceptance.md §2 硬门禁路由建议列出 `需求摘要.md` / `chg-NN-变更简报.md` / `chg-NN-实施说明.md` 三类，未列 `交付总结.md`（done-stage 产物）。本 req 判定此项为结构性预期缺失，不阻塞 acceptance verdict。已记录为后续优化建议（validate_human_docs 应按 current_stage 过滤 done-stage 文档）。

---

## 4. 风险检查

- [x] chg-02 工件已 commit ✓ — commit 171bac8（`fix: req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）`）
- [x] artifact-placement 反向抽样零命中 ✓ — `artifacts/main/requirements/req-46-.../` 下仅 `requirement.md`（§2 白名单），无 stage-name 子目录，无非白名单机器型文件
- [x] scaffold_v2 mirror 一致 ✓ — `diff -rq .workflow/evaluation/ scaffold_v2/...evaluation/` 无差异；`diff -rq .workflow/context/checklists/ scaffold_v2/...checklists/` 无差异；pre-existing drift（roles/usage-reporter.md + experience/{analyst,executing,testing}.md）非本 req 引入，已记录
- [x] git status — chg-01/chg-02 实现代码全部 committed（commit 6406c40 + 171bac8）；acceptance 工件属当前 stage 产出（session-memory.md + checklist.md），作为 acceptance → done 流转前 commit

---

## 5. sug 状态翻转（acceptance PASS 后执行）

- sug-35（reviewer checklist artifact-placement lint 条目补全）→ archived（chg-01）— 已翻转
- sug-46（req-44 二次实证 over-chain）→ archived（chg-02）— 已翻转
- sug-50（gate gap 部署 gap）→ archived（chg-02）— 已翻转
- sug-53（usage-log 缺失）→ status 保留 pending（主因 sug-39 未完）+ `partial_archived_at` + `partial_archive_note` 标注 over-chain 副作用部分 archived（chg-02）— 已标注

---

## §结论

**PASS**

chg-01（机器型工件路径修复 + 防再犯 lint）全部 7 条 AC 满足：4 件机器型工件物理回归 .workflow/flow/、artifact-placement lint 升级（敏感 + 白名单豁免）、stage 退出门禁接入（analyst.md + harness-manager.md + stage-role.md）、scaffold_v2 mirror 一致（roles/ + checklists/）、review-checklist 反向抽样条目落地、sug-35（reviewer checklist artifact-placement lint 条目补全）已于本阶段翻转 archived。

chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）全部 6 条 AC 满足：`_is_stage_work_done` executing 分支严格化（changes_dir 缺 → False）、subprocess dogfood 5 用例全绿（真跑 CLI 子进程）、自身周期 dogfood 自证（over-chain 连跳已止，间隔 >400ms）、sug-46（二次实证 over-chain）/ sug-50（gate gap 部署 gap）已翻转 archived、sug-53（usage-log 缺失）partial archived、acceptance.md 部署同步契约硬条目落地、scaffold_v2 evaluation/ mirror 无差异、经验十（三维失配诊断模板）+ 子进程 dogfood 红线均已沉淀。

req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）顶层 5 条 AC 全部满足：sug-audit.md 45 条全判定、roadmap.md 含完整 chg 拆分、用户认可首批（chg-01 + chg-02 已 executing PASS）、池清理路径明确。

部署同步契约 3 条硬验证全通过（pipx 已重装、import 成功、mtime ≥ commit ts）。

**verdict: PASS — 可流转 done。**
