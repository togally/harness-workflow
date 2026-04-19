# Target Layout

## Canonical Structure

```text
.workflow/
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

- `.workflow/context/team/`: stable team-wide rules and conventions
- `.workflow/context/project/`: current project facts and architecture
- `.workflow/context/experience/`: indexed lessons, pitfalls, self-checks
- `.workflow/context/rules/`: detailed agent workflow and execution rules
- `.workflow/changes/`: per-change workspace with requirement, design, plan, acceptance, and session memory
- `.workflow/plans/`: cross-change or shared plans
- `.workflow/decisions/`: architecture and technical decisions
- `.workflow/runbooks/`: startup, deploy, recovery, troubleshooting guides
- `.workflow/templates/`: reusable document templates
- `.workflow/memory/`: durable memory that survives across changes and sessions
