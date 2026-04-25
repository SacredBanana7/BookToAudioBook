# -*- coding: utf-8 -*-
"""
Hörbuch-Konverter – GUI-Anwendung
===================================
Erkennt Erzähler und Charaktere automatisch und weist ihnen
unterschiedliche Stimmen zu. Konvertiert Textdateien in
kapitelweise MP3-Hörbücher mit Microsoft Edge Neural TTS.

Module:
- zahlen_konverter: Deutsche Zahlen → Text
- text_parser: Kapitel-Erkennung, Dialog-Segmentierung
- charakter_engine: Geschlechts-Erkennung, Buch-Profile
- tts_engine: TTS-Abstraktionsschicht (Edge-TTS / Chatterbox)

Voraussetzung: pip install edge-tts
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import asyncio
import threading
import re
import os
import tempfile

# Eigene Module
from zahlen_konverter import zahlen_ersetzen
from text_parser import (
    text_bereinigen, kapitel_erkennen, parse_dialog_segmente,
    sprecher_finden, charaktere_sammeln
)
from charakter_engine import geschlecht_erkennen, BuchProfil
from tts_engine import (
    text_zu_mp3, mp3_zusammenfuegen,
    STIMMEN, STIMMEN_GESCHLECHT, STIMMEN_MAENNLICH, STIMMEN_WEIBLICH,
    STIMMEN_IDS, STIMMEN_NAMEN, DEFAULT_VOICE
)


# =============================================================================
# GUI Anwendung
# =============================================================================

class HoerbuchKonverter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hörbuch-Konverter")
        self.root.geometry("900x820")
        self.root.minsize(900, 820)
        self.root.configure(bg="#2b2b2b")

        self.text_content = ""
        self.chapters = []
        self.output_dir = ""
        self.is_converting = False
        self.charaktere = []  # [(name, count), ...]
        self.charakter_stimmen = {}  # {name: voice_id}
        self.multi_voice_enabled = tk.BooleanVar(value=True)
        self.buch_profil = None  # Optional: BuchProfil aus JSON

        self.setup_styles()
        self.setup_gui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#2b2b2b')
        style.configure('TLabel', background='#2b2b2b', foreground='#ffffff', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#61afef')
        style.configure('Sub.TLabel', font=('Segoe UI', 11, 'bold'), foreground='#c678dd')
        style.configure('Info.TLabel', font=('Segoe UI', 9), foreground='#abb2bf')
        style.configure('TButton', font=('Segoe UI', 10), padding=5)
        style.configure('Small.TButton', font=('Segoe UI', 8), padding=2)
        style.configure('Accent.TButton', font=('Segoe UI', 11, 'bold'))
        style.configure('TRadiobutton', background='#2b2b2b', foreground='#ffffff', font=('Segoe UI', 10))
        style.configure('TCheckbutton', background='#2b2b2b', foreground='#ffffff', font=('Segoe UI', 10))
        style.configure('TProgressbar', troughcolor='#3e4451', background='#61afef')
        style.configure('TLabelframe', background='#2b2b2b', foreground='#98c379')
        style.configure('TLabelframe.Label', background='#2b2b2b', foreground='#98c379', font=('Segoe UI', 10, 'bold'))
        style.configure('TCombobox', font=('Segoe UI', 9))

    def setup_gui(self):
        # Scrollbarer Hauptbereich
        canvas = tk.Canvas(self.root, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas, padding=20)

        self.scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Mausrad-Scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        main = self.scroll_frame

        # Titel
        ttk.Label(main, text="Hörbuch-Konverter", style='Title.TLabel').pack(anchor='w')
        ttk.Label(main, text="Multi-Stimmen Hörbuch-Erstellung mit KI-Sprachsynthese",
                  style='Info.TLabel').pack(anchor='w', pady=(0, 15))

        # --- Dateiauswahl ---
        file_frame = ttk.Frame(main)
        file_frame.pack(fill=tk.X, pady=5)
        ttk.Label(file_frame, text="Textdatei:").pack(side=tk.LEFT)
        self.file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_var, width=60).pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Durchsuchen...", command=self.datei_waehlen).pack(side=tk.LEFT)

        # --- Output-Ordner ---
        out_frame = ttk.Frame(main)
        out_frame.pack(fill=tk.X, pady=5)
        ttk.Label(out_frame, text="Ausgabe:    ").pack(side=tk.LEFT)
        self.out_var = tk.StringVar()
        ttk.Entry(out_frame, textvariable=self.out_var, width=60).pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        ttk.Button(out_frame, text="Durchsuchen...", command=self.output_waehlen).pack(side=tk.LEFT)

        # --- Optionen ---
        opt_frame = ttk.Frame(main)
        opt_frame.pack(fill=tk.X, pady=10)
        self.zahlen_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Zahlen ausschreiben", variable=self.zahlen_var).pack(side=tk.LEFT)
        self.bereinigen_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Text bereinigen", variable=self.bereinigen_var).pack(side=tk.LEFT, padx=20)
        ttk.Checkbutton(opt_frame, text="Multi-Stimmen (Charaktere)",
                        variable=self.multi_voice_enabled).pack(side=tk.LEFT, padx=20)

        # --- Buch-Profil ---
        profil_frame = ttk.Frame(main)
        profil_frame.pack(fill=tk.X, pady=5)
        ttk.Label(profil_frame, text="Buch-Profil:").pack(side=tk.LEFT)
        self.profil_var = tk.StringVar()
        ttk.Entry(profil_frame, textvariable=self.profil_var, width=50).pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        ttk.Button(profil_frame, text="Laden...", command=self.profil_laden).pack(side=tk.LEFT)
        self.profil_status = tk.StringVar(value="Kein Profil geladen")
        ttk.Label(profil_frame, textvariable=self.profil_status, style='Info.TLabel').pack(side=tk.LEFT, padx=10)

        # --- Erzähler-Stimme ---
        narrator_frame = ttk.LabelFrame(main, text=" Erzähler-Stimme ", padding=10)
        narrator_frame.pack(fill=tk.X, pady=5)

        self.narrator_voice = tk.StringVar(value="de-DE-ConradNeural")
        narrator_grid = ttk.Frame(narrator_frame)
        narrator_grid.pack(fill=tk.X)

        for i, (name, voice_id) in enumerate(STIMMEN.items()):
            col = i % 2
            row = i // 2
            ttk.Radiobutton(narrator_grid, text=name, variable=self.narrator_voice,
                          value=voice_id).grid(row=row, column=col*2, sticky='w', padx=5, pady=2)
            btn = ttk.Button(narrator_grid, text="Probe", width=5, style='Small.TButton',
                           command=lambda v=voice_id: self.stimme_testen(v))
            btn.grid(row=row, column=col*2+1, padx=2, pady=2)

        # --- Charakter-Stimmen ---
        self.char_frame = ttk.LabelFrame(main, text=" Erkannte Charaktere & Stimmen ", padding=10)
        self.char_frame.pack(fill=tk.X, pady=5)

        self.char_inner = ttk.Frame(self.char_frame)
        self.char_inner.pack(fill=tk.X)

        self.char_hint = ttk.Label(self.char_inner,
            text="Lade eine Textdatei, um Charaktere automatisch zu erkennen...",
            style='Info.TLabel')
        self.char_hint.pack(anchor='w')

        # --- Kapitel-Info ---
        self.info_frame = ttk.LabelFrame(main, text=" Erkannte Kapitel ", padding=10)
        self.info_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.chapter_list = tk.Listbox(self.info_frame, height=6, bg='#1e1e1e', fg='#abb2bf',
                                        font=('Consolas', 9), selectmode=tk.SINGLE)
        ch_scroll = ttk.Scrollbar(self.info_frame, orient=tk.VERTICAL, command=self.chapter_list.yview)
        self.chapter_list.configure(yscrollcommand=ch_scroll.set)
        self.chapter_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ch_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Vorschau ---
        preview_frame = ttk.Frame(main)
        preview_frame.pack(fill=tk.X, pady=5)
        ttk.Button(preview_frame, text="Dialog-Vorschau (ausgewähltes Kapitel)",
                   command=self.dialog_vorschau).pack(side=tk.LEFT)
        ttk.Label(preview_frame, text="  Wähle ein Kapitel oben, dann klicke für eine Multi-Stimmen-Vorschau",
                  style='Info.TLabel').pack(side=tk.LEFT, padx=10)

        # --- Fortschritt & Start ---
        bottom_frame = ttk.Frame(main)
        bottom_frame.pack(fill=tk.X, pady=10)

        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(bottom_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, pady=5)

        self.status_var = tk.StringVar(value="Bereit")
        ttk.Label(bottom_frame, textvariable=self.status_var, style='Info.TLabel').pack(anchor='w')

        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        self.start_btn = ttk.Button(btn_frame, text="  Hörbuch erstellen  ", style='Accent.TButton',
                                     command=self.konvertierung_starten)
        self.start_btn.pack(side=tk.RIGHT, pady=5)

    # --- Profil-Handling ---

    def profil_laden(self):
        """Lädt ein buchspezifisches Charakter-Profil (JSON)."""
        # Erst im book_profiles Ordner schauen
        initial_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "book_profiles")
        if not os.path.isdir(initial_dir):
            initial_dir = os.path.dirname(os.path.abspath(__file__))

        path = filedialog.askopenfilename(
            title="Buch-Profil auswählen",
            initialdir=initial_dir,
            filetypes=[("JSON-Dateien", "*.json"), ("Alle Dateien", "*.*")]
        )
        if path:
            try:
                self.buch_profil = BuchProfil(path)
                self.profil_var.set(path)
                n_chars = len(self.buch_profil.alle_charaktere())
                self.profil_status.set(f"{n_chars} Charaktere geladen")

                # Charakter-GUI aktualisieren wenn Text geladen
                if self.text_content:
                    self.charakter_gui_aktualisieren()
            except Exception as e:
                messagebox.showerror("Fehler", f"Profil konnte nicht geladen werden:\n{e}")

    # --- Datei-Handling ---

    def datei_waehlen(self):
        path = filedialog.askopenfilename(
            title="Textdatei auswählen",
            filetypes=[("Textdateien", "*.txt"), ("Alle Dateien", "*.*")]
        )
        if path:
            self.file_var.set(path)
            if not self.out_var.get():
                self.out_var.set(os.path.dirname(path))
            self.datei_laden(path)

    def output_waehlen(self):
        path = filedialog.askdirectory(title="Ausgabe-Ordner wählen")
        if path:
            self.out_var.set(path)

    def datei_laden(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.text_content = f.read()

            if self.bereinigen_var.get():
                self.text_content = text_bereinigen(self.text_content)

            # Kapitel erkennen
            self.chapters = kapitel_erkennen(self.text_content)
            self.chapter_list.delete(0, tk.END)
            for i, (titel, inhalt) in enumerate(self.chapters, 1):
                words = len(inhalt.split())
                minutes = round(words / 150)
                self.chapter_list.insert(tk.END,
                    f"  {i:02d}. {titel:<40} ({words} Wörter, ~{minutes} Min.)")

            # Charaktere erkennen
            self.status_var.set("Erkenne Charaktere...")
            self.root.update()
            self.charaktere = charaktere_sammeln(self.text_content)
            self.charakter_gui_aktualisieren()

            total_words = sum(len(c[1].split()) for c in self.chapters)
            total_min = round(total_words / 150)
            n_chars = len(self.charaktere)
            self.status_var.set(
                f"{len(self.chapters)} Kapitel | {total_words:,} Wörter | "
                f"~{total_min} Min. | {n_chars} Charaktere erkannt"
            )
        except Exception as e:
            messagebox.showerror("Fehler", f"Datei konnte nicht geladen werden:\n{e}")

    def _geschlecht_fuer_charakter(self, name):
        """Ermittelt das Geschlecht – Profil hat Vorrang vor Auto-Erkennung."""
        if self.buch_profil:
            g = self.buch_profil.geschlecht(name)
            if g:
                return g
        return geschlecht_erkennen(name, self.text_content)

    def _name_aufloesen(self, name):
        """Löst Alias-Namen auf, falls ein Profil geladen ist."""
        if self.buch_profil:
            return self.buch_profil.name_aufloesen(name)
        return name

    def charakter_gui_aktualisieren(self):
        """Aktualisiert die Charakter-Stimmen-Zuordnung in der GUI."""
        for widget in self.char_inner.winfo_children():
            widget.destroy()

        if not self.charaktere:
            ttk.Label(self.char_inner,
                text="Keine Charaktere mit wörtlicher Rede erkannt.",
                style='Info.TLabel').pack(anchor='w')
            return

        # Header
        header = ttk.Frame(self.char_inner)
        header.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(header, text="Charakter", width=20, font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        ttk.Label(header, text="Dialoge", width=8, font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        ttk.Label(header, text="Stimme", width=30, font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=10)

        narrator = self.narrator_voice.get()
        verf_m = [v for v in STIMMEN_MAENNLICH if v != narrator]
        verf_w = [v for v in STIMMEN_WEIBLICH if v != narrator]

        idx_m = 0
        idx_w = 0

        self.char_combos = {}

        for i, (name, count) in enumerate(self.charaktere[:15]):
            row = ttk.Frame(self.char_inner)
            row.pack(fill=tk.X, pady=1)

            # Name aufgelöst + Geschlecht
            display_name = self._name_aufloesen(name)
            geschlecht = self._geschlecht_fuer_charakter(name)
            geschlecht_label = " (m)" if geschlecht == 'm' else " (w)" if geschlecht == 'w' else " (?)"

            label_text = name
            if display_name != name:
                label_text = f"{name} → {display_name}"
            ttk.Label(row, text=label_text + geschlecht_label, width=25).pack(side=tk.LEFT)
            ttk.Label(row, text=str(count), width=6, style='Info.TLabel').pack(side=tk.LEFT)

            # Stimme zuweisen
            zuordnungs_name = display_name  # Kanonischer Name für Zuordnung
            if zuordnungs_name not in self.charakter_stimmen:
                if geschlecht == 'w' and verf_w:
                    self.charakter_stimmen[zuordnungs_name] = verf_w[idx_w % len(verf_w)]
                    idx_w += 1
                elif geschlecht == 'm' and verf_m:
                    self.charakter_stimmen[zuordnungs_name] = verf_m[idx_m % len(verf_m)]
                    idx_m += 1
                elif verf_m:
                    self.charakter_stimmen[zuordnungs_name] = verf_m[idx_m % len(verf_m)]
                    idx_m += 1
                else:
                    self.charakter_stimmen[zuordnungs_name] = narrator

            # Auch den Original-Namen verknüpfen
            if name != zuordnungs_name:
                self.charakter_stimmen[name] = self.charakter_stimmen[zuordnungs_name]

            combo_var = tk.StringVar(value=self.charakter_stimmen[zuordnungs_name])
            combo = ttk.Combobox(row, textvariable=combo_var, values=STIMMEN_IDS,
                               width=35, state='readonly')
            combo.pack(side=tk.LEFT, padx=10)

            btn = ttk.Button(row, text="Probe", width=5, style='Small.TButton',
                           command=lambda v=combo_var, n=name: self.charakter_probe(v.get(), n))
            btn.pack(side=tk.LEFT, padx=2)

            self.char_combos[zuordnungs_name] = combo_var

            combo_var.trace_add('write', lambda *args, n=zuordnungs_name, orig=name, v=combo_var:
                self._stimme_aktualisieren(n, orig, v.get()))

    def _stimme_aktualisieren(self, kanonisch, original, voice):
        """Aktualisiert Stimme für kanonischen und Original-Namen."""
        self.charakter_stimmen[kanonisch] = voice
        if original != kanonisch:
            self.charakter_stimmen[original] = voice

    # --- Vorschau & Test ---

    def stimme_testen(self, voice_id):
        """Testet eine Stimme mit Erzählertext."""
        if not self.text_content:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Textdatei laden.")
            return

        self.status_var.set("Erzeuge Vorschau...")
        self.root.update()

        def _generate():
            try:
                lines = self.text_content.split('\n')
                content_start = 0
                for i, line in enumerate(lines):
                    if len(line.strip()) > 50:
                        content_start = i
                        break
                preview_text = '\n'.join(lines[content_start:content_start + 3])
                preview_text = preview_text[:400]
                last_period = max(preview_text.rfind('.'), preview_text.rfind('!'), preview_text.rfind('?'))
                if last_period > 50:
                    preview_text = preview_text[:last_period + 1]
                if self.zahlen_var.get():
                    preview_text = zahlen_ersetzen(preview_text)

                temp_path = os.path.join(tempfile.gettempdir(), "hoerbuch_vorschau.mp3")
                asyncio.run(text_zu_mp3(preview_text, voice_id, temp_path))
                os.startfile(temp_path)
                self.root.after(0, lambda: self.status_var.set("Vorschau wird abgespielt..."))
            except Exception as e:
                err_msg = str(e)
                self.root.after(0, lambda msg=err_msg: messagebox.showerror("Fehler",
                    f"Vorschau fehlgeschlagen:\n{msg}"))

        threading.Thread(target=_generate, daemon=True).start()

    def charakter_probe(self, voice_id, charakter_name):
        """Spielt eine Probe mit der Stimme eines Charakters."""
        if not self.text_content:
            return

        self.status_var.set(f"Erzeuge Probe für {charakter_name}...")
        self.root.update()

        def _generate():
            try:
                dialog_text = None
                for match in re.finditer(r'[»„"](.+?)[«""]', self.text_content, re.DOTALL):
                    char = sprecher_finden(self.text_content, match.start(), match.end())
                    if char == charakter_name:
                        dialog_text = match.group(1).strip()
                        if len(dialog_text) > 20:
                            break

                if not dialog_text:
                    dialog_text = f"Ich bin {charakter_name} und dies ist meine Stimme."

                if len(dialog_text) > 300:
                    last_p = dialog_text[:300].rfind('.')
                    if last_p > 50:
                        dialog_text = dialog_text[:last_p + 1]

                if self.zahlen_var.get():
                    dialog_text = zahlen_ersetzen(dialog_text)

                temp_path = os.path.join(tempfile.gettempdir(), "hoerbuch_char_probe.mp3")
                asyncio.run(text_zu_mp3(dialog_text, voice_id, temp_path))
                os.startfile(temp_path)
                self.root.after(0, lambda: self.status_var.set(
                    f"Probe für {charakter_name} wird abgespielt..."))
            except Exception as e:
                err_msg = str(e)
                self.root.after(0, lambda msg=err_msg: messagebox.showerror("Fehler",
                    f"Probe fehlgeschlagen:\n{msg}"))

        threading.Thread(target=_generate, daemon=True).start()

    def dialog_vorschau(self):
        """Erzeugt eine Multi-Stimmen Vorschau des ausgewählten Kapitels."""
        sel = self.chapter_list.curselection()
        if not sel:
            messagebox.showinfo("Hinweis", "Bitte ein Kapitel in der Liste auswählen.")
            return

        idx = sel[0]
        _, inhalt = self.chapters[idx]

        self.status_var.set("Erzeuge Multi-Stimmen Vorschau...")
        self.root.update()

        def _generate():
            try:
                text = inhalt
                if self.zahlen_var.get():
                    text = zahlen_ersetzen(text)

                segmente = parse_dialog_segmente(text)

                vorschau_segmente = []
                total_chars = 0
                for seg in segmente:
                    if total_chars > 600:
                        break
                    vorschau_segmente.append(seg)
                    total_chars += len(seg[1])

                temp_dir = tempfile.mkdtemp(prefix="hoerbuch_preview_")
                segment_dateien = []

                narrator_voice = self.narrator_voice.get()

                for i, (typ, seg_text, charakter) in enumerate(vorschau_segmente):
                    if not seg_text.strip():
                        continue

                    if typ == 'dialog' and charakter and self.multi_voice_enabled.get():
                        # Alias auflösen
                        resolved = self._name_aufloesen(charakter)
                        voice = self.charakter_stimmen.get(resolved,
                                self.charakter_stimmen.get(charakter, narrator_voice))
                    else:
                        voice = narrator_voice

                    seg_path = os.path.join(temp_dir, f"seg_{i:04d}.mp3")
                    asyncio.run(text_zu_mp3(seg_text, voice, seg_path))
                    segment_dateien.append(seg_path)

                output_path = os.path.join(tempfile.gettempdir(), "hoerbuch_multi_preview.mp3")
                mp3_zusammenfuegen(segment_dateien, output_path)

                for f in segment_dateien:
                    os.remove(f)
                os.rmdir(temp_dir)

                os.startfile(output_path)
                self.root.after(0, lambda: self.status_var.set("Multi-Stimmen Vorschau wird abgespielt..."))

            except Exception as e:
                err_msg = str(e)
                self.root.after(0, lambda msg=err_msg: messagebox.showerror("Fehler",
                    f"Vorschau fehlgeschlagen:\n{msg}"))

        threading.Thread(target=_generate, daemon=True).start()

    # --- Konvertierung ---

    def konvertierung_starten(self):
        if not self.text_content or not self.chapters:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Textdatei laden.")
            return
        if not self.out_var.get():
            messagebox.showinfo("Hinweis", "Bitte einen Ausgabe-Ordner wählen.")
            return
        if self.is_converting:
            return

        self.is_converting = True
        self.start_btn.configure(state='disabled')
        self.output_dir = self.out_var.get()

        threading.Thread(target=self._konvertieren, daemon=True).start()

    def _konvertieren(self):
        try:
            narrator_voice = self.narrator_voice.get()
            total = len(self.chapters)
            os.makedirs(self.output_dir, exist_ok=True)
            use_multi = self.multi_voice_enabled.get() and len(self.charaktere) > 0

            for ch_idx, (titel, inhalt) in enumerate(self.chapters, 1):
                self.root.after(0, lambda i=ch_idx, t=titel:
                    self.status_var.set(f"[{i}/{total}] {t}"))
                self.root.after(0, lambda i=ch_idx:
                    self.progress_var.set((i - 1) / total * 100))

                text = inhalt
                if self.zahlen_var.get():
                    text = zahlen_ersetzen(text)

                output_path = os.path.join(self.output_dir, f"kapitel_{ch_idx:02d}.mp3")

                if use_multi:
                    segmente = parse_dialog_segmente(text)
                    temp_dir = tempfile.mkdtemp(prefix=f"hoerbuch_ch{ch_idx:02d}_")
                    segment_dateien = []

                    for seg_idx, (typ, seg_text, charakter) in enumerate(segmente):
                        if not seg_text.strip():
                            continue

                        if typ == 'dialog' and charakter:
                            resolved = self._name_aufloesen(charakter)
                            voice = self.charakter_stimmen.get(resolved,
                                    self.charakter_stimmen.get(charakter, narrator_voice))
                        else:
                            voice = narrator_voice

                        seg_path = os.path.join(temp_dir, f"seg_{seg_idx:04d}.mp3")
                        asyncio.run(text_zu_mp3(seg_text, voice, seg_path))
                        segment_dateien.append(seg_path)

                    mp3_zusammenfuegen(segment_dateien, output_path)

                    for f in segment_dateien:
                        try:
                            os.remove(f)
                        except:
                            pass
                    try:
                        os.rmdir(temp_dir)
                    except:
                        pass
                else:
                    asyncio.run(text_zu_mp3(text, narrator_voice, output_path))

            self.root.after(0, lambda: self.progress_var.set(100))
            self.root.after(0, lambda: self.status_var.set(
                f"Fertig! {total} MP3-Dateien in: {self.output_dir}"))
            self.root.after(0, lambda: messagebox.showinfo("Fertig!",
                f"Hörbuch erfolgreich erstellt!\n\n"
                f"{total} Kapitel als MP3 gespeichert in:\n{self.output_dir}\n\n"
                f"{'Multi-Stimmen aktiv' if use_multi else 'Einzel-Stimme'}"))
            try:
                os.startfile(self.output_dir)
            except:
                pass

        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda msg=err_msg: messagebox.showerror("Fehler",
                f"Konvertierung fehlgeschlagen:\n{msg}"))
            self.root.after(0, lambda: self.status_var.set("Fehler bei Konvertierung"))
        finally:
            self.is_converting = False
            self.root.after(0, lambda: self.start_btn.configure(state='normal'))

    def run(self):
        self.root.mainloop()


# =============================================================================
# Start
# =============================================================================

if __name__ == "__main__":
    app = HoerbuchKonverter()
    app.run()
