"""Showreel poster: media/showreel/poster-en.webp and poster-tr.webp, from media/showreel/recipe.json.

    python tools/reel.py

The page cannot play the video itself in every place (GitHub's app and a plain repo file
do not), so the section shows a moving poster that links to the full video: a few
seconds cut from the video's own beats, joined with dissolves like the cards, with a
small play mark in the corner. The video opens on the same lighthouse as the hero, so
the poster skips the opening and samples the projects instead. Each language is cut
from its own video, because the captions in the video are in that language.
"""
import json
import pathlib

from PIL import Image, ImageDraw

import cards

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIR = ROOT / "media" / "showreel"


def play_mark(w: int, h: int) -> Image.Image:
    """A dark translucent disc with a white triangle, bottom right, drawn at 4x and reduced."""
    d = round(w * 0.075)
    pad = round(w * 0.03)
    s = 4
    layer = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    g = ImageDraw.Draw(layer)
    x1, y1 = (w - pad) * s, (h - pad) * s
    x0, y0 = x1 - d * s, y1 - d * s
    g.ellipse((x0, y0, x1, y1), fill=(13, 17, 23, 170), outline=(255, 255, 255, 150), width=2 * s)
    cx, cy, r = (x0 + x1) / 2, (y0 + y1) / 2, d * s * 0.22
    g.polygon([(cx - r * 0.75, cy - r), (cx - r * 0.75, cy + r), (cx + r * 1.05, cy)], fill=(255, 255, 255, 235))
    return layer.resize((w, h), Image.LANCZOS)


def main() -> None:
    r = json.loads((DIR / "recipe.json").read_text(encoding="utf-8"))
    cards.W, cards.H = r["size"]
    cards.MASK = None
    fps = r["fps"]
    mark = play_mark(cards.W, cards.H) if r.get("play") else None
    for lang, src in r["videos"].items():
        parts = [[cards.fit(f) for f in seg] for seg in cards.video_frames(src, r["segments"], fps)]
        seq = cards.dissolve(parts, round(r["fade"] * fps))
        frames = []
        for f in seq:
            f = f.convert("RGBA")
            if mark:
                f = Image.alpha_composite(f, mark)
            frames.append(cards.finish(f))
        out = DIR / r["out"].format(lang=lang)
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=round(1000 / fps),
                       loop=0, quality=r["quality"], method=4)
        print(f"{out.relative_to(ROOT)}  {len(frames)} frames  {len(frames) / fps:.1f} s  "
              f"{out.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
