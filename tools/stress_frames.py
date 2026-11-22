"""Frames for the stress_test card, rendered from the app's own shaders on this PC.

    python tools/stress_frames.py

Drives C:/dev/stress_test/tools/scene_preview.py (its scene classes and post chain)
for a few seconds of chosen shots, at the card's frame rate, and writes them to
C:/dev/stress_test/tools/out/card/<scene>/NNN.png (ignored by that repo's git).
cards/stress.json then joins them with dissolves. A short GPU job (about a minute).
The shots below are what the card shows; change a start time and rebuild.
"""

import pathlib
import sys

if not sys.flags.utf8_mode:  # the shaders are UTF-8; Windows' default codec cannot read them
    import subprocess
    sys.exit(subprocess.run([sys.executable, "-X", "utf8", __file__, *sys.argv[1:]]).returncode)
REPO = pathlib.Path("C:/dev/stress_test")
sys.path.insert(0, str(REPO / "tools"))

import moderngl  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import scene_preview as sp  # noqa: E402

OUT = REPO / "tools/out/card"
FPS = 12
SIZE = (800, 450)        # the scene's size; the post chain renders at twice that
ACCUMULATE = 48          # jittered frames averaged per image, as the phone's history settles
SHOTS = [                # scene, start (s), length (s): inside one 14 s shot, no cut
    ("pool", 43.4, 2.6),     # overhead orbit: the glowing core through the ring
    ("hole", 23.6, 2.6),     # the disk edge-on, bent over the shadow
    ("forest", 9.4, 2.6),    # light through the trees, rain
    ("white", 29.8, 2.6),    # the ring tunnel
]


def render(name, start, length):
    ctx = moderngl.create_standalone_context(require=430)
    quad = ctx.buffer(np.array([-1, -1, 3, -1, -1, 3], dtype="f4").tobytes())
    scene = {"forest": sp.ForestScene, "white": sp.WhiteScene, "hole": sp.HoleScene}.get(name)
    scene = scene(ctx, quad, SIZE) if scene else sp.PoolScene(ctx, quad, SIZE, particles=True)
    post = sp.Post(ctx, quad, SIZE, (SIZE[0] * 2, SIZE[1] * 2), scene.defines)
    out = OUT / name
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.png"):
        f.unlink()
    for k in range(round(length * FPS)):
        t = start + k / FPS
        scene.prepare(t)
        total = np.zeros((SIZE[1], SIZE[0], 3), dtype=np.float64)
        for i in range(ACCUMULATE):
            total += scene.draw(t, i)
        hdr = np.nan_to_num((total / ACCUMULATE).astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
        history = post.target(SIZE, np.concatenate([hdr, np.ones_like(hdr[..., :1])], axis=2).astype("f2"))
        image = post.run(history, scene.distance, scene.layer(t), t)
        history.release()
        Image.fromarray(image).resize(SIZE, Image.LANCZOS).save(out / f"{k:03d}.png")
    ctx.release()
    print(f"{name}: {k + 1} frames from {start} s")


if __name__ == "__main__":
    for shot in SHOTS:
        render(*shot)
