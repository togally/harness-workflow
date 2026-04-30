---
id: reg-01
title: "req-51（项目级规则-经验-工具支持从制品引入）-artifacts跟项目走+索引懒加载+日志生效验证"
created_at: 2026-04-30
operation_type: requirement
stage: regression
route_to: "open_new_requirement+sug_pool"
diagnostician: "Subagent-L1（regression / opus）"
---

## 路由决策

**整体路由 = B**（P1 转新 req-52；P2 + P3 入 sug 池）。

### 路由依据矩阵

| 反馈点 | 真伪 | 推荐 default-pick | 路由 |
|--------|------|-----------------|------|
| P1 路径绑 branch vs 项目 | **真** | D：双轨（`artifacts/{branch}/project/` 保留 + 新增 `artifacts/project/`，三层文件级覆盖） | 转新 req-52（路径双轨 + 白名单通配修正） |
| P2 索引懒加载 | **部分真**（现状空占位未触发） | A：每子目录加 `index.md`（纯文档 SOP） | 入 sug 池（轻量优化，纳入 req-52 AC 也可） |
| P3 流程触发 + 打日志 | **真** | A + B 并行：helper 加 stderr 加载日志 + dogfood 子进程断言 + 用户 PetMallPlatform 真实验证 | 入 sug 池（可观测性提升 + AC-08 followup） |

## 路由候选完整清单（供用户拍板）

- **A — 开新 req-52，3 点统一收口**：P1 转 AC-01 ~ AC-03、P2 转 AC-04、P3 转 AC-05 + AC-06；改动面 = 契约层（repository-layout.md 双轨段）+ helper 层（白名单通配 / `_merge_project_level_files` 三路合并 + stderr 日志）+ 加载链层（role-loading-protocol Step 7.6 三层合并）+ 测试层（dogfood 子进程加日志断言）
- **B — 转 req-52 + sug 池（推荐）**：P1 单独走 req-52（核心契约改动）；P2 / P3 入 sug 池待 P1 落地后再决（P2 可作为 req-52 内的轻量补丁，P3 可作为 P1 落地后的可观测性 followup）
- **C — 3 点全入 sug 池**：保持 req-51 done 节奏，下次 sug 集中处理时挑选

## Notes

- req-51 OQ-1 = B-modified 拍板时未充分讨论"branch 切换可见性"——这是本次反馈的根因，属"OQ 拍板范围漏覆盖"，不算 req-51 实施失败（实施完全按拍板方向落地）
- bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）的"PetMallPlatform git branch=v1.0.0"用例正反馈了 `{branch}` 的设计意图（隔离 branch），但与项目级"跨 branch 共享"诉求**正面冲突** —— 双轨方案（D）即两者兼顾
- 白名单 `_SCAFFOLD_V2_MIRROR_WHITELIST` 字面量"artifacts/main/project/"问题严格说是 chg-02（升级保护-mirror-protected-双豁免）实施期遗留的小 bug（应该用通配前缀 `"artifacts/"` + 后缀 `/project/"` 或动态 `_get_git_branch`），可作 P1 子项一并修

## Follow-Up

- 用户拍板 A / B / C 后：
  - A → harness requirement "req-51 路径与索引优化"（开 req-52）
  - B → harness requirement "req-51 路径与索引优化"（开 req-52）+ 后续 P2 / P3 走 harness suggest
  - C → 3 点全走 harness suggest

## Conclusion

- [x] Routed —— 整体路由 = B
- [ ] Closed（待用户拍板路由 A / B / C 后由主 agent 收束）
