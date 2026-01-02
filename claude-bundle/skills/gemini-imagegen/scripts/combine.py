#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-genai>=1.0.0", "pillow>=10.0.0", "python-dotenv>=1.0.0"]
# ///
"""Combine multiple images using Google Gemini's image models."""

import argparse
import os
import sys
from pathlib import Path


def get_api_key() -> str:
    """Get API key from environment or .env file."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if key:
            return key
    except ImportError:
        pass
    
    print("Error: No API key found.", file=sys.stderr)
    print("Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.", file=sys.stderr)
    sys.exit(1)


def get_model_name(model_flag: str) -> str:
    """Convert model flag to full model name."""
    models = {
        "flash": "gemini-2.5-flash-image",
        "pro": "gemini-3-pro-image-preview",
    }
    return models.get(model_flag, model_flag)


def combine_images(
    input_paths: list[str],
    prompt: str,
    output_path: str,
    model: str = "pro"
) -> str:
    """Combine multiple images based on a text prompt."""
    from google import genai
    from google.genai import types
    from PIL import Image
    
    # Validate inputs (2-8 images supported)
    if len(input_paths) < 2:
        print("Error: At least 2 images required for combining.", file=sys.stderr)
        sys.exit(1)
    if len(input_paths) > 8:
        print("Warning: Maximum 8 images supported. Using first 8.", file=sys.stderr)
        input_paths = input_paths[:8]
    
    # Load images
    images = []
    for path in input_paths:
        if not Path(path).exists():
            print(f"Error: File not found: {path}", file=sys.stderr)
            sys.exit(1)
        try:
            images.append(Image.open(path))
        except Exception as e:
            print(f"Error loading {path}: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Initialize client
    api_key = get_api_key()
    client = genai.Client(api_key=api_key)
    model_name = get_model_name(model)
    
    # Ensure output directory exists
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Build content list: prompt + all images
        contents = [prompt] + images
        
        # Generate combined image
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )
        
        # Process response
        for part in response.parts:
            if part.inline_data is not None:
                combined_image = part.as_image()
                combined_image.save(str(output))
                print(f"Saved: {output}")
                return str(output)
            elif part.text:
                print(f"Model response: {part.text}")
        
        print("No combined image was returned.", file=sys.stderr)
        sys.exit(1)
        
    except Exception as e:
        print(f"Error combining images: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Combine multiple images using Google Gemini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s bg.png char.png "Place the character in front of the background"
  %(prog)s img1.png img2.png img3.png "Create a collage" -o collage.png
  %(prog)s face.png body.png "Merge face onto body naturally" -m pro
        """
    )
    parser.add_argument("images", nargs="+", help="Input image files (2-8 images)")
    parser.add_argument("-p", "--prompt", required=True,
                        help="Instructions for combining images")
    parser.add_argument("-o", "--output", default="tmp/combined.png",
                        help="Output file path (default: tmp/combined.png)")
    parser.add_argument("-m", "--model", default="pro",
                        choices=["flash", "pro"],
                        help="Model: flash (fast) or pro (quality, default)")
    
    args = parser.parse_args()
    
    combine_images(
        input_paths=args.images,
        prompt=args.prompt,
        output_path=args.output,
        model=args.model
    )


if __name__ == "__main__":
    main()