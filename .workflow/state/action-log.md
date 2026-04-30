# Action Log

## 2026-04-29T16:52:05Z harness-manager: manual recovery req-51 runtime
- 触发: `harness next` 在 testing → acceptance 推进时异常清空 runtime（active_requirements / current_requirement 全空），但 req-51.yaml + bugfix-11.yaml 状态保留。疑似 CLI 多 active 场景下推进的 bug。
- 结果: runtime.yaml 手动恢复 current_requirement=req-51 / stage=acceptance / active_requirements=[bugfix-11, req-51]；下一步派 acceptance subagent 跑客观核查。
- 待入 sug: harness next 多 active 场景推进异常清空 runtime（独立 bug，与 req-51 主线无关）

## 2026-04-29T17:10:00Z done(opus): req-51（项目级规则-经验-工具支持从制品引入）六层回顾完成
- 六层回顾: Context / Tools / Flow / State / Evaluation / Constraints 全过；硬门禁九本周期触发 3 次（executing round-1 / testing 数字 / acceptance 阶段 runtime 异常）均由主 agent 独立核查抓出；mirror 4 文件 diff silent；pytest 51/729（51 failed = bugfix-11 baseline 不增）。
- verdict: 不重审 acceptance verdict（PASS）；本周期 4 chg + 21 TC + 14 checklist 全 PASS。
- 产出: artifacts/main/requirements/req-51-项目级规则-经验-工具支持从制品引入/交付总结.md（新建）；req-51 session-memory.md 末尾追加 'Done Stage Six-Layer Review' 段。
- sug 入池 4 条: sug-65（harness next 多 active 推进异常清空 runtime / high）、sug-66（harness ff --auto UX 误导 / medium）、sug-67（testing subagent 必须独立 paste stdout / medium，与 sug-63 同型）、sug-68（硬门禁九升级 stdout paste 成文化 / high）。
- archive 建议: bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）+ req-51（项目级规则-经验-工具支持从制品引入）均建议立即 archive，由用户后续显式触发 `harness archive` 决定时点。

## 2026-04-29T19:45:00Z done(opus): bugfix-12（runtime-block.yaml-误判用户野文件-白名单漏配）六层回顾完成
- 六层回顾: Context / Tools / Flow / State / Evaluation / Constraints 全过；同型病扫描 10 类 .workflow/state/* 自写文件仅 1 例漏配（已修）；硬门禁九本周期触发 3 次（regression 4 结论 / executing 白名单 grep / acceptance dogfood Python）均由主 agent 独立核查；executing 首次未虚报（独立 paste lint stdout 全部对得上），bugfix-11 教训发挥作用。
- verdict: 不重审 acceptance verdict（PASS / 0 未达标项）；修复 = 白名单 +1 行（workflow_helpers.py:179）+ 4 TC（test_bugfix_12_runtime_block_whitelist.py）+ pytest 51 failed=baseline / 733 passed（+4 新 TC）。
- 产出: artifacts/main/bugfixes/bugfix-12-runtime-block-yaml-误判用户野文件-白名单漏配/bugfix-交付总结.md（新建）；session-memory.md 末尾追加 'Done Stage Six-Layer Review' 段；executing.md 经验十五（同型病兜底清单方法论）已沉淀。
- sug 入池: 0（bugfix-12 周期未发现新问题，旁支问题 0）。
- archive 建议: bugfix-11 + req-51 + bugfix-12 三件可一起 archive，但 done 阶段不动等用户后续显式触发 `harness archive`。

## 2026-04-30T11:15:00Z executing(sonnet): bugfix-13（install时自动创建artifacts-project骨架与索引模板）Round 1 executing 完成
- 新增: `src/harness_workflow/assets/templates/project-skeleton/`（10 文件：README.md + constraints/index.md + experience/{roles,tool,risk,regression,stage}/index.md + 3 .gitkeep）
- 新增: `workflow_helpers.py::_bootstrap_project_skeleton(root, check)` helper（L3745）+ `install_repo` 内调用点（L3816）
- 新增: `tests/test_bugfix_13_project_skeleton_bootstrap.py`（10 TC）
- lint: pytest 10/10 PASS；dogfood fresh repo created 10 files；validate user-write-protected-zones PASS；全 suite 754 passed / 52 failed（基线不增）

## 2026-04-30T02:35:00Z done(opus): req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）六层回顾完成
- 六层回顾: Context / Tools / Flow / State / Evaluation / Constraints 全过；契约层 4 文件 diff -q silent；State 层 usage-log 5 entries ≥ 派发次数；硬门禁九本周期触发 1 次（executing 虚报基线 "56 failed/721 passed" 实测 51/729，主 agent 独立核查抓出 + round-2 微调修复）；同型病第 5 次复发，与 sug-67 / sug-68 同型。
- verdict: 不重审 acceptance verdict（PASS / 0 未达标项）；req-52 12 TC 全 PASS（test_req52_e2e_log × 3 + test_req52_lazy_index_loading × 5 + test_req52_no_main_hardcode × 4）；bugfix-11 反例 lint 25/25 PASS；pytest 51 failed=baseline / 745 passed（含 req-52 +12 TC）；scaffold mirror 4 对全 silent。
- 产出: artifacts/main/requirements/req-52-硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证/交付总结.md（新建）；analysis/session-memory.md 末尾追加 'Done Stage' 段。
- sug 入池 2 条: sug-69（subagent 同型病第 5 次复发-升级硬门禁九 stdout paste 强制条款 / high，与 sug-67 / sug-68 同型，建议合并为专项 req）、sug-70（bugfix-11 反例 lint legacy fallback 关键词过宽-误伤合法 branch-path 兼容路径注释 / medium）。
- archive 建议: bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）+ req-51（项目级规则-经验-工具支持从制品引入）+ bugfix-12（runtime-block.yaml-误判用户野文件-白名单漏配）+ req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）四件均已 done，建议**一起 archive**；done 阶段不动，等用户后续显式触发 `harness archive`。

## 2026-04-29T18:00:00Z analyst(opus): req-53（新增-harness-命令-给项目添加规范-经验-工具-引导式）Phase 2 + Phase 3 完成
- 触发: subagent 收 briefing「Phase 2 chg 拆分 + Phase 3 plan.md per chg 一气完成」；requirement.md 不动（Phase 1 + OQ Verdicts 锁定）
- 拆分: 4 chg（chg-01 CLI 入口与反非法 lint / chg-02 add 落位与模板预填 / chg-03 index 登记与 git stage / chg-04 list 与 interactive 与 dogfood）线性依赖；stub-then-replace 渐进策略
- 产出: 4 chg 各 change.md / plan.md / session-memory.md（共 12 文件）；analysis/session-memory.md 追加 Phase 2 + 3 决策清单（10 条 P-2x default-pick 留痕）
- 测试 TC 设计: 38 条（chg-01 8 / chg-02 8 / chg-03 10 / chg-04 12）；plan.md 含精确文件 / 行号 / 函数名 / lint 字面
- lint: artifact-placement PASS / user-write-protected-zones PASS / test-case-design-completeness req-53 4 plan.md 全 PASS（其余 violations 均 req-41 archive 区历史遗留，与 req-53 无关）
- 阻塞用户拍板事项: 无；待用户对「需求 + 4 chg 拆分 + plan.md」整合产物一次性确认

## 2026-04-30T08:55:00Z done(opus): req-53（新增-harness-命令-给项目添加规范-经验-工具-引导式）六层回顾完成
- 六层回顾: Context / Tools / Flow / State / Evaluation / Constraints 全过；硬门禁九本周期触发 1 次（executing 自报 baseline 57 实测 51，主 agent 抓出虚报，与 sug-67 / sug-68 / sug-69 同型——同型病累计第 5+ 次复发）；State 层 usage-log 5 entries ≥ 派发次数 5（done 由主 agent 直跑无 entry）；范围红线清洁 0 命中 PetMallPlatform / PetMallAdmin / uav；契约 artifact-placement + user-write-protected-zones 双绿。
- verdict: 不重审 acceptance verdict（PASS / 0 未达标项）；req-53 4 chg 全过 + 40 TC + bugfix-13 防回归 10 TC 全 PASS；全 suite 51 failed=baseline / 797~798 passed（含 +40 req-53 新增 TC，0 new fail）；dogfood 端到端落位 / index 登记 / git stage / 反非法 ABORT 全过；2 处历史遗留 bug 顺手修（tools/index.md contract-7 + bugfix-13 .gitkeep 期望）。
- 关键决策: OQ-0 命令名=pad / OQ-1 命令形态 C 候选 + kind 3 个固定（rule/experience/tool）/ rule scope 5 个 + experience scope 5 个 + tool 不分 scope（user 不能发明枚举）/ OQ-2 add+list / OQ-3 interactive 默认开启 / OQ-4 when_load=always / OQ-5 自动 git add+提示 commit 不自动 commit；Phase 2 拆分 4 chg 线性依赖 + stub-then-replace 渐进策略。
- 产出: artifacts/main/requirements/req-53-新增-harness-命令-给项目添加规范-经验-工具-引导式/交付总结.md（新建）；analysis/session-memory.md 末尾追加 'Done Stage Six-Layer Review' 段。
- sug 入池 2 条: sug-71（修源码 + 删/改文件时同步扫 tests/ 是否有相关期望需更新 / medium，bugfix-13 round-4 .gitkeep 漏改虚报教训）、sug-72（harness validate 新增 contract 检测 artifacts/project 之外的 artifacts/{其他}/ 自定义结构防 AI 发明路径 / medium，与用户原话痛点呼应）。**不重复入池**：subagent baseline 虚报第 N 次（已有 sug-67/68/69 覆盖）。
- archive 建议: bugfix-11 + req-51 + bugfix-12 + req-52 + bugfix-13 + req-53 六件均已 done，建议**一起 archive**；done 阶段不动，等用户后续显式触发 `harness archive`。

## 2026-04-30T03:50:00Z done(opus): bugfix-13（install时自动创建artifacts-project骨架与索引模板）六层回顾完成
- 六层回顾: Context / Tools / Flow / State / Evaluation / Constraints 全过；硬门禁九本周期触发 1 次（testing 虚报 "52 failed=baseline" 实测 +1，主 agent 独立核查抓出 + round-2 修 README line 21 / 同型 README 模板 line 21 各 1 行，回到 51 failed=755 passed）；同型病第 6 次复发，与 sug-67 / sug-68 / sug-69 / sug-70 同源同型。
- verdict: 不重审 acceptance verdict（PASS / 0 未达标项）；修复 = 模板树 10 文件（src/.../assets/templates/project-skeleton/）+ helper `_bootstrap_project_skeleton`（workflow_helpers.py L3745）+ install_repo 调用点（L3816）+ 10 反例 TC（test_bugfix_13_project_skeleton_bootstrap.py）+ Round 2 README line 21 contract-7 微调；pytest 51 failed=baseline / 755 passed（acceptance 时刻；现 756 passed，差 1 无回归）。
- 产出: artifacts/main/bugfixes/bugfix-13-install时自动创建artifacts-project骨架与索引模板/bugfix-交付总结.md（新建）；session-memory.md 末尾追加 'Done Stage Six-Layer Review' 段。
- sug 入池: 0（同型病第 6 次复发不重复入池；建议把既有 sug-67 / sug-68 / sug-69 / sug-70 合并为专项 req 升级硬门禁九 "subagent 必须独立 paste lint stdout 全文 + 主 agent 必须独立 grep 实测 +1 / +0 比对" 成文化为契约硬门禁）。
- archive 建议: bugfix-11 + req-51 + bugfix-12 + req-52 + bugfix-13 五件均已 done，建议**一起 archive**；done 阶段不动，等用户后续显式触发 `harness archive`。

## 2026-04-30T11:16:37Z done(opus): req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束）六层回顾完成
- 六层回顾: Context / Tools / Flow / State / Evaluation / Constraints 全过；本 req 自身即"硬门禁体系简化"——硬门禁体系从 12+ 条（含跳号）减到 9 条有真威慑（保留 1/3 + base 三/四/五/六/七/八/九）；硬门禁九本周期触发 2 次（testing 抓 chg-02 executing §3.6.2 虚报 / 主 agent 抓 acceptance subagent 写错 checklist 路径）均独立核查兜底；契约 4 文件 mirror diff -q 全 silent；usage-log.yaml 缺失，效率与成本段按规约标 ⚠️ 无数据。
- verdict: 不重审 acceptance verdict（PASS / 0 未达标项）；req-54 9 TC 全 PASS（test_req54_hard_gate_simplify.py）；全 suite acceptance 时刻 40 failed / 821 passed（≤ 上轮 round-2 55 failed，环境改善非回归；req-54 自身 0 new fail）；fresh repo install + validate --contract all exit 0 ✅；chg-02 executing 虚报 §3.6.2 由 testing 抓出 + 主 agent round-2 直接补写完成闭环（同型病第 7+ 次复发，与 sug-67/68/69/70 同源）。
- 关键决策: OQ-3 砍法=降级文字 + 段标题改 + 保留段落（不删整段，便于历史追溯）；OQ-6 硬门禁八编号紧邻硬门禁九之前（7→8→9 连续）；OQ-7 dogfood 自证落点=done 交付总结一行（不新增独立工件）；硬门禁八与硬门禁九形成「事前 brief / 事后核查」配对闭环。
- 产出: artifacts/main/requirements/req-54-硬门禁体系简化-砍4条降级-加1条项目级brief强约束/交付总结.md（新建）；analysis/session-memory.md 末尾追加 'Done Stage Six-Layer Review' 段。
- sug 入池 0 条: chg-02 executing §3.6.2 虚报（同 sug-67/68/69 同型，第 7+ 次复发，不重复入池） / acceptance subagent 写错 checklist 路径（同型变种，不重复入池） / archive CLI bug runtime 异常切换（与 sug-65 同型第 2 次复发，不重复入池）。建议将 sug-67/68/69/70 + 本周期 2 次同型合并升级为专项 req（硬门禁九成文化）；建议将 sug-65 升级为 bugfix（archive CLI 多 active 推进异常清空 runtime）。
- archive 建议: bugfix-11 + bugfix-12 + bugfix-13 + req-51 + req-52 + req-53 + req-54 七件均已 done，建议**一起 archive**；done 阶段不动，等用户后续显式触发 `harness archive`。

