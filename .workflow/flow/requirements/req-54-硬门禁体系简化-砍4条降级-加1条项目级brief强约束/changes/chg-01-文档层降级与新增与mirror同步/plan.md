---
id: chg-01
title: "文档层降级与新增与mirror同步"
parent_req: req-54
operation_type: plan
---

## 1. Scope（精确文件 + 行号）

### 1.1 Live 文件改动 4 个

#### F1：`WORKFLOW.md`（仓库根）

- L3-L8（`## 全局硬门禁` 段，4 条编号行）：
  - 删除 L4「2. 节点任务必须派发给 subagent，主 agent 不直接操作项目文件或代码」
  - 删除 L6「4. `conversation_mode: harness` → 锁定当前节点，不得漂移到其他需求或阶段」
  - 重新编号：原 L3 「1. 未读取 `.workflow/state/runtime.yaml`...」 → 保持「1.」；原 L5「3. 无 `current_requirement`...」 → **保持「3.」编号不重排**（避免影响下游脚本）；
  - 在段尾追加注脚：`> 全局 2 / 全局 4 已 req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束）降级为指导原则；conversation_mode 语义并入状态机文档（.workflow/flow/stages.md / role-loading-protocol.md Step 1 异常处理）。`

#### F2：`.workflow/context/roles/base-role.md`

- L15-L21（`**硬门禁清单**` 总览块）：
  - 删除 L16「- 硬门禁一：工具优先」
  - 删除 L17「- 硬门禁二：操作说明与日志」
  - 在 L21 之后追加：「- 硬门禁八：subagent dispatch briefing 必含项目级加载链提示（req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束））」
  - 在「硬门禁九：subagent 产出独立核查」一行（如本块未列出则补加）保持继续列出；
  - 段尾追加一句备注：`> 原硬门禁一（工具优先）/ 二（操作说明与日志）已 req-54 降级为指导原则；详见下方 ## 工具委派指导原则 / ## 操作日志指导原则 段。`
- L23-L27（`## 硬门禁一：工具优先` 整段）：
  - 改 L23 标题为：`## 工具委派指导原则（原硬门禁一降级，req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束））`
  - 段内正文保留作历史追溯；段尾**新增** 4 行 reasons：
    ```
    ### Reasons（req-54 降级理由）

    - 实战 6 周期实证（bugfix-11 / req-51 / req-52 / bugfix-12 / req-53 / bugfix-13）：常规 read / edit 没有匹配工具，强制委派只是空跑。
    - toolsManager 真正发挥价值仅在「新工具 / 跨 repo / API 集成」三类场景；常规 IO 不需要委派。
    - 降级语义：**新工具 / 跨 repo / API 集成必派；常规 IO 不必**。违反不再阻塞 stage 推进。
    ```
- L29-L31（`## 硬门禁二：操作说明与日志` 整段）：
  - 改 L29 标题为：`## 操作日志指导原则（原硬门禁二降级，req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束））`
  - 段内正文保留作历史追溯；段尾**新增** 4 行 reasons：
    ```
    ### Reasons（req-54 降级理由）

    - 实战 6 周期实证：常规 read / edit 操作的「接下来我要执行 X」+ action-log 追加 → 噪音过多，action-log.md 已超 3000 行不可读。
    - 真正有价值的是「stage 流转 / rollback / CLI 异常 / 派 subagent」等少数事件。
    - 降级语义：**stage 流转 / rollback / CLI 异常 / 派 subagent 必记；常规 read / edit 不记**。违反不再阻塞 stage 推进。
    ```
- L173 之前（`## 硬门禁九：subagent 产出独立核查（上级必做）` 之上）：
  - 新增整段：
    ```
    ## 硬门禁八：subagent dispatch briefing 必含项目级加载链提示（req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束））

    ### 适用范围

    所有派发 subagent 的上级角色（含 harness-manager / technical-director / 各 stage 主控者 / 主 agent / 任意嵌套层级 Level N 派发 Level N+1 时）。

    ### 硬规则

    派发 subagent 时构建的 briefing **必须**显式注入「项目级加载链提示」段，包含以下三块字面内容：

    1. **role-loading-protocol.md Step 7.6 / 7.6.1 引用**（项目级承载路径 + 加载顺序 + 命中后自检要求）；
    2. **boilerplate 一句话**：`subagent 加载完角色文件后，必须按 role-loading-protocol.md Step 7.6 / 7.6.1 加载 artifacts/project/{constraints,experience,tools}/，并在首条输出追加「项目级加载：N 文件命中（路径：artifacts/project/）」自检行（与硬门禁三自我介绍并列）。`；
    3. **scope 提示**：`scope ∈ {constraints, experience-roles, experience-tool, experience-risk, experience-regression, experience-stage}`，由派发者按 subagent 任务类型挑选最相关 scope 显式标注。

    ### 与硬门禁九的关系（事前 brief / 事后核查闭环）

    - **硬门禁八**（事前）：派发时 brief 必含项目级加载链提示，让 subagent 加载链不漏调。
    - **硬门禁九**（事后）：subagent 报告完成后，上级独立核查产出真实生效。
    - 二者首尾相接，让"项目级承载层"（req-51 / req-52 / bugfix-13 立柱）从"靠 LLM 自觉"升级到"brief 强提示 + 核查兜底"。

    ### 违规判定

    - 上级派发的 briefing 中**未含**「项目级加载链」字面段（grep `artifacts/project/` + grep `Step 7.6` 任一缺失） → 上级硬门禁八违反；
    - 与硬门禁九（subagent 产出独立核查）配对成立——上级未 brief + 未核查 = 串联失职。

    ### 沉淀来源

    req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束）；与 req-51（项目级规则-经验-工具支持从制品引入）/ req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ bugfix-13（install时自动创建artifacts-project骨架与索引模板）项目级承载层立柱配套。

    ### 执行示例（参考用）

    - 派发 analyst 时 briefing 必含：「请按 role-loading-protocol.md Step 7.6 加载 `artifacts/project/experience/roles/`（scope=experience-roles）；首条输出追加「项目级加载：N 文件命中」自检行。」
    - 派发 testing 时 briefing 必含：「请按 Step 7.6.1 加载 `artifacts/project/experience/stage/` + `artifacts/project/experience/regression/`（scope=experience-stage / experience-regression）。」
    ```

#### F3：`.workflow/context/roles/harness-manager.md`

- §3.6「派发 Subagent」末尾（约 L295 处）的「**派发协议**」与「**构建 briefing**」之后追加 3.6.2 子条款：
  ```
  #### 3.6.2 按硬门禁八 brief 项目级加载链（req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束））

  按 base-role.md `## 硬门禁八：subagent dispatch briefing 必含项目级加载链提示` 落地：派发任意 subagent 时，briefing 正文必须显式注入下列字面段（不得省略、不得改写）：

  ```
  ## 项目级加载链提示（base-role 硬门禁八）

  请按 .workflow/context/roles/role-loading-protocol.md Step 7.6 / 7.6.1 加载 artifacts/project/{constraints,experience,tools}/（无 branch 维度，跟项目走；scope ∈ {constraints, experience-roles, experience-tool, experience-risk, experience-regression, experience-stage}）。
  本任务相关 scope = {{scope}}（由派发者按 subagent 任务类型挑选）。
  首条输出追加「项目级加载：N 文件命中（路径：artifacts/project/）」自检行（与硬门禁三自我介绍并列）。
  ```

  违反判定：briefing 内 grep 缺失「artifacts/project/」或「Step 7.6」字面 → 硬门禁八违反，reviewer / done 六层回顾兜底拦截。
  ```

#### F4：`.workflow/context/roles/stage-role.md`

- L51-L53（「继承自 base-role 的执行清单」表的硬门禁一 / 二行）：
  - 第 1 行（硬门禁一：工具优先）改文字为：`**工具委派指导原则**（原硬门禁一，req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束）降级）`；行尾标注「（req-54 降级，非硬门禁）」
  - 第 2 行（硬门禁二：操作说明与日志）改文字为：`**操作日志指导原则**（原硬门禁二，req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束）降级）`；行尾标注「（req-54 降级，非硬门禁）」
  - 不动其他清单行。

### 1.2 Mirror 文件改动 4 个（与 live 文件 1:1 对应）

- `src/harness_workflow/assets/scaffold_v2/WORKFLOW.md`（同 F1）
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md`（同 F2）
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md`（同 F3）
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md`（同 F4）

实施时一次完成 live + mirror 同 commit（硬门禁五要求）。

## 2. 实施步骤

1. **Step 1**：实施 F1（WORKFLOW.md live + mirror）— 砍 2 条编号行 + 加注脚。
2. **Step 2**：实施 F2（base-role.md live + mirror）— 4 块改动：
   - 2.1 改硬门禁清单总览（删 2 行 + 加 1 行硬门禁八 + 段尾备注）
   - 2.2 改硬门禁一段标题 + 加 reasons 段
   - 2.3 改硬门禁二段标题 + 加 reasons 段
   - 2.4 在硬门禁九段之前新增硬门禁八整段
3. **Step 3**：实施 F3（harness-manager.md live + mirror）— §3.6 末尾追加 §3.6.2 子条款（含 boilerplate 字面）。
4. **Step 4**：实施 F4（stage-role.md live + mirror）— 清单表 2 行降级注。
5. **Step 5**：自检 4 项：
   - 5.1 `diff -rq <live-4-files> <mirror-4-files>` 4 对全 silent
   - 5.2 grep WORKFLOW.md 全局硬门禁段 ≤ 2 编号行
   - 5.3 grep base-role.md「## 工具委派指导原则」+「## 操作日志指导原则」+「## 硬门禁八」三段标题命中
   - 5.4 grep harness-manager.md §3.6.2 命中
6. **Step 6**：跑 `harness validate --contract all`（exit 0）+ pytest 全 suite（不增 fail 数）。

## 4. 测试用例设计

> regression_scope: full（改动跨 base-role.md / harness-manager.md / stage-role.md 三大角色规约 + WORKFLOW.md 仓库入口；任何下游 subagent 加载链均会被波及，必须 full 回归）
> 波及接口清单（git diff --name-only 自动生成 + 人工补全）：
> - WORKFLOW.md
> - .workflow/context/roles/base-role.md
> - .workflow/context/roles/harness-manager.md
> - .workflow/context/roles/stage-role.md
> - src/harness_workflow/assets/scaffold_v2/WORKFLOW.md
> - src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md
> - src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md
> - src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md
> - 跨模块波及（间接）：所有 stage 角色 .md（继承自 base-role）/ role-loading-protocol.md（Step 7.6 引用闭环）/ harness validate --contract（不破现有契约）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | grep `^[0-9]+\\.` WORKFLOW.md L3-L10 之间 | 命中 ≤ 2 行（仅 1. 与 3.） | AC-01 | P0 |
| TC-02 | grep `## 工具委派指导原则` base-role.md（live + mirror） | 各命中 1 行 | AC-02 | P0 |
| TC-03 | grep `## 操作日志指导原则` base-role.md（live + mirror） | 各命中 1 行 | AC-03 | P0 |
| TC-04 | grep `## 硬门禁八：subagent dispatch briefing 必含项目级加载链提示` base-role.md（live + mirror） | 各命中 1 行 | AC-04 | P0 |
| TC-05 | grep `项目级加载链提示` harness-manager.md §3.6 块（live + mirror） | 各命中 ≥ 1 行（boilerplate 字面段） | AC-05 | P0 |
| TC-06 | grep `工具委派指导原则\\|操作日志指导原则` stage-role.md 「继承自 base-role 的执行清单」表（live + mirror） | 各命中 ≥ 2 行（一 / 二两行降级注均存在） | AC-06 | P0 |
| TC-07 | subprocess `diff -rq` 4 对 live ↔ mirror | returncode == 0（4 对全 silent） | AC-07 | P0 |
| TC-08 | subprocess `harness validate --contract all`（仓库根） | exit 0 + 无新违规 | AC-10（chg-01 范围） | P0 |
| TC-09 | grep `硬门禁一：工具优先\\|硬门禁二：操作说明与日志` base-role.md L15-L25 块（硬门禁清单总览） | 命中 0 行（已移除） | AC-02 / AC-03 | P0 |
| TC-10 | grep `硬门禁八：subagent dispatch briefing` base-role.md L15-L25 块（硬门禁清单总览） | 命中 ≥ 1 行（已新增） | AC-04 | P0 |

（≥ 3 条 / chg 满足）。具体单测文件由 chg-03 落地（test_req54_hard_gate_simplify.py），本 chg 仅在实施时手动跑命令验证；自动化 lint 由 chg-03 引入。

## 5. 验收 lint 命令字面

```bash
# AC-01：WORKFLOW.md 全局硬门禁段 ≤ 2 条
sed -n '3,10p' WORKFLOW.md | grep -cE '^[0-9]+\.'   # 期望 == 2

# AC-02：base-role.md 硬门禁一降级
grep -c '^## 工具委派指导原则' .workflow/context/roles/base-role.md   # 期望 == 1
grep -c '^## 工具委派指导原则' src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md   # 期望 == 1

# AC-03：base-role.md 硬门禁二降级
grep -c '^## 操作日志指导原则' .workflow/context/roles/base-role.md   # 期望 == 1
grep -c '^## 操作日志指导原则' src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md   # 期望 == 1

# AC-04：base-role.md 硬门禁八新增
grep -c '^## 硬门禁八：subagent dispatch briefing' .workflow/context/roles/base-role.md   # 期望 == 1
grep -c '^## 硬门禁八：subagent dispatch briefing' src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md   # 期望 == 1

# AC-05：harness-manager.md §3.6.2 命中
grep -c '#### 3.6.2 按硬门禁八 brief 项目级加载链' .workflow/context/roles/harness-manager.md   # 期望 == 1
grep -c '#### 3.6.2 按硬门禁八 brief 项目级加载链' src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md   # 期望 == 1

# AC-06：stage-role.md 硬门禁清单表降级注
grep -cE '工具委派指导原则|操作日志指导原则' .workflow/context/roles/stage-role.md   # 期望 ≥ 2
grep -cE '工具委派指导原则|操作日志指导原则' src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md   # 期望 ≥ 2

# AC-07：4 mirror diff
diff -q WORKFLOW.md src/harness_workflow/assets/scaffold_v2/WORKFLOW.md
diff -q .workflow/context/roles/base-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md
diff -q .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md
diff -q .workflow/context/roles/stage-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md

# AC-10（chg-01 范围）：harness validate 全契约
python3 -m harness_workflow.cli validate --contract all
```

## 6. scaffold_v2 mirror 同步清单

| Live 文件 | Mirror 路径 | 同步语义 |
|-----------|-----------|---------|
| `WORKFLOW.md` | `src/harness_workflow/assets/scaffold_v2/WORKFLOW.md` | 全文一致 |
| `.workflow/context/roles/base-role.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md` | 全文一致 |
| `.workflow/context/roles/harness-manager.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` | 全文一致 |
| `.workflow/context/roles/stage-role.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md` | 全文一致 |

实施约束：4 对必须**同 commit** 同步落地，违反硬门禁五。
