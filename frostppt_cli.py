"""
frostppt_cli.py  —  Interactive Frosted Glass Presentation Builder
══════════════════════════════════════════════════════════════════
  python frostppt_cli.py
Requires frostppt.py in the same directory.
"""

import os, sys, shutil, time, json, signal, atexit
from pathlib import Path
try:
    from .frostppt import Presentation, Slide  # installed as package
except ImportError:
    from frostppt import Presentation, Slide   # running as standalone script


# ══════════════════════════════════════════════════════════════════════════════
#  TERMINAL COLOUR ENGINE
# ══════════════════════════════════════════════════════════════════════════════

R    = "\033[0m"
BOLD = "\033[1m"
DIM  = "\033[2m"
ITAL = "\033[3m"
UND  = "\033[4m"

WHT  = "\033[97m";  GRY  = "\033[90m"
RED  = "\033[91m";  GRN  = "\033[92m";  YLW  = "\033[93m"
BLU  = "\033[94m";  PUR  = "\033[95m";  CYAN = "\033[96m"

def c256(n):    return f"\033[38;5;{n}m"
def bg256(n):   return f"\033[48;5;{n}m"

LAVEN  = c256(147);  SLATE  = c256(244);  TEAL   = c256(80)
MINT   = c256(121);  SAGE   = c256(150);  STEEL  = c256(111)
PEACH  = c256(216);  GOLD   = c256(220);  CORAL  = c256(203)
ROSE   = c256(211);  ORG    = c256(208);  LILAC  = c256(183)
SKY    = c256(117);  PLUM   = c256(135);  EMBER  = c256(202)
LIME   = c256(154);  ICE    = c256(195);  CREAM  = c256(230)
WINE   = c256(161);  INDIGO = c256(99)

def rgb(r,g,b):  return f"\033[38;2;{r};{g};{b}m"
def bgc(r,g,b):  return f"\033[48;2;{r};{g};{b}m"

def grad_text(text, r1,g1,b1, r2,g2,b2):
    n = max(len(text)-1, 1)
    out = ""
    for i, ch in enumerate(text):
        t  = i / n
        rr = int(r1+(r2-r1)*t); gg = int(g1+(g2-g1)*t); bb = int(b1+(b2-b1)*t)
        out += rgb(rr,gg,bb) + ch
    return out + R

def clr(t, *codes): return "".join(codes) + str(t) + R

TW = min(shutil.get_terminal_size((72,24)).columns, 76)


# ══════════════════════════════════════════════════════════════════════════════
#  UI PRIMITIVES
# ══════════════════════════════════════════════════════════════════════════════

def banner():
    os.system("clear" if os.name != "nt" else "cls")
    w  = TW
    C1 = (130, 80, 255);  C2 = (60, 210, 240);  C3 = (80, 255, 180)

    top = grad_text("╔"+"═"*(w-2)+"╗", *C1, *C2)
    bot = grad_text("╚"+"═"*(w-2)+"╝", *C2, *C1)
    mid = grad_text("║"+" "*(w-2)+"║", *C1, *C2)
    div = grad_text("╠"+"═"*(w-2)+"╣", *C2, *C3)

    def cline(text, tc=WHT, bold=False, c1=C1, c2=C2):
        pad   = max(0, w-2-len(text))
        inner = clr(text, tc, BOLD if bold else "")
        return grad_text("║",*c1,*c2) + inner + " "*pad + grad_text("║",*c2,*c1)

    title   = "  ❄  FROSTPPT"
    t_inner = grad_text(title, 200,140,255, 80,230,255)
    t_rpad  = max(0, w-2-len(title))
    t_line  = grad_text("║",*C1,*C2) + t_inner + " "*t_rpad + grad_text("║",*C2,*C1)

    print()
    print(top); print(mid)
    print(t_line)
    print(cline("  Frosted Glass Presentation Builder", SLATE, False, C2, C3))
    print(div)
    print(cline("  ⌨  Arrows / Space to navigate  ·  Esc exit fullscreen",   SLATE))
    print(cline("  🖱  Hover bottom-left for nav HUD  ·  move mouse → border glows", SLATE))
    print(cline("  ✦  Card auto-sizes to tallest slide  ·  no scrollbars ever",SLATE))
    print(mid); print(bot); print()


def header(title, c1=(130,80,255), c2=(60,210,240)):
    w   = TW
    top = grad_text("┌"+"─"*(w-2)+"┐", *c1, *c2)
    bot = grad_text("└"+"─"*(w-2)+"┘", *c2, *c1)
    inner = f"  {title}"
    pad   = max(0, w-2-len(inner))
    print()
    print(top)
    print(grad_text("│",*c1,*c2) + clr(inner,WHT,BOLD) + " "*pad + grad_text("│",*c2,*c1))
    print(bot)


def section(title, icon="◆", color=LAVEN):
    print()
    line = f"  {icon}  {title}"
    print(clr(line, color, BOLD))
    print(clr("  "+"╌"*min(len(line), TW-3), SLATE))


def rule(c1=(100,80,200), c2=(60,180,200)):
    print(grad_text("─"*TW, *c1, *c2))


def info(t, icon="·"):
    print(f"  {clr(icon,SLATE)}  {clr(t,SLATE)}")


def tip(t):
    print(f"  {clr('💡',GOLD)}  {clr(t,GOLD,DIM)}")


def success(t):
    print(f"\n  {clr('✓',GRN,BOLD)}  {clr(t,MINT)}")


def warn(t):
    print(f"\n  {clr('⚠',YLW,BOLD)}  {clr(t,YLW)}")


def error(t):
    print(f"  {clr('✗',RED,BOLD)}  {clr(t,CORAL)}")


def tag(label, value, lc=LAVEN, vc=TEAL):
    print(f"  {clr(label+':',lc)}  {clr(str(value),vc,BOLD)}")


def tag_row(**kv):
    parts = [f"{clr(k+':',SLATE)}  {clr(str(v),TEAL,BOLD)}" for k,v in kv.items()]
    print("  " + "   ".join(parts))


def ask(prompt, default="", color=CYAN):
    hint  = clr(f" [{default}]",SLATE) if default else ""
    arrow = clr("›",color,BOLD)
    raw   = input(f"\n  {arrow}  {clr(prompt,WHT)}{hint}\n  {clr('  ',DIM)}").strip()
    return raw if raw else default


def ask_inline(prompt, default="", color=TEAL):
    hint  = clr(f" [{default}]",SLATE) if default else ""
    arrow = clr("›",color,BOLD)
    raw   = input(f"  {arrow} {clr(prompt,WHT)}{hint}: ").strip()
    return raw if raw else default


def ask_multi(prompt, color=LAVEN):
    print()
    print(f"  {clr('❯',color,BOLD)}  {clr(prompt,WHT)}")
    info("one item per line  ·  empty line to finish")
    items, idx = [], 1
    while True:
        line = input(f"  {clr(str(idx)+'.',TEAL,BOLD)}  ").strip()
        if not line: break
        items.append(line); idx += 1
    return items


def confirm(prompt, default=True, color=CYAN):
    hint  = clr("[Y/n]" if default else "[y/N]",SLATE)
    arrow = clr("›",color,BOLD)
    raw   = input(f"  {arrow}  {clr(prompt,WHT)} {hint}: ").strip().lower()
    return default if not raw else raw in ("y","yes")


def menu(prompt, options, default=None, colors=None, descs=None):
    _CYC = [CYAN,TEAL,MINT,SAGE,STEEL,LAVEN,PEACH,GOLD,CORAL,ROSE,
            ORG,BLU,YLW,GRN,PUR,LILAC,SKY,PLUM,EMBER,LIME]
    print()
    print(f"  {clr('❯',LAVEN,BOLD)}  {clr(prompt,WHT,BOLD)}")
    rule((100,80,200),(60,180,200))
    for i,o in enumerate(options,1):
        num   = clr(f"{i:2d}.",SLATE)
        oc    = colors[i-1] if (colors and i-1<len(colors)) else _CYC[(i-1)%len(_CYC)]
        is_d  = (o==default)
        label = clr(o,oc,BOLD) if is_d else clr(o,oc)
        dflag = clr("  ✦ default",GOLD,ITAL) if is_d else ""
        desc  = clr(f"  — {descs[i-1]}",SLATE,ITAL) if (descs and i-1<len(descs)) else ""
        print(f"  {num}  {label}{dflag}{desc}")
    rule((60,180,200),(100,80,200))
    while True:
        raw = input(f"  {clr('›',LAVEN,BOLD)} ").strip()
        if not raw and default: return default
        if raw.isdigit() and 1<=int(raw)<=len(options): return options[int(raw)-1]
        error(f"Enter 1–{len(options)}")


def progress_bar(label, step, total, width=30):
    filled  = int(width * step / max(total,1))
    bar     = grad_text("█"*filled, 100,180,255, 80,240,200)
    empty   = clr("░"*(width-filled), SLATE)
    pct     = clr(f" {step}/{total}", TEAL, BOLD)
    spin    = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"[step%10]
    print(f"\r  {clr(spin,LAVEN,BOLD)}  {clr(label,SLATE)}  [{bar}{empty}]{pct}   ",
          end="", flush=True)


def show_slide_list(meta):
    ICONS = {"Title":("◈",LAVEN),"Content":("▤",TEAL),"Two Column":("⊞",MINT),
             "Quote":("❝",ROSE), "Media":("⬤",PEACH),"Raw HTML":("⚙",SAGE)}
    BADGE_RGB = {LAVEN:(147,112,219),TEAL:(64,200,180),MINT:(100,210,140),
                 ROSE:(220,120,160),PEACH:(220,160,120),SAGE:(120,180,120),STEEL:(100,150,200)}
    if not meta:
        print(); info("No slides yet — add your first slide below.", "○"); return
    print()
    for i,(kind,title) in enumerate(meta):
        icon,ic  = ICONS.get(kind,("◉",STEEL))
        num      = grad_text(f" {i+1:02d}", 120,100,220, 60,200,220)
        ico      = clr(icon,ic,BOLD)
        ttl      = clr(title[:50],WHT)
        br,bg,bb = BADGE_RGB.get(ic,(100,100,120))
        badge    = f"{bgc(br,bg,bb)}\033[30m {kind} {R}"
        print(f"  {num}  {ico}  {ttl}  {badge}")
    print(); rule()


def success_box(out_file, frppt_out, n_slides):
    w  = TW
    C1 = (60,220,120); C2 = (60,200,255); C3 = (120,255,180)
    top = grad_text("╔"+"═"*(w-2)+"╗",*C1,*C2)
    bot = grad_text("╚"+"═"*(w-2)+"╝",*C2,*C1)
    mid = grad_text("║"+" "*(w-2)+"║",*C1,*C2)
    def line(text,c1=C1,c2=C2):
        pad = max(0,w-2-len(text))
        return grad_text("║",*c1,*c2)+clr(text,WHT,BOLD)+" "*pad+grad_text("║",*c2,*c1)
    print(); print(top); print(mid)
    print(line(f"  ✓  HTML   →  {out_file}"))
    print(line(f"  ✓  Project →  {frppt_out}  (editable / shareable)",C2,C3))
    print(line(f"  {n_slides} slide{'s' if n_slides!=1 else ''}  ·  open HTML in any modern browser",C3,C2))
    print(mid)
    print(line("  CONTROLS:",C1,C2))
    print(line("  ← → or Space       navigate slides"))
    print(line("  Hover bottom-left  show nav HUD (arrows + dots + counter)"))
    print(line("  Move mouse          border opacity reacts to light angle"))
    print(line("  Esc                 exit fullscreen"))
    print(mid)
    print(line("  SHARE & EDIT:",C2,C3))
    print(line(f"  Send {frppt_out!r} to a collaborator"))
    print(line(f"  They open it with:  python frostppt_cli.py --load {frppt_out}"))
    print(line(f"  Decompile the HTML: python frostppt_cli.py --decompile {out_file}"))
    print(mid); print(bot); print()


# ══════════════════════════════════════════════════════════════════════════════
#  BACKGROUND & ORBS
# ══════════════════════════════════════════════════════════════════════════════

# ── 53 named gradient presets + 2 custom = 55 total ─────────────────────────
GRAD_PRESETS = {
    # Dark — Cool
    "Deep Space":          {"type":"linear-diagonal",   "colors":["#1a1428","#0d1f3c","#1a2840"],                     "duration":10},
    "Aurora Borealis":     {"type":"linear-diagonal",   "colors":["#0a0020","#00204a","#004040","#002030"],            "duration":12},
    "Ocean Deep":          {"type":"radial",             "colors":["#000d2e","#001a50","#003060","#001a3e"],            "duration":10},
    "Electric Storm":      {"type":"linear-horizontal", "colors":["#050020","#0a0040","#000830","#050020"],            "duration":6},
    "Midnight Bloom":      {"type":"radial",             "colors":["#0f0020","#1a0035","#200015","#0a0028"],            "duration":14},
    "Abyssal":             {"type":"radial",             "colors":["#000510","#001020","#002030","#000818"],            "duration":16},
    "Northern Lights":     {"type":"linear-diagonal",   "colors":["#001a20","#003830","#004820","#002818"],            "duration":13},
    "Deep Sea Rift":       {"type":"linear-vertical",   "colors":["#000818","#001530","#002040","#000c20"],            "duration":11},
    "Void":                {"type":"radial",             "colors":["#050008","#0a0015","#000008","#08000f"],            "duration":20},
    "Cobalt Night":        {"type":"linear-diagonal",   "colors":["#080030","#100050","#180060","#080040"],            "duration":9},
    "Steel Dusk":          {"type":"linear-horizontal", "colors":["#1a1a2e","#16213e","#0f3460","#1a1a2e"],            "duration":11},
    "Cryogenic":           {"type":"radial",             "colors":["#001828","#002838","#003040","#001020"],            "duration":14},
    # Dark — Warm
    "Sunset Dusk":         {"type":"linear-diagonal",   "colors":["#2d0030","#5c0050","#8b1a00","#3d1a00"],            "duration":8},
    "Rose Gold Dark":      {"type":"linear-diagonal",   "colors":["#3d1020","#5c2030","#3a1a00","#4a2a10"],            "duration":8},
    "Ember Glow":          {"type":"linear-diagonal",   "colors":["#1a0500","#2d0a00","#1a0808","#0d0500"],            "duration":7},
    "Crimson Tide":        {"type":"linear-diagonal",   "colors":["#200000","#380008","#280010","#180000"],            "duration":8},
    "Volcanic":            {"type":"radial",             "colors":["#1a0800","#2d1000","#1a0400","#3a0c00"],            "duration":9},
    "Burnt Sienna":        {"type":"linear-vertical",   "colors":["#1a0a00","#2a1000","#200c00","#180800"],            "duration":10},
    "Blood Moon":          {"type":"radial",             "colors":["#180005","#280010","#200008","#100003"],            "duration":12},
    "Copper Dusk":         {"type":"linear-diagonal",   "colors":["#1a0d00","#2d1800","#1a0a00","#250f00"],            "duration":9},
    "Dark Amber":          {"type":"linear-horizontal", "colors":["#1a0f00","#2a1800","#1a0c00","#220e00"],            "duration":8},
    "Obsidian Flame":      {"type":"linear-diagonal",   "colors":["#0d0000","#200500","#180000","#0a0300"],            "duration":11},
    # Dark — Purple / Violet
    "Violet Abyss":        {"type":"radial",             "colors":["#0d0018","#180030","#100020","#0a0015"],            "duration":13},
    "Cosmic Plum":         {"type":"linear-diagonal",   "colors":["#120015","#220025","#1a001a","#0f0012"],            "duration":11},
    "Grape Night":         {"type":"linear-vertical",   "colors":["#0f0020","#200035","#180028","#0a0018"],            "duration":10},
    "Indigo Dream":        {"type":"linear-diagonal",   "colors":["#080028","#140050","#100040","#060020"],            "duration":12},
    "Purple Haze":         {"type":"linear-horizontal", "colors":["#180020","#28003a","#200030","#100018"],            "duration":9},
    "Nebula":              {"type":"radial",             "colors":["#100018","#200030","#180028","#280020","#100018"], "duration":15},
    # Dark — Green / Teal
    "Forest Night":        {"type":"linear-vertical",   "colors":["#0a1a0a","#0f2a10","#1a3320","#0d2010"],            "duration":9},
    "Sage Dark":           {"type":"linear-vertical",   "colors":["#0a1208","#151e10","#101a0c","#0c1508"],            "duration":11},
    "Swamp":               {"type":"radial",             "colors":["#051008","#0a1a0d","#081408","#040d05"],            "duration":13},
    "Jungle Mist":         {"type":"linear-diagonal",   "colors":["#081510","#101f18","#0c1a14","#061010"],            "duration":10},
    "Deep Teal":           {"type":"radial",             "colors":["#001818","#002828","#002020","#001515"],            "duration":12},
    # Light — Cool
    "Arctic White":        {"type":"radial",             "colors":["#e8f4ff","#d0eaff","#f0f8ff","#ddf0ff"],            "duration":12},
    "Lavender Mist":       {"type":"radial",             "colors":["#f0eaff","#e8e0ff","#f5f0ff","#ece4ff"],            "duration":11},
    "Mint Cream":          {"type":"radial",             "colors":["#f0fff8","#e4fff2","#f5fffa","#eaffF5"],            "duration":12},
    "Sky Canvas":          {"type":"linear-vertical",   "colors":["#e8f4ff","#dceeff","#f0f8ff","#e4f2ff"],            "duration":13},
    "Soft Lilac":          {"type":"radial",             "colors":["#f5f0ff","#ede8ff","#f8f4ff","#eae0ff"],            "duration":11},
    "Morning Dew":         {"type":"linear-diagonal",   "colors":["#f0fff0","#e8f8ee","#f5fff5","#ecfaec"],            "duration":12},
    "Pearl":               {"type":"radial",             "colors":["#fffff8","#f8f8f0","#fffff8","#f5f5ee"],            "duration":15},
    "Seafoam":             {"type":"linear-horizontal", "colors":["#f0fffe","#e4fffc","#f5ffff","#e8fffd"],            "duration":11},
    "Cloud Nine":          {"type":"radial",             "colors":["#f5f8ff","#eef4ff","#f8faff","#edf2ff"],            "duration":13},
    "Baby Blue":           {"type":"radial",             "colors":["#eef6ff","#e4f0ff","#f0f8ff","#e8f2ff"],            "duration":12},
    "Lemon Sorbet":        {"type":"linear-diagonal",   "colors":["#fffff0","#fffde0","#fffff5","#fffbe5"],            "duration":10},
    # Light — Warm
    "Warm Parchment":      {"type":"linear-diagonal",   "colors":["#f5f0e8","#ede4d0","#f8f2e4","#ece0cc"],            "duration":10},
    "Rose Quartz":         {"type":"linear-diagonal",   "colors":["#fff0f3","#ffe4ea","#fff5f7","#fce8ee"],            "duration":10},
    "Peach Fizz":          {"type":"linear-diagonal",   "colors":["#fff3e8","#ffe8d0","#fff7f0","#ffeedd"],            "duration":9},
    "Cream Linen":         {"type":"linear-horizontal", "colors":["#faf8f0","#f5f2e8","#fdfaf3","#f8f5ec"],            "duration":14},
    "Blush":               {"type":"linear-diagonal",   "colors":["#fff0f5","#ffe8f0","#fff5f8","#fce8f2"],            "duration":10},
    "Champagne":           {"type":"linear-diagonal",   "colors":["#fff8e8","#f8f0d8","#fffcf0","#f5edd8"],            "duration":12},
    "Golden Hour":         {"type":"linear-diagonal",   "colors":["#fff8e0","#fff0cc","#fffce8","#f8ecd5"],            "duration":9},
    "Cotton Candy":        {"type":"linear-horizontal", "colors":["#fff0f8","#f8e8ff","#fff5ff","#f0e8ff"],            "duration":10},
    "Sunlit Paper":        {"type":"linear-diagonal",   "colors":["#fffde8","#fff8d0","#fffef0","#f8f5d5"],            "duration":11},
    # Custom
    "Custom solid color":  None,
    "Custom gradient":     None,
}

GRAD_DESCS = [
    "dark · deep space",
    "dark · aurora borealis",
    "dark · ocean deep",
    "dark · electric storm",
    "dark · midnight bloom",
    "dark cool · abyssal",
    "dark cool · northern lights",
    "dark cool · deep sea rift",
    "dark cool · void",
    "dark cool · cobalt night",
    "dark cool · steel dusk",
    "dark cool · cryogenic",
    "dark warm · sunset dusk",
    "dark warm · rose gold dark",
    "dark warm · ember glow",
    "dark warm · crimson tide",
    "dark warm · volcanic",
    "dark warm · burnt sienna",
    "dark warm · blood moon",
    "dark warm · copper dusk",
    "dark warm · dark amber",
    "dark warm · obsidian flame",
    "dark purple · violet abyss",
    "dark purple · cosmic plum",
    "dark purple · grape night",
    "dark purple · indigo dream",
    "dark purple · purple haze",
    "dark purple · nebula",
    "dark green · forest night",
    "dark green · sage dark",
    "dark green · swamp",
    "dark green · jungle mist",
    "dark green · deep teal",
    "light · arctic white",
    "light · lavender mist",
    "light · mint cream",
    "light · sky canvas",
    "light · soft lilac",
    "light · morning dew",
    "light · pearl",
    "light · seafoam",
    "light · cloud nine",
    "light · baby blue",
    "light · lemon sorbet",
    "light warm · warm parchment",
    "light warm · rose quartz",
    "light warm · peach fizz",
    "light warm · cream linen",
    "light warm · blush",
    "light warm · champagne",
    "light warm · golden hour",
    "light warm · cotton candy",
    "light warm · sunlit paper",
    "enter custom colors",
    "enter custom colors",
]

GRAD_COLORS = [STEEL,INDIGO,BLU,TEAL,LAVEN,ICE,MINT,BLU,SLATE,INDIGO,STEEL,ICE,PLUM,WINE,EMBER,CORAL,ORG,PEACH,WINE,PEACH,GOLD,EMBER,PLUM,PLUM,INDIGO,INDIGO,ROSE,LAVEN,MINT,SAGE,SAGE,TEAL,TEAL,ICE,LILAC,MINT,SKY,LILAC,MINT,CREAM,ICE,TEAL,SKY,CREAM,ICE,CREAM,ROSE,CREAM,GOLD,ROSE,CREAM,ICE,SLATE,GOLD,STEEL]


ORB_PRESETS = {
    # Pastels & Soft
    "Lavender / Cyan / Lime / Periwinkle":    ["#c084fc88","#67e8f988","#a3e63588","#818cf888"],
    "Rose / Peach / Mint / Sky":              ["#fd79a888","#fab1a088","#55efc488","#74b9ff88"],
    "Blush / Lilac / Ice / Sage":             ["#ffb3c688","#d4a5ff88","#b3e8ff88","#b7e4c788"],
    "Powder Blue / Lavender / Mint / White":  ["#bde0fe88","#c8b6ff88","#b5ead788","#ffffff2a"],
    "Baby Pink / Peach / Yellow / Mint":      ["#ffb3de88","#ffcba488","#fdff8888","#a8ffb888"],
    "Lilac / Sky / Seafoam / Cream":          ["#d8b4fe88","#7dd3fc88","#6ee7b788","#fef3c788"],
    "Soft Gold / Pink / Lavender / Teal":     ["#fde68a88","#fda4af88","#c4b5fd88","#5eead488"],
    "Peach / Rose / Violet / Aqua":           ["#fdba7488","#fb718588","#a78bfa88","#22d3ee88"],
    # Vivid & Saturated
    "Coral / Gold / Teal / Purple":           ["#ff6b6b88","#fdcb6e88","#00cec988","#6c5ce788"],
    "Deep Blue / Indigo / Violet / Cyan":     ["#1e3a8a88","#312e8188","#581c8788","#0e748888"],
    "Sunset — Orange / Red / Pink / Gold":    ["#ff6b0088","#ff003488","#ff006888","#ffaa0088"],
    "Forest — Green / Teal / Lime / Sage":    ["#22c55e88","#14b8a688","#84cc1688","#6b7c5588"],
    "Neon — Pink / Cyan / Green / Purple":    ["#ff00aa88","#00ddff88","#00ff6688","#aa00ff88"],
    "Fire — Red / Orange / Amber / Yellow":   ["#ff000088","#ff6b0088","#ffaa0088","#ffdd0088"],
    "Ocean — Navy / Teal / Cyan / Aqua":      ["#00308888","#00808088","#00bcd488","#00e5ff88"],
    "Jungle — Green / Lime / Teal / Yellow":  ["#16a34a88","#65a30d88","#0d948888","#ca8a0488"],
    "Royal — Purple / Gold / Crimson / Blue": ["#7c3aed88","#d9770688","#be123c88","#1d4ed888"],
    "Candy — Pink / Blue / Yellow / Green":   ["#ec489988","#3b82f688","#eab30888","#22c55e88"],
    "Retro — Orange / Pink / Teal / Yellow":  ["#f9731688","#ec489988","#14b8a688","#eab30888"],
    "Electric — Cyan / Lime / Pink / Blue":   ["#06b6d488","#84cc1688","#f43f5e88","#6366f188"],
    # Moody & Dark-toned
    "Midnight — Navy / Purple / Teal / Blue": ["#1e293b88","#312e8188","#0f766e88","#1e40af88"],
    "Shadow — Charcoal / Plum / Steel / Ink": ["#1f2937aa","#4c1d95aa","#1e3a5faa","#111827aa"],
    "Dusk — Mauve / Slate / Rose / Navy":     ["#9f1239aa","#475569aa","#be185daa","#1e3a8aaa"],
    "Ember Night — Red / Amber / Black / Rust":["#7f1d1d88","#78350f88","#1c1917bb","#92400e88"],
    "Poison — Green / Purple / Black / Lime": ["#14532d88","#4c1d9588","#1c191788","#365314aa"],
    "Vintage — Brown / Olive / Rust / Cream": ["#78350f88","#3f6212aa","#7f1d1d88","#78716c88"],
    "Storm — Grey / Blue / White / Navy":     ["#374151aa","#1e3a8a88","#ffffff22","#1f2937aa"],
    "Void — Black / Charcoal / Dark Purple":  ["#09090bbb","#18181baa","#1c091e99","#030712cc"],
    # Monochromatic
    "Ice — White / Blue / Cyan / Silver":     ["#ffffff22","#88ccff55","#aaddff44","#cceeFF33"],
    "Monochrome White (subtle)":              ["#ffffff18","#ffffff22","#ffffff15","#ffffff1a"],
    "Monochrome Black (subtle)":              ["#00000033","#00000022","#00000044","#0000002a"],
    "All Purple":                             ["#7c3aed88","#a855f788","#6d28d988","#9333ea88"],
    "All Blue":                               ["#1d4ed888","#2563eb88","#1e40af88","#3b82f688"],
    "All Pink":                               ["#db277788","#ec489988","#be185d88","#f43f5e88"],
    "All Green":                              ["#16a34a88","#15803d88","#14532d88","#22c55e88"],
    "All Teal":                               ["#0f766e88","#14b8a688","#0d948888","#2dd4bf88"],
    "All Orange":                             ["#c2410c88","#ea580c88","#f9731688","#fb923c88"],
    # Seasonal & Thematic
    "Spring — Pink / Green / Yellow / Lavender":["#f9a8d488","#86efac88","#fde04788","#c4b5fd88"],
    "Summer — Coral / Aqua / Gold / White":   ["#f8717188","#2dd4bf88","#fbbf2488","#ffffff2a"],
    "Autumn — Orange / Brown / Red / Gold":   ["#f9731688","#92400e88","#b91c1c88","#d9770688"],
    "Winter — Blue / Silver / White / Teal":  ["#3b82f688","#94a3b888","#ffffff2a","#0d948888"],
    "Halloween — Orange / Purple / Black":    ["#ea580c88","#7c3aed88","#1c191788","#b91c1c88"],
    "Christmas — Red / Green / Gold / White": ["#dc262688","#15803d88","#d9770688","#ffffff2a"],
    "Valentine — Red / Pink / Rose / Cream":  ["#dc262688","#ec489988","#f43f5e88","#fce7f388"],
    "Easter — Lavender / Mint / Yellow / Pink":["#a78bfa88","#6ee7b788","#fde04788","#f9a8d488"],
    # Nature-inspired
    "Ocean Sunset":                           ["#0ea5e988","#f9731688","#f59e0b88","#ec489988"],
    "Northern Forest":                        ["#166534aa","#052e16aa","#14532daa","#365314aa"],
    "Desert Sand":                            ["#b45309aa","#92400eaa","#78350faa","#d9770688"],
    "Cherry Blossom":                         ["#fda4af88","#f9a8d488","#fbcfe888","#ffffff2a"],
    "Deep Coral Reef":                        ["#0e7490aa","#155e75aa","#164e6388","#1e3a8a88"],
    "Lava Flow":                              ["#7f1d1d88","#991b1b88","#7c2d1288","#78350f88"],
    "Galaxy":                                 ["#1e1b4baa","#312e8188","#4c1d95aa","#2e1065aa"],
    "Aurora":                                 ["#06402888","#06b6d488","#7c3aed88","#059669aa"],
    "Midnight Sea":                           ["#0c4a6eaa","#1e3a8aaa","#312e8188","#164e63aa"],
    # Custom
    "Custom":                                 None,
}

ORB_COLORS = [LAVEN,ROSE,LILAC,SKY,PEACH,LILAC,GOLD,PEACH,CORAL,BLU,ORG,MINT,PUR,EMBER,BLU,LIME,GOLD,CORAL,ORG,LIME,INDIGO,SLATE,WINE,EMBER,MINT,PEACH,STEEL,SLATE,ICE,SLATE,SLATE,PUR,BLU,ROSE,MINT,TEAL,ORG,ROSE,ORG,MINT,TEAL,EMBER,WINE,ROSE,TEAL,CORAL,WINE,LILAC,TEAL,BLU,EMBER,BLU,MINT,ROSE,SLATE]

# ── 53 named font pairs + 1 custom + 1 system = 55 total ─────────────────────
FONT_PAIRS = [
    # Display / Expressive
    ("WDXL Lubrifont TC / Space Mono",    "WDXL Lubrifont TC",   "Space Mono",           "default · distressed display + monospace"),
    ("Playfair Display / Inter",          "Playfair Display",    "Inter",                "editorial serif + ultra-clean sans"),
    ("Cormorant Garamond / Jost",         "Cormorant Garamond",  "Jost",                 "luxury hairline serif + geometric sans"),
    ("Abril Fatface / Nunito",            "Abril Fatface",       "Nunito",               "bold display + friendly rounded"),
    ("Bebas Neue / Barlow",               "Bebas Neue",          "Barlow",               "condensed impact headers + wide body"),
    ("Righteous / Rubik",                 "Righteous",           "Rubik",                "retro rounded + modern sans"),
    ("Fredoka / Poppins",                 "Fredoka",             "Poppins",              "bubbly rounded + clean geometric"),
    ("Lobster / Raleway",                 "Lobster",             "Raleway",              "script display + elegant thin"),
    ("Boogaloo / Open Sans",              "Boogaloo",            "Open Sans",            "playful cartoon + neutral body"),
    ("Pacifico / Quicksand",              "Pacifico",            "Quicksand",            "casual script + geometric round"),
    ("Alfa Slab One / Roboto",            "Alfa Slab One",       "Roboto",               "heavy slab + system workhorse"),
    ("Teko / Hind",                       "Teko",                "Hind",                 "condensed Indian-influenced pair"),
    ("Black Han Sans / Noto Sans KR",     "Black Han Sans",      "Noto Sans KR",         "bold Korean-influenced display"),
    # Serif Elegant
    ("Bodoni Moda / Montserrat",          "Bodoni Moda",         "Montserrat",           "high-fashion editorial"),
    ("Cinzel / Quattrocento Sans",        "Cinzel",              "Quattrocento Sans",    "classical Roman engraving"),
    ("DM Serif Display / DM Sans",        "DM Serif Display",    "DM Sans",              "balanced Google design system"),
    ("Libre Baskerville / Libre Franklin","Libre Baskerville",   "Libre Franklin",       "newspaper editorial pair"),
    ("Merriweather / Source Sans 3",      "Merriweather",        "Source Sans 3",        "reading-optimised serif + sans"),
    ("Lora / Nunito Sans",                "Lora",                "Nunito Sans",          "warm calligraphic serif + clean"),
    ("EB Garamond / Proza Libre",         "EB Garamond",         "Proza Libre",          "Renaissance humanist pairing"),
    ("Cardo / Josefin Sans",              "Cardo",               "Josefin Sans",         "classical book + geometric thin"),
    ("Spectral / Karla",                  "Spectral",            "Karla",                "screen-optimised serif + grotesque"),
    ("Bitter / Source Code Pro",          "Bitter",              "Source Code Pro",      "slab serif + code mono"),
    ("Neuton / Cabin",                    "Neuton",              "Cabin",                "narrow text serif + humanist sans"),
    # Sans-Serif Clean
    ("Raleway / Lato",                    "Raleway",             "Lato",                 "elegant thin headers + readable body"),
    ("Space Grotesk / Space Grotesk",     "Space Grotesk",       "Space Grotesk",        "techy sci-fi mono-family"),
    ("Outfit / Outfit",                   "Outfit",              "Outfit",               "modern variable single-family"),
    ("Sora / Sora",                       "Sora",                "Sora",                 "Japanese-influenced geometric"),
    ("Oxanium / Exo 2",                   "Oxanium",             "Exo 2",                "futuristic tech / sci-fi"),
    ("Orbitron / Rajdhani",               "Orbitron",            "Rajdhani",             "sci-fi display + angular sans"),
    ("Chakra Petch / IBM Plex Sans",      "Chakra Petch",        "IBM Plex Sans",        "mechanical + corporate clean"),
    ("Urbanist / Plus Jakarta Sans",      "Urbanist",            "Plus Jakarta Sans",    "contemporary startup feel"),
    ("Manrope / Inter",                   "Manrope",             "Inter",                "refined geometric + UI standard"),
    ("Cabinet Grotesk / Satoshi",         "Cabinet Grotesk",     "Satoshi",              "editorial grotesque pair"),
    # Monospace / Code
    ("JetBrains Mono / Fira Sans",        "JetBrains Mono",      "Fira Sans",            "developer mono heading + humanist"),
    ("Fira Code / Fira Sans",             "Fira Code",           "Fira Sans",            "ligature code font + sans body"),
    ("IBM Plex Mono / IBM Plex Sans",     "IBM Plex Mono",       "IBM Plex Sans",        "IBM design system full pair"),
    ("Inconsolata / Roboto",              "Inconsolata",         "Roboto",               "narrow mono + system neutral"),
    ("Share Tech Mono / Share Tech",      "Share Tech Mono",     "Share Tech",           "terminal aesthetic pair"),
    ("Courier Prime / Source Sans 3",     "Courier Prime",       "Source Sans 3",        "refined typewriter + modern sans"),
    # Handwritten / Creative
    ("Caveat / Nunito",                   "Caveat",              "Nunito",               "casual handwriting + rounded body"),
    ("Dancing Script / Josefin Sans",     "Dancing Script",      "Josefin Sans",         "flowing script + geometric thin"),
    ("Satisfy / Lato",                    "Satisfy",             "Lato",                 "decorative script + neutral body"),
    ("Kalam / Hind",                      "Kalam",               "Hind",                 "pen-stroke handwriting + readable"),
    ("Architects Daughter / Roboto",      "Architects Daughter", "Roboto",               "sketchy hand + system neutral"),
    # Cultural / International
    ("Noto Serif / Noto Sans",            "Noto Serif",          "Noto Sans",            "universal multilingual coverage"),
    ("Sawarabi Mincho / Sawarabi Gothic", "Sawarabi Mincho",     "Sawarabi Gothic",      "Japanese mincho + gothic pair"),
    ("Taviraj / Kanit",                   "Taviraj",             "Kanit",                "Thai-influenced serif + sans"),
    ("Scheherazade New / Amiri",          "Scheherazade New",    "Amiri",                "Arabic-optimised classic pair"),
    # Web-safe (no download)
    ("Georgia / Helvetica Neue",          "Georgia",             "Helvetica Neue",       "web-safe · no download needed"),
    ("Times New Roman / Arial",           "Times New Roman",     "Arial",                "web-safe · universal fallback"),
    ("Palatino / Trebuchet MS",           "Palatino",            "Trebuchet MS",         "web-safe · refined classic"),
    ("Garamond / Gill Sans",              "Garamond",            "Gill Sans",            "web-safe · British classic pair"),
    ("Didot / Futura",                    "Didot",               "Futura",               "web-safe · fashion magazine pair"),
    # Custom
    ("Custom",                            None,                  None,                   "any Google Font name"),
]

FONT_COLORS = [LAVEN,TEAL,PLUM,ROSE,ORG,CORAL,PEACH,ROSE,MINT,PEACH,EMBER,TEAL,STEEL,WINE,GOLD,TEAL,CREAM,MINT,LILAC,SAGE,LILAC,SKY,MINT,PEACH,MINT,STEEL,ICE,SKY,INDIGO,INDIGO,STEEL,SKY,TEAL,LIME,STEEL,MINT,STEEL,ICE,TEAL,SLATE,ROSE,ROSE,LILAC,SAGE,CORAL,MINT,ROSE,PEACH,GOLD,CREAM,CREAM,CREAM,CREAM,CREAM,SLATE]


def build_background():
    header("Background & Atmosphere", (140,80,255),(60,200,230))

    section("Background Style", "🎨", LAVEN)
    tip("Presets range from dark moody to bright — affects auto text contrast too.")

    bg_choice = menu("Background preset:", list(GRAD_PRESETS.keys()),
                     default="Deep Space", colors=GRAD_COLORS, descs=GRAD_DESCS)

    gradient, bg_color = None, "#1a1428"

    if bg_choice == "Custom solid color":
        bg_color = ask_inline("Background hex color", "#1a1428", LAVEN)

    elif bg_choice == "Custom gradient":
        gtype_choices = ["Diagonal (135°)","Horizontal (90°)","Vertical (180°)","Radial (ellipse)"]
        gtype_map     = {"Diagonal (135°)":"linear-diagonal","Horizontal (90°)":"linear-horizontal",
                         "Vertical (180°)":"linear-vertical","Radial (ellipse)":"radial"}
        gt = menu("Gradient direction:", gtype_choices, default="Diagonal (135°)",
                  colors=[LAVEN,TEAL,MINT,CORAL])
        tip("Enter 2–7 colors.  Semi-transparent hex fine: #1a1428cc")
        colors = []
        for i in range(1,8):
            req = " (required)" if i<=2 else " (Enter to stop)"
            c   = ask_inline(f"  Color {i}{req}", "")
            if not c:
                if i<=2: c = "#1a1428" if i==1 else "#0d1f3c"
                else: break
            colors.append(c)
        dur      = ask_inline("Animation duration (seconds)", "8", TEAL)
        gradient = {"type":gtype_map[gt],"colors":colors,"duration":int(dur)}
        bg_color = colors[0]

    else:
        preset   = GRAD_PRESETS[bg_choice]
        gradient = dict(preset)
        bg_color = preset["colors"][0]
        tag("Preset loaded", bg_choice, SLATE, TEAL)

    section("Drifting Orbs", "🌈", MINT)
    tip("Blurred colored blobs drifting slowly — 2 to 7 orbs supported.")
    info("Trailing '88' in hex = 53% opacity.  Lower = more subtle.")

    orb_choice = menu("Orb preset:", list(ORB_PRESETS.keys()),
                      default="Lavender / Cyan / Lime / Periwinkle",
                      colors=ORB_COLORS)
    orb_colors = ORB_PRESETS[orb_choice]
    if orb_colors is None:
        tip("Include alpha in hex: #c084fc88  (last 2 chars = opacity)")
        orb_colors = []
        for i in range(1,8):
            req = " (required)" if i<=2 else " (Enter to stop)"
            c   = ask_inline(f"  Orb {i} color{req}", "")
            if not c:
                if i<=2: c = "#c084fc88" if i==1 else "#67e8f988"
                else: break
            orb_colors.append(c)

    success(f"{len(orb_colors)} orbs ready  ·  background configured")
    return bg_color, gradient, orb_colors


# ══════════════════════════════════════════════════════════════════════════════
#  FONTS
# ══════════════════════════════════════════════════════════════════════════════






def pick_fonts():
    header("Typography", (200,100,255),(80,200,255))
    section("Font Pairing", "🔤", LAVEN)
    tip("Every Google Font name auto-loads from CDN — just type the name.")
    print()
    for i,(name,hf,bf,desc) in enumerate(FONT_PAIRS,1):
        num   = clr(f"{i:2d}.",SLATE)
        fc    = FONT_COLORS[(i-1)%len(FONT_COLORS)]
        label = clr(name,fc,BOLD) if i==1 else clr(name,fc)
        star  = clr(" ✦",GOLD) if i==1 else ""
        d     = clr(f"  {desc}",SLATE,ITAL)
        print(f"  {num}  {label}{star}{d}")
    rule()
    while True:
        raw = input(f"  {clr('›',LAVEN,BOLD)} ").strip()
        if not raw: raw="1"
        if raw.isdigit() and 1<=int(raw)<=len(FONT_PAIRS):
            _,hf,bf,_ = FONT_PAIRS[int(raw)-1]; break
        error(f"Enter 1–{len(FONT_PAIRS)}")
    if hf is None:
        hf = ask_inline("Heading font (Google Fonts name)","WDXL Lubrifont TC",LAVEN)
        bf = ask_inline("Body font    (Google Fonts name)","Space Mono",TEAL)
    success(f"Heading: {hf}   Body: {bf}")
    return hf, bf


# ══════════════════════════════════════════════════════════════════════════════
#  TEXT COLORS
# ══════════════════════════════════════════════════════════════════════════════

def pick_colors(bg_color):
    section("Text Colors", "🎨", ROSE)
    lum      = Presentation._luminance(bg_color)
    card_lum = lum * 0.78 + 0.22
    auto_lbl = "dark text (light card)" if card_lum>=0.35 else "light text (dark card)"
    tip("FrostPPT measures bg luminance + frosted glass overlay to auto-pick contrast text.")
    info(f"Detected palette:  {clr(auto_lbl,TEAL,BOLD)}")
    info("Override with any CSS color: rgba(255,255,255,0.95)  ·  #1a0a30  ·  white")
    print()
    heading_color = body_color = None
    if confirm("Override heading color?", False, ROSE):
        heading_color = ask_inline("Heading CSS color", "", ROSE)
        if heading_color: tag("Heading color", heading_color, ROSE, ROSE)
    if confirm("Override body color?", False, PEACH):
        body_color = ask_inline("Body CSS color", "", PEACH)
        if body_color: tag("Body color", body_color, PEACH, PEACH)
    success(f"Custom colors: {heading_color or 'auto'}  /  {body_color or 'auto'}")
    return heading_color, body_color


# ══════════════════════════════════════════════════════════════════════════════
#  ADVANCED SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

def pick_advanced():
    header("Advanced Settings", (80,180,255),(60,240,180))
    section("Card Dimensions", "📐", TEAL)
    tip("Card height is set by JS to the tallest slide — min-height is just the floor.")
    card_width  = int(ask_inline("Card width (px)",        "700", TEAL))
    card_mh     = int(ask_inline("Card min-height (px)",   "420", TEAL))
    section("Grain Texture", "✨", LAVEN)
    tip("Grain simulates acid-etched frosted glass. 0 = off, 0.28 = default, 1 = heavy.")
    grain_op    = float(ask_inline("Grain opacity (0.0–1.0)", "0.28", LAVEN))
    section("Animation Timing", "⏱", MINT)
    frost_dur   = int(ask_inline("Frost crystallise (ms)",  "1800", MINT))
    shatter_dur = int(ask_inline("Shatter exit (ms)",       "1100", CORAL))
    success("Advanced settings saved")
    tag_row(**{"width":f"{card_width}px","min-h":f"{card_mh}px",
               "grain":grain_op,"frost":f"{frost_dur}ms","shatter":f"{shatter_dur}ms"})
    return card_width, card_mh, grain_op, frost_dur, shatter_dur


# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def build_title_slide():
    section("Title Slide", "◈", LAVEN)
    tip("Hero slide: large heading + optional tagline, body paragraph, pill tags.")
    label   = ask_inline("Section label (small text above heading)", "", SLATE)
    heading = ask_inline("Heading  (HTML ok — <br> for line breaks)", "Untitled", LAVEN)
    tagline = ask_inline("Tagline  (italic subtitle)", "", LILAC)
    body    = ask_inline("Body paragraph", "", SLATE)
    pills   = ask_multi("Pill tags", LAVEN) if confirm("Add pill tags?", False, LAVEN) else []
    return Slide.title(label=label, heading=heading, tagline=tagline,
                       body=body, pills=pills or None), heading


def build_content_slide():
    section("Content Slide", "▤", TEAL)
    tip("Paragraphs + optional stat callouts and pill tags.")
    label   = ask_inline("Section label", "", SLATE)
    heading = ask_inline("Heading", "", TEAL)
    info("HTML is fine in body — <em>, <strong>, <br> etc.")
    body    = ask_multi("Body paragraphs", TEAL)
    stats   = []
    if confirm("Add stat callouts?  (big number + label)", False, GOLD):
        while True:
            n = ask_inline("  Stat value  (e.g. 42, ~85%, $1M, ∞)", "", GOLD)
            l = ask_inline("  Stat label", "", SLATE)
            if n: stats.append((n,l))
            if not confirm("  Another stat?", False, GOLD): break
    pills = ask_multi("Pill tags",TEAL) if confirm("Add pill tags?",False,TEAL) else []
    note  = ask_inline("Footer note (optional)", "", SLATE)
    return Slide.content(label=label, heading=heading, body=body or None,
                         stats=stats or None, pills=pills or None, note=note), heading


def build_two_col_slide():
    section("Two-Column Slide", "⊞", MINT)
    tip("Up to 4 items in a 2×2 grid — ideal for comparisons or feature lists.")
    label   = ask_inline("Section label", "", SLATE)
    heading = ask_inline("Heading", "", MINT)
    intro   = ask_inline("Intro paragraph (optional)", "", SLATE)
    columns = []
    for i in range(1,5):
        print(f"\n  {clr(f'Column {i}',MINT,BOLD)}")
        rule((60,180,100),(40,160,160))
        t = ask_inline("  Title", "", MINT)
        if not t: break
        b = ask_inline("  Body", "", SLATE)
        columns.append((t,b))
        if i<4 and not confirm(f"  Add column {i+1}?", i<3, MINT): break
    return Slide.two_col(label=label, heading=heading, intro=intro,
                         columns=columns), heading


def build_quote_slide():
    section("Quote Slide", "❝", ROSE)
    tip(r"Full-bleed centered quote. Use \n for line breaks.")
    label = ask_inline("Section label", "", SLATE)
    quote = ask_inline(r"Quote text  (\n = new line)", "", ROSE)
    attr  = ask_inline("Attribution (optional)", "", SLATE)
    return Slide.quote(label=label, quote=quote.replace("\\n","\n"),
                       attribution=attr), f'"{quote[:40]}"'


def build_media_slide():
    section("Media Slide", "⬤", PEACH)
    tip("Image / video / audio.  Local file → base64 embedded.  URL → linked.")
    info("Supported: .jpg .png .gif .webp .mp4 .webm .mp3 .ogg .wav + more")
    src = ask_inline("File path or URL", "", PEACH)
    if not src:
        warn("No source — slide skipped."); return None, ""
    label    = ask_inline("Section label (optional)", "", SLATE)
    caption  = ask_inline("Caption (optional)", "", SLATE)
    autoplay = confirm("Autoplay?  (video/audio)", False, PEACH)
    loop_    = confirm("Loop?      (video/audio)", False, PEACH)
    controls = confirm("Show controls?", True, PEACH)
    return Slide.media(src=src, caption=caption, label=label,
                       autoplay=autoplay, loop=loop_, controls=controls), src.split("/")[-1]


def build_raw_slide():
    section("Raw HTML Slide", "⚙", SAGE)
    warn("Type raw HTML. Type END on its own line to finish.")
    label = ask_inline("Section label", "", SLATE)
    lines = []
    print(f"\n  {clr('HTML ›',SAGE,BOLD)}")
    print(f"  {clr('(type END to finish)',SLATE,ITAL)}")
    rule((60,140,80),(40,160,120))
    while True:
        line = input(f"  {clr('│ ',SAGE)}").rstrip()
        if line.strip().upper() == "END": break
        lines.append(line)
    return Slide.raw(label=label, html="\n".join(lines)), "Custom HTML"


SLIDE_BUILDERS = {
    "Title":      (build_title_slide,   "◈", LAVEN, "Hero heading · tagline · body · pills"),
    "Content":    (build_content_slide, "▤", TEAL,  "Paragraphs · stat callouts · pills"),
    "Two Column": (build_two_col_slide, "⊞", MINT,  "2×2 grid of title+body pairs"),
    "Quote":      (build_quote_slide,   "❝", ROSE,  "Full-bleed centered quote"),
    "Media":      (build_media_slide,   "⬤", PEACH, "Image / video / audio  (local or URL)"),
    "Raw HTML":   (build_raw_slide,     "⚙", SAGE,  "Full HTML — no constraints"),
}


# ══════════════════════════════════════════════════════════════════════════════
#  .FRPPT PROJECT ENGINE  —  save · load · autosave · decompile
# ══════════════════════════════════════════════════════════════════════════════

AUTOSAVE_PATH = Path.home() / ".frostppt_autosave.frppt"

# Global mutable session state — populated by main(), read by autosave hook
_SESSION: dict = {}


def _build_prs_from_session() -> Presentation:
    s = _SESSION
    prs = Presentation(
        title=s.get("prs_title","Untitled"), bg_color=s.get("bg_color","#1a1428"),
        gradient=s.get("gradient"), orb_colors=s.get("orb_colors"),
        heading_font=s.get("hf","WDXL Lubrifont TC"), body_font=s.get("bf","Space Mono"),
        heading_color=s.get("heading_color"), body_color=s.get("body_color"),
        card_width=s.get("card_width",700), card_min_height=s.get("card_mh",420),
        grain_opacity=s.get("grain_op",0.28),
        frost_duration=s.get("frost_dur",1800), shatter_duration=s.get("shatter_dur",1100),
    )
    for slide in s.get("slide_objs",[]): prs.add(slide)
    return prs


def _session_from_prs(prs: Presentation, slides_meta: list, out_file: str = "") -> None:
    _SESSION.update({
        "prs_title":prs.title, "out_file":out_file or prs.title.lower().replace(" ","_")[:40]+".html",
        "hf":prs.heading_font, "bf":prs.body_font,
        "bg_color":prs.bg_color, "gradient":prs.gradient, "orb_colors":prs.orb_colors,
        "heading_color":prs.heading_color, "body_color":prs.body_color,
        "card_width":prs.card_width, "card_mh":prs.card_min_height,
        "grain_op":prs.grain_opacity, "frost_dur":prs.frost_duration,
        "shatter_dur":prs.shatter_duration,
        "slide_objs":list(prs._slides), "slides_meta":slides_meta,
    })


def _save_frppt_with_meta(prs: Presentation, slides_meta: list, path: str) -> None:
    """Save .frppt with CLI display metadata (kind + title) embedded."""
    d = prs.to_dict()
    d["cli_meta"] = {"slides_meta": slides_meta,
                     "out_file": _SESSION.get("out_file","")}
    Path(path).write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_frppt_with_meta(path: str):
    """Returns (Presentation, slides_meta, out_file)."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    prs = Presentation.from_dict(raw)
    cli = raw.get("cli_meta", {})
    slides_meta = cli.get("slides_meta") or [
        (s.get("type","raw").replace("_"," ").title(), f"Slide {i+1}")
        for i,s in enumerate(raw.get("slides",[]))
    ]
    return prs, slides_meta, cli.get("out_file","")


def autosave_now(silent: bool = True) -> None:
    if not _SESSION.get("prs_title"): return
    try:
        prs = _build_prs_from_session()
        _save_frppt_with_meta(prs, _SESSION.get("slides_meta",[]), str(AUTOSAVE_PATH))
        if not silent:
            success(f"Autosaved  →  {AUTOSAVE_PATH}")
    except Exception:
        pass


def _atexit_hook() -> None:
    autosave_now(silent=True)


def _signal_handler(sig, frame) -> None:
    autosave_now(silent=True)
    print()
    warn("Interrupted — session autosaved")
    info(f"Resume:  python frostppt_cli.py --resume")
    print()
    sys.exit(0)


def _register_hooks() -> None:
    atexit.register(_atexit_hook)
    for sig in (signal.SIGINT, signal.SIGTERM):
        try: signal.signal(sig, _signal_handler)
        except (OSError, ValueError): pass


# ── CLI args: --resume  --load <f>  --decompile <f> ────────────────────────

def _check_args():
    """Returns (prs|None, slides_meta, out_file, was_loaded)."""
    args = sys.argv[1:]
    if "--decompile" in args:
        idx = args.index("--decompile")
        if idx+1 >= len(args):
            error("Usage:  python frostppt_cli.py --decompile myfile.html"); sys.exit(1)
        return _cmd_decompile(args[idx+1])
    if "--load" in args:
        idx = args.index("--load")
        if idx+1 >= len(args):
            error("Usage:  python frostppt_cli.py --load myfile.frppt"); sys.exit(1)
        return _cmd_load(args[idx+1])
    if "--resume" in args:
        if AUTOSAVE_PATH.exists():
            return _cmd_load(str(AUTOSAVE_PATH), autosave=True)
        warn("No autosave found."); return None,[],  "", False
    return None, [], "", False


def _cmd_load(path, autosave=False):
    try:
        prs, meta, out = _load_frppt_with_meta(path)
        lbl = "Autosave recovered" if autosave else f"Loaded  {path}"
        success(lbl)
        tag_row(**{"Slides":len(prs._slides),"Title":prs.title})
        return prs, meta, out, True
    except Exception as e:
        error(f"Failed to load {path}: {e}"); return None,[],  "",False


def _cmd_decompile(path):
    try:
        prs = Presentation.decompile_html(path)
        meta = [
            (s._data.get("type","raw").replace("_"," ").title(),
             (s._data.get("args",{}).get("heading") or
              s._data.get("args",{}).get("quote","Slide"))[:50])
            for s in prs._slides
        ]
        success(f"Decompiled  {path}  →  {len(prs._slides)} slides")
        tag_row(**{"Title":prs.title,"Font":prs.heading_font})
        return prs, meta, "", True
    except ValueError as e:
        error(str(e)); sys.exit(1)
    except Exception as e:
        error(f"Decompile failed: {e}"); sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    banner()
    _register_hooks()

    # ── Handle CLI args (--resume / --load / --decompile) ──────────────────
    loaded_prs, loaded_meta, loaded_out, was_loaded = _check_args()

    # ── Autosave opt-in (asked once at the very start) ──────────────────────
    section("Project Settings", "💾", GOLD)
    tip("Autosave writes to ~/.frostppt_autosave.frppt on every change and on exit.")
    tip("Resume a crashed/interrupted session with:  python frostppt_cli.py --resume")
    autosave_enabled = confirm("Enable autosave?", True, GOLD)
    if autosave_enabled:
        info("Autosave ON  ·  saved after every slide change + on exit", "✦")
    else:
        info("Autosave OFF  ·  use  Save project (.frppt)  from the slides menu", "○")

    # ── Identity ──────────────────────────────────────────────────────────────
    if was_loaded and loaded_prs:
        header("Resuming Project", (100,80,220),(60,180,200))
        section("Identity", "📋", LILAC)
        prs_title  = ask("Presentation title", loaded_prs.title, LAVEN)
        default_fn = loaded_out or prs_title.lower().replace(" ","_")[:40]+".html"
        out_file   = ask("Output filename", default_fn, SLATE)
        if not out_file.endswith(".html"): out_file += ".html"
        tag_row(**{"Title":prs_title,"File":out_file})

        # Ask whether to keep existing settings or reconfigure
        keep = confirm("Keep existing background / fonts / colors / advanced settings?", True, TEAL)
        if keep:
            hf=loaded_prs.heading_font; bf=loaded_prs.body_font
            bg_color=loaded_prs.bg_color; gradient=loaded_prs.gradient
            orb_colors=loaded_prs.orb_colors
            heading_color=loaded_prs.heading_color; body_color=loaded_prs.body_color
            card_width=loaded_prs.card_width; card_mh=loaded_prs.card_min_height
            grain_op=loaded_prs.grain_opacity; frost_dur=loaded_prs.frost_duration
            shatter_dur=loaded_prs.shatter_duration
            tag_row(**{"Heading font":hf,"Body font":bf,"BG":bg_color})
            success("Existing settings restored")
        else:
            hf, bf = pick_fonts()
            bg_color, gradient, orb_colors = build_background()
            heading_color, body_color = pick_colors(bg_color)
            card_width=700; card_mh=420; grain_op=0.28; frost_dur=1800; shatter_dur=1100
            if confirm("Configure advanced settings?", False, STEEL):
                card_width,card_mh,grain_op,frost_dur,shatter_dur = pick_advanced()

        slides_meta = list(loaded_meta)
        slide_objs  = list(loaded_prs._slides)

    else:
        header("New Presentation", (100,80,220),(60,180,200))
        section("Identity", "📋", LILAC)
        prs_title  = ask("Presentation title", "Untitled Presentation", LAVEN)
        default_fn = prs_title.lower().replace(" ","_")[:40]+".html"
        out_file   = ask("Output filename", default_fn, SLATE)
        if not out_file.endswith(".html"): out_file += ".html"
        tag_row(**{"Title":prs_title,"File":out_file})

        hf, bf                        = pick_fonts()
        bg_color, gradient, orb_colors = build_background()
        heading_color, body_color       = pick_colors(bg_color)

        card_width=700; card_mh=420; grain_op=0.28; frost_dur=1800; shatter_dur=1100
        if confirm("Configure advanced settings?  (card size · grain · timing)", False, STEEL):
            card_width, card_mh, grain_op, frost_dur, shatter_dur = pick_advanced()

        slides_meta = []
        slide_objs  = []

    # ── Populate session for autosave ─────────────────────────────────────────
    _SESSION.update({
        "prs_title":prs_title,"out_file":out_file,
        "hf":hf,"bf":bf,"bg_color":bg_color,"gradient":gradient,"orb_colors":orb_colors,
        "heading_color":heading_color,"body_color":body_color,
        "card_width":card_width,"card_mh":card_mh,"grain_op":grain_op,
        "frost_dur":frost_dur,"shatter_dur":shatter_dur,
        "slide_objs":slide_objs,"slides_meta":slides_meta,
    })

    def _after_change():
        """Call after every slide list mutation."""
        _SESSION["slide_objs"]  = slide_objs
        _SESSION["slides_meta"] = slides_meta
        if autosave_enabled:
            autosave_now(silent=True)

    # ── Slides loop ───────────────────────────────────────────────────────────
    while True:
        header(f"Slides  ·  {len(slides_meta)} added", (80,200,255),(100,255,200))
        show_slide_list(slides_meta)

        action = menu("What next?", [
            "Add slide","Remove slide","Reorder slides","Preview list",
            "Save project (.frppt)","Save as new (.frppt)","Done — generate",
        ], default="Add slide",
           colors=[TEAL,CORAL,ORG,STEEL,GOLD,LILAC,GRN],
           descs=["build a new slide","delete a slide","change order",
                  "review all slides",
                  "save editable project file",
                  "save copy under new name",
                  "compile to HTML + save .frppt"])

        # ── Add ───────────────────────────────────────────────────────────────
        if action == "Add slide":
            print()
            print(f"  {clr('❯',LAVEN,BOLD)}  {clr('Slide type:',WHT,BOLD)}")
            rule()
            keys = list(SLIDE_BUILDERS.keys())
            for i,k in enumerate(keys,1):
                _,icon,ic,desc = SLIDE_BUILDERS[k]
                print(f"  {clr(f'{i:2d}.',SLATE)}  {clr(icon,ic,BOLD)}  {clr(k,ic,BOLD)}{clr(f'  {desc}',SLATE,ITAL)}")
            rule()
            while True:
                raw = input(f"  {clr('›',LAVEN,BOLD)} ").strip()
                if raw.isdigit() and 1<=int(raw)<=len(keys):
                    kind=keys[int(raw)-1]; break
                error(f"Enter 1–{len(keys)}")
            try:
                slide_obj, title = SLIDE_BUILDERS[kind][0]()
                if slide_obj is not None:
                    slide_objs.append(slide_obj)
                    slides_meta.append((kind, title or f"Slide {len(slides_meta)+1}"))
                    success(f'Added {kind}  →  "{title}"')
                    _after_change()
            except KeyboardInterrupt:
                warn("Slide creation cancelled.")

        # ── Remove ────────────────────────────────────────────────────────────
        elif action == "Remove slide":
            if not slides_meta: warn("No slides to remove."); continue
            show_slide_list(slides_meta)
            raw = ask_inline("Remove slide number  (Enter to cancel)","",CORAL)
            if raw.isdigit():
                idx = int(raw)-1
                if 0<=idx<len(slides_meta):
                    removed=slides_meta.pop(idx); slide_objs.pop(idx)
                    success(f"Removed slide {idx+1}: {removed[1]}")
                    _after_change()
                else: error("Invalid slide number.")

        # ── Reorder ───────────────────────────────────────────────────────────
        elif action == "Reorder slides":
            if len(slides_meta)<2: warn("Need at least 2 slides."); continue
            show_slide_list(slides_meta)
            frm = ask_inline("Move slide number","",ORG)
            to  = ask_inline("To position",     "",ORG)
            if frm.isdigit() and to.isdigit():
                fi,ti = int(frm)-1,int(to)-1
                n = len(slides_meta)
                if 0<=fi<n and 0<=ti<n:
                    slides_meta.insert(ti,slides_meta.pop(fi))
                    slide_objs.insert(ti,slide_objs.pop(fi))
                    success(f"Moved slide {fi+1} → position {ti+1}")
                    _after_change()
                else: error("Invalid slide numbers.")

        # ── Preview ───────────────────────────────────────────────────────────
        elif action == "Preview list":
            show_slide_list(slides_meta)
            input(clr("\n  Press Enter to continue… ",SLATE))

        # ── Save project ─────────────────────────────────────────────────────
        elif action in ("Save project (.frppt)", "Save as new (.frppt)"):
            default_frppt = out_file.replace(".html",".frppt")
            if action == "Save as new (.frppt)":
                default_frppt = ask_inline("Save as", default_frppt, GOLD)
                if not default_frppt.endswith(".frppt"):
                    default_frppt += ".frppt"
            else:
                if not confirm(f"Save to  {default_frppt}?", True, GOLD):
                    default_frppt = ask_inline("Filename", default_frppt, GOLD)
                    if not default_frppt.endswith(".frppt"): default_frppt += ".frppt"
            try:
                prs_tmp = _build_prs_from_session()
                _save_frppt_with_meta(prs_tmp, slides_meta, default_frppt)
                success(f"Project saved  →  {default_frppt}")
                tip("Share this .frppt file — recipient opens with:  python frostppt_cli.py --load " + default_frppt)
            except Exception as e:
                error(f"Save failed: {e}")

        # ── Done ─────────────────────────────────────────────────────────────
        elif action == "Done — generate":
            if not slide_objs: warn("Add at least one slide first."); continue
            break

    # ── Build HTML ────────────────────────────────────────────────────────────
    header("Generating", (80,255,180),(80,180,255))
    print()
    steps = len(slide_objs)+4
    for s in range(steps+1):
        progress_bar("Compiling", s, steps); time.sleep(0.04)
    print()

    prs = Presentation(
        title=prs_title, bg_color=bg_color, gradient=gradient,
        orb_colors=orb_colors, heading_font=hf, body_font=bf,
        heading_color=heading_color, body_color=body_color,
        card_width=card_width, card_min_height=card_mh,
        grain_opacity=grain_op, frost_duration=frost_dur, shatter_duration=shatter_dur,
    )
    for s in slide_objs: prs.add(s)

    try:
        prs.save(out_file)
    except Exception as e:
        error(f"Failed to save HTML: {e}"); sys.exit(1)

    # Also save .frppt alongside HTML automatically
    frppt_out = out_file.replace(".html",".frppt")
    try:
        _save_frppt_with_meta(prs, slides_meta, frppt_out)
    except Exception:
        pass  # non-fatal

    # Clear autosave — clean finish
    try:
        if AUTOSAVE_PATH.exists(): AUTOSAVE_PATH.unlink()
    except Exception:
        pass

    success_box(out_file, frppt_out, len(slide_objs))


if __name__ == "__main__":
    # Handle --decompile / --load / --resume without calling full main()
    if len(sys.argv) > 1 and sys.argv[1] in ("--help","-h"):
        print()
        print(clr("  FrostPPT CLI", WHT, BOLD))
        print(clr("  ─────────────────────────────────────────────────────", SLATE))
        print(f"  {clr('python frostppt_cli.py',TEAL)}                     start new presentation")
        print(f"  {clr('python frostppt_cli.py --resume',TEAL)}            resume from autosave")
        print(f"  {clr('python frostppt_cli.py --load deck.frppt',TEAL)}   open a .frppt project")
        print(f"  {clr('python frostppt_cli.py --decompile deck.html',TEAL)}  recover HTML → .frppt")
        print()
        sys.exit(0)
    main()
