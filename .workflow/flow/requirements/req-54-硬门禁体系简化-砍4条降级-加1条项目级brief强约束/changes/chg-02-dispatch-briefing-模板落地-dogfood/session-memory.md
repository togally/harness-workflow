# Session Memory — chg-02（dispatch-briefing-模板落地-dogfood）

## 1. Current Goal

把 chg-01 在 base-role.md / harness-manager.md 落下的「硬门禁八 brief 项目级加载链」**实操化**：boilerplate 字面段 + scope 枚举 + 违反判定 + 与硬门禁九闭环说明；本会话 dogfood 自证。

## 2. Context Chain

- Level 0: 主 agent（technical-director / opus）→ analysis stage
- Level 1: Subagent-L1（analyst / opus）→ Phase 1 + 2 + 3 一气完成
- Level 2: chg-02 待执行（依赖 chg-01 落地后）

## 3. 关键决策

- 硬门禁八落实采用「文档约束 + reviewer / done 兜底拦截」路径，**不**写 helper / 不写运行时强校验（避免引入 src 改动 + tests 改动；与 OQ Out-of-scope 一致）。
- briefing 字段命名：`project_level_loading_brief`（对人 boilerplate 字面段，不引入 yaml schema）。
- dogfood 自证落 done 阶段交付总结一行（非本 chg 直接产物）。

## 4. default-pick 决策清单（本 chg）

- 无（OQ Verdicts 已锁定，无新增 default-pick）。

## 5. Next Steps

- chg-02 已完成：harness-manager.md §3.6.2 完整化（scope 枚举 + 违反判定 + 与硬门禁九闭环）+ §3.6 派发协议第 3.5 项 + base-role.md 派发协议第 5 项
- chg-03 接手测试 lint

## Lint 结果（chg-02 验收）

```
grep '^### scope 枚举' harness-manager.md: 1 ✅
grep '#### 3.6.2' harness-manager.md: 1 ✅
mirror diff base-role.md: silent ✅
mirror diff harness-manager.md: silent ✅
```

✅ chg-02 完成
