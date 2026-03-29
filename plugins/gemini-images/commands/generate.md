---
name: generate
description: Generate an image using Gemini with automatic prompt refinement and optional style guide constraints.
argument-hint: "[prompt description]"
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "Agent", "AskUserQuestion", "mcp__plugin_gemini-images_gemini-images__generate_image", "mcp__plugin_gemini-images_gemini-images__get_generation_stats"]
---

# Image Generation Workflow

You are generating an image using the Gemini image generation API. Follow these steps carefully.

## Step 1: Gather the prompt

If the user provided a prompt in the command arguments, use it. Otherwise, ask what they want to generate.

## Step 2: Load settings

Check if a `.claude/gemini-images.local.md` file exists in the current project directory. If it does, read it to get:
- `default_model` (fallback: `gemini-2.5-flash-image`)
- `output_dir` (fallback: `./generated-images`)
- `style_guide_path` (optional)
- `auto_refine_prompts` (fallback: `true`)

## Step 3: Apply style guide (if configured)

If `style_guide_path` is set in settings, read that file and extract:
- Color palette (hex values)
- Typography preferences
- Illustration style / mood
- Any brand do's and don'ts

Append these as constraints to the prompt. For example: "Use the color palette: #F3F0E7 (ivory), #2A2529 (charcoal), #FF3C00 (orange-red). Style: editorial, clean, modernist."

## Step 4: Refine the prompt

If `auto_refine_prompts` is true (default), improve the user's prompt following these Gemini best practices:

- **Describe the scene narratively** — don't just list keywords. "A cozy coffee shop at golden hour with warm light streaming through tall windows" beats "coffee shop, warm, golden hour".
- **Specify camera and lighting** for photorealistic images — mention lens type, focal length, lighting conditions. "Shot on 85mm portrait lens, soft natural window light, shallow depth of field."
- **Name the art style explicitly** for illustrations — "flat vector illustration", "watercolor with visible brush strokes", "minimalist line drawing".
- **Keep text-in-image to 25 characters max** and specify typography needs.
- **Use semantic negative prompts** — describe what you want, not what to avoid. Instead of "no clutter", say "clean, minimal background".
- **Include mood and atmosphere** — emotional tone helps the model significantly.
- **Be specific about composition** — foreground/background, perspective, framing.

Show the refined prompt to the user and ask for confirmation before proceeding.

## Step 5: Generate

Call the `generate_image` MCP tool with:
- `prompt`: the refined prompt
- `model`: from settings or default
- `aspect_ratio`: ask the user or default to "1:1"
- `output_dir`: from settings or default

## Step 6: Present the result

Read the generated image file using the Read tool to display it to the user.

Report: the file path, the model used, and the current session generation count.

Ask: "Satisfied with this result, or would you like to iterate?"

If the user wants to iterate, refine the prompt based on their feedback and repeat from Step 5.
