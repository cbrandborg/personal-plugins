# Gemini Images

Experimental MCP server and agent workflows for image generation and editing.
This is personal tooling; the repository's offline checks test filename/model
helpers, not the quality or availability of Gemini's live responses.

## Credentials

Set `GEMINI_API_KEY` in the server environment. Alternatively, explicitly set
`OP_GEMINI_API_KEY_REF` to your own 1Password secret reference and install/authenticate
the `op` CLI. No personal vault is selected by default. A plugin-local `.env`
containing `GEMINI_API_KEY` remains a fallback; do not commit it or store it in an
installation cache that may be replaced on upgrade.

## Run the server

Requires Python 3.13 and `uv`:

```bash
uv run --directory /absolute/path/to/personal-plugins/plugins/gemini-images \
  python /absolute/path/to/personal-plugins/plugins/gemini-images/server/gemini_server.py
```

Use that command and those arguments when configuring a standalone MCP host.
The bundled `.mcp.json` uses `CLAUDE_PLUGIN_ROOT`; automatic expansion in other
hosts is unverified. Configure absolute paths explicitly if your host does not
provide that variable. Shared skills do not imply identical commands/hooks in
both agents.

Pass absolute input/output paths. Relative output defaults resolve from the
server's working directory, which may be the plugin directory rather than your
project. Model availability and approximate cost values can change; the server's
estimates are not a billing guarantee. Concurrent image writes are not coordinated.

## Tests

The root `just ci` tests the actual dependency-free `server/image_helpers.py`.
It does not retrieve credentials or invoke a model.

Live integration tests require an explicit opt-in and can incur API charges:

```bash
cd plugins/gemini-images
RUN_GEMINI_INTEGRATION=1 uv run pytest tests/test_integration.py
```

Set credentials in the environment first. The standalone `scripts/test-api.py`
also requires `RUN_GEMINI_INTEGRATION=1` and reuses server key resolution.
