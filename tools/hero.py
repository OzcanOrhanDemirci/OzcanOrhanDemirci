"""The hero loop at the top of the profile: media/hero/hero.webp, from media/hero/recipe.json.

    python tools/hero.py                      build from media/hero/recipe.json
    python tools/hero.py some/recipe.json     build from another recipe (trying options)

The frames are a seamless loop rendered headless in pc_graphics (media/hero/recipe.md says
how). This script only crops them to the banner, rounds the corners and writes one animated
WebP; nothing is set over the picture (Özcan's choice: the scene stands on its own, his
line opens the page as text). Recipe keys:

  "frames":  glob of the PNG frames            "step":   take every n-th frame
  "fps":     playback rate after the step      "ratio":  banner width / height
  "y":       vertical centre of the crop, 0..1 "width":  output width in pixels
  "quality": WebP quality                      "out":    output path (repo-relative)
"""

import glob
import json
import pathlib
import sys

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent


def rounded(size, r):
    m = Image.new("L", (size[0] * 4, size[1] * 4), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, m.width - 1, m.height - 1), r * 4, fill=255)
    return m.resize(size, Image.LANCZOS)


def build(recipe_path: pathlib.Path) -> None:
    r = json.loads(recipe_path.read_text(encoding="utf-8"))
    files = sorted(glob.glob(r["frames"]))[:: r.get("step", 1)]
    if not files:
        raise SystemExit(f"no frames at {r['frames']}: render them first (media/hero/recipe.md)")
    W, H = Image.open(files[0]).size
    ratio = r.get("ratio", 2.0)
    ch = round(W / ratio)
    cy = r.get("y", 0.5) * H
    y0 = int(min(max(cy - ch / 2, 0), H - ch))
    out_w = r.get("width", 1280)
    size = (out_w, round(out_w / ratio))
    mask = rounded(size, round(size[1] * 0.025))
    frames = []
    for f in files:
        im = Image.open(f).convert("RGB").crop((0, y0, W, y0 + ch)).resize(size, Image.LANCZOS).convert("RGBA")
        im.putalpha(mask)
        frames.append(im)
    out = ROOT / r.get("out", "media/hero/hero.webp")
    out.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=round(1000 / r.get("fps", 15)),
                   loop=0, quality=r.get("quality", 80), method=4)
    print(f"{out}  {len(frames)} frames  {size[0]}x{size[1]}  {out.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    build(pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "media" / "hero" / "recipe.json")
