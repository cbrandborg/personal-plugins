---
name: image-settings
description: Use when configuring gemini-images defaults for a project, including model, output directory, style guide, generation limit, and prompt refinement.
---

# Configure Gemini Images

Store project settings in `.claude/gemini-images.local.md` so the existing Claude, Codex, and portable workflows share one configuration.

## 1. Read current settings

If `.claude/gemini-images.local.md` exists in the current project, read it and show the current configuration. Otherwise, show these defaults:

| Setting | Default | Description |
|---|---|---|
| `default_model` | `gemini-3.1-flash-lite-image` | Model used for generation |
| `output_dir` | `./gemini-assets/outputs` | Directory for generated images |
| `style_guide_path` | none | Brand or visual-identity guide |
| `max_generations` | `5` | Maximum billable attempts per MCP server session |
| `auto_refine_prompts` | `true` | Apply prompt-refinement guidance automatically |

Supported models:

- `gemini-3.1-flash-lite-image`
- `gemini-3.1-flash-image`
- `gemini-3-pro-image`

Pricing and model availability can change; do not present estimates as guaranteed billing rates.

## 2. Collect changes

Ask which settings the user wants to change. Preserve current values for settings they do not mention. Resolve `style_guide_path` when supplied, and explain that generation workflows resolve `output_dir` relative to the project working directory.

## 3. Write the settings

Write `.claude/gemini-images.local.md` with YAML frontmatter in this form:

```markdown
---
default_model: gemini-3.1-flash-lite-image
output_dir: ./gemini-assets/outputs
style_guide_path: /absolute/path/to/style-guide.md
max_generations: 5
auto_refine_prompts: true
---

# Gemini Images — Project Configuration
```

Omit `style_guide_path` when no guide is configured. Generation and modification workflows pass `max_generations` to the MCP server, which enforces the cap even on hosts without Claude's pre-tool hook. Confirm the saved settings by reading back the target file.
