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

Requires Python 3.13 and `uv` 0.12.15:

```bash
uv run --locked --directory /absolute/path/to/personal-plugins/plugins/gemini-images \
  python /absolute/path/to/personal-plugins/plugins/gemini-images/server/gemini_server.py
```

Use that command and those arguments when configuring a standalone MCP host.
The bundled `.mcp.json` uses `CLAUDE_PLUGIN_ROOT`; automatic expansion in other
hosts is unverified. Configure absolute paths explicitly if your host does not
provide that variable. Shared skills do not imply identical commands/hooks in
both agents.

Supported production image models:

- `gemini-3.1-flash-lite-image` — default, lowest latency and cost
- `gemini-3.1-flash-image` — general-purpose image generation and editing
- `gemini-3-pro-image` — premium image generation and editing

Gemini 2.5 Flash Image and the old Gemini 3 image preview IDs are not supported.
Check Google's current model list before changing these IDs:
https://ai.google.dev/gemini-api/docs/models

Pass absolute input/output paths. Local uploads (`reference_image_path`,
`modify_image.image_path`, and `generate_variations.image_path`) also require an
absolute `allowed_input_root`. The server rejects inputs outside that root,
symlinked path components, files over 10 MiB, and bytes that Pillow cannot fully
decode as PNG, JPEG, or WebP. Relative output defaults resolve from the
server's working directory, which may be the plugin directory rather than your
project. Secure local uploads require descriptor-relative, no-follow file opens;
platforms without those primitives reject local uploads while text-only generation
remains available. Model availability and approximate cost values can change; the server's
estimates are not a billing guarantee. The first valid `max_generations` value
fixes the MCP server's cap for that server process; later calls cannot raise it,
while Claude Code also applies its session-scoped pre-tool guard. Concurrent
image writes are not coordinated.

The Claude pre-tool generation counter is POSIX-only. It requires Python 3,
`fcntl`, and no-follow directory-relative file opens; unsupported platforms deny
generation rather than running without the configured limit.

## Tests

The root `just ci` runs all non-integration Gemini tests against the locked runtime.
It does not retrieve credentials or invoke a model.

Live integration tests require an explicit opt-in and can incur API charges:

```bash
cd plugins/gemini-images
RUN_GEMINI_INTEGRATION=1 uv run --locked pytest tests/test_integration.py
```

Set credentials in the environment first. The standalone `scripts/test-api.py`
also requires `RUN_GEMINI_INTEGRATION=1` and reuses server key resolution.
