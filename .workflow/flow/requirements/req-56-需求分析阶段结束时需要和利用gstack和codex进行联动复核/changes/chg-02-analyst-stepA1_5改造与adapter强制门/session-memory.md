# chg-02 session-memory

## 执行步骤

| Step | 描述 | 状态 |
|------|------|------|
| Step 1 | F1: live `.workflow/context/roles/analyst.md` Step A1.5 4 块改写（头段读字段直跑 / adapter 段头加"必经环节" / 新增退出门 / fallback 改名 escape） | ✅ |
| Step 2 | F2: mirror `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md` cp 同步 | ✅ |
| Step 3.1 | diff -q live mirror → silent | ✅ |
| Step 3.2 | grep `必经环节` 命中 2（≥1） | ✅ |
| Step 3.3 | grep `请选择.*office-hours\|是否.*office-hours` 命中 0（offer 已删） | ✅ |
| Step 3.4 | grep `office_hours_mode` 命中 7（≥1） | ✅ |
| Step 4 | harness validate --human-docs exit 0；--contract artifact-placement exit 0 | ✅ |

## 关键决策点

1. **escape vs fallback 命名**：原 Step A1.5.fallback 子段重命名为 Step A1.5.escape，因 mode=fallback 现已由 chg-01 CLI 入口决定，analyst 内部不再做 fallback 决策；保留场景 3（用户/主 agent 拒派发）作 escape hatch，与"用户后悔想换模式 → harness regression 重置"路径配合。
2. **adapter 标签强化**：段头加 `**必经环节**` 字面 + 段尾加退出门（双 validate 双绿才能离开 Step A1.5），防止 design doc 直接当 requirement.md 绕道。
3. **mode 切换 CLI 不在本 req**：用户跑了 office-hours 但中途想转 fallback 的场景，记入 sug 候选（recovery hint 里写明走 regression）。

## 测试结果

文档层 chg，无新增单元测试。靠 grep / diff 静态校验 + 后续 chg-03 dogfood TC 端到端联动覆盖。

- chg-02 plan.md §5 的 7 条 lint 命令全 PASS（验证脚本输出已留痕）
- live ↔ mirror diff silent
- harness validate --human-docs / --contract artifact-placement 双 exit 0

## 待处理捕获问题

- 无（mode 切换 CLI 已识别为 sug 候选，不在 req-56 范围）

## 汇报

主 agent 直接落地（文档层 2 文件改动按 WORKFLOW.md 降级"微调可主 agent 直接做"）；本 chg 无 default-pick 决策需汇报（"无"）。

本阶段已结束。
