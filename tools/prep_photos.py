#!/usr/bin/env python3
"""
Готовит слои главного экрана из фотографии кухни.

Вход:  img/source/kitchen.png  — исходное фото клиента
Выход: img/hero-bg.jpg    — фон героя (апскейл + лёгкая резкость и зерно)
       img/hero-front.webp — передний план: остров и каменная столешница
                            с прозрачностью, чтобы надпись уходила ЗА мебель
       img/shot-*.jpg     — кадрировки для секций «о компании» и портфолио

Почему не rembg: на интерьерном кадре u2net и isnet оставляют <1% кадра —
выделять нечего, «объекта» на фото нет. Поэтому маска переднего плана задана
кромкой столешницы (EDGE ниже) в координатах исходника 433×325.
Если пришлёте вырезанный PNG — положите его как img/hero-front.webp (или
поправьте путь в разметке),
разметку менять не нужно: слой берётся по этому имени.

Запуск: python3 tools/prep_photos.py
"""
import pathlib

from PIL import Image, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "img" / "source" / "kitchen.png"
SCALE = 4  # 433×325 → 1732×1300

# Кромка переднего плана в координатах исходника: остров слева,
# затем ступенька вверх на каменную столешницу с мойкой.
EDGE = [(0, 255), (132, 277), (133, 249), (433, 242)]


def upscale(im: Image.Image) -> Image.Image:
    big = im.resize((im.width * SCALE, im.height * SCALE), Image.LANCZOS)
    return big.filter(ImageFilter.UnsharpMask(radius=2.2, percent=85, threshold=3))


def grain(im: Image.Image, amount: int = 5) -> Image.Image:
    """Плёночное зерно: маскирует мягкость апскейла."""
    import numpy as np

    arr = np.asarray(im).astype(np.int16)
    rng = np.random.default_rng(7)
    noise = rng.normal(0, amount, arr.shape[:2])[..., None]
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype("uint8"))


def foreground(im: Image.Image) -> Image.Image:
    """Слой переднего плана: всё ниже кромки столешницы, край слегка размыт."""
    from PIL import ImageDraw

    w, h = im.size
    mask = Image.new("L", (w, h), 0)
    poly = [(x * SCALE, y * SCALE) for x, y in EDGE] + [(w, h), (0, h)]
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(2.5))
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


def main() -> None:
    src = Image.open(SRC).convert("RGB")
    big = grain(upscale(src))
    img = ROOT / "img"

    big.save(img / "hero-bg.jpg", quality=88, optimize=True, progressive=True)
    # WebP с альфой: полноразмерный PNG весит 3,6 МБ, WebP — в двадцать раз меньше
    foreground(big).save(img / "hero-front.webp", quality=88, method=6)

    # Кадрировки для остальных секций (в долях от исходника: left, top, right, bottom)
    crops = {
        "shot-wide": (0.00, 0.00, 1.00, 0.86),   # общий план
        "shot-stone": (0.52, 0.34, 1.00, 0.94),  # камень, мойка, смеситель
        "shot-wood": (0.05, 0.02, 0.55, 0.72),   # шпон и техника
        "shot-hob": (0.00, 0.62, 0.62, 1.00),    # варочная панель и остров
    }
    w, h = big.size
    for name, (l, t, r, b) in crops.items():
        big.crop((int(w * l), int(h * t), int(w * r), int(h * b))).save(
            img / f"{name}.jpg", quality=86, optimize=True, progressive=True
        )
    print("готово:", ", ".join(sorted(p.name for p in img.glob("*.jpg"))), "+ hero-front.webp")


if __name__ == "__main__":
    main()
