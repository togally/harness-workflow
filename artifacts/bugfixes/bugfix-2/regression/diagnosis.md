## 问题描述
用户要求回归"角色产生的制品应该有缺失"。用户明确指出：**所有制品都应该输出到 `artifacts/` 目录**，而非 `.workflow/state/` 或 `.workflow/flow/`。

## 证据

### 1. 用户期望的制品结构
```
/Users/jiazhiwei/claudeProject/harness-workflow/
└── artifacts/
    ├── requirements/    ✅ 正确（已有 req-01, req-05, req-12~req-26 等）
    ├── changes/         ❌ 缺失（实际在 .workflow/state/changes/）
    ├── bugfixes/        ❌ 缺失（实际在 .workflow/state/bugfixes/）
    └── regressions/      ❌ 缺失（实际在 .workflow/flow/regressions/）
```

### 2. Bugfix-2 目录位置错误
- **实际位置**: `.workflow/state/bugfixes/bugfix-2/`
- **预期位置**: `artifacts/bugfixes/bugfix-2/`（根据用户要求）

### 2. Bugfix-2 缺失制品清单
| 制品 | 预期位置 | 实际状态 |
|------|----------|----------|
| session-memory.md | `.workflow/flow/bugfixes/bugfix-2/` | 仅有空目录 `.workflow/state/bugfixes/bugfix-2/session-memory/` |
| test-evidence.md | `.workflow/flow/bugfixes/bugfix-2/` | 缺失 |
| regression/diagnosis.md | `.workflow/flow/bugfixes/bugfix-2/regression/` | 缺失 |
| regression/required-inputs.md | `.workflow/flow/bugfixes/bugfix-2/regression/` | 缺失 |

### 3. 正确结构参考（bugfix-1）
```
.workflow/flow/bugfixes/bugfix-1-ff模式应单次生效/
├── bugfix.md
├── session-memory.md
├── test-evidence.md
└── regression/
    ├── diagnosis.md
    └── required-inputs.md
```

### 4. 相关历史
- Commit `7352f06`: "fix: 清理状态文件并修复 archive 问题" 删除了 `.workflow/flow/requirements/req-25-...` 下大量制品
- req-28 在 `.workflow/state/requirements/` 中标记为 `status: "active"`，但 `runtime.yaml` 的 `active_requirements: []` 为空

## 根因分析

1. **制品目录规范不一致**: `harness bugfix` 命令创建 bugfix 时使用了 `.workflow/state/bugfixes/` 而非用户要求的 `artifacts/bugfixes/`
2. **requirements 已正确实现**: req 系列已正确输出到 `artifacts/requirements/`
3. **changes 和 bugfixes 未迁移**: `harness change` 和 `harness bugfix` 命令未遵循同一规范
4. **regressions 也分散在不同位置**: 部分在 `.workflow/flow/regressions/`，部分在 bugfix 目录内

## 结论
- [x] 真实问题
- [ ] 误判

## 路由决定
- **问题类型**: 实现/测试问题
- **目标阶段**: testing（修复 harness change/bugfix 命令的输出目录问题）

## 需要人工提供的信息
无

## 修复建议
1. **立即修复**: 将 `.workflow/state/bugfixes/bugfix-2/` 移动到 `artifacts/bugfixes/bugfix-2/`
2. **命令规范修复**: 修改 `harness bugfix` 命令使其输出到 `artifacts/bugfixes/` 而非 `.workflow/state/bugfixes/`
3. **命令规范修复**: 修改 `harness change` 命令使其输出到 `artifacts/changes/` 而非 `.workflow/state/changes/`
4. **统一制品结构**:
   ```
   artifacts/
   ├── requirements/    # 已正确实现
   ├── changes/
   │   └── req-XX/
   │       └── chg-XX/
   ├── bugfixes/
   │   └── bugfix-X/
   └── regressions/
   ```
