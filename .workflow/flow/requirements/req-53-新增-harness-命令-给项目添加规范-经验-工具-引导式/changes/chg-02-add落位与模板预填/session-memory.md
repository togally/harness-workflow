# Session Memory — chg-02（_pad_add 真实落位 + 模板预填）

## 1. Current Goal

为 chg-02 落 plan.md（§1~§6），确定 3 份 .tmpl 模板字面 + `_pad_add` 替换 stub 的精确实现 + `_resolve_pad_target` helper + pyproject.toml package-data 增补 + 8 条 pytest TC。

## 2. Context Chain

- Level 0: 主 agent
- Level 1: analyst / opus（Phase 2 + Phase 3 一气完成）

## 3. 关键决策（chg-02 范围内）

- **模板路径选择**：`assets/templates/project-add/{kind}.md.tmpl`，与既有 `assets/templates/project-skeleton/` 平级而非嵌入。理由：skeleton 是 install 时拷的 index 模板，project-add 是 user 跑命令时渲染的单条目模板，语义不同；分目录便于 future 扩展（如 add v2 加 `roleset.md.tmpl`）。
- **slug 生成走 `_path_slug`（既有 helper, line 2545）**：与 `harness requirement` / `harness bugfix` 同款。中文 title 走 `slugify_preserve_unicode` 保留中文（与 req-48 系列 path 处理一致）。fallback `slug = _path_slug(title) or title` 兜底。
- **模板渲染走最小替换**：用 `str.replace("{{ slug }}", ...)` 而非 `render_template` helper（line 268）。理由：项目级 tmpl 仅 4 个字段（slug / scope / title / created_at），无复杂条件分支；最小替换降低耦合。
- **scope 字段在 tool kind 时硬编码 "tools"**（写入 frontmatter）：与 `_load_project_level_index` scope_map 中 tools 的语义一致；user 只看到 `scope: tools` 行，不会困惑。
- **write_if_missing 幂等**：与 `_bootstrap_project_skeleton` 同款，不覆盖已存在文件。重复跑命令 → stderr 提示 "已存在，跳过" + exit 0（不报 ABORT，避免 user 不小心重跑就失败）。

## 4. 未做（chg-02 边界）

- 不动 index.md（chg-03 做）
- 不调 git add（chg-03 做）
- 不打 stderr 加载链活证（chg-03 做）
- 不实装 questionary 引导（chg-04 做）

## 5. 待沉淀经验（chg 完成后回填）

- **"模板分两类：install 时模板 vs 命令时模板"** —— `project-skeleton/` 是 install 一次性拷的 index 模板；`project-add/` 是命令多次渲染的条目模板；两者不复用，路径分离。
- **"slug 中文保留 vs ASCII-only"** —— `_path_slug` 走 `slugify_preserve_unicode`，与 `harness requirement` 一致；中文 title 在 macOS / Linux 文件系统下都能正确创建。

## Executing Stage 完成记录

- 3 份模板创建：rule.md.tmpl / experience.md.tmpl / tool.md.tmpl（assets/templates/project-add/）
- _pad_add 真实落位（chg-02 + chg-03 一体），_resolve_pad_target helper 落地
- pyproject.toml package-data 已加 `assets/templates/project-add/**/*`
- 测试：8 TC 全 pass（test_req53_pad_add.py）

✅ chg-02 完成
