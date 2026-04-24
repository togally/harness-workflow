# Session Memory — req-38（api-document-upload 工具闭环：触发门禁 + MCP pre-check 协议 + 存量项目同步）/ chg-01（protocols 目录 + catalog 单行引用 + 硬门禁五保护扩展）

## 1. Current Goal

新建 `.workflow/tools/protocols/mcp-precheck.md`（4 阶段状态机 + provider 参数槽）；改写 `api-document-upload.md` 前置检查为单行引用；更新 `tools/index.md` 和 `harness-manager.md §硬门禁五`；scaffold_v2 mirror 双写。

## 2. Context Chain

- Level 0: 主 agent（technical-director / opus） → executing 阶段
- Level 1: 本 subagent（executing / sonnet） → chg-01 实现

## 3. 模型自检留痕

- 期望 model = `sonnet`（按 `.workflow/context/role-model-map.yaml` roles.executing）
- 本 subagent 未能自省自身 model 一致性（Claude Code 环境不暴露自省 API），按 role-loading-protocol 降级规则留痕：**本 subagent 未能自检 model 一致性，briefing 期望 = sonnet**。

## 4. Completed Tasks

- [x] Step 1：新建 `.workflow/tools/protocols/mcp-precheck.md`（4 阶段状态机 + 参数槽声明）
- [x] Step 2：`.workflow/tools/index.md` 追加 `protocols/` 子目录语义说明段
- [x] Step 3：改写 `.workflow/tools/catalog/api-document-upload.md` apifox Provider `### 前置检查` 为单行引用 + 参数槽
- [x] Step 4：`.workflow/context/roles/harness-manager.md §硬门禁五` 第 2 条追加 `protocols` 子目录
- [x] Step 5：scaffold_v2 mirror 同步（4 个文件全部 cp）
- [x] Step 6：自检 AC-3 / AC-4 / AC-9 全 PASS

## 5. 文件改动清单

### live 文件

| 文件 | 操作 | 行数增量 |
|------|------|---------|
| `.workflow/tools/protocols/mcp-precheck.md` | 新建 | +96 行 |
| `.workflow/tools/index.md` | 追加 4 行 | +4 行 |
| `.workflow/tools/catalog/api-document-upload.md` | 前置检查块替换（-3 行 +1 行） | -2 行 |
| `.workflow/context/roles/harness-manager.md` | 第 2 条追加 protocols 说明 | +1 行（扩展同行文本） |

### scaffold_v2 mirror 文件

| mirror 路径 | 操作 |
|-------------|------|
| `src/harness_workflow/assets/scaffold_v2/.workflow/tools/protocols/mcp-precheck.md` | 新建（cp） |
| `src/harness_workflow/assets/scaffold_v2/.workflow/tools/catalog/api-document-upload.md` | 同步（cp） |
| `src/harness_workflow/assets/scaffold_v2/.workflow/tools/index.md` | 同步（cp） |
| `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` | 同步（cp） |

## 6. AC 自证 stdout

### AC-3（pre-check 协议落位）PASS

```
=== AC-3 验证 ===
--- 1. mcp-precheck.md 存在 ---
PASS: 文件存在
--- 2. ^## 章节数 ≥ 4 ---
命中数: 5
PASS: ≥ 4
--- 3. 参数槽 grep ≥ 3 行 ---
命中数: 3
PASS: ≥ 3
--- 4. tools/index.md 含 protocols/ ---
命中数: 1
PASS: ≥ 1
--- 5. scaffold_v2 mirror diff（protocols/）---
PASS: 无差异
```

### AC-4（catalog 单行引用）PASS

```
=== AC-4 验证 ===
--- 1. api-document-upload.md 含 protocols/mcp-precheck.md 引用 ---
命中数: 1
PASS: ≥ 1
--- 2. 前置检查块正文行数 ≤ 3（apifox provider）---
3 行（空行 + 引用行 + 空行）
--- 3. mcp__ 在 apifox 前置检查块数量 ---
mcp__ count: 1（≤ 1/Provider，PASS）
--- 4. scaffold_v2 mirror diff（api-document-upload.md）---
PASS: 无差异
```

### AC-9（硬门禁五保护面扩展）PASS

```
=== AC-9 验证 ===
--- 1. harness-manager.md §硬门禁五 适用范围含 protocols ---
命中数: 1
PASS: ≥ 1
--- 2. diff protocols/ live vs mirror ---
PASS: 退出码 0，无差异
--- 3. harness-manager.md mirror diff ---
PASS: 无差异
--- 4. index.md mirror diff ---
PASS: 无差异
```

## 7. default-pick 决策清单

本 chg 执行过程中无 default-pick 争议点；plan.md 所有步骤均有明确指示，无留白处推进。

## 8. 待处理捕获问题

无职责外问题。
