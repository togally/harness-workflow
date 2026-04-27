# Change Plan — chg-05（sug 直接处理路径产出 3 段轻量交付总结 + State 校验扩三类任务）

> 所属 req：req-43（交付总结完善）；前置依赖：chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））（task_type="sug" 字段）+ chg-04（bugfix 引入 bugfix-交付总结.md（done 模板精简版））（复用 bugfix 路径模式）；本 chg 是整 req 收口。

## §目标

sug 直接处理路径（`harness suggest --apply` 不转 req / `--archive` / `--reject` 三类）产出 **3 段轻量** `交付总结.md`（OQ-1 default-pick = B 锁定字段：建议是什么 / 处理结果 / 后续），落 `artifacts/{branch}/suggestions/sug-NN-{slug}/交付总结.md`；扩 `repository-layout.md` §2 白名单 + 新增 `artifacts/{branch}/suggestions/` 子树定义；改写 `base-role.md ## done 六层回顾 State 层自检` 把「req 维度」扩到三类任务（req / bugfix / sug，按 task_type 读 entries）；`harness validate --human-docs` 三类同等校验；scaffold mirror 同步 + 整 req dogfood 三类活证收口。AC-01 / AC-05 / AC-07 完整收口。

## §影响文件列表

- `.workflow/flow/repository-layout.md`：§2 对人文档白名单新增 `sug 交付总结.md`（轻量版）类型行；§3 新增「sug 子树落位」子段（与 §3.2 bugfix 对称）：`artifacts/{branch}/suggestions/sug-NN-{slug}/交付总结.md`；§5 命名前缀加一行。
- `src/harness_workflow/workflow_helpers.py::create_suggestion`（line 4134-4185）+ sug `--apply` / `--archive` / `--reject` 处理路径（grep `suggest_apply` / `suggest_archive` 定位）：状态翻转后自动产出 `artifacts/{branch}/suggestions/sug-NN-{slug}/交付总结.md`（轻量 3 段：建议是什么 / 处理结果 / 后续）；sug → req 转化路径**不重复**产出（OQ-1 兜底 = req 的 done 阶段）。
- `src/harness_workflow/validate_human_docs.py`：新增 `_collect_suggestion_items` 函数（与 `_collect_bugfix_items` 对称）；sug 已 applied / archived / rejected 但缺 `交付总结.md` → exit 非 0；sug → req 转化路径**豁免**（status = converted-to-req 不查）。
- `.workflow/context/roles/base-role.md` `## done 六层回顾 State 层自检`（line ~210-220）：把「读取 .workflow/state/sessions/{req-id}/usage-log.yaml」改写为「按 task_type 读 req / bugfix / sug 三类 usage-log.yaml」；State 层校验从 req 维度扩到三类任务。
- `.workflow/context/roles/done.md`：扩说明文字「三类任务级 usage-log entries 数 ≥ 派发次数 - 容差」（done 阶段六层回顾文字补全）。
- `tests/test_suggestion_delivery_summary.py`（**新增**）：覆盖 sug `--apply` 不转 req / `--archive` / `--reject` 三场景产出轻量 3 段交付总结 + 校验阻断 + sug → req 转化路径不重复产出 + State 层三类校验。
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md` + `done.md` + `.workflow/flow/repository-layout.md`：scaffold mirror 同步。

## §实施步骤

1. `repository-layout.md` 改写：§2 白名单加 `sug 交付总结.md`（3 段轻量版） 行；§3 新增 sug 子树落位段；§5 命名前缀加一行。
2. helper 在 sug 状态翻转点（`create_suggestion --apply` / `suggest_archive` / `suggest_reject` 路径）产出 3 段模板（template 内嵌：`## 建议是什么` / `## 处理结果` / `## 后续`）；sug → req 转化路径走分支判断不重复出（检查 frontmatter `status` 是否为 `converted-to-req` 标识）。
3. `validate_human_docs` 新增 `_collect_suggestion_items` 函数（与 bugfix 对称）；sug 已 applied / archived / rejected 但缺 `交付总结.md` → exit 非 0；converted-to-req 路径豁免。
4. 改 `base-role.md ## done 六层回顾 State 层自检` 文字契约：从 req 维度扩到三类任务；按 task_type 读 entries；断言三类 entries 数 ≥ 派发次数 - 容差。
5. `done.md` 扩文字「三类任务级 usage-log entries 数 ≥ 派发次数 - 容差」。
6. 写 pytest `tests/test_suggestion_delivery_summary.py` ≥ 5 case：sug `--apply` 不转 req 直接产出轻量 / sug `--archive` 产出轻量 / sug `--reject` 产出轻量 / sug → req 转化路径**不**产出（豁免） / `validate_human_docs` 缺失阻断。
7. scaffold mirror 同步（base-role.md + done.md + repository-layout.md）。
8. 整 req dogfood：req-43 完成时三类（req-43 自身 + 若有 bugfix-NN + 若有 sug-NN）的交付总结全产出，State 层校验全过；收口 `harness validate --human-docs` exit 0 + `pytest tests/` 全绿。

## §测试用例设计

> regression_scope: targeted（sug 维度新增路径 + State 层契约文字扩展，不动既有 req / bugfix 路径行为）
> 波及接口清单（git diff --name-only 预估 + 人工补全）：
> - `.workflow/flow/repository-layout.md` §2 / §3 / §5
> - `src/harness_workflow/workflow_helpers.py`（create_suggestion + suggest_apply + suggest_archive + suggest_reject 路径）
> - `src/harness_workflow/validate_human_docs.py`（新增 _collect_suggestion_items）
> - `.workflow/context/roles/base-role.md` ## done 六层回顾 State 层自检
> - `.workflow/context/roles/done.md`

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 sug --apply 不转 req 产出轻量 | 调 `harness suggest --apply sug-30`（不转 req 直接处理） | `artifacts/main/suggestions/sug-30-{slug}/交付总结.md` 落盘；含 3 段（建议是什么 / 处理结果 / 后续）；不含其它段 | AC-01（sug 维度） | P0 |
| TC-02 sug --archive 产出轻量 | 调 `harness suggest --archive sug-30` | 同 TC-01 落盘路径 + 内容；frontmatter `status: archived` | AC-01 | P0 |
| TC-03 sug --reject 产出轻量 | 调 `harness suggest --reject sug-30` | 同上落盘；frontmatter `status: rejected` | AC-01 | P1 |
| TC-04 sug → req 转化路径不重复产出 | sug-30 通过 `--apply` 升格转 req-99 | `artifacts/main/suggestions/sug-30-{slug}/` 下**不**产出 `交付总结.md`（由对应 req-99 done 阶段兜底） | AC-01（OQ-1） | P0 |
| TC-05 缺失阻断 archive | sug-30 已 applied / archived，但 artifacts 下无 `交付总结.md` | `harness validate --human-docs` exit 非 0；错误信息含 "sug-30 交付总结.md missing" | AC-07（sug 维度） | P0 |
| TC-06 State 层三类校验 | 跑 base-role.md ## done 六层回顾 State 层自检 in test 模式 | 校验扩三类任务（req / bugfix / sug）；任意一类 entries 数 < 派发次数 - 容差则 fail | AC-05 | P0 |
| TC-07 整 req dogfood | req-43 完成时三类工件全产出 | req-43 自身 `交付总结.md` + 若有 bugfix-NN `bugfix-交付总结.md` + 若有 sug-NN `交付总结.md` 全部落盘；validate --human-docs exit 0 | AC-01 / AC-05 / AC-07 | P0 |
| TC-08 scaffold mirror 同步 | `diff scaffold_v2/.workflow/context/roles/{base-role,done}.md + flow/repository-layout.md` | 三份均 exit 0（无 diff） | AC-04（前置） | P1 |

## §验证方式

- **AC-01（sug 维度 + 完整覆盖）**：TC-01 / TC-02 / TC-03 / TC-04 + TC-07；req-43 完成时三类任务级工作项的交付总结全产出。
- **AC-05（State 层不退化 + 扩三类）**：TC-06 + TC-07；base-role.md 文字契约 + State 层自检脚本扩三类后，本 req 三类校验全过。
- **AC-07（三类一致归档对接）**：TC-05；`harness archive` 对 req / bugfix / sug 三类的对人 folder 处理一致——原位保留 + 机器型迁 `.workflow/flow/archive/`（沿用 req-42（archive 重定义：对人不挪 + 摘要废止） 契约）。
- pytest：`pytest tests/test_suggestion_delivery_summary.py -v` 全绿 + 基线不退化。
- 整 req 收口 dogfood：req-43 自身 done 阶段产出三类活证。

## §回滚方式

`git revert` chg-05（sug 直接处理路径产出 3 段轻量交付总结 + State 校验扩三类任务） 的所有 commit；historic sug（sug-01 ~ sug-29 等）不做回填（与 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）） / req-42（archive 重定义：对人不挪 + 摘要废止） legacy fallback 一致）。

## §scaffold_v2 mirror 同步范围

按 harness-manager.md 硬门禁五（**本 chg mirror 范围最大，三个文件**）：
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md` ↔ `.workflow/context/roles/base-role.md`（diff 应 = 0）
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md` ↔ `.workflow/context/roles/done.md`（diff 应 = 0）
- `src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` ↔ `.workflow/flow/repository-layout.md`（diff 应 = 0）

`workflow_helpers.py` + `validate_human_docs.py` + `tests/` 不在 mirror 范围。

## §契约 7 注意点

- 本 plan.md 首次引用工作项 id 已带 title：req-43（交付总结完善）/ chg-05（sug 直接处理路径产出 3 段轻量交付总结 + State 校验扩三类任务）/ chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））/ chg-04（bugfix 引入 bugfix-交付总结.md（done 模板精简版））/ sug-25（record_subagent_usage 派发链路真实接通）/ req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））/ req-42（archive 重定义：对人不挪 + 摘要废止）。
- 提交信息须形如：`feat: chg-05（sug 直接处理路径产出 3 段轻量交付总结 + State 校验扩三类任务）三类任务收口` —— 带 ≤ 15 字描述（硬门禁六）。
- 整 req 收口涉及多 id 批量列举（req-43 + bugfix-NN + sug-NN）时按 reg-01（对人汇报批量列举 id 缺 title 不可读） / chg-06（硬门禁六 + 契约 7 批量列举子条款补丁） 每条必带 ≤ 15 字描述。
