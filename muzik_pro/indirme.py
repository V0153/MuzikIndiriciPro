# -*- coding: utf-8 -*-
"""İndirme motoru - yt-dlp üzerinden çoklu kaynak (YouTube, SoundCloud) desteği."""
import glob
import os

from . import APP_DIR, ARSIV_DOSYASI

# Arama kaynakları - yenisini eklemek için buraya bir satır eklemek yeterli
# (yt-dlp'nin desteklediği her arama öneki kullanılabilir).
KAYNAK_ONEKLERI = {
    "YouTube": "ytsearch1",
    "SoundCloud": "scsearch1",
}
# "Otomatik": sırayla dener; bir kaynak çökerse/bulamazsa sıradakine geçer.
KAYNAK_SECENEKLERI = ["Otomatik"] + list(KAYNAK_ONEKLERI)


def ffmpeg_bul():
    adaylar = (glob.glob(os.path.join(APP_DIR, "ffmpeg", "ffmpeg.exe"))
               + glob.glob(os.path.join(APP_DIR, "ffmpeg", "*", "bin", "ffmpeg.exe"))
               + glob.glob(os.path.join(APP_DIR, "ffmpeg.exe")))
    if adaylar:
        return os.path.dirname(adaylar[0])
    return None  # PATH'te aranır


def motor_surumu():
    import yt_dlp
    return yt_dlp.version.__version__


def _temel_ayarlar(hedef_klasor, kalite):
    ayarlar = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(hedef_klasor, "%(title)s.%(ext)s"),
        "noplaylist": True,
        "download_archive": ARSIV_DOSYASI,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
             "preferredquality": str(kalite)},
            {"key": "FFmpegMetadata"},
            {"key": "EmbedThumbnail"},
        ],
        "writethumbnail": True,
    }
    ffmpeg_yolu = ffmpeg_bul()
    if ffmpeg_yolu:
        ayarlar["ffmpeg_location"] = ffmpeg_yolu
    return ayarlar


def indir(sarkilar, hedef_klasor, kaynak="Otomatik", kalite="192",
          log=print, ilerleme=None, durduruldu=lambda: False):
    """Şarkı listesini indirir. Satır bir URL ise doğrudan, değilse arama ile.

    kaynak "Otomatik" ise kaynaklar sırayla denenir: biri çökerse veya
    sonuç bulamazsa bir sonrakine geçilir (gelecekte bir API patlarsa
    uygulama çalışmaya devam eder).
    """
    import yt_dlp

    os.makedirs(hedef_klasor, exist_ok=True)
    temel = _temel_ayarlar(hedef_klasor, kalite)

    basarili, hatali = 0, 0
    temiz = [s.strip() for s in sarkilar if s.strip() and not s.strip().startswith("#")]
    toplam = len(temiz)
    for i, sarki in enumerate(temiz, 1):
        if durduruldu():
            log("Durduruldu.")
            break
        if ilerleme:
            ilerleme(i, toplam)

        if sarki.lower().startswith(("http://", "https://")):
            denemeler = [("Bağlantı", None)]
        elif kaynak == "Otomatik":
            denemeler = list(KAYNAK_ONEKLERI.items())
        else:
            denemeler = [(kaynak, KAYNAK_ONEKLERI.get(kaynak, "ytsearch1"))]

        indi = False
        for deneme_no, (kaynak_adi, onek) in enumerate(denemeler, 1):
            log(f"[{i}/{toplam}] Aranıyor ({kaynak_adi}): {sarki}")
            ayarlar = dict(temel)
            if onek:
                ayarlar["default_search"] = onek
            try:
                with yt_dlp.YoutubeDL(ayarlar) as ydl:
                    if ydl.download([sarki]) == 0:
                        indi = True
                        break
            except Exception as e:
                kisa = str(e).splitlines()[0][:120]
                log(f"    ⚠ {kaynak_adi} başarısız: {kisa}")
            if deneme_no < len(denemeler):
                log("    ↻ Sıradaki kaynak deneniyor...")
        if indi:
            basarili += 1
            log(f"    ✔ Tamam: {sarki}")
        else:
            hatali += 1
            log(f"    ✖ Hata: {sarki} hiçbir kaynaktan indirilemedi")
    log("")
    log(f"Bitti. {basarili} başarılı, {hatali} hatalı. Klasör: {hedef_klasor}")
    return basarili, hatali
