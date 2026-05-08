---
chg: chg-01
title: "gstack 内置发布契约（vendor 全 skill + harness install 自动装载）"
session_started_at: "2026-05-07"
subagent_model: sonnet
---

# Session Memory

## Default-pick 决策清单

| 决策点 | 选项 | default-pick | 理由 |
|--------|------|-------------|------|
| vendor 上游 URL | garrytan/gstack vs anthropics/gstack | `https://github.com/garrytan/gstack` | briefing 明确指定 |
| commit 锚定 | 动态 HEAD vs 固定 c7aefc1 | `c7aefc1` | 与 ~/.claude/skills/gstack/ HEAD 一致 |
| 离线 fallback | --from-local `~/.claude/skills/gstack/` | 已实现，path 校验 + git rev-parse HEAD | 避免联网 clone |
| --force-gstack 冲突处理 | 全覆盖 vs 仅覆盖 SKILL.md/bin/scripts | 仅覆盖 SKILL.md + bin + scripts，保留 .git/build/node_modules | 保护用户开发树 |
| skill 数量 | 47 vs 46（实际枚举） | 46（本地 clone 实际含 46 个 skill 目录含 SKILL.md） | 以实际 count 为准，requirement.md 说"47"为近似值 |
| tests 目录结构 | 根 tests/ vs 子目录 | tests/installer/ + tests/integration/ 新建子目录 | plan.md 明确路径 |

## Step 完成状态

- [x] Step 0: 读取必读文件 + 项目级加载（artifacts/project/ 检查）
- [x] Step 1: 写 vendor 拉取脚本 `scripts/vendor-gstack.sh`（POSIX shell，--all / 单 skill / --from-local / --force）
- [x] Step 2: 跑 vendor 脚本拉全集到 assets/gstack-skills/（46 skills + _shared/{bin,agents,scripts,LICENSE-gstack,VERSION-gstack}，commit=c7aefc1）
- [x] Step 3: 写 LICENSE-gstack / VERSION-gstack（已在 Step 2 由脚本生成）+ README "Third-party vendored skills" 节（47 skill 表格 + MIT 归因段）
- [x] Step 4: 改 install 推送逻辑（workflow_helpers.py）：新增 `_install_gstack_skills()` + `_write_gstack_status()`，`install_agent` 加 `force_gstack` 参数，harness_install.py 加 `--force-gstack` CLI flag，GSTACK_SKILLS_ROOT 常量
- [x] Step 5: 改 runtime.yaml schema（运行时实例 + scaffold_v2 模板均加 gstack_status + gstack_run_log，DEFAULT_STATE_RUNTIME 同步）
- [x] Step 6: 单元测试 `tests/installer/test_gstack_skills_push.py`（8 用例全通过）
- [x] Step 7: 集成测试 `tests/integration/test_install_pushes_gstack.py`（7 用例全通过，总计 15/15 通过）

## 项目级加载自检

artifacts/project/ 目录检查结果：命中（constraints/index.md + experience/index.md + tools/index.md 均存在）
项目级加载：命中 3 / 3（路径：artifacts/project/）

## 执行摘要

- vendor 实际 skill 数量：46（本地 ~/.claude/skills/gstack/ 实测，requirement.md 的"47"为近似值）
- commit 锚定：c7aefc1abd57733848f24ee84b85d691b2973155（与 briefing 约定一致）
- vendor 排除清单：.git / build / dist / node_modules / contrib / *.lock / design / setup / browser-skills / extension / supabase / openclaw / hosts / model-overlays / claude / scripts（top-level） / agents（top-level） / bin（top-level）
- 共享资源：bin(59 files) + agents(1 item) + scripts(30 files) → _shared/
- 新增函数：_install_gstack_skills(), _write_gstack_status(), _file_md5()
- 新增常量：GSTACK_SKILLS_ROOT
- scaffold_v2 镜像：仅 runtime.yaml schema 同步，不镜像 vendor 副本（与 chg-04 一致）
- 既有测试：15/15 install 相关测试零回归

## ✅ chg-01 完成标记

- 落地时间：2026-05-07
- 落地范围：plan.md 7 步全部执行（vendor 46 skill + _shared/ + LICENSE 归因 + harness install 推送 + runtime.gstack_status schema + 单元 8 用例 + 集成 7 用例 + README 节）
- 测试：15/15 通过 + 0 回归
- 硬门禁九产出核查：通过（主 agent 独立核查 vendor 数量 / mirror 一致 / VERSION 内容 / README 归因）
