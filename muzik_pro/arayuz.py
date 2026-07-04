# -*- coding: utf-8 -*-
"""Müzik İndirici PRO - modern arayüz (CustomTkinter)."""
import io
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from . import (SURUM, UYGULAMA_ADI, YAPIMCI, kaynak_yolu,
               sarkilari_oku, sarkilari_yaz)
from . import ayarlar as ayar_modulu
from . import etiketler, gorsel_tara, guncelleme, indirme, studyo, yapay_zeka
from .oynatici import Oynatici

MOR = "#7C3AED"
MOR_KOYU = "#6D28D9"
AMBER = "#F59E0B"
KIRMIZI = "#EF4444"
YESIL = "#22C55E"


class Uygulama(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.ayar = ayar_modulu.yukle()
        ctk.set_appearance_mode(self.ayar.get("tema", "dark"))
        ctk.set_default_color_theme("dark-blue")

        self.title(f"{UYGULAMA_ADI} v{SURUM}")
        self.geometry("1100x700")
        self.minsize(960, 620)
        try:
            self.iconbitmap(kaynak_yolu("varliklar", "logo.ico"))
        except Exception:
            pass

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._durum = {"calisiyor": False, "durdur": False}
        self._secili_mp3 = None
        self._studyo_dosya = None
        self.oynatici = Oynatici()
        self._surukleme = False

        self._kenar_cubugu()
        self._sayfalar()
        self._calar_cubugu()
        self.sayfa_goster("indirici")
        self.protocol("WM_DELETE_WINDOW", self._kapat)

        # Otomatik güncelleme: açılıştan kısa süre sonra arka planda denetle
        self.after(2500, self._oto_guncelleme)
        self.after(500, self._calar_guncelle)

    def _kapat(self):
        self.oynatici.kapat()
        self.destroy()

    # ------------------------------------------------------------- kenar çubuğu
    def _kenar_cubugu(self):
        cubuk = ctk.CTkFrame(self, width=220, corner_radius=0)
        cubuk.grid(row=0, column=0, sticky="nsw")
        cubuk.grid_propagate(False)
        cubuk.grid_rowconfigure(8, weight=1)

        try:
            logo = ctk.CTkImage(Image.open(kaynak_yolu("varliklar", "logo.png")),
                                size=(72, 72))
            ctk.CTkLabel(cubuk, image=logo, text="").grid(row=0, column=0,
                                                          pady=(24, 8))
        except Exception:
            pass
        ctk.CTkLabel(cubuk, text="Müzik İndirici",
                     font=ctk.CTkFont(size=19, weight="bold")).grid(row=1, column=0)
        ctk.CTkLabel(cubuk, text="PRO", text_color=AMBER,
                     font=ctk.CTkFont(size=13, weight="bold")).grid(row=2, column=0,
                                                                    pady=(0, 18))

        self._nav_butonlar = {}
        for satir, (anahtar, yazi) in enumerate([
                ("indirici", "↓  İndirici"),
                ("kutuphane", "♫  Kütüphane"),
                ("studyo", "✎  Stüdyo"),
                ("tarama", "◈  Görselden Tara"),
                ("ayarlar", "⚙  Ayarlar")], start=3):
            b = ctk.CTkButton(cubuk, text=yazi, anchor="w", height=42,
                              corner_radius=10, fg_color="transparent",
                              hover_color=MOR_KOYU,
                              font=ctk.CTkFont(size=14),
                              command=lambda a=anahtar: self.sayfa_goster(a))
            b.grid(row=satir, column=0, sticky="ew", padx=14, pady=3)
            self._nav_butonlar[anahtar] = b

        ctk.CTkLabel(cubuk, text=f"v{SURUM}  •  Yapımcı: {YAPIMCI}",
                     text_color="gray55",
                     font=ctk.CTkFont(size=12)).grid(row=9, column=0, pady=14)

    def sayfa_goster(self, anahtar):
        for a, sayfa in self._sayfa_sozlugu.items():
            sayfa.grid_remove()
            self._nav_butonlar[a].configure(fg_color="transparent")
        self._sayfa_sozlugu[anahtar].grid()
        self._nav_butonlar[anahtar].configure(fg_color=MOR)
        if anahtar == "kutuphane":
            self.kutuphane_yenile()

    def _sayfalar(self):
        self._sayfa_sozlugu = {
            "indirici": self._sayfa_indirici(),
            "kutuphane": self._sayfa_kutuphane(),
            "studyo": self._sayfa_studyo(),
            "tarama": self._sayfa_tarama(),
            "ayarlar": self._sayfa_ayarlar(),
        }
        for sayfa in self._sayfa_sozlugu.values():
            sayfa.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)

    # -------------------------------------------------------------- çalar çubuğu
    def _calar_cubugu(self):
        bar = ctk.CTkFrame(self, height=64, corner_radius=0)
        bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        bar.grid_columnconfigure(3, weight=1)

        self.calar_dugme = ctk.CTkButton(
            bar, text="▶", width=46, height=46, corner_radius=23,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=MOR, hover_color=MOR_KOYU,
            command=self._calar_oynat_duraklat)
        self.calar_dugme.grid(row=0, column=0, rowspan=2, padx=(14, 6), pady=8)
        ctk.CTkButton(bar, text="■", width=34, height=34, corner_radius=17,
                      fg_color="transparent", border_width=1,
                      border_color=MOR, hover_color=MOR_KOYU,
                      command=self._calar_durdur).grid(row=0, column=1,
                                                       rowspan=2, padx=4)

        self.calar_baslik = ctk.CTkLabel(bar, text="Bir şarkı seç ve çal…",
                                         anchor="w",
                                         font=ctk.CTkFont(size=13,
                                                          weight="bold"))
        self.calar_baslik.grid(row=0, column=2, columnspan=2, sticky="ew",
                               padx=(10, 8), pady=(8, 0))

        self.calar_slider = ctk.CTkSlider(bar, from_=0, to=1000,
                                          progress_color=MOR,
                                          button_color=AMBER,
                                          button_hover_color="#D97706",
                                          command=self._calar_kaydirildi)
        self.calar_slider.set(0)
        self.calar_slider.grid(row=1, column=2, columnspan=2, sticky="ew",
                               padx=(10, 8), pady=(0, 8))
        self.calar_slider.bind("<Button-1>",
                               lambda e: setattr(self, "_surukleme", True))
        self.calar_slider.bind("<ButtonRelease-1>", self._calar_birakildi)

        self.calar_zaman = ctk.CTkLabel(bar, text="0:00 / 0:00", width=90,
                                        text_color="gray60")
        self.calar_zaman.grid(row=0, column=4, rowspan=2, padx=6)

        ctk.CTkLabel(bar, text="🔊").grid(row=0, column=5, rowspan=2,
                                          padx=(8, 2))
        ses = ctk.CTkSlider(bar, from_=0, to=1, width=110, progress_color=MOR,
                            button_color=MOR, button_hover_color=MOR_KOYU,
                            command=lambda v: self.oynatici.ses_ayarla(v))
        ses.set(0.8)
        ses.grid(row=0, column=6, rowspan=2, padx=(0, 16))

    def oynat(self, yol):
        """Bir MP3'ü uygulama içi çalarda başlatır."""
        try:
            self.oynatici.cal(yol)
            self.calar_baslik.configure(text="♪ " + os.path.basename(yol))
            self.calar_dugme.configure(text="⏸")
        except Exception as e:
            messagebox.showerror(UYGULAMA_ADI, f"Çalınamadı:\n{e}")

    def _calar_oynat_duraklat(self):
        if not self.oynatici.yol:
            if self._secili_mp3:
                self.oynat(self._secili_mp3)
            return
        self.oynatici.duraklat_devam()
        self.calar_dugme.configure(
            text="▶" if (self.oynatici.duraklatildi
                         or not self.oynatici.caliyor) else "⏸")

    def _calar_durdur(self):
        self.oynatici.durdur()
        self.calar_dugme.configure(text="▶")
        self.calar_slider.set(0)
        self.calar_zaman.configure(text="0:00 / 0:00")

    def _calar_kaydirildi(self, deger):
        if self._surukleme and self.oynatici.sure:
            hedef = deger / 1000 * self.oynatici.sure
            self.calar_zaman.configure(
                text=f"{studyo.zaman_metni(hedef)} / "
                     f"{studyo.zaman_metni(self.oynatici.sure)}")

    def _calar_birakildi(self, _olay):
        self._surukleme = False
        if self.oynatici.yol and self.oynatici.sure:
            hedef = self.calar_slider.get() / 1000 * self.oynatici.sure
            self.oynatici.atla(hedef)
            self.calar_dugme.configure(text="⏸")

    def _calar_guncelle(self):
        o = self.oynatici
        if o.caliyor and not self._surukleme:
            if o.bitti_mi():
                self._calar_durdur()
            elif o.sure:
                self.calar_slider.set(o.konum() / o.sure * 1000)
                self.calar_zaman.configure(
                    text=f"{studyo.zaman_metni(o.konum())} / "
                         f"{studyo.zaman_metni(o.sure)}")
        self.after(500, self._calar_guncelle)

    # ------------------------------------------------------------ İNDİRİCİ sayfası
    def _sayfa_indirici(self):
        s = ctk.CTkFrame(self, fg_color="transparent")
        s.grid_columnconfigure(0, weight=1)
        s.grid_rowconfigure(1, weight=3)
        s.grid_rowconfigure(4, weight=2)

        ctk.CTkLabel(s, text="İndirici", font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.sarki_kutusu = ctk.CTkTextbox(s, font=ctk.CTkFont(size=13),
                                           corner_radius=10)
        self.sarki_kutusu.grid(row=1, column=0, sticky="nsew")
        self.sarki_kutusu.insert("1.0", "\n".join(sarkilari_oku()))

        ust = ctk.CTkFrame(s, fg_color="transparent")
        ust.grid(row=2, column=0, sticky="ew", pady=8)
        ctk.CTkLabel(ust, text="Kaynak:").pack(side="left")
        self.kaynak_secim = ctk.CTkOptionMenu(
            ust, values=indirme.KAYNAK_SECENEKLERI, width=130,
            fg_color=MOR, button_color=MOR_KOYU)
        self.kaynak_secim.set(self.ayar.get("kaynak", "Otomatik"))
        self.kaynak_secim.pack(side="left", padx=(6, 18))
        ctk.CTkLabel(ust, text="Kalite:").pack(side="left")
        self.kalite_secim = ctk.CTkOptionMenu(
            ust, values=["128", "192", "320"], width=90,
            fg_color=MOR, button_color=MOR_KOYU)
        self.kalite_secim.set(self.ayar.get("kalite", "192"))
        self.kalite_secim.pack(side="left", padx=(6, 18))
        ctk.CTkLabel(ust, text="kbps").pack(side="left")

        klasor_kutu = ctk.CTkFrame(s, fg_color="transparent")
        klasor_kutu.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        klasor_kutu.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(klasor_kutu, text="Klasör:").grid(row=0, column=0)
        self.klasor_degisken = tk.StringVar(
            value=self.ayar.get("indirme_klasoru"))
        ctk.CTkEntry(klasor_kutu, textvariable=self.klasor_degisken
                     ).grid(row=0, column=1, sticky="ew", padx=6)
        ctk.CTkButton(klasor_kutu, text="Seç", width=70, fg_color=MOR,
                      hover_color=MOR_KOYU,
                      command=self._klasor_sec).grid(row=0, column=2)

        self.log_kutusu = ctk.CTkTextbox(s, font=ctk.CTkFont(family="Consolas",
                                                             size=12),
                                         corner_radius=10, state="disabled")
        self.log_kutusu.grid(row=4, column=0, sticky="nsew")

        alt = ctk.CTkFrame(s, fg_color="transparent")
        alt.grid(row=5, column=0, sticky="ew", pady=(8, 0))
        alt.grid_columnconfigure(0, weight=1)
        self.ilerleme = ctk.CTkProgressBar(alt, progress_color=MOR)
        self.ilerleme.set(0)
        self.ilerleme.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.indir_butonu = ctk.CTkButton(
            alt, text="↓  İndirmeyi Başlat", height=44, width=200,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=MOR, hover_color=MOR_KOYU, command=self._indirmeyi_baslat)
        self.indir_butonu.grid(row=0, column=1)
        return s

    def _klasor_sec(self):
        secim = filedialog.askdirectory()
        if secim:
            self.klasor_degisken.set(os.path.normpath(secim))

    def log(self, mesaj):
        def _ekle():
            self.log_kutusu.configure(state="normal")
            self.log_kutusu.insert("end", mesaj + "\n")
            self.log_kutusu.see("end")
            self.log_kutusu.configure(state="disabled")
        self.after(0, _ekle)

    def _indirmeyi_baslat(self):
        if self._durum["calisiyor"]:
            self._durum["durdur"] = True
            self.indir_butonu.configure(text="Durduruluyor...")
            return
        satirlar = [s for s in self.sarki_kutusu.get("1.0", "end").splitlines()
                    if s.strip()]
        if not satirlar:
            messagebox.showwarning(UYGULAMA_ADI, "Şarkı listesi boş!")
            return
        sarkilari_yaz(satirlar)
        self.ayar.update(kaynak=self.kaynak_secim.get(),
                         kalite=self.kalite_secim.get(),
                         indirme_klasoru=self.klasor_degisken.get())
        ayar_modulu.kaydet(self.ayar)

        self._durum.update(calisiyor=True, durdur=False)
        self.indir_butonu.configure(text="■  Durdur", fg_color=KIRMIZI,
                                    hover_color="#B91C1C")
        self.ilerleme.set(0)

        def ilerleme_guncelle(i, toplam):
            self.after(0, lambda: self.ilerleme.set(i / max(toplam, 1)))

        def calis():
            try:
                indirme.indir(satirlar, self.klasor_degisken.get(),
                              kaynak=self.kaynak_secim.get(),
                              kalite=self.kalite_secim.get(),
                              log=self.log, ilerleme=ilerleme_guncelle,
                              durduruldu=lambda: self._durum["durdur"])
            finally:
                self._durum["calisiyor"] = False
                self.after(0, lambda: (
                    self.indir_butonu.configure(text="↓  İndirmeyi Başlat",
                                                fg_color=MOR,
                                                hover_color=MOR_KOYU),
                    self.ilerleme.set(1)))

        threading.Thread(target=calis, daemon=True).start()

    # ----------------------------------------------------------- KÜTÜPHANE sayfası
    def _sayfa_kutuphane(self):
        s = ctk.CTkFrame(self, fg_color="transparent")
        s.grid_columnconfigure(0, weight=3)
        s.grid_columnconfigure(1, weight=2)
        s.grid_rowconfigure(1, weight=1)

        baslik = ctk.CTkFrame(s, fg_color="transparent")
        baslik.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ctk.CTkLabel(baslik, text="Kütüphane — MP3 Düzenle",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        ctk.CTkButton(baslik, text="⟳ Yenile", width=90, fg_color=MOR,
                      hover_color=MOR_KOYU,
                      command=self.kutuphane_yenile).pack(side="right")

        self.mp3_listesi = ctk.CTkScrollableFrame(s, corner_radius=10)
        self.mp3_listesi.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.mp3_listesi.grid_columnconfigure(0, weight=1)

        panel = ctk.CTkFrame(s, corner_radius=10)
        panel.grid(row=1, column=1, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)

        self.kapak_gorseli = ctk.CTkLabel(panel, text="Kapak yok", width=190,
                                          height=190, corner_radius=10,
                                          fg_color=("gray80", "gray20"))
        self.kapak_gorseli.grid(row=0, column=0, pady=(16, 4))
        ctk.CTkButton(panel, text="Kapak Değiştir", width=140, fg_color=AMBER,
                      hover_color="#D97706", text_color="black",
                      command=self._kapak_degistir).grid(row=1, column=0, pady=4)

        self._etiket_girdileri = {}
        for satir, (anahtar, etiket) in enumerate(
                [("baslik", "Başlık"), ("sanatci", "Sanatçı"),
                 ("album", "Albüm"), ("tur", "Tür"),
                 ("dosya", "Dosya adı")], start=2):
            ctk.CTkLabel(panel, text=etiket, anchor="w"
                         ).grid(row=satir * 2, column=0, sticky="ew",
                                padx=16, pady=(6, 0))
            g = ctk.CTkEntry(panel)
            g.grid(row=satir * 2 + 1, column=0, sticky="ew", padx=16)
            self._etiket_girdileri[anahtar] = g

        butonlar = ctk.CTkFrame(panel, fg_color="transparent")
        butonlar.grid(row=14, column=0, pady=(12, 4))
        ctk.CTkButton(butonlar, text="✔ Kaydet", width=100, fg_color=YESIL,
                      hover_color="#15803D", text_color="black",
                      command=self._etiket_kaydet).pack(side="left", padx=4)
        ctk.CTkButton(butonlar, text="▶ Çal", width=70, fg_color=MOR,
                      hover_color=MOR_KOYU,
                      command=self._mp3_cal).pack(side="left", padx=4)
        ctk.CTkButton(butonlar, text="✖ Sil", width=70, fg_color=KIRMIZI,
                      hover_color="#B91C1C",
                      command=self._mp3_sil).pack(side="left", padx=4)
        ctk.CTkButton(panel, text="✎  Stüdyoda Aç (kes / ses / fade)",
                      fg_color="transparent", border_width=1,
                      border_color=MOR, hover_color=MOR_KOYU,
                      command=self._studyoda_ac).grid(row=15, column=0,
                                                      padx=16, pady=(0, 14),
                                                      sticky="ew")
        return s

    def _studyoda_ac(self):
        if not self._secim_gerekli():
            return
        self._studyo_dosya_ayarla(self._secili_mp3)
        self.sayfa_goster("studyo")

    def kutuphane_yenile(self):
        for cocuk in self.mp3_listesi.winfo_children():
            cocuk.destroy()
        klasor = self.klasor_degisken.get()
        dosyalar = etiketler.mp3_listele(klasor)
        if not dosyalar:
            ctk.CTkLabel(self.mp3_listesi,
                         text=f"Bu klasörde MP3 yok:\n{klasor}").grid(pady=20)
            return
        for satir, bilgi in enumerate(dosyalar):
            yazi = f"{bilgi['ad'][:58]}   ({etiketler.sure_metni(bilgi['sure'])})"
            b = ctk.CTkButton(self.mp3_listesi, text=yazi, anchor="w",
                              fg_color="transparent", hover_color=MOR_KOYU,
                              command=lambda y=bilgi["yol"]: self._mp3_sec(y))
            b.grid(row=satir, column=0, sticky="ew", pady=1)

    def _mp3_sec(self, yol):
        self._secili_mp3 = yol
        bilgi = etiketler.etiket_oku(yol)
        degerler = {"baslik": bilgi["baslik"], "sanatci": bilgi["sanatci"],
                    "album": bilgi["album"], "tur": bilgi["tur"],
                    "dosya": os.path.basename(yol)}
        for anahtar, girdi in self._etiket_girdileri.items():
            girdi.delete(0, "end")
            girdi.insert(0, degerler[anahtar])
        veri = etiketler.kapak_oku(yol)
        if veri:
            try:
                img = Image.open(io.BytesIO(veri))
                self._kapak_ref = ctk.CTkImage(img, size=(190, 190))
                self.kapak_gorseli.configure(image=self._kapak_ref, text="")
                return
            except Exception:
                pass
        self.kapak_gorseli.configure(image=None, text="Kapak yok")

    def _secim_gerekli(self):
        if not self._secili_mp3 or not os.path.exists(self._secili_mp3):
            messagebox.showinfo(UYGULAMA_ADI, "Önce soldan bir MP3 seç.")
            return False
        return True

    def _etiket_kaydet(self):
        if not self._secim_gerekli():
            return
        g = self._etiket_girdileri
        try:
            etiketler.etiket_yaz(self._secili_mp3, baslik=g["baslik"].get(),
                                 sanatci=g["sanatci"].get(),
                                 album=g["album"].get(), tur=g["tur"].get())
            yeni_ad = g["dosya"].get()
            if yeni_ad and yeni_ad != os.path.basename(self._secili_mp3):
                self._secili_mp3 = etiketler.yeniden_adlandir(
                    self._secili_mp3, yeni_ad)
            messagebox.showinfo(UYGULAMA_ADI, "Kaydedildi ✔")
            self.kutuphane_yenile()
        except Exception as e:
            messagebox.showerror(UYGULAMA_ADI, f"Kaydedilemedi:\n{e}")

    def _kapak_degistir(self):
        if not self._secim_gerekli():
            return
        resim = filedialog.askopenfilename(
            filetypes=[("Resim", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")])
        if not resim:
            return
        try:
            etiketler.kapak_yaz(self._secili_mp3, resim)
            self._mp3_sec(self._secili_mp3)
            messagebox.showinfo(UYGULAMA_ADI, "Kapak güncellendi ✔")
        except Exception as e:
            messagebox.showerror(UYGULAMA_ADI, f"Kapak değiştirilemedi:\n{e}")

    def _mp3_cal(self):
        if self._secim_gerekli():
            self.oynat(self._secili_mp3)

    def _mp3_sil(self):
        if not self._secim_gerekli():
            return
        ad = os.path.basename(self._secili_mp3)
        if messagebox.askyesno(UYGULAMA_ADI, f"Silinsin mi?\n\n{ad}"):
            os.remove(self._secili_mp3)
            self._secili_mp3 = None
            self.kutuphane_yenile()

    # -------------------------------------------------------------- STÜDYO sayfası
    def _sayfa_studyo(self):
        s = ctk.CTkFrame(self, fg_color="transparent")
        s.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(s, text="Stüdyo — Ses Düzenleme",
                     font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(s, text="Kes (trim), sesi yükselt/alçalt, fade, hız, "
                             "bas-tiz ve normalize.",
                     text_color="gray60").grid(row=1, column=0, sticky="w",
                                               pady=(0, 10))

        dosya_kutu = ctk.CTkFrame(s, corner_radius=10)
        dosya_kutu.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        dosya_kutu.grid_columnconfigure(0, weight=1)
        self.studyo_dosya_etiketi = ctk.CTkLabel(
            dosya_kutu, text="Dosya seçilmedi — Kütüphaneden 'Stüdyoda Aç' "
                             "veya buradan seç.", anchor="w")
        self.studyo_dosya_etiketi.grid(row=0, column=0, sticky="ew",
                                       padx=14, pady=10)
        ctk.CTkButton(dosya_kutu, text="Dosya Seç", width=100, fg_color=MOR,
                      hover_color=MOR_KOYU, command=self._studyo_dosya_sec
                      ).grid(row=0, column=1, padx=14)

        k = ctk.CTkFrame(s, corner_radius=10)
        k.grid(row=3, column=0, sticky="ew")
        k.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(k, text="Başlangıç (dk:sn)").grid(row=0, column=0,
                                                       padx=14, pady=(14, 2),
                                                       sticky="w")
        self.studyo_bas = ctk.CTkEntry(k, width=90, placeholder_text="0:00")
        self.studyo_bas.grid(row=0, column=1, sticky="w", pady=(14, 2))
        ctk.CTkLabel(k, text="Bitiş (dk:sn)").grid(row=0, column=2, padx=14,
                                                   pady=(14, 2), sticky="w")
        self.studyo_bit = ctk.CTkEntry(k, width=90,
                                       placeholder_text="boş = son")
        self.studyo_bit.grid(row=0, column=3, sticky="w", pady=(14, 2))

        self.studyo_ses = self._kaydirici(k, 1, "Ses kazancı", -12, 12, 0, "dB")
        self.studyo_bas_eq = self._kaydirici(k, 2, "Bas", -12, 12, 0, "dB")
        self.studyo_tiz_eq = self._kaydirici(k, 3, "Tiz", -12, 12, 0, "dB")
        self.studyo_fadein = self._kaydirici(k, 4, "Fade in", 0, 10, 0, "sn")
        self.studyo_fadeout = self._kaydirici(k, 5, "Fade out", 0, 10, 0, "sn")
        self.studyo_hiz = self._kaydirici(k, 6, "Hız", 0.5, 2.0, 1.0, "x")
        self.studyo_perde = self._kaydirici(k, 7, "Perde (pitch)", -12, 12, 0,
                                            "yarım ton")
        self.studyo_yanki = self._kaydirici(k, 8, "Yankı (reverb)", 0, 100, 0,
                                            "%")

        self.studyo_normalize = ctk.CTkCheckBox(
            k, text="Normalize (-14 LUFS standart ses)",
            fg_color=MOR, hover_color=MOR_KOYU)
        self.studyo_normalize.grid(row=9, column=0, columnspan=2,
                                   padx=14, pady=(6, 14), sticky="w")
        self.studyo_karaoke = ctk.CTkCheckBox(
            k, text="Karaoke (vokali azalt)",
            fg_color=MOR, hover_color=MOR_KOYU)
        self.studyo_karaoke.grid(row=9, column=2, columnspan=2,
                                 padx=14, pady=(6, 14), sticky="w")

        alt = ctk.CTkFrame(s, fg_color="transparent")
        alt.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        self.studyo_onayar = ctk.CTkOptionMenu(
            alt, values=["Önayar Seç…"] + list(studyo.ONAYARLAR),
            width=170, fg_color=MOR, button_color=MOR_KOYU,
            command=self._onayar_uygula)
        self.studyo_onayar.pack(side="left", padx=(0, 12))
        self.studyo_butonlar = []
        for yazi, renk, hover, mod in [
                ("▶ Önizle", MOR, MOR_KOYU, "onizle"),
                ("✔ Kopya Olarak Kaydet", YESIL, "#15803D", "kopya"),
                ("⚠ Üzerine Yaz", AMBER, "#D97706", "uzerine")]:
            b = ctk.CTkButton(alt, text=yazi, height=40, fg_color=renk,
                              hover_color=hover, text_color="black"
                              if renk != MOR else "white",
                              font=ctk.CTkFont(size=13, weight="bold"),
                              command=lambda m=mod: self._studyo_uygula(m))
            b.pack(side="left", padx=(0, 8))
            self.studyo_butonlar.append(b)
        ctk.CTkButton(alt, text="⟲ Sıfırla", height=40, fg_color="transparent",
                      border_width=1, border_color=MOR, hover_color=MOR_KOYU,
                      command=self._studyo_sifirla).pack(side="left")
        self.studyo_durum = ctk.CTkLabel(s, text="", text_color="gray60",
                                         anchor="w")
        self.studyo_durum.grid(row=5, column=0, sticky="ew", pady=(8, 0))
        return s

    def _kaydirici(self, ana, satir, etiket, dusuk, yuksek, varsayilan, birim):
        ctk.CTkLabel(ana, text=etiket).grid(row=satir, column=0, padx=14,
                                            pady=2, sticky="w")
        deger = ctk.CTkLabel(ana, text=f"{varsayilan:g} {birim}", width=64,
                             anchor="e", text_color=AMBER)
        deger.grid(row=satir, column=3, padx=14, sticky="e")
        kaydirici = ctk.CTkSlider(
            ana, from_=dusuk, to=yuksek, progress_color=MOR,
            button_color=MOR, button_hover_color=MOR_KOYU,
            command=lambda v, d=deger, b=birim: d.configure(
                text=f"{round(v, 1):g} {b}"))
        kaydirici.set(varsayilan)
        kaydirici.grid(row=satir, column=1, columnspan=2, sticky="ew",
                       padx=(0, 8))
        kaydirici._deger_etiketi = deger
        kaydirici._varsayilan = varsayilan
        kaydirici._birim = birim
        return kaydirici

    def _studyo_sifirla(self):
        for k in (self.studyo_ses, self.studyo_bas_eq, self.studyo_tiz_eq,
                  self.studyo_fadein, self.studyo_fadeout, self.studyo_hiz,
                  self.studyo_perde, self.studyo_yanki):
            k.set(k._varsayilan)
            k._deger_etiketi.configure(text=f"{k._varsayilan:g} {k._birim}")
        self.studyo_bas.delete(0, "end")
        self.studyo_bit.delete(0, "end")
        self.studyo_normalize.deselect()
        self.studyo_karaoke.deselect()
        self.studyo_onayar.set("Önayar Seç…")
        self.studyo_durum.configure(text="")

    def _onayar_uygula(self, ad):
        degerler = studyo.ONAYARLAR.get(ad)
        if not degerler:
            return
        esleme = [(self.studyo_ses, "ses"), (self.studyo_bas_eq, "bas"),
                  (self.studyo_tiz_eq, "tiz"), (self.studyo_fadein, "fadein"),
                  (self.studyo_fadeout, "fadeout"), (self.studyo_hiz, "hiz"),
                  (self.studyo_perde, "perde"), (self.studyo_yanki, "yanki")]
        for kaydirici, anahtar in esleme:
            deger = degerler[anahtar]
            kaydirici.set(deger)
            kaydirici._deger_etiketi.configure(
                text=f"{round(deger, 1):g} {kaydirici._birim}")
        (self.studyo_normalize.select if degerler["normalize"]
         else self.studyo_normalize.deselect)()
        (self.studyo_karaoke.select if degerler["karaoke"]
         else self.studyo_karaoke.deselect)()
        self.studyo_durum.configure(
            text=f"Önayar uygulandı: {ad} — 'Önizle' ile dinleyebilirsin.",
            text_color=AMBER)

    def _studyo_dosya_sec(self):
        yol = filedialog.askopenfilename(
            initialdir=self.klasor_degisken.get(),
            filetypes=[("MP3", "*.mp3")])
        if yol:
            self._studyo_dosya_ayarla(yol)

    def _studyo_dosya_ayarla(self, yol):
        self._studyo_dosya = yol
        try:
            sure = studyo.zaman_metni(studyo.sure_al(yol))
        except Exception:
            sure = "?"
        self.studyo_dosya_etiketi.configure(
            text=f"♪ {os.path.basename(yol)}   [{sure}]")

    def _studyo_uygula(self, mod):
        if not self._studyo_dosya or not os.path.exists(self._studyo_dosya):
            messagebox.showinfo(UYGULAMA_ADI, "Önce bir MP3 seç.")
            return
        if mod == "uzerine" and not messagebox.askyesno(
                UYGULAMA_ADI, "Orijinal dosyanın üzerine yazılacak. Emin misin?"):
            return
        # Dosya kilidini önlemek için ilgili dosya çalıyorsa durdur
        if self.oynatici.yol and (mod == "uzerine"
                                  or self.oynatici.yol == self._studyo_dosya):
            self._calar_durdur()
        try:
            b0 = studyo.zaman_coz(self.studyo_bas.get())
            b1 = studyo.zaman_coz(self.studyo_bit.get())
        except ValueError:
            messagebox.showerror(UYGULAMA_ADI,
                                 "Zamanları 'dk:sn' biçiminde gir (örn. 1:30).")
            return

        kaynak = self._studyo_dosya
        parametreler = dict(
            baslangic=b0, bitis=b1,
            kazanc_db=round(self.studyo_ses.get(), 1),
            bas_db=round(self.studyo_bas_eq.get(), 1),
            tiz_db=round(self.studyo_tiz_eq.get(), 1),
            fade_in=round(self.studyo_fadein.get(), 1),
            fade_out=round(self.studyo_fadeout.get(), 1),
            hiz=round(self.studyo_hiz.get(), 2),
            perde=round(self.studyo_perde.get(), 1),
            yanki=round(self.studyo_yanki.get() / 100, 2),
            karaoke=bool(self.studyo_karaoke.get()),
            normalize=bool(self.studyo_normalize.get()))

        for b in self.studyo_butonlar:
            b.configure(state="disabled")
        self.studyo_durum.configure(text="İşleniyor...", text_color=AMBER)

        def calis():
            import tempfile
            try:
                if mod == "onizle":
                    hedef = os.path.join(tempfile.gettempdir(),
                                         "MuzikPro_onizleme.mp3")
                    self.oynatici.durdur()  # dosya kilidini bırak
                    studyo.duzenle(kaynak, hedef, **parametreler)
                    self.after(0, lambda: self.oynat(hedef))
                    mesaj = "Önizleme uygulama içinde çalıyor (kalıcı değil)."
                elif mod == "kopya":
                    hedef = studyo.kopya_adi(kaynak)
                    studyo.duzenle(kaynak, hedef, **parametreler)
                    mesaj = f"Kaydedildi: {os.path.basename(hedef)}"
                else:  # uzerine
                    gecici = os.path.join(tempfile.gettempdir(),
                                          "MuzikPro_uzerine.mp3")
                    studyo.duzenle(kaynak, gecici, **parametreler)
                    os.replace(gecici, kaynak)
                    mesaj = "Orijinal dosya güncellendi."
                self.after(0, lambda: self.studyo_durum.configure(
                    text="✔ " + mesaj, text_color=YESIL))
            except Exception as e:
                hata = str(e)
                self.after(0, lambda: self.studyo_durum.configure(
                    text="✖ " + hata[:160], text_color=KIRMIZI))
            finally:
                self.after(0, lambda: [b.configure(state="normal")
                                       for b in self.studyo_butonlar])

        threading.Thread(target=calis, daemon=True).start()

    # -------------------------------------------------------------- TARAMA sayfası
    def _sayfa_tarama(self):
        s = ctk.CTkFrame(self, fg_color="transparent")
        s.grid_columnconfigure(0, weight=1)
        s.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(s, text="Görselden Tara",
                     font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(s, text="Ekran görüntüsü için 'Görsel Tara' (çevrimdışı), "
                             "el yazısı liste için 'El Yazısı Tara' (ücretsiz "
                             "yapay zekâ) kullan.",
                     text_color="gray60").grid(row=1, column=0, sticky="w",
                                               pady=(0, 10))

        ust = ctk.CTkFrame(s, fg_color="transparent")
        ust.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.tara_butonu = ctk.CTkButton(
            ust, text="◈  Görsel Tara", height=44, width=170,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=MOR, hover_color=MOR_KOYU, command=self._gorsel_tara)
        self.tara_butonu.pack(side="left")
        self.el_yazisi_butonu = ctk.CTkButton(
            ust, text="✎  El Yazısı Tara (Yapay Zekâ)", height=44, width=230,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=AMBER, hover_color="#D97706", text_color="black",
            command=self._el_yazisi_tara)
        self.el_yazisi_butonu.pack(side="left", padx=(8, 0))
        self.tara_durum = ctk.CTkLabel(ust, text="", text_color="gray60")
        self.tara_durum.pack(side="left", padx=12)

        self.tarama_sonuc = ctk.CTkTextbox(s, font=ctk.CTkFont(size=13),
                                           corner_radius=10)
        self.tarama_sonuc.grid(row=3, column=0, sticky="nsew")

        ctk.CTkButton(s, text="+  Bunları İndirici Listesine Ekle", height=40,
                      fg_color=YESIL, hover_color="#15803D", text_color="black",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._taramayi_aktar).grid(row=4, column=0,
                                                         sticky="ew", pady=(8, 0))
        return s

    def _gorsel_tara(self):
        dosyalar = filedialog.askopenfilenames(
            filetypes=[("Görseller", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")])
        if not dosyalar:
            return
        self.tara_butonu.configure(state="disabled")
        self.tara_durum.configure(text=f"{len(dosyalar)} görsel taranıyor...")

        def calis():
            butun = []
            hata = None
            for yol in dosyalar:
                try:
                    metin = gorsel_tara.gorselden_metin(yol)
                    butun.extend(gorsel_tara.metinden_sarkilar(metin))
                except Exception as e:
                    hata = str(e)

            def bitti():
                self.tara_butonu.configure(state="normal")
                if butun:
                    mevcut = self.tarama_sonuc.get("1.0", "end").strip()
                    if mevcut:
                        butun.insert(0, mevcut)
                    self.tarama_sonuc.delete("1.0", "end")
                    self.tarama_sonuc.insert("1.0", "\n".join(butun))
                    self.tara_durum.configure(
                        text=f"✔ {len(butun)} satır bulundu — kontrol edip ekle",
                        text_color=YESIL)
                else:
                    self.tara_durum.configure(
                        text=hata or "Görselde metin bulunamadı.",
                        text_color=KIRMIZI)
            self.after(0, bitti)

        threading.Thread(target=calis, daemon=True).start()

    def _el_yazisi_tara(self):
        """El yazısı listeyi ücretsiz Gemini yapay zekâsıyla okur."""
        anahtar = self.ayar.get("gemini_anahtar", "").strip()
        if not anahtar:
            if messagebox.askyesno(
                    UYGULAMA_ADI,
                    "El yazısı tarama için ücretsiz bir Gemini API anahtarı "
                    "gerekiyor (Google hesabı yeterli, kart istemez).\n\n"
                    "Anahtar alma sayfası açılsın mı? Aldıktan sonra "
                    "Ayarlar sayfasına yapıştır."):
                import webbrowser
                webbrowser.open(yapay_zeka.ANAHTAR_ADRESI)
            self.sayfa_goster("ayarlar")
            return
        dosyalar = filedialog.askopenfilenames(
            filetypes=[("Görseller", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")])
        if not dosyalar:
            return
        self.el_yazisi_butonu.configure(state="disabled")
        self.tara_durum.configure(
            text=f"{len(dosyalar)} görsel yapay zekâya gönderiliyor...",
            text_color=AMBER)

        def calis():
            butun, hata = [], None
            for yol in dosyalar:
                try:
                    butun.extend(yapay_zeka.gorselden_sarkilar(yol, anahtar))
                except Exception as e:
                    hata = str(e)

            def bitti():
                self.el_yazisi_butonu.configure(state="normal")
                if butun:
                    mevcut = self.tarama_sonuc.get("1.0", "end").strip()
                    if mevcut:
                        butun.insert(0, mevcut)
                    self.tarama_sonuc.delete("1.0", "end")
                    self.tarama_sonuc.insert("1.0", "\n".join(butun))
                    self.tara_durum.configure(
                        text=f"✔ {len(butun)} şarkı bulundu — kontrol edip ekle",
                        text_color=YESIL)
                else:
                    self.tara_durum.configure(text="", text_color=KIRMIZI)
                    messagebox.showwarning(
                        UYGULAMA_ADI, hata or "Görselde şarkı bulunamadı.")
            self.after(0, bitti)

        threading.Thread(target=calis, daemon=True).start()

    def _taramayi_aktar(self):
        yeni = [s for s in self.tarama_sonuc.get("1.0", "end").splitlines()
                if s.strip()]
        if not yeni:
            messagebox.showinfo(UYGULAMA_ADI, "Aktarılacak satır yok.")
            return
        mevcut = [s for s in self.sarki_kutusu.get("1.0", "end").splitlines()
                  if s.strip()]
        eklenen = [s for s in yeni if s not in mevcut]
        self.sarki_kutusu.insert("end", "\n" + "\n".join(eklenen))
        sarkilari_yaz(mevcut + eklenen)
        self.sayfa_goster("indirici")
        messagebox.showinfo(UYGULAMA_ADI,
                            f"{len(eklenen)} şarkı indirici listesine eklendi.")

    # ------------------------------------------------------------- AYARLAR sayfası
    def _sayfa_ayarlar(self):
        s = ctk.CTkFrame(self, fg_color="transparent")
        s.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(s, text="Ayarlar", font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        kart1 = ctk.CTkFrame(s, corner_radius=10)
        kart1.grid(row=1, column=0, sticky="ew", pady=6)
        kart1.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(kart1, text="Görünüm",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))
        self.tema_secim = ctk.CTkSegmentedButton(
            kart1, values=["Koyu", "Açık"], command=self._tema_degistir,
            selected_color=MOR, selected_hover_color=MOR_KOYU)
        self.tema_secim.set("Koyu" if self.ayar.get("tema") == "dark" else "Açık")
        self.tema_secim.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))

        kart2 = ctk.CTkFrame(s, corner_radius=10)
        kart2.grid(row=2, column=0, sticky="ew", pady=6)
        kart2.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(kart2, text="Güncelleme",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(kart2,
                     text="Otomatik güncelleme etkin: uygulama her açılışta "
                          "yeni sürümü kendiliğinden denetler,\nindirir ve kurar. "
                          "Kapatma seçeneği yoktur.",
                     justify="left",
                     text_color="gray60").grid(row=1, column=0, sticky="w",
                                               padx=16)
        self.guncelleme_durum = ctk.CTkLabel(kart2, text="", anchor="w",
                                             text_color="gray60")
        self.guncelleme_durum.grid(row=2, column=0, sticky="ew", padx=16)
        ctk.CTkButton(kart2, text="⟳  Şimdi Denetle", width=180,
                      fg_color=MOR, hover_color=MOR_KOYU,
                      command=self._guncelleme_denetle
                      ).grid(row=3, column=0, sticky="w", padx=16, pady=(4, 14))

        kart_ai = ctk.CTkFrame(s, corner_radius=10)
        kart_ai.grid(row=3, column=0, sticky="ew", pady=6)
        kart_ai.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(kart_ai, text="Yapay Zekâ — El Yazısı Tarama (ücretsiz)",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, sticky="w",
                            padx=16, pady=(12, 4))
        ctk.CTkLabel(kart_ai,
                     text="Google hesabınla aistudio.google.com/apikey "
                          "adresinden ÜCRETSİZ anahtar al (kart istemez), "
                          "aşağıya yapıştır.",
                     text_color="gray60", justify="left"
                     ).grid(row=1, column=0, columnspan=2, sticky="w", padx=16)
        self.gemini_girdi = ctk.CTkEntry(
            kart_ai, placeholder_text="Gemini API anahtarı (AIza...)",
            show="•")
        self.gemini_girdi.grid(row=2, column=0, sticky="ew",
                               padx=(16, 6), pady=6)
        if self.ayar.get("gemini_anahtar"):
            self.gemini_girdi.insert(0, self.ayar["gemini_anahtar"])
        ctk.CTkButton(kart_ai, text="Kaydet", width=90, fg_color=YESIL,
                      hover_color="#15803D", text_color="black",
                      command=self._gemini_kaydet).grid(row=2, column=1,
                                                        padx=(0, 16))
        ctk.CTkButton(kart_ai, text="Ücretsiz Anahtar Al ↗", width=180,
                      fg_color="transparent", border_width=1,
                      border_color=AMBER, hover_color="#78350F",
                      command=lambda: __import__("webbrowser").open(
                          yapay_zeka.ANAHTAR_ADRESI)
                      ).grid(row=3, column=0, sticky="w", padx=16,
                             pady=(0, 14))

        kart3 = ctk.CTkFrame(s, corner_radius=10)
        kart3.grid(row=4, column=0, sticky="ew", pady=6)
        ctk.CTkLabel(kart3, text="Hakkında",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))
        try:
            motor = indirme.motor_surumu()
        except Exception:
            motor = "?"
        bilgi = (f"{UYGULAMA_ADI}  v{SURUM}\n"
                 f"Yapımcı: {YAPIMCI}\n"
                 f"İndirme motoru: yt-dlp {motor}\n"
                 f"Kaynaklar: Otomatik yedekli (YouTube → SoundCloud)\n"
                 f"Görsel tarama: Windows OCR (çevrimdışı) + "
                 f"Gemini (el yazısı, ücretsiz)\n"
                 f"Stüdyo: ffmpeg (kes, ses, fade, hız, EQ, normalize)")
        ctk.CTkLabel(kart3, text=bilgi, justify="left", text_color="gray70"
                     ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))
        return s

    def _gemini_kaydet(self):
        self.ayar["gemini_anahtar"] = self.gemini_girdi.get().strip()
        ayar_modulu.kaydet(self.ayar)
        messagebox.showinfo(UYGULAMA_ADI,
                            "Anahtar kaydedildi ✔\nArtık Görselden Tara "
                            "sayfasında 'El Yazısı Tara' kullanılabilir.")

    def _tema_degistir(self, secim):
        tema = "dark" if secim == "Koyu" else "light"
        ctk.set_appearance_mode(tema)
        self.ayar["tema"] = tema
        ayar_modulu.kaydet(self.ayar)

    def _guncelleme_denetle(self):
        """Ayarlar sayfasındaki elle denetleme - aynı otomatik akışı kullanır."""
        self.guncelleme_durum.configure(text="Denetleniyor...", text_color=AMBER)

        def calis():
            url = self.ayar.get("guncelleme_url") or None
            durum, mesaj, _ = guncelleme.kontrol_et(url)

            def goster():
                if durum == "yeni_var":
                    self.guncelleme_durum.configure(
                        text="Yeni sürüm bulundu, indiriliyor...",
                        text_color=AMBER)
                    self._oto_guncelleme(hemen=True)
                elif durum == "guncel":
                    self.guncelleme_durum.configure(text="✔ " + mesaj,
                                                    text_color=YESIL)
                else:
                    self.guncelleme_durum.configure(text=mesaj[:120],
                                                    text_color="gray60")
            self.after(0, goster)

        threading.Thread(target=calis, daemon=True).start()

    def _oto_guncelleme(self, hemen=False):
        """Açılışta (ve elle denetlemede) sessiz otomatik güncelleme.

        Kurulum başlatıldığında uygulama beklemeden kapanır; sessiz kurulum
        dosyaların üzerine yazar ve kısa sürede tamamlanır.
        """
        def calis():
            url = self.ayar.get("guncelleme_url") or None
            basladi, _ = guncelleme.oto_guncelle(url)
            if basladi:
                self.after(0, self._kapat)

        threading.Thread(target=calis, daemon=True).start()


def calistir():
    Uygulama().mainloop()
