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
WORKFLOW_RUNTIME_PATH = Path("docs") / "context" / "rules" / "workflow-runtime.yaml"

DEFAULT_LANGUAGE = "english"
DEFAULT_CONFIG = {"language": DEFAULT_LANGUAGE, "current_version": ""}
LANGUAGE_ALIASES = {
    "english": "english",
    "en": "english",
    "cn": "cn",
    "zh": "cn",
    "chinese": "cn",
}
DEFAULT_RUNTIME = {
    "current_version": "",
    "executing_version": "",
    "active_versions": {},
}
DEFAULT_VERSION_META = {
    "id": "",
    "title": "",
    "status": "draft",
    "stage": "idle",
    "current_task": "",
    "next_action": "",
    "current_artifact_kind": "",
    "current_artifact_id": "",
    "suggested_skill": "",
    "assistant_prompt": "",
    "approval_required": False,
    "completed_tasks": [],
    "pending_tasks": [],
    "requirement_ids": [],
    "change_ids": [],
}
WORKFLOW_SEQUENCE = [
    "requirement_review",
    "changes_review",
    "plan_review",
    "ready_for_execution",
    "executing",
    "done",
]
LANGUAGE_SPECS = {
    "english": {
        "requirements_dir": "requirements",
        "changes_dir": "changes",
        "plans_dir": "plans",
        "archive_dir": "archive",
        "version_memory": "version-memory.md",
    },
    "cn": {
        "requirements_dir": "需求",
        "changes_dir": "变更",
        "plans_dir": "计划",
        "archive_dir": "归档",
        "version_memory": "版本记忆.md",
    },
}

ITEM_META_ORDER = ["id", "title", "status", "kind", "requirement", "owner", "created_at"]


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


def load_runtime(root: Path) -> dict[str, object]:
    path = root / WORKFLOW_RUNTIME_PATH
    if not path.exists():
        return dict(DEFAULT_RUNTIME)
    data = json.loads(path.read_text(encoding="utf-8"))
    payload = dict(DEFAULT_RUNTIME)
    payload.update(data)
    if not isinstance(payload.get("active_versions"), dict):
        payload["active_versions"] = {}
    return payload


def save_runtime(root: Path, runtime: dict[str, object]) -> None:
    path = root / WORKFLOW_RUNTIME_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(DEFAULT_RUNTIME)
    payload.update(runtime)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
        "docs/context/rules/development-flow.md": render_template("development-flow.md.tmpl", repo_name, language),
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
        "archive_dir": version_dir / spec["archive_dir"],
        "version_memory": version_dir / spec["version_memory"],
    }


def load_item_meta(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    payload: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            try:
                payload[key.strip()] = json.loads(value)
            except json.JSONDecodeError:
                payload[key.strip()] = value.strip('"')
        else:
            payload[key.strip()] = value
    return payload


def save_item_meta(path: Path, payload: dict[str, str]) -> None:
    ordered_keys = [key for key in ITEM_META_ORDER if key in payload] + [key for key in payload if key not in ITEM_META_ORDER]
    lines = [f"{key}: {json.dumps(str(payload.get(key, '')), ensure_ascii=False)}" for key in ordered_keys]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def replace_in_file(path: Path, replacements: dict[str, str]) -> None:
    if not path.exists() or not replacements:
        return
    text = path.read_text(encoding="utf-8")
    updated = text
    for source, target in replacements.items():
        updated = updated.replace(source, target)
    if updated != text:
        path.write_text(updated, encoding="utf-8")


def remap_identifier_list(values: list[object], mapping: dict[str, str]) -> list[str]:
    return [mapping.get(str(value), str(value)) for value in values]


def remap_meta_strings(meta: dict[str, object], replacements: dict[str, str]) -> dict[str, object]:
    payload = dict(meta)
    for field in ("current_task", "next_action", "assistant_prompt"):
        current = str(payload.get(field, ""))
        for source, target in replacements.items():
            current = current.replace(source, target)
        payload[field] = current
    return payload


def fallback_stage_for_artifacts(meta: dict[str, object], requirement_ids: list[str], change_ids: list[str]) -> dict[str, object]:
    payload = dict(meta)
    if change_ids:
        focus_change = change_ids[-1]
        payload.update(
            {
                "status": "in_progress",
                "stage": "changes_review",
                "current_task": f"Review change {focus_change}",
                "next_action": "Discuss the change list and confirm the active change, then run `harness next`.",
                "current_artifact_kind": "change",
                "current_artifact_id": focus_change,
                "suggested_skill": "brainstorming",
                "assistant_prompt": f"Use brainstorming to refine change {focus_change}, fill the change document, and stop for human review.",
                "approval_required": True,
            }
        )
        return payload
    if requirement_ids:
        focus_requirement = requirement_ids[-1]
        payload.update(
            {
                "status": "in_progress",
                "stage": "requirement_review",
                "current_task": f"Review requirement {focus_requirement}",
                "next_action": "Discuss and confirm the requirement, then run `harness next` to move into change design.",
                "current_artifact_kind": "requirement",
                "current_artifact_id": focus_requirement,
                "suggested_skill": "brainstorming",
                "assistant_prompt": f"Use brainstorming to draft and refine requirement {focus_requirement} in its document, then stop for human review.",
                "approval_required": True,
            }
        )
        return payload
    payload.update(
        {
            "status": "in_progress",
            "stage": "idle",
            "current_task": "Create or review the first requirement",
            "next_action": "Run `harness requirement <title>` to begin requirement drafting.",
            "current_artifact_kind": "",
            "current_artifact_id": "",
            "suggested_skill": "",
            "assistant_prompt": "",
            "approval_required": False,
        }
    )
    return payload


def list_existing_versions(root: Path) -> list[str]:
    active_dir = root / "docs" / "versions" / "active"
    if not active_dir.exists():
        return []
    return sorted(path.name for path in active_dir.iterdir() if path.is_dir())


def active_version_instruction(root: Path, version_id: str = "") -> str:
    if version_id:
        return f'Run `harness active "{version_id}"`.'
    version_ids = list_existing_versions(root)
    if len(version_ids) == 1:
        return f'Run `harness active "{version_ids[0]}"`.'
    if version_ids:
        choices = ", ".join(f"`{item}`" for item in version_ids)
        return f"Run `harness active <version>` for one of: {choices}."
    return "Run `harness version <name>` first."


def workflow_blockers(root: Path, config: dict[str, str], runtime: dict[str, object]) -> list[str]:
    blockers: list[str] = []
    version_ids = list_existing_versions(root)
    if not version_ids:
        return blockers

    runtime_version = str(runtime.get("current_version", "")).strip()
    config_version = str(config.get("current_version", "")).strip()

    if runtime_version != config_version:
        if runtime_version and config_version:
            blockers.append(
                f"workflow runtime points to `{runtime_version}` but harness config points to `{config_version}`. "
                f"{active_version_instruction(root)}"
            )
        else:
            missing_side = "workflow runtime" if not runtime_version else "harness config"
            selected = config_version or runtime_version
            blockers.append(
                f"{missing_side} is missing the active version while `{selected}` exists elsewhere. "
                f"{active_version_instruction(root, selected)}"
            )

    effective_version = runtime_version or config_version
    if not effective_version:
        blockers.append(f"workflow routing has no active version. {active_version_instruction(root)}")
        return blockers

    if effective_version not in version_ids:
        blockers.append(
            f"active version `{effective_version}` does not exist under `docs/versions/active/`. "
            f"{active_version_instruction(root)}"
        )
        return blockers

    if not version_meta_path(root, effective_version).exists():
        blockers.append(
            f"active version `{effective_version}` is missing `meta.yaml`. Restore or recreate the version, then "
            f"{active_version_instruction(root, effective_version)}"
        )
    return blockers


def require_active_version_id(root: Path, config: dict[str, str], runtime: dict[str, object] | None = None) -> str:
    runtime_payload = dict(runtime or load_runtime(root))
    blockers = workflow_blockers(root, config, runtime_payload)
    if blockers:
        raise SystemExit(f"Workflow is blocked: {blockers[0]}")
    return str(runtime_payload.get("current_version", "") or config.get("current_version", "")).strip()


def current_version_layout(root: Path, config: dict[str, str]) -> dict[str, Path]:
    current_version = require_active_version_id(root, config)
    return resolve_version_layout(root, current_version, config["language"])


def version_meta_path(root: Path, version_id: str) -> Path:
    return root / "docs" / "versions" / "active" / version_id / "meta.yaml"


def load_version_meta(root: Path, version_id: str) -> dict[str, object]:
    path = version_meta_path(root, version_id)
    if not path.exists():
        payload = dict(DEFAULT_VERSION_META)
        payload["id"] = version_id
        payload["title"] = version_id
        return payload
    data = json.loads(path.read_text(encoding="utf-8"))
    payload = dict(DEFAULT_VERSION_META)
    payload.update(data)
    return payload


def save_version_meta(root: Path, version_id: str, meta: dict[str, object]) -> None:
    path = version_meta_path(root, version_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(DEFAULT_VERSION_META)
    payload.update(meta)
    payload["id"] = version_id
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_workflow_state(root: Path) -> tuple[dict[str, str], dict[str, object]]:
    config = ensure_harness_root(root)
    runtime = load_runtime(root)
    save_runtime(root, runtime)
    return config, runtime


def sync_runtime_version(root: Path, version_id: str, meta: dict[str, object], runtime: dict[str, object] | None = None) -> dict[str, object]:
    runtime_payload = dict(runtime or load_runtime(root))
    active_versions = dict(runtime_payload.get("active_versions", {}))
    active_versions[version_id] = {
        "status": str(meta.get("status", "draft")),
        "stage": str(meta.get("stage", "idle")),
        "current_task": str(meta.get("current_task", "")),
        "next_action": str(meta.get("next_action", "")),
        "current_artifact_kind": str(meta.get("current_artifact_kind", "")),
        "current_artifact_id": str(meta.get("current_artifact_id", "")),
        "suggested_skill": str(meta.get("suggested_skill", "")),
        "approval_required": bool(meta.get("approval_required", False)),
    }
    runtime_payload["active_versions"] = active_versions
    return runtime_payload


def persist_workflow_state(root: Path, version_id: str, meta: dict[str, object], runtime: dict[str, object]) -> None:
    save_version_meta(root, version_id, meta)
    runtime["current_version"] = version_id
    save_runtime(root, sync_runtime_version(root, version_id, meta, runtime))


def select_focus_change(meta: dict[str, object]) -> str:
    current_kind = str(meta.get("current_artifact_kind", ""))
    current_id = str(meta.get("current_artifact_id", ""))
    if current_kind in {"change", "plan"} and current_id:
        return current_id
    change_ids = [str(item) for item in meta.get("change_ids", [])]
    return change_ids[-1] if change_ids else ""


def apply_stage_transition(meta: dict[str, object], *, execute: bool = False, fast_forward: bool = False) -> dict[str, object]:
    payload = dict(meta)
    stage = str(payload.get("stage", "idle"))
    requirement_id = str(payload.get("current_artifact_id", "")) if str(payload.get("current_artifact_kind", "")) == "requirement" else ""
    focus_change = select_focus_change(payload)

    if fast_forward:
        payload.update(
            {
                "stage": "ready_for_execution",
                "status": "review",
                "current_task": "Confirm whether to start implementation",
                "next_action": "Run `harness next --execute` after the final review.",
                "suggested_skill": "",
                "assistant_prompt": "Review the current requirement, changes, and plan documents. Do not start coding until the human confirms execution.",
                "approval_required": True,
            }
        )
        return payload

    if stage == "requirement_review":
        payload.update(
            {
                "stage": "changes_review",
                "status": "review",
                "current_task": f"Split reviewed requirement {requirement_id or '(current requirement)'} into changes",
                "next_action": "Create or refine change documents, then run `harness next`.",
                "suggested_skill": "brainstorming",
                "assistant_prompt": f"Use brainstorming to decompose the approved requirement into independently deliverable changes, create or update the change documents, and stop for human review before advancing.",
                "approval_required": True,
            }
        )
        return payload

    if stage == "changes_review":
        if not focus_change:
            raise SystemExit("No changes exist yet. Create at least one `harness change` before advancing.")
        payload.update(
            {
                "stage": "plan_review",
                "status": "review",
                "current_task": f"Draft and review the plan for change {focus_change}",
                "next_action": f"Generate or review the plan for {focus_change}, then run `harness next`.",
                "current_artifact_kind": "change",
                "current_artifact_id": focus_change,
                "suggested_skill": "writing-plans",
                "assistant_prompt": f"Use writing-plans to turn change {focus_change} into a model-executable implementation plan, then stop for human review.",
                "approval_required": True,
            }
        )
        return payload

    if stage == "plan_review":
        payload.update(
            {
                "stage": "ready_for_execution",
                "status": "review",
                "current_task": "Review complete. Waiting for execution confirmation",
                "next_action": "Run `harness next --execute` to start implementation.",
                "suggested_skill": "",
                "assistant_prompt": "Ask the human to confirm execution. Do not start implementation before explicit confirmation.",
                "approval_required": True,
            }
        )
        return payload

    if stage == "ready_for_execution":
        if not execute:
            raise SystemExit("Current version is ready_for_execution. Run `harness next --execute` to confirm execution.")
        payload.update(
            {
                "stage": "executing",
                "status": "executing",
                "current_task": f"Execute approved work for {focus_change or 'the current version'}",
                "next_action": "Implement the approved plan and keep version state updated.",
                "current_artifact_kind": "change" if focus_change else str(payload.get("current_artifact_kind", "")),
                "current_artifact_id": focus_change or str(payload.get("current_artifact_id", "")),
                "suggested_skill": "executing-plans",
                "assistant_prompt": "Use executing-plans or subagent-driven-development to implement the approved plan. Keep documents and verification in sync while executing.",
                "approval_required": False,
            }
        )
        return payload

    if stage == "executing":
        payload.update(
            {
                "stage": "done",
                "status": "done",
                "current_task": "Execution finished. Summarize and verify outcomes",
                "next_action": "Review the implementation result and archive or continue as needed.",
                "suggested_skill": "verification-before-completion",
                "assistant_prompt": "Run final verification, summarize what changed, and capture any reusable lessons before closing the version.",
                "approval_required": False,
            }
        )
        return payload

    raise SystemExit("No workflow stage is active yet. Start with `harness requirement <title>`.")


def resolve_requirement_reference(requirements_dir: Path, reference: str, language: str) -> Path | None:
    direct = requirements_dir / reference
    if direct.exists():
        return direct
    derived = requirements_dir / resolve_artifact_id(reference, language)
    if derived.exists():
        return derived
    return None


def resolve_change_reference(changes_dir: Path, reference: str, language: str) -> Path | None:
    direct = changes_dir / reference
    if direct.exists():
        return direct
    derived = changes_dir / resolve_artifact_id(reference, language)
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


def rebuild_runtime_index(root: Path, runtime: dict[str, object]) -> dict[str, object]:
    payload = dict(runtime)
    payload["active_versions"] = {}
    for version_id in list_existing_versions(root):
        if version_meta_path(root, version_id).exists():
            payload = sync_runtime_version(root, version_id, load_version_meta(root, version_id), payload)
    return payload


def repair_identifier_drift(root: Path, config: dict[str, str], runtime: dict[str, object], check: bool) -> tuple[dict[str, str], dict[str, object], list[str]]:
    actions: list[str] = []
    version_map: dict[str, str] = {}
    versions_root = root / "docs" / "versions" / "active"
    version_ids = list_existing_versions(root)

    for field in ("current_version",):
        current_value = str(config.get(field, "")).strip()
        if current_value and current_value not in version_ids and version_ids:
            fallback = next((candidate for candidate in runtime.get("active_versions", {}) if candidate in version_ids), version_ids[0])
            actions.append(f"{'would roll back' if check else 'rolled back'} active version {current_value} -> {fallback}")
            if not check:
                config[field] = fallback
    for field in ("current_version", "executing_version"):
        current_value = str(runtime.get(field, "")).strip()
        if current_value and current_value not in version_ids:
            fallback = ""
            if field == "current_version" and version_ids:
                fallback = next((candidate for candidate in runtime.get("active_versions", {}) if candidate in version_ids), version_ids[0])
            actions.append(
                f"{'would roll back' if check else 'rolled back'} runtime {field} {current_value} -> {fallback or '(none)'}"
            )
            if not check:
                runtime[field] = fallback

    for version_dir in sorted(path for path in versions_root.iterdir() if path.is_dir()):
        meta_path = version_dir / "meta.yaml"
        if not meta_path.exists():
            continue
        meta = load_version_meta(root, version_dir.name)
        old_id = str(meta.get("id", "")).strip()
        if old_id and old_id != version_dir.name:
            version_map[old_id] = version_dir.name
            actions.append(f"{'would repair' if check else 'repaired'} version id {old_id} -> {version_dir.name}")
            if not check:
                if str(meta.get("title", "")) == old_id:
                    meta["title"] = version_dir.name
                meta["id"] = version_dir.name
                save_version_meta(root, version_dir.name, meta)

    if version_map:
        current_version = str(config.get("current_version", ""))
        executing_version = str(runtime.get("executing_version", ""))
        if current_version in version_map:
            config["current_version"] = version_map[current_version]
        if str(runtime.get("current_version", "")) in version_map:
            runtime["current_version"] = version_map[str(runtime.get("current_version", ""))]
        if executing_version in version_map:
            runtime["executing_version"] = version_map[executing_version]

    for version_dir in sorted(path for path in versions_root.iterdir() if path.is_dir()):
        if not (version_dir / "meta.yaml").exists():
            continue
        version_id = version_dir.name
        layout = resolve_version_layout(root, version_id, config["language"])
        requirement_map: dict[str, str] = {}
        change_map: dict[str, str] = {}

        if layout["requirements_dir"].exists():
            for requirement_dir in sorted(path for path in layout["requirements_dir"].iterdir() if path.is_dir()):
                meta_path = requirement_dir / "meta.yaml"
                if not meta_path.exists():
                    continue
                meta = load_item_meta(meta_path)
                old_id = meta.get("id", "").strip()
                if old_id and old_id != requirement_dir.name:
                    requirement_map[old_id] = requirement_dir.name
                    actions.append(f"{'would repair' if check else 'repaired'} requirement id {old_id} -> {requirement_dir.name}")
                    if not check:
                        meta["id"] = requirement_dir.name
                        save_item_meta(meta_path, meta)

        if layout["changes_dir"].exists():
            for change_dir in sorted(path for path in layout["changes_dir"].iterdir() if path.is_dir()):
                meta_path = change_dir / "meta.yaml"
                if not meta_path.exists():
                    continue
                meta = load_item_meta(meta_path)
                old_id = meta.get("id", "").strip()
                if old_id and old_id != change_dir.name:
                    change_map[old_id] = change_dir.name
                    actions.append(f"{'would repair' if check else 'repaired'} change id {old_id} -> {change_dir.name}")
                    if not check:
                        meta["id"] = change_dir.name
                        save_item_meta(meta_path, meta)

        if requirement_map or change_map:
            version_meta = load_version_meta(root, version_id)
            version_meta["requirement_ids"] = remap_identifier_list(list(version_meta.get("requirement_ids", [])), requirement_map)
            version_meta["change_ids"] = remap_identifier_list(list(version_meta.get("change_ids", [])), change_map)
            if str(version_meta.get("current_artifact_kind", "")) == "requirement":
                version_meta["current_artifact_id"] = requirement_map.get(str(version_meta.get("current_artifact_id", "")), str(version_meta.get("current_artifact_id", "")))
            if str(version_meta.get("current_artifact_kind", "")) in {"change", "plan"}:
                version_meta["current_artifact_id"] = change_map.get(str(version_meta.get("current_artifact_id", "")), str(version_meta.get("current_artifact_id", "")))
            version_meta = remap_meta_strings(version_meta, {**requirement_map, **change_map})
            if not check:
                save_version_meta(root, version_id, version_meta)

        actual_requirement_ids = []
        if layout["requirements_dir"].exists():
            actual_requirement_ids = sorted(path.name for path in layout["requirements_dir"].iterdir() if path.is_dir() and (path / "meta.yaml").exists())
        actual_change_ids = []
        if layout["changes_dir"].exists():
            actual_change_ids = sorted(path.name for path in layout["changes_dir"].iterdir() if path.is_dir() and (path / "meta.yaml").exists())

        if layout["changes_dir"].exists():
            for change_dir in sorted(path for path in layout["changes_dir"].iterdir() if path.is_dir()):
                meta_path = change_dir / "meta.yaml"
                if not meta_path.exists():
                    continue
                meta = load_item_meta(meta_path)
                requirement_ref = meta.get("requirement", "").strip()
                if requirement_ref in requirement_map:
                    actions.append(
                        f"{'would repair' if check else 'repaired'} change requirement link {requirement_ref} -> {requirement_map[requirement_ref]}"
                    )
                    if not check:
                        meta["requirement"] = requirement_map[requirement_ref]
                        save_item_meta(meta_path, meta)
                        replace_in_file(change_dir / "change.md", {requirement_ref: requirement_map[requirement_ref]})
                elif requirement_ref and requirement_ref not in actual_requirement_ids:
                    actions.append(
                        f"{'would clear' if check else 'cleared'} missing requirement link {requirement_ref} from change {change_dir.name}"
                    )
                    if not check:
                        meta["requirement"] = "None"
                        save_item_meta(meta_path, meta)
                        replace_in_file(change_dir / "change.md", {requirement_ref: "None"})

        if change_map and layout["requirements_dir"].exists():
            for requirement_dir in sorted(path for path in layout["requirements_dir"].iterdir() if path.is_dir()):
                replace_in_file(requirement_dir / "changes.md", change_map)

        version_meta = load_version_meta(root, version_id)
        tracked_requirements = [item for item in remap_identifier_list(list(version_meta.get("requirement_ids", [])), requirement_map) if item in actual_requirement_ids]
        tracked_changes = [item for item in remap_identifier_list(list(version_meta.get("change_ids", [])), change_map) if item in actual_change_ids]
        if tracked_requirements != list(version_meta.get("requirement_ids", [])) or tracked_changes != list(version_meta.get("change_ids", [])):
            actions.append(f"{'would reconcile' if check else 'reconciled'} deleted requirement/change references for {version_id}")
            version_meta["requirement_ids"] = tracked_requirements
            version_meta["change_ids"] = tracked_changes

        current_kind = str(version_meta.get("current_artifact_kind", ""))
        current_id = str(version_meta.get("current_artifact_id", ""))
        current_missing = (
            (current_kind == "requirement" and current_id and current_id not in tracked_requirements)
            or (current_kind in {"change", "plan"} and current_id and current_id not in tracked_changes)
            or (str(version_meta.get("stage", "")) in {"plan_review", "ready_for_execution", "executing", "done"} and not tracked_changes)
            or (not tracked_requirements and not tracked_changes and str(version_meta.get("stage", "")) != "idle")
        )
        if current_missing:
            actions.append(f"{'would roll back' if check else 'rolled back'} workflow state for {version_id} after deleted artifacts")
            version_meta = fallback_stage_for_artifacts(version_meta, tracked_requirements, tracked_changes)

        if not check:
            save_version_meta(root, version_id, version_meta)

    if not check:
        runtime = rebuild_runtime_index(root, runtime)
    return config, runtime, actions


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
    if not (root / WORKFLOW_RUNTIME_PATH).exists():
        save_runtime(root, dict(DEFAULT_RUNTIME))
        created.append(str(root / WORKFLOW_RUNTIME_PATH))

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
    runtime = load_runtime(root)
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
        if not (root / WORKFLOW_RUNTIME_PATH).exists():
            save_runtime(root, dict(DEFAULT_RUNTIME))
            actions.append("created docs/context/rules/workflow-runtime.yaml")
            runtime = load_runtime(root)

    config, runtime, repair_actions = repair_identifier_drift(root, config, runtime, check)
    actions.extend(repair_actions)
    if not check:
        save_config(root, config)
        save_runtime(root, runtime)

    blockers = workflow_blockers(root, config, runtime)
    for blocker in blockers:
        actions.append(f"workflow action required: {blocker}")

    print("Update summary:")
    for action in actions:
        print(f"- {action}")
    if check:
        print("")
        print("No files were changed.")
    if blockers:
        print("")
        print("Workflow is blocked until the active version is explicitly repaired.")
        return 1
    return 0


def set_language(root: Path, language: str) -> int:
    config = ensure_config(root)
    config["language"] = normalize_language(language)
    save_config(root, config)
    print(f"Language set to {config['language']}")
    print("Run `harness update` if you want managed templates and guides to refresh in the new language.")
    return 0


def create_version(root: Path, version_name: str) -> int:
    config, runtime = ensure_workflow_state(root)
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
    layout["archive_dir"].mkdir(parents=True, exist_ok=True)

    replacements = {"VERSION_ID": version_id}
    write_if_missing(layout["version_dir"] / "README.md", render_template("version-readme.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(layout["version_memory"], render_template("version-memory.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    meta = load_version_meta(root, version_id)
    meta.update(
        {
            "title": version_id,
            "status": "in_progress",
            "stage": meta.get("stage", "idle") or "idle",
            "current_task": meta.get("current_task", "") or "Create or review the first requirement",
            "next_action": meta.get("next_action", "") or "Run `harness requirement <title>` to begin requirement drafting.",
            "suggested_skill": meta.get("suggested_skill", "") or "",
            "assistant_prompt": meta.get("assistant_prompt", "") or "",
            "approval_required": bool(meta.get("approval_required", False)),
        }
    )

    config["current_version"] = version_id
    save_config(root, config)
    runtime["executing_version"] = runtime.get("executing_version", "")
    persist_workflow_state(root, version_id, meta, runtime)

    print(f"Active version: {version_id}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def create_requirement(root: Path, name: str | None, requirement_id: str | None = None, title: str | None = None) -> int:
    config, runtime = ensure_workflow_state(root)
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
    version_id = str(config["current_version"])
    meta = load_version_meta(root, version_id)
    requirement_ids = [str(item) for item in meta.get("requirement_ids", [])]
    if resolved_id not in requirement_ids:
        requirement_ids.append(resolved_id)
    meta.update(
        {
            "status": "in_progress",
            "stage": "requirement_review",
            "current_task": f"Review requirement {resolved_id}",
            "next_action": "Discuss and confirm the requirement, then run `harness next` to move into change design.",
            "current_artifact_kind": "requirement",
            "current_artifact_id": resolved_id,
            "suggested_skill": "brainstorming",
            "assistant_prompt": f"Use brainstorming to draft and refine requirement {resolved_id} in its document, then stop for human review.",
            "approval_required": True,
            "requirement_ids": requirement_ids,
        }
    )
    persist_workflow_state(root, version_id, meta, runtime)

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
    config, runtime = ensure_workflow_state(root)
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
    version_id = str(config["current_version"])
    meta = load_version_meta(root, version_id)
    change_ids = [str(item) for item in meta.get("change_ids", [])]
    if resolved_id not in change_ids:
        change_ids.append(resolved_id)
    meta.update(
        {
            "status": "in_progress",
            "stage": "changes_review" if meta.get("stage") in {"idle", "requirement_review", "changes_review"} else meta.get("stage", "changes_review"),
            "current_task": f"Review change {resolved_id}",
            "next_action": "Discuss the change list and confirm the active change, then run `harness next`.",
            "current_artifact_kind": "change",
            "current_artifact_id": resolved_id,
            "suggested_skill": "brainstorming",
            "assistant_prompt": f"Use brainstorming to refine change {resolved_id}, fill the change document, and stop for human review.",
            "approval_required": True,
            "change_ids": change_ids,
        }
    )
    persist_workflow_state(root, version_id, meta, runtime)

    print(f"Change workspace: {change_dir}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def create_plan(root: Path, change_name: str) -> int:
    config, runtime = ensure_workflow_state(root)
    layout = current_version_layout(root, config)
    candidate = layout["changes_dir"] / change_name
    if not candidate.exists():
        candidate = layout["changes_dir"] / resolve_artifact_id(change_name, config["language"])
    if not candidate.exists():
        raise SystemExit(f"Change does not exist: {change_name}")
    version_id = str(config["current_version"])
    meta = load_version_meta(root, version_id)
    meta.update(
        {
            "status": "in_progress",
            "stage": "plan_review",
            "current_task": f"Review plan for {candidate.name}",
            "next_action": "Discuss and confirm the plan, then run `harness next` to reach execution confirmation.",
            "current_artifact_kind": "plan",
            "current_artifact_id": candidate.name,
            "suggested_skill": "writing-plans",
            "assistant_prompt": f"Use writing-plans to expand plan.md for {candidate.name}, then stop for human review.",
            "approval_required": True,
        }
    )
    persist_workflow_state(root, version_id, meta, runtime)
    print(f"Plan file: {candidate / 'plan.md'}")
    print("Use writing-plans to expand this file into model-executable development and verification steps.")
    return 0


def rename_version(root: Path, current_name: str, new_name: str) -> int:
    config, runtime = ensure_workflow_state(root)
    old_id = current_name.strip()
    new_id = new_name.strip()
    if not old_id or not new_id:
        raise SystemExit("Both current and new version names are required.")
    old_dir = root / "docs" / "versions" / "active" / old_id
    new_dir = root / "docs" / "versions" / "active" / new_id
    if not old_dir.exists():
        raise SystemExit(f"Version does not exist: {old_id}")
    if new_dir.exists():
        raise SystemExit(f"Target version already exists: {new_id}")

    shutil.move(str(old_dir), str(new_dir))
    meta = load_version_meta(root, new_id)
    meta["id"] = new_id
    meta["title"] = new_id
    meta = remap_meta_strings(meta, {old_id: new_id})
    save_version_meta(root, new_id, meta)

    if str(config.get("current_version", "")) == old_id:
        config["current_version"] = new_id
    if str(runtime.get("current_version", "")) == old_id:
        runtime["current_version"] = new_id
    if str(runtime.get("executing_version", "")) == old_id:
        runtime["executing_version"] = new_id
    save_config(root, config)
    runtime = rebuild_runtime_index(root, runtime)
    save_runtime(root, runtime)
    print(f"Version renamed: {old_id} -> {new_id}")
    return 0


def rename_requirement(root: Path, current_name: str, new_name: str, version_name: str = "") -> int:
    config, runtime = ensure_workflow_state(root)
    version_id = version_name.strip() or require_active_version_id(root, config, runtime)
    layout = resolve_version_layout(root, version_id, config["language"])
    requirement_dir = resolve_requirement_reference(layout["requirements_dir"], current_name, config["language"])
    if not requirement_dir:
        raise SystemExit(f"Requirement does not exist: {current_name}")

    meta_path = requirement_dir / "meta.yaml"
    item_meta = load_item_meta(meta_path)
    old_id = item_meta.get("id", requirement_dir.name) or requirement_dir.name
    old_title = item_meta.get("title", old_id) or old_id
    new_title, new_id = resolve_title_and_id(new_name, None, None, config["language"])
    target_dir = layout["requirements_dir"] / new_id
    if target_dir.exists():
        raise SystemExit(f"Target requirement already exists: {new_id}")

    shutil.move(str(requirement_dir), str(target_dir))
    item_meta["id"] = new_id
    item_meta["title"] = new_title
    save_item_meta(target_dir / "meta.yaml", item_meta)
    replace_in_file(target_dir / "requirement.md", {old_title: new_title, old_id: new_id})

    if layout["changes_dir"].exists():
        for change_dir in sorted(path for path in layout["changes_dir"].iterdir() if path.is_dir()):
            change_meta_path = change_dir / "meta.yaml"
            if not change_meta_path.exists():
                continue
            change_meta = load_item_meta(change_meta_path)
            if change_meta.get("requirement", "") == old_id:
                change_meta["requirement"] = new_id
                save_item_meta(change_meta_path, change_meta)
                replace_in_file(change_dir / "change.md", {old_id: new_id, old_title: new_title})

    version_meta = load_version_meta(root, version_id)
    version_meta["requirement_ids"] = remap_identifier_list(list(version_meta.get("requirement_ids", [])), {old_id: new_id})
    if str(version_meta.get("current_artifact_kind", "")) == "requirement":
        version_meta["current_artifact_id"] = {old_id: new_id}.get(str(version_meta.get("current_artifact_id", "")), str(version_meta.get("current_artifact_id", "")))
    version_meta = remap_meta_strings(version_meta, {old_id: new_id, old_title: new_title})
    save_version_meta(root, version_id, version_meta)
    runtime = rebuild_runtime_index(root, runtime)
    save_runtime(root, runtime)
    print(f"Requirement renamed: {old_id} -> {new_id}")
    return 0


def rename_change(root: Path, current_name: str, new_name: str, version_name: str = "") -> int:
    config, runtime = ensure_workflow_state(root)
    version_id = version_name.strip() or require_active_version_id(root, config, runtime)
    layout = resolve_version_layout(root, version_id, config["language"])
    change_dir = resolve_change_reference(layout["changes_dir"], current_name, config["language"])
    if not change_dir:
        raise SystemExit(f"Change does not exist: {current_name}")

    meta_path = change_dir / "meta.yaml"
    item_meta = load_item_meta(meta_path)
    old_id = item_meta.get("id", change_dir.name) or change_dir.name
    old_title = item_meta.get("title", old_id) or old_id
    new_title, new_id = resolve_title_and_id(new_name, None, None, config["language"])
    target_dir = layout["changes_dir"] / new_id
    if target_dir.exists():
        raise SystemExit(f"Target change already exists: {new_id}")

    shutil.move(str(change_dir), str(target_dir))
    item_meta["id"] = new_id
    item_meta["title"] = new_title
    save_item_meta(target_dir / "meta.yaml", item_meta)
    replace_in_file(target_dir / "change.md", {old_title: new_title, old_id: new_id})

    requirement_ref = item_meta.get("requirement", "").strip()
    if requirement_ref:
        requirement_dir = resolve_requirement_reference(layout["requirements_dir"], requirement_ref, config["language"])
        if requirement_dir:
            replace_in_file(requirement_dir / "changes.md", {old_id: new_id, old_title: new_title})

    version_meta = load_version_meta(root, version_id)
    version_meta["change_ids"] = remap_identifier_list(list(version_meta.get("change_ids", [])), {old_id: new_id})
    if str(version_meta.get("current_artifact_kind", "")) in {"change", "plan"}:
        version_meta["current_artifact_id"] = {old_id: new_id}.get(str(version_meta.get("current_artifact_id", "")), str(version_meta.get("current_artifact_id", "")))
    version_meta = remap_meta_strings(version_meta, {old_id: new_id, old_title: new_title})
    save_version_meta(root, version_id, version_meta)
    runtime = rebuild_runtime_index(root, runtime)
    save_runtime(root, runtime)
    print(f"Change renamed: {old_id} -> {new_id}")
    return 0


def archive_requirement(root: Path, requirement_name: str, version_name: str = "") -> int:
    config, runtime = ensure_workflow_state(root)
    version_id = version_name.strip() or require_active_version_id(root, config, runtime)
    layout = resolve_version_layout(root, version_id, config["language"])
    requirement_dir = resolve_requirement_reference(layout["requirements_dir"], requirement_name, config["language"])
    if not requirement_dir:
        raise SystemExit(f"Requirement does not exist: {requirement_name}")

    requirement_id = requirement_dir.name
    archive_root = layout["archive_dir"]
    archive_root.mkdir(parents=True, exist_ok=True)
    archive_requirement_dir = archive_root / requirement_id
    if archive_requirement_dir.exists():
        raise SystemExit(f"Archive target already exists: {archive_requirement_dir}")

    linked_changes: list[Path] = []
    if layout["changes_dir"].exists():
        for change_dir in sorted(path for path in layout["changes_dir"].iterdir() if path.is_dir()):
            change_meta = load_item_meta(change_dir / "meta.yaml")
            if change_meta.get("requirement", "") == requirement_id:
                linked_changes.append(change_dir)

    shutil.move(str(requirement_dir), str(archive_root))
    archived_requirement_dir = archive_root / requirement_id
    archived_changes_dir = archived_requirement_dir / language_spec(config["language"])["changes_dir"]
    archived_changes_dir.mkdir(parents=True, exist_ok=True)
    archived_change_ids: list[str] = []
    for change_dir in linked_changes:
        archived_change_ids.append(change_dir.name)
        shutil.move(str(change_dir), str(archived_changes_dir))

    version_meta = load_version_meta(root, version_id)
    version_meta["requirement_ids"] = [item for item in remap_identifier_list(list(version_meta.get("requirement_ids", [])), {}) if item != requirement_id]
    version_meta["change_ids"] = [item for item in remap_identifier_list(list(version_meta.get("change_ids", [])), {}) if item not in archived_change_ids]
    current_kind = str(version_meta.get("current_artifact_kind", ""))
    current_id = str(version_meta.get("current_artifact_id", ""))
    if (current_kind == "requirement" and current_id == requirement_id) or (
        current_kind in {"change", "plan"} and current_id in archived_change_ids
    ):
        version_meta["current_artifact_kind"] = ""
        version_meta["current_artifact_id"] = ""
        version_meta["current_task"] = "Archived completed work. Select the next active requirement or change."
        version_meta["next_action"] = "Run `harness status` to review remaining active work, or create a new requirement."
    if not version_meta["requirement_ids"] and not version_meta["change_ids"] and str(version_meta.get("stage", "")) not in {"executing", "done"}:
        version_meta["stage"] = "idle"
        version_meta["status"] = "in_progress"
        version_meta["current_task"] = "Create or review the next requirement"
        version_meta["next_action"] = "Run `harness requirement <title>` to begin requirement drafting."
        version_meta["suggested_skill"] = ""
        version_meta["assistant_prompt"] = ""
        version_meta["approval_required"] = False
    save_version_meta(root, version_id, version_meta)
    runtime = rebuild_runtime_index(root, runtime)
    save_runtime(root, runtime)
    print(f"Archived requirement: {requirement_id}")
    print(f"Archive path: {archived_requirement_dir}")
    return 0


def set_active_version(root: Path, version_name: str) -> int:
    config, runtime = ensure_workflow_state(root)
    version_id = version_name.strip()
    if not version_meta_path(root, version_id).exists():
        raise SystemExit(f"Version does not exist: {version_id}")
    config["current_version"] = version_id
    save_config(root, config)
    meta = load_version_meta(root, version_id)
    persist_workflow_state(root, version_id, meta, runtime)
    print(f"Current active version set to {version_id}")
    return 0


def use_version(root: Path, version_name: str) -> int:
    return set_active_version(root, version_name)


def workflow_status(root: Path) -> int:
    config, runtime = ensure_workflow_state(root)
    current_version = str(runtime.get("current_version", "") or config.get("current_version", ""))
    print(f"current_version: {current_version or '(none)'}")
    print(f"executing_version: {runtime.get('executing_version', '') or '(none)'}")
    blockers = workflow_blockers(root, config, runtime)
    if blockers:
        print("workflow_blockers:")
        for blocker in blockers:
            print(f"- {blocker}")
    if current_version:
        meta = load_version_meta(root, current_version)
        print(f"stage: {meta.get('stage', 'idle')}")
        print(f"status: {meta.get('status', 'draft')}")
        print(f"current_task: {meta.get('current_task', '') or '(none)'}")
        print(f"next_action: {meta.get('next_action', '') or '(none)'}")
        print(f"current_artifact: {meta.get('current_artifact_kind', '')}:{meta.get('current_artifact_id', '')}".rstrip(":"))
        print(f"suggested_skill: {meta.get('suggested_skill', '') or '(none)'}")
        print(f"approval_required: {bool(meta.get('approval_required', False))}")
    return 0


def workflow_next(root: Path, execute: bool = False) -> int:
    config, runtime = ensure_workflow_state(root)
    current_version = require_active_version_id(root, config, runtime)
    meta = load_version_meta(root, current_version)
    meta = apply_stage_transition(meta, execute=execute)
    runtime["executing_version"] = current_version if meta.get("stage") == "executing" else ""
    persist_workflow_state(root, current_version, meta, runtime)
    print(f"Workflow advanced to {meta['stage']}")
    return 0


def workflow_fast_forward(root: Path) -> int:
    config, runtime = ensure_workflow_state(root)
    current_version = require_active_version_id(root, config, runtime)
    meta = apply_stage_transition(load_version_meta(root, current_version), fast_forward=True)
    runtime["executing_version"] = ""
    persist_workflow_state(root, current_version, meta, runtime)
    print("Workflow advanced to ready_for_execution")
    return 0
