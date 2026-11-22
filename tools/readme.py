"""Fill the card blocks of README.md from cards/*.json (text, link, tags) and media/cards/.

    python tools/readme.py

README.md is written by hand except between the markers
<!-- cards:en --> ... <!-- /cards:en --> and <!-- cards:tr --> ... <!-- /cards:tr -->,
which this script rewrites: two cards per row, in the order the files give. A card with
"feature": true stands alone across the full width (Mode_Code, the one a technical reader
should stop at); its text may run longer.
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent


def cell(c: dict, lang: str, width: str = "50%") -> str:
    return (f'<td width="{width}" valign="top">\n'
            f'<a href="{c["link"]}"><img src="media/cards/{c["id"]}.webp" width="100%" alt="{c["alt"]}"></a>\n'
            f'<br><b><a href="{c["link"]}">{c["name"]}</a></b><br>\n'
            f'{c[lang]}<br>\n'
            f'<sub>{c["tags_" + lang]}</sub>\n'
            f'</td>')


def block(cards, lang: str) -> str:
    rows, pair = [], []
    for c in cards:
        if c.get("feature"):
            rows.append(f"<table><tr>\n{cell(c, lang, '100%')}\n</tr></table>")
            continue
        pair.append(c)
        if len(pair) == 2:
            rows.append("<table><tr>\n" + "\n".join(cell(x, lang) for x in pair) + "\n</tr></table>")
            pair = []
    if pair:
        rows.append("<table><tr>\n" + "\n".join(cell(x, lang) for x in pair) + "\n</tr></table>")
    return "\n\n".join(rows)


def main() -> None:
    cards = []
    for p in (ROOT / "cards").glob("*.json"):
        c = json.loads(p.read_text(encoding="utf-8"))
        c["id"] = p.stem
        cards.append(c)
    cards.sort(key=lambda c: c["order"])
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    for lang in ("en", "tr"):
        pat = re.compile(rf"(<!-- cards:{lang} -->).*?(<!-- /cards:{lang} -->)", re.S)
        if not pat.search(text):
            raise SystemExit(f"README.md has no cards:{lang} markers")
        text = pat.sub(lambda m: m.group(1) + "\n" + block(cards, lang) + "\n" + m.group(2), text)
    readme.write_text(text, encoding="utf-8")
    print(f"{len(cards)} cards written")


if __name__ == "__main__":
    main()
