# Target Layout

## Canonical Structure

```text
docs/
├── README.md
├── context/
│   ├── team/
│   ├── project/
│   ├── experience/
│   │   └── index.md
│   └── rules/
│       └── agent-workflow.md
├── changes/
│   ├── active/
│   └── archive/
├── plans/
│   ├── active/
│   └── archive/
├── decisions/
├── runbooks/
├── templates/
└── memory/
    └── constitution.md
```

## Meaning

- `docs/context/team/`: stable team-wide rules and conventions
- `docs/context/project/`: current project facts and architecture
- `docs/context/experience/`: indexed lessons, pitfalls, self-checks
- `docs/context/rules/`: detailed agent workflow and execution rules
- `docs/changes/`: per-change workspace with requirement, design, plan, acceptance, and session memory
- `docs/plans/`: cross-change or shared plans
- `docs/decisions/`: architecture and technical decisions
- `docs/runbooks/`: startup, deploy, recovery, troubleshooting guides
- `docs/templates/`: reusable document templates
- `docs/memory/`: durable memory that survives across changes and sessions
