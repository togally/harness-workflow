# harness-workflow

`harness-workflow` 是一个面向 Codex / Claude Code 的 Harness Engineering 工作流仓库。

它提供两层能力：

- 全局 CLI：安装后可直接使用 `harness`
- 本地 skill：执行 `harness install` 后，会把 `harness` skill、根入口文件和 `docs/` 工作流骨架安装到当前项目

## 安装

推荐使用 `pipx`：

```bash
pipx install git+https://github.com/togally/harness-workflow.git
```

也可以直接用 `pip`：

```bash
pip install git+https://github.com/togally/harness-workflow.git
```

## 在项目中初始化

进入任意项目根目录后执行：

```bash
harness install
```

这会默认完成：

- 安装本地 `/.codex/skills/harness`
- 生成 `AGENTS.md` 和 `CLAUDE.md`（仅在缺失时创建）
- 初始化 `docs/` 下的 harness 工作流目录
- 写入 `tools/lint_harness_repo.py`

如果你只想初始化文档骨架，也可以执行：

```bash
harness init
```

## 日常工作流

```bash
harness requirement --id pet-health --title "在线健康服务"
harness change --id pet-health-booking --title "在线问诊预约" --requirement pet-health
harness plan --change pet-health-booking
harness version --id v1.0.0
```

## 目录约定

安装后项目会拥有以下核心结构：

```text
docs/
├── context/
├── memory/
├── requirements/
├── changes/
├── plans/
├── versions/
└── templates/
```

同时会生成：

- `AGENTS.md`
- `CLAUDE.md`
- `.codex/skills/harness/`

## 验证

```bash
python3 tools/lint_harness_repo.py --root . --strict-agents --strict-claude
```
