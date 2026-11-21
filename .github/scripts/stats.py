#!/usr/bin/env python3
"""Generate brutalist GitHub stats (stats-metrics.svg, stats-langs.svg) and framed snakes."""
import json, os, re, sys, datetime, urllib.request

OUT = sys.argv[1]
MOCK = "--mock" in sys.argv
os.makedirs(OUT, exist_ok=True)

CREAM, RED, ACC, DEEP = "#F5EFE6", "#87100F", "#E63946", "#5C0908"
FH = "'Helvetica Neue', 'Arial Black', Arial, sans-serif"
FM = "'Courier New', Courier, monospace"
SEG = ["#F5EFE6", "#E63946", "#B33A39", "#87100F", "#5C0908"]


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;")


QUERY = """
query($login:String!){
  user(login:$login){
    followers{ totalCount }
    repositories(first:100, ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC,
                 orderBy:{field:PUSHED_AT, direction:DESC}){
      totalCount
      nodes{ stargazerCount
             languages(first:8, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name } } } }
    }
    contributionsCollection{
      contributionCalendar{ totalContributions
        weeks{ contributionDays{ date contributionCount } } }
    }
  }
}"""


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-stats"})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload or not payload.get("data", {}).get("user"):
        raise RuntimeError(payload.get("errors") or "user not found")
    return payload["data"]["user"]


def streaks(days):
    counts = [d["contributionCount"] for d in sorted(days, key=lambda d: d["date"])]
    longest = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    tail = counts[:]
    if tail and tail[-1] == 0:
        tail = tail[:-1]
    cur = 0
    for c in reversed(tail):
        if c > 0:
            cur += 1
        else:
            break
    return cur, longest


def collect():
    if MOCK:
        return dict(total=1284, cur=17, longest=42, repos=23, stars=58, followers=31,
                    langs=[("JavaScript", 46.2), ("CSS", 18.5), ("HTML", 15.1), ("TypeScript", 9.4),
                           ("Java", 6.3), ("Other", 4.5)])
    d = dict(total=None, cur=None, longest=None, repos=None, stars=None, followers=None, langs=[])
    try:
        u = fetch(os.environ["LOGIN"], os.environ["GH_TOKEN"])
        cal = u["contributionsCollection"]["contributionCalendar"]
        days = [x for w in cal["weeks"] for x in w["contributionDays"]]
        d["total"] = cal["totalContributions"]
        d["cur"], d["longest"] = streaks(days)
        d["repos"] = u["repositories"]["totalCount"]
        d["stars"] = sum(n["stargazerCount"] for n in u["repositories"]["nodes"])
        d["followers"] = u["followers"]["totalCount"]
        size = {}
        for n in u["repositories"]["nodes"]:
            for e in n["languages"]["edges"]:
                size[e["node"]["name"]] = size.get(e["node"]["name"], 0) + e["size"]
        tot = sum(size.values()) or 1
        ranked = sorted(size.items(), key=lambda kv: -kv[1])
        top = [(k, v * 100 / tot) for k, v in ranked[:5]]
        rest = 100 - sum(p for _, p in top)
        if rest > 0.5 and len(ranked) > 5:
            top.append(("Other", rest))
        d["langs"] = top
    except Exception as e:
        print("stats fetch failed:", e, file=sys.stderr)
    return d


def num(v):
    return "—" if v is None else f"{v:,}"


def write_metrics(d):
    top = d["langs"][0][0].upper() if d["langs"] else "—"
    top_fs = max(18, min(27, int(200 / (max(len(top), 1) * 0.68))))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="310" viewBox="0 0 1000 310" role="img" aria-label="GitHub Activity Metrics">
  <defs>
    <radialGradient id="crimsonCard" cx="30%" cy="30%" r="85%">
      <stop offset="0%" stop-color="#A81918" />
      <stop offset="100%" stop-color="#620A09" />
    </radialGradient>
    <radialGradient id="darkCard" cx="50%" cy="50%" r="85%">
      <stop offset="0%" stop-color="#240404" />
      <stop offset="100%" stop-color="#120202" />
    </radialGradient>
  </defs>

  <rect x="1" y="1" width="386" height="168" rx="12" fill="url(#crimsonCard)" stroke="#87100F" stroke-width="1.5" />
  <text x="24" y="30" font-family="{FM}" font-size="11" font-weight="700" letter-spacing="1.5" fill="{CREAM}" fill-opacity="0.88">[ CONTRIBUTIONS ]</text>
  <text x="24" y="114" font-family="{FH}" font-size="68" font-weight="900" letter-spacing="-3" fill="{CREAM}">{esc(num(d["total"]))}</text>
  <text x="24" y="150" font-family="{FM}" font-size="10.5" letter-spacing="1.2" fill="{CREAM}" fill-opacity="0.78">LAST 12 MONTHS // ALL ACTIVITY</text>

  <rect x="397" y="1" width="296" height="168" rx="12" fill="url(#darkCard)" stroke="#5C0908" stroke-width="1.5" />
  <text x="420" y="30" font-family="{FM}" font-size="11" font-weight="700" letter-spacing="1.5" fill="{ACC}">CURRENT STREAK</text>
  <text x="420" y="114" font-family="{FH}" font-size="68" font-weight="900" letter-spacing="-3" fill="{CREAM}">{esc(num(d["cur"]))}</text>
  <text x="420" y="150" font-family="{FM}" font-size="10.5" letter-spacing="1.2" fill="{CREAM}" fill-opacity="0.65">DAYS IN A ROW</text>

  <rect x="703" y="1" width="296" height="168" rx="12" fill="{CREAM}" stroke="{CREAM}" stroke-width="1.5" />
  <text x="726" y="30" font-family="{FM}" font-size="11" font-weight="700" letter-spacing="1.5" fill="{RED}">LONGEST STREAK</text>
  <text x="726" y="114" font-family="{FH}" font-size="68" font-weight="900" letter-spacing="-3" fill="{RED}">{esc(num(d["longest"]))}</text>
  <text x="726" y="150" font-family="{FM}" font-size="10.5" font-weight="700" letter-spacing="1.2" fill="{DEEP}">DAYS // LAST 12 MONTHS</text>

  <rect x="1" y="179" width="242" height="130" rx="12" fill="url(#darkCard)" stroke="#5C0908" stroke-width="1.5" />
  <text x="20" y="205" font-family="{FM}" font-size="10.5" font-weight="700" letter-spacing="1.2" fill="{ACC}">PUBLIC REPOS</text>
  <text x="20" y="260" font-family="{FH}" font-size="44" font-weight="900" letter-spacing="-2" fill="{CREAM}">{esc(num(d["repos"]))}</text>
  <text x="20" y="292" font-family="{FM}" font-size="9.5" letter-spacing="1" fill="{CREAM}" fill-opacity="0.62">ORIGINAL, NON-FORK</text>

  <rect x="253" y="179" width="242" height="130" rx="12" fill="url(#crimsonCard)" stroke="#87100F" stroke-width="1.5" />
  <text x="272" y="205" font-family="{FM}" font-size="10.5" font-weight="700" letter-spacing="1.2" fill="{CREAM}" fill-opacity="0.88">TOTAL STARS</text>
  <text x="272" y="260" font-family="{FH}" font-size="44" font-weight="900" letter-spacing="-2" fill="{CREAM}">{esc(num(d["stars"]))}</text>
  <text x="272" y="292" font-family="{FM}" font-size="9.5" letter-spacing="1" fill="{CREAM}" fill-opacity="0.78">ACROSS PUBLIC REPOS</text>

  <rect x="505" y="179" width="242" height="130" rx="12" fill="url(#darkCard)" stroke="#5C0908" stroke-width="1.5" />
  <text x="524" y="205" font-family="{FM}" font-size="10.5" font-weight="700" letter-spacing="1.2" fill="{ACC}">FOLLOWERS</text>
  <text x="524" y="260" font-family="{FH}" font-size="44" font-weight="900" letter-spacing="-2" fill="{CREAM}">{esc(num(d["followers"]))}</text>
  <text x="524" y="292" font-family="{FM}" font-size="9.5" letter-spacing="1" fill="{CREAM}" fill-opacity="0.62">ON GITHUB</text>

  <rect x="757" y="179" width="242" height="130" rx="12" fill="{CREAM}" stroke="{CREAM}" stroke-width="1.5" />
  <text x="776" y="205" font-family="{FM}" font-size="10.5" font-weight="700" letter-spacing="1.2" fill="{RED}">TOP LANGUAGE</text>
  <text x="776" y="254" font-family="{FH}" font-size="{top_fs}" font-weight="900" letter-spacing="-1" fill="{RED}">{esc(top)}</text>
  <text x="776" y="292" font-family="{FM}" font-size="9.5" font-weight="700" letter-spacing="1" fill="{DEEP}">MOST CODE WRITTEN</text>
</svg>
'''
    with open(os.path.join(OUT, "stats-metrics.svg"), "w", encoding="utf-8") as f:
        f.write(svg)


def write_langs(d, updated):
    w, h = 1000, 150
    langs = d["langs"]
    parts = []
    if not langs:
        parts.append(f'<text x="24" y="86" font-family="{FM}" font-size="12" fill="{CREAM}" fill-opacity="0.7">NO LANGUAGE DATA YET</text>')
    else:
        x, bw, gap = 24, w - 48, 3
        usable = bw - gap * (len(langs) - 1)
        for i, (name, pct) in enumerate(langs):
            sw = max(usable * pct / 100, 4)
            col = "#8A7D70" if name == "Other" else SEG[i % len(SEG)]
            parts.append(f'<rect x="{x:.1f}" y="52" width="{sw:.1f}" height="24" fill="{col}"/>')
            x += sw + gap
        lx = 24
        for i, (name, pct) in enumerate(langs):
            col = "#8A7D70" if name == "Other" else SEG[i % len(SEG)]
            label = f"{name.upper()} {pct:.1f}%"
            parts.append(f'<rect x="{lx}" y="96" width="12" height="12" fill="{col}" stroke="{CREAM}" stroke-opacity="0.4"/>'
                         f'<text x="{lx + 20}" y="106" font-family="{FM}" font-size="11.5" font-weight="700" letter-spacing="0.8" fill="{CREAM}">{esc(label)}</text>')
            lx += 20 + len(label) * 7.6 + 26

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Top languages by code size">
  <defs>
    <radialGradient id="langBg" cx="50%" cy="50%" r="85%">
      <stop offset="0%" stop-color="#240404" />
      <stop offset="100%" stop-color="#120202" />
    </radialGradient>
  </defs>
  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12" fill="url(#langBg)" stroke="#5C0908" stroke-width="1.5" />
  <text x="24" y="34" font-family="{FM}" font-size="11" font-weight="700" letter-spacing="2" fill="{ACC}">TOP LANGUAGES // BY CODE SIZE</text>
  <text x="{w - 24}" y="34" text-anchor="end" font-family="{FM}" font-size="10" letter-spacing="1.4" fill="{CREAM}" fill-opacity="0.5">UPDATED {updated} UTC</text>
{chr(10).join(parts)}
  <line x1="1" y1="{h - 24}" x2="{w - 1}" y2="{h - 24}" stroke="{CREAM}" stroke-opacity="0.14"/>
  <text x="24" y="{h - 8}" font-family="{FM}" font-size="9.5" letter-spacing="1.6" fill="{CREAM}" fill-opacity="0.45">PUBLIC, NON-FORK REPOSITORIES ONLY</text>
</svg>
'''
    with open(os.path.join(OUT, "stats-langs.svg"), "w", encoding="utf-8") as f:
        f.write(svg)


def wrap_snake(src_name, dst_name, is_dark=True):
    src_path = os.path.join(OUT, src_name)
    if not os.path.exists(src_path):
        return
    with open(src_path, "r", encoding="utf-8") as f:
        raw = f.read()

    vb_m = re.search(r'viewBox="([^"]+)"', raw)
    vb = vb_m.group(1) if vb_m else "-16 -32 880 192"

    inner = re.sub(r'^.*?<svg[^>]*>', '', raw, flags=re.S)
    inner = re.sub(r'</svg>\s*$', '', inner, flags=re.S)

    bg_c1 = "#240404" if is_dark else "#F5EFE6"
    bg_c2 = "#120202" if is_dark else "#EAE0D0"
    stroke_col = "#5C0908" if is_dark else "#87100F"
    title_col = "#E63946" if is_dark else "#87100F"
    sub_col = "#F5EFE6" if is_dark else "#5C0908"
    dots = ["#241010", "#5C0908", "#872020", "#B33A39", "#E06B69"] if is_dark else ["#E8DDCB", "#D9908F", "#B33A39", "#872020", "#5C0908"]

    framed_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="240" viewBox="0 0 1000 240" role="img" aria-label="Contribution Snake">
  <defs>
    <radialGradient id="sBg" cx="50%" cy="50%" r="85%">
      <stop offset="0%" stop-color="{bg_c1}" />
      <stop offset="100%" stop-color="{bg_c2}" />
    </radialGradient>
  </defs>

  <rect x="1" y="1" width="998" height="238" rx="12" fill="url(#sBg)" stroke="{stroke_col}" stroke-width="1.5" />

  <text x="24" y="28" font-family="{FM}" font-size="11" font-weight="700" letter-spacing="1.5" fill="{title_col}">[ CONTRIBUTION SNAKE // 52 WEEKS ]</text>
  <text x="976" y="28" text-anchor="end" font-family="{FM}" font-size="10" letter-spacing="1.2" fill="{sub_col}" fill-opacity="0.55">LIVE ACTIVITY FEED</text>
  <line x1="24" y1="40" x2="976" y2="40" stroke="{sub_col}" stroke-opacity="0.14" />

  <svg x="24" y="46" width="952" height="154" viewBox="{vb}" preserveAspectRatio="xMidYMid meet">
{inner}
  </svg>

  <line x1="24" y1="208" x2="976" y2="208" stroke="{sub_col}" stroke-opacity="0.14" />
  <text x="24" y="225" font-family="{FM}" font-size="9.5" letter-spacing="1.2" fill="{sub_col}" fill-opacity="0.55">AUTO-GENERATED VIA GITHUB ACTIONS</text>

  <g transform="translate(835, 216)">
    <text x="-38" y="9" font-family="{FM}" font-size="9" fill="{sub_col}" fill-opacity="0.55">LESS</text>
    <rect x="0" y="0" width="10" height="10" rx="2" fill="{dots[0]}" stroke="{stroke_col}" stroke-width="0.5" />
    <rect x="15" y="0" width="10" height="10" rx="2" fill="{dots[1]}" />
    <rect x="30" y="0" width="10" height="10" rx="2" fill="{dots[2]}" />
    <rect x="45" y="0" width="10" height="10" rx="2" fill="{dots[3]}" />
    <rect x="60" y="0" width="10" height="10" rx="2" fill="{dots[4]}" />
    <text x="78" y="9" font-family="{FM}" font-size="9" fill="{sub_col}" fill-opacity="0.55">MORE</text>
  </g>
</svg>
'''
    with open(os.path.join(OUT, dst_name), "w", encoding="utf-8") as f:
        f.write(framed_svg)


def main():
    d = collect()
    updated = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
    write_metrics(d)
    write_langs(d, updated)
    wrap_snake("snake-dark.svg", "snake-framed-dark.svg", is_dark=True)
    wrap_snake("snake-light.svg", "snake-framed-light.svg", is_dark=False)
    print("All framed stats and snakes written to", OUT)


main()