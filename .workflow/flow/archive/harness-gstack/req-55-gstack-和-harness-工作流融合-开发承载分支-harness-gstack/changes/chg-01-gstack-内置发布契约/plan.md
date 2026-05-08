---
id: chg-01
title: "gstack 内置发布契约（vendor 全 skill + harness install 自动装载）"
parent_requirement: req-55
created_at: 2026-05-07
operation_type: change
stage: analysis
---

## Plan Steps

> 执行序为依赖顺序；Step 1~3 是 vendor 资产准备，Step 4~5 是 install 流程改造，Step 6~7 是测试。

### Step 1: 写 vendor 拉取脚本（先单 skill 形态）

- 文件：`scripts/vendor-gstack.sh`
- 形态：POSIX shell；接受 `<skill-name> [commit]` 或 `--all [commit]` 参数
- 单 skill 形态实现：
  1. clone gstack 仓库到 tmp（或 reuse `--from-local <path>` 参数读本地副本，离线 fallback）
  2. checkout 指定 commit（默认 HEAD）
  3. 复制 `<skill-name>/SKILL.md` + `<skill-name>/{references,scripts}/`（若存在）到 `src/harness_workflow/assets/gstack-skills/<skill-name>/`
  4. 写 `src/harness_workflow/assets/gstack-skills/<skill-name>/VERSION-gstack`（含 upstream URL + commit hash + version + vendor timestamp）
- `--all` 形态：扫上游所有顶层目录含 SKILL.md 的为 skill，循环单 skill 形态；额外复制顶层 `bin/agents/scripts/` + `LICENSE` 到 `_shared/`

### Step 2: 跑 vendor 脚本拉全集到 assets/gstack-skills/

- 命令：`scripts/vendor-gstack.sh --all <commit>`
- 产出：`src/harness_workflow/assets/gstack-skills/{47 个 skill 目录}/...` + `_shared/{bin,agents,scripts,LICENSE-gstack,VERSION-gstack}`
- 验证：
  - `find src/harness_workflow/assets/gstack-skills -name SKILL.md | wc -l` == 47
  - `_shared/LICENSE-gstack` 内容 = gstack MIT 全文
  - `_shared/VERSION-gstack` 含 upstream URL + commit + 时间戳

### Step 3: 写 LICENSE-gstack / VERSION-gstack / 仓库根 README "Third-party vendored skills" 节

- LICENSE-gstack：vendor 脚本已自动写到 `_shared/`，本 step 仅校验内容完整
- VERSION-gstack：同上
- 仓库根 README.md：增"Third-party vendored skills"小节
  - 一句话简介：harness 内置了 gstack（YC 风格工程辅助 skill 集合，MIT 协议）47 个 skill，harness install --agent claude 自动装载到 `~/.claude/skills/`
  - 表格列出：skill 名 / 一句话用途 / upstream 路径
  - MIT 归因：复制 gstack LICENSE 链接 + 致谢段
- 校验：跑 `markdownlint README.md` 通过

### Step 4: 改 install 推送逻辑

- 文件：`src/harness_workflow/installer/core.py`
- 改动点：
  1. 在 `install_local_skills` / `install_agent` 内 agent_kind=claude 分支前加新函数 `_install_gstack_skills(target_root: Path, force: bool) -> dict`：
     - 入参：target_root（默认 `~/.claude/skills/`）+ force（来自 `--force-gstack` flag）
     - 行为：遍历 `GSTACK_SKILLS_ROOT = src/harness_workflow/assets/gstack-skills/`，把每个 skill 目录复制到 `target_root/<skill-name>/`；把 `_shared/{bin,agents,scripts,LICENSE-gstack,VERSION-gstack}` 复制到 `target_root/gstack/{bin,agents,scripts,...}`（与 SKILL.md 内嵌硬编码路径一致）
     - 冲突检测：对每个 SKILL.md 比 hash；不同且 force=False → warn + 跳过；force=True → 覆盖
     - 失败回退：单个 skill 复制失败 → warn + 追加到 install_summary["gstack_failures"]；不阻塞主流程
     - 返回：installed_skills 列表 + vendor_version（读自 VERSION-gstack）
  2. 在 `install_agent` 末尾装载完成后调用 `_install_gstack_skills` 并把返回值写入 `runtime.yaml.gstack_status`
  3. agent_kind ≠ claude 时打印 "gstack skills only push to claude agents, skipping" warn

### Step 5: 改 runtime.yaml schema + 写入逻辑

- 文件：`.workflow/state/runtime.yaml`（运行时实例）+ schema 文件（如 `src/harness_workflow/assets/scaffold_v2/.workflow/state/runtime.yaml` 模板）
- 加 `gstack_status` 字段（默认值 `null`）：
  ```yaml
  gstack_status:
    installed_skills: []        # 已装 skill 名清单
    vendor_version: ""          # vendor commit hash
    last_install: ""            # ISO8601 时间戳
    agent_kind_compatible: false  # 当前 agent_kind 是否支持 gstack
  ```
- 失败回退字段 `gstack_run_log`（保留性追加）：
  ```yaml
  gstack_run_log:
    - timestamp: "..."
      skill: "..."
      action: "install"
      outcome: "failed"
      reason: "..."
  ```
- 写入逻辑落 install_agent 末尾（Step 4 已铺垫）

### Step 6: 单元测试

- 文件：`tests/installer/test_gstack_skills_push.py`
- 用例：
  - `test_vendor_script_single_skill`：跑 `scripts/vendor-gstack.sh office-hours <commit>` → 断言目录 + VERSION-gstack 落地
  - `test_vendor_script_all`：跑 `--all` → 断言 47 个 skill + `_shared/`
  - `test_install_pushes_skills_when_agent_claude`：mock agent_kind=claude → `_install_gstack_skills` 推送全集
  - `test_install_skips_when_agent_codex`：mock agent_kind=codex → 跳过 + warn
  - `test_conflict_default_warn`：~/.claude/skills/office-hours/SKILL.md 已存在不同 hash → warn 不覆盖
  - `test_force_gstack_overrides`：--force-gstack 传入 → 覆盖
  - `test_skill_push_failure_does_not_block`：mock 单 skill 复制失败 → 主流程继续 + gstack_run_log 写入
  - `test_runtime_yaml_gstack_status_written`：装载完成 → runtime.yaml.gstack_status 四子字段正确

### Step 7: 集成测试

- 文件：`tests/integration/test_install_pushes_gstack.py`
- 流程：
  1. 在 tmp 目录初始化干净 harness 项目（`harness install --agent claude`）
  2. 断言 `~/.claude/skills/` 下 47 个 skill 目录全到位（每目录有 SKILL.md）
  3. 断言 `~/.claude/skills/gstack/{bin,agents,scripts,LICENSE-gstack,VERSION-gstack}` 存在
  4. 断言 `~/.claude/skills/<core-skill>/LICENSE-gstack` 推送到位（每 skill 一份归因，或仅 _shared 一份——按实现选择）
  5. 断言 `<tmp>/runtime.yaml.gstack_status.installed_skills` 含 47 个 skill 名
  6. 断言 `vendor_version` 与 `_shared/VERSION-gstack` 内容一致
  7. 重跑 `harness install --agent claude` → 第二次因 hash 一致不报冲突 + 不重复推

## Verification Checklist

- [ ] AC-01：vendor 全 skill 落盘 + License 三件套 + 仓库根 README 节
- [ ] AC-02：harness install 自动装载 + agent_kind ≠ claude 跳过 warn
- [ ] AC-07：MIT 归因 4 项全做
- [ ] AC-08：runtime.yaml.gstack_status 字段写入正确

## Open Questions

- gstack 仓库 upstream URL 待 vendor 脚本编码时确认（脚本可接受 `--upstream <url>` 参数，默认值待定）
- `--from-local <path>` 离线模式实现细节（是否要校验 path 是 git 仓库、是否要 read commit hash from path/.git/HEAD）
- 推送目标 `~/.claude/skills/gstack/` 路径 collision：用户原 gstack git clone 也在该路径——`--force-gstack` 行为是"全覆盖"还是"仅覆盖 SKILL.md / bin / scripts，保留 .git"？倾向后者（保护用户开发树）
