#!/usr/bin/env python3
"""Process a source NFT image into a compact 512x512 JPG for the Tokenization Lab bank.

The generation step (codex / gpt-image-1) produces large square PNGs. We don't want
those in the repo, so every generated image is run through this script:

  - center-crop to a square (in case the source isn't perfectly square)
  - downscale to 512x512 with a high-quality filter
  - save as a JPG with reasonable compression so the bank stays small

Usage:
  process-nft-image.py <source> <dest.jpg> [--size 512] [--quality 80]
"""

import argparse
import os
import sys
import time

from PIL import Image


def process(source: str, dest: str, size: int = 512, quality: int = 80) -> None:
    with Image.open(source) as img:
        img = img.convert("RGB")

        # Center-crop to a square so the resize never distorts the art.
        width, height = img.size
        if width != height:
            edge = min(width, height)
            left = (width - edge) // 2
            top = (height - edge) // 2
            img = img.crop((left, top, left + edge, top + edge))

        img = img.resize((size, size), Image.LANCZOS)

        os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
        # The repo lives on a 9p/virtio shared filesystem that intermittently returns
        # EINVAL on open-for-write under load. Write to a temp file and atomically replace,
        # retrying a few times so a transient FS hiccup doesn't lose the image.
        tmp = f"{dest}.tmp"
        last_err = None
        for _ in range(6):
            try:
                img.save(tmp, "JPEG", quality=quality, optimize=True, progressive=True)
                os.replace(tmp, dest)
                last_err = None
                break
            except OSError as err:
                last_err = err
                time.sleep(0.5)
        if last_err is not None:
            raise last_err

    src_kb = os.path.getsize(source) / 1024
    dst_kb = os.path.getsize(dest) / 1024
    print(f"{source} ({src_kb:.0f} KB) -> {dest} ({dst_kb:.0f} KB, {size}x{size} q{quality})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Downscale an NFT source image to a compact JPG.")
    parser.add_argument("source", help="Path to the source image (PNG/JPG).")
    parser.add_argument("dest", help="Destination .jpg path.")
    parser.add_argument("--size", type=int, default=512, help="Output edge length (default 512).")
    parser.add_argument("--quality", type=int, default=80, help="JPEG quality 1-95 (default 80).")
    args = parser.parse_args()

    if not os.path.exists(args.source):
        print(f"error: source not found: {args.source}", file=sys.stderr)
        return 1

    process(args.source, args.dest, size=args.size, quality=args.quality)
    return 0


if __name__ == "__main__":
    sys.exit(main())
