# Gemini Image Generation — Best Practices Reference

## Model Comparison

| Model | Cost/image | Speed | Best for |
|-------|-----------|-------|----------|
| `gemini-2.5-flash-image` | $0.039 | Fastest | Iteration, drafts, high-volume |
| `gemini-3.1-flash-image-preview` | ~$0.10 | Fast | Advanced reasoning, complex scenes |
| `gemini-3-pro-image-preview` | ~$0.19 | Slower | Professional quality, final assets |

## Prompt Transformation Examples

### Example 1: Product shot

**Raw:** "a water bottle on a table"

**Refined:** "A sleek matte black stainless steel water bottle centered on a light oak table surface. Shot from a slightly elevated 30-degree angle with soft studio lighting from the upper left. Clean white background with subtle shadow cast to the right. Sharp focus on the bottle with smooth gradient background. Professional product photography, 4K."

### Example 2: Brand illustration

**Raw:** "illustration of a team working together"

**Refined:** "Flat vector illustration of four diverse people collaborating around a large shared screen in a modern open office. Mid-century modern style with clean geometric shapes and bold outlines. Color palette limited to warm ivory (#F3F0E7), charcoal (#2A2529), and accent orange-red (#FF3C00). Characters have simplified friendly features, no detailed faces. Generous negative space at the top for headline text. Editorial illustration quality."

### Example 3: Social media graphic

**Raw:** "announcement post for a new feature"

**Refined:** "Clean, modern social media announcement graphic with a 1:1 square format. Large bold text reading 'NEW' in uppercase sans-serif at the top. Centered below: a minimal isometric illustration of a smartphone showing a new interface. Background: solid deep navy blue (#1a1a2e). Text and illustration in white and bright cyan (#00d4ff). Ample breathing room between elements. Tech startup aesthetic."

### Example 4: Landscape photo

**Raw:** "sunset over the ocean"

**Refined:** "Dramatic ocean sunset captured with a wide-angle 24mm lens from a rocky coastal cliff. The sky transitions from deep purple at the zenith through fiery orange and gold to the horizon line. Long exposure effect on the water, creating silky smooth waves flowing between dark volcanic rocks in the foreground. Warm color temperature. Shot during the final minutes of golden hour. Landscape photography, 16:9 aspect ratio, HDR quality."

### Example 5: Image modification

**Raw:** "remove the background"

**Refined:** "Replace the entire background behind the main subject with a clean, solid white (#FFFFFF) backdrop. Preserve the subject's edges cleanly with no fringing or halos. Maintain the original lighting on the subject. Keep all foreground elements intact."

## Tips for Iterative Refinement

1. **Start broad, then focus:** First generation establishes the overall composition. Subsequent iterations should target specific elements.
2. **One change at a time:** When iterating, modify one aspect per round to understand what works.
3. **Build a vocabulary:** Note which descriptive terms produce the best results and reuse them.
4. **Reference the previous result:** "Keep the composition from the previous image but change the lighting to..."
5. **Use comparison language:** "More vibrant", "slightly warmer", "tighter crop" — relative adjustments work well.

## Safety Filters

Gemini will reject prompts that request:
- Real people's likenesses (celebrities, public figures)
- Violent or graphic content
- Content that could be used for deception
- Certain modifications to people in photos

If a generation fails due to safety filters, the error message will indicate this. Rephrase the prompt to avoid the filtered content.
