# Change: chg-01

## Title
对话摘要写入逻辑

## Goal
在 session-memory 中写入对话摘要，记录本轮关键信息。

## Scope

**包含**：
- 修改 `core.py`，在 `save_session_memory` 或相关流程中，确保 session-memory 的 `## Stage 结果摘要` 区块完整
- 在 `done` 阶段（或 `harness archive` 前）自动读取 session-memory 的关键内容，生成或补全摘要

**不包含**：
- 修改 session-memory 的基础格式（只是确保内容完整）
- 外部存储集成

## Acceptance Criteria

- [ ] session-memory.md 中包含清晰的阶段结果摘要
- [ ] 摘要内容能被后续 `harness enter` 读取
