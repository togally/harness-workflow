# Session Memory — req-26 uav-split

## 测试执行记录

### 测试命令
- `python3 -m unittest discover tests -v`（全量）
- `python3 -m unittest tests.test_regression_helpers tests.test_rename_helpers tests.test_next_writeback tests.test_archive_path tests.test_smoke_req26`（req-26 新增）
- `python3 -m unittest tests.test_req26_independent`（独立补测）

### 结果摘要
- 全量：86 / pass 47 / fail 3 / error 3 / skip 36。
- req-26 新增 23 条 + 独立补测 5 条：**全部通过**。
- 3 failures（`test_install_writes_three_platform_hard_gate_entrypoints` / `test_installed_skill_uses_global_harness_commands` / `test_bugfix_creates_workspace_and_enters_regression`）+ 3 errors（2 条 `test_update_check_and_apply_*`、1 条 `test_cycle_detection`）经 `git checkout 3f94c30^` 回滚核验，**均为 req-26 提交前的预存基线**，不阻塞。

### 补测文件
- `tests/test_req26_independent.py`（5 用例）独立视角覆盖 AC-06：
  1. `HumanDocFilenameTest`：7 份中文文件名字面出现于对应 stage.md；
  2. `HumanDocFilenameTest`：7 份路径前缀声明正确；
  3. `HumanDocExitConditionHardGateTest`：7 个 stage 的"退出条件"清单含硬门禁 checkbox；
  4. `TestingMinimalFieldTemplateTest`：testing.md 最小字段模板四字段顺序不得变更；
  5. `StageRoleContractReferencesRolesTest`：stage-role.md 契约命名表列齐 7 份文件名。

### 对人文档
- 路径：`artifacts/main/requirements/req-26-uav-split/测试结论.md`（req 级）。

### 对 acceptance 阶段的交接要点
1. 重点核对 6 个 change 分别是否已按契约产出对人文档（`需求摘要.md` / `变更简报.md` / `实施说明.md` / `测试结论.md` / `验收摘要.md` / `交付总结.md`；`回归简报.md` 视本次 smoke 是否触发 regression）；若 agent 未实际写盘，需补落盘。
2. 抽查 `artifacts/main/requirements/req-26-uav-split/` 与各 `changes/chg-XX-*/` 目录，确认无文件被搬离 `.workflow/flow/`（契约 1 反例核对）。
3. 确认 `artifacts/bugfixes/bugfix-2/`、`artifacts/main/bugfixes/bugfix-{3,4,5}/` 下历史脏数据未被触碰（契约 5 反例核对）。
4. 基线 failure（install/update/bugfix CLI 模板漂移 + `harness_workflow.core` 模块缺失）建议单独开 bugfix，不应阻塞 req-26 验收。

## 验收执行记录

### 核查动作
- 读取 `requirement.md`（AC-01~AC-07）与 `测试结论.md`，对 7 条 AC 逐条判定。
- `ls artifacts/main/requirements/req-26-uav-split/` + 各 `changes/chg-0{1..6}-*/`：统计对人文档落盘现状。
- `git show --stat 3f94c30`：核对 Excluded 反例未触碰 `.workflow/flow/`（除 sug-01 合规删除）、`artifacts/bugfixes/bugfix-2/`、`artifacts/main/bugfixes/bugfix-{3,4,5}/`、`.workflow/flow/archive/`。

### AC 核查结果（摘要）
- AC-01 ~ AC-05 / AC-07：**通过**。
- AC-06：**条件通过**——机制侧静态契约齐全；本需求 runtime 只产出 `测试结论.md` + 6 份 `实施说明.md` + `验收摘要.md`，`需求摘要.md` / 6 份 `变更简报.md` 按 chg-05 SOP"后续阶段生效"约定不回溯补产。

### 对人文档落盘统计
- 已产出：6 份 `实施说明.md`（chg-01~06） + `测试结论.md` + `验收摘要.md` = **8 份**。
- 按设计不在本需求内产出：`需求摘要.md` + 6 份 `变更简报.md` + `交付总结.md`（done 阶段产出）。

### 整体判定
- **有条件通过**。建议主 agent：
  1. 直接推进到 done。
  2. 新开 **bugfix-6** 承接 3 fail + 3 error 预存基线。
  3. 下一需求作为对人文档完整示范起点。

### 对人文档
- 路径：`artifacts/main/requirements/req-26-uav-split/验收摘要.md`（req 级，字段齐全、≤600 字）。

## Done 阶段记录

### 六层回顾结论（每层一行）

- **L1 需求层**：Goal/Scope/Excluded/AC 覆盖完整，6 条 sug 全部映射入 AC-01~AC-07，零遗漏。
- **L2 变更层**：6 个 change 拆分合理——AC-01+AC-04 合并 regression 命令簇、独立命令（rename/next/archive）独立成 change、纯文档 AC-06 单独成 chg-05、AC-07 smoke 压轴；planning 阶段主动捕获 `harness change` 目录命名 + 模板质量 2 条潜在问题并以 B/C 方案并入 chg-02 / chg-05，不新增 change 不新增 AC。
- **L3 实施层**：共享 `slugify` / `sanitize_artifact_dirname` util 降低重复实现风险；chg-05 纯文档不改 CLI 代码隔离风险；chg-06 smoke 在 tempdir 走完整生命周期覆盖端到端。
- **L4 测试层**：req-26 新增 28 条全过，预存基线 3 fail + 3 error 经 `git checkout 3f94c30^` 回滚核验与本需求无关；AC-06 降级为静态契约 + 运行时对人文档实际落盘（8 份）间接证明；testing 工程师主动产出独立补测 5 条从第三方视角核查 AC-06 字段顺序。
- **L5 验收层**：AC-01~AC-05/07 硬通过，AC-06 有条件通过——未达项以 sug-08（bugfix-6 预存基线）+ sug-11（下一需求首次完整示范）+ sug-09（AC-06 运行时闭环）承接。
- **L6 流程层**：本周期暴露 3 类问题——`harness change` 历史模板积弊（已本需求修复）+ 对人文档 SOP 执行起点问题（chg-05 豁免回溯，交 sug-11 承接）+ 预存基线长期未修（交 sug-08 承接）。

### 转 suggest 池条目

- **sug-08**（中）：新开 bugfix-6 修复 3 fail + 3 error 预存基线
- **sug-09**（中）：补充 AC-06 对人文档"agent 运行时真实落盘"验证
- **sug-10**（中低）：下游已安装仓库的 `harness change` 模板刷新策略
- **sug-11**（高）：下一需求作为对人文档产出链首次完整示范

编号续 archived 中最大 sug-07 之后。

### 经验文件更新

- `.workflow/context/experience/roles/testing.md`：新增"经验五：AC 可降级为静态契约，但必须有运行时闭环路径"（来源 req-26）。
- 其他 placeholder 经验文件（planning / acceptance / regression / executing / requirement-review）本轮不强制初始化，等 sug-11 下一需求首次完整示范产出更有价值的样例后再一次性沉淀。

### 对人文档 / 报告路径

- `done-report.md`：`.workflow/state/sessions/req-26/done-report.md`（与 req-02~11 非归档期的存放惯例一致）。
- `交付总结.md`：`artifacts/main/requirements/req-26-uav-split/交付总结.md`（契约 2 路径同构 req 级）。

### 对 archive 的建议

- 建议**不立即** `harness archive`。先等用户确认以下两件事：
  1. sug-08~11 四条 suggest 是否需要补充或调整优先级；
  2. 是否现在开 bugfix-6（sug-08）以便归档前先处理掉测试基线噪音。
- 若用户确认 suggest 池满意且同意把 bugfix-6 留到归档后单独承接，则可直接执行 `harness archive "req-26"`。本需求已满足 done 阶段所有退出条件。
