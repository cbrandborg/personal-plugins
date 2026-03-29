---
name: prompt-refinement
description: This skill should be used when generating or modifying images with Gemini, when the user asks to "refine a prompt", "optimize for Gemini", "improve image prompt", or before any image generation API call. It transforms raw image descriptions into Gemini-optimized prompts following Google's best practices.
---

# Gemini Image Prompt Refinement

When generating or modifying images with Gemini, apply these refinement rules to the user's raw prompt BEFORE calling the API. The goal is to transform a casual description into a detailed, Gemini-optimized prompt that produces significantly better results.

## Core Principle

**Describe the scene narratively. Do not list keywords.** Gemini's language understanding is its strength — treat the prompt like a paragraph describing a photograph or artwork, not a tag list.

Bad: `coffee shop, warm light, cozy, latte art, morning`
Good: `A cozy corner of a coffee shop bathed in warm golden morning light streaming through tall arched windows. A ceramic mug of latte with delicate rosetta art sits on a worn wooden table. Soft focus on the background showing exposed brick and hanging plants.`

## Refinement Rules

### For photorealistic images
- Specify **camera type and lens**: "Shot on Canon EOS R5 with 85mm f/1.4 lens"
- Specify **lighting**: "Soft diffused natural light from the left", "dramatic side lighting", "golden hour backlight"
- Specify **depth of field**: "Shallow depth of field with bokeh background", "everything in sharp focus"
- Include **perspective**: "Eye-level shot", "overhead flat lay", "low angle looking up"
- Add **quality markers**: "Professional photography", "editorial quality", "8K detail"

### For illustrations and artwork
- **Name the exact style**: "Flat vector illustration with bold outlines", "watercolor with visible wet-on-wet technique", "isometric pixel art"
- Specify **color approach**: "Limited palette of earth tones", "vibrant complementary colors", "monochrome with a single accent color"
- Reference **art movements or artists** when relevant: "In the style of mid-century modern poster design", "Bauhaus-inspired geometric composition"
- Detail **line work**: "Clean geometric lines", "hand-drawn sketchy quality", "no outlines, shape-based"

### For text in images
- **Keep text to 25 characters or fewer** for reliable generation
- Specify **font style**: "Bold sans-serif uppercase", "elegant serif script"
- Specify **placement**: "Centered at the top third", "bottom-right corner"
- Maximum 2-3 distinct text elements per image

### For composition
- Describe **foreground, midground, and background** separately
- Specify **framing**: "Rule of thirds with subject on left intersection", "centered symmetrical composition"
- Include **negative space**: "Generous white space on the right for text overlay"
- Describe **mood and atmosphere**: "Serene and contemplative", "energetic and dynamic", "nostalgic warmth"

### Semantic negative prompts
Instead of saying what to avoid, describe what you want:
- Instead of "no clutter" → "clean, minimal background with a single focal point"
- Instead of "no blur" → "tack-sharp focus across the entire frame"
- Instead of "not cartoonish" → "photorealistic with natural proportions and textures"

## Aspect Ratio Guidance

| Use case | Recommended |
|----------|-------------|
| Social media post | 1:1 |
| Landscape / hero banner | 16:9 |
| Portrait / mobile | 9:16 |
| Blog header | 3:2 |
| Product shot | 4:3 |
| Story / reel | 9:16 |

## Process

1. Read the user's raw prompt
2. Identify the image type (photo, illustration, icon, text-heavy, etc.)
3. Apply the relevant refinement rules above
4. Preserve the user's creative intent — enhance specificity without changing direction
5. If a style guide is active, incorporate its constraints (colors, typography, mood)
6. Present the refined prompt for user approval before calling the API

For detailed examples and model comparisons, see `references/gemini-best-practices.md`.
