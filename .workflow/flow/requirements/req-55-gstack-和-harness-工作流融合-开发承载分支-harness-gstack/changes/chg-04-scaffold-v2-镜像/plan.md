---
id: chg-04
title: "scaffold_v2 镜像（极简化，仅 analyst.md + 1 行 yaml + README）"
parent_requirement: req-55
created_at: 2026-05-07
operation_type: change
stage: analysis
---

## Plan Steps

> 执行序：Step 1 同步 analyst.md 改造，Step 2 同步映射 yaml + README，Step 3 跑 mirror 一致性 + 契约校验。

### Step 1: 同步 analyst.md 改造到 scaffold_v2

- 源文件：`.workflow/context/roles/analyst.md`（chg-02 落地后的状态）
- 目标文件：`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md`
- 操作：
  1. 读源文件 Step A1.5 段（含触发协议 + adapter mapping + fallback）
  2. 找到目标文件对应位置（同 Step A1 与 Step A2 之间）
  3. 复制 Step A1.5 段插入；保持源 / 目标其它段完全一致
  4. diff 源 vs 目标，确认仅 Step A1.5 段差异已抹平

### Step 2: 同步 role-command-map.yaml + README.md 到 scaffold_v2

- 创建目录：`src/harness_workflow/assets/scaffold_v2/.workflow/context/integrations/gstack/`
- 复制源文件到目标：
  - `.workflow/context/integrations/gstack/role-command-map.yaml` → 镜像目标
  - `.workflow/context/integrations/gstack/README.md` → 镜像目标
- 内容**完全一致**（不本地化、不参数化）；镜像系统按文件级 diff 检测漂移

### Step 3: 跑契约校验 + mirror 一致性测试

- 命令 1：`harness validate --contract role-stage-continuity`
  - 验证 scaffold_v2 模板的 analyst.md 改造没破坏 base-role / stage-role 加载链
  - 验证 Step A1.5 段插入位置不冲突 base-role 强约束
- 命令 2：跑 mirror 一致性测试 `tests/scaffold/test_gstack_mirror.py`
  - 断言 scaffold_v2 镜像的 3 个文件内容与 `.workflow/context/` 实例完全一致
  - 模拟 `harness install` 在 tmp 目录初始化新项目，断言新项目 `.workflow/context/integrations/gstack/` 子树存在
  - 断言新项目 `.workflow/context/roles/analyst.md` 含 Step A1.5 段
- 命令 3：手工抽检
  - cd 到 tmp 项目跑 `harness install` 后浏览 .workflow/context/roles/analyst.md，确认 Step A1.5 段确实可读

## Verification Checklist

- [ ] AC-06：scaffold_v2 镜像 3 个文件与实例完全一致
- [ ] mirror 白名单不含新增豁免项；不镜像 vendor 副本
- [ ] `harness validate --contract role-stage-continuity` 通过
- [ ] mirror 一致性测试通过

## Open Questions

- mirror 系统对新增 `.workflow/context/integrations/gstack/` 子目录的检测时机：是 `harness install` 后还是 `harness update --force-managed` 后？落地时确认 _SCAFFOLD_V2_MIRROR_WHITELIST 当前对 `.workflow/context/integrations/` 子树的策略
- 如果 mirror 系统按目录级 hash 检测漂移，新增子目录是否要先在 mirror 校验白名单中显式声明？落地时验证（当前判断：默认自动镜像，不需声明）
