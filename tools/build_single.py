#!/usr/bin/env python3
"""
Собирает один самодостаточный HTML для быстрого деплоя (Vercel Drop и т.п.).

Что делает:
  • вклеивает портфолио со второй страницы прямо в главную — стили, разметку
    и логику фильтров с просмотром фото (по маркерам PF:* в portfolio.html);
  • переводит ссылки portfolio.html на эту внутреннюю секцию, а ссылки
    по направлениям сразу включают нужный фильтр;
  • перекодирует фотографии в WebP и вшивает их как data:URI;
  • вшивает SVG-заглушки и фавикон;
  • убирает og:image — картинка для соцсетей не может быть data:URI.

Результат: dist/palki-i-balki.html — весь сайт в одном файле,
перетаскивается в браузер, на хостинг или в другой чат как есть.

Запуск: python3 tools/build_single.py
"""
import base64
import io
import pathlib
import re

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

# Ширина и качество WebP для каждой картинки.
# hero-bg и hero-front обязаны сохранить одинаковые пропорции, иначе
# передний план разъедется с фоном — поэтому у них общий размер.
PLAN = {
    # фон сильно затемнён фильтром, поэтому переживает сжатие;
    # передний план держим крупнее — он на виду и не затемнён
    "img/hero-bg.jpg": (1400, 70),
    "img/hero-front.webp": (1600, 78),
    "img/shot-wide.jpg": (1200, 74),
    "img/shot-stone.jpg": (900, 74),
    "img/shot-wood.jpg": (900, 74),
    "img/shot-hob.jpg": (900, 74),
}
DEFAULT = (1000, 74)


def as_webp(path: pathlib.Path, width: int, quality: int) -> bytes:
    im = Image.open(path)
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality, method=6)
    return buf.getvalue()


def data_uri(src: str) -> str:
    path = ROOT / src
    if src.endswith(".svg"):
        raw = path.read_bytes()
        return "data:image/svg+xml;base64," + base64.b64encode(raw).decode()
    width, quality = PLAN.get(src, DEFAULT)
    return "data:image/webp;base64," + base64.b64encode(as_webp(path, width, quality)).decode()


def part(text: str, name: str) -> str:
    """Кусок между маркерами PF:<name>:START и PF:<name>:END."""
    m = re.search(
        rf"PF:{name}:START\s*(?:\*/|-->)?\s*(.*?)\s*(?:/\*|<!--)\s*PF:{name}:END",
        text, re.S,
    )
    if not m:
        raise SystemExit(f"в portfolio.html нет маркеров PF:{name}")
    return m.group(1)


def merge_portfolio(html: str) -> str:
    """Переносит портфолио со второй страницы внутрь главной."""
    pf = (ROOT / "portfolio.html").read_text(encoding="utf-8")

    css = part(pf, "STYLE")
    body = part(pf, "BODY").replace('id="lightbox"', 'id="lightbox"', 1)
    js = part(pf, "JS")

    # секция портфолио получает свой якорь, чтобы не спорить с тизером
    body = body.replace(
        '<section class="wrap" style="padding-bottom: var(--sec)">',
        '<section class="wrap" id="portfolio-all" style="padding-bottom: var(--sec)">',
        1,
    )
    html = html.replace("</style>", "\n/* ---- портфолио, перенесённое со второй страницы ---- */\n" + css + "\n</style>", 1)
    html = html.replace("<!-- SINGLE:PORTFOLIO -->", body, 1)
    html = html.replace("/* SINGLE:JS */", js, 1)

    # ссылки: направления включают фильтр, остальные просто ведут в секцию
    html = re.sub(
        r'href="portfolio\.html#([a-z]+)"',
        lambda m: f'href="#portfolio-all" data-pf="{m.group(1)}"',
        html,
    )
    html = html.replace('href="portfolio.html"', 'href="#portfolio-all"')
    # в перенесённом куске были ссылки обратно на главную — теперь это та же страница
    html = html.replace('href="index.html#', 'href="#').replace('href="index.html"', 'href="#hero"')
    return html


def main() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    # 1. вторая страница переезжает внутрь первой
    html = merge_portfolio(html)

    # 2. og:image убираем: data:URI соцсети не читают
    html = re.sub(r'\s*<meta property="og:image"[^>]*>', "", html)

    # 3. фавикон и все картинки — внутрь файла
    assets = sorted(set(re.findall(r'(?:src|href)="(img/[^"]+)"', html)))
    total_before = 0
    for src in assets:
        total_before += (ROOT / src).stat().st_size
        html = html.replace('"' + src + '"', '"' + data_uri(src) + '"')

    # 4. пометка, что это сборка
    html = html.replace(
        "<!--SPRITE:START-->",
        "<!-- Однофайловая сборка: все картинки вшиты. Исходники — tools/build_single.py -->\n<!--SPRITE:START-->",
        1,
    )

    DIST.mkdir(exist_ok=True)
    out = DIST / "palki-i-balki.html"
    out.write_text(html, encoding="utf-8")

    print(f"вшито файлов: {len(assets)} ({total_before / 1024:.0f} КБ на диске)")
    print(f"готово: {out.relative_to(ROOT)} — {out.stat().st_size / 1024 / 1024:.2f} МБ")
    left = re.findall(r'(?:src|href)="(?!data:|https?:|#|tel:|mailto:)([^"]+)"', html)
    print("внешних ссылок на файлы:", left or "нет — файл самодостаточный")


if __name__ == "__main__":
    main()
