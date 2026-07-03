# -*- coding: utf-8 -*-
"""Güncelleme - açılışta otomatik denetler, yeni sürümü indirir ve kurar.

Sunucudaki JSON biçimi:
    {"surum": "1.40", "indirme_url": "https://.../Kurulum.exe", "notlar": "..."}
"""
import json
import os
import subprocess
import tempfile
import urllib.request

from . import SURUM

# Varsayılan güncelleme adresi: depodaki surum.json güncellendiği anda tüm
# kurulu kopyalar açılışta güncellemeyi kendiliğinden alır.
VARSAYILAN_URL = ("https://raw.githubusercontent.com/V0153/MuzikIndiriciPro/"
                  "main/surum.json")


def kontrol_et(url=None, zaman_asimi=10):
    """(durum, mesaj, indirme_url) döndürür.

    durum: 'guncel' | 'yeni_var' | 'hata'
    """
    if not url or not url.strip():
        url = VARSAYILAN_URL
    try:
        istek = urllib.request.Request(url.strip(),
                                       headers={"User-Agent": "MuzikIndiriciPro"})
        with urllib.request.urlopen(istek, timeout=zaman_asimi) as yanit:
            veri = json.loads(yanit.read().decode("utf-8"))
        uzak = str(veri.get("surum", "")).strip()
        if not uzak:
            return ("hata", "Sunucudan geçerli sürüm bilgisi alınamadı.", None)
        if _surum_karsilastir(uzak, SURUM) > 0:
            notlar = veri.get("notlar", "")
            mesaj = f"Yeni sürüm mevcut: v{uzak} (kurulu: v{SURUM})"
            if notlar:
                mesaj += f"\n\nYenilikler:\n{notlar}"
            return ("yeni_var", mesaj, veri.get("indirme_url"))
        return ("guncel", f"Uygulama güncel (v{SURUM}).", None)
    except Exception as e:
        return ("hata", f"Güncelleme denetlenemedi: {e}", None)


def oto_guncelle(url=None):
    """Sessiz otomatik güncelleme: yeni sürüm varsa kurulum dosyasını indirir.

    (kuruldu_mu_baslatilacak, mesaj) döndürür; yeni sürüm indirildiyse
    kurulumu başlatır ve True döner (uygulama kapanmalı). Ağ yoksa veya
    sürüm güncelse sessizce False döner.
    """
    durum, mesaj, indirme_url = kontrol_et(url)
    if durum != "yeni_var" or not indirme_url:
        return False, mesaj
    try:
        hedef = os.path.join(tempfile.gettempdir(),
                             "MuzikIndiriciPro_Guncelleme.exe")
        istek = urllib.request.Request(indirme_url,
                                       headers={"User-Agent": "MuzikIndiriciPro"})
        with urllib.request.urlopen(istek, timeout=60) as kaynak, \
                open(hedef, "wb") as cikti:
            cikti.write(kaynak.read())
        # Kurulumu sessiz başlat; uygulama kapanınca dosyaların üzerine yazar
        subprocess.Popen([hedef, "/SILENT", "/NORESTART"], close_fds=True)
        return True, mesaj
    except Exception as e:
        return False, f"Güncelleme indirilemedi: {e}"


def _surum_karsilastir(a, b):
    def parcala(s):
        return [int(p) for p in s.split(".") if p.isdigit()]
    pa, pb = parcala(a), parcala(b)
    return (pa > pb) - (pa < pb)
