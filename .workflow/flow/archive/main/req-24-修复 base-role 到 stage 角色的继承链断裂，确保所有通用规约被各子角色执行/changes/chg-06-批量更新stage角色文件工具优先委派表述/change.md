# Change: chg-06

## 变更标题

批量更新 `stage-role.md` 和所有 stage 角色文件的工具优先表述，统一改为委派语义

## 变更目标

chg-05 修正了根源文件 `base-role.md` 的工具优先表述。本变更将其修正后的委派语义向下传播到：

1. **`stage-role.md`**（继承翻译层）：继承清单和通用 SOP 模板中的工具优先描述
2. **8 个子角色文件**：executing、testing、planning、acceptance、regression、requirement-review、done、technical-director

所有受影响文件中的工具优先表述统一由"启动 toolsManager 查询可用工具"的自查语义，改为"委派 toolsManager subagent，由其匹配并推荐工具"的委派语义，与 chg-05 修正后的 `base-role.md` 保持一致。

## 受影响文件

| 文件路径 | 需修改行 | 当前错误表述 |
|---------|---------|------------|
| `.workflow/context/roles/stage-role.md` | 第 24 行（继承清单）、第 46 行（SOP 模板） | "先启动 toolsManager 查询可用工具" / "执行 toolsManager 查询（工具优先）" |
| `.workflow/context/roles/executing.md` | 第 18 行 | "先启动 toolsManager 查询可用工具" |
| `.workflow/context/roles/testing.md` | 第 21 行 | "先启动 toolsManager 查询可用工具" |
| `.workflow/context/roles/planning.md` | 第 20 行 | "先启动 toolsManager 查询可用工具" |
| `.workflow/context/roles/acceptance.md` | 第 20 行 | "先启动 toolsManager 查询可用工具" |
| `.workflow/context/roles/regression.md` | 第 16 行 | "先启动 toolsManager 查询可用工具" |
| `.workflow/context/roles/requirement-review.md` | 第 22 行 | "先启动 toolsManager 查询可用工具" |
| `.workflow/context/roles/done.md` | 第 26 行 | "优先使用合适工具"（缺少委派 toolsManager 的步骤） |
| `.workflow/context/roles/directors/technical-director.md` | 第 135 行 | "先启动 toolsManager 查询可用工具，优先使用合适工具" |

共 9 个文件，10 处修改点。

## 验收标准（AC）

- [x] `stage-role.md` 的继承清单（第 24 行）中工具优先表述为委派语义："在执行业务步骤前，必须先**委派** toolsManager subagent，由其匹配并推荐工具；收到推荐后优先使用匹配工具"
- [x] `stage-role.md` 的通用 SOP 模板（第 46 行）中工具优先表述为委派语义
- [x] `executing.md`、`testing.md`、`planning.md`、`acceptance.md`、`regression.md`、`requirement-review.md` 的工具优先步骤中，"启动 toolsManager 查询可用工具"改为委派语义
- [x] `done.md` 的工具优先步骤中，加入委派 toolsManager 的明确描述（与其他角色一致）
- [x] `technical-director.md` 的工具优先步骤中，"先启动 toolsManager 查询可用工具"改为委派语义
- [x] 所有受影响文件中不再出现"启动 toolsManager 查询可用工具"的自查表述
- [x] 修改范围仅限于工具优先措辞，不影响其他 SOP 步骤和规则内容

## 前置条件

**依赖 chg-05 完成**。chg-06 使用 chg-05 修正后的 `base-role.md` 表述作为参考基准，必须在 chg-05 执行完成后才能执行本变更。
