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


def _kayit(mesaj):
    """Güncelleme olaylarını VERI_DIR/guncelleme.log dosyasına yazar."""
    try:
        from . import VERI_DIR
        with open(os.path.join(VERI_DIR, "guncelleme.log"), "a",
                  encoding="utf-8") as f:
            import datetime
            f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {mesaj}\n")
    except Exception:
        pass


def oto_guncelle(url=None, kur=True):
    """Sessiz otomatik güncelleme: yeni sürüm varsa kurulum dosyasını indirir.

    (kurulum_basladi, mesaj) döndürür; yeni sürüm indirildiyse kurulumu
    başlatır ve True döner (uygulama kapanmalı). Ağ yoksa veya sürüm
    güncelse sessizce False döner. kur=False ise yalnızca indirip doğrular.
    """
    durum, mesaj, indirme_url = kontrol_et(url)
    if durum != "yeni_var" or not indirme_url:
        return False, mesaj
    _kayit(f"Yeni sürüm bulundu, indiriliyor: {indirme_url}")
    hedef = os.path.join(tempfile.gettempdir(),
                         "MuzikIndiriciPro_Guncelleme.exe")
    try:
        istek = urllib.request.Request(indirme_url,
                                       headers={"User-Agent": "MuzikIndiriciPro"})
        with urllib.request.urlopen(istek, timeout=60) as kaynak, \
                open(hedef, "wb") as cikti:
            beklenen = int(kaynak.headers.get("Content-Length") or 0)
            while True:
                parca = kaynak.read(512 * 1024)
                if not parca:
                    break
                cikti.write(parca)
        inen = os.path.getsize(hedef)
        if inen < 1_000_000 or (beklenen and inen != beklenen):
            raise RuntimeError(f"eksik indirme ({inen}/{beklenen} bayt)")
        _kayit(f"İndirme tamam ({inen // 1048576} MB), doğrulandı.")
        if kur:
            # Sessiz kur; CloseApplications açık uygulamayı kapatıp günceller
            subprocess.Popen([hedef, "/SILENT", "/NORESTART"], close_fds=True)
            _kayit("Kurulum başlatıldı.")
        return True, mesaj
    except Exception as e:
        try:
            if os.path.exists(hedef):
                os.remove(hedef)  # bozuk dosya sonraki denemeyi engellemesin
        except OSError:
            pass
        _kayit(f"HATA: {e}")
        return False, f"Güncelleme indirilemedi: {e}"


def _surum_karsilastir(a, b):
    def parcala(s):
        return [int(p) for p in s.split(".") if p.isdigit()]
    pa, pb = parcala(a), parcala(b)
    return (pa > pb) - (pa < pb)
