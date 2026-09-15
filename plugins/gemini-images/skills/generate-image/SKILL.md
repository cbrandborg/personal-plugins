---
name: generate-image
description: Use when generating an image with Gemini. Refine the prompt, apply optional style constraints, and save the result through the gemini-images MCP server.
---

# Generate an Image with Gemini

## 1. Gather inputs

Use the prompt from the user's request. If no prompt was provided, ask what they want to generate.

Identify any reference images the user provided or mentioned. Reference images normally live in `gemini-assets/inputs/` under the current project. Resolve every reference image to an absolute path before passing it to an MCP tool.

If the user wants to match an existing style, palette, or composition but did not provide the image, ask for its path or check `gemini-assets/inputs/` in the current working directory.

For any reference upload, pass the current project root as `allowed_input_root` by default. If the image is outside the project, use an external root only after explicit user confirmation; scope it to the narrowest directory containing the confirmed image, never `/` or the user's whole home directory.

## 2. Load project settings

Read `.claude/gemini-images.local.md` in the current project if it exists. Use these settings:

- `default_model` (default: `gemini-3.1-flash-image-preview`)
- `output_dir` (default: `./gemini-assets/outputs`)
- `style_guide_path` (optional)
- `max_generations` (default: `5`)
- `auto_refine_prompts` (default: `true`)

## 3. Apply the style guide

If `style_guide_path` is configured, read that file and extract its colors, typography, illustration style, mood, and explicit do's and don'ts. Append those details to the prompt as constraints. Never modify the style guide.

## 4. Refine and confirm the prompt

When `auto_refine_prompts` is enabled, improve the prompt before generation:

- Describe the scene narratively rather than as a keyword list.
- For photorealistic work, specify camera, lens, lighting, perspective, and depth of field when relevant.
- For illustrations, name the art style and describe the line work and color approach.
- Keep requested text in the image to 25 characters or fewer.
- Describe the desired result instead of listing negative prompts.
- Include mood, composition, foreground, and background details when useful.

Preserve the user's creative intent. Show the refined prompt and get confirmation before making a billable generation call.

## 5. Generate

Call the `generate_image` tool from the `gemini-images` MCP server with:

- `prompt`: the confirmed prompt
- `name`: a short, descriptive three-to-five-word name
- `model`: the configured model or default
- `aspect_ratio`: the user's choice, or `1:1` by default
- `reference_image_path`: the absolute reference-image path when applicable
- `allowed_input_root`: when `reference_image_path` is set, the confirmed absolute root from Step 1
- `output_dir`: an absolute path resolved from the project working directory
- `max_generations`: the configured positive integer, or `5`

Never pass a relative output path. The MCP server runs from the plugin installation directory, not the user's project.

## 6. Present the result

Display or inspect the generated image with the host's available image-reading tool. Report the output path, model, and current session generation count. Ask whether the user wants to keep it or iterate. For an iteration, refine the prompt from their feedback and repeat the generation step after confirmation.
