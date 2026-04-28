# Roadmap — req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）留尾

> 来源：chg-03（reviewer 加项 + 端到端 dogfood + roadmap）/ plan.md §5 骨架；本文件由 done 阶段 cp 出（落 `.workflow/flow/requirements/req-48-{slug}/done/roadmap.md`）。
> 命名约定：本 roadmap 仅记录留尾内容骨架 + 优先级 + 建议归属，不指派具体执行计划；具体落地由 req-49 / sug 池单独安排。

---

## §1 留尾 fix-checklist（3 个）

| 名称 | 优先级 | 触发条件（来自 PetMall / uav 实证）| 建议归属 |
|------|--------|--------------------------------|----------|
| `fix-user-write-protected-zones.md` | **高** | `check_user_write_protected_zones` ABORT — 用户写到 artifacts/ 下保护区（PetMall / uav 实证频次最高）| req-49（首批）|
| `fix-build-cache-freshness.md` | 中 | `check_build_cache_freshness` WARN — `build/` 缓存过期或污染（bugfix-8 经验十五同根因）| req-49（首批）|
| `fix-self-audit-drift.md` | 中 | `check_role_stage_continuity` 类自审漂移（角色表 / map.yaml / md 三镜像不一致）| req-49（首批）|

## §2 留尾 contract 改造（5 个，配 fix-checklist 时同时改造）

| contract 名 | 优先级 | 当前状态 | 建议归属 |
|------------|--------|----------|----------|
| `role-stage-continuity` | 中 | 已存在但 FAIL 仅打 hint | req-49（与 fix-self-audit-drift 配套）|
| `test-case-design-completeness` | 中 | 已存在但 FAIL 仅 print | sug-pool（独立小 chg）|
| `triggers` | 低 | 已存在 | sug-pool |
| `testing-no-destructive-git` | 中 | 已存在（事后 lint，bugfix-8 经验十七 sandbox 化方向）| sug-pool（建议合并到 testing sandbox 主线 req）|
| `deployment-sync` | 低 | 已存在 | sug-pool |

## §3 落地节奏

- **req-49（推荐）**：3 fix-checklist + 2 配套 contract 改造（user-write-protected-zones / build-cache-freshness / role-stage-continuity）；优先级最高，PetMall / uav 实证痛点收敛；
- **sug-pool**：3 sug（test-case-design-completeness / triggers / deployment-sync 各一条），按低 / 中优先级排队；testing-no-destructive-git 建议合并到独立的"testing subagent sandbox 化"主线 req（经验十七、十九长期方向）；
- **节奏选择理由**：req-46 / req-47 同款"首批 K + 留尾"模式已被 req-48 自身验证可用（3 chg + 8 AC + 37 TC 一次闭环），避免单 req 超载、reviewer 压力大；按优先级渐进落，5 个待办在后续 req 完成时顺手 cherry-pick 即可。

## §4 优先级建议（按 PetMall / uav 实证痛点频次）

1. **user-write-protected-zones**（高）：bugfix-8/9 已暴露过 269 文件误报问题；新加 fix-checklist 后用户能直接按指引把违规文件 mv 回业务区或加 managed-files 登记；
2. **build-cache-freshness**（中）：bugfix-8 经验十五已落 lint，缺 fix-checklist；用户碰到时仍需阅读经验十五理解根因，配套 checklist 可一步执行 `rm -rf build/ && pipx install --force`；
3. **role-stage-continuity / self-audit-drift**（中）：经验八 / 经验十六覆盖；自审漂移触发面较低，但一旦命中需要修三处镜像 + map.yaml，配套 checklist 价值大；
4. **test-case-design-completeness**（中）：bugfix-6 主题，已稳定运行；FAIL 改 raise_harness_block 收益小但闭环规整；
5. **triggers / deployment-sync**（低）：触发面低，可作 sug 池碎片化时间渐进落。

---

> **后续可关闭项**：当 req-49 落地完成 + 5 sug 全部出池后，本 roadmap 任务全部清空，req-48 反馈闭环正式收口。
