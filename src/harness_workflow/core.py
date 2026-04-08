from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date
from importlib.resources import files
from pathlib import Path

from harness_workflow import __version__


PACKAGE_ROOT = files("harness_workflow")
SKILL_ROOT = PACKAGE_ROOT.joinpath("assets", "skill")
TEMPLATE_ROOT = SKILL_ROOT.joinpath("assets", "templates")
MANAGED_STATE_PATH = Path(".codex") / "harness" / "managed-files.json"


def render_template(name: str, repo_name: str, replacements: dict[str, str] | None = None) -> str:
    text = TEMPLATE_ROOT.joinpath(name).read_text(encoding="utf-8")
    mapping = {
        "{{REPO_NAME}}": repo_name,
        "{{DATE}}": date.today().isoformat(),
    }
    if replacements:
        mapping.update({f"{{{{{key}}}}}": value for key, value in replacements.items()})
    for key, value in mapping.items():
        text = text.replace(key, value)
    return text


def write_if_missing(path: Path, content: str, created: list[str], skipped: list[str]) -> None:
    if path.exists():
        skipped.append(str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(str(path))


def ensure_harness_root(root: Path) -> None:
    required = [root / "docs", root / "docs" / "context", root / "docs" / "memory"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"Harness workspace is missing. Run `harness install` or `harness init` first. Missing: {', '.join(missing)}")


def append_change_to_requirement(requirement_dir: Path, change_id: str, title: str) -> None:
    change_map = requirement_dir / "changes.md"
    if not change_map.exists():
        return
    line = f"- [ ] `{change_id}`：{title}\n"
    text = change_map.read_text(encoding="utf-8")
    if line not in text:
        if text.rstrip().endswith("- 暂无"):
            text = text.replace("- 暂无", line.rstrip())
        else:
            text = text.rstrip() + "\n" + line
        change_map.write_text(text.rstrip() + "\n", encoding="utf-8")


def _copy_tree(source: Path, target: Path) -> None:
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        destination = target / relative
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def _managed_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_managed_state(root: Path) -> dict[str, str]:
    path = root / MANAGED_STATE_PATH
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(key): str(value) for key, value in data.get("managed_files", {}).items()}


def _save_managed_state(root: Path, managed_files: dict[str, str]) -> None:
    path = root / MANAGED_STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "tool_version": __version__,
        "managed_files": dict(sorted(managed_files.items())),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _required_dirs(root: Path) -> list[Path]:
    return [
        root / "docs" / "context" / "team",
        root / "docs" / "context" / "project",
        root / "docs" / "context" / "experience",
        root / "docs" / "context" / "rules",
        root / "docs" / "requirements" / "active",
        root / "docs" / "requirements" / "archive",
        root / "docs" / "changes" / "active",
        root / "docs" / "changes" / "archive",
        root / "docs" / "plans" / "active",
        root / "docs" / "plans" / "archive",
        root / "docs" / "versions",
        root / "docs" / "decisions",
        root / "docs" / "runbooks",
        root / "docs" / "templates",
        root / "docs" / "memory",
        root / "tools",
    ]


def _managed_file_contents(root: Path, include_agents: bool, include_claude: bool) -> dict[str, str]:
    repo_name = root.name
    managed = {
        "docs/README.md": render_template("docs-README.md.tmpl", repo_name),
        "docs/memory/constitution.md": render_template("constitution.md.tmpl", repo_name),
        "docs/context/experience/index.md": render_template("experience-index.md.tmpl", repo_name),
        "docs/context/rules/agent-workflow.md": render_template("agent-workflow.md.tmpl", repo_name),
        "docs/context/rules/risk-rules.md": render_template("risk-rules.md.tmpl", repo_name),
        "docs/context/project/仓库概览.md": render_template("project-overview.md.tmpl", repo_name),
        "docs/context/team/开发规范.md": render_template("development-standards.md.tmpl", repo_name),
        "docs/templates/requirement.md": render_template("requirement.md.tmpl", repo_name),
        "docs/templates/requirement-changes.md": render_template("requirement-changes.md.tmpl", repo_name),
        "docs/templates/change.md": render_template("change.md.tmpl", repo_name),
        "docs/templates/change-requirement.md": render_template("change-requirement.md.tmpl", repo_name),
        "docs/templates/change-design.md": render_template("change-design.md.tmpl", repo_name),
        "docs/templates/change-plan.md": render_template("change-plan.md.tmpl", repo_name),
        "docs/templates/change-acceptance.md": render_template("change-acceptance.md.tmpl", repo_name),
        "docs/templates/session-memory.md": render_template("session-memory.md.tmpl", repo_name),
        "docs/templates/version-readme.md": render_template("version-readme.md.tmpl", repo_name),
        "tools/lint_harness_repo.py": SKILL_ROOT.joinpath("scripts", "lint_harness_repo.py").read_text(encoding="utf-8"),
    }
    if include_agents:
        managed["AGENTS.md"] = render_template("AGENTS.md.tmpl", repo_name)
    if include_claude:
        managed["CLAUDE.md"] = render_template("CLAUDE.md.tmpl", repo_name)
    return managed


def _refresh_managed_state(
    root: Path,
    managed_contents: dict[str, str],
    existing_state: dict[str, str] | None = None,
) -> dict[str, str]:
    state = dict(existing_state or {})
    for relative, content in managed_contents.items():
        path = root / relative
        if path.exists() and path.read_text(encoding="utf-8") == content:
            state[relative] = _managed_hash(content)
    return state


def install_local_skill(root: Path, force: bool = False) -> Path:
    target = root / ".codex" / "skills" / "harness"
    if target.exists():
        if force:
            shutil.rmtree(target)
        else:
            return target
    target.mkdir(parents=True, exist_ok=True)
    _copy_tree(Path(str(SKILL_ROOT)), target)
    return target


def init_repo(root: Path, write_agents: bool, write_claude: bool) -> int:
    created: list[str] = []
    skipped: list[str] = []
    for directory in _required_dirs(root):
        directory.mkdir(parents=True, exist_ok=True)
    managed_contents = _managed_file_contents(root, include_agents=write_agents, include_claude=write_claude)
    managed_state = _load_managed_state(root)
    for relative, content in managed_contents.items():
        write_if_missing(root / relative, content, created, skipped)
    _save_managed_state(root, _refresh_managed_state(root, managed_contents, managed_state))

    print("Created files:")
    for path in created:
        print(f"- {path}")
    print("")
    print("Skipped existing files:")
    for path in skipped:
        print(f"- {path}")
    return 0


def install_repo(root: Path, force_skill: bool = False) -> int:
    skill_path = install_local_skill(root, force=force_skill)
    print(f"Installed local skill: {skill_path}")
    return init_repo(root, write_agents=True, write_claude=True)


def update_repo(root: Path, check: bool = False, force_managed: bool = False) -> int:
    ensure_harness_root(root)
    for directory in _required_dirs(root):
        directory.mkdir(parents=True, exist_ok=True)

    managed_contents = _managed_file_contents(root, include_agents=True, include_claude=True)
    managed_state = _load_managed_state(root)
    refreshed_state = dict(managed_state)
    actions: list[str] = []

    if check:
        actions.append("would refresh .codex/skills/harness")
    else:
        install_local_skill(root, force=True)
        actions.append("refreshed .codex/skills/harness")

    for relative, content in managed_contents.items():
        path = root / relative
        desired_hash = _managed_hash(content)
        if not path.exists():
            actions.append(f"{'missing' if check else 'created'} {relative}")
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                refreshed_state[relative] = desired_hash
            continue

        current = path.read_text(encoding="utf-8")
        current_hash = _managed_hash(current)
        if current == content:
            actions.append(f"current {relative}")
            refreshed_state[relative] = desired_hash
            continue

        if managed_state.get(relative) == current_hash:
            actions.append(f"{'would update' if check else 'updated'} {relative}")
            if not check:
                path.write_text(content, encoding="utf-8")
                refreshed_state[relative] = desired_hash
            continue

        if force_managed:
            actions.append(f"{'would overwrite modified' if check else 'overwrote modified'} {relative}")
            if not check:
                path.write_text(content, encoding="utf-8")
                refreshed_state[relative] = desired_hash
            continue

        actions.append(f"skipped modified {relative}")

    if not check:
        _save_managed_state(root, _refresh_managed_state(root, managed_contents, refreshed_state))

    print("Update summary:")
    for action in actions:
        print(f"- {action}")
    if check:
        print("")
        print("No files were changed.")
    return 0


def create_requirement(root: Path, requirement_id: str, title: str) -> int:
    ensure_harness_root(root)
    repo_name = root.name
    requirement_dir = root / "docs" / "requirements" / "active" / requirement_id
    created: list[str] = []
    skipped: list[str] = []
    replacements = {"ID": requirement_id, "TITLE": title}

    write_if_missing(requirement_dir / "requirement.md", render_template("requirement.md.tmpl", repo_name, replacements), created, skipped)
    write_if_missing(requirement_dir / "changes.md", render_template("requirement-changes.md.tmpl", repo_name, replacements), created, skipped)
    write_if_missing(requirement_dir / "meta.yaml", render_template("requirement-meta.yaml.tmpl", repo_name, replacements), created, skipped)

    print(f"Requirement workspace: {requirement_dir}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def create_change(root: Path, change_id: str, title: str, requirement_id: str) -> int:
    ensure_harness_root(root)
    repo_name = root.name
    change_dir = root / "docs" / "changes" / "active" / change_id
    created: list[str] = []
    skipped: list[str] = []
    replacements = {"ID": change_id, "TITLE": title, "REQUIREMENT_ID": requirement_id or "未指定"}

    write_if_missing(change_dir / "change.md", render_template("change.md.tmpl", repo_name, replacements), created, skipped)
    write_if_missing(change_dir / "design.md", render_template("change-design.md.tmpl", repo_name, replacements), created, skipped)
    write_if_missing(change_dir / "plan.md", render_template("change-plan.md.tmpl", repo_name, replacements), created, skipped)
    write_if_missing(change_dir / "acceptance.md", render_template("change-acceptance.md.tmpl", repo_name, replacements), created, skipped)
    write_if_missing(change_dir / "session-memory.md", render_template("session-memory.md.tmpl", repo_name, replacements), created, skipped)
    write_if_missing(change_dir / "meta.yaml", render_template("change-meta.yaml.tmpl", repo_name, replacements), created, skipped)

    if requirement_id:
        requirement_dir = root / "docs" / "requirements" / "active" / requirement_id
        if requirement_dir.exists():
            append_change_to_requirement(requirement_dir, change_id, title)

    print(f"Change workspace: {change_dir}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def create_version(root: Path, version_id: str) -> int:
    ensure_harness_root(root)
    repo_name = root.name
    version_dir = root / "docs" / "versions" / version_id
    snapshot_dir = version_dir / "snapshot"
    if version_dir.exists():
        raise SystemExit(f"Version already exists: {version_id}")
    version_dir.mkdir(parents=True)
    snapshot_dir.mkdir(parents=True)

    readme = render_template("version-readme.md.tmpl", repo_name, {"VERSION_ID": version_id})
    (version_dir / "README.md").write_text(readme, encoding="utf-8")

    for relative in ["requirements", "changes", "plans", "context", "memory"]:
        source = root / "docs" / relative
        if source.exists():
            shutil.copytree(source, snapshot_dir / relative)

    print(f"Version snapshot created: {version_dir}")
    return 0


def create_plan(root: Path, change_id: str) -> int:
    ensure_harness_root(root)
    change_dir = root / "docs" / "changes" / "active" / change_id
    if not change_dir.exists():
        raise SystemExit(f"Change does not exist: {change_id}")
    print(f"Plan file: {change_dir / 'plan.md'}")
    print("Use writing-plans to expand this file into model-executable development and verification steps.")
    return 0
