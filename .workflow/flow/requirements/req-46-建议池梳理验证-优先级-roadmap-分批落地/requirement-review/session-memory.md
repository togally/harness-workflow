# Session Memory — req-46 requirement_review

## 1. Current Goal

清池 + 排序 + 分批落地：
- 验证 .workflow/flow/suggestions/ 下 45 条 sug 现状（live / stale / dup / applied-out）
- 主题簇归类（已识别 10 簇）
- 优先级初评 + 处理建议
- 产出 sug-audit.md 作为后续 planning stage 拆 chg 的依据

## 2. Context Chain

- Level 0：主 agent（harness-manager / opus，harness requirement 派发入口）
- Level 1：analyst-L1（opus，requirement_review + planning 续跑）

## 3. Completed Tasks

- [x] 完整加载角色协议（runtime.yaml / base-role.md / stage-role.md / analyst.md / role-loading-protocol.md / role-model-map.yaml）
- [x] 模型一致性自检：opus = roles.analyst.model（OK）
- [x] 列举 .workflow/flow/suggestions/ 下 45 个 .md（含 sug-25 applied 在池 + sug-46 archive 也在池）
- [x] 逐条读 45 个 sug.md 内容
- [x] grep 当前 src/harness_workflow/workflow_helpers.py 关键函数核实代码现状（_is_stage_work_done / record_subagent_usage / apply_suggestion / _append_sug_body_to_req_md）
- [x] 比对 git log 最近 20 commit + artifacts/main/archive/ + .workflow/flow/archive/ 归档列表
- [x] 产出 sug-audit.md（45 条逐条判定 + 主题簇归类 + 优先级评估 + 默认决策记录）
- [x] 落地 requirement.md §2-§5（见 §4 Results 段链接）

## 4. Results

### 4.1 sug-audit.md（独立文件）

落位：`artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/requirement-review/sug-audit.md`

关键产出：
- 45 条 sug 状态分布：live=32 / applied-out=6 / stale=4 / dup-of=2（与 stale 部分重叠）
- 10 个主题簇定义（C-1 over-chain / C-2 usage-log runtime / C-3 apply-rename CLI / C-4 scaffold mirror / C-5 契约 lint / C-6 archive 路径 / C-7 testing-dogfood / C-8 install-update 体验 / C-9 runtime 同步 / C-10 杂项）
- 6 条出池建议：sug-09 / sug-12 / sug-17 / sug-32 / sug-40 stale → delete；sug-25 / sug-44 / sug-45 / sug-46 / sug-49 / sug-50 applied-out → archive
- 2 条 P0 升级建议：sug-39（usage-log runtime 接通）+ sug-51（testing 红线 + safer dogfood）

### 4.2 requirement.md（机器型工件）

落位：`.workflow/flow/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/requirement.md`

§2~§5 全填：Goal（清池 + 排序 + 分批落地）/ Scope（sug-08~sug-53 + 排除项）/ AC（5 条）/ Split Rules（按 10 主题簇切 chg）。

### 4.3 主题簇 → chg 拟定映射（详见 planning/roadmap.md）

| chg 编号 | 主题 | 主线 sug | P 评级 |
|---------|-----|---------|-------|
| chg-1 | over-chain dogfood 复验 + 兜底加固 | sug-38 | P0 |
| chg-2 | usage-log runtime 强制接通（含口径修正 + token 落地）| sug-39 / sug-41 / sug-42 | P0 |
| chg-3 | apply / rename / suggest CLI 顺修 | sug-08 / sug-19 / sug-48 | P2 |
| chg-4 | scaffold_v2 mirror 漂移批量修复 + 自动同步告警 | sug-15 / sug-21 | P1 |
| chg-5 | 契约硬门禁 lint 套件（id+title / 路径 / 派发话术 / reviewer 抽样）| sug-11 / sug-22 / sug-23 / sug-27 / sug-33 / sug-35 / sug-47 | P1 |
| chg-6 | archive 路径关注点分离 + 双源整合 + bugfix 工件 migrate | sug-29 / sug-30 / sug-34 / sug-36 | P1 |
| chg-7 | testing 红线 + safer dogfood 协议 + commit revert dry-run | sug-31 / sug-51 / sug-52 | P0 |
| chg-8 | install / update / next CLI 体验顺修 | sug-10 / sug-14 / sug-20 / sug-24 | P2 |
| chg-9 | runtime / enter / archive / next 状态同步统一 | sug-13 / sug-26 / sug-37 | P1 |
| chg-10 | 杂项小修（migrate Path str + 池清理 + Level-2 派发硬门禁等）| sug-08 / sug-14 / sug-16 / sug-18 / sug-28 | P3 |

> 完整 chg 拆分（依赖图 / 工作量 / 验收点）见 planning/roadmap.md。

### 4.4 默认决策清单（default-pick）

D-1 ~ D-10 共 10 条决策按默认推进，详见 sug-audit.md `## 默认决策记录` 段。摘要：
- D-1（sug-09/-12 dup-of sug-38）= A（stale）
- D-2（sug-25 出池）= B（archive）
- D-3（sug-50 复验后判定）= C（保留 live 直至 dogfood 复验）
- D-4（sug-38 主线保留 live）= B（保留至 chg-1 dogfood 复验）
- D-5（sug-17/-32/-40 stale）= A（建议 delete）
- D-6（chg 粒度 5~10 个簇）= A
- D-7（优先级 P0→P1→P2 排）= A
- D-8（chg-2 最前置）= A（usage-log 是数据底座）
- D-9（sug-audit.md 独立文件）= B
- D-10（不创建 chg 工件等用户拍板）= B

### 4.5 待处理捕获问题

- sug-46 双份（live + archive 副本同存）：归 chg-3 顺修
- sug 优先级 frontmatter 与 audit 新评估不一致：default-pick 不回填，仅 roadmap 记新优先级，避免 sug 文件 churn
- bugfix-1/-2/-3/-4/-5 历史脏数据（archive 路径）：归 chg-6 一并清理

## 5. Next Steps

- requirement_review stage 出口决策 = auto（stage_policies.requirement_review = auto，analyst 自决推进）
- planning stage 续跑（同 subagent 同会话）：完成 chg 拆分 + roadmap.md 落地 + 首批推荐
- planning 完成后 stage_policies.planning = user：等用户拍板首批 chg 范围后，由主 agent 用 harness change 创建对应 chg 工件

## 6. 模型一致性自检

- 期望 model：opus（roles.analyst.model）
- 实际 model：opus（briefing 注入 expected_model = opus，已自检一致）
- 时间戳：requirement_review 入口 2026-04-27T07:03:22Z（runtime.yaml stage_entered_at）
