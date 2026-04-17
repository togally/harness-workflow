# chg-04: 端到端验证与经验沉淀

## 变更目标

用一条模拟 bug 走完整 bugfix 流程，验证各阶段流转正常，并将测试经验沉淀到经验文件。

## 变更范围

- 临时目录中的端到端 bugfix 流程验证
- `experience/roles/bugfix.md`（新建）或 `experience/roles/regression.md` 更新
- 端到端测试报告

## 验收标准

- [x] 至少用一条模拟 bug 走完 `regression → executing → testing → acceptance → done`
- [x] 验证 `technical-director.md` 在 bugfix 模式下正确切换流程图
- [x] lint 脚本在严格模式下能识别 bugfix 目录结构
- [x] 测试经验已写入 `experience/roles/bugfix.md` 或 `experience/roles/regression.md`
