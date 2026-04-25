# Change Plan — chg-05（dogfood 活证 + 契约 7 自证 + mirror diff 全量断言）

## 1. Development Steps

### Step 1: 前置校验（chg-01~chg-04 全部 PASS）

- 确认 chg-01 / chg-02 / chg-03 / chg-04 的 session-memory.md 全部标记完成；
- 跑 `diff -rq` 对 6 个规约文件快速自检，若任何一处有输出则 ABORT（退回 chg-03 / chg-04 executing）。

### Step 2: dogfood 活证采集（default-pick DF-1 = A 最小闭环）

- 在 req-40 executing 阶段（本 chg 被执行时）由 analyst 承接 chg-05 自身剩余动作；
- 采集以下 5 个关键节点并写入 `.workflow/state/sessions/req-40/session-memory.md` 新段 `## dogfood 活证节点清单（chg-05 封存）`：
  1. **t0**：chg-01 executing 启动时刻（读 action-log.md 最早 chg-01 写入时间）；
  2. **t1**：analyst 角色首次自我介绍文本（在 chg-05 executing subagent 启动时按硬门禁三自报 `我是 分析师（analyst / opus），接下来我将...`，本行完整拷贝进 session-memory）；
  3. **t2**：假设在下一新 req（或 req-40 后续）调用 analyst 时的 requirement_review PASS 时间 + 同一会话续跑 planning 的时间戳差（演示"无用户介入"的流转点）；
  4. **t3**：batched-report 样本引用（从 analyst 交接时的 stage-role 统一精简汇报模板输出中摘取"产出 + 状态 + 开放问题 + 本阶段已结束"四字段文本段）；
  5. **t4**：dogfood 结论（三选一：PASS / 发现轻微瑕疵（记 chg-06） / 明显退化（记 chg-06 + 建议开 reg-02 回调方向 B））；
- **default-pick 清单**（若触发）完整抄录；若无触发则写"无"。

### Step 3: 契约 7 自证扫描

- 跑命令：
  ```bash
  grep -rnE "(req|chg|sug|bugfix|reg)-[0-9]+" \
      artifacts/main/requirements/req-40-阶段合并与用户介入窄化-方向-c-角色合并-analyst-md/ \
      .workflow/state/sessions/req-40/ \
      --include="*.md"
  ```
- 把命中行清单保存到 session-memory 临时块；
- 对每个**首次出现**的 id（同一文档内同一 id 第二次起豁免）核对紧随有 `（...）` / `— ...` 描述或行内已有 title；
- 批量列举场景（DAG / 进度表 / 跨 chg 索引）每条 id 均按首次处理；
- 若 `harness validate --contract 7` CLI 可用则直接调用，优先采用；
- 期望：违规命中数 = 0；若 ≠ 0 则 ABORT 并列出违规行，退回对应 chg executing 修正。

### Step 4: mirror diff 全量断言

- 跑 7 条 `diff -rq` 命令（见 change.md §4 Included 列表）；
- 全部无输出即 PASS；任一有输出则 ABORT + 记录差异文件 + 回退到对应 chg 的 mirror sync 步骤补做。

### Step 5: 生成 chg-05 自证报告

- 在 session-memory.md `## dogfood 活证节点清单（chg-05 封存）` 段后追加 `## chg-05 自证报告` 段，三子段：
  1. dogfood 5 节点摘要（t0~t4）；
  2. 契约 7 扫描结果（命中行数 / 违规数 / 若有违规的处理记录）；
  3. mirror diff 7 文件结果（全部 PASS / 若有差异的修正记录）；
- 更新 `artifacts/main/requirements/req-40-.../chg-05-变更简报.md`；
- 按硬门禁二追加 `action-log.md`。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `grep -q "dogfood 活证节点清单" .workflow/state/sessions/req-40/session-memory.md`（AC-8）
- `grep -q "我是 *分析师\|analyst / opus" .workflow/state/sessions/req-40/session-memory.md`（AC-8 自报文本）
- 契约 7 扫描违规数 = 0（AC-10）
- 7 条 mirror diff 无输出（AC-9）
- `grep -q "chg-05 自证报告" .workflow/state/sessions/req-40/session-memory.md`

### 2.2 Manual smoke / integration verification

- 人工核对 session-memory.md 新增两段的语义连贯性（dogfood 节点 + 自证报告）；
- 人工抽读 3-5 个 req-40 scope 内 .md 文件，对比契约 7 扫描结果，确认无漏报；
- 人工抽读 scaffold_v2 mirror 对应的 2-3 个文件，与 live 肉眼对比，确认 diff -rq 未漏报；
- 对 AC-8 / AC-9 / AC-10 逐条过一遍判据。

### 2.3 AC Mapping

- AC-8（dogfood 活证） -> Step 2 + Step 5 + 2.1 grep 节点清单 + 2.2 语义核对；
- AC-9（scaffold_v2 mirror 跨文件 diff 归零） -> Step 4 + 2.1 7 条 diff -rq + 2.2 肉眼对比；
- AC-10（契约 7 + 硬门禁六自证） -> Step 3 + 2.1 扫描违规数 = 0 + 2.2 抽读核对。

## 3. Dependencies & Execution Order

- **前置依赖**：chg-01 + chg-02 + chg-03 + chg-04 全部 PASS（本 chg 是收束自证，不能前置）；
- **后置依赖**：chg-06（专业化反馈模板可消费本 chg 的 t4 dogfood 结论作为"首次运行质量"输入）；
- **与 chg-04 关系**：default-pick D-1 = B 串行（chg-04 → chg-05），理由：静态证据（pytest）先行，动态证据（dogfood）后置，降低上下文负荷 + 便于 mirror diff 单点校验；
- **本 chg 内部顺序**：Step 1 → Step 2 → Step 3 → Step 4 → Step 5 强制串行；Step 3 / Step 4 均有 ABORT 回退条件，不能忽略。
