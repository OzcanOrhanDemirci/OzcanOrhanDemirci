"""Stills for the Mobil_App_Check_List card: one checklist item under different stacks.

    python tools/checklist_frames.py

Serves C:/dev/Mobil_App_Check_List locally, opens the PWA in Playwright (English,
technical wording, dark, showcase design, a phone-width viewport) once per
framework/backend pair below, and shoots the project pill and item 6.1 ("Backend
Connection and Authentication"), whose text is written for each stack. Each pair is
composed into an 800x450 still in media/sources/checklist/; cards/checklist.json
dissolves between them. Needs Python Playwright with Chromium.
"""
import json
import pathlib
import socket
import subprocess
import sys
import tempfile
import time

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = pathlib.Path("C:/dev/Mobil_App_Check_List")
OUT = ROOT / "media" / "sources" / "checklist"
PAIRS = [("flutter", "firebase"), ("reactNative", "supabase"), ("kotlin", "pocketbase")]
ITEM = "#feat-06-6-1"
VIEW_W, DPR = 430, 2
W, H = 800, 450
BG = (6, 6, 13)  # the showcase page behind the item
RIGHT_W, PAD = 500, 18


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def shoot(page, port, fw, be, tmp):
    store = {"version": 1, "activeId": "p", "projects": [{
        "id": "p", "name": "My App", "createdAt": "2026-11-01T10:00:00Z", "updatedAt": "2026-11-01T10:00:00Z",
        "data": {"framework": fw, "backend": be, "state": {}, "notes": {}, "collapsed": [], "celebrations": {},
                 "viewMode": "both", "viewFilter": "all", "lockState": False, "collapseInit": False}}]}
    page.goto(f"http://127.0.0.1:{port}/", wait_until="domcontentloaded")
    page.evaluate("""(s) => {
        const set = (k, v) => localStorage.setItem(k, v);
        set('mobil_kontrol_projects_v2', s); set('mobil_kontrol_lang_v1', 'en');
        set('mobil_kontrol_style_v1', 'technical'); set('mobil_kontrol_mode_v1', 'build');
        set('mobil_kontrol_theme_v1', 'dark'); set('mobil_kontrol_design_v1', 'showcase'); }""", json.dumps(store))
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(700)
    page.evaluate("""() => {
        const m = document.getElementById('welcomeModal'); if (m) m.hidden = true;
        document.querySelectorAll('section.category').forEach(c => c.classList.remove('collapsed'));
        const st = document.createElement('style');  /* sticky bars would cover the item */
        st.textContent = '[class*=sticky], #installBanner { position: static !important; }';
        document.head.appendChild(st); }""")
    page.wait_for_timeout(500)
    pill = tmp / f"{fw}_pill.png"
    page.locator("#projectFrameworkBtn .proj-pill-rows").screenshot(path=pill)
    page.evaluate("""(sel) => { const r = document.querySelector(sel).getBoundingClientRect();
        scrollTo(0, r.top + scrollY - 12); }""", ITEM)
    page.wait_for_timeout(1400)  # showcase reveals sections on scroll
    x, y, w = page.evaluate("""(sel) => { const r = document.querySelector(sel).getBoundingClientRect();
        return [r.left, r.top, r.width]; }""", ITEM)
    h = (H - 2 * PAD) * w / RIGHT_W  # the same scale for every pair, so the text does not jump
    item = tmp / f"{fw}_item.png"
    page.screenshot(path=item, clip={"x": x, "y": y, "width": w, "height": h})
    return Image.open(pill).convert("RGB"), Image.open(item).convert("RGB")


def compose(pill, item):
    """The project's stack on the left, the item on the right, its bottom fading into the page."""
    out = Image.new("RGB", (W, H), BG)
    right = item.resize((RIGHT_W, H - 2 * PAD), Image.LANCZOS)
    fade = Image.new("L", right.size, 255)
    d = ImageDraw.Draw(fade)
    n = 56
    for i in range(n):
        d.line((0, right.size[1] - n + i, right.size[0], right.size[1] - n + i), fill=round(255 * (1 - (i + 1) / n) ** 1.5))
    x = W - RIGHT_W - PAD
    out.paste(right, (x, PAD), fade)
    # the pill's rows, larger than life so they read on a phone, on the pill's own surface
    col = x - PAD
    bg = pill.getpixel((1, 1))  # trim the rows to their text
    diff = pill.convert("L").point(lambda v, b=sum(bg) // 3: 255 if abs(v - b) > 18 else 0)
    pill = pill.crop(diff.getbbox())
    cw = col - 28  # one chip size for every pair, so only the words change
    k = min(1.0, (cw - 44) / pill.size[0])
    p = pill.resize((round(pill.size[0] * k), round(pill.size[1] * k)), Image.LANCZOS)
    ch = p.size[1] + 2 * 22
    cx, cy = (col - cw) // 2 + 6, (H - ch) // 2
    ImageDraw.Draw(out).rounded_rectangle((cx, cy, cx + cw, cy + ch), 16, fill=bg, outline=(54, 56, 72), width=2)
    out.paste(p, (cx + 22, cy + 22))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    port = free_port()
    server = subprocess.Popen([sys.executable, str(APP / "scripts/serve-local.py"), str(port)], cwd=APP,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1.5)
        with sync_playwright() as p, tempfile.TemporaryDirectory() as tmp:
            browser = p.chromium.launch()
            for fw, be in PAIRS:
                ctx = browser.new_context(viewport={"width": VIEW_W, "height": 900}, device_scale_factor=DPR,
                                          is_mobile=True, has_touch=True, reduced_motion="reduce")
                pill, item = shoot(ctx.new_page(), port, fw, be, pathlib.Path(tmp))
                path = OUT / f"{fw}-{be}.png"
                compose(pill, item).save(path)
                print(path.relative_to(ROOT))
                ctx.close()
            browser.close()
    finally:
        server.terminate()


if __name__ == "__main__":
    main()
