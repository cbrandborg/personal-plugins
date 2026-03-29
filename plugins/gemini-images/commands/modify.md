---
name: modify
description: Modify an existing image using Gemini. Requires an image path and modification instructions.
argument-hint: "[path to image]"
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion", "mcp__plugin_gemini-images_gemini-images__modify_image", "mcp__plugin_gemini-images_gemini-images__get_generation_stats"]
---

# Image Modification Workflow

You are modifying an existing image using Gemini's conversational image editing. Follow these steps.

## Step 1: Get the source image

If the user provided an image path in the arguments, use it. Otherwise, ask for the path to the image they want to modify.

Verify the file exists. If it doesn't, tell the user and ask for the correct path.

**IMPORTANT:** An image path is REQUIRED. Do not proceed without one. If the user hasn't provided one, ask for it explicitly.

## Step 2: Display the source image

Read the source image using the Read tool so the user can see what they're working with. Briefly describe what you see in the image.

## Step 3: Get modification instructions

Ask what changes they want to make. Common modifications include:
- Removing objects or people
- Changing backgrounds
- Altering colors or lighting
- Adding elements
- Blurring backgrounds
- Changing poses or positions
- Converting to different styles

## Step 4: Load settings

Check for `.claude/gemini-images.local.md` to get `default_model` and `output_dir`.

## Step 5: Refine the instruction

Apply these Gemini image editing best practices to the instruction:
- Be specific about WHAT to change and HOW — "Remove the person standing on the left side and fill with the existing brick wall pattern" is better than "remove the person".
- Describe the desired end state, not just the operation.
- For style changes, be explicit about the target style.

Show the refined instruction to the user for confirmation.

## Step 6: Modify

Call the `modify_image` MCP tool with:
- `image_path`: the source image
- `instruction`: the refined instruction
- `model`: from settings or default
- `output_dir`: from settings or default

## Step 7: Present the result

Read the modified image to display it. Report: file path, model used, session count.

Ask: "Satisfied, iterate further, or revert to the original?"

If iterating, the user can either:
- Modify the NEW image further (chain modifications)
- Go back to the original and try a different instruction
