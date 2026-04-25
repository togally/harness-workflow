# Change

## 1. Title

harness-manager 路由 + technical-director 流转 + stage-role 决策批量化扩展

## 2. Goal

- 三文件协同改写：`harness-manager.md` 把 req_review / planning 两 stage 的派发目标改为 analyst；`technical-director.md` 新增"requirement_review → planning 自动静默推进"子条款 + escape hatch 声明；`stage-role.md` 决策批量化协议段新增"stage 流转点豁免"子条款。三者共同把"用户只拍板一次需求 + chg 拆分 agent 自主"的方向 C 精神落到编排层。

## 3. Requirement

- `req-40`（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））

## 4. Scope

### Included

- **`.workflow/context/roles/harness-manager.md`** 改写：
  - §3.2 会话控制类 → 主 agent（technical-director）执行表无需改（不涉及 req_review / planning 派发）；
  - §3.4 工件管理类加载对应 stage 角色表改写两行：
    - `harness requirement` 处理逻辑：`创建需求，加载 analyst 角色（原 requirement-review，req-40 合并）`；
    - `harness change` 处理逻辑：`创建变更，加载 analyst 角色（原 planning，req-40 合并）`；
  - §3.6 派发 Subagent 协议段：在 Step 2.5 旁加一小节 "§3.6.1 req_review 与 planning 派发到 analyst"，说明两 stage 统一派发目标为 analyst（role_key=analyst），model 透出为 `analyst / opus`；
  - default-pick HM-1 = A（同一会话续跑）文字落地：在 §3.6.1 说明"requirement_review PASS 后 technical-director 默认让 analyst 在**同一会话**续跑 planning 任务（不新开 subagent 会话），退化路径 B（两次派发 analyst）保留作 fallback"；
- **`.workflow/context/roles/directors/technical-director.md`** 改写：
  - Step 6 处理阶段流转段新增子条款"6.2 requirement_review → planning 自动静默推进（req-40）"：
    - 明示"用户对 requirement 拍板后，technical-director **不邀**用户对 planning 结果决策；analyst 自主推进 chg 拆分至 ready_for_execution"；
    - 明示 escape hatch："若用户明确说出 '我要自拆' / '我自己拆' / '让我自己拆' / '我拆 chg' 等等价触发词，analyst 退化为只产 `requirement.md` + §5 推荐拆分，**不产** change.md / plan.md；用户自己敲 `harness change` 手动拆分"；
    - 与硬门禁四（base-role）/ 硬门禁七 Rc（周转汇报必报本阶段已结束）**并列生效**，不替代；
- **`.workflow/context/roles/stage-role.md`** 改写：
  - "硬门禁：同阶段不打断 + default-pick 记录"段尾部新增子段"### stage 流转点豁免子条款（req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md）））"：
    - 原协议：同一 stage 内 default-pick 推进，stage 流转前 batched-report；
    - 扩展：**相邻同类型 stage（req_review + planning）之间的流转点**同样豁免打断，analyst 自主推进；
    - 保留对"ready_for_execution 前让用户拍板"的不豁免（用户仍拍一次，只是对象变为"需求 + 推荐拆分合并"）；
- **mirror 同步** 三文件至 scaffold_v2 对应路径。
- 涉及文件路径：
  - live：`.workflow/context/roles/harness-manager.md` + `.workflow/context/roles/directors/technical-director.md` + `.workflow/context/roles/stage-role.md`
  - mirror：`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` + `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/directors/technical-director.md` + `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md`

### Excluded

- **不改** `analyst.md`（归属 chg-01）；
- **不改** `index.md` / `role-model-map.yaml`（归属 chg-02）；
- **不改** 其他 stage 角色文件（executing / testing / acceptance / regression / done 的流转条款）；
- **不改** CLI 源码（`harness-manager.md` 文字改写不涉及 Python 代码）；
- **不新增** pytest（归属 chg-04）。

## 5. Acceptance

- Covers requirement.md **AC-4**（harness-manager 路由调整）：
  - `grep -n "analyst" .workflow/context/roles/harness-manager.md` 至少 2 处命中（§3.4 两行 + §3.6.1）；
  - §3.4 `harness requirement` 行派发目标含 `analyst` 字面；
  - §3.4 `harness change` 行派发目标含 `analyst` 字面；
  - `diff -rq .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` 无输出。
- Covers requirement.md **AC-5**（technical-director 自动流转）：
  - `grep -q "requirement_review → planning 自动" .workflow/context/roles/directors/technical-director.md` 或等价表述命中；
  - `grep -q "我要自拆\|我自己拆\|escape hatch" .workflow/context/roles/directors/technical-director.md` 至少 1 处命中；
  - `diff -rq .workflow/context/roles/directors/technical-director.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/directors/technical-director.md` 无输出。
- Covers requirement.md **AC-6**（决策批量化扩展到流转点）：
  - `grep -q "stage 流转点豁免\|相邻同类型 stage" .workflow/context/roles/stage-role.md` 命中；
  - `grep -q "req-40" .workflow/context/roles/stage-role.md` 命中（溯源留痕）；
  - `diff -rq .workflow/context/roles/stage-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md` 无输出。

## 6. Risks

- **风险 1：派发改写与现有 `role-loading-protocol.md` 的 role_key 校验机制冲突**。缓解：chg-02 已保留 legacy key 作别名指 opus；harness-manager 派发说明改写后，stage → role_key 的映射由"req_review → requirement-review"改为"req_review → analyst"，但 role-model-map 同时保留两 key 兼容。reviewer / chg-04 pytest 断言覆盖。
- **风险 2：technical-director 自动静默推进破坏 `harness next` 既有交互**。缓解：本 chg 只改"文字描述 + 编排协议"，不改 `harness next` CLI 源码；既有 `harness next` 用户手动调用路径仍有效；auto-advance 只是在 subagent 返回 PASS 后 director 不邀用户，继续派发 planning subagent。
- **风险 3：stage-role 扩展条款与 base-role 硬门禁四（例外清单 i/ii/iii）冲突**。缓解：明示"并列生效不替代"；数据丢失 / 不可回滚 / 合规三类例外仍打断。
- **风险 4：mirror 漏同步触发硬门禁五**。缓解：三文件 live 改完立刻 cp 到 mirror + diff -rq 自检。
- **风险 5：escape hatch 触发词识别误伤**。缓解：触发词用精确字面匹配 4 个（"我要自拆" / "我自己拆" / "让我自己拆" / "我拆 chg"）；模糊语义由 technical-director 判断时走 default-pick C-1 = 按字面，不臆测。
