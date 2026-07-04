# -*- coding: utf-8 -*-
"""El yazısı tarama - Google Gemini API (ücretsiz katman).

Ücretsiz API anahtarı: https://aistudio.google.com/apikey
(Google hesabı yeterli, kredi kartı istemez.)

Windows OCR basılı yazıda iyidir ama el yazısını okuyamaz; el yazısı
listeler bu modülle görüntü anlayan yapay zekâya gönderilir.
"""
import base64
import json
import mimetypes
import os
import urllib.request

ANAHTAR_ADRESI = "https://aistudio.google.com/apikey"

# Modeller sırayla denenir; Google eskisini kapatırsa sıradaki kullanılır
# (gelecekte API değişirse uygulama çalışmaya devam etsin diye).
MODELLER = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]

_KOMUT = (
    "Bu görüntüde bir müzik/şarkı listesi var (el yazısı olabilir). "
    "Listedeki HER şarkıyı ayrı bir satıra yaz. "
    "Kategori başlıkları (örn. Halay, Roman, Horon, Oyun havaları) tek başına "
    "şarkı değildir; onları satır olarak yazma ama şarkının YouTube'da kolay "
    "bulunması için tür adını şarkının sonuna ekle (örn. 'Delilo halay', "
    "'Müjgan roman havası'). Türkçe karakterleri doğru kullan. "
    "Sadece şarkı satırlarını yaz; açıklama, numara veya başka bir şey yazma."
)


def gorselden_sarkilar(yol, anahtar, zaman_asimi=90):
    """Görseli yapay zekâya gönderir, şarkı satırlarının listesini döndürür."""
    if not anahtar or not anahtar.strip():
        raise RuntimeError(
            "Yapay zekâ API anahtarı ayarlanmamış.\n"
            "Ayarlar sayfasından ücretsiz Gemini anahtarını gir:\n"
            + ANAHTAR_ADRESI)

    yol = os.path.abspath(yol)
    with open(yol, "rb") as f:
        veri = base64.b64encode(f.read()).decode("ascii")
    mime = mimetypes.guess_type(yol)[0] or "image/jpeg"

    govde = json.dumps({
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": mime, "data": veri}},
                {"text": _KOMUT},
            ],
        }],
    }).encode("utf-8")

    son_hata = None
    for model in MODELLER:
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent")
        istek = urllib.request.Request(
            url, data=govde, method="POST",
            headers={"Content-Type": "application/json",
                     "x-goog-api-key": anahtar.strip()})
        try:
            with urllib.request.urlopen(istek, timeout=zaman_asimi) as yanit:
                sonuc = json.loads(yanit.read().decode("utf-8"))
            metin = sonuc["candidates"][0]["content"]["parts"][0]["text"]
            return _satirlara_ayir(metin)
        except urllib.error.HTTPError as e:
            detay = ""
            try:
                detay = json.loads(e.read().decode("utf-8"))["error"]["message"]
            except Exception:
                pass
            if e.code in (401, 403) or "API key" in detay or "API_KEY" in detay:
                raise RuntimeError(
                    "API anahtarı geçersiz veya yetkisiz.\n"
                    "Ayarlar'dan anahtarı kontrol et. Ücretsiz anahtar:\n"
                    + ANAHTAR_ADRESI) from e
            if e.code == 429:
                raise RuntimeError(
                    "Ücretsiz kullanım sınırına ulaşıldı; birkaç dakika sonra "
                    "tekrar dene.") from e
            son_hata = f"{model}: HTTP {e.code} {detay[:120]}"
            continue  # model bulunamadı/emekliye ayrıldıysa sıradakini dene
        except Exception as e:
            son_hata = f"{model}: {e}"
            continue
    raise RuntimeError(f"Yapay zekâ servisine ulaşılamadı. ({son_hata})")


def _satirlara_ayir(metin):
    sarkilar = []
    for satir in metin.splitlines():
        s = satir.strip().strip("-•*").strip()
        # "1. Şarkı" gibi numaralandırmayı temizle
        if s[:3].strip().rstrip(".)").isdigit():
            s = s.lstrip("0123456789.) ").strip()
        if len(s) >= 3:
            sarkilar.append(s)
    return sarkilar
