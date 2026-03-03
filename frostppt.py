"""
frostppt.py — Frosted Glass Presentation Generator
====================================================
Usage:
    from frostppt import Presentation, Slide

    prs = Presentation(title="My Deck")
    prs.add(Slide.title(heading="Hello", tagline="World"))
    prs.add(Slide.content(heading="Details", body=["Para 1", "Para 2"]))
    prs.add(Slide.media(src="photo.jpg", caption="A caption"))
    prs.save("out.html")

Slide types: title | content | two_col | quote | media | raw
"""

from __future__ import annotations
import textwrap, html as html_mod, base64, mimetypes, json
from pathlib import Path
from typing import List, Optional, Tuple

FRPPT_VERSION = "1"   # bump when format changes incompatibly


# ─────────────────────────────────────────────────────────────────────────────
# Slide builders
# ─────────────────────────────────────────────────────────────────────────────

class Slide:
    """
    Internal: stores both rendered HTML (for presentation) and raw _data
    dict (for .frppt serialisation / decompile roundtrip).
    """

    def __init__(self, inner_html: str, data: Optional[dict] = None):
        self._html = inner_html
        self._data = data or {"type": "raw", "args": {"html": inner_html}}

    @property
    def html(self) -> str:
        return self._html

    # ── Factory methods ───────────────────────────────────────────────────────

    @staticmethod
    def title(heading: str, label: str = "", tagline: str = "",
              body: str = "", pills: Optional[List[str]] = None) -> "Slide":
        parts = []
        if label:
            parts.append(f'<div class="slide-label">{_e(label)}</div>')
        parts.append(f'<h1>{heading}</h1>')
        parts.append('<div class="divider"></div>')
        if tagline:
            parts.append(f'<p class="tagline">{tagline}</p>')
        if body:
            parts.append(f'<p>{_e(body)}</p>')
        if pills:
            pills_html = "".join(f'<span class="pill">{_e(p)}</span>' for p in pills)
            parts.append(f'<div class="pill-row">{pills_html}</div>')
        data = {"type": "title", "args": {"heading": heading, "label": label,
                "tagline": tagline, "body": body, "pills": pills}}
        return Slide("\n".join(parts), data)

    @staticmethod
    def content(heading: str, label: str = "", body: Optional[List[str]] = None,
                stats: Optional[List[Tuple[str, str]]] = None,
                pills: Optional[List[str]] = None, note: str = "") -> "Slide":
        parts = []
        if label:
            parts.append(f'<div class="slide-label">{_e(label)}</div>')
        parts.append(f'<h2>{_e(heading)}</h2>')
        parts.append('<div class="divider"></div>')
        for para in (body or []):
            parts.append(f'<p>{para}</p>')
        if stats:
            items = "".join(
                f'<div class="stat"><span class="stat-num">{_e(n)}</span>'
                f'<span class="stat-label">{_e(l)}</span></div>'
                for n, l in stats)
            parts.append(f'<div class="stat-row">{items}</div>')
        if pills:
            pills_html = "".join(f'<span class="pill">{_e(p)}</span>' for p in pills)
            parts.append(f'<div class="pill-row">{pills_html}</div>')
        if note:
            parts.append(f'<p style="margin-top:12px">{_e(note)}</p>')
        data = {"type": "content", "args": {"heading": heading, "label": label,
                "body": body, "stats": [list(s) for s in (stats or [])],
                "pills": pills, "note": note}}
        return Slide("\n".join(parts), data)

    @staticmethod
    def two_col(heading: str, columns: List[Tuple[str, str]],
                label: str = "", intro: str = "") -> "Slide":
        parts = []
        if label:
            parts.append(f'<div class="slide-label">{_e(label)}</div>')
        parts.append(f'<h2>{_e(heading)}</h2>')
        parts.append('<div class="divider"></div>')
        if intro:
            parts.append(f'<p>{_e(intro)}</p>')
        col_items = "".join(
            f'<div class="col-item"><span class="col-title">{_e(t)}</span>'
            f'<span class="col-body">{_e(b)}</span></div>'
            for t, b in columns)
        parts.append(f'<div class="two-col">{col_items}</div>')
        data = {"type": "two_col", "args": {"heading": heading, "label": label,
                "intro": intro, "columns": [list(c) for c in columns]}}
        return Slide("\n".join(parts), data)

    @staticmethod
    def quote(quote: str, attribution: str = "", label: str = "") -> "Slide":
        parts = []
        if label:
            parts.append(f'<div class="slide-label">{_e(label)}</div>')
        parts.append(f'<blockquote class="big-quote">{quote}</blockquote>')
        if attribution:
            parts.append(f'<p class="attribution">— {_e(attribution)}</p>')
        data = {"type": "quote", "args": {"quote": quote,
                "attribution": attribution, "label": label}}
        return Slide("\n".join(parts), data)

    @staticmethod
    def media(src: str, caption: str = "", label: str = "",
              autoplay: bool = False, loop: bool = False,
              controls: bool = True) -> "Slide":
        """
        Embed an image, video, or audio file.
        src can be a file path (auto base64-encoded) or a URL.
        Note: in .frppt the original src path/URL is stored (not the base64 blob).
        """
        parts = []
        if label:
            parts.append(f'<div class="slide-label">{_e(label)}</div>')

        mt, _ = mimetypes.guess_type(src)
        if not mt:
            mt = "image/jpeg"

        p = Path(src)
        if p.exists():
            data_b64 = base64.b64encode(p.read_bytes()).decode()
            uri = f"data:{mt};base64,{data_b64}"
        else:
            uri = src

        if mt.startswith("image/"):
            parts.append(
                f'<div class="media-wrap">'
                f'<img src="{uri}" alt="{_e(caption)}" class="slide-img">'
                f'</div>')
        elif mt.startswith("video/"):
            auto = ' autoplay muted' if autoplay else ''
            lp   = ' loop'           if loop     else ''
            ctrl = ' controls'       if controls else ''
            parts.append(
                f'<div class="media-wrap">'
                f'<video class="slide-video"{auto}{lp}{ctrl}>'
                f'<source src="{uri}" type="{mt}"></video>'
                f'</div>')
        elif mt.startswith("audio/"):
            auto = ' autoplay' if autoplay else ''
            lp   = ' loop'     if loop     else ''
            ctrl = ' controls' if controls else ''
            parts.append(
                f'<div class="media-wrap audio-wrap">'
                f'<div class="audio-icon">♪</div>'
                f'<audio class="slide-audio"{auto}{lp}{ctrl}>'
                f'<source src="{uri}" type="{mt}"></audio>'
                f'</div>')
        else:
            parts.append(f'<p>[Unsupported media: {_e(src)}]</p>')

        if caption:
            parts.append(f'<p class="media-caption">{_e(caption)}</p>')
        data = {"type": "media", "args": {"src": src, "caption": caption,
                "label": label, "autoplay": autoplay, "loop": loop,
                "controls": controls}}
        return Slide("\n".join(parts), data)

    @staticmethod
    def raw(html: str, label: str = "") -> "Slide":
        prefix = f'<div class="slide-label">{_e(label)}</div>\n' if label else ""
        data = {"type": "raw", "args": {"html": html, "label": label}}
        return Slide(prefix + html, data)

    # ── Deserialisation ───────────────────────────────────────────────────────

    @classmethod
    def _from_data(cls, d: dict) -> "Slide":
        """Reconstruct a Slide from a _data dict stored in .frppt / HTML meta."""
        t    = d.get("type", "raw")
        args = d.get("args", {})
        builders = {
            "title":   cls.title,
            "content": cls.content,
            "two_col": cls.two_col,
            "quote":   cls.quote,
            "media":   cls.media,
            "raw":     cls.raw,
        }
        builder = builders.get(t, cls.raw)
        # two_col columns need to be tuples
        if t == "two_col" and "columns" in args:
            args = dict(args); args["columns"] = [tuple(c) for c in args["columns"]]
        # content stats need to be tuples
        if t == "content" and "stats" in args and args["stats"]:
            args = dict(args); args["stats"] = [tuple(s) for s in args["stats"]]
        return builder(**args)


# ─────────────────────────────────────────────────────────────────────────────
# Presentation
# ─────────────────────────────────────────────────────────────────────────────

class Presentation:
    """
    Parameters
    ----------
    title              Deck title shown on start screen.
    bg_color           Page base background color.
    gradient           Dict with keys: type ('linear-diagonal'|'linear-horizontal'|
                       'linear-vertical'|'radial'), colors (list of 2-7 CSS color
                       strings), duration (animation seconds, default 8).
    orb_colors         List of 2–7 CSS colors for the drifting orbs.
    heading_font       Any Google Font name or web-safe font.
    body_font          Any Google Font name or web-safe font.
    heading_color      Override auto heading color (CSS color string).
    body_color         Override auto body color (CSS color string).
    card_width         Glass card width in px.
    card_min_height    Glass card min-height in px (card auto-grows to fit content).
    grain_opacity      0.0–1.0
    frost_duration     ms for frost crystallisation.
    shatter_duration   ms for shatter animation.
    """

    DEFAULT_ORBS = ["#c084fc88", "#67e8f988", "#a3e63588", "#818cf888"]

    # Text palettes keyed by bg luminance
    # dark_bg (lum < 0.35) → light text; light_bg (lum ≥ 0.35) → dark text
    _PALETTE = {
        "dark": {
            "h1":          "rgba(235,225,255,0.95)",
            "h2":          "rgba(220,210,245,0.90)",
            "p":           "rgba(195,185,225,0.80)",
            "label":       "rgba(200,190,235,0.48)",
            "tagline":     "rgba(205,190,240,0.68)",
            "quote":       "rgba(225,215,250,0.90)",
            "attribution": "rgba(180,170,215,0.52)",
            "stat_num":    "rgba(230,220,255,0.92)",
            "stat_label":  "rgba(180,170,215,0.52)",
            "pill_bg":     "rgba(255,255,255,0.07)",
            "pill_border": "rgba(255,255,255,0.18)",
            "pill_text":   "rgba(210,200,245,0.78)",
            "col_title":   "rgba(215,205,248,0.88)",
            "col_body":    "rgba(190,180,225,0.68)",
            "divider":     "rgba(255,255,255,0.14)",
        },
        "light": {
            "h1":          "rgba(18,4,40,0.92)",
            "h2":          "rgba(22,6,48,0.88)",
            "p":           "rgba(28,12,52,0.75)",
            "label":       "rgba(42,18,76,0.50)",
            "tagline":     "rgba(48,18,86,0.67)",
            "quote":       "rgba(18,4,40,0.86)",
            "attribution": "rgba(58,28,96,0.50)",
            "stat_num":    "rgba(18,4,40,0.90)",
            "stat_label":  "rgba(58,28,96,0.50)",
            "pill_bg":     "rgba(70,32,148,0.07)",
            "pill_border": "rgba(70,32,148,0.22)",
            "pill_text":   "rgba(36,12,74,0.74)",
            "col_title":   "rgba(26,8,56,0.84)",
            "col_body":    "rgba(42,18,72,0.65)",
            "divider":     "rgba(70,32,148,0.16)",
        },
    }

    def __init__(
        self,
        title: str = "Presentation",
        bg_color: str = "#1a1428",
        gradient: Optional[dict] = None,
        orb_colors: Optional[List[str]] = None,
        heading_font: str = "WDXL Lubrifont TC",
        body_font: str = "Space Mono",
        heading_color: Optional[str] = None,
        body_color: Optional[str] = None,
        card_width: int = 700,
        card_min_height: int = 420,
        grain_opacity: float = 0.28,
        frost_duration: int = 1800,
        shatter_duration: int = 1100,
    ):
        self.title            = title
        self.bg_color         = bg_color
        self.gradient         = gradient
        self.orb_colors       = orb_colors or list(self.DEFAULT_ORBS)
        self.heading_font     = heading_font
        self.body_font        = body_font
        self.heading_color    = heading_color   # None = auto from bg luminance
        self.body_color       = body_color      # None = auto from bg luminance
        self.card_width       = card_width
        self.card_min_height  = card_min_height
        self.grain_opacity    = grain_opacity
        self.frost_duration   = frost_duration
        self.shatter_duration = shatter_duration
        self._slides: List[Slide] = []

    # ── .frppt serialisation ─────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialise the whole presentation to a plain JSON-safe dict."""
        return {
            "frppt_version": FRPPT_VERSION,
            "meta": {
                "title":            self.title,
                "bg_color":         self.bg_color,
                "gradient":         self.gradient,
                "orb_colors":       self.orb_colors,
                "heading_font":     self.heading_font,
                "body_font":        self.body_font,
                "heading_color":    self.heading_color,
                "body_color":       self.body_color,
                "card_width":       self.card_width,
                "card_min_height":  self.card_min_height,
                "grain_opacity":    self.grain_opacity,
                "frost_duration":   self.frost_duration,
                "shatter_duration": self.shatter_duration,
            },
            "slides": [s._data for s in self._slides],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Presentation":
        """Reconstruct a Presentation from a dict produced by to_dict()."""
        meta = d.get("meta", {})
        prs  = cls(
            title            = meta.get("title",            "Presentation"),
            bg_color         = meta.get("bg_color",         "#1a1428"),
            gradient         = meta.get("gradient",         None),
            orb_colors       = meta.get("orb_colors",       None),
            heading_font     = meta.get("heading_font",     "WDXL Lubrifont TC"),
            body_font        = meta.get("body_font",        "Space Mono"),
            heading_color    = meta.get("heading_color",    None),
            body_color       = meta.get("body_color",       None),
            card_width       = meta.get("card_width",       700),
            card_min_height  = meta.get("card_min_height",  420),
            grain_opacity    = meta.get("grain_opacity",    0.28),
            frost_duration   = meta.get("frost_duration",   1800),
            shatter_duration = meta.get("shatter_duration", 1100),
        )
        for slide_data in d.get("slides", []):
            prs._slides.append(Slide._from_data(slide_data))
        return prs

    def save_frppt(self, path: str) -> None:
        """Save as a .frppt JSON project file."""
        Path(path).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    @classmethod
    def load_frppt(cls, path: str) -> "Presentation":
        """Load a .frppt JSON project file and return a Presentation."""
        raw = Path(path).read_text(encoding="utf-8")
        return cls.from_dict(json.loads(raw))

    @classmethod
    def decompile_html(cls, path: str) -> "Presentation":
        """
        Recover a Presentation from a FrostPPT-generated HTML file.
        The HTML embeds source JSON in a <meta name="frppt-source"> tag.
        Raises ValueError if the file was not made by FrostPPT v6+.
        """
        import re
        html_text = Path(path).read_text(encoding="utf-8")
        m = re.search(r'<meta\s+name="frppt-source"\s+content="([^"]+)"', html_text)
        if m:
            raw = base64.b64decode(m.group(1)).decode("utf-8")
            return cls.from_dict(json.loads(raw))
        raise ValueError(
            "No FrostPPT source data found in this HTML file.\n"
            "Only HTML files generated by FrostPPT v6+ can be decompiled."
        )

    # ── Luminance helper ──────────────────────────────────────────────────────

    @staticmethod
    def _luminance(hex_color: str) -> float:
        """Perceived relative luminance 0–1 of a hex color (ignores alpha)."""
        h = hex_color.lstrip('#')[:6]
        if len(h) < 6:
            return 0.5
        r, g, b = int(h[0:2], 16)/255, int(h[2:4], 16)/255, int(h[4:6], 16)/255
        def lin(c): return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4
        return 0.2126*lin(r) + 0.7152*lin(g) + 0.0722*lin(b)

    def _palette(self) -> dict:
        """Return the correct text color palette for the current background."""
        # The frosted glass card adds a white overlay (~0.11 alpha) + backdrop blur.
        # This lightens the effective card surface significantly even on dark bgs.
        # We therefore treat the *card surface* luminance, not the raw bg.
        # Card surface ≈ bg blended with white at 0.22 (backdrop + card fill).
        bg_lum = self._luminance(self.bg_color)
        # Blend: card_lum ≈ bg_lum*0.78 + 1.0*0.22
        card_lum = bg_lum * 0.78 + 0.22
        return self._PALETTE["light" if card_lum >= 0.35 else "dark"]

    def add(self, slide: Slide) -> "Presentation":
        self._slides.append(slide)
        return self

    def save(self, path: str) -> None:
        Path(path).write_text(self._render(), encoding="utf-8")

    def to_html(self) -> str:
        return self._render()

    # ─────────────────────────────────────────────────────────────────────────
    # Rendering
    # ─────────────────────────────────────────────────────────────────────────

    def _render(self) -> str:
        total       = len(self._slides)
        slides_html = self._render_slides(total)
        gfont       = self._gfont_link()
        # Embed the full project JSON as base64 in a meta tag so the HTML
        # can be decompiled back to .frppt at any time.
        _src_b64 = base64.b64encode(
            json.dumps(self.to_dict(), ensure_ascii=False).encode("utf-8")
        ).decode("ascii")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- Made with FrostPPT — https://github.com/frostppt -->
<meta name="frppt-source" content="{_src_b64}">
<title>{_e(self.title)}</title>
{gfont}
{self._css()}
</head>
<body>

<!-- ── Start screen ─────────────────────────────────────────────────── -->
<div id="start-screen">
  {self._bg_html()}
  <div class="start-card">
    <div class="start-title">{_e(self.title)}</div>
    <div class="start-sub">{total} slide{"s" if total != 1 else ""}</div>
    <button id="start-btn">Present</button>
  </div>
</div>

<!-- ── Main (hidden until Present clicked) ──────────────────────────── -->
<div id="main" style="display:none">
  {self._bg_html()}
  <div class="scene">
    <div id="card-border"></div>
    <div id="glow-ring"></div>
    <div class="glass-card" id="card">
      <canvas id="grain-canvas"></canvas>
      <div id="frost-mask"></div>
{slides_html}
    </div>
  </div>
  <canvas id="shatter-canvas"></canvas>
  <!-- HUD: only visible when mouse is in bottom-left corner -->
  <div id="hud">
    <button class="nav-btn" id="prev-btn">&#8592;</button>
    <div class="nav-dots" id="dots"></div>
    <button class="nav-btn" id="next-btn">&#8594;</button>
    <div id="slide-counter">01 / {total:02d}</div>
  </div>
</div>

{self._js(total)}
</body>
</html>"""

    def _bg_html(self) -> str:
        orbs = "".join(f'<div class="orb orb{i+1}"></div>' for i in range(len(self.orb_colors)))
        return f'<div class="bg"></div>{orbs}'

    def _render_slides(self, total: int) -> str:
        out = []
        for i, slide in enumerate(self._slides):
            active = " active" if i == 0 else ""
            out.append(
                f'    <div class="slide{active}" id="slide-{i}">\n'
                f'{textwrap.indent(slide.html, "      ")}\n'
                f'    </div>'
            )
        return "\n".join(out)

    def _gfont_link(self) -> str:
        WEB_SAFE = {
            'georgia','times new roman','times','palatino','garamond','bookman',
            'arial','helvetica','helvetica neue','verdana','tahoma','trebuchet ms',
            'calibri','gill sans','optima','futura','courier new','courier',
            'lucida console','monaco','impact','arial black','comic sans ms',
        }
        to_load = []
        for f in (self.heading_font, self.body_font):
            if f.lower().strip() not in WEB_SAFE and f not in to_load:
                to_load.append(f)
        if not to_load:
            return ""
        families = "&family=".join(
            f.replace(" ", "+") + ":wght@300;400;500;600;700"
            for f in to_load)
        url = f"https://fonts.googleapis.com/css2?family={families}&display=swap"
        return (
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            f'<link href="{url}" rel="stylesheet">'
        )

    def _bg_css(self) -> str:
        """Generate .bg CSS including animated gradient if configured."""
        base = f"background-color: {self.bg_color};"
        if not self.gradient:
            return f"""  .bg {{
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    {base}
  }}"""

        gtype  = self.gradient.get("type", "radial")
        colors = self.gradient.get("colors", [self.bg_color, "#2a1a50"])
        dur    = self.gradient.get("duration", 8)

        # Build 3 keyframe stops by cycling/shifting colors for smooth loop
        def grad(shift: int) -> str:
            n = len(colors)
            shifted = [colors[(i + shift) % n] for i in range(n)]
            stops = ", ".join(shifted)
            if gtype == "radial":
                return f"radial-gradient(ellipse at center, {stops})"
            elif gtype == "linear-horizontal":
                return f"linear-gradient(90deg, {stops})"
            elif gtype == "linear-vertical":
                return f"linear-gradient(180deg, {stops})"
            else:  # diagonal
                return f"linear-gradient(135deg, {stops})"

        return f"""  .bg {{
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background: {grad(0)};
    background-size: 300% 300%;
    animation: bgshift {dur}s ease infinite;
  }}
  @keyframes bgshift {{
    0%   {{ background: {grad(0)}; background-size: 300% 300%; background-position: 0% 50%; }}
    50%  {{ background: {grad(len(colors)//2)}; background-size: 300% 300%; background-position: 100% 50%; }}
    100% {{ background: {grad(0)}; background-size: 300% 300%; background-position: 0% 50%; }}
  }}"""

    def _orb_css(self) -> str:
        orbs = self.orb_colors
        n    = len(orbs)
        sizes   = [380, 320, 280, 350, 300, 260, 340][:n]
        tops    = [10,  60,  30,  70,  20,  50,  40 ][:n]
        lefts   = [15,  70,  60,  10,  40,  80,  30 ][:n]
        durs    = [22,  28,  18,  24,  20,  26,  16 ][:n]
        delays  = [0,  -9,  -5, -13,  -3,  -7, -11 ][:n]

        drift_keys = [
            "0%{transform:translate(0,0)}25%{transform:translate(18vw,-15vh)}50%{transform:translate(35vw,10vh)}75%{transform:translate(-10vw,25vh)}100%{transform:translate(0,0)}",
            "0%{transform:translate(0,0)}20%{transform:translate(-28vw,12vh)}40%{transform:translate(-12vw,-22vh)}60%{transform:translate(22vw,-20vh)}80%{transform:translate(30vw,8vh)}100%{transform:translate(0,0)}",
            "0%{transform:translate(0,0)}33%{transform:translate(22vw,20vh)}66%{transform:translate(-25vw,28vh)}100%{transform:translate(0,0)}",
            "0%{transform:translate(0,0)}25%{transform:translate(38vw,-10vh)}50%{transform:translate(15vw,30vh)}75%{transform:translate(-20vw,-5vh)}100%{transform:translate(0,0)}",
            "0%{transform:translate(0,0)}50%{transform:translate(-30vw,-20vh)}100%{transform:translate(0,0)}",
            "0%{transform:translate(0,0)}33%{transform:translate(25vw,15vh)}66%{transform:translate(-15vw,-25vh)}100%{transform:translate(0,0)}",
            "0%{transform:translate(0,0)}50%{transform:translate(20vw,-30vh)}100%{transform:translate(0,0)}",
        ]

        lines = ["  .orb { position: fixed; border-radius: 50%; filter: blur(70px); pointer-events: none; z-index: 1; }"]
        for i in range(n):
            sz  = sizes[i]
            d   = delays[i]
            lines.append(
                f"  .orb{i+1} {{ width:{sz}px;height:{sz}px;background:{orbs[i]};"
                f"top:{tops[i]}%;left:{lefts[i]}%;"
                f"animation:drift{i+1} {durs[i]}s ease-in-out infinite;animation-delay:{d}s; }}"
            )
        for i in range(n):
            lines.append(f"  @keyframes drift{i+1} {{ {drift_keys[i % len(drift_keys)]} }}")
        return "\n".join(lines)

    def _css(self) -> str:
        hf = self.heading_font
        bf = self.body_font
        p  = self._palette()

        # Allow user overrides on top of palette
        h1_c   = self.heading_color or p["h1"]
        h2_c   = self.heading_color or p["h2"]
        body_c = self.body_color    or p["p"]

        return f"""<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}

  html, body {{
    width:100%; height:100%; overflow:hidden;
    background:{self.bg_color};
    font-family:'{hf}', serif;
    user-select:none;
  }}

{self._bg_css()}

{self._orb_css()}

  /* ── Layout ── */
  #start-screen, #main {{
    position:fixed; inset:0;
    display:flex; align-items:center; justify-content:center;
    z-index:10;
  }}

  .scene {{ position:relative; z-index:10; }}

  /* ── Card border ── */
  #card-border {{
    position:absolute;
    border-radius:28px;
    pointer-events:none;
    z-index:20;
    border: 2px solid rgba(255,255,255,0.18);
    transition: border-color 0.15s ease;
  }}

  #glow-ring {{
    position:absolute; inset:0; border-radius:28px;
    pointer-events:none; z-index:19;
  }}

  /* ── Glass card ── height set by JS to tallest slide ── */
  .glass-card {{
    position:relative;
    width:{self.card_width}px;
    min-height:{self.card_min_height}px;
    padding:0;
    border-radius:28px;
    background:rgba(255,255,255,0.11);
    backdrop-filter:blur(22px) saturate(1.3);
    -webkit-backdrop-filter:blur(22px) saturate(1.3);
    box-shadow:0 16px 48px rgba(0,0,0,0.35);
    overflow:hidden;
    z-index:1;
  }}

  #grain-canvas {{
    position:absolute; inset:0; width:100%; height:100%;
    border-radius:inherit; pointer-events:none;
    z-index:2; opacity:{self.grain_opacity}; mix-blend-mode:screen;
  }}

  #frost-mask {{
    position:absolute; inset:0; border-radius:inherit;
    pointer-events:none; z-index:3;
  }}

  /* ── Slides — absolutely fill the card, NO overflow/scrollbar ── */
  .slide {{
    position:absolute; inset:0; z-index:10;
    display:none; opacity:1;
    padding:56px 64px; box-sizing:border-box;
    overflow:hidden;
  }}
  .slide.active {{ display:block; }}

  /* ── Typography ── */
  .slide-label {{
    font-size:10px; letter-spacing:0.28em; text-transform:uppercase;
    color:{p["label"]}; margin-bottom:10px;
    font-family:'{bf}', monospace;
  }}

  h1 {{
    font-size:42px; font-weight:400; color:{h1_c};
    line-height:1.2; margin-bottom:18px; letter-spacing:-0.03em;
    font-family:'{hf}', serif;
  }}
  h2 {{
    font-size:28px; font-weight:400; color:{h2_c};
    line-height:1.3; margin-bottom:20px; letter-spacing:-0.02em;
    font-family:'{hf}', serif;
  }}
  p {{
    font-size:14px; line-height:1.85; color:{body_c};
    margin-bottom:16px; font-family:'{bf}', monospace;
    font-weight:400; max-width:520px;
  }}
  .divider {{ width:40px; height:1px; background:{p["divider"]}; margin-bottom:24px; }}
  .tagline {{
    font-size:17px; font-style:italic; color:{p["tagline"]};
    font-family:'{hf}', serif; margin-bottom:8px;
  }}
  .big-quote {{
    font-size:24px; font-style:italic; font-weight:300;
    color:{p["quote"]}; line-height:1.5;
    border:none; margin:24px 0; max-width:540px;
    font-family:'{hf}', serif;
  }}
  .attribution {{
    font-size:12px; color:{p["attribution"]};
    font-family:'{bf}', monospace; margin-top:8px;
  }}

  .stat-row {{ display:flex; gap:40px; margin:20px 0; }}
  .stat {{ display:flex; flex-direction:column; }}
  .stat-num {{
    font-size:40px; font-weight:300; color:{p["stat_num"]};
    letter-spacing:-0.03em; line-height:1; font-family:'{hf}', serif;
  }}
  .stat-label {{
    font-size:11px; letter-spacing:0.12em; text-transform:uppercase;
    color:{p["stat_label"]}; font-family:'{bf}', monospace; margin-top:6px;
  }}

  .pill-row {{ display:flex; flex-wrap:wrap; gap:10px; margin:14px 0; }}
  .pill {{
    padding:6px 16px; border-radius:100px;
    background:{p["pill_bg"]};
    border:1px solid {p["pill_border"]};
    font-size:11px; letter-spacing:0.08em;
    color:{p["pill_text"]}; font-family:'{bf}', monospace;
  }}

  .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:28px; margin-top:8px; }}
  .col-item {{ display:flex; flex-direction:column; gap:6px; }}
  .col-title {{
    font-size:11px; font-weight:500; letter-spacing:0.08em;
    color:{p["col_title"]}; font-family:'{bf}', monospace; text-transform:uppercase;
  }}
  .col-body {{
    font-size:12px; line-height:1.7; color:{p["col_body"]};
    font-family:'{bf}', monospace; font-weight:400;
  }}

  /* ── Media ── */
  .media-wrap {{
    width:100%; margin:12px 0; border-radius:12px; overflow:hidden;
    max-height:260px; display:flex; align-items:center; justify-content:center;
  }}
  .slide-img {{
    width:100%; max-height:260px;
    object-fit:contain; border-radius:12px; display:block;
  }}
  .slide-video {{
    width:100%; max-height:260px; border-radius:12px; display:block; background:#000;
  }}
  .audio-wrap {{
    flex-direction:column; gap:12px; padding:24px;
    background:{p["pill_bg"]};
    border:1px solid {p["pill_border"]}; border-radius:12px;
  }}
  .audio-icon {{ font-size:32px; color:{p["attribution"]}; }}
  .slide-audio {{ width:100%; }}
  .media-caption {{
    font-size:11px !important; color:{p["attribution"]} !important;
    margin-top:4px !important; font-style:italic;
  }}

  /* ── HUD ── */
  #hud {{
    position:fixed; bottom:0; left:0;
    width:220px; height:80px;
    display:flex; align-items:center;
    padding:0 20px; gap:14px;
    z-index:500;
    opacity:0;
    transition:opacity 0.3s ease;
    pointer-events:none;
  }}
  #hud.visible {{ opacity:1; pointer-events:all; }}
  .nav-btn {{
    width:38px; height:38px; border-radius:50%;
    background:rgba(255,255,255,0.13);
    border:1px solid rgba(255,255,255,0.3);
    color:rgba(255,255,255,0.8);
    font-size:16px; cursor:pointer;
    display:flex; align-items:center; justify-content:center;
    backdrop-filter:blur(10px);
    transition:background 0.2s;
    flex-shrink:0;
  }}
  .nav-btn:hover {{ background:rgba(255,255,255,0.25); }}
  .nav-btn:disabled {{ opacity:0.25; cursor:default; }}
  .nav-dots {{ display:flex; gap:6px; align-items:center; }}
  .dot {{
    width:6px; height:6px; border-radius:50%;
    background:rgba(255,255,255,0.3);
    transition:background 0.3s, transform 0.3s; cursor:pointer;
    flex-shrink:0;
  }}
  .dot.active {{ background:rgba(255,255,255,0.85); transform:scale(1.35); }}
  #slide-counter {{
    font-family:'{bf}', monospace;
    font-size:10px; letter-spacing:0.18em;
    color:rgba(255,255,255,0.45); white-space:nowrap;
  }}

  /* ── Shatter canvas ── */
  #shatter-canvas {{
    position:fixed; inset:0; width:100%; height:100%;
    pointer-events:none; z-index:200; display:none;
  }}

  /* ── Start screen ── */
  .start-card {{
    position:relative; z-index:10;
    display:flex; flex-direction:column; align-items:center; gap:16px;
    text-align:center; padding:56px 72px;
    border-radius:28px;
    background:rgba(255,255,255,0.12);
    backdrop-filter:blur(24px) saturate(1.4);
    -webkit-backdrop-filter:blur(24px) saturate(1.4);
    border:2px solid rgba(255,255,255,0.45);
    box-shadow:0 20px 60px rgba(0,0,0,0.3);
  }}
  .start-title {{
    font-family:'{hf}', serif;
    font-size:38px; font-weight:400;
    color:{h1_c}; letter-spacing:-0.02em; line-height:1.2;
    max-width:480px;
  }}
  .start-sub {{
    font-family:'{bf}', monospace;
    font-size:10px; letter-spacing:0.22em; text-transform:uppercase;
    color:{p["label"]};
  }}
  #start-btn {{
    margin-top:12px; padding:13px 46px; border-radius:100px;
    background:{p["pill_bg"]};
    border:1px solid {p["pill_border"]};
    color:{h2_c};
    font-family:'{bf}', monospace;
    font-size:12px; letter-spacing:0.14em; text-transform:uppercase;
    cursor:pointer;
    transition:background 0.25s, border-color 0.25s, transform 0.15s;
  }}
  #start-btn:hover {{ background:{p["pill_bg"]}; border-color:{p["pill_border"]}; transform:scale(1.03); filter:brightness(1.2); }}
  #start-btn:active {{ transform:scale(0.98); }}
</style>"""

    def _js(self, total: int) -> str:
        cw = self.card_width
        ch = self.card_min_height
        return f"""<script>
  // ── Element refs ──────────────────────────────────────────────────────────
  const card        = document.getElementById('card');
  const cardBorder  = document.getElementById('card-border');
  const grainCvs    = document.getElementById('grain-canvas');
  const frostMask   = document.getElementById('frost-mask');
  const ring        = document.getElementById('glow-ring');
  const shatterCvs  = document.getElementById('shatter-canvas');
  const sCtx        = shatterCvs.getContext('2d');
  const prevBtn     = document.getElementById('prev-btn');
  const nextBtn     = document.getElementById('next-btn');
  const dotsEl      = document.getElementById('dots');
  const slideCounter= document.getElementById('slide-counter');
  const hud         = document.getElementById('hud');
  const SLIDES      = document.querySelectorAll('.slide');
  const TOTAL       = SLIDES.length;
  let current       = 0;
  let transitioning = false;

  // ── Nav dots ─────────────────────────────────────────────────────────────
  SLIDES.forEach((_, i) => {{
    const d = document.createElement('div');
    d.className = 'dot' + (i === 0 ? ' active' : '');
    d.addEventListener('click', () => goTo(i));
    dotsEl.appendChild(d);
  }});

  function updateHUD() {{
    document.querySelectorAll('.dot').forEach((d, i) => d.classList.toggle('active', i === current));
    prevBtn.disabled = current === 0;
    nextBtn.disabled = current === TOTAL - 1;
    const n = String(current + 1).padStart(2,'0');
    const t = String(TOTAL).padStart(2,'0');
    slideCounter.textContent = n + ' / ' + t;
  }}

  // ── HUD: show when mouse within 220×80 bottom-left corner ────────────────
  let hudTimer = null;
  document.addEventListener('mousemove', e => {{
    const inCorner = e.clientX < 220 && e.clientY > window.innerHeight - 80;
    if (inCorner) {{
      hud.classList.add('visible');
      clearTimeout(hudTimer);
      hudTimer = setTimeout(() => hud.classList.remove('visible'), 2000);
    }} else {{
      clearTimeout(hudTimer);
      hud.classList.remove('visible');
    }}
  }});

  // ── Sync card-border size to card ────────────────────────────────────────
  function syncBorder() {{
    const r = card.getBoundingClientRect();
    cardBorder.style.width  = r.width  + 'px';
    cardBorder.style.height = r.height + 'px';
    // position border relative to .scene
    const sceneRect = card.parentElement.getBoundingClientRect();
    cardBorder.style.left = (r.left - sceneRect.left) + 'px';
    cardBorder.style.top  = (r.top  - sceneRect.top)  + 'px';
  }}

  // ── Fit card to tallest slide (no scrollbar, no overflow) ────────────────
  function fitCardToTallestSlide() {{
    // Temporarily make every slide block-rendered but invisible so we can
    // measure its natural scrollHeight. Then set card height to the max.
    const PAD = 56 * 2; // top + bottom padding (56px each)
    let maxH = {self.card_min_height};

    SLIDES.forEach(slide => {{
      // Save original state
      const origDisplay    = slide.style.display;
      const origPosition   = slide.style.position;
      const origVisibility = slide.style.visibility;

      // Make it renderable but invisible, in normal flow
      slide.style.position   = 'relative';
      slide.style.display    = 'block';
      slide.style.visibility = 'hidden';

      const h = slide.scrollHeight;
      if (h > maxH) maxH = h;

      // Restore
      slide.style.display    = origDisplay;
      slide.style.position   = origPosition;
      slide.style.visibility = origVisibility;
    }});

    card.style.height = maxH + 'px';
  }}

  // ── Grain — deferred until #main is visible ───────────────────────────────
  let W, H, grainTile;

  function initGrain() {{
    W = card.offsetWidth || {cw};
    H = card.offsetHeight || {ch};
    if (!W || !H) {{ W = {cw}; H = {ch}; }}
    grainCvs.width = W; grainCvs.height = H;
    const gCtx = grainCvs.getContext('2d');
    const imgData = gCtx.createImageData(W, H);
    const px = imgData.data;
    for (let i = 0; i < px.length; i += 4) {{
      if (Math.random() > 0.44) {{
        const b = 175 + Math.random() * 80;
        px[i]=b; px[i+1]=b; px[i+2]=b+8; px[i+3]=Math.random()*150+40;
      }} else px[i+3] = 0;
    }}
    gCtx.putImageData(imgData, 0, 0);
    for (let n = 0; n < 2500; n++) {{
      const x=Math.random()*W, y=Math.random()*H, r=Math.random()*2+0.2, a=Math.random()*0.13+0.02;
      gCtx.beginPath(); gCtx.arc(x,y,r,0,Math.PI*2);
      gCtx.fillStyle=`rgba(255,255,255,${{a}})`; gCtx.fill();
    }}
    grainTile = document.createElement('canvas');
    grainTile.width = 200; grainTile.height = 200;
    const gtx = grainTile.getContext('2d');
    const gid = gtx.createImageData(200, 200);
    for (let i = 0; i < gid.data.length; i += 4) {{
      if (Math.random() > 0.44) {{
        const b = 175 + Math.random() * 80;
        gid.data[i]=b; gid.data[i+1]=b; gid.data[i+2]=b+8; gid.data[i+3]=Math.random()*180+50;
      }} else gid.data[i+3] = 0;
    }}
    gtx.putImageData(gid, 0, 0);
  }}

  // ── Frost ─────────────────────────────────────────────────────────────────
  let frostStart = null;
  const FROST_DUR = {self.frost_duration};

  function ease(t) {{ return t < 0.5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3)/2; }}

  function animateFrost(ts) {{
    if (!frostStart) frostStart = ts;
    const MAX_R = Math.sqrt((W/2)**2 + (H/2)**2) + 20;
    const t = ease(Math.min((ts - frostStart) / FROST_DUR, 1));
    const r = t * MAX_R;
    const inner = Math.max(0, r - 40);
    const m = `radial-gradient(circle at 50% 50%, white ${{inner}}px, transparent ${{r}}px)`;
    grainCvs.style.maskImage = m;
    grainCvs.style.webkitMaskImage = m;
    frostMask.style.background = `radial-gradient(circle at 50% 50%, rgba(200,230,255,${{(1-t)*0.2}}) 0%, transparent ${{r*0.7}}px)`;
    if (t < 1) requestAnimationFrame(animateFrost);
    else {{
      grainCvs.style.maskImage = 'none';
      grainCvs.style.webkitMaskImage = 'none';
      frostMask.style.background = 'none';
      transitioning = false;
    }}
  }}

  function startFrost() {{
    frostStart = null;
    const z = 'radial-gradient(circle at 50% 50%, white 0px, transparent 0px)';
    grainCvs.style.maskImage = z;
    grainCvs.style.webkitMaskImage = z;
    setTimeout(() => requestAnimationFrame(animateFrost), 300);
  }}

  // ── Shatter ───────────────────────────────────────────────────────────────
  function generateShards() {{
    const shards = [];
    const rect = card.getBoundingClientRect();
    const ox = rect.left, oy = rect.top, cw = rect.width, ch = rect.height;
    const impactX = ox + cw/2, impactY = oy + ch/2;
    const COLS = 14, ROWS = 12;
    const cellW = cw/COLS, cellH = ch/ROWS;
    const verts = [];
    for (let row = 0; row <= ROWS; row++) {{
      verts.push([]);
      for (let col = 0; col <= COLS; col++) {{
        const jx = (col===0||col===COLS) ? 0 : (Math.random()-0.5)*cellW*0.85;
        const jy = (row===0||row===ROWS) ? 0 : (Math.random()-0.5)*cellH*0.85;
        verts[row].push({{ x: ox+col*cellW+jx, y: oy+row*cellH+jy }});
      }}
    }}
    for (let row = 0; row < ROWS; row++) {{
      for (let col = 0; col < COLS; col++) {{
        const tl=verts[row][col], tr=verts[row][col+1];
        const bl=verts[row+1][col], br=verts[row+1][col+1];
        const tris = (col+row)%2===0 ? [[tl,tr,br],[tl,br,bl]] : [[tl,tr,bl],[tr,br,bl]];
        tris.forEach(([a,b,c]) => {{
          const cx=(a.x+b.x+c.x)/3, cy=(a.y+b.y+c.y)/3;
          const dx=cx-impactX, dy=cy-impactY;
          const dist=Math.sqrt(dx*dx+dy*dy)||1;
          const speed=2+Math.random()*3.5;
          shards.push({{
            pts:[{{x:a.x-cx,y:a.y-cy}},{{x:b.x-cx,y:b.y-cy}},{{x:c.x-cx,y:c.y-cy}}],
            // Store original absolute pts for border drawing on first frame
            absPts:[{{x:a.x,y:a.y}},{{x:b.x,y:b.y}},{{x:c.x,y:c.y}}],
            x:cx, y:cy,
            vx:(dx/dist)*speed*(0.5+Math.random()*0.5),
            vy:(dy/dist)*speed*(0.4+Math.random()*0.6)+Math.random(),
            spin:(Math.random()-0.5)*0.18, angle:0, alpha:1,
            grainOffX:(Math.random()-0.5)*160,
            grainOffY:(Math.random()-0.5)*160,
          }});
        }});
      }}
    }}
    return shards;
  }}

  function shatter(onDone) {{
    shatterCvs.width  = window.innerWidth;
    shatterCvs.height = window.innerHeight;
    shatterCvs.style.display = 'block';
    // Hide the static card border — it moves to shards
    cardBorder.style.opacity = '0';
    card.style.transition = 'none';
    card.style.opacity = '0';

    const shards = generateShards();
    const GRAVITY = 0.22, DUR = {self.shatter_duration};
    let t0 = null;

    function draw(ts) {{
      if (!t0) t0 = ts;
      const progress = (ts - t0) / DUR;
      sCtx.clearRect(0, 0, shatterCvs.width, shatterCvs.height);
      let alive = false;

      shards.forEach(s => {{
        s.vy += GRAVITY; s.x += s.vx; s.y += s.vy; s.angle += s.spin;
        s.alpha = Math.max(0, 1 - progress * 1.2);
        if (s.alpha > 0) alive = true;

        sCtx.save();
        sCtx.translate(s.x, s.y);
        sCtx.rotate(s.angle);

        // Clip to shard shape
        sCtx.beginPath();
        s.pts.forEach((p, i) => i===0 ? sCtx.moveTo(p.x,p.y) : sCtx.lineTo(p.x,p.y));
        sCtx.closePath();
        sCtx.clip();

        // Glass fill
        sCtx.globalAlpha = s.alpha * 0.22;
        sCtx.fillStyle = 'rgba(210,228,250,1)';
        sCtx.fill();

        // Grain texture
        sCtx.globalCompositeOperation = 'screen';
        sCtx.globalAlpha = s.alpha * 0.6;
        sCtx.drawImage(grainTile, s.grainOffX-100, s.grainOffY-100, 200, 200);
        sCtx.globalCompositeOperation = 'source-over';

        sCtx.restore();

        // ── Border on each shard — 2px glowing white, drawn OUTSIDE clip ──
        sCtx.save();
        sCtx.translate(s.x, s.y);
        sCtx.rotate(s.angle);
        sCtx.beginPath();
        s.pts.forEach((p, i) => i===0 ? sCtx.moveTo(p.x,p.y) : sCtx.lineTo(p.x,p.y));
        sCtx.closePath();
        // Glow layer
        sCtx.strokeStyle = `rgba(255,255,255,${{s.alpha * 0.4}})`;
        sCtx.lineWidth = 6;
        sCtx.stroke();
        // Crisp 2px border
        sCtx.strokeStyle = `rgba(255,255,255,${{s.alpha * 0.95}})`;
        sCtx.lineWidth = 2;
        sCtx.stroke();
        sCtx.restore();
      }});

      if (alive) {{
        requestAnimationFrame(draw);
      }} else {{
        sCtx.clearRect(0, 0, shatterCvs.width, shatterCvs.height);
        shatterCvs.style.display = 'none';
        onDone();
      }}
    }}
    requestAnimationFrame(draw);
  }}

  // ── Navigation ────────────────────────────────────────────────────────────
  function goTo(index) {{
    if (transitioning || index === current || index < 0 || index >= TOTAL) return;
    transitioning = true;
    shatter(() => {{
      SLIDES[current].classList.remove('active');
      current = index;
      SLIDES[current].classList.add('active');
      updateHUD();
      card.style.transition = 'opacity 0.5s ease';
      card.style.opacity = '1';
      // Restore border
      cardBorder.style.transition = 'opacity 0.5s ease';
      cardBorder.style.opacity = '1';
      startFrost();
    }});
  }}

  prevBtn.addEventListener('click', () => goTo(current - 1));
  nextBtn.addEventListener('click', () => goTo(current + 1));

  document.addEventListener('keydown', e => {{
    if (document.getElementById('start-screen').style.display !== 'none') return;
    if (e.key==='ArrowRight'||e.key==='ArrowDown'||e.key===' ') {{ e.preventDefault(); goTo(current+1); }}
    if (e.key==='ArrowLeft' ||e.key==='ArrowUp')                 {{ e.preventDefault(); goTo(current-1); }}
  }});

  // ── Border opacity reacts to mouse as light source ──────────────────────
  // dx/dy are normalised -1..+1 from card centre.
  // Opacity rises as mouse approaches and brightens toward the nearest face.
  function updateBorderLight(dx, dy) {{
    const dist = Math.sqrt(dx * dx + dy * dy);
    // Base opacity: dim at rest (0.15), bright when mouse is close (up to 0.88)
    // clamp dist: mouse outside card can go > 1, cap at 1.4
    const d = Math.min(dist, 1.4);
    const opacity = 0.15 + (1 - d / 1.4) * 0.73;
    cardBorder.style.borderColor = `rgba(255,255,255,${{opacity.toFixed(3)}})`;
    cardBorder.style.boxShadow = 'none';
  }}

  document.addEventListener('mousemove', e => {{
    if (!W) return;
    const r = card.getBoundingClientRect();
    const dx = (e.clientX - (r.left + r.width/2))  / (r.width/2);
    const dy = (e.clientY - (r.top  + r.height/2)) / (r.height/2);
    updateBorderLight(dx, dy);
  }});
  document.addEventListener('mouseleave', () => updateBorderLight(2, 2));

  // ── Start + fullscreen ────────────────────────────────────────────────────
  const startScreen = document.getElementById('start-screen');
  const mainEl      = document.getElementById('main');
  const startBtn    = document.getElementById('start-btn');

  function enterFullscreen() {{
    const el = document.documentElement;
    try {{
      if      (el.requestFullscreen)       el.requestFullscreen();
      else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();
      else if (el.mozRequestFullScreen)    el.mozRequestFullScreen();
      else if (el.msRequestFullscreen)     el.msRequestFullscreen();
    }} catch(e) {{ /* fullscreen blocked — continue anyway */ }}
  }}

  startBtn.addEventListener('click', () => {{
    startScreen.style.transition = 'opacity 0.5s ease';
    startScreen.style.opacity    = '0';
    enterFullscreen();
    setTimeout(() => {{
      startScreen.style.display = 'none';
      mainEl.style.display      = 'flex';
      mainEl.style.alignItems   = 'center';
      mainEl.style.justifyContent = 'center';
      mainEl.style.minHeight    = '100vh';
      // Grain needs real dimensions — wait one frame for layout
      requestAnimationFrame(() => {{
        fitCardToTallestSlide();
        initGrain();
        syncBorder();
        updateHUD();
        const z = 'radial-gradient(circle at 50% 50%, white 0px, transparent 0px)';
        grainCvs.style.maskImage = z;
        grainCvs.style.webkitMaskImage = z;
        setTimeout(() => requestAnimationFrame(animateFrost), 400);
      }});
    }}, 500);
  }});

  document.addEventListener('keydown', e => {{
    if (startScreen.style.display !== 'none' && (e.key==='Enter'||e.key===' ')) {{
      e.preventDefault(); startBtn.click();
    }}
  }});

  window.addEventListener('resize', () => {{ if (W) syncBorder(); }});
</script>"""


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _e(text: str) -> str:
    return html_mod.escape(str(text))


# ─────────────────────────────────────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    prs = Presentation(
        title="FrostPPT — Demo Deck",
        gradient={"type": "linear-diagonal", "colors": ["#1a1428", "#0d1f3c", "#1a2840", "#1a1428"], "duration": 10},
        orb_colors=["#c084fc99", "#67e8f999", "#a3e63599", "#818cf899"],
    )

    prs.add(Slide.title(
        label="Introduction",
        heading="FrostPPT",
        tagline='"The first frosted glass presentation engine."',
        body="Shatter transitions · organic grain · physics rim glow · all pure Python.",
        pills=["Frosted Glass", "Shatter UI", "HTML Export"],
    ))
    prs.add(Slide.content(
        label="Why",
        heading="Why Frosted Glass?",
        body=[
            "Apple uses Liquid Glass. Microsoft uses Acrylic. Both blur-and-tint — smooth, textureless.",
            "Frosted glass is different: organic grain, rim glow from real scatter, shatter as navigation.",
        ],
        stats=[("0.28", "grain opacity"), ("1800ms", "frost spread"), ("∞", "slides")],
    ))
    prs.add(Slide.two_col(
        label="Features",
        heading="What's Inside",
        columns=[
            ("Organic Grain", "Canvas acid-etched texture, static, drawn once."),
            ("Edge Rim Glow", "Mouse is the light source. Edges scatter warm glow."),
            ("Shatter Exit",  "Triangular mesh shards, physics + per-shard border."),
            ("Frost Entry",   "Grain crystallises from centre over live text."),
        ],
    ))
    prs.add(Slide.quote(
        label="Vision",
        quote="Glass that breaks to navigate.\nGlass that crystallises to appear.\nMaterial and interaction — one language.",
        attribution="FrostPPT",
    ))

    out = "frostppt_demo.html"
    prs.save(out)
    print(f"✓ Saved {out}  ({len(prs._slides)} slides)")
