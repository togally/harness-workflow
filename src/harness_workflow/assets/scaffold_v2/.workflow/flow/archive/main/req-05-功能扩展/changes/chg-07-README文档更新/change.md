# Change

## 1. Title
README 与文档更新（kimicli 平台 + artifacts/ 制品仓库说明）

## 2. Goal
更新 `README.md` 和 `README.zh.md`，将 kimicli 加入受支持平台列表（含安装说明和 skill 路径），并新增 `artifacts/` 制品仓库功能说明，使文档与 chg-01/chg-02 实现的平台能力和 chg-06 实现的制品仓库功能保持一致。

## 3. Requirement
- req-05-功能扩展

## 4. Scope
**包含**：
- `README.md`：支持平台列表增加 kimicli（`.kimi/skills/` 路径说明）
- `README.zh.md`：同上，中文版本
- `README.md`：新增 `artifacts/` 目录说明章节（归档触发机制、requirements/ 自动生成、其余子目录用户自管）
- `README.zh.md`：同上，中文版本
- `harness install` 命令说明中更新默认启用 4 个平台的描述

**不包含**：
- `AGENTS.md` 修改（kimicli 已原生支持）
- 新建 `KIMI.md`（kimicli 不使用此模式）
- `.workflow/` 目录下文档的修改
- 代码注释或 docstring 更新

## 5. Acceptance Criteria
- [ ] README.md 平台列表包含 kimicli，说明 `.kimi/skills/{command}/SKILL.md` 路径
- [ ] README.zh.md 同上（中文版）
- [ ] README.md 包含 `artifacts/` 目录说明，解释 `harness archive` 自动生成 `requirements/` 下摘要文档
- [ ] README.zh.md 同上（中文版）
- [ ] 平台数量描述从"三个平台"更新为"四个平台"（如文档中有此表述）

## 6. Dependencies
- **前置**：chg-01（kimicli 核心实现）、chg-02（平台检测注册）、chg-06（制品仓库功能）均已完成
- **后置**：无（文档更新为最终收尾变更）
