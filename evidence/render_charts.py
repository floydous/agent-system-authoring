#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pillow>=10.0",
# ]
# ///
"""Render taste-skill minimal dark/light README benchmark charts from raw traces.

Applies Leonxlnx/taste-skill developer-tool principles:
- Geist + Geist Mono typography (500 display weight, -0.035em tracking, >= 13px floor)
- 90-95% neutral ground and ink (Sheet and biro light / Night and sky blue dark)
- Zero violet/lavender, zero neon blurs, zero nested box-in-box tiles, sharp 4/6px radius
- Plain factual sentence-case copy (zero virtue words or tracked all-caps eyebrows)
- Exact cross-model min-max ranges computed directly from bundled raw JSONL traces

Usage:
    python -B evidence/render_charts.py
"""
from __future__ import annotations

import html
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = ROOT / "evidence"
OUT_DIR = EVIDENCE_DIR / "charts"


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _mean_metric(path: Path, condition: str, key: str = "score") -> float:
    rows = [r for r in _load_jsonl(path) if r.get("condition") == condition]
    if not rows:
        raise ValueError(f"No rows for {condition!r} in {path}")
    by_prompt: dict[str, list[float]] = {}
    for r in rows:
        v = r.get(key)
        if v is None and isinstance(r.get("metrics"), dict):
            v = r["metrics"].get(key)
        if v is None:
            raise KeyError(f"Metric {key!r} missing in {path} ({condition})")
        pid = str(r.get("prompt_id", len(by_prompt)))
        by_prompt.setdefault(pid, []).append(float(v))
    prompt_means = [sum(vs) / len(vs) for vs in by_prompt.values()]
    return sum(prompt_means) / len(prompt_means)


def _pct(path: Path, cond: str, key: str = "score") -> float:
    return _mean_metric(path, cond, key) * 100.0


def _round_half_up(v: float) -> int:
    return int(v + 0.5)


def _fmt_range(lo: float, hi: float) -> str:
    a, b = _round_half_up(lo), _round_half_up(hi)
    return f"{a}%" if a == b else f"{a}–{b}%"


def collect_verified_metrics() -> dict:
    """Compute exact min-max cross-model ranges directly from raw JSONL traces."""
    p = {
        "ling": EVIDENCE_DIR / "raw_phase_f_ling",
        "nemo": EVIDENCE_DIR / "raw_phase_f_nemo",
        "h08": EVIDENCE_DIR / "raw_h08_particle1",
        "pe": EVIDENCE_DIR / "raw_phase_e",
        "pd": EVIDENCE_DIR / "raw_phase_d",
        "pc": EVIDENCE_DIR / "raw_phase_c",
        "pb": EVIDENCE_DIR / "raw_phase_b",
    }

    def band(pairs: list[tuple[Path, str, str]]) -> tuple[float, float]:
        vals = [_pct(path, cond, key) for path, cond, key in pairs]
        return min(vals), max(vals)

    ts_drops = []
    for path in (
        p["ling"] / "results_LING-PD5.jsonl",
        p["pd"] / "results_PD-5.jsonl",
        p["h08"] / "results_H08-PD5.jsonl",
    ):
        j = _mean_metric(path, "json_schema", "prompt_tokens")
        ts = _mean_metric(path, "typescript_interface", "prompt_tokens")
        ts_drops.append((j - ts) / j * 100.0)

    rt_drops = []
    for path in (
        p["nemo"] / "results_NEMO-PD1.jsonl",
        p["h08"] / "results_H08-PD1.jsonl",
        p["pd"] / "results_PD-1.jsonl",
        p["ling"] / "results_LING-PD1.jsonl",
    ):
        wo = _mean_metric(path, "without_descriptions", "reasoning_tokens")
        wi = _mean_metric(path, "with_descriptions", "reasoning_tokens")
        rt_drops.append((wo - wi) / wo * 100.0)

    return {
        "rows": [
            {
                "title": "Parameter descriptions",
                "sub": "Valid argument formats",
                "tone": "gain",
                "before": band([
                    (p["pd"] / "results_PD-1.jsonl", "without_descriptions", "score"),
                    (p["ling"] / "results_LING-PD1.jsonl", "without_descriptions", "score"),
                    (p["h08"] / "results_H08-PD1.jsonl", "without_descriptions", "score"),
                    (p["nemo"] / "results_NEMO-PD1.jsonl", "without_descriptions", "score"),
                ]),
                "after": band([
                    (p["pd"] / "results_PD-1.jsonl", "with_descriptions", "score"),
                    (p["ling"] / "results_LING-PD1.jsonl", "with_descriptions", "score"),
                    (p["h08"] / "results_H08-PD1.jsonl", "with_descriptions", "score"),
                    (p["nemo"] / "results_NEMO-PD1.jsonl", "with_descriptions", "score"),
                ]),
            },
            {
                "title": "Assertive tool hype",
                "sub": "Wrong-tool hijack rate",
                "tone": "risk",
                "before": band([
                    (p["pc"] / "results_PC-1.jsonl", "neutral", "score"),
                    (p["ling"] / "results_LING-PC1.jsonl", "neutral", "score"),
                    (p["nemo"] / "results_NEMO-PC1.jsonl", "neutral", "score"),
                    (p["h08"] / "results_H08-PC1.jsonl", "neutral", "score"),
                ]),
                "after": band([
                    (p["pc"] / "results_PC-1.jsonl", "assertive_on_second", "score"),
                    (p["ling"] / "results_LING-PC1.jsonl", "assertive_on_second", "score"),
                    (p["nemo"] / "results_NEMO-PC1.jsonl", "assertive_on_second", "score"),
                    (p["h08"] / "results_H08-PC1.jsonl", "assertive_on_second", "score"),
                ]),
            },
            {
                "title": "In-schema rationale first",
                "sub": "Accuracy with thinking off",
                "tone": "gain",
                "before": band([
                    (p["nemo"] / "results_NEMO-PB6.jsonl", "no_rationale", "score"),
                    (p["ling"] / "results_LING-PB6.jsonl", "no_rationale", "score"),
                    (p["pb"] / "results_PB-6.jsonl", "no_rationale", "score"),
                ]),
                "after": band([
                    (p["nemo"] / "results_NEMO-PB6.jsonl", "rationale_first", "score"),
                    (p["ling"] / "results_LING-PB6.jsonl", "rationale_first", "score"),
                    (p["pb"] / "results_PB-6.jsonl", "rationale_first", "score"),
                ]),
            },
            {
                "title": "50 rules vs. 5–10 rules",
                "sub": "Strict all-rules pass rate",
                "tone": "risk",
                "before": band([
                    (p["ling"] / "results_LING-PE1.jsonl", "rules_05", "strict_all"),
                    (p["pe"] / "results_PE-1.jsonl", "rules_10", "strict_all"),
                ]),
                "after": band([
                    (p["ling"] / "results_LING-PE1.jsonl", "rules_50", "strict_all"),
                    (p["pe"] / "results_PE-1.jsonl", "rules_50", "strict_all"),
                ]),
            },
            {
                "title": "Explicit word bans",
                "sub": "Clean output vs. hints",
                "tone": "gain",
                "before": band([
                    (p["h08"] / "results_H08-PC2.jsonl", "affirmative_only", "lexical_clean"),
                    (p["nemo"] / "results_NEMO-PC2.jsonl", "affirmative_only", "lexical_clean"),
                    (p["pc"] / "results_PC-2.jsonl", "affirmative_only", "lexical_clean"),
                    (p["ling"] / "results_LING-PC2.jsonl", "affirmative_only", "lexical_clean"),
                ]),
                "after": band([
                    (p["h08"] / "results_H08-PC2.jsonl", "bare_negative", "lexical_clean"),
                    (p["nemo"] / "results_NEMO-PC2.jsonl", "bare_negative", "lexical_clean"),
                    (p["pc"] / "results_PC-2.jsonl", "bare_negative", "lexical_clean"),
                    (p["ling"] / "results_LING-PC2.jsonl", "bare_negative", "lexical_clean"),
                ]),
            },
        ],
        "ts_drop": (min(ts_drops), max(ts_drops)),
        "rt_drop": (min(rt_drops), max(rt_drops)),
    }


# Authentic Leonxlnx/taste-skill developer-tool palettes:
# - light: "Sheet and biro" (#ffffff ground, #111111 ink, #6b6b6b muted, #1a4be0 accent)
# - dark: "Night and sky blue" (#0d1117 GitHub ground, #e9edf3 ink, #8891a1 muted, #5ab9fc accent)
THEMES = {
    "dark": {
        "page_bg": "#0D1117",
        "card_bg": "#0D1117",
        "line": "rgba(233, 237, 243, 0.12)",
        "line_strong": "rgba(233, 237, 243, 0.22)",
        "ink": "#E9EDF3",
        "muted": "#8891A1",
        "base_fill": "#0D1117",
        "base_stroke": "#8891A1",
        "gain": "#5AB9FC",
        "gain_text": "#79C7FF",
        "risk": "#E5534B",
        "risk_text": "#F47067",
    },
    "light": {
        "page_bg": "#FFFFFF",
        "card_bg": "#FFFFFF",
        "line": "rgba(17, 17, 17, 0.12)",
        "line_strong": "rgba(17, 17, 17, 0.22)",
        "ink": "#111111",
        "muted": "#6B6B6B",
        "base_fill": "#FFFFFF",
        "base_stroke": "#6B6B6B",
        "gain": "#1A4BE0",
        "gain_text": "#1A4BE0",
        "risk": "#C2352B",
        "risk_text": "#B92B22",
    },
}


def _build_dumbbell_svg(rows: list[dict], t: dict) -> str:
    """Render one crisp architectural SVG plot with sharp 4px range bars and 1px hairlines."""
    w = 604
    pad_l = 78
    pad_r = 84
    span = w - pad_l - pad_r
    axis_h = 30
    row_h = 64
    h = axis_h + len(rows) * row_h
    font_mono = "'Geist Mono', 'JetBrains Mono', 'Cascadia Mono', monospace"

    def x_of(v: float) -> float:
        return pad_l + (v / 100.0) * span

    parts = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="display:block;overflow:visible;">']

    # Scale labels (>= 13px) and clean dashed/solid rules (matching taste-skill fx-bars/fx-chart)
    for tick in (0, 25, 50, 75, 100):
        tx = x_of(tick)
        stroke = t["line_strong"] if tick in (0, 100) else t["line"]
        dash = "" if tick in (0, 100) else ' stroke-dasharray="3 4"'
        parts.append(
            f'<text x="{tx:.1f}" y="16" text-anchor="middle" font-family="{font_mono}" '
            f'font-size="13" font-weight="400" fill="{t["muted"]}">{tick}%</text>'
        )
        parts.append(
            f'<line x1="{tx:.1f}" y1="{axis_h}" x2="{tx:.1f}" y2="{h}" '
            f'stroke="{stroke}" stroke-width="1"{dash}/>'
        )

    for idx, row in enumerate(rows):
        y_top = axis_h + idx * row_h
        cy = y_top + row_h / 2.0
        b_lo, b_hi = row["before"]
        a_lo, a_hi = row["after"]
        tone = row["tone"]
        col = t[tone]
        col_txt = t[f"{tone}_text"]
        is_right = (a_lo + a_hi) >= (b_lo + b_hi)

        # Continuous horizontal hairline closing each row (taste-skill .rows recipe)
        parts.append(
            f'<line x1="0" y1="{y_top:.1f}" x2="{w}" y2="{y_top:.1f}" '
            f'stroke="{t["line"]}" stroke-width="1"/>'
        )

        bx0, bx1 = x_of(b_lo), x_of(b_hi)
        ax0, ax1 = x_of(a_lo), x_of(a_hi)

        # Sharp 4px architectural bars (min width 10px for single-point values)
        half_h = 5.0
        rx = 3.0
        b_left, b_right = bx0 - half_h, bx1 + half_h
        a_left, a_right = ax0 - half_h, ax1 + half_h

        if is_right:
            s_start = b_right + 3.0
            s_end = a_left - 5.0
            tip_x = a_left - 3.5
            wing_x = tip_x - 6.5
        else:
            s_start = b_left - 3.0
            s_end = a_right + 5.0
            tip_x = a_right + 3.5
            wing_x = tip_x + 6.5

        parts.append(
            f'<line x1="{s_start:.1f}" y1="{cy:.1f}" x2="{s_end:.1f}" y2="{cy:.1f}" '
            f'stroke="{col}" stroke-width="2" stroke-linecap="round"/>'
        )
        parts.append(
            f'<polyline points="{wing_x:.1f},{cy - 4.2:.1f} {tip_x:.1f},{cy:.1f} {wing_x:.1f},{cy + 4.2:.1f}" '
            f'fill="none" stroke="{col}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        )

        # Baseline hollow bar (flat ground fill + muted ink stroke, zero tint/blur)
        parts.append(
            f'<rect x="{b_left:.1f}" y="{cy - half_h:.1f}" '
            f'width="{b_right - b_left:.1f}" height="{2 * half_h:.1f}" '
            f'rx="{rx}" fill="{t["base_fill"]}" stroke="{t["base_stroke"]}" stroke-width="1.75"/>'
        )

        # Intervention solid bar (flat ink/accent, zero neon halo)
        parts.append(
            f'<rect x="{a_left:.1f}" y="{cy - half_h:.1f}" '
            f'width="{a_right - a_left:.1f}" height="{2 * half_h:.1f}" '
            f'rx="{rx}" fill="{col}"/>'
        )

        # Direct endpoint labels (>= 13px Geist Mono, always outside bars -> zero collisions)
        b_label = _fmt_range(b_lo, b_hi)
        a_label = _fmt_range(a_lo, a_hi)
        if is_right:
            parts.append(
                f'<text x="{b_left - 10:.1f}" y="{cy + 4.5:.1f}" text-anchor="end" '
                f'font-family="{font_mono}" font-size="13.5" font-weight="400" fill="{t["muted"]}">{b_label}</text>'
            )
            parts.append(
                f'<text x="{a_right + 10:.1f}" y="{cy + 4.5:.1f}" text-anchor="start" '
                f'font-family="{font_mono}" font-size="13.5" font-weight="500" fill="{col_txt}">{a_label}</text>'
            )
        else:
            parts.append(
                f'<text x="{a_left - 10:.1f}" y="{cy + 4.5:.1f}" text-anchor="end" '
                f'font-family="{font_mono}" font-size="13.5" font-weight="500" fill="{col_txt}">{a_label}</text>'
            )
            parts.append(
                f'<text x="{b_right + 10:.1f}" y="{cy + 4.5:.1f}" text-anchor="start" '
                f'font-family="{font_mono}" font-size="13.5" font-weight="400" fill="{t["muted"]}">{b_label}</text>'
            )

    # Bottom hairline closing final row
    parts.append(f'<line x1="0" y1="{h}" x2="{w}" y2="{h}" stroke="{t["line"]}" stroke-width="1"/>')
    parts.append("</svg>")
    return "".join(parts)


def render_html(data: dict, theme_name: str) -> str:
    t = THEMES[theme_name]
    rows = data["rows"]
    svg = _build_dumbbell_svg(rows, t)

    labels_html = []
    for row in rows:
        labels_html.append(
            f'<div class="row-label">'
            f'  <div class="row-title">{html.escape(row["title"])}</div>'
            f'  <div class="row-sub">{html.escape(row["sub"])}</div>'
            f'</div>'
        )

    ts_lo, ts_hi = data["ts_drop"]
    rt_lo, rt_hi = data["rt_drop"]
    ts_range = f"{_round_half_up(ts_lo)}–{_round_half_up(ts_hi)}%"
    rt_range = f"{_round_half_up(rt_lo)}–{_round_half_up(rt_hi)}%"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: 920px;
    background: {t["page_bg"]};
    color: {t["ink"]};
    font-family: 'Geist', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    -webkit-font-smoothing: antialiased;
    font-variant-numeric: tabular-nums;
  }}
  .frame {{
    width: 920px;
    padding: 16px;
    background: {t["page_bg"]};
  }}
  .sheet {{
    background: {t["card_bg"]};
    border: 1px solid {t["line"]};
    border-radius: 6px;
    padding: 36px 36px 28px 36px;
  }}
  h1 {{
    font-size: 24px;
    font-weight: 500;
    letter-spacing: -0.035em;
    line-height: 1.22;
    color: {t["ink"]};
    white-space: nowrap;
  }}
  h1 .muted {{
    color: {t["muted"]};
    font-weight: 400;
  }}
  .legend {{
    display: flex;
    align-items: center;
    gap: 24px;
    margin-top: 20px;
    margin-bottom: 22px;
    font-size: 13px;
    font-weight: 500;
    color: {t["muted"]};
  }}
  .leg-item {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }}
  .leg-bar-base {{
    width: 18px;
    height: 10px;
    border-radius: 3px;
    background: {t["base_fill"]};
    border: 1.75px solid {t["base_stroke"]};
    display: inline-block;
  }}
  .leg-bar-solid {{
    width: 18px;
    height: 10px;
    border-radius: 3px;
    display: inline-block;
  }}
  .leg-right {{
    margin-left: auto;
    font-weight: 400;
  }}
  .chart-grid {{
    display: grid;
    grid-template-columns: 210px 604px;
    column-gap: 0;
    align-items: start;
  }}
  .label-col {{
    padding-top: 30px;
  }}
  .row-label {{
    height: 64px;
    padding-right: 14px;
    border-top: 1px solid {t["line"]};
    display: flex;
    flex-direction: column;
    justify-content: center;
  }}
  .row-label:last-child {{
    border-bottom: 1px solid {t["line"]};
  }}
  .row-title {{
    font-size: 15.5px;
    font-weight: 500;
    letter-spacing: -0.015em;
    color: {t["ink"]};
    line-height: 1.25;
  }}
  .row-sub {{
    font-size: 13px;
    color: {t["muted"]};
    margin-top: 3px;
    line-height: 1.25;
  }}
  .notes-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    margin-top: 28px;
  }}
  .note-col {{
    padding-right: 20px;
  }}
  .note-col + .note-col {{
    padding-left: 20px;
    border-left: 1px solid {t["line"]};
  }}
  .note-col:last-child {{
    padding-right: 0;
  }}
  .note-head {{
    font-size: 15.5px;
    font-weight: 600;
    letter-spacing: -0.015em;
    color: {t["ink"]};
    margin-bottom: 6px;
  }}
  .note-head .num {{
    font-family: 'Geist Mono', 'JetBrains Mono', monospace;
    font-weight: 500;
    color: {t["ink"]};
  }}
  .note-body {{
    font-size: 13.5px;
    line-height: 1.5;
    color: {t["muted"]};
  }}
  .footer {{
    margin-top: 26px;
    padding-top: 16px;
    border-top: 1px solid {t["line"]};
    font-size: 13px;
    color: {t["muted"]};
    display: flex;
    justify-content: space-between;
  }}
  .footer .mono {{
    font-family: 'Geist Mono', 'JetBrains Mono', monospace;
  }}
</style>
</head>
<body>
  <div class="frame">
    <div class="sheet">
      <h1>Prompt changes that move pass rate. <span class="muted">8,028 runs across 4 models.</span></h1>

      <div class="legend">
        <span class="leg-item"><span class="leg-bar-base"></span>Before</span>
        <span class="leg-item"><span class="leg-bar-solid" style="background:{t["gain"]};"></span>After (gain)</span>
        <span class="leg-item"><span class="leg-bar-solid" style="background:{t["risk"]};"></span>After (hijack or collapse)</span>
        <span class="leg-right">Bar width shows range across models</span>
      </div>

      <div class="chart-grid">
        <div class="label-col">
          {"".join(labels_html)}
        </div>
        <div>
          {svg}
        </div>
      </div>

      <div class="notes-grid">
        <div class="note-col">
          <div class="note-head"><span class="num">{ts_range}</span> fewer prompt tokens</div>
          <div class="note-body">TypeScript matches JSON Schema at 100% accuracy in prose prompts.</div>
        </div>
        <div class="note-col">
          <div class="note-head"><span class="num">{rt_range}</span> fewer thinking tokens</div>
          <div class="note-body">Explicit parameter formats cut reasoning cost on all four models.</div>
        </div>
        <div class="note-col">
          <div class="note-head">No accuracy lift</div>
          <div class="note-body">Expert personas, Arabic digits, and ### tool headers stayed flat.</div>
        </div>
      </div>

      <div class="footer">
        <span>Paired prompt-level tests (N = 5 repeats per prompt)</span>
        <span class="mono">evidence/stats_recomputed.md</span>
      </div>
    </div>
  </div>
</body>
</html>
"""


def _find_browser() -> str:
    candidates = [
        shutil.which("chrome"),
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("msedge"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return str(c)
    raise RuntimeError("No headless Chromium/Chrome/Edge browser found.")


def _render_png(html_text: str, out_png: Path, browser: str, bg_hex: str) -> tuple[int, int]:
    from PIL import Image

    out_png.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        html_path = tmp / "chart.html"
        raw_png = tmp / "raw.png"
        html_path.write_text(html_text, encoding="utf-8")

        cmd = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=3",
            "--window-size=920,1050",
            "--virtual-time-budget=4000",
            f"--screenshot={raw_png}",
            html_path.as_uri(),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        img = Image.open(raw_png).convert("RGB")
        bg_rgb = tuple(int(bg_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
        px = img.load()
        w, h = img.size

        last_y = h - 1
        for y in range(h - 1, -1, -1):
            row_diff = False
            for x in range(0, w, 4):
                r, g, b = px[x, y]
                if abs(r - bg_rgb[0]) > 2 or abs(g - bg_rgb[1]) > 2 or abs(b - bg_rgb[2]) > 2:
                    row_diff = True
                    break
            if row_diff:
                last_y = y
                break

        crop_h = min(h, last_y + 48)
        cropped = img.crop((0, 0, w, crop_h))
        cropped.save(out_png, format="PNG", optimize=True)
        return cropped.size


def main() -> None:
    data = collect_verified_metrics()
    browser = _find_browser()
    for theme_name in ("dark", "light"):
        html_text = render_html(data, theme_name)
        out_path = OUT_DIR / f"what_held_up_{theme_name}.png"
        w, h = _render_png(html_text, out_path, browser, THEMES[theme_name]["page_bg"])
        kb = out_path.stat().st_size / 1000.0
        print(f"Rendered {out_path.relative_to(ROOT)} ({w}x{h}px, {kb:.1f} KB)")


if __name__ == "__main__":
    main()
