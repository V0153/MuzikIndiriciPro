# -*- coding: utf-8 -*-
"""MP3 etiket (ID3) okuma/yazma, kapak resmi ve dosya işlemleri."""
import io
import os

from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3, ID3NoHeaderError
from mutagen.mp3 import MP3


def mp3_listele(klasor):
    """Klasördeki MP3'leri [{yol, ad, baslik, sanatci, sure}] olarak döndürür."""
    liste = []
    if not os.path.isdir(klasor):
        return liste
    for ad in sorted(os.listdir(klasor), key=str.casefold):
        if not ad.lower().endswith(".mp3"):
            continue
        yol = os.path.join(klasor, ad)
        bilgi = etiket_oku(yol)
        bilgi["yol"] = yol
        bilgi["ad"] = ad
        liste.append(bilgi)
    return liste


def etiket_oku(yol):
    bilgi = {"baslik": "", "sanatci": "", "album": "", "tur": "", "sure": 0}
    try:
        mp3 = MP3(yol)
        bilgi["sure"] = int(mp3.info.length)
    except Exception:
        pass
    try:
        e = EasyID3(yol)
        bilgi["baslik"] = (e.get("title") or [""])[0]
        bilgi["sanatci"] = (e.get("artist") or [""])[0]
        bilgi["album"] = (e.get("album") or [""])[0]
        bilgi["tur"] = (e.get("genre") or [""])[0]
    except ID3NoHeaderError:
        pass
    except Exception:
        pass
    return bilgi


def etiket_yaz(yol, baslik=None, sanatci=None, album=None, tur=None):
    try:
        e = EasyID3(yol)
    except ID3NoHeaderError:
        e = EasyID3()
        e.save(yol)
        e = EasyID3(yol)
    for anahtar, deger in (("title", baslik), ("artist", sanatci),
                           ("album", album), ("genre", tur)):
        if deger is not None:
            if deger.strip():
                e[anahtar] = deger.strip()
            elif anahtar in e:
                del e[anahtar]
    e.save(yol)


def kapak_oku(yol):
    """Gömülü kapak resmini bytes olarak döndürür (yoksa None)."""
    try:
        id3 = ID3(yol)
        resimler = id3.getall("APIC")
        if resimler:
            return resimler[0].data
    except Exception:
        pass
    return None


def kapak_yaz(yol, resim_yolu):
    """Seçilen resmi JPEG'e çevirip kapak olarak gömer."""
    from PIL import Image

    img = Image.open(resim_yolu).convert("RGB")
    img.thumbnail((1000, 1000))
    tampon = io.BytesIO()
    img.save(tampon, format="JPEG", quality=90)
    kapak_yaz_bytes(yol, tampon.getvalue())


def kapak_yaz_bytes(yol, veri, mime="image/jpeg"):
    """Hazır resim verisini (bytes) kapak olarak gömer."""
    try:
        id3 = ID3(yol)
    except ID3NoHeaderError:
        id3 = ID3()
    id3.delall("APIC")
    id3.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=veri))
    id3.save(yol)


def yeniden_adlandir(yol, yeni_ad):
    """Dosyayı aynı klasörde yeniden adlandırır, yeni yolu döndürür."""
    yeni_ad = yeni_ad.strip()
    if not yeni_ad.lower().endswith(".mp3"):
        yeni_ad += ".mp3"
    for yasak in '\\/:*?"<>|':
        yeni_ad = yeni_ad.replace(yasak, "")
    yeni_yol = os.path.join(os.path.dirname(yol), yeni_ad)
    if os.path.abspath(yeni_yol) != os.path.abspath(yol):
        os.rename(yol, yeni_yol)
    return yeni_yol


def sure_metni(saniye):
    return f"{saniye // 60}:{saniye % 60:02d}"
