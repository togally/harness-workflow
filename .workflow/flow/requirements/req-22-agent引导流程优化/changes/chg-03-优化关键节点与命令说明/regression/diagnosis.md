# Regression Diagnosis: req-22 / acceptance stage (3rd)

## 触发来源

用户在 acceptance 阶段第三次执行 `harness regression`，反馈角色加载流程的架构设计仍不够通用和抽象。

## 问题描述

1. **`context/index.md` 仍耦合了两种职责**：当前文件同时是"角色索引"和"角色加载流程"的载体。用户认为"角色加载流程"应该被抽离为一个独立的通用协议文件，而不是和索引混在一起。
2. **顶级角色被特殊对待**：当前 `context/index.md` 的 Step 3 明确写着"加载顶级角色"，暗示顶级角色有一套独立的加载逻辑。用户认为顶级角色（技术总监）也应该被**通用的角色加载流程**约束，不应该有特权路径。
3. **`WORKFLOW.md` 的入口引导不够准确**：当前只说"去 `context/index.md` 找角色并按角色加载流程执行"，但用户期望它能更明确地表达：先总结需求 → 去索引找角色 → 按通用协议加载 → 执行。

## 根因分析

前两次 regression 修复虽然简化了 `WORKFLOW.md` 和重构了 `context/index.md` 的结构，但没有把"角色加载流程"这一**通用规则**彻底抽象为独立文件。

当前架构中：
- `context/index.md` = 索引 + 流程（耦合）
- 顶级角色有单独的加载步骤（Step 3）
- 没有独立的"角色加载协议"可供所有角色引用

这导致角色加载规则无法被各角色文件（包括 `technical-director.md`）显式引用和约束。

## 问题确认

✅ **真实问题**。这是 req-22 核心设计意图（以角色为核心、流程由角色维护）尚未完全落地的结构性缺陷。

## 路由决定

**需求/设计问题** → 回到 `planning` 阶段，重新调整 chg-01 的范围。

具体修复方向：
1. **新建通用角色加载协议**：`.workflow/context/roles/role-loading-protocol.md`，定义所有角色（含顶级角色）的通用加载步骤
2. **`context/index.md` 纯索引化**：只保留角色索引表格 + 一句话"请根据下方索引找到你的角色，并按 `role-loading-protocol.md` 加载"
3. **更新 `WORKFLOW.md`**：入口改为"请总结用户需求，然后去 `context/index.md` 索引中找到所需角色，并按 `role-loading-protocol.md` 加载执行"
4. **更新 `technical-director.md`**：SOP 中引用 `role-loading-protocol.md`，明确技术总监也遵循该协议加载
