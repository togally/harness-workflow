# Known Risks and Mitigations

## 风险一：tools/ 目录迁移后路径丢失

### 场景
req-02/chg-03 恢复 tools/ 工具层时，备份源路径已随 chg-04（context/backup → archive）迁移。

### 风险内容
如果 chg-03 和 chg-04 顺序调换，tools/ 的备份源 `context/backup/` 在 chg-04 完成后变成 `archive/`。
先找路径再做迁移；执行多个目录迁移变更时要注意彼此的依赖顺序。

### 缓解
- 任务开始前列出所有受影响路径
- 平行变更中若有路径依赖，应标记为串行执行

### 来源
req-02/chg-03 tools/ 迁移，实际备份位置 archive/legacy-cleanup/workflow/tools/

---

## 风险二：Edit 工具在未读取文件时拒绝写入

### 场景
req-02/chg-03 批量更新 6 个角色文件时，对未 Read 过的文件调用 Edit 工具失败。

### 风险内容
Edit 工具强制要求在同一会话中先 Read 目标文件，否则报 "file not read" 错误。
批量编辑多文件时，必须先并行 Read 所有目标文件，再做 Edit。

### 缓解
- 批量编辑前：一次并行 Read 所有目标文件
- Write 工具用于创建新文件或完整重写，Edit 用于局部修改

### 来源
req-02/chg-03 角色文件批量更新

---

## 风险三：禁止 subagent 执行破坏性 git 操作

### 场景
harness-manager 派 subagent 执行 req/chg 实施任务时。

### 风险内容
并行 subagent 执行期间，若 subagent prompt 未显式禁止破坏性 git 操作，subagent 可能（意外或误判）执行 `git reset --hard`、`git restore`、`git checkout --`、`git clean -f`、`git rm` 等操作，导致同批次其他 subagent 已写入的 tracked 文件改动被抹除，难以溯源。

本次事故记录：req-55（事故时 req-id 为 req-53，因后与远程 main 撞车 rename）chg-01/02 tracked 文件改动被某并行 subagent 执行 5 次 `git reset --hard HEAD` 抹回 baseline，需要整批重做。

### 缓解

**harness-manager 派发 subagent 时必须在 prompt 头部显式写入以下禁止段**：

```
严格禁止破坏性 git 操作：
- git reset（任何形式：--hard / --soft / --mixed / HEAD / commit）
- git restore
- git checkout -- / git checkout <file>
- git clean -f / git clean -fd
- git rm
只允许：Read / Edit / Write / 只读 git 命令（status/log/diff）/ pytest 类只读命令。
git commit 须经主 agent 明确授权后才允许执行。
```

**验证方式**：主 agent 派发前检查 subagent briefing 中是否含上述禁止段；无禁止段的 briefing 视为不合规，必须补充后再发出。

### 来源
req-55（项目路书Playbook体系；事故时 req-id 为 req-53，因后与远程 main 撞车 rename）并行执行期间，5 次 git reset --hard 抹掉 chg-01（路书目录骨架契约）/ chg-02（baseRole代码加载规则与CLAUDE索引）tracked 文件改动。

---

## 风险四：harness 工作流偏离（速度优先 chg 不立项）

### 场景
1.0.0 发版前临时收口阶段，主 agent 跳过 harness requirement / change 标准流程，直接派 subagent 实施改动。

### 风险内容
req-55（项目路书Playbook体系）+ req-56（路书引擎升级）后续的 **chg-A（路书改进 maven nested + 提示句）/ chg-B（清 kimi/qoder + 2 polish）/ chg-C（产品规范完善 + 1.0.0 发版）** 三组改动**未走 harness 立项流程**：
- 无 harness requirement 立项
- 无 analysis stage（OQ + default-pick 决策记录）
- 无标准 chg.md / plan.md
- 无 testing / acceptance gate runtime.yaml stage 流转
- 直接 commit + push 到 feature/req-53-playbook

涉及改动规模较大（chg-C 单 chg 14 文件 + 30+ 测试），**严格按规范应作为 req-57（路书产品规范完善 + 1.0.0 发版准备）立项**。

### 缓解 / 决策溯源
**用户授权速度优先**：1.0.0 关键发版里程碑，速度优先 vs 流程完整性的权衡选择 Plan B（接受偏离），换取尽快在其他项目（PetMallPlatform）中使用 1.0.0 路书功能。

涉及 commit:
- 79df99e Merge origin/main
- 04d167a WIP req-55/56
- c131dfa req-56 完成 + 硬门禁十一
- b5fb966 req-56 后续完善 + 46 upstream bug
- 58125b0 fix refresh nested maven
- 1.0.0 发版（chg-C，本次 commit）

### 后续补救建议
1.0.0 发版后，下个 req 周期：
- 反向补 req-57（"路书产品规范完善 + 1.0.0 发版"）的 requirement / chg-A/B/C 的 plan.md 作为审计补档
- 或在下一个 req 第一个 chg 里 retrofit 此次偏离

### 来源
1.0.0 发版前临时收口阶段（用户授权速度优先决策，2026-04-30 / 05-01）。
