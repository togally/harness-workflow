# req-23 端到端测试报告

## 测试目标

验证 bugfix 快速修复流程能够完整走通：`regression → executing → testing → acceptance → done`。

## 测试环境

- 临时仓库：`/var/folders/6m/zn3fr14x6856870jqqfmpnx80000gn/T/tmp.7Fw975gkJY/repo`
- Harness 版本：当前开发分支（req-23 实现）
- 测试时间：2026-04-17

## 测试步骤

1. 在临时仓库初始化 harness 工作流
2. 创建 bugfix：`harness bugfix "SKILL.md missing bugfix command"`
3. 填写 `regression/diagnosis.md` 与 `bugfix.md`
4. 依次执行 `harness next` 推进阶段

## 验证结果

| 阶段流转 | 结果 | 备注 |
|---------|------|------|
| `regression → executing` | 通过 | `workflow_next` 正确识别 bugfix 模式 |
| `executing → testing` | 通过 | - |
| `testing → acceptance` | 通过 | - |
| `acceptance → done` | 通过 | 状态文件 `status` 自动更新为 `done` |

## 状态文件校验

```yaml
id: "bugfix-1"
title: "SKILL.md missing bugfix command"
stage: "done"
status: "done"
completed_at: "2026-04-17"
stage_timestamps:
  executing: "2026-04-17T07:30:27.835817+00:00"
  testing: "2026-04-17T07:34:46.625022+00:00"
  acceptance: "2026-04-17T07:34:51.539230+00:00"
  done: "2026-04-17T07:34:55.971925+00:00"
```

## 技术总监模式切换验证

- `technical-director.md` 中已定义 bugfix 模式识别规则（SOP Step 2：检查 `current_requirement` 前缀）
- 流程图明确区分 Mode A（六阶段）与 Mode B（四阶段，`regression` 作为入口）
- 端到端推进过程中未出现 `planning` 角色加载请求，符合设计

## lint 验证

在临时仓库执行：

```bash
python3 tools/lint_harness_repo.py --root . --strict-claude --strict-stage-roles
```

结果：`Repository Harness Workflow v2 lint passed.`

确认 lint 脚本对 `.workflow/flow/bugfixes/` 目录结构无报错。

## 发现的问题与修复

### 问题 1：`workflow_next` 不支持 `regression` 阶段

**现象**：`harness next` 从 `regression` 阶段推进时提示 `Unknown stage: regression`。

**根因**：`WORKFLOW_SEQUENCE` 未包含 `regression` 阶段，且 `workflow_next` 未区分 bugfix 模式。

**修复**：
- 新增 `BUGFIX_SEQUENCE = ["regression", "executing", "testing", "acceptance", "done"]`
- `workflow_next` 根据 `current_requirement` 前缀选择对应序列
- 同步修复 `workflow_fast_forward` 与 `list_active_requirements` 对 bugfix 状态目录的支持

### 问题 2：`load_simple_yaml` 无法解析嵌套字典

**现象**：`workflow_next` 在更新 `stage_timestamps` 时抛出 `TypeError: list indices must be integers or slices, not str`。

**根因**：`save_simple_yaml` 会将嵌套字典序列化为多行缩进格式，但 `load_simple_yaml` 原实现只能解析列表子项，无法解析字典子项。

**修复**：重写 `load_simple_yaml`，在解析空值子节点时同时支持列表（`- `）和字典（`key: value`）两种缩进格式。

## 经验沉淀

已将 bugfix 模式下的 regression 阶段经验写入 `.workflow/context/experience/roles/regression.md`（经验五）。

## 结论

req-23 的 bugfix 快速修复流程已端到端验证通过，核心变更（chg-01 ~ chg-04）全部就绪。
