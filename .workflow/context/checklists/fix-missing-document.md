# Fix Checklist — missing-document

> error_type: `missing-document`
> 对应 contract: `check_missing_document`（`src/harness_workflow/validate_contract.py`）
> 协议引用：`.workflow/context/error-protocol.md` §3

## 触发条件

以下任一情况触发此 checklist：

1. `harness validate --contract missing-document` 返回 exit 64；
2. 当前 stage 关键必需文档缺失（按 stage 分类见下方清单）；
3. `.workflow/flow/requirements/{req-id}-{slug}/changes/` 目录存在但无任何 `chg-XX-*/` 子目录（planning 阶段必需）。

## 按 stage 的必需文档清单

| stage | 必需文档 | 路径 |
|-------|---------|------|
| `requirement_review` | `requirement.md` | `.workflow/flow/requirements/{req-id}-{slug}/requirement.md` |
| `planning` | `requirement.md` + 至少一个 `changes/chg-XX-*/change.md` + `plan.md` | 同上 + `.../changes/chg-XX-{slug}/change.md` 等 |
| `executing` | `changes/chg-XX-*/plan.md`（所有 chg）+ `executing/session-memory.md` | 各 chg 子目录下 |
| `testing` | `testing/session-memory.md` 或 `testing/test-report.md` | `.workflow/flow/requirements/{req-id}-{slug}/testing/` |
| `acceptance` | `acceptance/session-memory.md` 或 `acceptance/acceptance-report.md` | 同上 |
| `done` | `done/done-report.md` | `.workflow/flow/requirements/{req-id}-{slug}/done/` |
| `regression` | `.workflow/flow/bugfixes/{bugfix-id}-{slug}/regression/diagnosis.md` | 独立 bugfix 目录 |

## 修复步骤

```bash
# 1. 查看当前 stage 和 current_requirement
python3 -m harness_workflow.cli status 2>&1 | grep -E "stage|current_requirement"

# 或直接读 runtime.yaml
cat .workflow/state/runtime.yaml | grep -E "stage|current_requirement"

# 2. 确认缺失文档
python3 -m harness_workflow.cli validate --contract missing-document 2>&1

# 3a. 缺 requirement.md（requirement_review / planning stage）：
REQ_DIR=".workflow/flow/requirements/req-99-{slug}"
mkdir -p "$REQ_DIR"
cat > "$REQ_DIR/requirement.md" << 'EOF'
# Requirement — req-99（{title}）

## 1. 背景

（填写背景）

## 2. 目标

（填写目标）

## 3. 范围

### 包含
（填写）

### 排除
（填写）

## 4. 验收条件

- [ ] AC-01：（填写）

## 5. 关联

（无）
EOF

# 3b. 缺 changes/chg-XX-*/change.md + plan.md（planning stage）：
CHG_DIR=".workflow/flow/requirements/req-99-{slug}/changes/chg-01-{slug}"
mkdir -p "$CHG_DIR"
cat > "$CHG_DIR/change.md" << 'EOF'
# Change — chg-01（{title}）

> 父需求：req-99
> 目标：（填写）

## 1. 目标

## 2. 范围
### 2.1 包含
### 2.2 排除

## 3. 验收
- [ ]

## 4. 关联 sug
EOF

cat > "$CHG_DIR/plan.md" << 'EOF'
# Plan — chg-01（{title}）

> 父需求：req-99
> 父 chg：chg-01

## 1. Steps

### Step A：...

## 2. 验证

## 3. 硬序约束

## 4. 测试用例设计

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | - | - | - | P0 |
EOF

# 3c. 缺 executing/session-memory.md：
SM_DIR=".workflow/flow/requirements/req-99-{slug}/executing"
mkdir -p "$SM_DIR"
cat > "$SM_DIR/session-memory.md" << 'EOF'
# Session Memory — req-99 / executing

## 1. Current Goal

## 2. Context Chain

## 3. Completed Tasks

## 4. Default-pick 决策

## 5. 待处理捕获问题

## 6. Results
EOF

# 4. 验证
python3 -m harness_workflow.cli validate --contract missing-document
```

## 验证步骤

```bash
# 重跑 contract lint
python3 -m harness_workflow.cli validate --contract missing-document
# 期望：PASS: missing-document — 当前 stage 必需文档完整
echo "Exit code: $?"

# 也可以跑 harness status 确认
python3 -m harness_workflow.cli status
```

## 回退路径

骨架文件创建后如发现内容错误：

```bash
# 直接编辑骨架文件填充正确内容
# 若目录建错（如 req-id 错误），删除后重建
rm -rf ".workflow/flow/requirements/req-99-wrong-slug"
```

## dogfood 样本

> 来源：req-48 executing stage session-memory.md 创建实证

**场景**：harness-manager 派发 executing subagent 前，`executing/session-memory.md` 不存在，触发 missing-document 检测。

**修复**：
```bash
mkdir -p .workflow/flow/requirements/req-48-xxx/executing
# 创建 session-memory.md 骨架
```

**结果**：`harness validate --contract missing-document` exit 0。
