# Fix Checklist — schema-audit

> error_type: `schema-audit`
> 对应 contract: `check_schema_audit`（`src/harness_workflow/validate_contract.py`）
> 协议引用：`.workflow/context/error-protocol.md` §3

## 触发条件

以下任一情况触发此 checklist：

1. `harness validate --contract schema-audit` 返回 exit 64；
2. `.workflow/state/requirements/` 下存在 `req-XX/`（纯数字目录）残留（旧格式，应为 `req-XX-{slug}.yaml` 文件）；
3. `.workflow/state/bugfixes/` 下存在 `bugfix-XX/`（纯数字目录）残留。

旧目录结构是 pre-flow-layout 时代遗留，新版本所有 requirement/bugfix 元数据应以 `req-XX-{slug}.yaml` 或 `bugfix-XX-{slug}.yaml` 文件形式存在。

## 修复步骤

```bash
# 1. 扫描违规目录
python3 -m harness_workflow.cli validate --contract schema-audit 2>&1 | tee /tmp/schema-violations.txt

# 2. 列出所有纯数字需求目录
ls .workflow/state/requirements/ | grep -E '^req-[0-9]+$'
ls .workflow/state/bugfixes/ 2>/dev/null | grep -E '^bugfix-[0-9]+$'

# 3. 针对每个旧目录，选择以下三种修复路径之一：

# --- 路径 A：迁移到 yaml 文件（推荐，旧目录有有效内容）---
OLD_DIR=".workflow/state/requirements/req-99"
# 检查是否已存在对应 yaml
ls .workflow/state/requirements/req-99-*.yaml 2>/dev/null

# 如果已有对应 yaml，merge 内容后删除旧目录：
# （手工检查 OLD_DIR 内容与 yaml 是否一致）
rm -rf "$OLD_DIR"

# --- 路径 B：archive 旧目录（旧目录有历史价值但已完成）---
mkdir -p .workflow/state/requirements/archive/
mv "$OLD_DIR" .workflow/state/requirements/archive/

# --- 路径 C：新建 yaml + 从目录迁内容（旧目录是唯一数据源）---
OLD_DIR=".workflow/state/requirements/req-99"
SLUG=$(ls "$OLD_DIR"/*.yaml 2>/dev/null | head -1 | xargs grep -h "^title:" | sed 's/title: //' | tr ' ' '-' | tr '[:upper:]' '[:lower:]')
TARGET_YAML=".workflow/state/requirements/req-99-${SLUG:-unknown}.yaml"

# 拷贝旧目录下第一个 yaml 为新命名文件
if ls "$OLD_DIR"/*.yaml 1>/dev/null 2>&1; then
    cp "$OLD_DIR"/*.yaml "$TARGET_YAML"
fi
mv "$OLD_DIR" .workflow/state/requirements/archive/

# 4. 批量处理所有旧目录（选择路径 B 归档）：
for d in .workflow/state/requirements/req-[0-9]*/; do
    if [[ -d "$d" ]]; then
        mkdir -p .workflow/state/requirements/archive/
        mv "$d" .workflow/state/requirements/archive/
        echo "Archived: $d"
    fi
done
```

## 验证步骤

```bash
# 重跑 schema-audit contract
python3 -m harness_workflow.cli validate --contract schema-audit
# 期望：PASS: schema-audit — 无旧格式目录残留
echo "Exit code: $?"

# 确认状态目录干净
ls .workflow/state/requirements/ | grep -E '^req-[0-9]+$' && echo "FAIL: still found" || echo "OK: no old dirs"
```

## 回退路径

如果误归档了有效数据：

```bash
# 从 archive 恢复
mv .workflow/state/requirements/archive/req-99 .workflow/state/requirements/
```

若需恢复 yaml 数据，检查归档目录内容后手工合并。

## dogfood 样本

> 来源：req-41（机器型工件回 flow/requirements）迁移后状态目录清理实证

**场景**：迁移期间 `.workflow/state/requirements/req-39/` 和 `req-40/` 旧目录遗留。

**修复**：
```bash
mkdir -p .workflow/state/requirements/archive
mv .workflow/state/requirements/req-39 .workflow/state/requirements/archive/
mv .workflow/state/requirements/req-40 .workflow/state/requirements/archive/
```

**结果**：`harness validate --contract schema-audit` exit 0。
