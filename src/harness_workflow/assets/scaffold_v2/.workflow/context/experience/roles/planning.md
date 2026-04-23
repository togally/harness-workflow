# Planning Stage Experience

> Placeholder experience file. Fill in based on actual project lessons.

## Key Constraints

<!-- Record must-follow constraints here -->

## Best Practices

<!-- Record recommended approaches here -->

## Common Mistakes

<!-- Record common errors here -->

## 经验一：功能 + bugfix 合集需求的 change 拆分范式

### 场景

req-29 同时合并 sug-01（产品级 feature：ff --auto 自主推进）与 sug-08（CLI bugfix + 数据迁移：archive 判据修复 + 一次性迁移）两条建议，拆分粒度需权衡。

### 经验内容

对"一个 feature sug + 一个 bugfix sug"合集，建议采用 **3 + 2 + 1（端到端 smoke）** 的 5-change 结构：

- **feature 侧拆 3 个 change**：
  - chg-A：数据层/数据契约（数据模型 + 契约声明文件更新，无 CLI 入口）
  - chg-B：CLI 入口层 + 主循环（依赖 chg-A 的数据层）
  - chg-C（可合并到 smoke）：独立纯函数工具（如阻塞检测、渲染器）
- **bugfix 侧合 2 个 change**：
  - chg-D：判据修复 + 单测
  - chg-E：数据迁移命令 + 幂等/冲突测试
- **整合层 1 个 smoke change**：
  - chg-F：tempdir 端到端整合，覆盖所有 AC 的集成点 + 对人文档示范

这个范式的好处：
1. 每个 change 可独立并行 executing，互相不阻塞。
2. smoke change 作为最后屏障，保证"单独通过 ≠ 整体通过"的风险被兜住。
3. chg-D 可在 feature 侧任意阶段合入，不占关键路径。

### 来源

req-29（批量建议合集 2 条）— sug-01（ff --auto）+ sug-08（archive 判据）合集，5 个 change 并行 + 最后 smoke 收尾

---

## 经验二：scaffold mirror 类资产打包契约——`**/*` 全量 glob + 契约测试双锁

### 场景

`pyproject.toml` `[tool.setuptools.package-data]` 用 14 行细分 patterns 列举
`assets/scaffold_v2/.workflow/...` 子目录通配（`context/*.md` / `context/roles/*.md` /
`flow/*.md` 等），每次 mirror 演进新增子目录或新增非 `.md` 资产（如 `.yaml` /
新建的 `checklists/` 子目录 / 新建的 `experience/regression/` 子目录），都会因细分
patterns 漏列而漏装到 wheel——typical 表现是真 wheel 安装到下游项目后 `harness
install` 末尾 mirror→live 同步检测到一批 missing 文件，但开发者本地 `pip install
-e .` 因 src 路径恒可见无法暴露。

### 经验内容

1. **scaffold mirror 类资产用 `**/*` 全量 glob，而非细分 patterns 列举**：
   `assets/scaffold_v2/.workflow/**/*` 单行覆盖任意深度任意扩展名，setuptools
   >= 69 原生支持，避免子目录 / 文件类型演进时漏列回归。
2. **同时落契约测试**：`tests/test_package_data_completeness.py` 读 pyproject
   patterns 直接模拟 setuptools 匹配语义，dev 端 mirror 全集与 patterns 匹配集
   做差集；editable 模式与真 wheel 模式行为一致（不依赖 `importlib.resources.files()`
   命中安装态路径，避免 src-import 假绿）。
3. **真 wheel sanity 一次性兜底**：`pip wheel . -w /tmp/whl/ && pip install
   --target /tmp/test_inst /tmp/whl/*.whl && PYTHONPATH=/tmp/test_inst python -m
   pytest tests/test_package_data_completeness.py -v`，验证打包真值与 dev 同步。
4. **dev mirror 防污染**：契约测试同时锁死 mirror 树不得混入运行时态产物
   （`state/sessions/` / `state/feedback/` / `flow/archive/` / `__pycache__` 等）；
   `state/runtime.yaml` 与 `state/action-log.md` 作为 install bootstrap 的初始
   空模板**保留**（reg-01 analysis.md §2.4 白名单语义）。

### 反例

- 只列细分 patterns（`context/*.md` / `tools/catalog/*.md` …），下次 mirror 新增
  `context/checklists/role-inheritance-checklist.md` 漏列 → wheel 中无该文件 →
  下游 `harness install` mirror→live 同步检测到 missing → 用户报漂移。
- 只跑 `pip install -e . && pytest` 不跑真 wheel：editable 模式下
  `importlib.resources.files()` 返回 src 源码路径，与 dev 同源恒 PASS，packaging
  bug 沉默。

### 来源

req-36（harness install 同步契约完整性修复（存量项目 .workflow/ 与 scaffold_v2
mirror 保持一致））/ chg-08（pyproject.toml package-data 补齐 + 加打包契约测试）/
reg-02（CLI 路由 + packaging 双根因）实证教训。
