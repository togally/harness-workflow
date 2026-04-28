# Fix Checklist — artifact-placement

> error_type: `artifact-placement`
> 对应 contract: `check_artifact_placement`（`src/harness_workflow/validate_contract.py`）
> 协议引用：`.workflow/context/error-protocol.md` §3

## 触发条件

以下任一情况触发此 checklist：

1. `harness validate --contract artifact-placement` 返回 exit 64；
2. `artifacts/main/requirements/{req-id}-{slug}/` 下发现 stage-name 子目录（如 `planning/` / `executing/` / `testing/` / `acceptance/` / `done/` / `regression/` / `regressions/` / `requirement-review/`）；
3. `artifacts/` 下发现机器型文件名（session-memory.md / change.md / plan.md / diagnosis.md / sug-audit.md / roadmap.md 等）。

机器型文件必须落 `.workflow/flow/requirements/{req-id}-{slug}/{stage-name}/`，不可落 `artifacts/`。

## 修复步骤

```bash
# 1. 先跑 lint，记录所有违规路径
python3 -m harness_workflow.cli validate --contract artifact-placement 2>&1 | tee /tmp/artifact-violations.txt

# 2. 从输出解析违规文件（逐行 grep）
grep -E "^\s+artifacts/" /tmp/artifact-violations.txt

# 3. 对每条违规文件，计算目标路径
#    规则：artifacts/main/requirements/{req-id}-{slug}/{stage}/{file}
#    → 目标：.workflow/flow/requirements/{req-id}-{slug}/{stage}/{file}
#    示例（planning/session-memory.md）：
SRC="artifacts/main/requirements/req-99-x/planning/session-memory.md"
DEST=".workflow/flow/requirements/req-99-x/planning/session-memory.md"

# 4. 确保目标目录存在
mkdir -p "$(dirname "$DEST")"

# 5. 迁移文件（mv，不是 cp，避免二次违规）
mv "$SRC" "$DEST"

# 6. 如有 stage-name 子目录违规（整个子目录迁移）：
SRC_DIR="artifacts/main/requirements/req-99-x/planning"
DEST_DIR=".workflow/flow/requirements/req-99-x/planning"
mkdir -p "$(dirname "$DEST_DIR")"
mv "$SRC_DIR" "$DEST_DIR"

# 7. 批量迁移脚本（适用于多文件场景）：
for violation_line in $(grep -oE "artifacts/main/requirements/[^ ]+" /tmp/artifact-violations.txt); do
    # 把 artifacts/main → .workflow/flow 前缀替换
    dest="${violation_line/artifacts\/main\//\.workflow\/flow\/}"
    mkdir -p "$(dirname "$dest")"
    mv "$violation_line" "$dest"
done

# 8. 清理空目录
find artifacts/main/requirements -type d -empty -delete 2>/dev/null || true
```

## 验证步骤

```bash
# 重跑 contract lint，期望 exit 0 + PASS 输出
python3 -m harness_workflow.cli validate --contract artifact-placement
# 期望输出：PASS: artifact-placement lint — artifacts/ 下无机器型文件
echo "Exit code: $?"
```

## 回退路径

如果迁移后原功能异常（如某流程依赖旧 artifacts 路径）：

```bash
# 回退：把文件搬回去（但先确认这是真错误，不是路径硬编码 bug）
mv "$DEST" "$SRC"
```

若确认是代码路径写死 artifacts/ 而非故意，应修正代码路径为 `.workflow/flow/requirements/...`，然后重跑迁移。

## dogfood 样本

> 来源：PetMall 项目 150 文件迁移（req-46 / chg-02 实证）

**场景**：PetMall 项目 req-41 到 req-45 共 150+ 机器型文件错落 artifacts/main/requirements/ 下。

**修复命令（实际执行过）**：
```bash
# 扫描所有违规
python3 -m harness_workflow.cli validate --contract artifact-placement 2>&1 | grep "artifacts/"

# 批量迁移（按 req-id 分批）
for req_dir in artifacts/main/requirements/req-4*/; do
    req_slug=$(basename "$req_dir")
    for stage_dir in "$req_dir"*/; do
        stage=$(basename "$stage_dir")
        dest=".workflow/flow/requirements/$req_slug/$stage"
        mkdir -p "$dest"
        mv "$stage_dir"* "$dest/" 2>/dev/null || true
    done
done

# 清理空目录
find artifacts/main/requirements -type d -empty -delete
```

**结果**：`harness validate --contract artifact-placement` exit 0，PASS。
