# -*- coding: utf-8 -*-
"""Müzik İndirici PRO - çekirdek sabitler ve yollar."""
import os
import sys

SURUM = "1.34"
YAPIMCI = "V™"
UYGULAMA_ADI = "Müzik İndirici PRO"

if getattr(sys, "frozen", False):  # PyInstaller .exe
    APP_DIR = os.path.dirname(sys.executable)
    _KAYNAK_DIR = getattr(sys, "_MEIPASS", APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _KAYNAK_DIR = APP_DIR


def kaynak_yolu(*parcalar):
    """Paketlenmiş varlıklara (logo vb.) erişim yolu."""
    return os.path.join(_KAYNAK_DIR, *parcalar)


def _veri_klasoru():
    try:
        test = os.path.join(APP_DIR, ".yazma_testi")
        with open(test, "w") as f:
            f.write("x")
        os.remove(test)
        return APP_DIR
    except OSError:
        klasor = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                              "MuzikIndirici")
        os.makedirs(klasor, exist_ok=True)
        return klasor


VERI_DIR = _veri_klasoru()
SARKI_DOSYASI = os.path.join(VERI_DIR, "sarkilar.txt")
ARSIV_DOSYASI = os.path.join(VERI_DIR, "indirilenler.txt")
AYAR_DOSYASI = os.path.join(VERI_DIR, "ayarlar.json")
VARSAYILAN_KLASOR = os.path.join(os.path.expanduser("~"), "Music", "OyunHavalari")


def sarkilari_oku():
    if os.path.exists(SARKI_DOSYASI):
        with open(SARKI_DOSYASI, "r", encoding="utf-8-sig") as f:
            return [s.strip() for s in f if s.strip()]
    return []


def sarkilari_yaz(satirlar):
    with open(SARKI_DOSYASI, "w", encoding="utf-8") as f:
        f.write("\n".join(s.strip() for s in satirlar if s.strip()) + "\n")
