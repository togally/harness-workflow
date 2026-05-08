---
id: chg-05
title: "dogfood 活证（用下一个真实需求端到端验证融合入口）"
parent_requirement: req-55
created_at: 2026-05-07
operation_type: change
stage: analysis
---

## Plan Steps

> 第 8 轮重写：本 chg 在 req-55 周期内仅做"deferred 承诺 + retro 模板段预埋"两件事；真活证由下一个真实 `/harness-requirement` 触发时由其 analyst 自动兑现。
> 本 plan 的 Step 1~3 在 req-55 executing stage 内由 executing 角色执行；Step 4~6 是 deferred 触发后由该 req 的 analyst 在其周期内执行（不在 req-55 周期内）。

### req-55 周期内（本 chg 执行段）

#### Step 1: 在 analyst 经验文件预埋 retro 模板段

- 文件：`artifacts/project/experience/roles/analyst.md`（如不存在则创建；存在则追加）
- 内容（追加到末尾）：

  ```markdown
  ## gstack-harness 融合 retro（首次填写：req-56+）

  > 占位段：本节由下一个真实 `/harness-requirement` 触发时由其 analyst 在 chg-02 adapter SOP 完成后回填。回填时把"req-56+"替换为实际触发的 req-id。

  ### 1. 调 /office-hours 的姿势
  - 触发协议路径 α 实操经验（subagent 提示主 agent → 用户跑 → 反馈 path → analyst 跑 adapter）
  - 实际触发是否流畅 / 用户疑惑点 / 反馈 path 时是否正确

  ### 2. adapter 章节 mapping 实操细节
  - 哪些段 mapping trivial（如 Success Criteria → Acceptance Criteria）
  - 哪些段需人工裁剪（如 Recommended Approach 多技术细节）
  - 哪些段映射不到位（mapping 表 fallback 是否够用）
  - 是否需要反馈给 chg-02 修订 adapter mapping 表

  ### 3. fallback 触发场景
  - 本次是否触发 fallback？
  - 假设性观察："如果用户拒跑 /office-hours，体验如何"

  ### 4. 多余段处理选择
  - 本次按 adapter SOP 全保留追加到 Office Hours Notes？还是部分裁剪？
  - 保留量是否影响 requirement.md 可读性
  - 给后续 req 的改进方向
  ```

#### Step 2: 同步 retro 模板段到 scaffold_v2 mirror（硬门禁五）

- 文件：`src/harness_workflow/assets/scaffold_v2/artifacts/project/experience/roles/analyst.md`
  - 如 scaffold_v2 路径下尚无 `artifacts/project/experience/roles/`，先创建目录骨架
  - 把 Step 1 同样的模板段写入 scaffold_v2 镜像（保持新项目首次 install 即包含此模板）
- 自检：`diff -q live vs scaffold_v2`（应清洁）

注：本 step 与 chg-04 已 mirror 范围有重叠——chg-04 mirror 仅含 chg-02 修改的三个文件；本 step 是 chg-05 自己 mirror 自己产物（retro 模板段），不重叠于 chg-04 已落地。

#### Step 3: 在本 chg session-memory.md 文档化 deferred 承诺

- 文件：`.workflow/flow/requirements/req-55-.../changes/chg-05-dogfood-活证/session-memory.md`（chg 局部）
- 内容关键节：
  - **deferred 承诺**：本 chg 真活证由下一个真实 `/harness-requirement` 触发时由其 analyst 兑现
  - **触发证据预留段**：`## 触发证据（待下一个真实 req 回填）`，含字段
    ```markdown
    - trigger_req_id: <待回填>
    - trigger_date: <待回填>
    - design_doc_path: <待回填>
    - 触发链耗时（用户视角）: <待回填>
    - 卡点 / 摩擦: <待回填>
    - retro 四点已落 analyst 经验: 是 / 否（应是）
    ```
  - **回填合约**：下一个真实 req 的 analyst 在其 Step A1.5.adapter 完成后，必须：
    1. 把 retro 四点真实内容回填到 `artifacts/project/experience/roles/analyst.md` 的「## gstack-harness 融合 retro」段（替换占位 sub-section 内容）
    2. 在本 chg-05 session-memory.md「触发证据」段追加一条记录（含上述 6 字段）
    3. 在该 req 自己的 session-memory.md 留一行 cross-link 指向 chg-05 触发证据条目

### 下一个真实 req 触发后（deferred 段，不在 req-55 周期内执行）

#### Step 4: 用户调 `/harness-requirement "<新需求>"` 启动 req-56+

- 触发方：用户
- 行为：harness-manager 解析 → 创建 req 骨架 → 派发 analyst（与本 req-55 流程相同，不再是手工填）
- 关键差异：analyst 的 Step A1.5 触发协议（chg-02 落地）现在是默认 SOP

#### Step 5: 该 req 的 analyst 自动跑融合入口链

- analyst 检测 `runtime.yaml.gstack_status.agent_kind_compatible`
- 为 true → 主动**提示**用户："本 req 已配置 analyst → /office-hours 强映射；请在 Claude Code 主对话执行 /office-hours，主题输入..."
- 用户响应提示，跑 /office-hours
- 用户反馈 path
- analyst 跑 chg-02 落地的 adapter SOP，重组覆盖该 req 的 requirement.md

#### Step 6: 该 req 的 analyst 回填 chg-05 deferred 承诺

- 把 retro 四点真实内容写入 `artifacts/project/experience/roles/analyst.md`（替换占位 sub-section）
- 在本 chg-05 session-memory.md 追加触发证据条目
- 在该 req 自己的 session-memory.md 加 cross-link

## Verification Checklist

> 在 req-55 周期内仅 √ Step 1~3；Step 4~6 由下一个真实 req 兑现，归该 req 验收。

- [ ] AC-05 子项 1（req-55 内）：retro 模板段已写入 `artifacts/project/experience/roles/analyst.md`
- [ ] AC-05 子项 2（req-55 内）：retro 模板段已 mirror 到 scaffold_v2
- [ ] AC-05 子项 3（req-55 内）：chg-05 session-memory.md 含 deferred 承诺 + 触发证据预留段 + 回填合约
- [ ] AC-05 子项 4（deferred）：下一个真实 req 触发时 analyst 自动跑融合入口链 + 回填 retro + 触发证据

## Open Questions

- 如多人协作、多个 req 同时进行 → 哪个真实 req 兑现 chg-05？答：**第一个**触发 analyst Step A1.5 的 req（不限定 req-id）；后续 req 复用同一 retro 段（追加新 sub-section 而非覆盖）。
- retro 模板段如果用户提前在 req-56 之外的场景（如直接编辑文件）填了内容 → 是否视为 chg-05 兑现？答：不视为；必须由 `/harness-requirement` 入口触发的 analyst 自动回填，才是融合机制端到端验证；用户手填只是文档预备，不构成活证。
