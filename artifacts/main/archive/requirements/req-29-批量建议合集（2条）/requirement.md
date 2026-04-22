# Requirement

## 1. Title

ff --auto 自主推进 + archive 路径清洗（批量建议合集 2 条）

## 2. Goal

- (1) 为 `harness ff` 新增 `--auto` 模式，让 agent 自主推进 `requirement_review → planning → executing → testing` 全流程，在遇到非确定性开放问题时自主选择当前最优解但打标记，并在进入 `acceptance` 阶段前一次性汇总所有自主决策点，由用户批量确认后再走验收。
- (2) 修复 `resolve_archive_root` 在 legacy `.workflow/flow/archive/` 非空时错误降级到 legacy 路径的 bug，让归档默认优先落到 primary `artifacts/{branch}/archive/`，并提供一次性迁移命令把 legacy 下已有归档（req-26 / req-27 / req-28 / bugfix-3/4/5/6 等）迁到 primary。

## 3. Scope

### 3.1 Included

**A 档（sug-01，产品级 feature）**

- 扩展 CLI：`harness ff --auto [--auto-accept]`，覆盖从 requirement_review 到 testing 的完整流水线推进。
- 自主决策点（下简称"决策点"）的数据契约：时刻、可选项列表、选择项、一句话理由；持久化到 `artifacts/{branch}/requirements/{req-id}-{slug}/decisions-log.md`（建议路径，可在 planning 阶段微调）。
- 决策点汇总 UX：进入 acceptance 之前 CLI 打印全部决策点，用户一次性批量 ack（默认交互，`--auto-accept` 跳过交互）。
- stage-role 契约扩展：在 stage-role.md 增补"决策点记录格式"子契约（作为 chg-05 契约的增量）。

**B 档（sug-08，CLI bug + 数据迁移）**

- 修改 `resolve_archive_root`（`src/harness_workflow/workflow_helpers.py:4280` 附近）的判据：默认优先返回 primary `artifacts/{branch}/archive/`，只有显式指定 legacy 时才使用 legacy。
- 新增/扩展 `harness migrate --archive`（或等价 `harness migrate archive` 子命令），把 legacy 下已有归档一次性迁移到 primary，迁移后 `harness status` / `harness archive` 不再输出 "using legacy archive path" 警告。
- 迁移目标范围：legacy 下现存的 req-26 / req-27 / req-28 / bugfix-3 / bugfix-4 / bugfix-5 / bugfix-6 等归档产物。

### 3.2 Excluded

- 不做"agent 自主决策"的完整 AI 规划引擎——仅定义"打标记 + 汇总 + 验收前一次性确认"的工程框架；实际选项比较和选择逻辑由 subagent 的 LLM 判断承担。
- 不做 `pip install -U harness-workflow` 等 Python 包发布 / 版本发布流程。
- 不回溯修改已归档的 req-26 / req-27 / req-28 / bugfix-3/4/5/6 的文档内容，仅做物理路径迁移。
- 不在本需求内扩展 `--auto` 到 acceptance 阶段之后（acceptance 必须停下等人）。
- 不在本需求内定义"允许 / 禁止自主决策的完整问题清单"——仅在 stage-role 中给出最小约束框架，详细清单列入后续 sug。

## 4. Acceptance Criteria

- **AC-01（sug-01，CLI 主路径）**：`harness ff --auto` 在 `current_requirement` 处于 `requirement_review / planning / plan_review / ready_for_execution / executing / testing` 任一阶段时都能正确接续推进，并在进入 `acceptance` 阶段之**前**停下；进入 acceptance 之前 CLI 打印一次决策点汇总，用户一次性批量确认（支持 `--auto-accept` 开关跳过交互）。
- **AC-02（sug-01，决策点数据契约）**：agent 在 `--auto` 模式下每次做出非确定性选择时，必须写入一条决策点记录，字段至少包含：决策时刻（ISO 时间戳）、可选项列表、实际选择项、一句话决策理由；存储路径建议 `artifacts/{branch}/requirements/{req-id}-{slug}/decisions-log.md`（由 planning 拍板固化），格式约束写入 `stage-role.md`。
- **AC-03（sug-08，判据修复）**：`resolve_archive_root` 默认优先返回 primary `artifacts/{branch}/archive/`；只有在显式传入 legacy 指示（例如 `--legacy` flag 或环境变量）时才返回 legacy 路径。单元测试覆盖"legacy 非空时新归档仍落 primary"这一 happy path。
- **AC-04（sug-08，一次性迁移）**：`harness migrate --archive`（或 `harness migrate archive`）能把 legacy `.workflow/flow/archive/` 下已有的归档产物（含 req-26 / req-27 / req-28 / bugfix-3/4/5/6 等）迁到 primary `artifacts/{branch}/archive/`，迁移后执行 `harness status` / `harness archive` 不再出现 "using legacy archive path" 警告。

## 5. 决策边界与 --auto-accept 规约（sug-01 定稿）

### 5.1 必须阻塞等人的决策类别（agent 不得自主）

- **破坏性 IO**：`rm -rf`、`DROP TABLE`、物理删除文件/目录
- **不可逆 git**：`--force` push、`reset --hard`、amend 已推 commit
- **跨 req / 跨 change 修改**：越界改别的需求或变更的交付产物
- **archive 物理删除 / 清仓**：删除或覆盖已归档内容
- **涉及凭证 / 网络的写入**：token、secret、远程服务变更
- **敏感配置修改**：`.claude/settings.json`、`.env`、平台/agent 配置文件
- **依赖变更**：`package.json` / `pyproject.toml` / `Cargo.toml` 等的 dependencies 增删
- **数据模型 / schema 变更**：DB migration、collection 结构重定义

以上类别触发时，`ff --auto` 必须停下等人，打印阻塞原因；不得记入 decisions-log 后继续。

### 5.2 decisions-log 双轨约定

- **agent 运行时记录**：`.workflow/flow/requirements/{req-id}/decisions-log.md` —— 每次自主决策一行追加，含时间戳、stage、决策点描述、可选项、选择、理由
- **用户验收汇总**：`artifacts/{branch}/requirements/{req-id}-{slug}/决策汇总.md` —— 进入 acceptance 前一次性产出，按风险等级分组（low / medium / high），是"对人文档"双轨输出的一部分

### 5.3 --auto-accept 三档语义

| flag | 语义 |
|------|------|
| （未传） | 每个决策点都交互确认（默认） |
| `--auto-accept low` | 低风险自动 ack，中高仍交互（推荐默认） |
| `--auto-accept all` | 全部自动 ack（危险，仅限自动化脚本） |

决策风险等级由 agent 在打决策点时显式标记（low / medium / high）。规则：
- **high**：触及 5.1 阻塞类别的边缘/预备操作；必须 high
- **medium**：跨文件 / 多步骤 / 语义偏差可能的选择
- **low**：命名微调 / 格式选择 / 等价替代方案

## 6. 风险

- **R1（sug-01）**：`--auto` 模式下"允许 / 禁止自主决策"的边界不清会导致 agent 在应该停下等人的场景（例如涉及破坏性 IO、需要额外权限、跨需求决策）擅自选择。planning 阶段必须明确最小阻塞规则集（例如：涉及 `git push --force` / 跨 req 修改 / `--archive` 物理删除等必须阻塞等人），后续再通过 sug 扩展完整清单。
- **R2（sug-08）**：legacy → primary 迁移涉及实际移动历史归档文件，迁移命令必须是**幂等**的，并在迁移前自动做备份或要求用户显式确认；迁移失败时可回滚，不得留下"两边都有"的脏状态。

## 7. Split Rules

- sug-01 建议拆 2–3 个 change（例如：决策点数据契约 + stage-role 规约 / CLI `--auto` 主循环 / 汇总 UX + 测试）。
- sug-08 建议合并到 1–2 个 change（判据修复 + 迁移命令，或合并为一个 change 两个 step）。
- 每个 change 覆盖一个独立可交付单元；需求完成时填充 `completion.md`，记录项目启动校验通过。

## 合并建议清单

- sug-01: ff模式支持 --auto命令全程跑完，碰到问题自行选择最优解。在验收前给出整理的执行问题点选择，让用户验收
- sug-08: resolve_archive_root 在 legacy .workflow/flow/archive/ 非空时降级返回 legacy，导致 chg-03 对 bugfix 分流设计的 artifacts/{branch}/archive/bugfixes/ 目标路径失效。
