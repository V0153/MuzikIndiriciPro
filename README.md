<p align="center">
  <img src="varliklar/logo.png" width="120" alt="Müzik İndirici PRO">
</p>

<h1 align="center">Müzik İndirici PRO</h1>
<p align="center"><b>v1.34</b> • Yapımcı: <b>V™</b></p>

Modern arayüzlü, tam kapsamlı müzik indirme ve düzenleme uygulaması (Windows).

## Özellikler

- **↓ İndirici** — şarkı adı listesinden veya bağlantıdan MP3 indirme; kapak ve
  etiketler otomatik. Çoklu kaynak: *Otomatik* modda YouTube → SoundCloud
  yedekleme zinciri (bir API değişirse uygulama çalışmaya devam eder).
- **▶ Yerleşik Çalar** — alt çubukta oynat/duraklat, sarma ve ses düzeyi.
- **♫ Kütüphane** — MP3 etiketleri (başlık/sanatçı/albüm/tür), dosya adı ve
  albüm kapağı düzenleme.
- **✎ Stüdyo** — kes (trim), ses kazancı, bas/tiz EQ, fade in/out, hız,
  perde (pitch), yankı (reverb), karaoke (vokal azaltma), normalize ve
  7 hazır önayar (Bas Güçlü, Nightcore, Slowed + Reverb…).
- **⊘ Sözsüz Çıkar** — vokali kaldırıp enstrümantal üretir. 3 hızlı ffmpeg
  yöntemi (anında, çevrimdışı) + **Demucs** yapay zekâ ile stüdyo kalitesinde
  gerçek vokal ayırma (ilk kullanımda izole Python 3.12 ortamı indirilir).
- **◈ Görselden Tara** — müzik listesi ekran görüntüsünden şarkı adlarını
  çevrimdışı Windows OCR ile okur ve indirme listesine ekler.
- **✎ El Yazısı Tara** — el yazısı şarkı listelerini ücretsiz Gemini
  yapay zekâsıyla okur (aistudio.google.com/apikey'den ücretsiz anahtar).
- **Otomatik güncelleme** — her açılışta bu depodaki
  [`surum.json`](surum.json) denetlenir; yeni sürüm kendiliğinden iner ve kurulur.

## Kurulum

[Releases](../../releases) sayfasından son `MuzikIndiriciPro_Kurulum.exe`
dosyasını indirip çalıştırın. Python veya başka bir şey gerekmez.

## Geliştirici Notları

```
python MuzikIndiriciPro.py            # arayüz
python MuzikIndiriciPro.py --otomatik # sarkilar.txt'yi sessiz indir
python MuzikIndiriciPro.py --ocr x.png# görselden şarkı adı testi
```

Derleme: PyInstaller (`--collect-all customtkinter --collect-all winsdk
--collect-all pygame`), kurulum paketi: Inno Setup (`kurulum_pro.iss`).
ffmpeg ikilileri `ffmpeg/` klasörüne (gyan.dev essentials) açılmalıdır.

### Yeni sürüm çıkarma

1. `muzik_pro/__init__.py` içindeki `SURUM` değerini artır, exe + kurulumu derle.
2. Yeni `MuzikIndiriciPro_Kurulum.exe`'yi `vX.Y` etiketiyle Releases'a yükle.
3. `surum.json`'daki `surum` ve `indirme_url` alanlarını güncelle → tüm kurulu
   kopyalar bir sonraki açılışta otomatik güncellenir.

## Yasal Uyarı

Bu yazılımı yalnızca indirme hakkına sahip olduğunuz içerikler için kullanın.
