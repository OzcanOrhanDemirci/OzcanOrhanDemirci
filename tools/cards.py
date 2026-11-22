"""Card media for the profile: media/cards/<id>.webp, built from the "media" part of cards/<id>.json.

    python tools/cards.py            all cards
    python tools/cards.py km pcg     only these

Every card is 16:9 at 800x450 (shown at about 400x225), with rounded corners and a
faint inner edge so dark pictures keep their shape on the light theme too. A recipe
says where the picture comes from:

  "video":  {"src": "...mp4", "segments": [[start_s, end_s], ...], "fps": 15}
            segments are joined with short dissolves, the loop closes with one too
  "frames": {"glob": ".../*.png", "fps": 15, "step": 1}
  "still":  {"src": "...png|jpg", "contain": "#0b0f14"}   contain: fit inside on that colour
  "slides": {"srcs": [...], "hold": 1.6, "fps": 15}         stills in turn, dissolving
  "phones": {"srcs": [...], "bg": "#101418"}   portrait screens side by side
  optional for all: "crop": [x0, y0, x1, y1] as fractions of the source, "fade": 0.4

The sources are outside this repository (in the projects themselves); the recipe keeps
the path, so a card can be rebuilt or re-cut later.
"""
import glob
import json
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
RECIPES = ROOT / "cards"
OUT = ROOT / "media" / "cards"
W, H = 800, 450
RADIUS = 18


def fit(im: Image.Image, crop=None) -> Image.Image:
    im = im.convert("RGB")
    if crop:
        w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    w, h = im.size
    s = max(W / w, H / h)
    im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    w, h = im.size
    return im.crop(((w - W) // 2, (h - H) // 2, (w - W) // 2 + W, (h - H) // 2 + H))


def contain(im: Image.Image, bg: str) -> Image.Image:
    im = im.convert("RGB")
    w, h = im.size
    s = min(W / w, H / h)
    im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    out = Image.new("RGB", (W, H), bg)
    out.paste(im, ((W - im.size[0]) // 2, (H - im.size[1]) // 2))
    return out


def mask() -> Image.Image:
    m = Image.new("L", (W * 4, H * 4), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, W * 4 - 1, H * 4 - 1), RADIUS * 4, fill=255)
    return m.resize((W, H), Image.LANCZOS)


MASK = None
EDGE = None


def finish(im: Image.Image) -> Image.Image:
    global MASK, EDGE
    if MASK is None:
        MASK = mask()
        inner = MASK.filter(ImageFilter.MinFilter(3))
        EDGE = ImageChops.subtract(MASK, inner).point(lambda v: v * 0.10)
    out = im.convert("RGBA")
    out = Image.composite(Image.new("RGBA", (W, H), (255, 255, 255, 255)), out, EDGE)
    out.putalpha(MASK)
    return out


def video_frames(src, segments, fps):
    frames = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, (a, b) in enumerate(segments):
            pat = f"{tmp}/s{i}_%04d.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-to", str(b), "-i", src,
                            "-vf", f"fps={fps}", pat], check=True)
            frames.append([Image.open(f).copy() for f in sorted(glob.glob(f"{tmp}/s{i}_*.png"))])
    return frames


def dissolve(parts, n):
    """Join clips with n-frame dissolves; the last dissolves into the first, so it loops."""
    if len(parts) == 1 and n == 0:
        return parts[0]
    seq = []
    for i, p in enumerate(parts):
        nxt = parts[(i + 1) % len(parts)]
        seq += p[n:len(p) - n]   # its first n frames went into the dissolve before it
        for k in range(n):
            t = (k + 1) / (n + 1)
            seq.append(Image.blend(p[len(p) - n + k], nxt[k], t))
    return seq


def build(cid: str) -> None:
    r = json.loads((RECIPES / f"{cid}.json").read_text(encoding="utf-8"))["media"]
    if not r:
        print(f"{cid}: no media recipe yet")
        return
    crop = r.get("crop")
    if "video" in r:
        v = r["video"]
        fps = v.get("fps", 15)
        parts = [[fit(f, crop) for f in seg] for seg in video_frames(v["src"], v["segments"], fps)]
        seq = dissolve(parts, round(r.get("fade", 0.5) * fps))
    elif "frames" in r:
        v = r["frames"]
        fps = v.get("fps", 15)
        files = sorted(glob.glob(v["glob"]))[:: v.get("step", 1)]
        seq = [fit(Image.open(f), crop) for f in files]
        fps = fps
    elif "slides" in r:
        v = r["slides"]
        fps = v.get("fps", 15)
        hold = round(v.get("hold", 1.6) * fps)
        n = round(r.get("fade", 0.5) * fps)
        parts = [[fit(Image.open(s), crop)] * (hold + 2 * n) for s in v["srcs"]]
        seq = dissolve(parts, n)
    elif "phones" in r:
        seq, fps = [phones(r["phones"])], 0
    else:
        s = r["still"]
        im = Image.open(s["src"])
        seq, fps = [contain(im, s["contain"]) if s.get("contain") else fit(im, crop)], 0
    frames = [finish(f) for f in seq]
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{cid}.webp"
    q = r.get("quality", 78)
    if len(frames) > 1:
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=round(1000 / fps),
                       loop=0, quality=q, method=4)
    else:
        frames[0].save(out, quality=q + 10, method=6)
    print(f"{out.relative_to(ROOT)}  {len(frames)} frames  {out.stat().st_size / 1e6:.2f} MB")


def phones(p) -> Image.Image:
    """Portrait screens side by side on a quiet backdrop, as rounded slabs."""
    bg = Image.new("RGB", (W, H), p.get("bg", "#101418"))
    srcs = p["srcs"]
    n = len(srcs)
    ph = int(H * p.get("height", 0.86))
    gap = p.get("gap", 26)
    shots = []
    for s in srcs:
        im = Image.open(s).convert("RGB")
        if p.get("trim_top"):
            w, h = im.size
            im = im.crop((0, int(h * p["trim_top"]), w, h))
        w, h = im.size
        sw = round(w * ph / h)
        shots.append(im.resize((sw, ph), Image.LANCZOS))
    total = sum(s.size[0] for s in shots) + gap * (n - 1)
    x = (W - total) // 2
    y = (H - ph) // 2 + p.get("dy", 0)
    for s in shots:
        m = Image.new("L", s.size, 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, s.size[0] - 1, s.size[1] - 1), 14, fill=255)
        bg.paste(s, (x, y), m)
        x += s.size[0] + gap
    return bg


if __name__ == "__main__":
    ids = sys.argv[1:] or [p.stem for p in sorted(RECIPES.glob("*.json"))]
    for cid in ids:
        build(cid)
