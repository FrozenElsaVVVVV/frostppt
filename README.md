# ❄ FrostPPT

> *Where ideas crystallise.*

**FrostPPT** is a Python library and interactive CLI for building stunning frosted-glass HTML presentations — no design tools, no browser extensions, no dependencies beyond a standard Python install.

Built by **D. Saahishnu Ram**.

---

## Features

- **Frosted glass card** with animated grain texture and crystallising frost effect
- **Animated backgrounds** — 53 gradient presets across moody darks and bright lights, plus fully custom
- **Drifting orbs** — 54 colour presets for soft ambient lighting
- **55 font pairings** — every Google Font supported, auto-loaded from CDN
- **Auto text contrast** — detects card surface luminance and picks readable text automatically
- **6 slide types** — Title, Content, Two Column, Quote, Media, Raw HTML
- **`.frppt` project format** — save, share, and reload your whole deck as a JSON file
- **Decompile any HTML** — every generated `.html` embeds the full source; recover it with one command
- **Autosave** — writes to `~/.frostppt_autosave.frppt` on every change and on `^C`
- **Mouse-reactive border** — border opacity responds to cursor proximity
- **Keyboard navigation** — `<-` `->` `Space` to advance, `Esc` to exit fullscreen
- **Zero runtime dependencies** — pure Python 3.7+, single-file output opens in any modern browser

---

## Installation

```bash
# From PyPI
pip install frostppt

# Or just drop both files into your project
frostppt.py
frostppt_cli.py
```

---

## Quick Start

### Interactive CLI

```bash
python frostppt_cli.py
```

Follow the prompts to choose a background, fonts, colours, and build your slides. When done, two files are saved side by side:

```
my_deck.html    <- open in browser to present
my_deck.frppt   <- editable project file
```

### Python API

```python
from frostppt import Presentation, Slide

prs = Presentation(
    title="My Deck",
    bg_color="#1a1428",
)

prs.add(Slide.title(
    heading="Where Ideas Crystallise",
    tagline="A FrostPPT presentation",
    pills=["Python", "Open Source"],
))

prs.add(Slide.content(
    heading="Why FrostPPT?",
    body=["No PowerPoint. No Keynote. Just a terminal and a browser."],
    stats=[("55", "font pairs"), ("53", "backgrounds"), ("0", "dependencies")],
))

prs.add(Slide.quote(
    quote="Cold clarity.\nWarm presence.",
    attribution="D. Saahishnu Ram",
))

prs.save("my_deck.html")
```

---

## Slide Types

| Type | Method | Description |
|---|---|---|
| Title | `Slide.title()` | Hero heading, tagline, body, pill tags |
| Content | `Slide.content()` | Paragraphs, stat callouts, pill tags |
| Two Column | `Slide.two_col()` | 2x2 comparison grid |
| Quote | `Slide.quote()` | Full-bleed centered quote |
| Media | `Slide.media()` | Image / video / audio (local file or URL) |
| Raw HTML | `Slide.raw()` | Full HTML control |

---

## `.frppt` Project Files

FrostPPT saves your deck as a human-readable JSON `.frppt` file alongside every HTML export. Share it with collaborators, reload it, or edit it by hand.

```bash
# Resume an interrupted or crashed session
python frostppt_cli.py --resume

# Open a saved project file
python frostppt_cli.py --load my_deck.frppt

# Recover a project from a previously exported HTML
python frostppt_cli.py --decompile my_deck.html

# Show all flags
python frostppt_cli.py --help
```

Every generated HTML embeds the full source JSON invisibly in a `<meta name="frppt-source">` tag, so decompilation is always lossless — even if you lose the `.frppt` file.

---

## Presentation Controls

| Key / Action | Effect |
|---|---|
| `<-` `->` or `Space` | Navigate slides |
| Hover bottom-left corner | Show nav HUD (arrows, dots, counter) |
| Move mouse near card | Border glows toward cursor |
| `Esc` | Exit fullscreen |

---

## Presentation Parameters

```python
Presentation(
    title            = "My Deck",
    bg_color         = "#1a1428",           # base background hex
    gradient         = {                     # optional animated gradient
        "type":      "linear-diagonal",     # linear-diagonal | linear-horizontal
        "colors":    ["#1a1428","#0d1f3c"], #   | linear-vertical | radial
        "duration":  10,                    # animation loop in seconds
    },
    orb_colors       = ["#c084fc88", ...],  # 2-7 semi-transparent hex colours
    heading_font     = "Playfair Display",  # any Google Font or web-safe name
    body_font        = "Inter",
    heading_color    = None,                # None = auto-selected from bg luminance
    body_color       = None,
    card_width       = 700,                 # px
    card_min_height  = 420,                 # px floor (card auto-grows to fit content)
    grain_opacity    = 0.28,                # 0.0-1.0
    frost_duration   = 1800,               # ms for crystallise animation
    shatter_duration = 1100,               # ms for shatter exit animation
)
```

---

## Project Structure

```
frostppt.py        <- library  (Presentation + Slide classes)
frostppt_cli.py    <- interactive CLI
README.md
LICENSE
```

---

## Contributing

Contributions are welcome. Fork the repo, make your changes, and open a pull request. All modifications to FrostPPT source files must remain open source under the same licence (MPL-2.0) and must preserve credit to the original author.

---

## Licence

This project is licensed under the **Mozilla Public License 2.0 (MPL-2.0)**.

You are free to:
- Use it in personal and commercial projects
- Modify and redistribute it
- Include it in larger projects, even proprietary ones

You must:
- Keep credit to the original author — **D. Saahishnu Ram**
- Open source any modifications to FrostPPT files under the same MPL-2.0 licence
- Include the licence notice in any distribution

See [`LICENSE`](LICENSE) for the full text.

---

## Author

**D. Saahishnu Ram**

*"Where ideas crystallise."*
