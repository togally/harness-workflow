---
id: chg-04
title: "scaffold_v2 镜像（极简化，仅 analyst.md + 1 行 yaml + README）"
parent_requirement: req-55
created_at: 2026-05-07
operation_type: change
stage: analysis
---

## Change Statement

把 [chg-02:analyst-office-hours 强映射] 对 `.workflow/context/roles/analyst.md` + `.workflow/context/integrations/gstack/role-command-map.yaml` + `.workflow/context/integrations/gstack/README.md` 的改造**完全镜像**到 scaffold_v2 模板（`src/harness_workflow/assets/scaffold_v2/.workflow/context/...`），保证新项目 `harness install` 后获得与本 repo 一致的 analyst 强映射 SOP。

**不**镜像 `assets/gstack-skills/` 副本到 scaffold（vendor 资产是 harness 仓库自有；scaffold_v2 是项目模板骨架，不应携带 gstack vendor 副本）。

## Key Deliverables

| # | 产物 | 落点 |
|---|---|---|
| (1) | scaffold_v2 镜像 analyst.md | `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md`（与 chg-02 (a) 改造一致） |
| (2) | scaffold_v2 镜像 role-command-map.yaml | `src/harness_workflow/assets/scaffold_v2/.workflow/context/integrations/gstack/role-command-map.yaml`（与 chg-02 (b) 一致） |
| (3) | scaffold_v2 镜像 README.md | `src/harness_workflow/assets/scaffold_v2/.workflow/context/integrations/gstack/README.md`（与 chg-02 (c) 一致） |
| (4) | mirror 白名单校验 | 验证 `_SCAFFOLD_V2_MIRROR_WHITELIST` 不含 `assets/gstack-skills/`；不含 `artifacts/project/` 子树（与 chg-03 砍掉一致）；本 chg 不引入新 mirror 豁免项 |
| (5) | mirror 一致性测试 | `tests/scaffold/test_gstack_mirror.py`：断言 scaffold_v2 镜像的 3 个文件内容与 .workflow/context/ 实例完全一致；模拟 harness install 后新项目 .workflow/context/integrations/gstack/ 子树存在 |

## Constraints / Reasoning

- **完全镜像**（不简化）：scaffold_v2 是新项目模板，必须含完整 analyst SOP 才能保证新项目 fallback 可用（即使新项目还没 chg-01 vendor 资产，analyst.md 内嵌 fallback 协议会自动走原生 SOP）。
- **不镜像 vendor 副本**：`assets/gstack-skills/` 是 harness 自身的内置资产（用于 install 推送到 ~/.claude/skills/），不属于"项目模板"——scaffold_v2 镜像不应包含；新项目运行 harness install 时由 chg-01 改造的 install_local_skills 主动推送。
- **不引入新 mirror 豁免项**：本 chg 落地范围全在 scaffold_v2 模板内，正常进 mirror 路径；与 [chg-03（已作废）] 砍掉路径一致——不再需要豁免 `artifacts/{branch}/` 或 `artifacts/project/` 子树。
- **跑 harness validate**：`harness validate --contract role-stage-continuity` 通过——确保 scaffold_v2 镜像的 analyst.md 改造没破坏 base-role / stage-role 加载链。

## Risks

| 风险 | 缓解 |
|---|---|
| chg-02 改 analyst.md 与 scaffold_v2 镜像内容漂移 | 落地时 chg-02 / chg-04 一并 commit；mirror 一致性测试在 CI 防漂移 |
| scaffold_v2 镜像的 analyst.md 在新项目上下文下"调用 /office-hours"路径与 repo 不同 | 强映射 SOP 文档与 repo 完全一致，新项目装 chg-01 vendor 后立即生效；fallback 协议覆盖未装情形 |
| `_SCAFFOLD_V2_MIRROR_WHITELIST` 校验未覆盖新增的 integrations/gstack/ 子目录 | 落地时确认 mirror 系统对 .workflow/context/integrations/ 子树的处理（默认应自动镜像，不需豁免）；测试覆盖 |

## Acceptance Criteria

覆盖父 req AC-06：
- scaffold_v2 镜像 3 个文件与实例完全一致
- mirror 白名单不含新增豁免项
- 不镜像 vendor 副本
- `harness validate --contract role-stage-continuity` 通过

## Dependencies

- [chg-02:analyst-office-hours 强映射]（必须 chg-02 先落地，本 chg 才有镜像源）

## Downstream

- chg-05 dogfood（间接依赖：dogfood 跑 adapter，scaffold_v2 镜像不直接影响 dogfood，但镜像缺失会导致新项目无法复现 dogfood 流程）

## Notes

- 镜像只复制改造段；不复制整个 analyst.md 文件（如果 chg-02 仅注入 Step A1.5 段，scaffold_v2 镜像同步注入即可，保持 base-role / stage-role 引用关系一致）
- 实务上 chg-02 / chg-04 可合 commit；分 chg 是为了 plan / 验证维度清晰
