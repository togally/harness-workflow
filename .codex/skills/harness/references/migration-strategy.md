# Migration Strategy

## When `doc/` Already Exists

If the repository already uses `doc/`, do not force an immediate rename.

Preferred strategy:

1. Create `.workflow/` as the new canonical entrypoint
2. Add indexes and workflow entry files under `.workflow/`
3. Reference legacy `doc/` locations from `.workflow/README.md`
4. Move content gradually when a real maintenance opportunity appears

## When `AGENTS.md` Already Exists

If `AGENTS.md` already exists:

1. Keep it in place
2. Detect whether it already points to project docs
3. If it does not, recommend a manual merge
4. Do not overwrite it without explicit approval

## When The Repository Already Has Planning Or Decision Docs

Map what exists before creating duplicates.

- Existing ADRs can remain where they are if `.workflow/README.md` links them
- Existing plans can remain if there is a clear active/archive distinction
- Existing architecture docs can be referenced from `.workflow/context/project/` indexes
