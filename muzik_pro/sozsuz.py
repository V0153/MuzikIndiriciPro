# -*- coding: utf-8 -*-
"""Sözsüz (enstrümantal) çıkarma - vokal kaldırma yöntemleri.

Hızlı yöntemler (ffmpeg, anında, çevrimdışı):
  - Klasik Merkez Çıkarma: sol-sağ farkı, ortadaki vokali siler.
  - Bas Korumalı Çıkarma: vokali siler ama bas/davulu korur.
  - Güçlü Çıkarma (Mono): en agresif merkez bastırma.

Yapay zekâ yöntemi (Demucs, ilk kullanımda ~indirme, çok daha temiz):
  - İzole bir Python 3.12 ortamı indirilip Demucs kurulur; parça
    gerçek anlamda vokal/enstrümantal olarak ayrılır.
"""
import glob
import os
import subprocess
import urllib.request

from . import VERI_DIR
from .indirme import ffmpeg_bul

# Hızlı yöntem adı -> ffmpeg ses filtresi
FFMPEG_YONTEMLERI = {
    "Klasik Merkez Çıkarma": "pan=stereo|c0=c0-c1|c1=c1-c0",
    "Güçlü Çıkarma (Mono)": "pan=mono|c0=0.5*c0-0.5*c1,aformat=channel_layouts=stereo",
    # Bas korumalı: alt frekanslarda mono toplam (bas/davul kalır),
    # üst frekanslarda sol-sağ farkı (vokal gider), sonra birleştir.
    "Bas Korumalı Çıkarma": (
        "asplit[a][b];"
        "[a]pan=stereo|c0=c0-c1|c1=c1-c0,highpass=f=180[hi];"
        "[b]lowpass=f=180,pan=mono|c0=0.5*c0+0.5*c1[lo];"
        "[hi][lo]amerge=inputs=2,pan=stereo|c0=c0+c2|c1=c1+c2"
    ),
}

YONTEMLER = list(FFMPEG_YONTEMLERI) + ["Yapay Zekâ (Demucs)"]

# --- Demucs izole çalışma ortamı ------------------------------------------
_RT_DIR = os.path.join(VERI_DIR, "demucs_rt")
_PY_DIR = os.path.join(_RT_DIR, "python")
_PY_EXE = os.path.join(_PY_DIR, "python.exe")
_HAZIR_ISARET = os.path.join(_RT_DIR, "HAZIR.txt")

# torch, Python 3.12 için tekerlek (wheel) sağlar; sistem Python sürümünden
# bağımsız çalışsın diye embeddable 3.12 indiriyoruz.
_EMBED_URL = ("https://www.python.org/ftp/python/3.12.8/"
              "python-3.12.8-embed-amd64.zip")
_GETPIP_URL = "https://bootstrap.pypa.io/get-pip.py"


def _sessiz():
    return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def demucs_hazir():
    return os.path.exists(_HAZIR_ISARET) and os.path.exists(_PY_EXE)


def _indir(url, hedef, log, etiket):
    log(f"İndiriliyor: {etiket} ...")
    with urllib.request.urlopen(url, timeout=120) as kaynak, \
            open(hedef, "wb") as cikti:
        toplam = int(kaynak.headers.get("Content-Length") or 0)
        inen = 0
        while True:
            parca = kaynak.read(1024 * 256)
            if not parca:
                break
            cikti.write(parca)
            inen += len(parca)
            if toplam:
                log(f"   {etiket}: %{inen * 100 // toplam}")


def demucs_kur(log=print):
    """İzole Python 3.12 ortamını kurup Demucs'i yükler (ilk kullanım)."""
    import zipfile

    os.makedirs(_PY_DIR, exist_ok=True)
    # 1) Embeddable Python
    if not os.path.exists(_PY_EXE):
        zip_yolu = os.path.join(_RT_DIR, "python.zip")
        _indir(_EMBED_URL, zip_yolu, log, "Python 3.12")
        with zipfile.ZipFile(zip_yolu) as z:
            z.extractall(_PY_DIR)
        os.remove(zip_yolu)
        # site-packages'i etkinleştir (._pth içindeki 'import site' satırını aç)
        for pth in glob.glob(os.path.join(_PY_DIR, "python*._pth")):
            with open(pth, "r", encoding="utf-8") as f:
                icerik = f.read()
            icerik = icerik.replace("#import site", "import site")
            if "import site" not in icerik:
                icerik += "\nimport site\n"
            with open(pth, "w", encoding="utf-8") as f:
                f.write(icerik)

    # 2) pip
    if subprocess.run([_PY_EXE, "-m", "pip", "--version"],
                      capture_output=True, creationflags=_sessiz()).returncode != 0:
        getpip = os.path.join(_RT_DIR, "get-pip.py")
        _indir(_GETPIP_URL, getpip, log, "pip")
        log("pip kuruluyor ...")
        _kosul([_PY_EXE, getpip, "--no-warn-script-location"], log)

    # 3) Demucs + CPU torch (CUDA'sız, daha küçük)
    log("Demucs ve torch kuruluyor (~1-2 GB, birkaç dakika) ...")
    _kosul([_PY_EXE, "-m", "pip", "install", "--no-warn-script-location",
            "torch", "--index-url", "https://download.pytorch.org/whl/cpu"], log)
    _kosul([_PY_EXE, "-m", "pip", "install", "--no-warn-script-location",
            "demucs"], log)

    with open(_HAZIR_ISARET, "w", encoding="utf-8") as f:
        f.write("hazir")
    log("Demucs kurulumu tamam.")


def _kosul(komut, log):
    sonuc = subprocess.run(komut, capture_output=True, creationflags=_sessiz())
    if sonuc.returncode != 0:
        hata = sonuc.stderr.decode("utf-8", errors="replace")[-500:]
        raise RuntimeError(f"Kurulum adımı başarısız:\n{hata}")


# --- Ana işlem -------------------------------------------------------------
def sozsuz_yap(kaynak, hedef, yontem, bitrate="192k", log=print,
               ilerleme=None):
    """Kaynağı sözsüz (enstrümantal) hâle getirip hedefe yazar."""
    if yontem in FFMPEG_YONTEMLERI:
        _ffmpeg_yontem(kaynak, hedef, yontem, bitrate)
    elif yontem.startswith("Yapay Zekâ"):
        _demucs_yontem(kaynak, hedef, bitrate, log, ilerleme)
    else:
        raise ValueError(f"Bilinmeyen yöntem: {yontem}")
    _etiket_kopyala(kaynak, hedef)
    return hedef


def _ffmpeg_yontem(kaynak, hedef, yontem, bitrate):
    ffdir = ffmpeg_bul()
    ffmpeg = os.path.join(ffdir, "ffmpeg.exe") if ffdir else "ffmpeg"
    filtre = FFMPEG_YONTEMLERI[yontem]
    komut = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
             "-i", kaynak, "-af", filtre, "-map_metadata", "0",
             "-id3v2_version", "3", "-b:a", bitrate, hedef]
    sonuc = subprocess.run(komut, capture_output=True, creationflags=_sessiz())
    if sonuc.returncode != 0:
        hata = sonuc.stderr.decode("utf-8", errors="replace")[-400:]
        raise RuntimeError(f"ffmpeg hatası: {hata}")


def _demucs_yontem(kaynak, hedef, bitrate, log, ilerleme):
    if not demucs_hazir():
        if ilerleme:
            ilerleme("kurulum")
        demucs_kur(log=log)

    import tempfile
    cikti_dir = os.path.join(tempfile.gettempdir(), "MuzikPro_demucs")
    os.makedirs(cikti_dir, exist_ok=True)

    ffdir = ffmpeg_bul()
    ortam = dict(os.environ)
    if ffdir:  # demucs mp3 yazımı için ffmpeg'i bulabilsin
        ortam["PATH"] = ffdir + os.pathsep + ortam.get("PATH", "")

    if ilerleme:
        ilerleme("ayirma")
    log("Yapay zekâ parçayı ayırıyor (1-2 dakika sürebilir) ...")
    komut = [_PY_EXE, "-m", "demucs", "--two-stems=vocals", "--mp3",
             "--mp3-bitrate", bitrate.rstrip("k"), "-o", cikti_dir, kaynak]
    sonuc = subprocess.run(komut, capture_output=True, creationflags=_sessiz(),
                           env=ortam)
    if sonuc.returncode != 0:
        hata = sonuc.stderr.decode("utf-8", errors="replace")[-500:]
        raise RuntimeError(f"Demucs hatası: {hata}")

    # Demucs çıktısı: <cikti_dir>/<model>/<parça adı>/no_vocals.mp3
    adaylar = glob.glob(os.path.join(cikti_dir, "*", "*", "no_vocals.mp3"))
    if not adaylar:
        raise RuntimeError("Demucs çıktısı bulunamadı.")
    en_yeni = max(adaylar, key=os.path.getmtime)
    os.replace(en_yeni, hedef)


def _etiket_kopyala(kaynak, hedef):
    """Kapak resmini korur (ses filtreleri kapak/etiketi düşürebilir)."""
    try:
        from . import etiketler
        veri = etiketler.kapak_oku(kaynak)
        if veri:
            etiketler.kapak_yaz_bytes(hedef, veri)
    except Exception:
        pass


def sozsuz_adi(yol):
    """'sarki.mp3' -> 'sarki (sözsüz).mp3' (çakışırsa numaralandırır)."""
    govde, uzanti = os.path.splitext(yol)
    aday = f"{govde} (sözsüz){uzanti}"
    sayac = 2
    while os.path.exists(aday):
        aday = f"{govde} (sözsüz {sayac}){uzanti}"
        sayac += 1
    return aday
