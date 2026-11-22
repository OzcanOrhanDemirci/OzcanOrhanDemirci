"""Build the quiz app's picture under "Live": the projector and a player's phone, side by side.

    python tools/quiz_scene.py

Reads media/quiz/recipe.json. The projector is cut from the showcase's local run
(bilgi-yarismasi-showcase/yerel, bot players, no real names); each segment shows the phone
screen of the same moment: answering, a right answer, the leaderboard, the podium.
Writes an animated WebP with a transparent background, so it sits on light and dark themes.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from phone import Phone, rounded_mask, SS  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIR = ROOT / "media" / "quiz"


def video_frames(src, t0, t1, fps, width, tmp):
    pat = pathlib.Path(tmp) / f"f{t0:.1f}_%04d.png"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(t0), "-to", str(t1), "-i", src,
                    "-vf", f"fps={fps},scale={width}:-1:flags=lanczos", str(pat)], check=True)
    return [Image.open(p).convert("RGB") for p in sorted(pathlib.Path(tmp).glob(f"f{t0:.1f}_*.png"))]


def with_status_bar(im, share):
    """Room above the app for the camera, in the colour of the app's own top edge.

    The screenshots have no status bar, so the punch-hole would sit on the app's header."""
    band = round(im.height * share)
    out = Image.new("RGB", (im.width, im.height + band), im.getpixel((im.width // 2, 2)))
    out.paste(im, (0, band))
    return out


def screen_frame(size, bezel, radius, body, rim):
    """A display's bezel: the projector's picture shown as a screen, as the phone is."""
    w, h = size[0] + 2 * bezel, size[1] + 2 * bezel
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), radius * SS, fill=rim)
    r = round(1.6 * SS)
    d.rounded_rectangle((r, r, w * SS - 1 - r, h * SS - 1 - r), radius * SS - r, fill=body)
    return big.resize((w, h), Image.LANCZOS)


def main():
    r = json.loads((DIR / "recipe.json").read_text(encoding="utf-8"))
    f = r["frame"]
    bz = r["bezel"]
    sw = r["screen_width"]
    sh = round(sw * 9 / 16)
    shell = screen_frame((sw, sh), bz, 14, f["body"], f["rim"])
    smask = rounded_mask((sw, sh), 6)

    ph_src = pathlib.Path(r["phones"])
    first = with_status_bar(Image.open(ph_src / r["segments"][0]["phone"]).convert("RGB"), r["status_bar"])
    phone = Phone(r["phone_width"], first.height / first.width, f)

    W = shell.width + r["gap"] + phone.size[0]
    H = max(shell.height, phone.size[1])
    sy = H - shell.height  # bottoms aligned
    px = shell.width + r["gap"]

    def compose(proj, ph):
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        s = shell.copy()
        s.paste(proj, (bz, bz), smask)
        c.alpha_composite(s, (0, sy))
        c.alpha_composite(phone.frame(ph), (px, H - phone.size[1]))
        return c

    frames = []
    with tempfile.TemporaryDirectory() as tmp:
        for seg in r["segments"]:
            vf = video_frames(r["video"], seg["from"], seg["to"], r["fps"], sw, tmp)
            ph = with_status_bar(Image.open(ph_src / seg["phone"]).convert("RGB"), r["status_bar"])
            ph = ph.resize(phone.screen_size, Image.LANCZOS)
            frames.append([compose(v, ph) for v in vf])

    nf = max(1, round(r["fade"] * r["fps"]))
    out_frames = []
    for i, seg in enumerate(frames):
        nxt = frames[(i + 1) % len(frames)]
        body = seg[:-nf] if len(seg) > nf else seg
        out_frames += body
        tail = seg[-nf:]
        for k, a in enumerate(tail):
            x = (k + 1) / (nf + 1)
            x = x * x * (3 - 2 * x)
            out_frames.append(Image.blend(a, nxt[min(k, len(nxt) - 1)], x))

    step = round(1000 / r["fps"])
    out = DIR / r["out"]
    out_frames[0].save(out, save_all=True, append_images=out_frames[1:], duration=step, loop=0,
                       quality=r["quality"], method=6)
    print(f"{out.relative_to(ROOT)}  {W}x{H}  {len(out_frames)} frames  "
          f"{len(out_frames) * step / 1000:.1f} s  {out.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
