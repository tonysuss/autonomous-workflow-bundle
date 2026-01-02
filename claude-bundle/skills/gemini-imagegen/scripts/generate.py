#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-genai>=1.0.0", "pillow>=10.0.0", "python-dotenv>=1.0.0"]
# ///
"""Generate images using Google Gemini's image models."""

import argparse
import os
import sys
from pathlib import Path


def get_api_key() -> str:
    """Get API key from environment or .env file."""
    # Check environment variables first
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    
    # Try loading from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if key:
            return key
    except ImportError:
        pass
    
    print("Error: No API key found.", file=sys.stderr)
    print("Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable,", file=sys.stderr)
    print("or add it to a .env file in the current directory.", file=sys.stderr)
    sys.exit(1)


def get_model_name(model_flag: str) -> str:
    """Convert model flag to full model name."""
    models = {
        "flash": "gemini-2.5-flash-image",
        "pro": "gemini-3-pro-image-preview",
    }
    return models.get(model_flag, model_flag)


def validate_aspect_ratio(aspect: str) -> str:
    """Validate and return aspect ratio."""
    valid = {"1:1", "16:9", "9:16", "4:3", "3:4"}
    if aspect not in valid:
        print(f"Warning: Invalid aspect ratio '{aspect}'. Using 1:1.", file=sys.stderr)
        return "1:1"
    return aspect


def generate_image(
    prompt: str,
    output_path: str,
    model: str = "flash",
    aspect_ratio: str = "1:1",
    count: int = 1
) -> list[str]:
    """Generate image(s) from a text prompt."""
    from google import genai
    from google.genai import types
    
    # Initialize client
    api_key = get_api_key()
    client = genai.Client(api_key=api_key)
    
    # Get model name
    model_name = get_model_name(model)
    aspect = validate_aspect_ratio(aspect_ratio)
    
    # Ensure output directory exists
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    saved_files = []
    
    for i in range(count):
        try:
            # Generate image
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect
                    )
                )
            )
            
            # Process response
            for part in response.parts:
                if part.inline_data is not None:
                    image = part.as_image()
                    
                    # Handle multiple images
                    if count > 1:
                        stem = output.stem
                        suffix = output.suffix or ".png"
                        save_path = output.parent / f"{stem}-{i+1}{suffix}"
                    else:
                        save_path = output
                    
                    image.save(str(save_path))
                    saved_files.append(str(save_path))
                    print(f"Saved: {save_path}")
                    
                elif part.text:
                    print(f"Model response: {part.text}")
                    
        except Exception as e:
            print(f"Error generating image {i+1}: {e}", file=sys.stderr)
            continue
    
    if not saved_files:
        print("No images were generated.", file=sys.stderr)
        sys.exit(1)
    
    return saved_files


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Google Gemini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "A cat wearing a hat"
  %(prog)s "Mountain landscape" -o landscape.png -a 16:9
  %(prog)s "App icon" -m pro -n 3
        """
    )
    parser.add_argument("prompt", help="Text prompt for image generation")
    parser.add_argument("-o", "--output", default="tmp/generated.png",
                        help="Output file path (default: tmp/generated.png)")
    parser.add_argument("-a", "--aspect", default="1:1",
                        choices=["1:1", "16:9", "9:16", "4:3", "3:4"],
                        help="Aspect ratio (default: 1:1)")
    parser.add_argument("-m", "--model", default="flash",
                        choices=["flash", "pro"],
                        help="Model: flash (fast) or pro (quality)")
    parser.add_argument("-n", "--count", type=int, default=1,
                        help="Number of images to generate (default: 1)")
    
    args = parser.parse_args()
    
    generate_image(
        prompt=args.prompt,
        output_path=args.output,
        model=args.model,
        aspect_ratio=args.aspect,
        count=args.count
    )


if __name__ == "__main__":
    main()