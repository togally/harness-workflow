# Session Memory — bugfix-4

## 1. Current Goal
完成 bugfix-4（scaffold 清洗 harness-workflow 历史数据）的 regression → executing → testing 全链路，确保 `harness install` 在空仓不再把本仓 runtime、sessions、archive、suggestions、requirements 污染到用户新仓。

## 2. Current Status

- regression 诊断完成：已定位到 `_scaffold_v2_file_contents()` 过滤规则不足 + scaffold_v2 被误同步了作者仓全量 .workflow/
- executing 清洗完成：scaffold_v2 下污染文件从 903 降到 72；runtime.yaml 重置为初始值；action-log 清空
- testing 验证完成：空仓 init 7/7 场景 PASS；smoke requirement 创建成功；主仓 harness status 非回归
- 调用链：Level 0 主 agent（bugfix-4 regression 阶段）→ Level 1 bugfix 全链路 subagent（本次 regression+executing+testing）

## 3. Validated Approaches

- 空仓 init 验证：`mkdir -p /tmp/harness-bugfix4-<ts>/ && cd $_ && git init -q && harness install --agent claude` → 立即检查 runtime.yaml 字段，稳定可复现的 scaffold 泄漏验证模式
- `_scaffold_v2_file_contents()` 直接 Python 回归调用，快速确认过滤效果（文件数 + runtime 内容）
- 主仓非污染验证：清洗后 `harness status` 在主仓工作目录仍正常读取真实状态（证明 SCAFFOLD_V2_ROOT 只用于 copy，不被主仓 runtime 读取）

## 4. Failed Paths

- 无失败路径。唯一需要注意的是 `harness install` 的参数名是 `--agent claude` 而非假设的其他选项；首次调用若拼错参数会报 argparse 错误。

## 5. Candidate Lessons

```markdown
### 2026-04-19 scaffold 静态资产污染
- Symptom: 空仓 `harness install` 后 runtime.yaml 直接出现 req-25/active_requirements 等作者仓真实状态；sessions/archive/suggestions/requirements 子树混入作者仓历史
- Cause: `src/harness_workflow/assets/scaffold_v2/` 在历次同步操作中被误当作主仓 mirror 全量复制；`_scaffold_v2_file_contents()` 仅排除 `/requirements/` 路径，无法拦截 state/runtime.yaml、state/sessions/、flow/archive/、archive/、context/backup/、flow/suggestions/archive/ 等污染
- Fix: 静态清洗 scaffold_v2，重置 runtime.yaml 为 DEFAULT_STATE_RUNTIME 初始值，删除所有进行中业务数据；后续应加代码层 deny-list 或白名单防御
```

## 6. Next Steps

- 主 agent 根据 bugfix SEQUENCE（regression → executing → testing → acceptance → done）推进
- 本 subagent 已完成 executing + testing 两阶段的实质内容；主 agent 可直接路由至 acceptance
- 衍生 suggestion（非本 bugfix 范围）：在 `_scaffold_v2_file_contents()` 中追加显式 deny-list（state/runtime.yaml、state/sessions/、state/requirements/、flow/archive/、flow/requirements/req-、flow/suggestions/archive/、archive/、context/backup/、state/action-log.md），作为代码层防御；或改为白名单 allow-list 模式
- CI 加固建议：引入空仓 init smoke test，断言 runtime.yaml 字段全部为初始值

## 7. Open Questions

- 是否需要在 `_scaffold_v2_file_contents()` 中额外加 deny-list 作为运行时防御？本次已走静态清洗方案，视主 agent 判断是否作为独立 suggestion。
- `.workflow/flow/suggestions/archive/` 目录在 scaffold 中完全删除后，首次 `harness suggest` 是否会自动创建？已通过 `harness requirement` 正向验证，但 suggest 链未显式测试。
