---
name: modify-image
description: Use when modifying an existing image with Gemini. Validate the source image, refine the requested edit, and save the result through the gemini-images MCP server.
---

# Modify an Image with Gemini

## 1. Resolve the source image

Use the image path from the user's request. If none was provided, ask for it. Resolve it to an absolute path and verify that the file exists before proceeding. Do not call the modification tool without a valid source image.

Pass the current project root as `allowed_input_root` by default. If the source image is outside the project, use an external root only after explicit user confirmation; scope it to the narrowest directory containing the confirmed image, never `/` or the user's whole home directory.

Display or inspect the source image with the host's available image-reading tool and briefly describe it.

## 2. Gather the edit request

Ask what the user wants changed if their instruction is incomplete. Common edits include removing objects, changing backgrounds, altering color or lighting, adding elements, changing poses, blurring backgrounds, or converting styles.

## 3. Load project settings

Read `.claude/gemini-images.local.md` in the current project if it exists. Use its `default_model`, `output_dir`, and `max_generations`; otherwise default to `gemini-3.1-flash-lite-image`, `./gemini-assets/outputs`, and `5`.

## 4. Refine and confirm the instruction

Make the instruction specific about what should change and how the finished image should look. Describe the desired end state rather than only naming an operation. For style changes, state the target style explicitly.

Show the refined instruction and get confirmation before making a billable modification call.

## 5. Modify

Call the `modify_image` tool from the `gemini-images` MCP server with:

- `image_path`: the absolute source-image path
- `allowed_input_root`: the confirmed absolute root from Step 1
- `instruction`: the confirmed instruction
- `model`: the configured model or default
- `output_dir`: an absolute path resolved from the project working directory
- `max_generations`: the configured positive integer, or `5`

Never pass a relative output path. The MCP server runs from the plugin installation directory, not the user's project.

## 6. Present the result

Display or inspect the modified image. Report the output path, model, and current session generation count. Ask whether the user wants to keep it, modify the new image further, or return to the original and try a different instruction.
