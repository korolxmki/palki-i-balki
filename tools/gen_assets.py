#!/usr/bin/env python3
"""
Генератор статичных ассетов сайта «Палки и Балки».

Создаёт:
  img/shots/*.svg   — плейсхолдеры фотографий (заменяются на реальные фото)
  img/favicon.svg   — фавикон
  img/og.svg        — картинка для соцсетей
и вставляет SVG-спрайт иконок в index.html / portfolio.html
между маркерами <!--SPRITE:START--> и <!--SPRITE:END-->.

Запуск:  python3 tools/gen_assets.py
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────
# Иконки направлений и интерфейса. viewBox 0 0 48 48, штрих.
# ─────────────────────────────────────────────────────────────
ICONS = {
    "kitchen": """
        <rect x="5" y="7" width="17" height="11" rx="1.6"/>
        <path d="M27 18 L29.5 7 H38.5 L41 18 Z"/>
        <path d="M4 25h40"/>
        <rect x="6" y="25" width="36" height="16" rx="1.6"/>
        <path d="M24 25v16"/>
        <path d="M11.5 12.5h4M11.5 32h5M31.5 32h5"/>""",
    "wardrobe": """
        <rect x="7" y="6" width="34" height="36" rx="2"/>
        <path d="M7 11.5h34"/>
        <path d="M24 11.5V42"/>
        <path d="M19.5 22v6M28.5 22v6"/>""",
    "dressing": """
        <rect x="6" y="6" width="36" height="36" rx="2"/>
        <path d="M24 6v36"/>
        <path d="M6 16.5h18M6 26h18M6 35h18"/>
        <path d="M27 14h12"/>
        <path d="M31 14v3.5M31 17.5l-2.6 4.2h5.2zM36 14v3.5M36 17.5l-2.6 4.2h5.2z"/>""",
    "kids": """
        <path d="M9 43V9M39 43V9"/>
        <path d="M9 23h30M9 37h30"/>
        <path d="M9 17.5h30"/>
        <path d="M16.5 23v-5.5M24 23v-5.5M31.5 23v-5.5"/>
        <path d="M9 30h6"/>""",
    "bath": """
        <ellipse cx="17" cy="20" rx="8.5" ry="3.6"/>
        <path d="M13 16.5V11h4.5a3 3 0 0 1 3 3v2"/>
        <path d="M4 24h40"/>
        <rect x="8" y="24" width="32" height="16" rx="1.6"/>
        <path d="M24 24v16"/>
        <path d="M13.5 31.5h5M29.5 31.5h5"/>
        <circle cx="34" cy="13" r="6.5"/>""",
    "hallway": """
        <rect x="6" y="6" width="13" height="32" rx="1.6"/>
        <path d="M15.5 19v5"/>
        <path d="M24 12h18"/>
        <path d="M28 12v4.5M34 12v4.5M40 12v4.5"/>
        <path d="M24 31h18M27 31v7M39 31v7"/>""",
    "living": """
        <rect x="8" y="7" width="32" height="20" rx="2"/>
        <path d="M20 27h8"/>
        <rect x="5" y="31" width="38" height="11" rx="2"/>
        <path d="M24 31v11"/>
        <path d="M11.5 36.5h5M31.5 36.5h5"/>""",
    "office": """
        <rect x="12" y="6" width="24" height="12" rx="1.6"/>
        <path d="M24 6v12"/>
        <path d="M4 24h40"/>
        <path d="M9 24v18M39 24v18"/>
        <rect x="14" y="28" width="16" height="12" rx="1.6"/>
        <path d="M14 34h16"/>""",
    # процесс
    "measure": """
        <circle cx="24" cy="24" r="17"/>
        <circle cx="24" cy="24" r="6"/>
        <path d="M28.5 28.5 41 41"/>
        <path d="M24 7v4M24 37v4M7 24h4M37 24h4"/>""",
    "sketch": """
        <path d="M8 40h32"/>
        <path d="M12 33 32 13l4 4-20 20z"/>
        <path d="M12 33l-1.5 5.5L16 37"/>
        <path d="M29 10l3-3 4 4-3 3"/>""",
    "factory": """
        <path d="M6 41V20l11 7V20l11 7V12l14 9v20z"/>
        <path d="M6 41h36"/>
        <path d="M31 30v5M22 32v3M13 32v3"/>""",
    "install": """
        <path d="M30 8a8 8 0 0 0-10.4 10.4L8.5 29.5a3.5 3.5 0 0 0 5 5l11.1-11.1A8 8 0 0 0 35 13z"/>
        <path d="M11.5 32.5h.02"/>""",
    # интерфейс
    "arrow": """<path d="M10 24h28M27 13l11 11-11 11"/>""",
    "plus": """<path d="M24 12v24M12 24h24"/>""",
    "check": """<path d="M10 25l9 9 19-20"/>""",
    "star": """<path d="M24 6l5.4 11.6 12.6 1.6-9.3 8.7 2.4 12.5L24 34.3 12.9 40.4l2.4-12.5L6 19.2l12.6-1.6z"/>""",
    "quote": """
        <path d="M20 12c-6 2-10 7-10 14v10h13V24h-7c0-4 2-7 6-8z"/>
        <path d="M41 12c-6 2-10 7-10 14v10h13V24h-7c0-4 2-7 6-8z"/>""",
    "pin": """
        <path d="M24 43s13-12.3 13-22a13 13 0 1 0-26 0c0 9.7 13 22 13 22z"/>
        <circle cx="24" cy="21" r="5"/>""",
    "phone": """
        <path d="M17.6 8.5 21 16l-4 3.5a24 24 0 0 0 11.5 11.5L32 27l7.5 3.4v7.4c0 1.8-1.5 3.3-3.3 3.1C20 39.6 8.4 28 7.1 11.8 7 10 8.4 8.5 10.2 8.5z"/>""",
    "clock": """<circle cx="24" cy="24" r="17"/><path d="M24 13v11l7 5"/>""",
    "shield": """<path d="M24 5 8 11v13c0 10 7 16.6 16 19 9-2.4 16-9 16-19V11z"/><path d="M17 24l5 5 10-11"/>""",
    "ruler": """
        <rect x="4" y="16" width="40" height="16" rx="2" transform="rotate(-8 24 24)"/>
        <path d="M13 19.5v5M20 18.5v7M27 17.5v5M34 16.5v7"/>""",
    "layers": """<path d="M24 6 5 16l19 10 19-10z"/><path d="M5 26l19 10 19-10"/><path d="M5 34l19 8 19-8"/>""",
    "menu": """<path d="M7 16h34M7 24h34M7 32h34"/>""",
    "close": """<path d="M12 12l24 24M36 12L12 36"/>""",
    "chevron": """<path d="M12 19l12 12 12-12"/>""",
}

# Бренд-иконки (заливка, viewBox 0 0 24 24)
BRAND = {
    "tg": '<path d="M9.04 15.47 8.7 19.9c.5 0 .72-.21.98-.47l2.36-2.24 4.9 3.57c.9.5 1.55.24 1.78-.83l3.23-15.1c.29-1.32-.48-1.84-1.35-1.52L1.6 9.53C.31 10.03.33 10.75 1.38 11.06l4.9 1.53L17.66 5.4c.53-.34 1.02-.15.62.19z"/>',
    "wa": '<path d="M17.47 14.38c-.3-.15-1.75-.86-2.02-.96-.27-.1-.47-.15-.67.15-.2.3-.77.96-.94 1.16-.17.2-.35.22-.64.07-.3-.15-1.25-.46-2.38-1.47-.88-.78-1.47-1.75-1.64-2.05-.17-.3-.02-.46.13-.6.13-.13.3-.35.45-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.02-.52-.07-.15-.67-1.6-.92-2.2-.24-.58-.48-.5-.67-.5h-.57c-.2 0-.52.07-.8.37-.27.3-1.04 1.02-1.04 2.47s1.07 2.86 1.22 3.06c.15.2 2.1 3.2 5.08 4.49.71.3 1.26.49 1.7.63.71.23 1.36.2 1.87.12.57-.08 1.75-.71 2-1.4.25-.7.25-1.29.17-1.41-.07-.12-.27-.2-.57-.35z"/><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38a9.87 9.87 0 0 0 4.79 1.22c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.82 9.82 0 0 0 12.04 2zm0 18.15a8.2 8.2 0 0 1-4.19-1.15l-.3-.18-3.11.82.83-3.04-.2-.31a8.17 8.17 0 0 1-1.26-4.38c0-4.54 3.7-8.24 8.24-8.24 2.2 0 4.27.86 5.82 2.42a8.18 8.18 0 0 1 2.41 5.83c0 4.54-3.7 8.23-8.24 8.23z"/>',
}


def sprite() -> str:
    out = ['<svg class="sprite" aria-hidden="true" focusable="false" width="0" height="0">']
    for name, body in ICONS.items():
        out.append(
            f'<symbol id="i-{name}" viewBox="0 0 48 48" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            f'{" ".join(body.split())}</symbol>'
        )
    for name, body in BRAND.items():
        out.append(
            f'<symbol id="i-{name}" viewBox="0 0 24 24" fill="currentColor">{body}</symbol>'
        )
    out.append("</svg>")
    return "".join(out)


# ─────────────────────────────────────────────────────────────
# Плейсхолдеры фотографий
# ─────────────────────────────────────────────────────────────
TONES = [
    # (верх градиента, низ, цвет линий/иконки, цвет текста)
    ("#e4e0d9", "#c8c1b6", "#8d8579", "#4a453e"),
    ("#b6ada1", "#918879", "#efeae2", "#2d2a26"),
    ("#3c3936", "#262321", "#a09587", "#e7e3dc"),
    ("#d5cec4", "#b0a89b", "#7d7467", "#3a3630"),
    ("#514c46", "#332f2c", "#b3a897", "#ece8e1"),
]

SHOTS = {
    "kitchen": ("Кухни", "kitchen"),
    "wardrobe": ("Шкафы-купе", "wardrobe"),
    "dressing": ("Гардеробные", "dressing"),
    "kids": ("Детская мебель", "kids"),
    "bath": ("Мебель для ванной", "bath"),
    "hallway": ("Прихожие", "hallway"),
    "living": ("Гостиные и ТВ-зоны", "living"),
    "office": ("Офисная мебель", "office"),
}


def shot(slug: str, label: str, icon: str, idx: int, tone: int) -> str:
    top, bottom, line, text = TONES[tone % len(TONES)]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 900" width="1200" height="900" role="img" aria-label="{label} — место для фотографии проекта">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0.35" y2="1">
      <stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/>
    </linearGradient>
    <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse" patternTransform="rotate(-18)">
      <path d="M0 0v60" stroke="{line}" stroke-width="1" opacity="0.18"/>
    </pattern>
  </defs>
  <rect width="1200" height="900" fill="url(#bg)"/>
  <rect width="1200" height="900" fill="url(#grid)"/>
  <circle cx="985" cy="205" r="330" fill="{line}" opacity="0.10"/>
  <g transform="translate(600 415) scale(6.2) translate(-24 -24)" fill="none" stroke="{line}"
     stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.85">
    {" ".join(ICONS[icon].split())}
  </g>
  <g font-family="Manrope, 'Trebuchet MS', Arial, sans-serif" fill="{text}">
    <text x="600" y="735" font-size="46" font-weight="700" text-anchor="middle" letter-spacing="1">{label}</text>
    <text x="600" y="790" font-size="28" font-weight="500" text-anchor="middle" opacity="0.72">проект {idx:02d} · место для фото</text>
  </g>
</svg>
"""


def favicon() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <rect width="64" height="64" rx="14" fill="#232323"/>
  <g stroke="#e6e4e0" stroke-width="5" stroke-linecap="round">
    <path d="M18 46V18h11a8 8 0 0 1 0 16h-11"/>
    <path d="M38 46V18"/><path d="M38 46h8"/>
  </g>
</svg>
"""


def og() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <rect width="1200" height="630" fill="#232323"/>
  <circle cx="1030" cy="120" r="300" fill="#343434"/>
  <g font-family="Manrope, Arial, sans-serif" fill="#e6e4e0">
    <text x="80" y="250" font-size="52" font-weight="500" opacity="0.7" letter-spacing="6">АТЕЛЬЕ МЕБЕЛИ · МОСКВА</text>
    <text x="80" y="370" font-size="104" font-weight="800" letter-spacing="-2">ПАЛКИ И БАЛКИ</text>
    <text x="80" y="450" font-size="40" font-weight="500" opacity="0.8">Мебель на заказ под любой запрос</text>
  </g>
  <rect x="80" y="510" width="360" height="72" rx="36" fill="#e6e4e0"/>
  <text x="260" y="556" font-size="26" font-weight="700" fill="#232323" text-anchor="middle"
        font-family="Manrope, Arial, sans-serif" letter-spacing="2">БЕСПЛАТНЫЙ ЗАМЕР</text>
</svg>
"""


def inject_sprite(path: pathlib.Path, markup: str) -> None:
    if not path.exists():
        return
    html = path.read_text(encoding="utf-8")
    new = re.sub(
        r"<!--SPRITE:START-->.*?<!--SPRITE:END-->",
        "<!--SPRITE:START-->" + markup + "<!--SPRITE:END-->",
        html,
        flags=re.S,
    )
    if new != html:
        path.write_text(new, encoding="utf-8")
        print(f"  спрайт вставлен в {path.name}")


def main() -> None:
    shots_dir = ROOT / "img" / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for i, (slug, (label, icon)) in enumerate(SHOTS.items()):
        for j in range(1, 4):
            (shots_dir / f"{slug}-{j}.svg").write_text(
                shot(slug, label, icon, j, i + j), encoding="utf-8"
            )
            n += 1
    (ROOT / "img" / "favicon.svg").write_text(favicon(), encoding="utf-8")
    (ROOT / "img" / "og.svg").write_text(og(), encoding="utf-8")
    print(f"  сгенерировано плейсхолдеров: {n}")
    markup = sprite()
    for page in ("index.html", "portfolio.html"):
        inject_sprite(ROOT / page, markup)


if __name__ == "__main__":
    main()
