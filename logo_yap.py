# -*- coding: utf-8 -*-
"""Müzik İndirici Pro logosunu üretir (logo.png + logo.ico)."""
import os
from PIL import Image, ImageDraw

BOYUT = 512
CIKTI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "varliklar")


def dikey_gradyan(boyut, ust, alt):
    img = Image.new("RGB", (boyut, boyut))
    d = ImageDraw.Draw(img)
    for y in range(boyut):
        t = y / boyut
        r = int(ust[0] + (alt[0] - ust[0]) * t)
        g = int(ust[1] + (alt[1] - ust[1]) * t)
        b = int(ust[2] + (alt[2] - ust[2]) * t)
        d.line([(0, y), (boyut, y)], fill=(r, g, b))
    return img


def yap():
    os.makedirs(CIKTI, exist_ok=True)
    B = BOYUT

    # Yuvarlak köşeli mor-indigo gradyan zemin
    zemin = dikey_gradyan(B, (124, 58, 237), (49, 46, 129))
    maske = Image.new("L", (B, B), 0)
    ImageDraw.Draw(maske).rounded_rectangle([0, 0, B - 1, B - 1], radius=110, fill=255)
    logo = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    logo.paste(zemin, (0, 0), maske)
    d = ImageDraw.Draw(logo)

    beyaz = (255, 255, 255, 255)

    # Sekizlik nota: gövde (elips), sap ve bayrak
    d.ellipse([132, 320, 250, 408], fill=beyaz)                       # nota gövdesi
    d.rounded_rectangle([228, 118, 252, 372], radius=12, fill=beyaz)  # sap
    d.polygon([(252, 118), (252, 196), (352, 260), (352, 182)], fill=beyaz)  # bayrak

    # Sağ altta amber "indirme" rozeti
    mx, my, r = 372, 372, 92
    d.ellipse([mx - r, my - r, mx + r, my + r], fill=(251, 191, 36, 255))
    d.ellipse([mx - r + 10, my - r + 10, mx + r - 10, my + r - 10],
              fill=(245, 158, 11, 255))
    ko = (30, 27, 75, 255)  # koyu lacivert ok
    d.rounded_rectangle([mx - 14, my - 52, mx + 14, my + 16], radius=8, fill=ko)
    d.polygon([(mx - 40, my + 2), (mx + 40, my + 2), (mx, my + 50)], fill=ko)

    logo.save(os.path.join(CIKTI, "logo.png"))
    logo.save(os.path.join(CIKTI, "logo.ico"),
              sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                     (64, 64), (128, 128), (256, 256)])
    print("Logo uretildi:", CIKTI)


if __name__ == "__main__":
    yap()
