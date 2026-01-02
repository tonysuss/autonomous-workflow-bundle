#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-genai>=1.0.0", "pillow>=10.0.0", "python-dotenv>=1.0.0"]
# ///
"""Edit existing images using Google Gemini's image models."""

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


def edit_image(
    input_path: str,
    prompt: str,
    output_path: str,
    model: str = "flash"
) -> str:
    """Edit an existing image based on a text prompt."""
    from google import genai
    from google.genai import types
    from PIL import Image
    
    # Validate input
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize client
    api_key = get_api_key()
    client = genai.Client(api_key=api_key)
    model_name = get_model_name(model)
    
    # Load input image
    try:
        img = Image.open(input_path)
    except Exception as e:
        print(f"Error loading image: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Ensure output directory exists
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Generate edited image
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt, img],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )
        
        # Process response
        for part in response.parts:
            if part.inline_data is not None:
                edited_image = part.as_image()
                edited_image.save(str(output))
                print(f"Saved: {output}")
                return str(output)
            elif part.text:
                print(f"Model response: {part.text}")
        
        print("No edited image was returned.", file=sys.stderr)
        sys.exit(1)
        
    except Exception as e:
        print(f"Error editing image: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Edit images using Google Gemini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s photo.png "Remove the background"
  %(prog)s input.jpg "Add a sunset sky" -o sunset.png
  %(prog)s logo.png "Make it more vibrant" -m pro
        """
    )
    parser.add_argument("input", help="Input image file path")
    parser.add_argument("prompt", help="Edit instructions")
    parser.add_argument("-o", "--output", default="tmp/edited.png",
                        help="Output file path (default: tmp/edited.png)")
    parser.add_argument("-m", "--model", default="flash",
                        choices=["flash", "pro"],
                        help="Model: flash (fast) or pro (quality)")
    
    args = parser.parse_args()
    
    edit_image(
        input_path=args.input,
        prompt=args.prompt,
        output_path=args.output,
        model=args.model
    )


if __name__ == "__main__":
    main()