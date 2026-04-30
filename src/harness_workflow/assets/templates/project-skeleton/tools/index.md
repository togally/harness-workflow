# Project-level Tools Index

> 项目级工具索引（artifacts/project/tools/）

本目录承载**项目独有的工具配置**，由 `harness install` 自动创建并按 req-52 / chg-03 索引懒加载契约组织。

## 加载契约

- 项目级工具 catalog 优先匹配（OQ-2 = A：项目级覆盖全局）
- `tools-manager` 派发时按本 index.md 列出的清单按需加载
- `harness install --force-managed` 不覆盖本目录（OQ-4 = A：mirror 白名单 + protected-zones 双豁免）

## 添加自家工具

```markdown
## 项目级工具清单

- my-tool-name.md — 一句话用途说明
```

每条工具放一个独立 `.md` 文件，frontmatter 含 `tool_id` / `keywords` 等字段（参考全局 `.workflow/tools/catalog/_template.md`）。

## branch-path 兼容路径

如果你的 git branch 视角下还有历史 `artifacts/{branch}/project/tools/`，加载链会按 D-modified 双轨过渡同时扫一遍兼容存量；新工具一律落本目录（`artifacts/project/tools/`）。
