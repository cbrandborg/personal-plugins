---
name: image-settings
description: Configure gemini-images plugin defaults — model, output directory, style guide, cost limits.
allowed-tools: ["Read", "Write", "AskUserQuestion", "Glob"]
---

# Gemini Images Settings

Configure the plugin defaults for this project. Settings are stored in `.claude/gemini-images.local.md`.

## Step 1: Read current settings

Check if `.claude/gemini-images.local.md` exists in the current project. If it does, read it and display the current configuration. If not, show the defaults.

## Step 2: Present configurable options

| Setting | Default | Description |
|---------|---------|-------------|
| `default_model` | `gemini-3.1-flash-lite-image` | Model for generation (~$0.034/1K image) |
| `output_dir` | `./gemini-assets/outputs` | Where to save images |
| `style_guide_path` | (none) | Path to brand/visual identity guide |
| `max_generations` | `5` | Cost control — max generations per session |
| `auto_refine_prompts` | `true` | Auto-apply prompt best practices |

Available models and pricing:
- `gemini-3.1-flash-lite-image` — ~$0.034 per 1K image, fastest and default
- `gemini-3.1-flash-image` — ~$0.067 per 1K image, general-purpose
- `gemini-3-pro-image` — ~$0.134 per image, premium quality

## Step 3: Collect changes

Ask the user which settings they want to change. Accept changes interactively.

## Step 4: Write settings file

Write the settings to `.claude/gemini-images.local.md` with YAML frontmatter:

```markdown
---
default_model: gemini-3.1-flash-lite-image
output_dir: ./gemini-assets/outputs
style_guide_path: /path/to/style-guide.md
max_generations: 5
auto_refine_prompts: true
---

# Gemini Images — Project Configuration

Configured for [project name] on [date].
```

Confirm the settings were saved.
