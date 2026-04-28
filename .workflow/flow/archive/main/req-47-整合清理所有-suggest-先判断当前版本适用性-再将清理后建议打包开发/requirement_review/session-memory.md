# Session Memory — req-47 requirement_review

## 1. Current Goal

执行 req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）requirement_review stage（Part A），承接 req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）成果，澄清复核范围 / 打包粒度 / 交付边界 / 池清理动作 / sug-58 优先级承接 5 个关键边界，编写 requirement.md（背景 / 目标 / 范围 / 验收标准）。

## 2. Context Chain

- Level 0: 主 agent → harness-manager (opus, harness requirement)
- Level 1: analyst-L1 (opus, req-47 requirement_review Part A)

## 3. 已做工作

- 读取 runtime.yaml 确认 current_requirement = req-47, stage = requirement_review；conversation_mode = harness（锁定）
- 读取背景文件：tools/index.md / project-overview.md / context/index.md
- 加载角色链：base-role.md → stage-role.md → analyst.md
- 模型一致性自检：role-model-map.yaml roles.analyst.model = opus，与 briefing 期望一致 ✓
- 读 req-46 关键产物：requirement.md / sug-audit.md / roadmap.md / done/session-memory.md / artifacts/.../交付总结.md
- 读 repository-layout.md §3 机器型路径表（防 chg-01 路径修复回归）
- 核实当前 sug 池实况（51 个 .md 文件）：
  - status: applied → sug-25（live 残留）
  - status: archived → sug-35 / sug-46 / sug-50（live 残留，违反契约 6"frontmatter status: archived 应在 archive/"）
  - sug-46 双份残留：live + archive 各一份
  - archive/ 目录现有 9 条（sug-01 ~ sug-07 历史 + sug-43 转 req + sug-46 双份）
- 写入 requirement.md 到 `.workflow/flow/requirements/req-47-{slug}/requirement.md`（机器型权威路径）

## 4. 关键拍板边界（拍板候选 + default-pick）

> 按硬门禁四同阶段不打断原则：列 options + 标 default-pick + 按默认推进 + stage 流转前 batched-report；用户拍板争议点不属于 stage 末选项（豁免硬门禁七 Ra），属于 batched-report 内容。

| 决策点 | 选项 | default-pick | 理由 |
|-------|-----|-------------|-----|
| **D-1 复核范围** | A. 仅复核 req-46 audit 标 live 的 31 条 + 6 条新增 = 37 条 / B. 全量 51 条池中文件再过一遍 / C. 含 audit 已标 stale/applied/dup 的 11 条也重审 | **A**（37 条聚焦） | req-46 audit 已对 11 条做权威判定 + 决策记录（D-1 ~ D-5），D-1 = A 已确定；重审等于推翻已决议；池中翻转滞留 4 条只做出池物理动作不重判，不算复核工作 |
| **D-2 打包粒度** | A. 直接复用 req-46 roadmap 剩余 8 chg / B. 基于复核后存活 sug 重新拆 chg / C. 增量校准（A 底盘 + 新 sug 归簇 + 必要时合并/拆分） | **C**（增量校准） | A 忽略 chg-01 / chg-02 落地后的语义变化；B 推翻 req-46 已用户拍板的拆分共识；C 既保留 roadmap 共识又吸收实战变化，最贴合用户原意"清理后建议打包开发" |
| **D-3 交付边界** | A. 复核 + 打包 + 全部 8 chg 一次性落地 / B. 复核 + 打包 + 首批 K 个 chg 落地 + 其余留尾给下个 req（与 req-46 同模式）/ C. 复核 + 打包 + 不落地（只产出 roadmap） | **B**（首批 K 落地 + 留尾） | A 体量过大（合计 3 大 / 5 中 / 2 小，~600~1500k token）单 req 不可能完成；C 用户原话"打包开发"明确含落地动作；B 与 req-46 同节奏，可控可演进 |
| **D-4 首批 K 推荐** | A. K = 1（chg-7 testing 红线，sug-58 high）/ B. K = 2（chg-7 + chg-2 数据底座）/ C. K = 3（chg-7 + chg-2 + chg-9 runtime sync）/ D. 由 planning stage 拍 | **A**（K = 1，chg-7） | sug-58 在 req-46 交付总结明确"下个 req 优先承接"；chg-7 是 P0 数据安全 + 中工作量；chg-2 是大工作量（150-400k token），与 chg-7 一起容易超标；K = 1 保证单 req 可控 + chg-7 落地后 testing 红线立刻保护后续所有 req；本 D-4 仅给 req_review stage 推荐，最终拆分由 planning stage 决定 |
| **D-5 池清理动作** | A. 复核出 stale / applied-out / dup-of 直接 archive（翻 frontmatter + 物理移走）/ B. 仅标记不做物理动作 / C. 全部 delete 不留 archive | **A**（archive） | 契约 6 frontmatter status: applied/archived 配合 archive/ 物理位置；B 违反契约 6 语义；C 失追溯链路；A 与 req-46 同模式 |
| **D-6 翻转滞留 4 条处理** | A. 与新复核 sug 一起 archive / B. 单独物理动作快速出池（不计入复核工作量） | **B**（独立快速出池） | sug-25 / sug-35 / sug-46 / sug-50 frontmatter 已是 applied/archived，状态判定无争议，仅 live 目录残留违反契约 6；与新复核解耦避免阻塞复核工作；sug-46 双份残留同期处理 |
| **D-7 sug-58 优先级承接** | A. 本 req 首批必含 chg-7（承接 sug-58）/ B. 由 planning 拆分时再定 / C. 推迟到下下个 req | **A**（必含 chg-7） | sug-58 在 req-46 done 阶段明确"下个 req 优先承接 chg-7（testing 红线 + safer dogfood）"，本 req 即"下个 req"；推迟违反 sug 承接路径；B 把决策推后增加 planning 不确定性 |
| **D-8 6 条新 sug 归簇** | A. 全部进既有 chg 不新设 / B. sug-58 → chg-7 / sug-59 → chg-2 / sug-55 → chg-2 或 chg-7 / sug-54 + sug-56 + sug-57 视粒度分散 / C. 新设 chg-11 收所有新 sug | **B**（按主题分散归簇） | A 不区分主题强行塞既有 chg 反而模糊边界；C 新设 chg 仅为 6 条 sug 粒度过细；B 按主题归簇最自然，sug-58 → chg-7（同 testing 红线主题）/ sug-59 → chg-2（usage-log 路径漂移同 chg-2 数据底座主题）/ sug-55 → 待 planning 决（dev mode 与 testing/部署都相关）/ sug-54 / sug-56 / sug-57 → 视粒度合并入相关 chg 或独立小 chg；详细归簇由 planning 决定 |
| **D-9 audit-r2 / roadmap-r2 命名** | A. 沿用 sug-audit / roadmap 命名（覆盖 req-46 副本不存在风险）/ B. 加 -r2 后缀（round 2）明示承接 req-46 / C. audit-req-47.md / roadmap-req-47.md | **B**（-r2 后缀） | A 路径在 req-47 目录不会覆盖 req-46，但语义不清；C 冗余（已在 req-47 目录内）；B 简洁 + 明示与 req-46 衔接关系 |
| **D-10 是否产出独立 audit-r2 / roadmap-r2 文件** | A. 内嵌 session-memory / B. 独立文件挂在 §4 引用（req-46 同款）/ C. 仅写入 requirement.md 不独立产出 | **B**（独立文件） | 体量 39 行表格 + 8 chg 表格难以塞 session-memory；C 把分析丢失到流转后无可读载体；B 与 req-46 同款，可读性 + 复验性 |

## 5. 重要约束 / 假设

- **不重判 req-46 已结案 sug**：D-1 = A 锁定 11 条 stale/applied/dup 不重审，避免推翻已用户拍板共识
- **不动 sug 文件 frontmatter 优先级**：避免 sug 文件 churn（与 req-46 同款），新优先级仅落 audit-r2 / roadmap-r2
- **首批 K = 1 推荐**：考虑工作量上限 + chg-7 单点 P0 数据安全紧迫性，避免与 chg-2（大）合并超标
- **chg 编号方案**：本 req 复用 req-46 簇编号 chg-3 ~ chg-10（语义稳定），新增 chg 由 CLI 分配序号 chg-NN
- **路径自检硬门禁**：requirement.md 已落 `.workflow/flow/requirements/req-47-{slug}/`（非 artifacts/main/requirements/req-47-{slug}/{stage-name}/），符合 req-46 chg-01 路径修复后契约

## 6. 待处理捕获问题

- 池中实际 51 个 .md 文件（.workflow/flow/suggestions/ 直接 ls，不计 archive/），与 briefing "52 条" 估算差 1 条；不影响 req_review 工作（具体复核单位为"实际池现状 + 命名档"，不是估算数）
- chg-7 落地涉及 testing.md 红线 + harness validate testing-no-destructive-git lint + plan.md §测试用例设计 dogfood TC 字段 + done 阶段 git revert --dry-run，工作量"中"上限；planning 时需注意是否触发 chg-7a / chg-7b 二次拆分（保留给 planning 拍）
- sug-55（dev mode flag）主题既属 chg-2（部署同步）也属 chg-7（testing 流程），归簇待 planning 拍

## 7. 退出条件 checklist

Part A（req_review）退出条件（按 analyst.md §退出条件）：
- [x] requirement.md 含背景（§2）/ 目标（§2）/ 范围（§3 In/Out）/ 验收标准（§4 AC-01 ~ AC-05）
- [x] `harness validate --human-docs`：exit 1，0/2 通过（raw_artifact + 交付总结 两条都是 done 阶段产物，按 D-11 = B 留痕放行；与 req-43/-44/-45/-46 同 case 一致）
- [x] `harness validate --contract artifact-placement` exit 0 ✓

经验沉淀检查：
- [x] 本 stage 主要复用 req-46 经验 + 既有契约（base-role / stage-role / analyst.md），无新可泛化经验需要沉淀（无新沉淀亦合规）

上下文负载评估：
- 当前用量约 60-65k tokens（读完 base-role / stage-role / analyst.md / sug-audit.md / roadmap.md 大文件后），未达 70% 阈值，无需 /compact 或 /clear

## 8. Default-pick 决策清单

| 决策点 | default-pick | 状态 |
|-------|-------------|-----|
| D-1 复核范围 | A（37 条聚焦） | 已落 requirement.md §3.1 |
| D-2 打包粒度 | C（增量校准） | 已落 requirement.md §5 |
| D-3 交付边界 | B（首批 K + 留尾） | 已落 requirement.md §5（首批 ≤ 3）|
| D-4 首批 K 推荐 | A（K = 1，chg-7） | 推荐落 requirement.md §2，最终由 planning 拍 |
| D-5 池清理动作 | A（archive） | 已落 requirement.md §3.1 B |
| D-6 翻转滞留 4 条处理 | B（独立快速出池） | 已落 requirement.md §3.1 B + AC-02 |
| D-7 sug-58 优先级承接 | A（必含 chg-7） | 推荐已落 requirement.md §2 + §5 split rules |
| D-8 6 条新 sug 归簇 | B（按主题分散归簇） | 已落 requirement.md §3.1 + Split Rules，详细归簇由 planning 拍 |
| D-9 audit-r2 / roadmap-r2 命名 | B（-r2 后缀） | 已落 requirement.md §5 末尾引用路径 |
| D-10 独立文件产出 | B（独立文件 + §4 引用） | 已落 requirement.md AC-01 / AC-03 |
| D-11 raw_artifact / 交付总结 validate 不绿是否 ABORT | A. 严格 ABORT / B. raw_artifact ✓ 留痕放行（done 文档豁免到 done 阶段）/ C. 用户介入 | **B** | 沿用 req-46 D-11 = B 决策；raw_artifact 副本 + 交付总结.md 都是 done 阶段产物，工具未做 stage 感知；历史 req-43/-44/-45/-46 同 case 均放行；本 stage 留痕放行，工具修复列入 chg-5 lint 套件（已在 req-46 roadmap） |

## 9. Results

verdict: PASS。req-47 requirement.md 已落 `.workflow/flow/requirements/req-47-{slug}/requirement.md`，覆盖 5 个用户原意核心边界（复核范围 / 打包粒度 / 交付边界 / 池清理动作 / sug-58 承接），10 条 default-pick 决策已记录。等待 harness validate 双门禁。
