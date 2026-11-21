#!/usr/bin/env python3
"""Mobile-friendly assets for the profile README.

  python3 build_mobile.py <repo_root>

Writes into <repo_root>/assets:
  flora-card-01..06.svg   one self-contained card per work (head + animated GIF + demo button)
  hero-card.svg           EXP.001 strip + compilation GIF
  hero-side.svg           folder-index strip + description tile
  manifesto-m.svg         single-column manifesto
  stack-m.svg             2-column toolkit grid

Cards are meant to be placed as plain <img width="NNN"> tags (fixed pixel width): they sit side by
side on a laptop and wrap to one per row on a phone, no CSS needed.
"""
import base64, os, re, sys

ROOT = sys.argv[1]
A = os.path.join(ROOT, "assets")
CREAM, RED, ACC, DEEP = "#F5EFE6", "#87100F", "#E63946", "#7A0E0D"
FH = "'Helvetica Neue', 'Arial Black', Helvetica, Arial, sans-serif"
FM = "'Courier New', Courier, monospace"


def esc(t):
    return t.replace("&", "&amp;")


def write(name, text):
    with open(os.path.join(A, name), "w", encoding="utf-8") as f:
        f.write(text)


def gif_uri(name):
    with open(os.path.join(A, name), "rb") as f:
        return "data:image/gif;base64," + base64.b64encode(f.read()).decode()


def gif_size(name):
    import struct
    with open(os.path.join(A, name), "rb") as f:
        w, h = struct.unpack("<HH", f.read(10)[6:10])
    return w, h


def nested(fname, x, y, w, h, prefix):
    """embed another svg file as a nested <svg>, namespacing its ids"""
    t = open(os.path.join(A, fname), encoding="utf-8").read()
    vb = re.search(r'viewBox="([^"]+)"', t).group(1)
    inner = re.sub(r"^.*?<svg[^>]*>", "", t, count=1, flags=re.S)
    inner = re.sub(r"</svg>\s*$", "", inner, flags=re.S)
    for i in set(re.findall(r'\bid="([^"]+)"', inner)):
        inner = inner.replace(f'id="{i}"', f'id="{prefix}{i}"').replace(f"url(#{i})", f"url(#{prefix}{i})")
    return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vb}">{inner}</svg>'


# ------------------------------------------------------------------ flora cards (320 x 326)
WORKS = [
    ("01", "ROSES", "red-roses.gif"), ("02", "LOTUS", "lotus.gif"),
    ("03", "BLOOMING FLOWER", "blooming-flower.gif"), ("04", "EDELWEISS", "edelweiss.gif"),
    ("05", "STARGAZER LILY", "stargazer-lily.gif"), ("06", "HIGANBANA", "higanbana.gif"),
]
for num, title, gif in WORKS:
    uri = gif_uri(gif)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="326" viewBox="0 0 320 326" role="img" aria-label="{num} {title.lower()}: live preview. Open live demo.">
  <defs><clipPath id="r{num}"><rect width="320" height="326" rx="10"/></clipPath></defs>
  <g clip-path="url(#r{num})">
    <rect width="320" height="326" fill="#140202"/>
    <rect width="320" height="40" fill="{RED}"/>
    <line x1="0" y1="39.25" x2="320" y2="39.25" stroke="{CREAM}" stroke-opacity="0.22"/>
    <text x="16" y="25" font-family="{FM}" font-size="12" font-weight="700" letter-spacing="1.5" fill="{CREAM}">№  {num}</text>
    <text x="304" y="25" text-anchor="end" font-family="{FM}" font-size="12" font-weight="700" letter-spacing="1.5" fill="{CREAM}" fill-opacity="0.72">// {title}</text>
    <image x="0" y="40" width="320" height="240" preserveAspectRatio="xMidYMid slice" href="{uri}"/>
    <rect y="280" width="320" height="46" fill="{CREAM}"/>
    <text x="16" y="308" font-family="{FH}" font-size="14" font-weight="900" letter-spacing="0.8" fill="{DEEP}">OPEN LIVE DEMO</text>
    <path d="M 288,310 L 302,296 M 291,296 H 302 V 307" fill="none" stroke="{DEEP}" stroke-width="2.6" stroke-linecap="square"/>
  </g>
  <rect x="0.75" y="0.75" width="318.5" height="324.5" rx="10" fill="none" stroke="{RED}" stroke-width="1.5"/>
</svg>
'''
    write(f"flora-card-{num}.svg", svg)

# ------------------------------------------------------------------ hero card + side tile
gw, gh = gif_size("compilation.gif")
HW = 620
GH = round(HW * gh / gw, 2)
HH = 44 + GH
write("hero-card.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" width="{HW}" height="{HH}" viewBox="0 0 {HW} {HH}" role="img" aria-label="EXP.001 flora: compilation of interactive flower studies">
  <defs><clipPath id="hc"><rect width="{HW}" height="{HH}" rx="8"/></clipPath></defs>
  <g clip-path="url(#hc)">
    <rect width="{HW}" height="{HH}" fill="#140202"/>
    {nested("exp-001.svg", 0, 0, HW, 44, "s_")}
    <image x="0" y="44" width="{HW}" height="{GH}" preserveAspectRatio="xMidYMid slice" href="{gif_uri("compilation.gif")}"/>
  </g>
  <rect x="0.75" y="0.75" width="{HW - 1.5}" height="{HH - 1.5:.2f}" rx="8" fill="none" stroke="{RED}" stroke-width="1.5"/>
</svg>
''')
SH = 44 + 6 + 386.73
write("hero-side.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" width="360" height="{SH:.2f}" viewBox="0 0 360 {SH:.2f}" role="img" aria-label="flora: a growing series of interactive flower studies. Open flora folder.">
  {nested("lab-url.svg", 0, 0, 360, 44, "u_")}
  {nested("lab-desc.svg", 0, 50, 360, 386.73, "d_")}
</svg>
''')
print("hero heights  card@520 =", round(520 * HH / HW, 1), " side@272 =", round(272 * SH / 360, 1))

# ------------------------------------------------------------------ manifesto (single column)
W, H = 400, 552
write("manifesto-m.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Manifesto: building interactive visual playgrounds, generative art and tactile web interfaces. Explorations: interactive canvas, 2D/3D simulation, shaders, generative art, kinetic UI, motion systems. Arsenal: JS, TS, Three.js, Vue, React, Processing, After Effects.">
  <defs>
    <radialGradient id="mb" cx="30%" cy="30%" r="90%"><stop offset="0" stop-color="#2A0505"/><stop offset="1" stop-color="#140202"/></radialGradient>
    <clipPath id="mc"><rect width="{W}" height="{H}" rx="12"/></clipPath>
  </defs>
  <g clip-path="url(#mc)">
    <rect width="{W}" height="{H}" fill="url(#mb)"/>
    <g stroke="{CREAM}" stroke-opacity="0.14"><line x1="0" y1="44" x2="{W}" y2="44"/><line x1="24" y1="326" x2="{W - 24}" y2="326"/><line x1="24" y1="450" x2="{W - 24}" y2="450"/></g>
    <text x="24" y="28" font-family="{FM}" font-size="11.5" font-weight="700" letter-spacing="2" fill="{ACC}">[01 // MANIFESTO]</text>
    <g font-family="{FH}" font-weight="800" font-size="33" letter-spacing="-1.4" fill="{CREAM}">
      <text x="24" y="92">building interactive</text>
      <text x="24" y="130">visual playgrounds,</text>
      <text x="24" y="168">generative art</text>
      <text x="24" y="206">&amp; tactile web</text>
      <text x="24" y="244">interfaces.</text>
    </g>
    <g font-family="Georgia, 'Times New Roman', serif" font-style="italic" font-size="14" fill="{CREAM}" fill-opacity="0.75">
      <text x="24" y="284">“I’d rather spend an hour on an easing curve</text>
      <text x="24" y="304">than skip it.”</text>
    </g>
    <text x="24" y="356" font-family="{FM}" font-size="11.5" font-weight="700" letter-spacing="2" fill="{ACC}">[02 // EXPLORATIONS]</text>
    <g font-family="{FH}" font-weight="700" font-size="16" letter-spacing="-0.3" fill="{CREAM}">
      <text x="24" y="386">Interactive Canvas · 2D/3D Simulation</text>
      <text x="24" y="410" fill-opacity="0.82">Shaders · Generative Art</text>
      <text x="24" y="434" fill-opacity="0.82">Kinetic UI · Motion Systems</text>
    </g>
    <text x="24" y="480" font-family="{FM}" font-size="11.5" font-weight="700" letter-spacing="2" fill="{ACC}">[03 // ARSENAL]</text>
    <g font-family="{FM}" font-size="13.5" font-weight="700" letter-spacing="1" fill="{CREAM}" fill-opacity="0.9">
      <text x="24" y="508">JS / TS · THREE.JS · VUE</text>
      <text x="24" y="530">REACT · PROCESSING · AE</text>
    </g>
  </g>
  <rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="12" fill="none" stroke="{RED}" stroke-width="1.5"/>
</svg>
''')

# ------------------------------------------------------------------ stack (2 columns)
ITEMS = [("HTML5", "MARKUP"), ("CSS3", "STYLE"), ("JAVASCRIPT", "LANGUAGE"), ("TYPESCRIPT", "LANGUAGE"),
         ("CANVAS API", "2D GRAPHICS"), ("THREE.JS", "3D / WEBGL"), ("SHADERS", "GLSL"), ("PROCESSING", "CREATIVE CODE"),
         ("VUE 3", "FRAMEWORK"), ("REACT", "LIBRARY"), ("TAILWIND", "UTILITY CSS"), ("AFTER EFFECTS", "MOTION")]
cw, ch, gap, mx, my = 176, 60, 10, 18, 18
SW = 400
SHt = my * 2 + 6 * ch + 5 * gap
boxes = []
for i, (name, cat) in enumerate(ITEMS):
    r, c = divmod(i, 2)
    x, y = mx + c * (cw + gap), my + r * (ch + gap)
    inv = (r + c) % 2 == 0
    fill, fo = (CREAM, "1") if inv else ("#2A0505", "0.55")
    tc = DEEP if inv else CREAM
    boxes.append(f'''    <rect x="{x}" y="{y}" width="{cw}" height="{ch}" fill="{fill}" fill-opacity="{fo}" stroke="{CREAM}" stroke-opacity="0.85" stroke-width="1.5"/>
    <text x="{x + 12}" y="{y + 19}" font-family="{FM}" font-size="10" letter-spacing="1" fill="{tc}" fill-opacity="0.72">{i + 1:02d} / {cat}</text>
    <text x="{x + 12}" y="{y + 47}" font-family="{FH}" font-size="21" font-weight="800" letter-spacing="-0.8" fill="{tc}">{esc(name)}</text>''')
write("stack-m.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SW}" height="{SHt}" viewBox="0 0 {SW} {SHt}" role="img" aria-label="Tooling: HTML5, CSS3, JavaScript, TypeScript, Canvas API, Three.js, shaders, Processing, Vue 3, React, Tailwind, After Effects">
  <defs>
    <radialGradient id="sb" cx="45%" cy="40%" r="90%"><stop offset="0" stop-color="#A81918"/><stop offset="0.65" stop-color="#87100F"/><stop offset="1" stop-color="#5C0908"/></radialGradient>
    <clipPath id="sc2"><rect width="{SW}" height="{SHt}" rx="12"/></clipPath>
  </defs>
  <g clip-path="url(#sc2)">
    <rect width="{SW}" height="{SHt}" fill="url(#sb)"/>
{chr(10).join(boxes)}
  </g>
</svg>
''')
print("mobile assets written")