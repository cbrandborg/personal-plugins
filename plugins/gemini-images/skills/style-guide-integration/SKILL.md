---
name: style-guide-integration
description: This skill should be used when applying a brand guide or visual identity to image generation. Reads a style guide document and extracts visual constraints (colors, typography, illustration style, mood) to constrain Gemini image generation. Triggers when user mentions "brand", "style guide", "visual identity", or when a style_guide_path is configured in settings.
---

# Style Guide Integration for Image Generation

When a style guide or visual identity document is available, use it to constrain image generation prompts. This ensures generated images are consistent with the brand.

## Process

### 1. Locate the style guide

Check these sources in order:
1. User-provided path in the current request
2. `style_guide_path` from `.claude/gemini-images.local.md` settings
3. Ask the user if they have a style guide to apply

### 2. Read and extract constraints

Read the style guide document and extract these categories:

**Colors:**
- Primary, secondary, and accent colors with hex values
- Background colors
- Any color restrictions ("never use X")
- Format as: `Color palette: #HEXVAL (name), #HEXVAL (name), ...`

**Typography:**
- Display/heading fonts and weights
- Body/UI fonts
- Any text styling preferences
- Format as: `Typography: [font] for headings, [font] for body`

**Illustration style:**
- Preferred visual style (editorial, playful, technical, etc.)
- Line work preferences (clean, sketchy, geometric, etc.)
- Level of detail (minimal, detailed, abstract)
- Format as: `Style: [description]`

**Mood and tone:**
- Brand personality keywords
- Emotional direction
- Format as: `Mood: [keywords]`

**Do's and don'ts:**
- Any explicit restrictions from the guide
- Format as constraints in the prompt

### 3. Format as prompt constraints

Combine the extracted elements into a constraint block that gets appended to the generation prompt:

```
[Brand constraints: Color palette — #F3F0E7 (ivory background), #2A2529 (charcoal text), #FF3C00 (orange-red accent). Typography — Courier Prime 700 for display, system sans-serif for body. Style — editorial, clean, modernist. Mood — thoughtful, precise, Scandinavian.]
```

### 4. Apply to prompt

The constraint block should be appended AFTER the scene description but BEFORE any technical specifications (camera, lighting, etc.). This way the creative direction is set by the brand while the technical execution remains flexible.

## Example

**User prompt:** "Create a hero image for the blog"

**After style guide integration:**
"A wide editorial photograph of a clean Scandinavian workspace — a minimal desk with a single open laptop, a ceramic cup, and a small potted plant. Warm ivory tones dominate with charcoal accents. A single orange-red (#FF3C00) notebook provides a deliberate pop of color. [Brand constraints: Color palette — #F3F0E7 (ivory), #2A2529 (charcoal), #FF3C00 (orange-red accent), #7A7570 (muted). Style — editorial, clean, modernist. Mood — thoughtful, precise, Scandinavian.] Shot at eye level with soft diffused natural light from large windows. 16:9 aspect ratio, editorial photography quality."

## Notes

- The style guide is READ-ONLY — never modify it
- If the user explicitly says to ignore the style guide for a particular generation, respect that
- For internal/draft work, style guide constraints can be relaxed — ask if unsure
- When generating variations, all variations should respect the style guide unless exploring alternatives is the explicit goal
