---
name: gemini-imagegen
description: Generate and edit images using Google Gemini's image models (Nano Banana). Use this skill when users request image generation, AI art creation, image editing, style transfers, logos, icons, mockups, stickers, or any visual content creation. Triggers include "generate image", "create picture", "make an image", "draw", "nano banana", "edit this image", "add to image", or any image/visual generation request. Requires GEMINI_API_KEY or GOOGLE_API_KEY environment variable.
---

# Gemini Image Generation

Generate and edit images using Google's Gemini image models via `uv run` scripts with inline dependencies.

## Quick Start

```bash
# Generate an image
uv run scripts/generate.py "A serene mountain lake at sunset" --output output.png

# Edit an existing image  
uv run scripts/edit.py input.png "Add a rainbow in the sky" --output edited.png

# Generate with specific aspect ratio
uv run scripts/generate.py "Cyberpunk cityscape" --aspect 16:9 --output wide.png
```

## Model Selection

| Model | Use When | Flag |
|-------|----------|------|
| `gemini-2.5-flash-image` | Speed priority, iterations, drafts | `--model flash` (default) |
| `gemini-3-pro-image-preview` | Quality priority, final assets | `--model pro` |

## Scripts Reference

### generate.py
```bash
uv run scripts/generate.py "<prompt>" [options]

Options:
  --output, -o   Output path (default: tmp/generated.png)
  --aspect, -a   Aspect ratio: 1:1, 16:9, 9:16, 4:3, 3:4 (default: 1:1)
  --model, -m    Model: flash, pro (default: flash)
  --count, -n    Number of images to generate (default: 1)
```

### edit.py
```bash
uv run scripts/edit.py <input_image> "<edit_prompt>" [options]

Options:
  --output, -o   Output path (default: tmp/edited.png)
  --model, -m    Model: flash, pro (default: flash)
```

### combine.py
```bash
uv run scripts/combine.py <image1> <image2> [image3...] "<prompt>" [options]

Options:
  --output, -o   Output path (default: tmp/combined.png)
  --model, -m    Model: flash, pro (default: pro)
```

## API Key Setup

Scripts auto-detect key from (in order):
1. `GEMINI_API_KEY` environment variable
2. `GOOGLE_API_KEY` environment variable
3. `.env` file in current directory

## Best Practices

- **Iterative workflow**: Start with `flash` for quick iterations, switch to `pro` for finals
- **Specific prompts**: Include style, colors, composition, lighting details
- **Save to tmp/**: Use `tmp/` directory for generated images
- **Evaluate output**: Review each generation before proceeding

## Advanced Usage

For complex workflows including multi-turn conversations, Google Search grounding, and professional asset production, see [references/advanced.md](references/advanced.md).