"""Fill the card blocks of README.md from cards/*.json (text, link, tags) and media/cards/.

    python tools/readme.py

README.md is written by hand except between the markers
<!-- cards:en --> ... <!-- /cards:en --> and <!-- cards:tr --> ... <!-- /cards:tr -->,
which this script rewrites: two cards per row, in the order the files give.
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent


def cell(c: dict, lang: str) -> str:
    return (f'<td width="50%" valign="top">\n'
            f'<a href="{c["link"]}"><img src="media/cards/{c["id"]}.webp" width="100%" alt="{c["alt"]}"></a>\n'
            f'<br><b><a href="{c["link"]}">{c["name"]}</a></b><br>\n'
            f'{c[lang]}<br>\n'
            f'<sub>{c["tags_" + lang]}</sub>\n'
            f'</td>')


def block(cards, lang: str) -> str:
    rows = []
    for i in range(0, len(cards), 2):
        pair = "\n".join(cell(c, lang) for c in cards[i:i + 2])
        rows.append(f"<table><tr>\n{pair}\n</tr></table>")
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
