# -*- coding: utf-8 -*-
"""
Stimmen-Tester – GUI
====================
Laedt ein gespeichertes Stimmprofil und spricht beliebigen Text.
Profil einmalig anlegen: python stimme_einpflegen.py <name>
"""

import os
import sys
import io
import time
import threading
import subprocess
from pathlib import Path

import tkinter as tk
from tkinter import ttk, scrolledtext

PROJECT_DIR  = Path(__file__).parent.resolve()
MODELS_DIR   = PROJECT_DIR / "models"
PROFILES_DIR = PROJECT_DIR / "stimmen_profile"
OUTPUT_DIR   = PROJECT_DIR / "test_output"

os.environ["HF_HOME"]            = str(MODELS_DIR / "huggingface")
os.environ["HF_HUB_CACHE"]       = str(MODELS_DIR / "huggingface" / "hub")
os.environ["TORCH_HOME"]          = str(MODELS_DIR / "torch")
os.environ["TRANSFORMERS_CACHE"]  = str(MODELS_DIR / "huggingface" / "transformers")
os.environ["TTS_HOME"]            = str(MODELS_DIR / "coqui")
os.environ["COQUI_TOS_AGREED"]    = "1"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BG     = "#2b2b2b"
BG2    = "#3c3f41"
FG     = "#bbbbbb"
ACCENT = "#4a9eff"
GREEN  = "#6aa84f"
RED    = "#cc4444"
FONT   = ("Segoe UI", 10)
MONO   = ("Consolas", 9)


class SprechenGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Stimmen-Tester")
        self.root.geometry("600x500")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.model = None
        self.profile_cache = {}
        self.last_output = None
        self._build_ui()
        self._lade_modell_async()
        self.root.mainloop()

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}

        # Titel
        tk.Label(self.root, text="Stimmen-Tester", font=("Segoe UI", 14, "bold"),
                 bg=BG, fg=ACCENT).pack(pady=(14, 4))

        # Stimme
        frame_stimme = tk.Frame(self.root, bg=BG)
        frame_stimme.pack(fill="x", **pad)
        tk.Label(frame_stimme, text="Stimme:", width=10, anchor="w",
                 bg=BG, fg=FG, font=FONT).pack(side="left")
        self.stimme_var = tk.StringVar()
        self.stimme_cb = ttk.Combobox(frame_stimme, textvariable=self.stimme_var,
                                      font=FONT, state="readonly", width=20)
        self.stimme_cb.pack(side="left", padx=(0, 8))
        self._refresh_profile_liste()
        tk.Button(frame_stimme, text="↺", command=self._refresh_profile_liste,
                  bg=BG2, fg=FG, font=FONT, relief="flat", cursor="hand2",
                  padx=6).pack(side="left")

        # Text
        frame_text = tk.Frame(self.root, bg=BG)
        frame_text.pack(fill="both", expand=True, **pad)
        tk.Label(frame_text, text="Text:", anchor="w",
                 bg=BG, fg=FG, font=FONT).pack(anchor="w")
        self.text_box = scrolledtext.ScrolledText(
            frame_text, height=6, font=FONT,
            bg=BG2, fg=FG, insertbackground=FG,
            relief="flat", wrap="word")
        self.text_box.pack(fill="both", expand=True, pady=(4, 0))
        self.text_box.insert("1.0", "Es war einmal ein Lindwurm namens Hildegunst.")

        # Buttons
        frame_btn = tk.Frame(self.root, bg=BG)
        frame_btn.pack(fill="x", **pad)
        self.btn_gen = tk.Button(
            frame_btn, text="▶  Sprechen", command=self._sprechen,
            bg=ACCENT, fg="white", font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2", padx=16, pady=6,
            state="disabled")
        self.btn_gen.pack(side="left", padx=(0, 8))
        self.btn_play = tk.Button(
            frame_btn, text="🔊  Abspielen", command=self._abspielen,
            bg=BG2, fg=FG, font=FONT,
            relief="flat", cursor="hand2", padx=12, pady=6,
            state="disabled")
        self.btn_play.pack(side="left")

        # Status-Log
        frame_log = tk.Frame(self.root, bg=BG)
        frame_log.pack(fill="both", expand=False, padx=12, pady=(0, 12))
        tk.Label(frame_log, text="Log:", anchor="w",
                 bg=BG, fg=FG, font=FONT).pack(anchor="w")
        self.log = scrolledtext.ScrolledText(
            frame_log, height=7, font=MONO,
            bg="#1e1e1e", fg=FG, insertbackground=FG,
            relief="flat", state="disabled")
        self.log.pack(fill="both")

    def _refresh_profile_liste(self):
        profile = sorted([p.stem for p in PROFILES_DIR.glob("*.pt")])
        self.stimme_cb["values"] = profile
        if profile and not self.stimme_var.get():
            self.stimme_var.set(profile[0])

    def _log(self, msg, color=None):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _lade_modell_async(self):
        self._log("Lade XTTS v2 Modell ...")
        threading.Thread(target=self._lade_modell, daemon=True).start()

    def _lade_modell(self):
        try:
            import contextlib
            import numpy as np
            import soundfile as sf
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
            # sys.stdout/stderr im Thread umleiten (verhindert Hängen ohne Konsole)
            _old_out, _old_err = sys.stdout, sys.stderr
            try:
                sys.stdout = sys.stderr = open(os.devnull, "w")
                from TTS.api import TTS
                device = "cuda" if torch.cuda.is_available() else "cpu"
                tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            finally:
                sys.stdout = _old_out
                sys.stderr = _old_err

            self.tts    = tts
            self.model  = tts.synthesizer.tts_model
            self.device = device
            self.np     = np
            self.sf     = sf
            self.torch  = torch

            elapsed = f"{time.time()-t0:.0f}s"
            gpu     = "CUDA" if device == "cuda" else "CPU"
            self.root.after(0, lambda: self._log(f"Modell geladen ({elapsed}) | {gpu} | Bereit."))
            self.root.after(0, lambda: self.btn_gen.configure(state="normal"))
        except Exception as e:
            err = str(e)
            self.root.after(0, lambda: self._log(f"FEHLER beim Laden: {err}"))

    def _lade_profil(self, stimme):
        if stimme not in self.profile_cache:
            pt_path = PROFILES_DIR / f"{stimme}.pt"
            data = self.torch.load(str(pt_path), map_location=self.device)
            self.profile_cache[stimme] = {
                "gpt_cond_latent":   data["gpt_cond_latent"].to(self.device),
                "speaker_embedding": data["speaker_embedding"].to(self.device),
            }
        return self.profile_cache[stimme]

    def _sprechen(self):
        stimme = self.stimme_var.get().strip()
        text   = self.text_box.get("1.0", "end").strip()
        if not stimme or not text:
            self._log("Bitte Stimme und Text eingeben.")
            return
        if not (PROFILES_DIR / f"{stimme}.pt").exists():
            self._log(f"Profil '{stimme}' nicht gefunden.")
            return
        self.btn_gen.configure(state="disabled")
        self.btn_play.configure(state="disabled")
        threading.Thread(target=self._gen_thread, args=(stimme, text), daemon=True).start()

    def _gen_thread(self, stimme, text):
        try:
            self.root.after(0, lambda: self._log(f"[{stimme}] '{text[:60]}'..."))
            prof = self._lade_profil(stimme)
            import contextlib
            t0 = time.time()
            with open(os.devnull, "w") as null:
                with contextlib.redirect_stdout(null), contextlib.redirect_stderr(null):
                    out = self.model.inference(
                        text=text,
                        language="de",
                        gpt_cond_latent=prof["gpt_cond_latent"],
                        speaker_embedding=prof["speaker_embedding"],
                        temperature=0.7,
                        repetition_penalty=10.0,
                        top_k=50,
                        top_p=0.85,
                        enable_text_splitting=True,
                    )
            wav_np = self.np.array(out["wav"], dtype=self.np.float32)
            if wav_np.ndim > 1:
                wav_np = wav_np.squeeze()
            gen_time = time.time() - t0
            audio_sec = len(wav_np) / 24000

            out_path = OUTPUT_DIR / f"sprechen_{stimme}.wav"
            self.sf.write(str(out_path), wav_np, 24000)
            self.last_output = out_path

            self.root.after(0, lambda: self._log(
                f"  -> {gen_time:.1f}s generiert, {audio_sec:.1f}s Audio | {out_path.name}"))
            self.root.after(0, lambda: self.btn_play.configure(state="normal"))
        except Exception as e:
            self.root.after(0, lambda: self._log(f"  FEHLER: {e}"))
        finally:
            self.root.after(0, lambda: self.btn_gen.configure(state="normal"))

    def _abspielen(self):
        if self.last_output and self.last_output.exists():
            os.startfile(str(self.last_output))


if __name__ == "__main__":
    SprechenGUI()
