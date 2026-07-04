# -*- coding: utf-8 -*-
"""Müzik İndirici PRO - giriş noktası.

Kullanım:
    MuzikIndiriciPro.exe                 -> arayüzü açar
    MuzikIndiriciPro.exe --otomatik      -> sarkilar.txt'yi indirir (sessiz)
    MuzikIndiriciPro.exe --ocr resim.png -> görseldeki şarkıları yazar (test)
    MuzikIndiriciPro.exe --surum         -> sürüm bilgisi
"""
import os
import sys


def guvenli_yaz(mesaj):
    try:
        print(mesaj)
    except Exception:
        try:
            print(mesaj.encode("ascii", errors="replace").decode("ascii"))
        except Exception:
            pass
    # Penceresiz .exe'de konsol olmadığından kayıt dosyasına da yaz
    try:
        from muzik_pro import VERI_DIR
        with open(os.path.join(VERI_DIR, "cikti.log"), "a",
                  encoding="utf-8") as f:
            f.write(mesaj + "\n")
    except Exception:
        pass


def main():
    from muzik_pro import SURUM, YAPIMCI, VARSAYILAN_KLASOR, sarkilari_oku

    if "--surum" in sys.argv:
        guvenli_yaz(f"Muzik Indirici PRO v{SURUM} - {YAPIMCI}")
        return 0

    if "--ocr" in sys.argv:
        from muzik_pro import gorsel_tara
        yol = sys.argv[sys.argv.index("--ocr") + 1]
        metin = gorsel_tara.gorselden_metin(yol)
        for sarki in gorsel_tara.metinden_sarkilar(metin):
            guvenli_yaz(sarki)
        return 0

    if "--guncelleme-testi" in sys.argv:
        # Eski sürüm gibi davranıp güncellemeyi indirir ama KURMAZ (tanı için)
        from muzik_pro import guncelleme
        guncelleme.SURUM = "0.1"
        tamam, mesaj = guncelleme.oto_guncelle(kur=False)
        guvenli_yaz(f"Guncelleme testi: {'BASARILI' if tamam else 'BASARISIZ'}"
                    f" - {mesaj.splitlines()[0]}")
        return 0 if tamam else 1

    if "--otomatik" in sys.argv:
        from muzik_pro import ayarlar, indirme
        liste = sarkilari_oku()
        if not liste:
            guvenli_yaz("sarkilar.txt bos veya yok.")
            return 1
        ayar = ayarlar.yukle()
        indirme.indir(liste, ayar.get("indirme_klasoru", VARSAYILAN_KLASOR),
                      kaynak=ayar.get("kaynak", "YouTube"),
                      kalite=ayar.get("kalite", "192"), log=guvenli_yaz)
        return 0

    from muzik_pro import arayuz
    arayuz.calistir()
    return 0


if __name__ == "__main__":
    sys.exit(main())
