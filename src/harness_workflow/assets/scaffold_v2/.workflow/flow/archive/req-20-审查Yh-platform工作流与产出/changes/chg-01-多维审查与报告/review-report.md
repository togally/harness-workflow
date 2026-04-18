# Yh-platform 项目 req-01 ~ req-05 Harness 工作流审查报告

审查日期：2026-04-15  
审查范围：`/Users/jiazhiwei/IdeaProjects/Yh-platform` 的 req-01 至 req-05 共 5 个需求  
审查维度：流程合规性、经验产出、Bug 与反思、工具层变更、制品完整性

---

## 一、总体概览

| 需求 | 标题 | 状态 | 变更数 | 阶段完整度 | 归档情况 |
|------|------|------|--------|-----------|----------|
| req-01 | dockDetail 新增字段 | archived | 1 | 完整 | 已归档 |
| req-02 | 无人机和机场 OSD 数据新增 | archived | 3 | 完整 | 已归档 |
| req-03 | uav-test 分支 Maven 编译报错修复 | archived | 1 | 不完整（跳过 planning/executing） | 已归档 |
| req-04 | uav-test 分支编译语法错误修复 | archived | 1 | 不完整（跳过 planning/executing） | 已归档 |
| req-05 | dockDetail 新增字段验收回归 | done | 3 | 完整 | 未归档（当前活跃） |

---

## 二、维度一：流程是否符合标准

### 2.1 阶段流转与合规性逐项分析

#### req-01：dockDetail 新增字段
- **阶段记录**：requirement_review → planning → executing → testing → acceptance → done
- **合规性**：各阶段时间戳齐全，流转顺序正确，无阶段跳过。
- **问题**：`stage_timestamps` 中所有时间戳均为 `2026-04-15T00:00:00`，精度不足，无法反映真实阶段耗时。这是 req-12 已记录但尚未修复的问题。
- **结论**：流程合规，但时间戳精度存疑。

#### req-02：无人机和机场 OSD 数据新增
- **阶段记录**：requirement_review → planning → executing → regression → testing → acceptance → done
- **合规性**：唯一一个经历了 regression 阶段后再回到 testing 的完整流程的需求。regression 触发原因是 `uavDetail` 中 `deviceUavDetail` 为 null 时未返回带默认值的空对象，属于真实问题。
- **结论**：流程完整且合规，regression 使用合理。

#### req-03：uav-test 分支 Maven 编译报错修复
- **阶段记录**：requirement_review → planning → executing → testing → acceptance → done
- **合规性**：时间戳全部为 `00:00:00`，与 req-01 类似。且作为紧急编译修复，planning/executing 阶段是否有实质产出存疑（仅 1 个变更，无 regression 记录）。
- **结论**：流程记录完整，但阶段实质执行深度不足，时间戳精度问题同样存在。

#### req-04：uav-test 分支编译语法错误修复
- **阶段记录**：requirement_review → regression → testing → acceptance → done
- **合规性**：明确跳过了 planning 和 executing。`done-report.md` 中解释为"单字符语法修复，planning/executing 非必需"。
- **问题**：虽然理由合理，但 Harness 标准流程中 executing 是代码变更的必经阶段。对于直接修改代码的变更，跳过 executing 属于流程例外，应在 `done-report.md` 中更明确地标注例外审批依据。
- **结论**：流程存在合理例外，但记录不够正式。

#### req-05：dockDetail 新增字段验收回归
- **阶段记录**：regression → testing → acceptance → done
- **合规性**：作为验收回归需求，从 regression 直接进入 testing 是合理的。无 requirement_review / planning / executing 符合回归修复的场景定义。
- **时间戳**：regression `12:00` → testing `12:15` → acceptance `17:30` → done `17:45`，时间戳精确，阶段耗时可计算。
- **结论**：流程合规，时间戳记录质量最佳。

### 2.2 流程合规性评分

| 需求 | 评分 | 说明 |
|------|------|------|
| req-01 | 良好 | 完整流转，时间戳精度不足 |
| req-02 | 优秀 | 唯一完整经历 regression 的需求 |
| req-03 | 合格 | 记录完整但阶段深度和时间戳不足 |
| req-04 | 合格 | 合理跳过 executing，但例外记录不够正式 |
| req-05 | 优秀 | 回归场景流程清晰，时间戳精确 |

---

## 三、维度二：经验产出

### 3.1 经验文件审查

读取 `.workflow/context/experience/index.md` 及下属目录后，经验产出分布如下：

#### 有实质内容的经验文件

| 文件 | 实质经验条数 | 来源需求 | 质量评价 |
|------|-------------|----------|----------|
| `stage/regression.md` | 7 条 | req-02, req-05 | 优秀，覆盖需求范围遗漏、语义确认、backup 使用、前端 ground truth、编译与结构问题分离、厂商文档权威等 |
| `stage/development.md` | 4 条 | req-02, req-05 | 优秀，覆盖薄壳脚本依赖、并行状态迁移、MQTT/OSD 扁平化陷阱、分支编译基线检查 |
| `stage/requirement.md` | 3 条 | req-02 | 良好，覆盖需求边界例外、删除前追溯消费者、大架构重构后脚本同步更新 |
| `risk/known-risks.md` | 3 条 | req-02, req-05 | 良好，覆盖 tools 目录迁移路径依赖、Edit 工具限制、JDK 21 + Lombok 不兼容 |
| `tool/claude-code-context.md` | 2 条大经验 | req-03, req-04 | 优秀，详细记录了上下文爆炸教训及六层解决方案设计 |
| `tool/harness.md` | 4 条 | req-02, req-07 | 良好，覆盖 pipx inject、python3 命令、subagent 大文件重写、scaffold_v2 同步 |
| `tool/harness-ff.md` | 4 条 | req-05 | 良好，覆盖 ff 模式边界、skill 缺失恢复、API Error 400 恢复、AI 自主验收标准 |

#### 空模板/未更新的经验文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `stage/acceptance.md` | 空占位符 | 仅有模板标题，无实质内容 |
| `stage/testing.md` | 空占位符 | 仅有模板标题，无实质内容 |

### 3.2 各需求经验产出覆盖

| 需求 | 是否有经验沉淀 | 沉淀位置 | 缺失说明 |
|------|---------------|----------|----------|
| req-01 | 无 | 无 | `session-memory.md` 中 "Candidate Lessons: None"，done-report 未提及经验 |
| req-02 | 有 | regression.md、requirement.md、development.md、known-risks.md、harness.md | 经验最丰富 |
| req-03 | 有（间接） | tool/claude-code-context.md | req-03 本身是上下文爆炸触发源，但需求 done-report 未主动记录 |
| req-04 | 有（间接） | tool/claude-code-context.md | done-report 明确写"未产生需要泛化的经验教训"，无主动沉淀 |
| req-05 | 有 | regression.md、development.md、known-rrisks.md、harness-ff.md | done-report 明确记录了 4 条经验更新 |

### 3.3 经验产出评分

| 需求 | 评分 | 说明 |
|------|------|------|
| req-01 | 差 | 无任何经验沉淀 |
| req-02 | 优秀 | 多维度、多文件、高质量 |
| req-03 | 合格 | 作为触发源被记录，但自身无主动沉淀 |
| req-04 | 差 | 明确声明无经验，作为简单修复可接受，但仍有提升空间 |
| req-05 | 优秀 | 主动记录并更新多个经验文件 |

---

## 四、维度三：Bug 数量与反思质量

### 4.1 各需求 regression / bug 统计

#### req-01
- **regression 文件**：`regression/diagnosis.md`
- **问题**：后端将 10 个新增字段放在 `DockResp` 顶层，而前端从 `deviceDockDetail` 下读取，导致接口字段位置不匹配。
- **根因**：实现时未对照前端实际消费路径，需求文档中"或"字（`DockResp` 或 `DeviceDockDetail`）被误读。
- **反思质量**：高。diagnosis.md 详细分析了前端读取路径、后端字段分布、需求文档对照，并给出了完整的修复方案（模型层、Handler 层、Controller 层、清理）。
- **Bug 数**：1 个（接口字段位置不匹配）

#### req-02
- **regression 文件**：`changes/chg-03/regression/diagnosis.md`
- **问题**：`UavDetailController.uavDetail` 中 `deviceUavDetail` 为 null 时未返回带默认值的空对象，前端可能收到 null。
- **根因**：开发者只考虑了对象存在但字段为 null 的情况，遗漏了数据库中无记录导致对象本身为 null 的场景。
- **反思质量**：高。明确引用 AC 原文作为判定依据，指出 testing 阶段禁止修改被测代码，因此路由回 executing。
- **Bug 数**：1 个（null 对象未兜底）

#### req-03
- **regression 文件**：无
- **问题**：Maven 编译报错（Lombok 与 JDK 21 不兼容）。
- **说明**：这是一个环境/依赖问题，未触发 regression 流程，直接在 executing 阶段修复。
- **Bug 数**：0（属于依赖兼容性问题，非代码 bug）

#### req-04
- **regression 文件**：`changes/chg-01/regression/diagnosis.md`
- **问题**：`DefaultWSSHandler.java` 编译语法错误，根因为历史提交 `49d1561f6` 意外删除了 `if (isUavOsd)` 代码块的结束括号 `}`。
- **根因**：合并冲突解决时的语法遗漏。
- **反思质量**：高。通过 `git diff` 精确定位到引入错误的提交，给出了逐行代码对比和编译器报错链式分析。
- **Bug 数**：1 个（合并引入的语法错误）

#### req-05
- **regression 文件**：3 个（chg-01、chg-02、chg-03 均有 diagnosis.md）
- **问题汇总**：
  1. **chg-01**：编译阻断（Lombok 版本 + `DefaultWSSHandler` 语法错误）+ 前后端字段结构不匹配（嵌套对象被扁平化、字段语义混淆、`coverState` 映射不完整）
  2. **chg-02**：`DockResp` 中 9 个透传 `JSONObject` 字段注释过于模糊，未说明具体子字段
  3. **chg-03**：缺少针对真实设备的端到端联调测试；`UavDetailControllerTest.dockDetail()` 无断言
- **深层发现（重要）**：在 chg-03 regression 调查中，发现 **DefaultWSSHandler 中 13 个 OSD 字段名与 DJI 协议不匹配**（原始 diagnosis.md 写为 14 个，但实际列出的独立字段映射为 13 个），并逐一修正。这是 req-05 最重要的技术产出。
- **反思质量**：极高。chg-01 diagnosis.md 是全场最详细的诊断报告，分章节明确区分"编译阻断"与"结构不匹配"，梳理了前端 `updateDockData(data)` 函数，输出了 `frontend-osd-mapping.md` 知识文档。
- **Bug 数**：
  - 编译问题：2 个（Lombok 版本、语法错误）
  - 结构/语义问题：3 个（嵌套对象扁平化、字段语义混淆、`coverState` 映射不完整）
  - 测试覆盖问题：1 个（无断言的集成测试）
  - 深层字段映射错误：13 个 OSD 字段名不匹配

### 4.2 Bug 与反思汇总表

| 需求 | Bug/问题数 | 反思质量 | 关键教训 |
|------|-----------|----------|----------|
| req-01 | 1 | 高 | 后端实现必须对照前端实际消费路径 |
| req-02 | 1 | 高 | null 兜底要考虑对象本身为 null 的场景 |
| req-03 | 0 | - | JDK 21 需配套升级 Lombok |
| req-04 | 1 | 高 | 合并冲突解决需更仔细审查语法完整性 |
| req-05 | 5+14 | 极高 | 前端参考实现是 API 验收的权威 ground truth；厂商 API 文档是字段映射的最终权威 |

---

## 五、维度四：工具层变更

### 5.1 工具系统现状

读取 `.workflow/tools/index.md` 及下属文件：

- `stage-tools.md`：完整定义了各 stage 的工具白名单和上下文管理规则
- `selection-guide.md`：包含工具选择决策矩阵、上下文维护决策流程图、subagent 派发规范
- `maintenance.md`：存在（未详细读取，但目录规范中提及）
- `catalog/`：包含 6 个工具定义文件
  - `_template.md`：新增工具模板
  - `agent.md`、`bash.md`、`claude-code-context.md`、`edit.md`、`grep.md`、`read.md`

### 5.2 工具层新增与修改

根据文件修改时间和内容判断，以下工具层文件是在 req-01 ~ req-05 期间新增或显著更新的：

| 文件 | 变更性质 | 来源需求 | 说明 |
|------|----------|----------|------|
| `tools/index.md` | 新增/重构 | req-02 | 定义了工具系统四项核心能力 |
| `tools/stage-tools.md` | 新增/重构 | req-02 ~ req-05 | 定义各 stage 白名单，后期因 ff 模式等更新 |
| `tools/selection-guide.md` | 新增/重构 | req-02 ~ req-04 | 包含上下文维护决策树，源自 req-04 的上下文维护机制设计 |
| `tools/catalog/claude-code-context.md` | 新增 | req-04 | 源自 req-04 专门设计的上下文维护工具 |
| `tools/catalog/agent.md` | 新增 | req-02 | 标准的 Agent 工具定义 |
| `tools/catalog/bash.md` | 新增 | req-02 | 标准的 Bash 工具定义 |
| `tools/catalog/edit.md` | 新增 | req-02 | 标准的 Edit/Write 工具定义 |
| `tools/catalog/grep.md` | 新增 | req-02 | 标准的 Grep/Glob 工具定义 |
| `tools/catalog/read.md` | 新增 | req-02 | 标准的 Read 工具定义 |

### 5.3 工具层变更评价

- **req-01**：无工具层变更
- **req-02**：大量工具层基础设施建立（`index.md`、`stage-tools.md`、`selection-guide.md`、5 个 catalog 文件），是工具层的奠基需求
- **req-03**：无直接工具层变更
- **req-04**：新增 `claude-code-context.md` 工具定义，是上下文维护机制的重要组成部分
- **req-05**：`stage-tools.md` 因 ff 模式有更新，`tools/index.md` 结构保持稳定

---

## 六、维度五：制品完整性

### 6.1 各需求制品清单

#### req-01
| 制品类型 | 是否存在 | 说明 |
|----------|----------|------|
| requirement.md | 是 | 完整，含背景、目标、范围、AC、Split Rules |
| change.md | 是 | 1 个变更 |
| plan.md | 是 | 1 个变更 |
| session-memory.md | 是 | 有，但 Candidate Lessons 为空 |
| test-results.md | 是 | 详细记录了 5 个 TC 及编译验证 |
| acceptance-report.md | 是 | 含 AC 核查表和人工验收待确认项 |
| done-report.md | 否 | 未找到（已归档目录中不存在） |
| regression/diagnosis.md | 是 | 详细诊断报告 |
| 归档产物 | 是 | 已归档到 `flow/archive/` |
| artifacts/requirements/ | 否 | 未找到（根目录无 `artifacts/`） |

**缺失**：`done-report.md` 缺失。req-01 作为已归档需求，缺少 done 阶段回顾报告。**此外，根目录未生成 `artifacts/requirements/` 制品仓库摘要。**

#### req-02
| 制品类型 | 是否存在 | 说明 |
|----------|----------|------|
| requirement.md | 是 | 非常详细，含大量字段表格 |
| change.md | 是 | 3 个变更均有 |
| plan.md | 是 | 3 个变更均有 |
| session-memory.md | 未找到 | 可能分散在 3 个变更下，但未在目录列表中显式出现 |
| test-results.md | 未找到 | 未在目录列表中显式出现 |
| acceptance-report.md | 未找到 | 未在目录列表中显式出现 |
| done-report.md | 否 | 未找到 |
| regression/diagnosis.md | 是 | chg-03 下有 |
| 归档产物 | 是 | 已归档 |
| artifacts/requirements/ | 否 | 未找到 |

**缺失**：`done-report.md`、各变更的 `session-memory.md`、`test-report.md`、`acceptance-report.md` 均缺失或未被单独记录。**根目录也未生成 `artifacts/requirements/` 制品仓库摘要。** req-02 虽然变更规划详细，但执行过程的 session 记录不完整。

#### req-03
| 制品类型 | 是否存在 | 说明 |
|----------|----------|------|
| requirement.md | 是 | 简洁明确 |
| change.md | 是 | 1 个 |
| plan.md | 是 | 1 个 |
| session-memory.md | 否 | 未找到 |
| test-results.md | 否 | 未找到 |
| acceptance-report.md | 否 | 未找到 |
| done-report.md | 否 | 未找到 |
| regression/diagnosis.md | 否 | 未找到 |
| 归档产物 | 是 | 已归档 |
| artifacts/requirements/ | 否 | 未找到 |

**缺失**：除 requirement/change/plan 外，几乎所有执行和评估阶段制品均缺失。作为简单编译修复，部分缺失可理解，但 `done-report.md` 仍应存在。**根目录同样无 `artifacts/requirements/` 制品仓库摘要。**

#### req-04
| 制品类型 | 是否存在 | 说明 |
|----------|----------|------|
| requirement.md | 是 | 简洁 |
| change.md | 是 | 1 个 |
| plan.md | 是 | 1 个 |
| session-memory.md | 否 | 未找到 |
| test-report.md | 是 | 有 |
| acceptance-report.md | 是 | 有 |
| done-report.md | 是 | 有，且内容完整 |
| regression/diagnosis.md | 是 | 有 |
| 归档产物 | 是 | 已归档 |
| artifacts/requirements/ | 否 | 未找到 |

**评价**：req-04 制品相对完整，是 5 个需求中 done-report 质量较高的一个。**但根目录未生成 `artifacts/requirements/` 制品仓库摘要。**

#### req-05
| 制品类型 | 是否存在 | 说明 |
|----------|----------|------|
| requirement.md | 是 | 明确 |
| change.md | 是 | 3 个变更 |
| plan.md | 否 | 3 个变更目录中均未找到 plan.md |
| session-memory.md | 否 | 未找到 |
| test-report.md | 是 | chg-01、chg-02 均有 |
| acceptance-report.md | 是 | chg-01、chg-02 均有 |
| done-report.md | 是 | 内容完整，质量高 |
| regression/diagnosis.md | 是 | 3 个变更均有，质量极高 |
| frontend-osd-mapping.md | 是 | 重要知识文档 |
| 归档产物 | 否 | 尚未归档（当前活跃） |
| artifacts/requirements/ | 否 | 未找到（根目录无 `artifacts/`） |

**缺失**：3 个变更均无 `plan.md`，session-memory.md 也未找到。作为验收回归需求，planning/executing 被跳过是合理的，但变更级别的 `plan.md` 仍建议补充以记录执行计划。**此外，根目录未生成 `artifacts/requirements/` 制品仓库摘要。**

### 6.2 制品完整性评分

| 需求 | 评分 | 说明 |
|------|------|------|
| req-01 | 良好 | 缺少 done-report 和 artifacts/requirements/ 制品仓库摘要 |
| req-02 | 合格 | 变更规划详细，但执行记录、done-report 和 artifacts/ 制品仓库摘要缺失 |
| req-03 | 差 | 仅基础文档，评估和回顾制品几乎全部缺失，且无 artifacts/ 制品仓库摘要 |
| req-04 | 良好 | 除 session-memory 外基本完整，但缺少 artifacts/ 制品仓库摘要 |
| req-05 | 良好 | 缺少 plan.md、session-memory 和 artifacts/ 制品仓库摘要，但诊断和知识文档质量极高 |

---

## 七、综合评分与结论

### 7.1 五维度综合评分表

评分标准：优秀（5）、良好（4）、合格（3）、差（2）、极差（1）

| 需求 | 流程合规 | 经验产出 | Bug 反思 | 工具变更 | 制品完整 | 综合均分 |
|------|----------|----------|----------|----------|----------|----------|
| req-01 | 4 | 2 | 4 | 1 | 4 | 3.0 |
| req-02 | 5 | 5 | 4 | 5 | 3 | 4.4 |
| req-03 | 3 | 3 | - | 1 | 2 | 2.2 |
| req-04 | 3 | 2 | 4 | 4 | 4 | 3.4 |
| req-05 | 5 | 5 | 5 | 3 | 4 | 4.4 |

### 7.2 各需求一句话结论

- **req-01**：流程完整但时间戳精度不足，无经验沉淀，缺少 done-report，regression 诊断质量高。
- **req-02**：流程最规范的需求之一，经验产出最丰富，工具层奠基需求，但执行过程记录（session-memory、test-report）缺失较多。
- **req-03**：作为简单编译修复，流程和制品均过于简化，时间戳全为占位符，几乎无评估和回顾产出。
- **req-04**：合理跳过部分阶段，done-report 质量较好，但明确声明"无经验教训"略显消极；发现了上下文爆炸这一关键问题（间接推动 req-04 机制设计）。
- **req-05**：验收回归的典范，diagnosis.md 和 `frontend-osd-mapping.md` 是全场最高质量产出，发现并修正了 13 个 OSD 字段映射错误，但 plan.md 和 session-memory 缺失。

---

## 八、整体评价

### 8.1 做得好的方面

1. **regression 诊断质量整体较高**：req-01、req-02、req-04、req-05 的 diagnosis.md 均体现了系统化的问题分析能力，尤其是 req-05 的 chg-01 诊断报告，堪称标杆。
2. **req-05 的知识文档沉淀突出**：`frontend-osd-mapping.md` 将前端消费逻辑与后端接口字段一一对应，是前后端对接类需求的宝贵资产。13 个 OSD 字段修正体现了细致的协议对照能力。
3. **工具层在 req-02 ~ req-04 期间快速成熟**：从几乎空白到建立了完整的 `stage-tools.md`、`selection-guide.md`、工具 catalog，体现了流程自我进化的能力。
4. **req-05 的 done-report 质量高**：明确记录了经验沉淀位置、六层检查结果、改进建议，符合 Harness 工作流的设计目标。

### 8.2 存在的问题

1. **时间戳精度严重不足**：req-01、req-02、req-03 的 `stage_timestamps` 大量为 `00:00:00` 占位符，导致无法计算真实阶段耗时。这与 req-12 记录的改进项一致，但尚未修复。
2. **经验产出不均衡**：req-01、req-03、req-04 几乎没有主动沉淀经验，而 req-02、req-05 承担了大部分经验积累。简单需求不应成为零经验的借口。
3. **session-memory 和 done-report 缺失普遍**：5 个需求中，req-02、req-03 缺少 done-report；session-memory 在 req-02、req-03、req-05 中均未找到。这削弱了流程的可追溯性。
4. **plan.md 在部分需求中缺失**：req-05 的 3 个变更均无 plan.md，对于需要多步执行的变更（如联调测试），缺少计划文档会影响后续复现和审计。
5. **testing / acceptance 阶段的经验文件为空**：`stage/testing.md` 和 `stage/acceptance.md` 仍是空占位符，而 req-01 ~ req-05 中多次涉及 testing 和 acceptance，经验未得到沉淀。
6. **制品仓库（artifacts/requirements/）完全缺失**：req-01 ~ req-05 归档后，根目录均未生成 `artifacts/requirements/{req-id}-{title}.md` 摘要文档。根据 Harness 规范，`harness archive` 应自动产出该制品，但 Yh-platform 项目目前无此目录。

---

## 九、改进建议

### 9.1 立即执行（高优先级）

1. **修复时间戳记录机制**
   - 确保 `harness next` 在推进阶段时写入精确到秒的真实时间戳，禁止 `00:00:00` 占位符。
   - 已在 req-12 中记录，建议尽快排期修复。

2. **强制要求 done-report.md**
   - 无论需求大小，done 阶段必须产出 `done-report.md`。
   - 可在 `context/roles/done.md` 中将 done-report 作为硬门禁检查项。

3. **补齐空模板经验文件**
   - 从 req-01 ~ req-05 的 testing / acceptance 实践中提取教训，填充 `stage/testing.md` 和 `stage/acceptance.md`。
   - 例如：req-05 的"无断言集成测试"、req-01 的"编译环境配置缺失导致测试无法运行"等。

### 9.2 中期优化（中优先级）

4. **规范 session-memory 管理**
   - 每个变更目录下强制保留 `session-memory.md`，即使内容简短。
   - 在 `harness next` 或 ff 模式自动推进前，校验 session-memory 是否已更新。

5. **plan.md 补录机制**
   - 对于从 regression 直接进入 testing 的变更，若变更涉及多步执行（如 req-05 chg-03 联调测试），建议在 testing 阶段开始前补充简版 plan.md。

6. **建立简单需求的经验沉淀最低标准**
   - 即使是单字符语法修复（req-04）或依赖升级（req-03），也应在 done-report 或 session-memory 中记录至少一条可泛化的教训（如"CI 中增加编译检查"已很好，但应同步到 experience 目录）。

7. **补齐制品仓库（artifacts/requirements/）输出**
   - 检查 Yh-platform 的 Harness 版本是否支持 `generate_requirement_artifact` 功能；如不支持，建议升级 harness 工具或手动补录 req-01 ~ req-05 的制品仓库摘要。
   - 在未来需求中，将 `artifacts/requirements/{req-id}-{title}.md` 的生成作为 `harness archive` 后的必检项。

### 9.3 长期建设（低优先级）

7. **经验索引目录化**
   - 当前 `experience/index.md` 是扁平列表，当经验文件增多时检索困难。建议按需求来源、阶段、关键词建立索引，或引入标签系统。
   - 此建议与 req-20 的原始背景一致。

8. **定期审查工具 catalog 的完整性**
   - 当前 catalog 覆盖了 Read、Edit、Bash、Grep、Agent、claude-code-context，但缺少 Write、WebSearch、WebFetch、Skill 等实际频繁使用的工具定义。建议逐步补齐。

---

## 十、审查结论

Yh-platform 项目的 req-01 ~ req-05 在 Harness 工作流的执行上呈现**"两头强、中间弱"**的特征：

- **强**：regression 诊断能力、req-05 的知识文档产出、req-02 ~ req-04 的工具层建设。
- **弱**：时间戳精度、session-memory / done-report 的覆盖、经验产出的均衡性、testing/acceptance 阶段的经验沉淀、制品仓库（artifacts/requirements/）的完全缺失。

req-05 是 5 个需求中综合质量最高的一项，其 `frontend-osd-mapping.md` 和 13 个 OSD 字段修正体现了 Harness 工作流在复杂验收回归场景下的价值。req-03 则是流程执行最薄弱的一环，简单需求不应成为降低流程标准的理由。

**最终判定**：Yh-platform 的 Harness 工作流已具备基本运转能力，但在**状态记录准确性、制品完整性、经验沉淀均衡性**三个方面仍需显著改进。
