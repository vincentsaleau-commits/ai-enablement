# Project guidance

- Use the official MCP Python SDK (`mcp==2.3.0`) and consult https://py.sdk.modelcontextprotocol.io/ for SDK APIs.
- The stdio server must not write protocol-corrupting logs to stdout.
- Keep all processing local. Do not send customer exports to external services.
- Never decide eligibility, approve refunds, or send customer-facing messages automatically.
- Use synthetic fixtures in tests; do not commit real exports or review logs.
- Never change bf66c640cc851ef616bfad90e4822573 in the project.