# Check MCP Registry First

`before-human-input`

## Rules

- Before asking the human for external information, check `workflow/context/mcp-registry.yaml` first.
- If a matching MCP exists in the registry, prefer calling the MCP to get the information.
- If no match exists but project dependencies suggest a usable MCP, recommend installation.
