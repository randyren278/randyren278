#!/usr/bin/env python3
"""Render the Rosé Pine neofetch-style profile card as a single SVG.

Runs inside the daily GitHub Action. Everything here is a real image, so it
carries actual color — sidesteps GitHub's markdown/HTML style-stripping that
made the old <pre> + shields-badge version render in default gray.
"""
import argparse
import base64
import calendar
import datetime
import html
import textwrap
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")

ROSEPINE = {
    "bg": "#191724",
    "ink": "#e0def4",
    "accent": "#c4a7e7",
    "dim": "#908caa",
    "swatches": ["#1f1d2e", "#eb6f92", "#9ccfd8", "#f6c177", "#31748f", "#c4a7e7", "#ebbcba", "#e0def4"],
}

BIRTHDATE = datetime.date(2005, 9, 17)


def age_parts(birth, today):
    years = today.year - birth.year
    months = today.month - birth.month
    days = today.day - birth.day
    if days < 0:
        months -= 1
        prev_month = today.month - 1 or 12
        prev_year = today.year if today.month > 1 else today.year - 1
        days += calendar.monthrange(prev_year, prev_month)[1]
    if months < 0:
        years -= 1
        months += 12
    return years, months, days


def uptime_string():
    today = datetime.datetime.now(PACIFIC).date()
    y, m, d = age_parts(BIRTHDATE, today)
    parts = []
    parts.append(f"{y} year{'s' if y != 1 else ''}")
    parts.append(f"{m} month{'s' if m != 1 else ''}")
    parts.append(f"{d} day{'s' if d != 1 else ''}")
    return ", ".join(parts)


def esc(s):
    return html.escape(str(s), quote=True)


def build_svg(args):
    c = ROSEPINE
    photo_b64 = base64.b64encode(open(args.photo, "rb").read()).decode("ascii")

    W = 1060
    PAD = 26
    PHOTO = 240
    photo_x = PAD
    text_x = photo_x + PHOTO + 32
    text_w = W - text_x - PAD

    rows = [
        ("who", args.name, None),
        ("rule", "─" * 44, None),
        ("kv", "Role", args.role),
        ("kv", "Focus", args.focus),
        ("kv", "Editor", args.editor),
        ("kv", "Site", args.site),
        ("kv", "Uptime", uptime_string()),
        ("gap", "", None),
        ("rule-label", "GitHub Stats", None),
        ("kv", "Commits", f"{args.commits:,} (all-time, incl. private)"),
        ("kv", "Lines", f"{args.loc_add + args.loc_del:,}  (+{args.loc_add:,} / -{args.loc_del:,})"),
    ]

    line_h = 24
    y = PAD + 6
    svg_rows = []
    key_col = 108
    # deliberately generous monospace char-width estimate at 15px — better to wrap
    # a little early than risk clipping if the viewer's font substitution is wider
    CHAR_W = 16
    value_w = text_x + text_w - (text_x + key_col)
    max_chars = max(10, int(value_w / CHAR_W))

    for kind, a, b in rows:
        if kind == "who":
            svg_rows.append(f'<text x="{text_x}" y="{y}" font-weight="700" font-size="17" fill="{c["ink"]}" font-family="ui-monospace,Menlo,Consolas,monospace">{esc(a)}</text>')
            y += line_h + 4
        elif kind == "rule":
            svg_rows.append(f'<text x="{text_x}" y="{y}" font-size="15" fill="{c["accent"]}" font-family="ui-monospace,Menlo,Consolas,monospace">{esc(a)}</text>')
            y += line_h + 6
        elif kind == "kv":
            svg_rows.append(f'<text x="{text_x}" y="{y}" font-size="15" fill="{c["accent"]}" font-family="ui-monospace,Menlo,Consolas,monospace">{esc(a)}</text>')
            wrapped = textwrap.wrap(str(b), width=max_chars) or [""]
            for i, line in enumerate(wrapped):
                svg_rows.append(f'<text x="{text_x + key_col}" y="{y}" font-size="15" fill="{c["dim"]}" font-family="ui-monospace,Menlo,Consolas,monospace">{esc(line)}</text>')
                if i < len(wrapped) - 1:
                    y += line_h
            y += line_h
        elif kind == "gap":
            y += line_h * 0.5
        elif kind == "rule-label":
            svg_rows.append(f'<text x="{text_x}" y="{y}" font-size="14" fill="{c["accent"]}" font-family="ui-monospace,Menlo,Consolas,monospace">{esc(a)}</text>')
            y += line_h + 4

    # palette swatch strip
    sw_w, sw_h, sw_gap = 34, 18, 4
    sw_y = y + 6
    swatch_svg = []
    for i, hexcolor in enumerate(c["swatches"]):
        sw_x = text_x + i * (sw_w + sw_gap)
        swatch_svg.append(f'<rect x="{sw_x}" y="{sw_y}" width="{sw_w}" height="{sw_h}" rx="2" fill="{hexcolor}"/>')

    content_bottom = sw_y + sw_h + PAD
    H = max(PHOTO + 2 * PAD, content_bottom)
    photo_y = (H - PHOTO) // 2

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <clipPath id="photoClip">
      <rect x="{photo_x}" y="{photo_y}" width="{PHOTO}" height="{PHOTO}" rx="10"/>
    </clipPath>
    <clipPath id="cardClip">
      <rect x="0" y="0" width="{W}" height="{H}" rx="14"/>
    </clipPath>
  </defs>
  <g clip-path="url(#cardClip)">
    <rect x="0" y="0" width="{W}" height="{H}" fill="{c["bg"]}"/>
    <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{c["swatches"][0]}" stroke-width="1"/>
    <image href="data:image/jpeg;base64,{photo_b64}" x="{photo_x}" y="{photo_y}" width="{PHOTO}" height="{PHOTO}" clip-path="url(#photoClip)" preserveAspectRatio="xMidYMid slice"/>
    {''.join(svg_rows)}
    {''.join(swatch_svg)}
  </g>
</svg>'''
    return svg


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--photo", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--focus", required=True)
    p.add_argument("--editor", required=True)
    p.add_argument("--site", required=True)
    p.add_argument("--commits", type=int, required=True)
    p.add_argument("--loc-add", type=int, required=True)
    p.add_argument("--loc-del", type=int, required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    svg = build_svg(args)
    with open(args.out, "w") as f:
        f.write(svg)
    print(f"wrote {args.out} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
