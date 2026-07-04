# -*- coding: utf-8 -*-
"""Görselden şarkı adı tarama - Windows yerleşik OCR motoru (çevrimdışı)."""
import asyncio
import os
import re

# Ekran görüntülerinde şarkı adı OLMAYAN tipik arayüz metinleri
_UI_KELIMELER = {
    "oynatma listesi", "kitaplar", "klasörler", "klasorler", "şarkılar",
    "ad", "aç", "ac", "oyun havaları", "çalma listesi", "playlist",
    "library", "songs", "albums",
}
_SURE_DESENI = re.compile(r"^\(?(\d{1,2}:)?\d{1,2}:\d{2}\)?\s*(.*)$")


async def _oku_async(yol):
    from winsdk.windows.globalization import Language
    from winsdk.windows.graphics.imaging import BitmapDecoder
    from winsdk.windows.media.ocr import OcrEngine
    from winsdk.windows.storage import StorageFile

    dosya = await StorageFile.get_file_from_path_async(yol)
    akis = await dosya.open_read_async()
    dec = await BitmapDecoder.create_async(akis)
    bmp = await dec.get_software_bitmap_async()

    motor = None
    if OcrEngine.is_language_supported(Language("tr")):
        motor = OcrEngine.try_create_from_language(Language("tr"))
    if motor is None:
        motor = OcrEngine.try_create_from_user_profile_languages()
    if motor is None:
        raise RuntimeError("Windows OCR motoru bulunamadı. "
                           "Ayarlar > Zaman ve Dil'den bir dil paketi kurun.")
    sonuc = await motor.recognize_async(bmp)
    return "\n".join(satir.text for satir in sonuc.lines)


def gorselden_metin(yol):
    """Görseldeki tüm metni döndürür."""
    # Windows OCR (WinRT) eğik çizgili yolları kabul etmez; normalleştir
    yol = os.path.normpath(os.path.abspath(yol))
    return asyncio.run(_oku_async(yol))


def metinden_sarkilar(metin):
    """OCR metnini şarkı arama satırlarına çevirir.

    'Başlık' satırının ardından 'SÜRE Sanatçı' satırı gelirse ikisini birleştirir.
    """
    sarkilar = []
    bekleyen_baslik = None

    def ekle(sanatci, baslik):
        baslik = _temizle(baslik)
        sanatci = _temizle(sanatci)
        if not baslik:
            return
        if sanatci and sanatci.casefold() not in baslik.casefold():
            sarkilar.append(f"{sanatci} {baslik}")
        else:
            sarkilar.append(baslik)

    for ham in metin.splitlines():
        satir = ham.strip()
        if len(satir) < 3:
            continue
        if satir.casefold() in _UI_KELIMELER:
            continue
        m = _SURE_DESENI.match(satir)
        if m:  # "05:05 Sanatçı Adı" satırı
            if bekleyen_baslik:
                ekle(m.group(2), bekleyen_baslik)
                bekleyen_baslik = None
            continue
        if bekleyen_baslik:  # arka arkaya iki başlık: öncekini tek başına ekle
            ekle("", bekleyen_baslik)
        bekleyen_baslik = satir
    if bekleyen_baslik:
        ekle("", bekleyen_baslik)

    # Sırayı koruyarak tekrarları at
    benzersiz, gorulen = [], set()
    for s in sarkilar:
        if s.casefold() not in gorulen:
            gorulen.add(s.casefold())
            benzersiz.append(s)
    return benzersiz


def _temizle(s):
    s = re.sub(r"#\S+", "", s)                      # hashtag'ler
    s = re.sub(r"[|•▶►✔️🔥♫█▬▀]+", " ", s)          # süs karakterleri
    s = s.replace("...", " ").replace("…", " ")
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip(" -–—/")
