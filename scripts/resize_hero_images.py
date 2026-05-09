"""
One-off script: generate small thumbnails of every hero portrait.

Run:  ``python scripts/resize_hero_images.py``

Outputs into ``images/heroes/_thumbs/`` at 240px width (preserving aspect)
which the deck-page hero grid uses instead of full-resolution sources.
This is a major mobile-data win.
"""

from __future__ import annotations

import os
import sys

try:
    from PIL import Image
except ImportError:
    print("Pillow is required: pip install Pillow", file=sys.stderr)
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "images", "heroes")
DST = os.path.join(SRC, "_thumbs")
TARGET_W = 240
QUALITY = 78


def main() -> int:
    if not os.path.isdir(SRC):
        print(f"Source directory not found: {SRC}", file=sys.stderr)
        return 1
    os.makedirs(DST, exist_ok=True)

    count = 0
    for name in os.listdir(SRC):
        src_path = os.path.join(SRC, name)
        if not os.path.isfile(src_path):
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue

        dst_path = os.path.join(DST, os.path.splitext(name)[0] + ".jpg")
        try:
            with Image.open(src_path) as im:
                im = im.convert("RGB")
                w, h = im.size
                if w <= TARGET_W:
                    im.save(dst_path, "JPEG", quality=QUALITY, optimize=True)
                else:
                    new_h = int(h * TARGET_W / w)
                    resized = im.resize((TARGET_W, new_h), Image.LANCZOS)
                    resized.save(dst_path, "JPEG", quality=QUALITY, optimize=True)
            count += 1
        except Exception as e:  # noqa: BLE001 — script-level catch is fine
            print(f"Skipping {name}: {e}", file=sys.stderr)

    print(f"Wrote {count} thumbnails to {DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
