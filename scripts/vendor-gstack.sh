#!/bin/sh
# vendor-gstack.sh — Vendor gstack skills into src/harness_workflow/assets/gstack-skills/
#
# Usage:
#   scripts/vendor-gstack.sh --all [commit]
#   scripts/vendor-gstack.sh <skill-name> [commit]
#   scripts/vendor-gstack.sh --all [commit] --from-local <path>
#   scripts/vendor-gstack.sh <skill-name> [commit] --from-local <path>
#
# Options:
#   --all                 Vendor all skills (47 skill dirs) + shared resources
#   <skill-name>          Vendor a single skill by name
#   [commit]              Git commit/ref to checkout (default: HEAD)
#   --from-local <path>   Read from a local clone instead of cloning from upstream
#   --upstream <url>      Override upstream URL (default: https://github.com/garrytan/gstack)
#   --force               Force re-vendor even if skill already exists
#
# Environment:
#   GSTACK_UPSTREAM_URL   Override upstream URL (alternative to --upstream)
#
# Requirements:
#   - git must be available in PATH
#   - Internet access required unless --from-local is used
#
# License:
#   harness-workflow (MIT) — this script vendors gstack (MIT, Copyright (c) 2026 Garry Tan)
#   See src/harness_workflow/assets/gstack-skills/_shared/LICENSE-gstack for full text.

set -e

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
UPSTREAM_URL="${GSTACK_UPSTREAM_URL:-https://github.com/garrytan/gstack}"
TARGET_ROOT="src/harness_workflow/assets/gstack-skills"
COMMIT="HEAD"
FROM_LOCAL=""
SKILL_ARG=""
VENDOR_ALL=0
FORCE=0

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [ $# -gt 0 ]; do
  case "$1" in
    --all)
      VENDOR_ALL=1
      shift
      ;;
    --from-local)
      if [ -z "$2" ]; then
        echo "ERROR: --from-local requires a path argument" >&2
        exit 1
      fi
      FROM_LOCAL="$2"
      shift 2
      ;;
    --upstream)
      if [ -z "$2" ]; then
        echo "ERROR: --upstream requires a URL argument" >&2
        exit 1
      fi
      UPSTREAM_URL="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --help|-h)
      head -25 "$0" | grep "^#" | sed 's/^# //' | sed 's/^#//'
      exit 0
      ;;
    -*)
      echo "ERROR: Unknown option: $1" >&2
      exit 1
      ;;
    *)
      # First positional: skill name or commit (if starts like a hash or HEAD)
      if [ -z "$SKILL_ARG" ]; then
        SKILL_ARG="$1"
      else
        # Second positional: commit
        COMMIT="$1"
      fi
      shift
      ;;
  esac
done

# Validate: must have --all or a skill name
if [ $VENDOR_ALL -eq 0 ] && [ -z "$SKILL_ARG" ]; then
  echo "ERROR: specify --all or a skill name" >&2
  echo "Usage: $0 --all [commit] | $0 <skill-name> [commit]" >&2
  exit 1
fi

# If skill name given and second positional was absorbed as commit, check
if [ $VENDOR_ALL -eq 0 ] && [ -n "$SKILL_ARG" ]; then
  : # SKILL_ARG is skill name; commit may be in COMMIT
fi

# ---------------------------------------------------------------------------
# Locate repo root (script may be called from any directory)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_ABS="$REPO_ROOT/$TARGET_ROOT"

# ---------------------------------------------------------------------------
# Resolve / validate local gstack source
# ---------------------------------------------------------------------------
resolve_source() {
  if [ -n "$FROM_LOCAL" ]; then
    # Validate path exists
    if [ ! -d "$FROM_LOCAL" ]; then
      echo "ERROR: --from-local path does not exist: $FROM_LOCAL" >&2
      exit 1
    fi
    # Validate it's a git repo
    if ! git -C "$FROM_LOCAL" rev-parse HEAD >/dev/null 2>&1; then
      echo "ERROR: --from-local path is not a git repository: $FROM_LOCAL" >&2
      exit 1
    fi
    GSTACK_SRC="$FROM_LOCAL"
    ACTUAL_COMMIT="$(git -C "$GSTACK_SRC" rev-parse HEAD)"
    echo "[vendor-gstack] Using local source: $FROM_LOCAL (commit: ${ACTUAL_COMMIT})"
  else
    # Clone to a temp directory
    TMP_DIR="$(mktemp -d)"
    trap 'rm -rf "$TMP_DIR"' EXIT INT TERM
    echo "[vendor-gstack] Cloning $UPSTREAM_URL ..."
    git clone --depth 1 "$UPSTREAM_URL" "$TMP_DIR/gstack" 2>&1
    GSTACK_SRC="$TMP_DIR/gstack"
    if [ "$COMMIT" != "HEAD" ]; then
      echo "[vendor-gstack] Checking out commit: $COMMIT"
      git -C "$GSTACK_SRC" fetch --depth 1 origin "$COMMIT" 2>&1 || true
      git -C "$GSTACK_SRC" checkout "$COMMIT" 2>&1
    fi
    ACTUAL_COMMIT="$(git -C "$GSTACK_SRC" rev-parse HEAD)"
    echo "[vendor-gstack] Cloned. Commit: ${ACTUAL_COMMIT}"
  fi
}

# ---------------------------------------------------------------------------
# Write per-skill VERSION-gstack
# ---------------------------------------------------------------------------
write_version_file() {
  skill_dir="$1"
  cat > "$skill_dir/VERSION-gstack" <<EOF
upstream_url: $UPSTREAM_URL
commit: $ACTUAL_COMMIT
vendor_timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
notes: "Vendored by scripts/vendor-gstack.sh into harness-workflow assets."
EOF
}

# ---------------------------------------------------------------------------
# Copy a single skill
# ---------------------------------------------------------------------------
vendor_skill() {
  skill_name="$1"
  src_skill_dir="$GSTACK_SRC/$skill_name"

  if [ ! -f "$src_skill_dir/SKILL.md" ]; then
    echo "[vendor-gstack] SKIP: $skill_name — no SKILL.md found in $src_skill_dir" >&2
    return
  fi

  dest_dir="$TARGET_ABS/$skill_name"
  if [ -d "$dest_dir" ] && [ $FORCE -eq 0 ]; then
    echo "[vendor-gstack] EXISTS: $skill_name (use --force to re-vendor)"
  else
    mkdir -p "$dest_dir"
    # Copy SKILL.md
    cp "$src_skill_dir/SKILL.md" "$dest_dir/SKILL.md"
    # Copy references/ if exists
    if [ -d "$src_skill_dir/references" ]; then
      cp -r "$src_skill_dir/references" "$dest_dir/references"
    fi
    # Copy scripts/ if exists
    if [ -d "$src_skill_dir/scripts" ]; then
      cp -r "$src_skill_dir/scripts" "$dest_dir/scripts"
    fi
    # Write per-skill VERSION-gstack
    write_version_file "$dest_dir"
    echo "[vendor-gstack] VENDORED: $skill_name"
  fi
}

# ---------------------------------------------------------------------------
# Copy shared resources (_shared/)
# ---------------------------------------------------------------------------
vendor_shared() {
  shared_dest="$TARGET_ABS/_shared"
  mkdir -p "$shared_dest"

  # LICENSE -> LICENSE-gstack
  if [ -f "$GSTACK_SRC/LICENSE" ]; then
    cp "$GSTACK_SRC/LICENSE" "$shared_dest/LICENSE-gstack"
    echo "[vendor-gstack] SHARED: LICENSE-gstack"
  else
    echo "[vendor-gstack] WARN: LICENSE not found in gstack root" >&2
  fi

  # Write shared VERSION-gstack
  write_version_file "$shared_dest"
  echo "[vendor-gstack] SHARED: VERSION-gstack"

  # bin/
  if [ -d "$GSTACK_SRC/bin" ]; then
    mkdir -p "$shared_dest/bin"
    cp -r "$GSTACK_SRC/bin/." "$shared_dest/bin/"
    echo "[vendor-gstack] SHARED: bin/ ($(ls "$shared_dest/bin" | wc -l | tr -d ' ') files)"
  fi

  # agents/
  if [ -d "$GSTACK_SRC/agents" ]; then
    mkdir -p "$shared_dest/agents"
    cp -r "$GSTACK_SRC/agents/." "$shared_dest/agents/"
    echo "[vendor-gstack] SHARED: agents/ ($(ls "$shared_dest/agents" | wc -l | tr -d ' ') items)"
  fi

  # scripts/
  if [ -d "$GSTACK_SRC/scripts" ]; then
    mkdir -p "$shared_dest/scripts"
    cp -r "$GSTACK_SRC/scripts/." "$shared_dest/scripts/"
    echo "[vendor-gstack] SHARED: scripts/ ($(ls "$shared_dest/scripts" | wc -l | tr -d ' ') files)"
  fi
}

# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------
resolve_source

mkdir -p "$TARGET_ABS"

if [ $VENDOR_ALL -eq 1 ]; then
  echo "[vendor-gstack] Vendoring all skills from $GSTACK_SRC ..."
  # Find all top-level directories containing SKILL.md
  skill_count=0
  for skill_dir in "$GSTACK_SRC"/*/; do
    skill_name="$(basename "$skill_dir")"
    # Skip excluded directories
    case "$skill_name" in
      .git|build|dist|node_modules|contrib|_shared|test|docs|lib|design|setup|browser-skills|extension|supabase|openclaw|hosts|model-overlays|claude|scripts|agents|bin)
        continue
        ;;
    esac
    if [ -f "$skill_dir/SKILL.md" ]; then
      vendor_skill "$skill_name"
      skill_count=$((skill_count + 1))
    fi
  done
  vendor_shared
  echo "[vendor-gstack] Done. Vendored $skill_count skills + shared resources."
  echo "[vendor-gstack] Commit anchored: $ACTUAL_COMMIT"
else
  vendor_skill "$SKILL_ARG"
  echo "[vendor-gstack] Done. Commit anchored: $ACTUAL_COMMIT"
fi
