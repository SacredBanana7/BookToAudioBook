# -*- coding: utf-8 -*-
"""
Stimme einpflegen – GUI
=======================
Erstellt ein XTTS v2 Speaker-Profil (.pt) aus einer oder mehreren
Audiodateien. Das Profil wird einmalig berechnet und kann danach
direkt in sprechen.py und demo_kapitel3.py genutzt werden.
"""

import os
import sys
import time
import contextlib
import threading
import tempfile
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext

PROJECT_DIR  = Path(__file__).parent.resolve()
MODELS_DIR   = PROJECT_DIR / "models"
SAMPLES_DIR  = PROJECT_DIR / "Audio Samples whatzapp"
PROFILES_DIR = PROJECT_DIR / "stimmen_profile"

os.environ["TORCH_HOME"]          = str(MODELS_DIR / "torch")
os.environ["TRANSFORMERS_CACHE"]  = str(MODELS_DIR / "huggingface" / "transformers")
os.environ["TTS_HOME"]            = str(MODELS_DIR / "coqui")
os.environ["COQUI_TOS_AGREED"]    = "1"

PROFILES_DIR.mkdir(parents=True, exist_ok=True)

BG     = "#2b2b2b"
BG2    = "#3c3f41"
FG     = "#bbbbbb"
ACCENT = "#4a9eff"
GREEN  = "#6aa84f"
FONT   = ("Segoe UI", 10)
MONO   = ("Consolas", 9)


class EinpflegenGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Stimme einpflegen")
        self.root.geometry("620x520")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.model  = None
        self.device = None
        self.selected_files = []
        self._build_ui()
        self._lade_modell_async()
        self.root.mainloop()

    def _build_ui(self):
        pad = {"padx": 12, "pady": 5}

        tk.Label(self.root, text="Stimme einpflegen", font=("Segoe UI", 14, "bold"),
                 bg=BG, fg=ACCENT).pack(pady=(14, 4))

        # Profilname
        f = tk.Frame(self.root, bg=BG)
        f.pack(fill="x", **pad)
        tk.Label(f, text="Profilname:", width=12, anchor="w",
                 bg=BG, fg=FG, font=FONT).pack(side="left")
        self.name_var = tk.StringVar()
        tk.Entry(f, textvariable=self.name_var, font=FONT,
                 bg=BG2, fg=FG, insertbackground=FG,
                 relief="flat", width=20).pack(side="left", ipady=4)
        tk.Label(f, text="(z.B. fred, jadusa, micha)", bg=BG, fg="#777",
                 font=("Segoe UI", 9)).pack(side="left", padx=8)

        # Audiodateien
        f2 = tk.Frame(self.root, bg=BG)
        f2.pack(fill="x", **pad)
        tk.Label(f2, text="Audiodatei(en):", width=12, anchor="w",
                 bg=BG, fg=FG, font=FONT).pack(side="left")
        tk.Button(f2, text="📂  Dateien wählen", command=self._dateien_waehlen,
                  bg=BG2, fg=FG, font=FONT, relief="flat",
                  cursor="hand2", padx=10, pady=4).pack(side="left", padx=(0, 8))
        tk.Button(f2, text="Samples-Ordner", command=self._auto_suchen,
                  bg=BG2, fg=FG, font=FONT, relief="flat",
                  cursor="hand2", padx=10, pady=4).pack(side="left")

        # Dateiliste
        f3 = tk.Frame(self.root, bg=BG)
        f3.pack(fill="x", padx=12, pady=(0, 4))
        self.datei_label = tk.Label(f3, text="Keine Datei ausgewählt.",
                                     bg=BG, fg="#888", font=("Segoe UI", 9),
                                     anchor="w", wraplength=560, justify="left")
        self.datei_label.pack(anchor="w")

        # Vorhandene Profile
        f4 = tk.Frame(self.root, bg=BG)
        f4.pack(fill="x", **pad)
        tk.Label(f4, text="Vorhandene Profile:", width=16, anchor="w",
                 bg=BG, fg=FG, font=FONT).pack(side="left")
        self.profile_label = tk.Label(f4, text="", bg=BG, fg=GREEN,
                                       font=("Segoe UI", 9))
        self.profile_label.pack(side="left")
        self._refresh_profile_liste()

        # Einpflegen-Button
        f5 = tk.Frame(self.root, bg=BG)
        f5.pack(fill="x", **pad)
        self.btn = tk.Button(
            f5, text="✔  Profil erstellen", command=self._einpflegen,
            bg=ACCENT, fg="white", font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2", padx=16, pady=7,
            state="disabled")
        self.btn.pack(side="left")
        self.status_lbl = tk.Label(f5, text="Modell wird geladen ...",
                                    bg=BG, fg="#888", font=FONT)
        self.status_lbl.pack(side="left", padx=12)

        # Log
        f6 = tk.Frame(self.root, bg=BG)
        f6.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        tk.Label(f6, text="Log:", anchor="w", bg=BG, fg=FG, font=FONT).pack(anchor="w")
        self.log = scrolledtext.ScrolledText(
            f6, font=MONO, bg="#1e1e1e", fg=FG,
            insertbackground=FG, relief="flat", state="disabled")
        self.log.pack(fill="both", expand=True)

    def _refresh_profile_liste(self):
        profile = [p.stem for p in sorted(PROFILES_DIR.glob("*.pt"))]
        self.profile_label.configure(
            text=", ".join(profile) if profile else "—")

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _dateien_waehlen(self):
        files = filedialog.askopenfilenames(
            title="Audiodateien wählen",
            initialdir=str(SAMPLES_DIR),
            filetypes=[("Audio", "*.ogg *.wav *.mp3 *.opus"), ("Alle", "*.*")])
        if files:
            self.selected_files = list(files)
            namen = [Path(f).name for f in self.selected_files]
            self.datei_label.configure(text="  ".join(namen))
            if not self.name_var.get():
                # Name aus erstem Dateinamen ableiten
                stem = Path(self.selected_files[0]).stem.lower()
                for w in ["audio", "whatzapp", "längeres", "von", "neu", "sample"]:
                    stem = stem.replace(w, "").strip()
                stem = stem.strip(" _-")
                if stem:
                    self.name_var.set(stem)

    def _auto_suchen(self):
        name = self.name_var.get().strip().lower()
        if not name:
            self._log("Bitte zuerst einen Profilnamen eingeben.")
            return
        found = sorted([
            f for f in SAMPLES_DIR.iterdir()
            if f.suffix.lower() in (".ogg", ".wav", ".mp3", ".opus")
            and name in f.stem.lower()
        ])
        if found:
            self.selected_files = [str(f) for f in found]
            self.datei_label.configure(text="  ".join(f.name for f in found))
            self._log(f"Auto-gefunden: {[f.name for f in found]}")
        else:
            self._log(f"Keine Datei für '{name}' in Samples-Ordner gefunden.")

    def _lade_modell_async(self):
        threading.Thread(target=self._lade_modell, daemon=True).start()

    def _lade_modell(self):
        try:
            import numpy as np
            import soundfile as sf
            import librosa
            import torch

            import torchaudio as _ta
            def _ta_load(filepath, frame_offset=0, num_frames=-1, **_kw):
                data, sr = sf.read(str(filepath), always_2d=True, dtype="float32")
                t = torch.from_numpy(data.T.copy())
                if frame_offset > 0: t = t[:, frame_offset:]
                if num_frames and num_frames > 0: t = t[:, :num_frames]
                return t, sr
            def _ta_save(filepath, src, sample_rate, **_kw):
                arr = src.squeeze().cpu().numpy()
                sf.write(str(filepath), arr if arr.ndim == 1 else arr.T, sample_rate)
            _ta.load = _ta_load
            _ta.save = _ta_save

            import transformers.pytorch_utils as _pt_utils
            if not hasattr(_pt_utils, "isin_mps_friendly"):
                _pt_utils.isin_mps_friendly = torch.isin

            t0 = time.time()
            _old_out, _old_err = sys.stdout, sys.stderr
            try:
                sys.stdout = sys.stderr = open(os.devnull, "w")
                from TTS.api import TTS
                device = "cuda" if torch.cuda.is_available() else "cpu"
                tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            finally:
                sys.stdout = _old_out
                sys.stderr = _old_err

            self.model   = tts.synthesizer.tts_model
            self.device  = device
            self.torch   = torch
            self.np      = np
            self.sf      = sf
            self.librosa = librosa

            self.root.after(0, lambda: self.status_lbl.configure(
                text=f"Bereit  |  {'CUDA' if device=='cuda' else 'CPU'}"))
            elapsed = f"{time.time()-t0:.0f}s"
            self.root.after(0, lambda: self._log(f"XTTS v2 geladen ({elapsed})"))
            self.root.after(0, lambda: self.btn.configure(state="normal"))
        except Exception as e:
            err = str(e)
            self.root.after(0, lambda: self._log(f"Ladefehler: {err}"))
            self.root.after(0, lambda: self.status_lbl.configure(text="Fehler!"))

    def _einpflegen(self):
        name = self.name_var.get().strip().lower()
        if not name:
            self._log("Bitte einen Profilnamen eingeben.")
            return
        if not self.selected_files:
            self._log("Bitte zuerst Audiodatei(en) auswählen.")
            return
        self.btn.configure(state="disabled")
        threading.Thread(
            target=self._einpflegen_thread,
            args=(name, list(self.selected_files)),
            daemon=True).start()

    def _einpflegen_thread(self, name, files):
        try:
            self.root.after(0, lambda: self._log(
                f"[{name}] Verarbeite {len(files)} Datei(en) ..."))
            TARGET_SR   = 22050
            MAX_REF_SEC = 30

            teile = []
            for f in files:
                audio, _ = self.librosa.load(f, sr=TARGET_SR, mono=True)
                teile.append(audio)
                self.root.after(0, lambda fn=Path(f).name, a=audio:
                    self._log(f"  {fn}: {len(a)/TARGET_SR:.1f}s"))

            combined = self.np.concatenate(teile)
            ref_len  = len(combined) / TARGET_SR
            if ref_len > MAX_REF_SEC:
                combined = combined[:int(MAX_REF_SEC * TARGET_SR)]
                ref_len  = MAX_REF_SEC

            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.close()
            self.sf.write(tmp.name, combined, TARGET_SR)

            self.root.after(0, lambda: self._log(
                f"  Referenz: {ref_len:.1f}s | berechne Latents ..."))
            t0 = time.time()

            with open(os.devnull, "w") as null:
                with contextlib.redirect_stdout(null), contextlib.redirect_stderr(null):
                    gpt_cond_latent, speaker_embedding = \
                        self.model.get_conditioning_latents(
                            audio_path=[tmp.name],
                            max_ref_length=MAX_REF_SEC,
                            gpt_cond_len=int(min(ref_len, 30)),
                            gpt_cond_chunk_len=6,
                        )

            os.unlink(tmp.name)
            out_path = PROFILES_DIR / f"{name}.pt"
            self.torch.save({
                "name":              name,
                "gpt_cond_latent":   gpt_cond_latent.cpu(),
                "speaker_embedding": speaker_embedding.cpu(),
                "sample_rate":       24000,
            }, str(out_path))

            gt = time.time() - t0
            self.root.after(0, lambda: self._log(
                f"[ok] Profil '{name}.pt' gespeichert ({gt:.1f}s)"))
            self.root.after(0, self._refresh_profile_liste)
        except Exception as e:
            self.root.after(0, lambda: self._log(f"FEHLER: {e}"))
        finally:
            self.root.after(0, lambda: self.btn.configure(state="normal"))


if __name__ == "__main__":
    EinpflegenGUI()
