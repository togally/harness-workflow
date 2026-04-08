from __future__ import annotations

import hashlib
import json
import re
import shutil
import unicodedata
from datetime import date
from importlib.resources import files
from pathlib import Path

from harness_workflow import __version__


PACKAGE_ROOT = files("harness_workflow")
SKILL_ROOT = PACKAGE_ROOT.joinpath("assets", "skill")
TEMPLATE_ROOT = SKILL_ROOT.joinpath("assets", "templates")
HARNESS_DIR = Path(".codex") / "harness"
MANAGED_STATE_PATH = HARNESS_DIR / "managed-files.json"
CONFIG_PATH = HARNESS_DIR / "config.json"

DEFAULT_LANGUAGE = "english"
DEFAULT_CONFIG = {"language": DEFAULT_LANGUAGE, "current_version": ""}
LANGUAGE_ALIASES = {
    "english": "english",
    "en": "english",
    "cn": "cn",
    "zh": "cn",
    "chinese": "cn",
}
LANGUAGE_SPECS = {
    "english": {
        "requirements_dir": "requirements",
        "changes_dir": "changes",
        "plans_dir": "plans",
        "version_memory": "version-memory.md",
    },
    "cn": {
        "requirements_dir": "需求",
        "changes_dir": "变更",
        "plans_dir": "计划",
        "version_memory": "版本记忆.md",
    },
}


def normalize_language(value: str | None) -> str:
    if not value:
        return DEFAULT_LANGUAGE
    normalized = LANGUAGE_ALIASES.get(value.strip().lower())
    if not normalized:
        supported = ", ".join(sorted(LANGUAGE_ALIASES))
        raise SystemExit(f"Unsupported language: {value}. Supported values: {supported}")
    return normalized


def language_spec(language: str) -> dict[str, str]:
    return LANGUAGE_SPECS[normalize_language(language)]


def template_name(name: str, language: str) -> str:
    if normalize_language(language) == "english":
        english_name = name.replace(".tmpl", ".en.tmpl")
        if TEMPLATE_ROOT.joinpath(english_name).is_file():
            return english_name
    return name


def render_template(
    name: str,
    repo_name: str,
    language: str,
    replacements: dict[str, str] | None = None,
) -> str:
    text = TEMPLATE_ROOT.joinpath(template_name(name, language)).read_text(encoding="utf-8")
    mapping = {
        "{{REPO_NAME}}": repo_name,
        "{{DATE}}": date.today().isoformat(),
        "{{LANGUAGE}}": normalize_language(language),
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


def _copy_tree(source: Path, target: Path) -> None:
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        destination = target / relative
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def _project_skill_targets(root: Path) -> list[Path]:
    return [
        root / ".codex" / "skills" / "harness",
        root / ".claude" / "skills" / "harness",
    ]


def _managed_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_json(path: Path, default: dict[str, str]) -> dict[str, str]:
    if not path.exists():
        return dict(default)
    data = json.loads(path.read_text(encoding="utf-8"))
    merged = dict(default)
    merged.update({str(key): str(value) for key, value in data.items()})
    return merged


def load_config(root: Path) -> dict[str, str]:
    config = _load_json(root / CONFIG_PATH, DEFAULT_CONFIG)
    config["language"] = normalize_language(config.get("language"))
    config["current_version"] = config.get("current_version", "").strip()
    return config


def save_config(root: Path, config: dict[str, str]) -> None:
    path = root / CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(DEFAULT_CONFIG)
    payload.update(config)
    payload["language"] = normalize_language(payload.get("language"))
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_config(root: Path) -> dict[str, str]:
    config = load_config(root)
    save_config(root, config)
    return config


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
        root / "docs" / "versions" / "active",
        root / "docs" / "versions" / "archive",
        root / "docs" / "decisions",
        root / "docs" / "runbooks",
        root / "docs" / "templates",
        root / "docs" / "memory",
        root / "tools",
        root / HARNESS_DIR,
    ]


def _managed_file_contents(root: Path, language: str, include_agents: bool, include_claude: bool) -> dict[str, str]:
    repo_name = root.name
    managed = {
        "docs/README.md": render_template("docs-README.md.tmpl", repo_name, language),
        "docs/memory/constitution.md": render_template("constitution.md.tmpl", repo_name, language),
        "docs/context/experience/index.md": render_template("experience-index.md.tmpl", repo_name, language),
        "docs/context/rules/agent-workflow.md": render_template("agent-workflow.md.tmpl", repo_name, language),
        "docs/context/rules/risk-rules.md": render_template("risk-rules.md.tmpl", repo_name, language),
        "docs/context/project/project-overview.md": render_template("project-overview.md.tmpl", repo_name, language),
        "docs/context/team/development-standards.md": render_template("development-standards.md.tmpl", repo_name, language),
        "docs/templates/requirement.md": render_template("requirement.md.tmpl", repo_name, language),
        "docs/templates/requirement-changes.md": render_template("requirement-changes.md.tmpl", repo_name, language),
        "docs/templates/change.md": render_template("change.md.tmpl", repo_name, language),
        "docs/templates/change-requirement.md": render_template("change-requirement.md.tmpl", repo_name, language),
        "docs/templates/change-design.md": render_template("change-design.md.tmpl", repo_name, language),
        "docs/templates/change-plan.md": render_template("change-plan.md.tmpl", repo_name, language),
        "docs/templates/change-acceptance.md": render_template("change-acceptance.md.tmpl", repo_name, language),
        "docs/templates/session-memory.md": render_template("session-memory.md.tmpl", repo_name, language),
        "docs/templates/version-readme.md": render_template("version-readme.md.tmpl", repo_name, language),
        "docs/templates/version-memory.md": render_template("version-memory.md.tmpl", repo_name, language),
        "tools/lint_harness_repo.py": SKILL_ROOT.joinpath("scripts", "lint_harness_repo.py").read_text(encoding="utf-8"),
    }
    if include_agents:
        managed["AGENTS.md"] = render_template("AGENTS.md.tmpl", repo_name, language)
    if include_claude:
        managed["CLAUDE.md"] = render_template("CLAUDE.md.tmpl", repo_name, language)
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


def install_local_skills(root: Path, force: bool = False) -> list[Path]:
    installed: list[Path] = []
    for target in _project_skill_targets(root):
        if target.exists():
            if force:
                shutil.rmtree(target)
            else:
                installed.append(target)
                continue
        target.mkdir(parents=True, exist_ok=True)
        _copy_tree(Path(str(SKILL_ROOT)), target)
        installed.append(target)
    return installed


def ensure_harness_root(root: Path) -> dict[str, str]:
    required = [root / "docs", root / "docs" / "context", root / "docs" / "versions" / "active"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"Harness workspace is missing. Run `harness install` or `harness init` first. Missing: {', '.join(missing)}")
    return ensure_config(root)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    return slug


def resolve_artifact_id(title: str, language: str) -> str:
    title = title.strip()
    if normalize_language(language) == "cn":
        return title
    slug = slugify(title)
    if slug:
        return slug
    fallback = re.sub(r"\s+", "-", title).strip("-")
    return fallback or title


def resolve_title_and_id(
    positional: str | None,
    id_flag: str | None,
    title_flag: str | None,
    language: str,
) -> tuple[str, str]:
    if positional:
        title = positional.strip()
        return title, resolve_artifact_id(title, language)
    if title_flag:
        title = title_flag.strip()
        return title, (id_flag.strip() if id_flag else resolve_artifact_id(title, language))
    if id_flag:
        identifier = id_flag.strip()
        return identifier, identifier
    raise SystemExit("A title or id is required.")


def resolve_version_layout(root: Path, version_id: str, language: str) -> dict[str, Path]:
    spec = language_spec(language)
    version_dir = root / "docs" / "versions" / "active" / version_id
    return {
        "version_dir": version_dir,
        "requirements_dir": version_dir / spec["requirements_dir"],
        "changes_dir": version_dir / spec["changes_dir"],
        "plans_dir": version_dir / spec["plans_dir"],
        "version_memory": version_dir / spec["version_memory"],
    }


def current_version_layout(root: Path, config: dict[str, str]) -> dict[str, Path]:
    current_version = config.get("current_version", "").strip()
    if not current_version:
        raise SystemExit("No active version selected. Run `harness version <name>` first.")
    return resolve_version_layout(root, current_version, config["language"])


def resolve_requirement_reference(requirements_dir: Path, reference: str, language: str) -> Path | None:
    direct = requirements_dir / reference
    if direct.exists():
        return direct
    derived = requirements_dir / resolve_artifact_id(reference, language)
    if derived.exists():
        return derived
    return None


def append_change_to_requirement(requirement_dir: Path, change_id: str, title: str) -> None:
    change_map = requirement_dir / "changes.md"
    if not change_map.exists():
        return
    line = f"- [ ] `{change_id}`: {title}\n"
    text = change_map.read_text(encoding="utf-8")
    if line not in text:
        if text.rstrip().endswith("- None yet") or text.rstrip().endswith("- 暂无"):
            text = text.replace("- None yet", line.rstrip()).replace("- 暂无", line.rstrip())
        else:
            text = text.rstrip() + "\n" + line
        change_map.write_text(text.rstrip() + "\n", encoding="utf-8")


def init_repo(root: Path, write_agents: bool, write_claude: bool) -> int:
    created: list[str] = []
    skipped: list[str] = []
    config = ensure_config(root)
    language = config["language"]
    for directory in _required_dirs(root):
        directory.mkdir(parents=True, exist_ok=True)
    managed_contents = _managed_file_contents(root, language=language, include_agents=write_agents, include_claude=write_claude)
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
    skill_paths = install_local_skills(root, force=force_skill)
    print("Installed local skills:")
    for skill_path in skill_paths:
        print(f"- {skill_path}")
    return init_repo(root, write_agents=True, write_claude=True)


def update_repo(root: Path, check: bool = False, force_managed: bool = False) -> int:
    config = ensure_harness_root(root)
    language = config["language"]
    for directory in _required_dirs(root):
        directory.mkdir(parents=True, exist_ok=True)

    managed_contents = _managed_file_contents(root, language=language, include_agents=True, include_claude=True)
    managed_state = _load_managed_state(root)
    refreshed_state = dict(managed_state)
    actions: list[str] = []

    if check:
        actions.append("would refresh .codex/skills/harness")
        actions.append("would refresh .claude/skills/harness")
    else:
        install_local_skills(root, force=True)
        actions.append("refreshed .codex/skills/harness")
        actions.append("refreshed .claude/skills/harness")

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
        save_config(root, config)
        _save_managed_state(root, _refresh_managed_state(root, managed_contents, refreshed_state))

    print("Update summary:")
    for action in actions:
        print(f"- {action}")
    if check:
        print("")
        print("No files were changed.")
    return 0


def set_language(root: Path, language: str) -> int:
    config = ensure_config(root)
    config["language"] = normalize_language(language)
    save_config(root, config)
    print(f"Language set to {config['language']}")
    print("Run `harness update` if you want managed templates and guides to refresh in the new language.")
    return 0


def create_version(root: Path, version_name: str) -> int:
    config = ensure_harness_root(root)
    version_id = version_name.strip()
    if not version_id:
        raise SystemExit("Version name is required.")
    layout = resolve_version_layout(root, version_id, config["language"])
    repo_name = root.name
    created: list[str] = []
    skipped: list[str] = []

    layout["version_dir"].mkdir(parents=True, exist_ok=True)
    layout["requirements_dir"].mkdir(parents=True, exist_ok=True)
    layout["changes_dir"].mkdir(parents=True, exist_ok=True)
    layout["plans_dir"].mkdir(parents=True, exist_ok=True)

    replacements = {"VERSION_ID": version_id}
    write_if_missing(layout["version_dir"] / "README.md", render_template("version-readme.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(layout["version_memory"], render_template("version-memory.md.tmpl", repo_name, config["language"], replacements), created, skipped)

    config["current_version"] = version_id
    save_config(root, config)

    print(f"Active version: {version_id}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def create_requirement(root: Path, name: str | None, requirement_id: str | None = None, title: str | None = None) -> int:
    config = ensure_harness_root(root)
    repo_name = root.name
    requirement_title, resolved_id = resolve_title_and_id(name, requirement_id, title, config["language"])
    layout = current_version_layout(root, config)
    requirement_dir = layout["requirements_dir"] / resolved_id
    created: list[str] = []
    skipped: list[str] = []
    replacements = {"ID": resolved_id, "TITLE": requirement_title}

    write_if_missing(requirement_dir / "requirement.md", render_template("requirement.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(requirement_dir / "changes.md", render_template("requirement-changes.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(requirement_dir / "meta.yaml", render_template("requirement-meta.yaml.tmpl", repo_name, config["language"], replacements), created, skipped)

    print(f"Requirement workspace: {requirement_dir}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def create_change(
    root: Path,
    name: str | None,
    change_id: str | None = None,
    title: str | None = None,
    requirement_id: str = "",
) -> int:
    config = ensure_harness_root(root)
    repo_name = root.name
    change_title, resolved_id = resolve_title_and_id(name, change_id, title, config["language"])
    layout = current_version_layout(root, config)
    change_dir = layout["changes_dir"] / resolved_id
    created: list[str] = []
    skipped: list[str] = []

    linked_requirement = requirement_id.strip() if requirement_id else ""
    replacements = {"ID": resolved_id, "TITLE": change_title, "REQUIREMENT_ID": linked_requirement or "None"}
    if config["language"] == "cn" and not linked_requirement:
        replacements["REQUIREMENT_ID"] = "未指定"

    write_if_missing(change_dir / "change.md", render_template("change.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "design.md", render_template("change-design.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "plan.md", render_template("change-plan.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "acceptance.md", render_template("change-acceptance.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "session-memory.md", render_template("session-memory.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "meta.yaml", render_template("change-meta.yaml.tmpl", repo_name, config["language"], replacements), created, skipped)

    if linked_requirement:
        requirement_dir = resolve_requirement_reference(layout["requirements_dir"], linked_requirement, config["language"])
        if requirement_dir:
            append_change_to_requirement(requirement_dir, resolved_id, change_title)

    print(f"Change workspace: {change_dir}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def create_plan(root: Path, change_name: str) -> int:
    config = ensure_harness_root(root)
    layout = current_version_layout(root, config)
    candidate = layout["changes_dir"] / change_name
    if not candidate.exists():
        candidate = layout["changes_dir"] / resolve_artifact_id(change_name, config["language"])
    if not candidate.exists():
        raise SystemExit(f"Change does not exist: {change_name}")
    print(f"Plan file: {candidate / 'plan.md'}")
    print("Use writing-plans to expand this file into model-executable development and verification steps.")
    return 0
