# Advanced Gemini Image Generation

## Multi-Turn Conversation Workflow

For iterative refinement, use a stateful approach:

```python
# /// script
# dependencies = ["google-genai", "pillow"]
# ///
from google import genai
from google.genai import types
from PIL import Image
import os

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Start conversation
chat = client.chats.create(model="gemini-2.5-flash-image")

# Initial generation
response = chat.send_message(
    "Create a cute mascot character: a friendly robot",
    config=types.GenerateContentConfig(response_modalities=["IMAGE"])
)
# Save and review...

# Refinement round 1
response = chat.send_message(
    "Make the robot blue and add antennae",
    config=types.GenerateContentConfig(response_modalities=["IMAGE"])
)
# Save and review...

# Refinement round 2
response = chat.send_message(
    "Give it a warm smile and rounder edges",
    config=types.GenerateContentConfig(response_modalities=["IMAGE"])
)
```

## Google Search Grounding

Generate images based on real-world references:

```python
# /// script
# dependencies = ["google-genai", "pillow"]
# ///
from google import genai
from google.genai import types
import os

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=["Create an image in the style of Studio Ghibli featuring a forest spirit"],
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        tools=[types.Tool(google_search=types.GoogleSearch())]
    )
)
```

## Professional Asset Production

### App Icons (iOS/Android)

```bash
# Generate base icon
uv run scripts/generate.py "Flat design app icon, minimalist finance app, green gradient" \
  --aspect 1:1 --model pro --output tmp/icon-base.png

# Generate variations
uv run scripts/edit.py tmp/icon-base.png "Add subtle shadow and depth" \
  --model pro --output tmp/icon-final.png
```

### Marketing Assets

```bash
# Wide banner
uv run scripts/generate.py "Product launch banner, modern tech aesthetic, blue and white" \
  --aspect 16:9 --model pro --output tmp/banner.png

# Social media
uv run scripts/generate.py "Instagram post, product showcase, lifestyle" \
  --aspect 1:1 --model pro --output tmp/social.png

# Story format
uv run scripts/generate.py "Instagram story, product teaser, vertical" \
  --aspect 9:16 --model pro --output tmp/story.png
```

## Batch Processing Pattern

For generating multiple variations efficiently:

```python
# /// script
# dependencies = ["google-genai", "pillow"]
# ///
from google import genai
from google.genai import types
from concurrent.futures import ThreadPoolExecutor
import os

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

prompts = [
    "Minimalist logo, letter A, blue gradient",
    "Minimalist logo, letter A, green gradient", 
    "Minimalist logo, letter A, purple gradient",
]

def generate_one(prompt, index):
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt],
        config=types.GenerateContentConfig(response_modalities=["IMAGE"])
    )
    for part in response.parts:
        if part.inline_data:
            part.as_image().save(f"tmp/variation-{index}.png")
            return f"tmp/variation-{index}.png"

# Parallel generation
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(
        lambda x: generate_one(x[1], x[0]), 
        enumerate(prompts)
    ))
print(f"Generated: {results}")
```

## Error Handling Patterns

### Retry with Exponential Backoff

```python
import time

def generate_with_retry(client, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt],
                config=types.GenerateContentConfig(response_modalities=["IMAGE"])
            )
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"Retry {attempt + 1} in {wait}s: {e}")
                time.sleep(wait)
            else:
                raise
```

### Content Safety Fallback

```python
def safe_generate(client, prompt):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt],
            config=types.GenerateContentConfig(response_modalities=["IMAGE"])
        )
        # Check for blocked content
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            print(f"Content blocked: {response.prompt_feedback}")
            return None
        return response
    except Exception as e:
        print(f"Generation failed: {e}")
        return None
```

## Model Comparison

| Feature | Flash (2.5) | Pro (3.0) |
|---------|-------------|-----------|
| Speed | ~3-5s | ~8-15s |
| Quality | Good | Excellent |
| Text rendering | Basic | Advanced |
| Fine details | Moderate | High |
| Cost | Lower | Higher |
| Best for | Iterations, drafts | Final assets, text-heavy |

## Prompt Engineering Tips

### Structure
```
[Subject] + [Style] + [Composition] + [Lighting] + [Technical specs]
```

### Examples

**Bad**: "A cat"

**Good**: "Orange tabby cat sitting on windowsill, soft natural lighting, shallow depth of field, warm color palette, photorealistic style"

**For icons**: "Flat design icon of [subject], single color background, minimal shadows, suitable for app icon, clean vector style"

**For marketing**: "Product photography style, [product] on white background, soft shadows, high-end commercial aesthetic"