# -*- coding: utf-8 -*-
"""Yerleşik müzik çalar (pygame mixer) - oynat/duraklat/atla/ses düzeyi."""
import os
import time

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from mutagen.mp3 import MP3


class Oynatici:
    def __init__(self):
        self._hazir = False
        self.yol = None
        self.sure = 0.0
        self.caliyor = False
        self.duraklatildi = False
        self._konum0 = 0.0     # son başlangıç/duraklama konumu
        self._t0 = 0.0         # oynatmanın başladığı an (monotonic)
        self._ses = 0.8

    def _muzik(self):
        import pygame
        if not self._hazir:
            pygame.mixer.init()
            self._hazir = True
            pygame.mixer.music.set_volume(self._ses)
        return pygame.mixer.music

    # ------------------------------------------------------------ temel kontroller
    def cal(self, yol, konum=0.0):
        """Dosyayı (varsa verilen saniyeden) çalmaya başlar."""
        m = self._muzik()
        m.stop()
        m.load(yol)
        try:
            self.sure = MP3(yol).info.length
        except Exception:
            self.sure = 0.0
        konum = max(0.0, min(konum, max(self.sure - 0.2, 0.0)))
        m.play(start=konum)
        self.yol = yol
        self._konum0 = konum
        self._t0 = time.monotonic()
        self.caliyor = True
        self.duraklatildi = False

    def duraklat_devam(self):
        """Oynat/duraklat düğmesi; duraklatıldıysa sürdürür."""
        if not self.caliyor:
            if self.yol and os.path.exists(self.yol):
                self.cal(self.yol, self._konum0)
            return
        m = self._muzik()
        if self.duraklatildi:
            m.unpause()
            self._t0 = time.monotonic()
            self.duraklatildi = False
        else:
            self._konum0 = self.konum()
            m.pause()
            self.duraklatildi = True

    def durdur(self):
        if self._hazir:
            self._muzik().stop()
        self.caliyor = False
        self.duraklatildi = False
        self._konum0 = 0.0

    def atla(self, saniye):
        """Parçanın istenen saniyesine gider (çalıyorsa çalmaya devam eder)."""
        if not self.yol:
            return
        duraklatilmisti = self.duraklatildi
        self.cal(self.yol, saniye)
        if duraklatilmisti:
            self.duraklat_devam()

    def ses_ayarla(self, oran):
        self._ses = max(0.0, min(1.0, oran))
        if self._hazir:
            self._muzik().set_volume(self._ses)

    # ------------------------------------------------------------------ durum bilgisi
    def konum(self):
        if not self.caliyor:
            return self._konum0
        if self.duraklatildi:
            return self._konum0
        return min(self._konum0 + (time.monotonic() - self._t0), self.sure)

    def bitti_mi(self):
        """Parça doğal olarak sonlandıysa True."""
        if not (self.caliyor and not self.duraklatildi and self._hazir):
            return False
        import pygame
        return (not pygame.mixer.music.get_busy()
                and self.konum() >= self.sure - 1.0)

    def kapat(self):
        try:
            if self._hazir:
                import pygame
                pygame.mixer.quit()
        except Exception:
            pass
