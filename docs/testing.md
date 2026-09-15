# Testing and support

## Offline checks

Install the hash-locked development dependencies into a Python 3.13+ virtual
environment with Hermes and uv 0.12.15 available, then run `PYTHON=python just ci`.
GitHub CI runs the same functional checks and adds Gitleaks and CodeQL scans:

```bash
python -m pip install --require-hashes -r requirements-dev.lock
PYTHON=python just ci
```

- Structural validation of both installation registries, manifests, and skill frontmatter.
- Actual importer regression tests: selective updates, local edits, conflict-only checks,
  failed registration, later-source failure, version/lock consistency, and validation rollback.
- Canvas script checks using temporary synthetic vaults: retries, missing files,
  paths outside the vault, malformed JSON, preservation of nodes, and exact hook references.
- Env-guard checks using synthetic files: direct paths, symlinks, nested shells,
  and allowed template paths. These do not establish comprehensive access control.
- Real Hermes Plugin Doctor validation for every manifested bundle.
- Locked Gemini helper and server-limit tests, without API calls.
- Gemini `uv.lock` freshness plus a locked runtime import smoke test using uv 0.12.15.
- A real CLI import/update example using temporary local Git repositories.

Tests do not modify installed plugins. Local CLI examples validate generated files;
they do not install them into either agent application.

## Support scope

| Component | Automated evidence | Not established by these checks |
| --- | --- | --- |
| Import/sync tooling | Local Git imports, failure handling, content/version/lock regressions | Crash-atomic commits or concurrent writers |
| Claude/Codex registries | Structure and shared metadata | Clean host installation and complete feature parity |
| Imported skills | Source/revision tracking and basic frontmatter | Quality or behavior of upstream instructions |
| dm-kit | Deterministic canvas helper/hook behavior | Agent completion rates or live rules API behavior |
| Gemini | Production helper functions | Successful live image generation or host MCP wiring |
| env-guard | Specific accidental-access checks | A sandbox or security boundary; Codex hook support |
| xmind-campaign | Basic package validation | Runtime behavior; treated as legacy |

`evals/dm-kit/*.json` are positive/negative trigger examples. They are not a
measured evaluation report or an automated proof that workflows complete.

## Manual clean-install check

Use a disposable agent configuration and sample vault, not an existing personal
installation. Record host name/version and date for any compatibility claim.

1. Register this checkout and install the selected bundle through the host CLI/UI.
2. Verify that its skills are discovered and invoke one against synthetic content.
3. For hooks or MCP, verify the component actually loads; do not infer support
   from the presence of a manifest. Check the output path and error handling.
4. For dm-kit, create one scene and verify its exact canvas file node; repeat safely.
5. Remove the disposable installation when done.

No successful clean host-install result is claimed yet. Live Gemini tests remain
opt-in via `RUN_GEMINI_INTEGRATION=1`; they require credentials and can incur costs.
