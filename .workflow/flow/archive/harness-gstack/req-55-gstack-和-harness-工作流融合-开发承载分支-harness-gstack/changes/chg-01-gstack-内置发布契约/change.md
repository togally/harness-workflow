---
id: chg-01
title: "gstack 内置发布契约（vendor 全 skill + harness install 自动装载）"
parent_requirement: req-55
created_at: 2026-05-07
operation_type: change
stage: analysis
---

## Change Statement

把 **gstack 全部 47 个 SKILL.md + 顶层共享资源（bin/agents/scripts）** 作为 harness 自身的内置 vendored 资产固化到 `src/harness_workflow/assets/gstack-skills/`；改 `install_local_skills` / `install_agent` 流程，在 agent_kind=claude 时把全集推送到 `~/.claude/skills/`（用户立即能在 Claude Code 主对话直接 `/<skill-name>` 触发任意 gstack skill）；agent_kind ≠ claude 时跳过 + warn 不阻塞 install；`runtime.yaml.gstack_status` 字段记录装载状态；MIT 协议 4 项归因合规全做。

本 chg 是 [req-55:gstack-harness 融合开荒] 的最前置 chg，无依赖；后续 chg-02 / chg-04 / chg-05 依赖本 chg 的装载层产物。

## Key Deliverables

| # | 产物 | 落点 |
|---|---|---|
| 1 | vendor 副本目录骨架（47 个 skill 目录，每目录至少 SKILL.md + 子资源 references/ scripts/ 若上游存在）+ 共享资源 | `src/harness_workflow/assets/gstack-skills/{skill-name}/...` 各 skill 一目录 + `src/harness_workflow/assets/gstack-skills/_shared/{bin,agents,scripts}/` |
| 2 | License 归因三件套（vendor 副本根） | `src/harness_workflow/assets/gstack-skills/_shared/LICENSE-gstack`（gstack MIT 全文复制）+ `_shared/VERSION-gstack`（含上游 URL + commit + 版本 + vendor 时间） |
| 3 | vendor 拉取脚本 | `scripts/vendor-gstack.sh [skill-name|--all] [commit]`（POSIX shell；先实现单 skill 形态，再加 `--all` 形态；自动写 `_shared/VERSION-gstack`；保留上游目录结构包括 references/ scripts/） |
| 4 | install 推送逻辑改造 | `src/harness_workflow/installer/core.py` 的 `install_local_skills` / `install_agent`：检测 `agent_kind == "claude"` → 调用 `_copy_tree(GSTACK_SKILLS_ROOT, ~/.claude/skills/)`（全 47 个 + `_shared/{bin,agents,scripts}/` 落 `~/.claude/skills/gstack/{bin,agents,scripts}/` 给 SKILL.md 二进制依赖兜底）；其它 agent_kind 跳过 + warn |
| 5 | runtime.yaml schema 扩展 | `runtime.yaml.gstack_status: { installed_skills: [...], vendor_version: "<commit>", last_install: "<iso8601>", agent_kind_compatible: bool }` 四子字段；schema 更新到 `.workflow/state/runtime-schema.yaml`（如存在）；写入逻辑落 install_agent 末尾 |
| 6 | 装载冲突处理 | 检测 `~/.claude/skills/{name}/SKILL.md` 已存在且 hash 不同 → 默认 warn 不覆盖；`harness install --force-gstack` flag 才覆盖；用户已自装 gstack 全套（含 git clone）的场景兼容 |
| 7 | 装载失败回退 | 任一 skill 推送失败 → warn 输出 + `runtime.yaml.gstack_run_log` 追加（含 skill 名 + 失败原因 + 时间戳）；不阻塞 install 主流程；其它 skill 继续推 |
| 8 | 仓库根 README "Third-party vendored skills" 节 | `README.md` 增"Third-party vendored skills"小节，列出全部 47 vendored skills + MIT 归因（核心 skill 如 office-hours / codex / qa / review 单独 attribution；列表项可表格形式紧凑展示） |
| 9 | 单元测试 | `tests/installer/test_gstack_skills_push.py`：vendor 脚本单 skill / --all 形态 + agent_kind=claude 推送 + agent_kind=codex 跳过 warn + 冲突默认不覆盖 + --force-gstack 覆盖 + 推送失败回退 |
| 10 | 集成测试 | `tests/integration/test_install_pushes_gstack.py`：在 tmp 目录跑完整 `harness install --agent claude` 流程 → 断言 `~/.claude/skills/` 下 47 个 skill 全到位 + LICENSE-gstack 推送 + runtime.yaml.gstack_status 写入正确 |

## Constraints / Reasoning

- **vendor 形态选 a 复制快照**（非 submodule / 非 subtree）：harness 已有 `assets/skill/` 复制管线，gstack-skills 当作 vendored 资产管理对称；不引入 submodule clone 复杂度；MIT 允许 vendor。
- **vendor 范围选 b 全部 47 skill**（第 7 轮用户拍板修正 Q8.2，从"仅 office-hours"扩到"全集"）：装载层成本不高（仅 SKILL.md + 子资源；不带上游 .git / build / node_modules，估算总体积数 MB～几十 MB），价值高（用户立即能用任何 gstack skill）；融合层仍仅 analyst → /office-hours 渐进。
- **装载时机选 a harness install / install --agent 同步**：与 [reg-02:同步契约统一] chg-07 "install 是同步契约唯一真入口"对齐；不另开 `harness install --gstack` 命令面。
- **装载目标选 a 全局 ~/.claude/skills/**：gstack 自身就是全局 skill；多项目场景全局装一次即够；与 harness skill 项目级 `.{agent}/skills/harness/` 是不同语义层（harness 必须随项目走的状态机；gstack 是命名 skill，全局即可）。
- **共享资源 vendor 必要性（第 7 轮调研结论）**：每个 SKILL.md 内嵌 `~/.claude/skills/gstack/bin/gstack-{update-check,config,telemetry-log,repo-mode,slug}` 二进制调用；如不 vendor `_shared/bin/` 用户即使有 SKILL.md 也无法运行 → 必须把 gstack 仓库顶层 `bin/agents/scripts/` 一并 vendor 到 `_shared/` 并推送到 `~/.claude/skills/gstack/{bin,agents,scripts}/` 路径（与 SKILL.md 内嵌的硬编码绝对路径一致）。
- **upstream commit 锚定**：本 chg 第一次 vendor 锚定到 gstack 当前默认分支最新 commit（vendor 脚本执行时记录），写入 `_shared/VERSION-gstack`；后续升级走独立 sug / chg。
- **License 4 项归因不可省**：MIT 强制要求保留 copyright + permission notice；本 chg 全做（vendor 根 LICENSE-gstack 全文 + VERSION-gstack 来源声明 + 仓库根 README 节 + 推送时同步 LICENSE-gstack 副本到 `~/.claude/skills/gstack/`）。
- **装载冲突场景**：用户本机已有 `~/.claude/skills/gstack/` 整仓 git clone（开发者场景）→ 默认 warn 不覆盖（保护用户工作树）；带 `--force-gstack` 才覆盖；新用户场景无冲突直接推。

## Risks

| 风险 | 缓解 |
|---|---|
| 47 SKILL.md 中部分 skill 依赖上游仓库 root 的 BROWSER.md / ARCHITECTURE.md / 其它非 bin/scripts 资源 | 第 7 轮调研未深查每个 SKILL.md 完整依赖；vendor 脚本初版可保守把 gstack 仓库根除 .git / build / node_modules / contrib 之外的 markdown 文件一并 vendor 到 `_shared/`，体积代价仍可控 |
| vendor 总体积偏大 | 严格排除 .git / node_modules / build / dist / *.lock / contrib；只保留 SKILL.md + 同 skill 子目录 references/ scripts/ + 顶层 bin/agents/scripts/ + 必要 markdown |
| 用户已自装 gstack 不希望被 harness 接管 | `--force-gstack` opt-in；默认不覆盖；warn 提示用户已有版本 |
| install 推送 47 个 skill 耗时 | 复制操作纯 IO；47 skill 总 < 几十 MB；预计 < 1 秒；无性能风险 |
| MIT 归因遗漏被上游投诉 | 4 项全做；README 节单独点名核心 skill attribution；vendor 副本根 LICENSE-gstack + VERSION-gstack 双重声明 |
| vendor 脚本拉取需联网 | 脚本说明文档明示需联网 + 给出离线 fallback（用户预先 clone gstack 到本地，脚本接受 `--from-local <path>` 参数读本地副本） |

## Acceptance Criteria

覆盖父 req AC-01 / AC-02 / AC-07 / AC-08：
- vendor 副本目录 + License 三件套 + 仓库根 README 节齐全
- `harness install --agent claude` 后 `~/.claude/skills/` 下 47 个 skill + LICENSE-gstack 推送到位 + runtime.yaml.gstack_status 写入正确
- agent_kind ≠ claude 时跳过 + warn 不阻塞
- 单元测试 + 集成测试全过

## Dependencies

- 无（本 chg 是最前置）

## Downstream

- chg-02 / chg-04 / chg-05 全部依赖本 chg 装载层落地

## Notes

- gstack 上游 URL 待 vendor 时确认（vendor 脚本中硬编码或通过参数传入）
- 升级策略：本 req 只锚一次 vendor commit；后续升级走独立 sug
