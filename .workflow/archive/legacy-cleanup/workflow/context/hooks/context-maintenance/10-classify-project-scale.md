# Choose Context Strategy by Project Scale

`context-maintenance`

## Rules

- Small projects (< 50 files): use about 80% token utilization as the cleanup threshold. Prefer cost-effective models such as GPT-4o or DeepSeek and keep the full conversation history unless pressure is real.
- Medium projects (50 - 500 files): use about 60% token utilization, or the completion of each sub-feature/module, as the threshold. Prefer auto-compact and switch between `Plan Mode` and `Act Mode`.
- Large or enterprise projects (> 500 files): use about 32k tokens for GPT-family models or 150k for Claude-family models as the threshold. Enforce a Repo-map + RAG hybrid strategy, never read more than 10 full files at once, and prefer multi-agent module isolation.
