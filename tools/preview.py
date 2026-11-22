"""Render README.md the way GitHub does and screenshot it: desktop and phone, light and dark.

    python tools/preview.py [out_dir]

The markdown goes through GitHub's own renderer (`gh api markdown`), is wrapped in
github-markdown-css (npm, path in CSS_DIR) at the width of the profile page's README
box, and is shot with Playwright in Chrome. Animated images are shot as they stand
when the page is ready, so a preview shows one moment of each loop.
"""
import json
import pathlib
import subprocess
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSS_DIR = pathlib.Path("C:/Temp/vitrin/preview/node_modules/github-markdown-css")
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "C:/Temp/vitrin/shots")

# Profile page README box: about 830 px of content on a desktop window, the full
# width less 16 px each side on a phone.
PAGE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="{scheme}">
<style>{css}
html,body{{margin:0;background:{page_bg}}}
.box{{max-width:{box}px;margin:{margin};border:1px solid {border};border-radius:6px;background:{bg};}}
.box-head{{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;color:{muted};padding:16px 24px 0}}
.markdown-body{{padding:16px 24px 24px;}}
@media (max-width:600px){{.box{{margin:12px 8px}} .markdown-body{{padding:12px 16px 16px}}}}
</style></head><body><div class="box"><div class="box-head">OzcanOrhanDemirci / README.md</div>
<article class="markdown-body">{body}</article></div>
<script>
Promise.all([...document.images].map(i => i.decode().catch(()=>0))).then(()=>document.body.dataset.ready=1);
</script></body></html>"""

THEMES = {
    "light": dict(css="github-markdown-light.css", page_bg="#ffffff", bg="#ffffff", border="#d1d9e0", muted="#59636e"),
    "dark": dict(css="github-markdown-dark.css", page_bg="#0d1117", bg="#0d1117", border="#3d444d", muted="#9198a1"),
}


def render_markdown() -> str:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    res = subprocess.run(
        ["gh", "api", "markdown", "--input", "-"],
        input=json.dumps({"text": text, "mode": "gfm", "context": "OzcanOrhanDemirci/OzcanOrhanDemirci"}),
        capture_output=True, text=True, encoding="utf-8", check=True)
    return res.stdout


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    body = render_markdown()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        for scheme, t in THEMES.items():
            css = (CSS_DIR / t["css"]).read_text(encoding="utf-8")
            html = PAGE.format(scheme=scheme, css=css, body=body, box=880, margin="24px auto", **{k: v for k, v in t.items() if k != "css"})
            page_file = ROOT / f".preview-{scheme}.html"
            page_file.write_text(html, encoding="utf-8")
            for device, ctx_args in {
                "desktop": dict(viewport={"width": 1280, "height": 900}, device_scale_factor=1),
                "phone": dict(**p.devices["iPhone 13"]),
            }.items():
                ctx = browser.new_context(color_scheme=scheme, **ctx_args)
                page = ctx.new_page()
                page.goto(page_file.as_uri())
                page.wait_for_function("document.body.dataset.ready == 1", timeout=60000)
                page.wait_for_timeout(500)
                shot = OUT / f"{device}-{scheme}.png"
                page.screenshot(path=str(shot), full_page=True)
                print(shot)
                ctx.close()
            page_file.unlink()
        browser.close()


if __name__ == "__main__":
    main()
