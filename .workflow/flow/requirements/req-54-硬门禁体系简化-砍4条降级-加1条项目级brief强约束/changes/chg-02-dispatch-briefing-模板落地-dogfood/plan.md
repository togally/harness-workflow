---
id: chg-02
title: "dispatch-briefing-模板落地-dogfood"
parent_req: req-54
operation_type: plan
---

## 1. Scope（精确文件 + 行号）

### F1：`.workflow/context/roles/harness-manager.md`（live + mirror）

- §3.6.2「按硬门禁八 brief 项目级加载链」（chg-01 已落占位）正文**完整化**：

  - 1.1 在子条款顶部加 1 行「**适用范围**：所有派发 subagent 的上级（含 harness-manager / technical-director / 各 stage 主控者 / 主 agent）」。
  - 1.2 在 boilerplate 字面段之前加段落说明：「派发任意 subagent 时，briefing 正文 **必须** 显式注入下列 boilerplate 字面段（不得省略、不得改写、不得替换为概念引用）：」
  - 1.3 boilerplate 字面段（chg-01 已写）保留不动。
  - 1.4 scope 枚举段：
    ```
    ### scope 枚举（派发者按 subagent 任务挑选最相关的 1~3 个）

    - `constraints`（项目级约束 / 规则）
    - `experience-roles`（角色经验，如 analyst / executing / testing 实战教训）
    - `experience-tool`（工具经验）
    - `experience-risk`（风险经验）
    - `experience-regression`（regression 教训）
    - `experience-stage`（stage 流转经验）
    - `tools`（工具目录）
    ```
  - 1.5 违反判定段：
    ```
    ### 违反判定 grep

    - `grep "artifacts/project/" <briefing-text>` 命中 0 行 → 硬门禁八违反；
    - `grep "Step 7.6" <briefing-text>` 命中 0 行 → 硬门禁八违反；
    - reviewer 阶段 checklist + done 六层回顾 State 层兜底拦截。
    ```
  - 1.6 与硬门禁九闭环说明段：
    ```
    ### 与硬门禁九的闭环

    - 硬门禁八（事前 brief） + 硬门禁九（事后核查）首尾相接；
    - 上级未 brief（违反硬门禁八） + 上级未核查（违反硬门禁九） = 双违反，与 subagent 串联失职。
    ```

- §3.6「派发协议」-「构建 briefing」清单（约 L302-L313）追加一项：
  - 在现有「3. 上下文链 (context_chain)」后插入：
    ```
    3.5. **项目级加载链提示**（base-role 硬门禁八，req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束））：briefing 必含 §3.6.2 boilerplate 字面段 + 当前 scope 字段（取自 §3.6.2 scope 枚举）。
    ```

### F2：`.workflow/context/roles/base-role.md`（live + mirror）

- 「Subagent 嵌套调用规则」段（约 L273）的「**派发协议**」清单（L289-L309 之间）追加第 5 项：
  ```
  5. **项目级加载链提示**（硬门禁八，req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束））：briefing 必显式包含 role-loading-protocol.md Step 7.6 / 7.6.1 引用 + boilerplate 字面段（路径 `artifacts/project/{constraints,experience,tools}/` + 首条输出加载数自检要求）+ scope 字段。
  ```

### F3：dogfood 自证（本会话内主 agent 行为，非文件改动）

- 主 agent（technical-director / opus）在 chg-02 实施完成后，派发 chg-03 subagent 时，briefing 正文必含：
  - boilerplate 字面段（artifacts/project/ + Step 7.6 / 7.6.1）
  - scope 字段（chg-03 推荐 scope = experience-stage + experience-tool）
- 本 dogfood 行为由 done 阶段交付总结记录「硬门禁八 dogfood 自证（含 N 次派发）」。

### F4 / F5：mirror 同步

- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md`（同 F2）
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md`（同 F1）

## 2. 实施步骤

1. **Step 1**：完整化 harness-manager.md §3.6.2（live + mirror）— 顶部适用范围 + 段落说明 + scope 枚举 + 违反判定 + 闭环说明 5 块。
2. **Step 2**：harness-manager.md §3.6 「构建 briefing」清单插入第 3.5 项（live + mirror）。
3. **Step 3**：base-role.md 「Subagent 嵌套调用规则」-「派发协议」清单追加第 5 项（live + mirror）。
4. **Step 4**：自检：
   - grep `^### scope 枚举` harness-manager.md → 命中 1 行
   - grep `^### 违反判定 grep` harness-manager.md → 命中 1 行
   - grep `^### 与硬门禁九的闭环` harness-manager.md → 命中 1 行
   - grep `^5\\. \\*\\*项目级加载链提示\\*\\*` base-role.md → 命中 1 行
   - diff -q 2 mirror 文件全 silent
5. **Step 5**：dogfood—主 agent 派发 chg-03 subagent 时观察 briefing 字面（手动 / lint）。
6. **Step 6**：跑 `harness validate --contract all` exit 0。

## 4. 测试用例设计

> regression_scope: targeted（chg-02 仅文档级补强 chg-01 占位 + 派发协议清单一项；不动 src / 不动 tests / 不动 contract 定义）
> 波及接口清单（git diff --name-only 自动生成 + 人工补全）：
> - .workflow/context/roles/harness-manager.md（§3.6 / §3.6.2）
> - .workflow/context/roles/base-role.md（Subagent 嵌套调用规则 - 派发协议清单）
> - src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md
> - src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md
> - 间接波及：所有派发 subagent 的代码路径（仅文档约束，运行时不强校验，靠 reviewer / done 兜底）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | grep `^### scope 枚举` harness-manager.md（live + mirror） | 各命中 1 行 | AC-05 | P0 |
| TC-02 | grep `^### 违反判定 grep` harness-manager.md（live + mirror） | 各命中 1 行 | AC-05 | P0 |
| TC-03 | grep `^### 与硬门禁九的闭环` harness-manager.md（live + mirror） | 各命中 1 行 | AC-05 | P0 |
| TC-04 | grep `项目级加载链提示\\|硬门禁八` base-role.md「派发协议」清单（live + mirror，约 L289-L309 区段） | 各命中 ≥ 1 行 | AC-04 | P0 |
| TC-05 | subprocess `diff -rq` 2 对 live ↔ mirror（base-role.md / harness-manager.md） | returncode == 0（2 对全 silent） | AC-07（chg-02 子集） | P0 |
| TC-06 | dogfood：本会话 done 阶段交付总结字面 grep `硬门禁八 dogfood 自证` | 命中 ≥ 1 行（done 产出后） | AC-08 | P0 |

> TC-06 由 done 阶段产出后 lint，本 chg 实施时不直接断言；chg-03 lint 套件覆盖 TC-01~TC-05（自动化），TC-06 由 done 六层回顾验收。

## 5. 验收 lint 命令字面

```bash
# AC-05：harness-manager.md §3.6.2 完整化
grep -c '^### scope 枚举' .workflow/context/roles/harness-manager.md   # 期望 == 1
grep -c '^### 违反判定 grep' .workflow/context/roles/harness-manager.md   # 期望 == 1
grep -c '^### 与硬门禁九的闭环' .workflow/context/roles/harness-manager.md   # 期望 == 1
grep -c '^### scope 枚举' src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md   # 期望 == 1
grep -c '^### 违反判定 grep' src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md   # 期望 == 1
grep -c '^### 与硬门禁九的闭环' src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md   # 期望 == 1

# AC-04（chg-02 子集）：base-role.md 派发协议清单第 5 项
grep -cE '^5\. \*\*项目级加载链提示\*\*' .workflow/context/roles/base-role.md   # 期望 == 1
grep -cE '^5\. \*\*项目级加载链提示\*\*' src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md   # 期望 == 1

# AC-07（chg-02 子集）：mirror diff
diff -q .workflow/context/roles/base-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md
diff -q .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md

# AC-08：dogfood（done 阶段产出后）
grep -c '硬门禁八 dogfood 自证' artifacts/main/requirements/req-54-硬门禁体系简化-砍4条降级-加1条项目级brief强约束/交付总结.md   # 期望 ≥ 1
```

## 6. scaffold_v2 mirror 同步清单

| Live 文件 | Mirror 路径 | 同步语义 |
|-----------|-----------|---------|
| `.workflow/context/roles/base-role.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md` | 全文一致（含 chg-01 + chg-02 改动） |
| `.workflow/context/roles/harness-manager.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` | 全文一致（含 chg-01 + chg-02 改动） |

实施约束：2 对必须**同 commit** 同步落地，违反硬门禁五。
