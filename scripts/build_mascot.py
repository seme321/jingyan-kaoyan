# -*- coding: utf-8 -*-
"""Remove the white background from the original mascot renders and export trimmed WebP sprites."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "assets_src" / "mascot_raw"
OUT = ROOT / "web" / "public" / "mascot"

THRESH = 232  # near-white


def cutout(path: Path, thresh: int = THRESH, extra_seeds=None) -> Image.Image:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    # binary map: 255 where near white
    r, g, b = img.split()
    white = ImageChops.darker(ImageChops.darker(r, g), b).point(lambda v: 255 if v >= thresh else 0)
    # flood fill from border on the binary map, marking background as 128
    flood = white.copy()
    seeds = (
        [(x, 0) for x in range(0, w, 16)]
        + [(x, h - 1) for x in range(0, w, 16)]
        + [(0, y) for y in range(0, h, 16)]
        + [(w - 1, y) for y in range(0, h, 16)]
    )
    if extra_seeds:
        seeds.extend((int(rx * w), int(ry * h)) for rx, ry in extra_seeds)
    for s in seeds:
        if 0 <= s[0] < w and 0 <= s[1] < h and flood.getpixel(s) == 255:
            ImageDraw.floodfill(flood, s, 128)
    bg = flood.point(lambda v: 255 if v == 128 else 0)
    # grow background by 1px to eat the light halo, then feather
    bg = bg.filter(ImageFilter.MaxFilter(3))
    alpha = ImageChops.invert(bg).filter(ImageFilter.GaussianBlur(0.8))
    rgba = img.convert("RGBA")
    rgba.putalpha(alpha)
    bbox = alpha.point(lambda v: 255 if v > 10 else 0).getbbox()
    if bbox:
        pad = 8
        bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(w, bbox[2] + pad), min(h, bbox[3] + pad))
        rgba = rgba.crop(bbox)
    # fit into square canvas, bottom aligned
    side = max(rgba.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(rgba, ((side - rgba.width) // 2, side - rgba.height), rgba)
    return canvas.resize((512, 512), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    targets = sys.argv[1:] if len(sys.argv) > 1 else ["hero", "think", "cheer", "study"]
    for name in targets:
        src = next((p for p in RAW.glob(f"{name}.*")), None)
        if not src:
            print("missing", name)
            continue
        im = cutout(
            src,
            thresh=244 if name == "gemini" else THRESH,
            extra_seeds=[
                (0.2545, 0.4882),
                (0.7828, 0.4806),
                (0.1772, 0.5989),
                (0.8392, 0.5961),
                (0.2520, 0.7657),
                (0.3278, 0.7990),
            ]
            if name == "gemini"
            else None,
        )
        im.save(OUT / f"{name}.webp", "WEBP", quality=90, method=6)
        print("ok", name, (OUT / f"{name}.webp").stat().st_size)

    if len(sys.argv) == 1:
        # favicon / app icon from hero head crop
        hero = Image.open(OUT / "hero.webp")
        head = hero.crop((96, 20, 416, 340)).resize((256, 256), Image.LANCZOS)
        bgc = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        mask = Image.new("L", (256, 256), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, 255, 255), 56, fill=255)
        tile = Image.new("RGBA", (256, 256), (214, 238, 255, 255))
        tile.alpha_composite(head)
        bgc.paste(tile, (0, 0), mask)
        bgc.save(ROOT / "web" / "public" / "icon-192.png")
        bgc.resize((512, 512), Image.LANCZOS).save(ROOT / "web" / "public" / "icon-512.png")
        print("icons ok")


if __name__ == "__main__":
    sys.exit(main())
