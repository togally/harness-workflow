# Switch Between Plan Mode and Act Mode

`context-maintenance`

## Rules

- `Plan Mode`: load only the file tree, workflow state, version `meta.yaml`, requirement/change/plan indexes, and the smallest useful rules to scope and sequence the work.
- `Act Mode`: load only the concrete files being changed, the active change / plan, verification commands, and relevant logs; do not keep the whole file tree in context.
- Run one context-maintenance check before switching from planning to acting, and again before moving from one submodule to the next.
