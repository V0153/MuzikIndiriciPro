# -*- coding: utf-8 -*-
"""Stüdyo - MP3 düzenleme motoru (ffmpeg): kesme, ses, fade, hız, bas/tiz, normalize."""
import os
import subprocess

from mutagen.mp3 import MP3

from .indirme import ffmpeg_bul


def sure_al(yol):
    """Parçanın süresi (saniye, float)."""
    return MP3(yol).info.length


def zaman_coz(metin):
    """'1:23' / '01:02:03' / '45' / '12.5' -> saniye (float). Boş -> None."""
    if metin is None or not str(metin).strip():
        return None
    parcalar = str(metin).strip().replace(",", ".").split(":")
    saniye = 0.0
    for p in parcalar:
        saniye = saniye * 60 + float(p or 0)
    return saniye


def zaman_metni(saniye):
    saniye = int(saniye)
    return f"{saniye // 60}:{saniye % 60:02d}"


def duzenle(kaynak, hedef, baslangic=None, bitis=None, kazanc_db=0.0,
            fade_in=0.0, fade_out=0.0, hiz=1.0, bas_db=0.0, tiz_db=0.0,
            perde=0.0, yanki=0.0, karaoke=False,
            normalize=False, bitrate=None):
    """Kaynak MP3'ü verilen ayarlarla işleyip hedefe yazar.

    baslangic/bitis: saniye (None = dosyanın başı/sonu)
    kazanc_db: ses kazancı (+/- dB), bas_db/tiz_db: ekolayzır kazancı
    fade_in/fade_out: saniye, hiz: 0.5 - 2.0
    perde: yarım ton (+/- 12, süre değişmez), yanki: 0.0 - 1.0 (eko miktarı)
    karaoke: True ise vokali azaltır, normalize: loudnorm (-14 LUFS)
    """
    ffdir = ffmpeg_bul()
    ffmpeg = os.path.join(ffdir, "ffmpeg.exe") if ffdir else "ffmpeg"

    toplam = sure_al(kaynak)
    b0 = max(0.0, baslangic or 0.0)
    b1 = min(bitis if bitis else toplam, toplam)
    if b0 >= b1:
        raise ValueError("Başlangıç zamanı bitişten önce olmalı.")
    sure = b1 - b0

    filtreler = []
    if karaoke:  # orta kanalı (vokali) bastır
        filtreler.append("pan=stereo|c0=0.5*c0-0.5*c1|c1=0.5*c1-0.5*c0")
    if abs(kazanc_db) > 0.01:
        filtreler.append(f"volume={kazanc_db}dB")
    if abs(bas_db) > 0.01:
        filtreler.append(f"bass=g={bas_db}")
    if abs(tiz_db) > 0.01:
        filtreler.append(f"treble=g={tiz_db}")
    if abs(perde) > 0.01:  # perdeyi kaydır, süreyi atempo ile koru
        perde = min(max(perde, -12.0), 12.0)
        carpan = 2 ** (perde / 12.0)
        filtreler.append(f"asetrate=44100*{carpan:.6f}")
        filtreler.append("aresample=44100")
        filtreler.append(f"atempo={1 / carpan:.6f}")
    if yanki > 0.01:
        yanki = min(yanki, 1.0)
        filtreler.append(
            f"aecho=0.8:0.85:60|180:{0.35 * yanki:.3f}|{0.25 * yanki:.3f}")
    if normalize:
        filtreler.append("loudnorm=I=-14:TP=-1.5:LRA=11")
    if fade_in > 0:
        filtreler.append(f"afade=t=in:st=0:d={fade_in}")
    if fade_out > 0:
        filtreler.append(f"afade=t=out:st={max(sure - fade_out, 0):.3f}:d={fade_out}")
    if abs(hiz - 1.0) > 0.001:
        hiz = min(max(hiz, 0.5), 2.0)
        filtreler.append(f"atempo={hiz}")

    if not bitrate:
        try:
            bitrate = f"{max(int(MP3(kaynak).info.bitrate / 1000), 128)}k"
        except Exception:
            bitrate = "192k"

    komut = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
    if b0 > 0:
        komut += ["-ss", f"{b0:.3f}"]
    komut += ["-t", f"{sure:.3f}", "-i", kaynak]
    if filtreler:
        komut += ["-af", ",".join(filtreler)]
    komut += ["-map_metadata", "0", "-id3v2_version", "3",
              "-b:a", bitrate, hedef]

    bayrak = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    sonuc = subprocess.run(komut, capture_output=True, creationflags=bayrak)
    if sonuc.returncode != 0:
        hata = sonuc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"ffmpeg hatası: {hata[-400:]}")

    # Kapak resmi ses filtrelemesinde düşer; kaynaktan kopyala
    try:
        from . import etiketler
        veri = etiketler.kapak_oku(kaynak)
        if veri:
            etiketler.kapak_yaz_bytes(hedef, veri)
    except Exception:
        pass
    return hedef


# Hazır önayarlar: kaydırıcı değerleri (ses/bas/tiz dB, fade sn, hız x,
# perde yarım ton, yanki %, karaoke/normalize açık-kapalı)
ONAYARLAR = {
    "Bas Güçlü": dict(ses=1, bas=8, tiz=-1, fadein=0, fadeout=0, hiz=1.0,
                      perde=0, yanki=0, karaoke=False, normalize=False),
    "Canlı Konser": dict(ses=2, bas=3, tiz=2, fadein=0, fadeout=0, hiz=1.0,
                         perde=0, yanki=45, karaoke=False, normalize=False),
    "Telefon Hoparlörü": dict(ses=3, bas=-6, tiz=4, fadein=0, fadeout=0,
                              hiz=1.0, perde=0, yanki=0, karaoke=False,
                              normalize=True),
    "Gece Modu": dict(ses=-4, bas=-2, tiz=-2, fadein=2, fadeout=3, hiz=1.0,
                      perde=0, yanki=0, karaoke=False, normalize=True),
    "Karaoke (Vokalsiz)": dict(ses=2, bas=2, tiz=1, fadein=0, fadeout=0,
                               hiz=1.0, perde=0, yanki=15, karaoke=True,
                               normalize=False),
    "Slowed + Reverb": dict(ses=0, bas=3, tiz=-1, fadein=1, fadeout=2,
                            hiz=0.85, perde=-1, yanki=55, karaoke=False,
                            normalize=False),
    "Nightcore": dict(ses=1, bas=0, tiz=2, fadein=0, fadeout=0, hiz=1.25,
                      perde=2, yanki=10, karaoke=False, normalize=False),
}


def kopya_adi(yol):
    """'sarki.mp3' -> 'sarki (düzenlendi).mp3' (çakışırsa numaralandırır)."""
    govde, uzanti = os.path.splitext(yol)
    aday = f"{govde} (düzenlendi){uzanti}"
    sayac = 2
    while os.path.exists(aday):
        aday = f"{govde} (düzenlendi {sayac}){uzanti}"
        sayac += 1
    return aday
