# -*- coding: utf-8 -*-
"""Kalıcı uygulama ayarları (JSON)."""
import json
import os

from . import AYAR_DOSYASI, VARSAYILAN_KLASOR

VARSAYILANLAR = {
    "tema": "dark",
    "kaynak": "Otomatik",
    "kalite": "192",
    "indirme_klasoru": VARSAYILAN_KLASOR,
    "guncelleme_url": "",
}


def yukle():
    ayar = dict(VARSAYILANLAR)
    if os.path.exists(AYAR_DOSYASI):
        try:
            with open(AYAR_DOSYASI, "r", encoding="utf-8") as f:
                ayar.update(json.load(f))
        except (OSError, ValueError):
            pass
    return ayar


def kaydet(ayar):
    try:
        with open(AYAR_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(ayar, f, ensure_ascii=False, indent=2)
    except OSError:
        pass
