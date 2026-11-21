#!/usr/bin/env python3
"""Generate brutalist GitHub stats tiles (SVG) from the GitHub GraphQL API.

Usage:  python3 stats.py <out_dir>          (needs env GH_TOKEN and LOGIN)
        python3 stats.py <out_dir> --mock   (sample data, for previewing)

Every tile in a row has the same scale: viewBox width = (percent width in README) * 10.
"""
import json, os, sys, datetime, urllib.request

OUT = sys.argv[1]
MOCK = "--mock" in sys.argv
os.makedirs(OUT, exist_ok=True)

CREAM, RED, ACC, DEEP = "#F5EFE6", "#87100F", "#E63946", "#7A0E0D"
FH = "'Helvetica Neue', 'Arial Black', Helvetica, Arial, sans-serif"
FM = "'Courier New', Courier, monospace"
SEG = ["#F5EFE6", "#E63946", "#B33A39", "#87100F", "#5C0908"]  # language bar palette


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;")


# ------------------------------------------------------------------ data
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
    if tail and tail[-1] == 0:  # today may not have a contribution yet
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
    except Exception as e:  # keep going, tiles fall back to dashes
        print("stats fetch failed:", e, file=sys.stderr)
    return d


def num(v):
    return "—" if v is None else f"{v:,}"


# ------------------------------------------------------------------ svg
def tile(fname, w, h, kind, body, label, uid, rx=6):
    bg = {"crimson": f"url(#c{uid})", "dark": f"url(#d{uid})", "cream": CREAM}[kind]
    border = {"crimson": f'stroke="{CREAM}" stroke-opacity="0.35" stroke-width="1.5"',
              "dark": f'stroke="{RED}" stroke-width="1.5"',
              "cream": 'stroke="none"'}[kind]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">
  <defs>
    <radialGradient id="c{uid}" cx="45%" cy="40%" r="90%"><stop offset="0" stop-color="#A81918"/><stop offset="0.65" stop-color="#87100F"/><stop offset="1" stop-color="#5C0908"/></radialGradient>
    <radialGradient id="d{uid}" cx="30%" cy="40%" r="90%"><stop offset="0" stop-color="#2A0505"/><stop offset="1" stop-color="#140202"/></radialGradient>
    <clipPath id="p{uid}"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>
  </defs>
  <g clip-path="url(#p{uid})">
    <rect width="{w}" height="{h}" fill="{bg}"/>
{body}
  </g>
  <rect x="0.75" y="0.75" width="{w - 1.5}" height="{h - 1.5}" rx="{rx}" fill="none" {border}/>
</svg>
'''
    with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
        f.write(svg)


def big_tile(fname, uid, w, h, kind, label, value, sub, fs):
    c_text = DEEP if kind == "cream" else CREAM
    c_lab = DEEP if kind == "cream" else (ACC if kind == "dark" else CREAM)
    lab_op = "1" if kind != "crimson" else "0.8"
    small = h < 140
    ly = 28 if small else 34
    div = h - (34 if small else 38)
    vy = div - (13 if small else 14)
    sy = h - (12 if small else 14)
    body = f'''
    <line x1="0" y1="{div}" x2="{w}" y2="{div}" stroke="{c_text}" stroke-opacity="0.18"/>
    <text x="22" y="{ly}" font-family="{FM}" font-size="11" font-weight="700" letter-spacing="2" fill="{c_lab}" fill-opacity="{lab_op}">{esc(label)}</text>
    <text x="20" y="{vy}" font-family="{FH}" font-size="{fs}" font-weight="800" letter-spacing="{-fs * 0.045:.1f}" fill="{c_text}">{esc(value)}</text>
    <text x="22" y="{sy}" font-family="{FM}" font-size="10.5" letter-spacing="1.4" fill="{c_text}" fill-opacity="0.7">{esc(sub)}</text>'''
    tile(fname, w, h, kind, body, f"{label}: {value}", uid)


def langs_tile(d, updated):
    w, h = 980, 150
    langs = d["langs"]
    parts = []
    if not langs:
        parts.append(f'<text x="22" y="86" font-family="{FM}" font-size="12" fill="{CREAM}" fill-opacity="0.7">NO LANGUAGE DATA YET</text>')
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
    body = f'''
    <text x="24" y="34" font-family="{FM}" font-size="11" font-weight="700" letter-spacing="2" fill="{ACC}">TOP LANGUAGES // BY CODE SIZE</text>
    <text x="{w - 24}" y="34" text-anchor="end" font-family="{FM}" font-size="10" letter-spacing="1.4" fill="{CREAM}" fill-opacity="0.5">UPDATED {updated} UTC</text>
{chr(10).join(parts)}
    <line x1="0" y1="{h - 24}" x2="{w}" y2="{h - 24}" stroke="{CREAM}" stroke-opacity="0.14"/>
    <text x="24" y="{h - 8}" font-family="{FM}" font-size="9.5" letter-spacing="1.6" fill="{CREAM}" fill-opacity="0.45">PUBLIC, NON-FORK REPOSITORIES ONLY</text>'''
    tile("stats-langs.svg", w, h, "dark", body, "Top languages by code size", 20)


def main():
    d = collect()
    updated = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")

    # row 1 (h=176): widths 380 / 300 / 300
    big_tile("stats-contrib.svg", 11, 380, 176, "crimson", "[ CONTRIBUTIONS ]", num(d["total"]),
             "LAST 12 MONTHS // ALL ACTIVITY", 86)
    big_tile("stats-streak.svg", 12, 300, 176, "dark", "CURRENT STREAK", num(d["cur"]),
             "DAYS IN A ROW", 86)
    big_tile("stats-longest.svg", 13, 300, 176, "cream", "LONGEST STREAK", num(d["longest"]),
             "DAYS // LAST 12 MONTHS", 86)

    # row 2 (h=118): four tiles of 240
    big_tile("stats-repos.svg", 14, 240, 118, "dark", "PUBLIC REPOS", num(d["repos"]), "ORIGINAL, NON-FORK", 44)
    big_tile("stats-stars.svg", 15, 240, 118, "crimson", "TOTAL STARS", num(d["stars"]), "ACROSS PUBLIC REPOS", 44)
    big_tile("stats-followers.svg", 16, 240, 118, "dark", "FOLLOWERS", num(d["followers"]), "ON GITHUB", 44)
    top = d["langs"][0][0].upper() if d["langs"] else "—"
    fs = max(20, min(38, int(196 / (max(len(top), 1) * 0.64))))
    big_tile("stats-toplang.svg", 17, 240, 118, "cream", "TOP LANGUAGE", top, "MOST CODE WRITTEN", fs)

    # row 3
    langs_tile(d, updated)
    print("stats tiles written to", OUT)


main()
