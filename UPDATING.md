# Updating the profile

This repository is the GitHub profile page of Özcan Orhan Demirci: `README.md` is what
the profile shows. It is meant to change often, so every part has one place.

| What | Where | Rebuild |
| --- | --- | --- |
| Page text, English and the Turkish section | `README.md`, written by hand | nothing |
| A card: name, link, text in both languages, tags, alt text, where its picture comes from | `cards/<id>.json` | `python tools/cards.py <id>` then `python tools/readme.py` |
| Card order | `"order"` in each card file | `python tools/readme.py` |
| Section numbers and the accent colour | `media/headings/headings.json` | `python tools/headers.py` |
| Hero loop | `media/hero/` (its `recipe.md` says how it was rendered in pc_graphics) | see the recipe |
| ChefOl phone, English and Turkish | `media/chefol/` (`recipe.json`, `recipe-tr.json`; Turkish screens end in `_TR`) | `python tools/phone.py` |
| Quiz picture under Live (projector and a player's phone) | `media/quiz/recipe.json` (English run, `yerel/en`) and `recipe-tr.json` (Turkish run, `yerel`); sources in `bilgi-yarismasi-showcase/yerel` (local only, bot players) | `python tools/quiz_scene.py` |
| Mode_Code card's loop | the real terminal recording in `C:/dev/video/public/showreel/modecode/h` (its `SOURCE.md` says how it is made) | `python tools/cards.py modecode` |
| stress_test card's frames | the shots in `tools/stress_frames.py` (rendered from the app's shaders on the GPU) | `python tools/stress_frames.py` then `python tools/cards.py stress` |
| Mobil_App_Check_List card's stills | the stack pairs in `tools/checklist_frames.py` (shot from the PWA in Playwright) | `python tools/checklist_frames.py` then `python tools/cards.py checklist` |
| Showreel (section 03) | the player is Özcan's upload (720p, under the free plan's 10 MB, in closed issue #1, which must not be deleted); the moving poster above it is cut from the finals in `C:/dev/video/out/showreel/` by `media/showreel/recipe.json` | `python tools/reel.py` |

Each language section shows an app in that language where the app speaks both (Özcan,
11-22). A card's `"media_tr"` names the Turkish sources and builds `media/cards/<id>-tr.webp`,
`"alt_tr"` is its Turkish alt text; a one-language app (Kontrol Merkezi) or a picture
with no words (pc_graphics, stress_test) has one image for both. Mode_Code's Turkish
loop is the same recording run with the program in Turkish (`h-tr/`).

`tools/readme.py` rewrites only the blocks between `<!-- cards:en -->` and
`<!-- /cards:en -->` (and the `tr` pair); everything else in `README.md` is left alone.

Selected work is one project per row (picture across the column, name, a sentence or
two, tech line); tables of pairs became thin columns on a phone. Every picture is full
width; a low-key card (`"light": true`) is low-key by its place near the end and its
short text, not by a smaller picture. A card whose repository is not public yet has no
`"link"` (keep it as `"link_when_public"` until then), so nothing links to a 404.

A card's picture is built from sources that live in the projects themselves (paths in
the card file), so a new screenshot or a new loop is a matter of pointing the card at it
and rebuilding. Cards are 800x450 WebP, animated or still, with rounded corners.

## Before pushing

`python tools/preview.py` renders the README through GitHub's own markdown renderer and
shoots it on a desktop and a phone, light and dark, into `C:/Temp/vitrin/shots`. Look at
the phone shots: that is where most visitors see it. `--open` shoots
the Turkish section alone, opened (the whole page opened passes Chrome's screenshot limit). It needs `gh`, Python Playwright
with Chrome, and `github-markdown-css` (path at the top of the script).

## Rules that hold

- Images of private projects may appear; their code never does. Private projects link to
  their public `-showcase` repository.
- U-108-Remake appears nowhere on this page.
- Animations are WebP or GIF, never animated SVG (it does not always play in GitHub's
  mobile app). GitHub strips JavaScript and CSS.
- Fonts: IBM Plex (SIL Open Font License, `media/fonts/OFL.txt`), the same family as the
  pc_graphics interface.
