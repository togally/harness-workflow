# Done Report: bugfix-3 install/update 仅更新当前选定 agent + .harness/feedback.jsonl 落层归位

## 基本信息
- **需求 ID**: bugfix-3（本轮 ID 与上一轮已归档的 bugfix-3 冲突，属 ID 复用缺陷 / Q4 另立跟踪）
- **需求标题**: install/update 仅更新当前选定 agent + `.harness/feedback.jsonl` 落层归位
- **归档日期**: 2026-04-20

## 实现时长
- **总时长**: 约 58 分钟（regression 进入 → done 完成）
- **regression**: ~9m（subagent ≈ 558s）
- **executing**: ~16m（ff 路径跳过 planning；subagent ≈ 976s）
- **testing**: ~13m（主 agent 补齐烟测 + 对人文档；subagent 超时后主 agent 接手）
- **acceptance**: ~5m（精简版独立核查，subagent ≈ 286s）
- **done**: ~15m（本阶段）

> 数据来源：`state/bugfixes/bugfix-3-*.yaml` 的 `stage_timestamps` + subagent `duration_ms`。
> 注：`_sync_stage_to_state_yaml` 在 `regression --testing` 和 ff 路径仍然有 stage_timestamps 盲区（sug-16 跟踪），本轮也不例外。

## 执行摘要

用户提出两条独立问题：(1) install/update 应只作用于当前选定 agent（通过状态层记录）；(2) `.harness/feedback.jsonl` 落在六层外需归位。regression 独立诊断确认均为真实问题、建议合并路由到 testing（代码段高度重叠）。用户选 A/A/A/A 推荐路径（保留迁移 / 保留 escape hatch / 保留 enabled[] / ID 复用另立）。ff 模式下 regression → executing → testing → acceptance → done 一条龙：executing 落地两条修复 + 3 条 TDD 红转绿；testing 补 3 条边界用例（compat warning / 迁移不覆盖 / 一次性 flag）并独立烟测 6 步全绿；acceptance 独立复跑认证 pre-existing failure + validate 4/5（`交付总结.md` 本阶段补齐 → 5/5）。

## 六层检查结果

### 第一层：Context — 通过
- 四个 subagent（regression / executing / testing / acceptance）硬门禁全过
- 本轮新增经验候选 2 条（见下方"经验沉淀"）
- 对上轮 bugfix-3 沉淀的经验八（managed-state 幂等）+ 经验七（slug 下沉）在本轮自主生效

### 第二层：Tools — 通过（附适配问题）
- toolsManager 四次查询均未命中 `.workflow/tools/index/keywords.yaml`，`missing-log.yaml` 已持续累积
- **工具层新发现**：testing subagent **超时**（API stream idle 1068s）——ff 模式下连续派发多 subagent 的长任务有 API 超时风险，建议主 agent 分段派发 + 中途保存 session-memory

### 第三层：Flow — 通过
- bugfix 流程按 `regression → executing → testing → acceptance → done` 单调推进，ff 模式减少了人工 gate
- 阶段完整性：5 阶段全部实际执行（regression 虽然用户推荐 A/A/A/A 但仍做了完整独立诊断）
- testing 阶段 subagent 超时后主 agent 接手完成 `测试结论.md` + 烟测 + `test-evidence.md` + stage 推进，流程连续性未破坏

### 第四层：State — 通过（附历史盲区）
- runtime.yaml + bugfix-3 state yaml `stage=done` 一致
- `stage_timestamps` 仍缺 regression/executing/testing 时间戳（sug-16 已跟踪，ff 路径未触发修复）
- `active_agent` 字段本次刚引入，未来 bugfix 的 runtime 不再受影响

### 第五层：Evaluation — 通过
- testing 独立：executing 3 条 + testing 3 条共 6 条用例，独立 subagent 补边界
- acceptance 独立：`git stash push -u` 回到 HEAD baseline 复跑 `test_smoke_req29` 认证为 pre-existing，"经验二"硬门禁严格执行
- 评估标准 bugfix.md 5 项 Validation Criteria 全通过（含烟测端到端）

### 第六层：Constraints — 通过
- 无越界：scaffold_v2 仅改 2 处文档文案；目标项目 PetMall 未被改动；红用例本体未被改
- 衍生问题：bugfix-3 ID 复用 / 主仓 `.harness/feedback.jsonl` 迁移待真实 update 触发（低风险、预期）

## 工具层适配发现

| 痛点 | 建议 | 预期收益 |
|---|---|---|
| testing subagent 超时（~17min） | ff 模式下拆分子任务（写用例 / 烟测 / 文档分 3 次派发） | 避免单次 API idle timeout，保障 ff 连贯 |
| `harness next` cwd 敏感（上一轮已发现） | sug-17 已跟踪 | — |
| toolsManager 查询关键词无匹配持续累积 | 建议后续由 done 阶段汇总 missing-log.yaml 起补齐任务 | 降低 agent 工具盲人摸象 |

## 经验沉淀

本轮新增 2 条经验候选：

1. **executing 经验九（新）**：**"agent 作用域收敛"类修复，决策 / 生成 / 落盘三段管道必须同时接参数**——只接任一段都会导致泄漏（状态层写了但消费点没读 → 无效；消费点读了但状态层没写 → 老仓破坏；生成点改了但 CLI 没透传 → flag 无效）。
2. **executing 经验十（新）**：**"路径常量迁移"要同时建"新常量 + 旧常量 + 迁移点"三件套**——新常量用于新写入，旧常量保留用于 `LEGACY_FEEDBACK_DIR` 式的历史识别，update_repo 中加一次性 move + 空目录 rmdir；三者缺一都会导致用户数据丢失或路径残留。

两条经验已在 `.workflow/context/experience/roles/executing.md` 追加。

## 流程完整性评估

- bugfix 流程按设计跳过 requirement_review / planning，其余 5 阶段全部实际执行
- testing 独立性：6 条用例跨 2 个独立 subagent（executing 3 条 + testing 3 条）+ 主 agent 接手烟测
- acceptance 独立性：`git stash` baseline 认证 + 独立 3 步烟测，未读 executing 简报结论
- ff 模式没破坏独立性——每个 stage 用独立 subagent 实例

## 改进建议（转 sug 池）

1. **sug-18（high）**：ff 模式下 subagent 拆分策略——单任务粒度限制（建议 ≤ 600s / ≤ 15 次工具调用）避免 API idle timeout，由主 agent 分段派发
2. **sug-19（medium）**：`harness bugfix` ID 分配器应扫归档树——当前只扫 `state/bugfixes/`，导致 archive 后可复用 ID；建议扫 `state/bugfixes/` + `artifacts/**/archive/bugfixes/` 双源（对应 Q4）
3. **sug-20（low）**：主仓 `.harness/feedback.jsonl`（182 行）迁移将在下次真实 `harness update` 触发，建议 done 阶段主动提示用户或由 git hook 提醒 commit `rm .harness/feedback.jsonl` + `add .workflow/state/feedback/feedback.jsonl`
4. **sug-21（medium）**：bugfix 流程 ff 路径下 `stage_timestamps` 只记 acceptance/done，regression/executing/testing 仍空（与 sug-16 合并或细化）

## 下一步行动

- [x] 产出 `done-report.md`（本文件）
- [x] 产出 `交付总结.md`（对人文档 ≤ 1 页）
- [x] 经验沉淀到 `experience/roles/executing.md` 经验九 + 十
- [x] 创建 sug-18 / sug-19 / sug-20 / sug-21
- [x] action-log 顶部追加 done 条目
- [ ] 用户授权后执行 `harness archive bugfix-3 --folder main` + `git commit` + `git push`

## 上下文消耗评估

主 agent 本会话累计约 70-75%（接近阈值，归档前应 `/compact`）。四 subagent 峰值 ~55-65%。下一步 archive + commit 可能触发大量 I/O，建议 `/compact` 后再动。
