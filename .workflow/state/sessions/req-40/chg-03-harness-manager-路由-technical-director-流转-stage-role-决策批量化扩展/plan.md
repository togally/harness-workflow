# Change Plan — chg-03（harness-manager 路由 + technical-director 流转 + stage-role 决策批量化扩展）

## 1. Development Steps

### Step 1: 改写 `harness-manager.md`（live）

- 定位 §3.4（工件管理类 → 加载对应 stage 角色）表：
  - 把 `harness requirement` 行的 "处理逻辑" 列从 `创建需求，加载 requirement-review 角色` 改为 `创建需求，加载 analyst 角色（原 requirement-review，req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））合并）`；
  - 把 `harness change` 行的 "处理逻辑" 列从 `创建变更，加载 planning 角色` 改为 `创建变更，加载 analyst 角色（原 planning，req-40 合并）`；
- 在 §3.6（派发 Subagent）末尾追加 §3.6.1 小节（约 15 行）：
  ```
  #### 3.6.1 req_review / planning 统一派发 analyst（req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md）））

  - `req_review` stage 与 `planning` stage 的派发目标统一为 `analyst` 角色（role_key=analyst，model=opus）；
  - default-pick HM-1 = A：requirement_review PASS 后 technical-director **默认让 analyst 在同一会话续跑 planning 任务**（不新开 subagent 会话），以保持上下文连贯；退化路径 B（两次派发 analyst）保留作 fallback，当上下文达到 70% 阈值需 /compact 时使用；
  - 派发说明 model 透出：`派发 analyst（Opus 4.7）执行需求澄清 + 变更拆分`（对人文案 Opus 大写，briefing / yaml 保持 lowercase）；
  - legacy role_key `requirement-review` / `planning` 仍在 `role-model-map.yaml` 保留作别名指 opus（chg-02 落地），兼容归档引用。
  ```

### Step 2: 改写 `technical-director.md`（live）

- 定位 `### Step 6: 处理阶段流转` 段，在其末尾追加 `#### 6.2 requirement_review → planning 自动静默推进（req-40）` 子段（约 20 行）：
  ```
  #### 6.2 requirement_review → planning 自动静默推进（req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md）））

  - analyst 在 requirement_review 完成 requirement.md 产出并取得用户拍板后，technical-director **不再邀请用户对 planning 结果决策**；
  - technical-director 直接推进 stage → planning（更新 runtime.yaml），由 analyst 在同一会话续跑变更拆分（default-pick HM-1 = A，harness-manager §3.6.1）；
  - analyst 在 planning 完成 change.md + plan.md 全集产出后，batched-report 一次给用户（"需求 + 推荐拆分"合并报告），用户对此联合产出拍板一次即进入 ready_for_execution；
  - **保留 escape hatch**：用户在 requirement_review 或 planning 任一时刻明确说出触发词 `我要自拆` / `我自己拆` / `让我自己拆` / `我拆 chg` 之一时，analyst 退化为只产 `requirement.md` + §5 推荐拆分，不产 change.md / plan.md；用户自己敲 `harness change "<title>"` 手动拆分；
  - 与 base-role 硬门禁四（同阶段不打断 + 例外三类）+ 硬门禁七（周转汇报 Ra/Rb/Rc）**并列生效**，不替代任何一条既有硬门禁。
  ```

### Step 3: 改写 `stage-role.md`（live）

- 定位 `### 硬门禁：同阶段不打断 + default-pick 记录（req-31 / chg-05）` 段，在其末尾追加 `#### stage 流转点豁免子条款（req-40）` 子段（约 15 行）：
  ```
  #### stage 流转点豁免子条款（req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md）））

  - 原协议（req-31（角色功能优化整合与交互精简）/ chg-05（S-E 决策批量化协议））止于同一 stage 内争议点；本子条款把豁免面扩展到**相邻同类型 stage 的流转点**：
    - `requirement_review → planning` 流转点**默认静默**：analyst 自主推进 chg 拆分，不邀用户对"是否进入 planning"决策（default-pick 直接按 HM-1 = A）；
    - `planning → ready_for_execution` **保留用户拍板**（但此处拍板对象是"需求 + 推荐拆分"合并产物）；
  - 与 base-role 硬门禁四（例外条款 i/ii/iii 数据丢失 / 不可回滚 / 合规）+ 硬门禁七（Ra/Rb/Rc）**并列生效**，不替代；
  - 豁免仅适用于 analyst 承载的两 stage（req-40 方向 C）；其他 stage 流转（executing → testing / testing → acceptance 等）不在本条款豁免面内。
  ```

### Step 4: 同步 mirror 三文件

- `cp .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md`；
- `cp .workflow/context/roles/directors/technical-director.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/directors/technical-director.md`；
- `cp .workflow/context/roles/stage-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md`；
- 跑三次 `diff -rq` 确认无输出。

### Step 5: 自检 + 交接

- 跑 AC-4 / AC-5 / AC-6 的 grep 断言（见 2.1）；
- 更新 chg-03 `session-memory.md`：default-pick HM-1 = A / C-1 = 按字面 escape hatch 匹配；
- 更新 `artifacts/main/requirements/req-40-.../chg-03-变更简报.md`（≤ 1 页）；
- 按硬门禁二追加 `action-log.md`。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `grep -n "analyst" .workflow/context/roles/harness-manager.md | wc -l` ≥ 3（§3.4 两行 + §3.6.1 至少一处）
- `grep -q "3.6.1" .workflow/context/roles/harness-manager.md`（新小节锚）
- `grep -q "req_review.*planning\|requirement_review.*planning" .workflow/context/roles/harness-manager.md`（路由描述）
- `grep -q "requirement_review → planning 自动\|自动静默推进" .workflow/context/roles/directors/technical-director.md`
- `grep -q "我要自拆\|我自己拆" .workflow/context/roles/directors/technical-director.md`（escape hatch）
- `grep -q "stage 流转点豁免\|相邻同类型 stage" .workflow/context/roles/stage-role.md`
- `grep -q "req-40" .workflow/context/roles/stage-role.md`（溯源）
- `diff -rq .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md`（无输出）
- `diff -rq .workflow/context/roles/directors/technical-director.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/directors/technical-director.md`（无输出）
- `diff -rq .workflow/context/roles/stage-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md`（无输出）

### 2.2 Manual smoke / integration verification

- 肉眼复核 harness-manager.md §3.4 表格两行改写、§3.6.1 小节文字；
- 肉眼复核 technical-director.md Step 6.2 子段语义（"不邀用户" + escape hatch 4 触发词）；
- 肉眼复核 stage-role.md 扩展子段与原"硬门禁：同阶段不打断 + default-pick 记录"段衔接，无语义冲突；
- 对照 base-role 硬门禁四例外条款 + 硬门禁七 Rc 核对"并列生效"措辞。

### 2.3 AC Mapping

- AC-4（harness-manager 路由调整） -> Step 1 + Step 4 + 2.1 grep/diff 断言 + 2.2 §3.4 / §3.6.1 肉眼复核；
- AC-5（technical-director 自动流转） -> Step 2 + Step 4 + 2.1 grep 断言 + 2.2 escape hatch 触发词复核；
- AC-6（决策批量化扩展到流转点） -> Step 3 + Step 4 + 2.1 grep 断言 + 2.2 并列生效措辞核对。

## 3. Dependencies & Execution Order

- **前置依赖**：chg-01（analyst.md 已存在）+ chg-02（role-model-map analyst key + legacy 别名已注册）；
- **后置依赖**：chg-04（pytest 断言要检查 harness-manager.md 含 analyst 字面）+ chg-05（mirror diff 全量断言）；
- **本 chg 内部顺序**：Step 1 → Step 2 → Step 3 → Step 4 → Step 5 强制串行；三文件改写顺序 harness-manager → technical-director → stage-role（从派发入口到编排协议到规约层，逐层外推）；mirror 同步放在三文件 live 全部改完后一次性批量。
