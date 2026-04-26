# Stage 定义与流转规则

## 完整流转图

```
requirement_review          ← 第三层管辖
      ↓ harness next
   planning                 ← 第三层管辖
      ↓ harness next
   executing                ← 第三层管辖
      ↓ harness next
   testing                  ← 第五层管辖（evaluation/testing.md）
      ↓ harness next
  acceptance                ← 第五层管辖（evaluation/acceptance.md）
      ↓ harness next
    done

任意阶段 ──harness regression──→ regression ← 第五层管辖
                                      ↓
                         ┌────────────┴────────────┐
                   需求/设计问题              实现/测试问题
                         ↓                          ↓
               requirement_review               testing
```

---

## Bugfix 快速流转图

针对已知缺陷的快速修复流程（`bugfix-*` 需求）：

```
regression                  ← 第五层管辖
      ↓ harness next
   executing                ← 第三层管辖
      ↓ harness next
   testing                  ← 第五层管辖
      ↓ harness next
  acceptance                ← 第五层管辖
      ↓ harness next
    done
```

- **进入条件**：`harness bugfix "<title>"` 创建 bugfix 目录
- **跳过阶段**：`requirement_review`、`planning`
- **模式识别**：`current_requirement` 以 `bugfix-` 开头时启用本流程
- **产物**：`.workflow/flow/bugfixes/{bugfix-id}/bugfix.md` 替代 `requirement.md` + `change.md` + `plan.md`

---

## 第三层 Stage 定义

> 本文件 stage 与角色对应关系以 `.workflow/context/role-model-map.yaml` 为准；本文件为反向引用展示。（bugfix-5（同角色跨 stage 自动续跑硬门禁））

### requirement_review
- **角色**：需求分析师（`context/roles/requirement-review.md`）
- **覆盖角色**：analyst（以 `.workflow/context/role-model-map.yaml` 为准）
- **出口决策**：auto（以 `.workflow/context/role-model-map.yaml` stage_policies 为准）（bugfix-5（同角色跨 stage 自动续跑硬门禁）修复点 6）
- **进入条件**：`harness requirement "<title>"` 创建需求
- **退出条件**：requirement.md 包含背景、目标、范围、验收标准，用户确认
- **必须产出**：`.workflow/flow/requirements/{req-id}/requirement.md`
- **下一步**：`harness next` → `planning`

### planning
- **角色**：架构师（`context/roles/planning.md`）
- **覆盖角色**：analyst（以 `.workflow/context/role-model-map.yaml` 为准）
- **出口决策**：user（以 `.workflow/context/role-model-map.yaml` stage_policies 为准）（bugfix-5（同角色跨 stage 自动续跑硬门禁）修复点 6）
- **进入条件**：requirement_review 退出条件满足
- **退出条件**：所有变更有 change.md + plan.md，执行顺序明确，用户确认
- **必须产出**：每个变更的 `change.md` + `plan.md`
- **下一步**：`harness next` → `executing`

### executing
- **角色**：开发者（`context/roles/executing.md`）
- **覆盖角色**：executing（以 `.workflow/context/role-model-map.yaml` 为准）
- **出口决策**：auto（以 `.workflow/context/role-model-map.yaml` stage_policies 为准）（bugfix-5（同角色跨 stage 自动续跑硬门禁）修复点 6）
- **进入条件**：
  - 标准流程：planning 退出条件满足
  - bugfix 流程：regression 诊断完成，修复方案已写入 `bugfix.md`
- **退出条件**：所有变更实现完成，内部测试通过，session-memory 全部 ✅
- **必须产出**：代码/文件变更 + session-memory 执行日志
- **下一步**：`harness next` → `testing`（进入第五层）

### regression
- **角色**：诊断师（`context/roles/regression.md`）
- **覆盖角色**：regression（以 `.workflow/context/role-model-map.yaml` 为准）
- **出口决策**：verdict（以 `.workflow/context/role-model-map.yaml` stage_policies 为准）（bugfix-5（同角色跨 stage 自动续跑硬门禁）修复点 6）
- **进入条件**：
  - 标准流程：任意阶段执行 `harness regression <issue>`
  - bugfix 流程：`harness bugfix "<title>"` 创建 bugfix 目录后直接进入
- **退出条件**：
  - `regression/diagnosis.md` 已产出
  - 根因已明确，路由方向已确定（真实问题 / 误判）
  - bugfix 流程下：修复方案已写入 `bugfix.md#修复方案`
- **必须产出**：`regression/diagnosis.md`（含 `required-inputs.md` 如需人工输入）
- **下一步**：
  - 需求/设计问题 → `requirement_review`
  - 实现/测试问题 → `testing`
  - 误判 → 回到触发前的 stage
  - bugfix 流程 → `executing`

### done
- **角色**：主 agent（非 subagent）
- **覆盖角色**：done（以 `.workflow/context/role-model-map.yaml` 为准）
- **出口决策**：terminal（以 `.workflow/context/role-model-map.yaml` stage_policies 为准）（bugfix-5（同角色跨 stage 自动续跑硬门禁）修复点 6）
- **进入条件**：acceptance 通过（第五层判定）
- **动作**：
  - 读取 `context/roles/done.md` 作为检查清单
  - 执行六层回顾检查（Context、Tools、Flow、State、Evaluation、Constraints）
  - 输出回顾报告到 `session-memory.md` 的 `## done 阶段回顾报告` 区块
- **归档命令**：`harness archive "<req-id>" [--version "<v>"]`

---

## 需求目录规范

### 标准需求（req-*）

```
.workflow/flow/requirements/
└── req-{两位数字}-{title}/
    ├── requirement.md
    └── changes/
        └── chg-{两位数字}-{title}/
            ├── change.md
            ├── plan.md
            └── regression/
                ├── diagnosis.md
                └── required-inputs.md
```

### Bugfix 需求（bugfix-*）

```
.workflow/flow/bugfixes/
└── bugfix-{数字}-{title}/
    ├── bugfix.md
    ├── session-memory.md
    ├── test-evidence.md
    └── regression/
        ├── diagnosis.md
        └── required-inputs.md
```

## 归档目录规范

```
.workflow/flow/archive/
└── {folder}/              # 可选，归档时通过 --folder 指定；不指定则直接放 archive/ 下
    └── req-{id}-{title}/  # 结构与活跃需求一致
```

归档规则：
- 只有 `done` 状态的需求可以归档
- 从 `.workflow/flow/requirements/` 移动到 `.workflow/flow/archive/[{folder}/]`
- 目标 folder 不存在则新建，已存在则合并写入（不报冲突）
- `state/requirements/{req-id}.yaml` 标记为 `archived`
- `state/sessions/{req-id}/` 保留不删（历史可查）

---

## harness ff（fast-forward）

`harness ff` 用于从当前 stage 启动自动推进模式，AI 自主完成后续阶段的工作，无需用户逐 stage 确认。

### 启动条件

- **允许启动的 stage**：`requirement_review`、`planning`
- **启动方式**：用户在允许 stage 执行 `harness ff`
- **启动后标记**：`runtime.yaml` 设置 `ff_mode: true`

### 自动推进规则

ff 模式下，各 stage 的完成判定由 AI 自主执行，满足退出条件后自动进入下一 stage：

| Stage | 自动完成判定条件 |
|-------|-----------------|
| `requirement_review` | `requirement.md` 包含背景、目标、范围、验收标准 |
| `planning` | 所有变更都有 `change.md` + `plan.md`，执行顺序明确 |
| `executing` | 所有 `plan.md` 步骤已完成，内部测试通过，session-memory 全部 ✅ |
| `testing` | 测试运行通过，测试报告已产出 |
| `acceptance` | 验收标准已核对通过 |
| `done` | 六层回顾完成，回顾报告已写入 `session-memory.md` |

推进逻辑：
1. 当前 stage 的 subagent 任务完成
2. 主 agent 检查退出条件是否满足
3. 满足则将当前 stage 结果保存到 `session-memory.md`
4. 自动更新 `runtime.yaml` 到下一 stage，并将原 stage 追加到 `ff_stage_history`
5. 不需要用户手动输入 `harness next`

### ff 模式下 session-memory 规范

每个 stage 结束时，必须更新该变更对应的 `session-memory.md`，包含：
- **stage 结果摘要**：完成了什么、产出了哪些文件
- **关键决策**：AI 在 ff 模式下做出的重要选择及其理由
- **遇到的问题**：任何阻塞、风险或需要后续关注的事项
- **下一步任务**：下一 stage 的目标和注意事项

主 agent 在自动推进前，应确认 `session-memory.md` 已保存，确保上下文维护（如 `/compact` 或新开 agent）后可恢复。

### 暂停与退出机制

**暂停 ff**：
- 当遇到 AI 自主决策边界之外的问题时，主 agent 将 `ff_mode` 设为 `paused`
- `paused` 状态下，保留 `current_requirement` 和当前 stage，等待用户回复
- 用户回复后，若问题已解决，可恢复 `ff_mode: true` 继续自动推进

**退出 ff**：
- 用户说 "停止 ff"、"退出 ff" 或等效指令时，主 agent 将 `ff_mode` 设为 `false`
- 退出后转为正常模式，后续 stage 推进需要用户手动执行 `harness next`
- `ff_stage_history` 保留作为审计记录

### AI 自主决策边界

**AI 可以自行决定**：
- 文档内容的补充和细化
- 拆分规则的细化（在需求范围内）
- 实现方案的选择（在 plan 范围内）
- 测试策略和用例设计
- 代码级的小范围调整

**AI 必须暂停 ff 模式并向用户求援**：
- 涉及外部系统凭据、密钥或权限
- 可能破坏生产环境或导致数据丢失
- 用户意图不明确或与已有需求冲突
- 超出 plan 范围的大架构改动
- regression 诊断后仍无法自动恢复
- 连续遇到平台级错误（如 API Error 400）且会话恢复机制失效

### 失败处理路径

**正常终止**：到达 `done` 后，可选择自动执行 `harness archive`。

**异常终止**：
1. **遇到可自动恢复的 regression**：AI 尝试自动诊断和修复一次，成功则继续 ff
2. **遇到无法自主决策的问题**：主 agent 将 `ff_mode` 标记为 `paused`，向用户报告上下文和问题，等待人工回复后继续
3. **用户可随时退出 ff**：用户说 "停止 ff" 或等效指令时，主 agent 清除 `ff_mode`，转为正常模式
4. **平台级错误导致会话损坏**：参照 `constraints/recovery.md` 中的"平台级错误/会话损坏"恢复条目处理

---

## 命令与 Stage 对应关系

| 命令 | 作用 | 适用 Stage |
|------|------|-----------|
| `harness requirement` | 创建需求，进入 requirement_review | 任意 |
| `harness change` | 创建变更文档（change.md） | planning |
| `harness next` | 推进到下一 stage | 任意（满足退出条件） |
| `harness ff` | 启动 fast-forward 模式，AI 自动推进到 done/archive | requirement_review / planning |
| `harness archive <req-id> [--folder <name>]` | 归档已完成需求，可选指定目标文件夹 | done |
| `harness regression` | 进入 regression | 任意 |

---

## 工具命令补充说明

### `harness update`
- 除刷新 managed 文档外，还会自动检测并迁移旧版 `state/` 文件格式
- `runtime.yaml` 会自动补齐缺失的新字段（如 `ff_mode`、`ff_stage_history`）
- `requirements/*.yaml` 会自动将旧字段（`req_id`→`id`、`created`→`created_at` 等）升级到新格式，并生成 `.bak` 备份

### `harness archive`
- 归档完成后会自动清理 `flow/requirements/` 中对应的残留目录
- 归档产物包括需求文档、变更文档、状态文件和会话记录

---

## 需求实现时长记录

### 计算口径

- **总时长**：从需求进入 `requirement_review` 阶段开始，到 `done` 阶段结束为止的时间跨度
- **分阶段时长**（可选）：各 stage 的停留时间，由相邻 stage 时间戳之差计算得出

### 数据来源

时长数据统一存储在 `state/requirements/{req-id}.yaml` 中：

```yaml
id: req-XX
title: xxx
status: requirement_review | planning | executing | testing | acceptance | done | archived
created_at: "YYYY-MM-DD"
started_at: "YYYY-MM-DDTHH:MM:SS"      # requirement_review 阶段开始时间
completed_at: "YYYY-MM-DDTHH:MM:SS"    # done 阶段完成时间
stage_timestamps:
  requirement_review: "YYYY-MM-DDTHH:MM:SS"
  planning: "YYYY-MM-DDTHH:MM:SS"
  executing: "YYYY-MM-DDTHH:MM:SS"
  testing: "YYYY-MM-DDTHH:MM:SS"
  acceptance: "YYYY-MM-DDTHH:MM:SS"
  done: "YYYY-MM-DDTHH:MM:SS"
```

**采集规则**：
1. `harness requirement` 创建需求时，同步设置 `started_at`（与 `created_at` 等效或更精确）
2. 每次 `harness next` 推进到新 stage 时，记录当前 stage 的时间戳到 `stage_timestamps`
3. `done` 阶段完成时，设置 `completed_at`

### 降级策略

- `started_at` 缺失 → 使用 `created_at` 降级
- `completed_at` 缺失 → 使用报告生成时的当前时间
- 某 stage 时间戳缺失 → 该阶段时长显示 "N/A"，总时长仍尽可能计算

### 展示位置

时长记录展示在 `done-report.md` 头部，格式由 `context/roles/done.md` 定义。

<!-- Legacy (req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界））/ chg-01（S-A 合并 changes_review + plan_review → 单一 planning sub-stage）)：
  - 旧 stage 序列曾为 requirement_review → changes_review → plan_review → ready_for_execution → executing → testing → acceptance → done；
  - 自 req-31 chg-01 合并后，changes_review / plan_review 统一为 planning；归档 req-02..req-30 的 stage_timestamps 保留历史字段不迁移。
-->
