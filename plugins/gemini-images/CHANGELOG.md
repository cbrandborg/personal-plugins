## 0.2.1 - 2026-10-29

- Move the MCP server to MCP Python SDK 2 (`MCPServer`, formerly `FastMCP`).
- Lock session stats and output-file naming, since SDK 2 runs tool calls on worker threads.
- Refresh locked dependencies, including Pillow 13 and google-genai 2.33.

## 0.2.0 - 2026-09-16

- Add Gemini 3.1 Flash Lite Image and make it the default.
- Replace deprecated preview IDs with stable Gemini 3.1 Flash Image and Gemini 3 Pro Image IDs.
- Remove discontinued Gemini 2.5 Flash Image support.

## 0.1.1 - 2026-09-07

- Test shared production helpers, make credentials explicit, and require live-test opt-in.

