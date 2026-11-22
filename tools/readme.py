"""Fill the card blocks of README.md from cards/*.json (text, link, tags) and media/cards/.

    python tools/readme.py

README.md is written by hand except between the markers
<!-- cards:en --> ... <!-- /cards:en --> and <!-- cards:tr --> ... <!-- /cards:tr -->,
which this script rewrites in the order the files give.

One project per row: the picture across the column, then the name, a sentence or two and
the tech line. Pairs in tables were dropped on 11-22: GitHub's tables never reflow, so on
a phone two cards became two thin columns of text with small pictures, and there are no
media queries to fix that. Every picture is full width. A low-key project ("light": true
in its card) is low-key by its place near the end and its short text, not by a smaller
picture: at 60% the two such cards looked small and out of place beside the others
(Özcan, 11-22).

A card with "media_tr" (an app that speaks both languages) shows media/cards/<id>-tr.webp
in the Turkish section, and "alt_tr" is the Turkish section's alt text.

A card without "link" (its repository not yet public) shows its picture and name
unlinked, so a visitor never meets a dead link.
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent


def linked(c: dict, inner: str) -> str:
    return f'<a href="{c["link"]}">{inner}</a>' if c.get("link") else inner


def card(c: dict, lang: str) -> str:
    pic = c["id"] + ("-tr" if lang == "tr" and c.get("media_tr") else "")
    alt = c.get("alt_" + lang) or c["alt"]
    img = f'<img src="media/cards/{pic}.webp" width="100%" alt="{alt}">'
    return (f'<p>{linked(c, img)}</p>\n\n'
            f'<p><b>{linked(c, c["name"])}</b><br>\n'
            f'{c[lang]}<br>\n'
            f'<sub>{c["tags_" + lang]}</sub></p>')


def block(cards, lang: str) -> str:
    return "\n\n<br>\n\n".join(card(c, lang) for c in cards)


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
