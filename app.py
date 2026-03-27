"""Vidra - powered by Sheri Akhtamov | v7 (2026 Motion Daylight UI)"""

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image as PilImage

RESAMPLE_LANCZOS = getattr(
    getattr(PilImage, "Resampling", None), "LANCZOS", getattr(PilImage, "LANCZOS", 1)
)

# Форсируем светлую тему
ctk.set_appearance_mode("light")

# ==========================================
# 🎨 2026 AERO GLASS PREMIUM PALETTE (LIGHT)
# ==========================================
# Ультрасовременный "воздушный" дизайн. Чистота, негативное пространство, мягкие контрасты.
BG_APP = "#F2F6FC"
BG_LAYER = "#E7EEF8"
BG_BLOB_A = "#E4F0FF"
BG_BLOB_B = "#EAFBF6"
BG_BLOB_C = "#FFF3EA"

GLASS_BG = "#FFFFFF"
GLASS_BG_SOFT = "#F7FAFF"
GLASS_BORDER = "#D6E1EF"
GLASS_BORDER_FOCUS = "#A3BCD8"

PRI = "#0E6BFF"
PRI_H = "#0A56CC"
PRI_L = "#E8F1FF"
PRI_MUTED = "#7FAEF6"

TEAL = "#14B8A6"
TEAL_H = "#0F9487"
TEAL_L = "#EAFBF8"

PLUM = "#FF7B5B"
PLUM_H = "#E26041"
PLUM_L = "#FFF1EA"

TEXT_MAIN = "#0C1B2F"
TEXT_SEC = "#405670"
TEXT_TERT = "#8597AD"

OK = "#16B364"
OK_H = "#139255"
OK_L = "#EAF9F1"

ERR = "#E5484D"
ERR_H = "#C93A3F"
ERR_L = "#FDEEEE"

WARN = "#F59E0B"
WARN_L = "#FFF7E8"

SHADOW_SOFT = "#DDE7F4"
SHADOW_STRONG = "#C9D8EA"

FONT_FAMILY = "Segoe UI Variable Text" if sys.platform == "win32" else "SF Pro Text"
FONT_FAMILY_FALLBACK = "Segoe UI"

DISPLAY = (FONT_FAMILY, 32, "bold")
H1 = (FONT_FAMILY, 24, "bold")
H2 = (FONT_FAMILY, 19, "bold")
H3 = (FONT_FAMILY, 16, "bold")
BODY_L = (FONT_FAMILY, 15)
BODY = (FONT_FAMILY, 14)
BODY_BOLD = (FONT_FAMILY, 14, "bold")
SMALL = (FONT_FAMILY, 12)
SMALL_BOLD = (FONT_FAMILY, 12, "bold")
CODE = ("Cascadia Code", 12)


# ==========================================
# ⚙️ БЭКЕНД РУТИЛИТЫ (НЕТРОНУТО)
# ==========================================
def _popen_hidden(cmd, **kw):
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        kw["startupinfo"] = si
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    return subprocess.Popen(cmd, **kw)


def _run_hidden(cmd, **kw):
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        kw["startupinfo"] = si
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    return subprocess.run(cmd, **kw)


def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def get_ytdlp():
    for n in ("yt-dlp_bundled.exe", "yt-dlp.exe", "yt-dlp"):
        p = resource_path(n)
        if os.path.isfile(p):
            return p
    return shutil.which("yt-dlp") or shutil.which("yt-dlp.exe") or "yt-dlp"


def get_ffmpeg():
    for n in ("ffmpeg.exe", "ffmpeg", "ffmpeg_bundled.exe"):
        p = resource_path(n)
        if os.path.isfile(p):
            return p
    return shutil.which("ffmpeg")


def friendly_size(b):
    if not b:
        return ""
    for u in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{int(b)} {u}" if u == "B" else f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"


def fmt_dur(s):
    if s in (None, ""):
        return "—"
    try:
        total = int(float(s))
    except (TypeError, ValueError):
        return "—"
    h, r = divmod(total, 3600)
    m, sec = divmod(r, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def ts():
    return datetime.now().strftime("%H:%M:%S")


def _hex_to_rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*[max(0, min(255, int(v))) for v in rgb])


def mix_color(color_a, color_b, t):
    t = max(0.0, min(1.0, float(t)))
    a = _hex_to_rgb(color_a)
    b = _hex_to_rgb(color_b)
    return _rgb_to_hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))



QUALITY_PRESETS = [
    {
        "label": "Лучшее качество",
        "sub": "авто",
        "fmt": "bestvideo+bestaudio/best",
        "h": 9999,
    },
    {
        "label": "4K",
        "sub": "до 2160p",
        "fmt": "bestvideo[height<=2160]+bestaudio/bestvideo+bestaudio/best",
        "h": 2160,
    },
    {
        "label": "Full HD",
        "sub": "до 1080p",
        "fmt": "bestvideo[height<=1080]+bestaudio/bestvideo+bestaudio/best",
        "h": 1080,
    },
    {
        "label": "HD",
        "sub": "до 720p",
        "fmt": "bestvideo[height<=720]+bestaudio/bestvideo+bestaudio/best",
        "h": 720,
    },
    {
        "label": "SD",
        "sub": "до 480p",
        "fmt": "bestvideo[height<=480]+bestaudio/bestvideo+bestaudio/best",
        "h": 480,
    },
    {
        "label": "360p",
        "sub": "до 360p",
        "fmt": "bestvideo[height<=360]+bestaudio/bestvideo+bestaudio/best",
        "h": 360,
    },
    {"label": "Только аудио", "sub": "MP3", "fmt": "bestaudio/best", "h": 0},
]


def parse_raw_formats(info):
    out = []
    seen = {}
    for fmt in reversed(info.get("formats", [])):
        vid = fmt.get("vcodec", "none")
        aud = fmt.get("acodec", "none")
        is_audio_only = not vid or vid == "none"
        ha = bool(aud and aud != "none")
        if not is_audio_only and not fmt.get("height") and not fmt.get("width"):
            is_audio_only = True
        if is_audio_only and not ha:
            continue

        h = fmt.get("height")
        fps = fmt.get("fps")
        ext = fmt.get("ext", "?")
        fs = fmt.get("filesize") or fmt.get("filesize_approx")
        tbr = fmt.get("tbr")
        fid = fmt.get("format_id", "")
        key = (h, fps, ext, ha, is_audio_only)
        if key in seen:
            prev_idx = seen[key]
            if out[prev_idx]["id"].endswith("-1") and not fid.endswith("-1"):
                out[prev_idx]["id"] = fid
            continue
        seen[key] = len(out)
        parts = []
        if not is_audio_only:
            if h:
                parts.append(f"{h}p")
            if fps and fps > 30:
                parts.append(f"{int(fps)}fps")
        else:
            parts.append("Аудио")
            if tbr:
                parts.append(f"{int(tbr)}kbps")

        parts.append(ext.upper())
        if fs:
            parts.append(friendly_size(fs))
        elif tbr and not is_audio_only:
            parts.append(f"~{tbr:.0f}k")

        lbl = " · ".join(parts) + (
            "" if ha or is_audio_only else "  (без звука)"
        )
        out.append(
            {
                "id": fid,
                "label": lbl,
                "h": h or 0,
                "audio_only": is_audio_only,
                "has_audio": ha,
                "tbr": tbr or 0,
                "protocol": fmt.get("protocol", ""),
            }
        )
    out.sort(key=lambda x: x["h"], reverse=True)
    return out[:25]


class QueueItem:
    def __init__(
        self, url, fmt, title, is_pl=False, count=0, cmd=None, audio_only=False
    ):
        self.url = url
        self.fmt = fmt
        self.title = title
        self.is_pl = is_pl
        self.count = count
        self.status = "waiting"
        self.cmd = cmd
        self.audio_only = audio_only


# ==========================================
# 💎 UI КОМПОНЕНТЫ
# ==========================================
class GlassCard(ctk.CTkFrame):
    def __init__(self, master, **kw):
        kw.setdefault("fg_color", GLASS_BG)
        kw.setdefault("corner_radius", 20)
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", GLASS_BORDER)
        super().__init__(master, **kw)


class FloatingEntry(ctk.CTkEntry):
    def __init__(self, master, **kw):
        kw.setdefault("font", BODY_L)
        kw.setdefault("height", 48)
        kw.setdefault("fg_color", GLASS_BG)
        kw.setdefault("border_color", GLASS_BORDER)
        kw.setdefault("border_width", 1)
        kw.setdefault("text_color", TEXT_MAIN)
        kw.setdefault("placeholder_text_color", TEXT_TERT)
        kw.setdefault("corner_radius", 12)
        super().__init__(master, **kw)


class MotionButton(ctk.CTkButton):
    def __init__(self, master, **kw):
        if "border_color" in kw:
            kw.setdefault("border_width", 1)
        else:
            kw.setdefault("border_width", 0)
        kw.setdefault("corner_radius", 12)
        super().__init__(master, **kw)


class HeroButton(ctk.CTkButton):
    def __init__(self, master, **kw):
        kw.setdefault("height", 44)
        kw.setdefault("fg_color", PRI)
        kw.setdefault("hover_color", PRI_H)
        kw.setdefault("text_color", "white")
        kw.setdefault("corner_radius", 12)
        kw.setdefault("font", BODY_BOLD)
        kw.setdefault("border_width", 0)
        super().__init__(master, **kw)


class PillButton(ctk.CTkButton):
    def __init__(self, master, **kw):
        kw.setdefault("height", 38)
        kw.setdefault("fg_color", GLASS_BG_SOFT)
        kw.setdefault("hover_color", PRI_L)
        kw.setdefault("text_color", TEXT_SEC)
        kw.setdefault("border_color", GLASS_BORDER)
        kw.setdefault("border_width", 1)
        kw.setdefault("corner_radius", 12)
        kw.setdefault("font", BODY_BOLD)
        super().__init__(master, **kw)


# ==========================================
# 🚀 ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ==========================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Vidra 2026 - Motion Daylight")
        self.geometry("1360x920")
        self.minsize(1100, 800)
        self.configure(fg_color=BG_APP)

        # Данные
        self._info = {}
        self._raw_formats = []
        self._is_playlist = False
        self._fetch_thread = None
        self._dl_thread = None
        self._mq = queue.Queue()
        self._dl_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        self._dl_queue = []
        self._history = []
        self._ffmpeg_ok = bool(get_ffmpeg())
        self._fmt_radio_btns = []

        # Прогресс
        self._target_prog_value = 0.0

        # Переменные UI
        self._quality_idx = ctk.IntVar(value=2)
        self._raw_fmt_var = ctk.StringVar(value="")
        self._sub_var = ctk.BooleanVar(value=False)
        self._speed_var = ctk.StringVar(value="")
        self._tmpl_var = ctk.StringVar(value="%(title)s [%(id)s].%(ext)s")
        self._pl_tmpl_var = ctk.StringVar(
            value="%(playlist_title)s/%(playlist_index)s - %(title)s [%(id)s].%(ext)s"
        )
        self._embed_thumb = ctk.BooleanVar(value=True)
        self._embed_meta = ctk.BooleanVar(value=True)

        self._build_ui()
        self._poll()

        self._log(
            "Движок FFmpeg интегрирован — доступно студийное качество склейки."
            if self._ffmpeg_ok
            else "FFmpeg не найден. Установите для разблокировки максимального качества видео.",
            OK if self._ffmpeg_ok else WARN,
        )

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0, minsize=280)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()

        self._content_container = ctk.CTkFrame(self, fg_color="transparent")
        self._content_container.grid(
            row=0, column=1, sticky="nsew", padx=(8, 20), pady=(16, 16),
        )
        self._content_container.grid_rowconfigure(0, weight=1)
        self._content_container.grid_columnconfigure(0, weight=1)

        self._tabs = {}
        for tab_name in ("download", "queue", "history", "settings"):
            frame = ctk.CTkFrame(self._content_container, fg_color="transparent")
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._tabs[tab_name] = frame

        self._build_dl_tab(self._tabs["download"])
        self._build_queue_tab(self._tabs["queue"])
        self._build_history_tab(self._tabs["history"])
        self._build_settings_tab(self._tabs["settings"])

        self._current_tab_id = None
        self._select_tab("download")

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, fg_color="transparent", width=280, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew", padx=(14, 6), pady=(16, 16))
        sb.grid_propagate(False)
        sb.grid_rowconfigure(2, weight=1)

        shell = ctk.CTkFrame(
            sb, fg_color=GLASS_BG_SOFT, border_width=1,
            border_color=GLASS_BORDER, corner_radius=20,
        )
        shell.place(relx=0, rely=0, relwidth=1, relheight=1)
        shell.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(shell, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        top.grid_columnconfigure(1, weight=1)

        logo_pad = ctk.CTkFrame(
            top, fg_color=PRI_L, width=48, height=48, corner_radius=14
        )
        logo_pad.grid(row=0, column=0, rowspan=2, sticky="nw")
        logo_pad.grid_propagate(False)

        try:
            logo_path = resource_path("vidra_logo_48.png")
            pil_img = PilImage.open(logo_path).resize((30, 30), RESAMPLE_LANCZOS)
            ctk_img = ctk.CTkImage(light_image=pil_img, size=(30, 30))
            ctk.CTkLabel(
                logo_pad, image=ctk_img, text="", fg_color="transparent"
            ).place(relx=0.5, rely=0.5, anchor="center")
            logo_pad._logo_ref = ctk_img
        except Exception:
            ctk.CTkLabel(
                logo_pad, text="V", font=(FONT_FAMILY, 20, "bold"),
                text_color=PRI, fg_color="transparent",
            ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(top, text="Vidra", font=H2, text_color=TEXT_MAIN).grid(
            row=0, column=1, sticky="sw", padx=(12, 0)
        )
        ctk.CTkLabel(
            top, text="Universal Video Downloader", font=SMALL, text_color=TEXT_TERT,
        ).grid(row=1, column=1, sticky="nw", padx=(12, 0), pady=(2, 0))

        self._nav_frame = ctk.CTkFrame(shell, fg_color="transparent")
        self._nav_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(10, 0))

        self._nav_buttons = {}
        self._nav_order = []

        nav_items = [
            ("download", "Загрузка"),
            ("queue", "Очередь"),
            ("history", "История"),
            ("settings", "Настройки"),
        ]
        for tab_id, text in nav_items:
            btn = ctk.CTkButton(
                self._nav_frame, text=f"  {text}", anchor="w",
                height=44, fg_color="transparent", hover_color=PRI_L,
                text_color=TEXT_SEC, font=BODY_BOLD, corner_radius=12,
                border_width=0,
                command=lambda tid=tab_id: self._select_tab(tid),
            )
            btn.pack(fill="x", pady=2)
            self._nav_buttons[tab_id] = btn
            self._nav_order.append(tab_id)

        footer = ctk.CTkFrame(shell, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="sew", padx=20, pady=(0, 16))
        ctk.CTkLabel(
            footer, text="Vidra 2026 • by Sheri Akhtamov", font=SMALL, text_color=TEXT_TERT, anchor="w",
        ).pack(side="bottom", anchor="w")

    def _select_tab(self, tab_id):
        if self._current_tab_id == tab_id:
            return
        self._current_tab_id = tab_id
        self._tabs[tab_id].tkraise()
        self._tabs[tab_id].place(x=0, y=0, relwidth=1, relheight=1)
        for t_id, btn in self._nav_buttons.items():
            if t_id == tab_id:
                btn.configure(fg_color=PRI_L, text_color=PRI)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SEC)

    def _build_dl_tab(self, tab):
        tab.grid_columnconfigure(0, weight=6)
        tab.grid_columnconfigure(1, weight=4)
        tab.grid_rowconfigure(0, weight=1)

        left_col = ctk.CTkFrame(tab, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left_col.grid_rowconfigure(2, weight=1)
        left_col.grid_columnconfigure(0, weight=1)

        right_col = ctk.CTkFrame(tab, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right_col.grid_rowconfigure(0, weight=1)
        right_col.grid_columnconfigure(0, weight=1)

        self._build_url_card(left_col)
        self._build_pl_panel(left_col)
        self._build_fmt_card(left_col)

        self._build_log_card(right_col)
        self._build_footer_card(right_col)

    def _build_url_card(self, parent):
        card = GlassCard(parent)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text="Новая загрузка", font=H1, text_color=TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(
            card, text="Вставьте ссылку на видео, трек или плейлист",
            font=BODY, text_color=TEXT_SEC,
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 10))

        self._url_var = ctk.StringVar()
        self._url_entry = FloatingEntry(
            card, textvariable=self._url_var,
            placeholder_text="Вставьте URL сюда...",
        )
        self._url_entry.grid(row=2, column=0, padx=24, pady=(0, 12), sticky="ew")
        self._url_entry.bind("<Return>", lambda _: self._do_fetch())
        self._url_entry.bind("<<Paste>>", self._on_url_paste_shortcut)
        self._url_entry.bind("<Control-v>", self._on_url_paste_shortcut)
        self._url_entry.bind("<Control-V>", self._on_url_paste_shortcut)
        self._url_entry.bind("<Shift-Insert>", self._on_url_paste_shortcut)
        if sys.platform == "darwin":
            self._url_entry.bind("<Command-v>", self._on_url_paste_shortcut)
            self._url_entry.bind("<Command-V>", self._on_url_paste_shortcut)

        br = ctk.CTkFrame(card, fg_color="transparent")
        br.grid(row=3, column=0, padx=24, pady=(0, 12), sticky="ew")
        br.grid_columnconfigure(3, weight=1)

        ctk.CTkButton(
            br, text="Вставить", width=100, height=38,
            fg_color=GLASS_BG_SOFT, hover_color=PRI_L, text_color=TEXT_SEC,
            corner_radius=10, font=BODY_BOLD, border_width=0,
            command=self._paste,
        ).grid(row=0, column=0, padx=(0, 6))

        ctk.CTkButton(
            br, text="Очистить", width=100, height=38,
            fg_color=GLASS_BG_SOFT, hover_color=ERR_L, text_color=ERR,
            corner_radius=10, font=BODY_BOLD, border_width=0,
            command=lambda: self._url_var.set(""),
        ).grid(row=0, column=1, padx=(0, 12))

        ctk.CTkCheckBox(
            br, text="Субтитры", variable=self._sub_var,
            font=BODY, text_color=TEXT_SEC, fg_color=PRI, hover_color=PRI_H,
            border_color=GLASS_BORDER, corner_radius=6,
            checkbox_width=20, checkbox_height=20,
        ).grid(row=0, column=2, padx=(0, 12))

        self._fetch_btn = HeroButton(
            br, text="Анализировать", width=160, command=self._do_fetch,
        )
        self._fetch_btn.grid(row=0, column=3, sticky="e")

        self._info_lbl = ctk.CTkLabel(
            card, text="", font=BODY_BOLD, text_color=TEAL_H,
            wraplength=500, justify="left", anchor="w",
        )
        self._info_lbl.grid(row=4, column=0, padx=24, pady=(0, 16), sticky="w")

    def _build_pl_panel(self, parent):
        self._pl_card = GlassCard(
            parent,
            fg_color=TEAL_L,
            border_color=mix_color(TEAL, "#FFFFFF", 0.6),
        )
        self._pl_card.grid_columnconfigure(0, weight=1)

        ph = ctk.CTkFrame(self._pl_card, fg_color="transparent")
        ph.grid(row=0, column=0, sticky="ew", padx=24, pady=(18, 10))
        ph.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            ph,
            text="Обнаружен плейлист",
            font=H3,
            text_color=TEAL_H,
        ).grid(row=0, column=0, sticky="w")
        self._pl_pill = ctk.CTkLabel(
            ph,
            text="0 видео",
            font=SMALL_BOLD,
            text_color="white",
            fg_color=TEAL,
            corner_radius=12,
        )
        self._pl_pill.grid(row=0, column=1, ipadx=12, ipady=4)

        self._pl_scroll = ctk.CTkScrollableFrame(
            self._pl_card,
            fg_color=mix_color(TEAL_L, "#FFFFFF", 0.3),
            corner_radius=14,
            height=144,
        )
        self._pl_scroll.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 18))
        self._pl_scroll.grid_columnconfigure(0, weight=1)

    def _build_fmt_card(self, parent):
        card = GlassCard(parent)
        card.grid(row=2, column=0, sticky="nsew")
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        fh = ctk.CTkFrame(card, fg_color="transparent")
        fh.grid(row=0, column=0, sticky="ew", padx=34, pady=(28, 14))
        fh.grid_columnconfigure(0, weight=1)

        self._fmt_title_lbl = ctk.CTkLabel(
            fh,
            text="Качество",
            font=H2,
            text_color=TEXT_MAIN,
        )
        self._fmt_title_lbl.grid(row=0, column=0, sticky="w")
        self._fmt_cnt_lbl = ctk.CTkLabel(
            fh,
            text="",
            font=BODY_L,
            text_color=TEXT_TERT,
        )
        self._fmt_cnt_lbl.grid(row=0, column=1)

        self._fmt_scroll = ctk.CTkScrollableFrame(
            card,
            fg_color=GLASS_BG_SOFT,
            corner_radius=14,
            border_width=1,
            border_color=GLASS_BORDER,
        )
        self._fmt_scroll.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 20))
        self._fmt_scroll.grid_columnconfigure(0, weight=1)

        self._fmt_ph = ctk.CTkLabel(
            self._fmt_scroll,
            text="Введите ссылку, чтобы загрузить доступные форматы",
            font=BODY_L,
            text_color=TEXT_TERT,
        )
        self._fmt_ph.grid(row=0, column=0, pady=80)

    def _build_log_card(self, parent):
        card = GlassCard(parent)
        card.grid(row=0, column=0, sticky="nsew", pady=(0, 20))
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        lh = ctk.CTkFrame(card, fg_color="transparent")
        lh.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 10))
        lh.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(lh, text="Логи процесса", font=H3, text_color=TEXT_MAIN).grid(
            row=0,
            column=0,
            sticky="w",
        )
        MotionButton(
            lh,
            text="Очистить",
            width=96,
            height=34,
            fg_color=GLASS_BG_SOFT,
            hover_color=PRI_L,
            text_color=TEXT_SEC,
            border_color=GLASS_BORDER,
            corner_radius=12,
            font=SMALL_BOLD,
            command=self._clear_log,
        ).grid(row=0, column=1)

        self._log_box = ctk.CTkTextbox(
            card,
            fg_color=GLASS_BG_SOFT,
            border_width=1,
            border_color=GLASS_BORDER,
            corner_radius=16,
            font=CODE,
            text_color=TEXT_SEC,
            wrap="word",
            state="disabled",
        )
        self._log_box.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def _build_footer_card(self, parent):
        card = GlassCard(parent)
        card.grid(row=1, column=0, sticky="sew")
        card.grid_columnconfigure(0, weight=1)

        fr = ctk.CTkFrame(card, fg_color="transparent")
        fr.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 10))
        fr.grid_columnconfigure(1, weight=1)

        self._folder_lbl = ctk.CTkLabel(
            fr, text=self._dl_dir, font=BODY, text_color=TEXT_SEC, anchor="w",
        )
        self._folder_lbl.grid(row=0, column=0, columnspan=2, sticky="ew")

        ctk.CTkButton(
            fr, text="Изменить папку", width=120, height=32,
            fg_color=GLASS_BG_SOFT, hover_color=PRI_L, text_color=TEXT_SEC,
            corner_radius=8, font=SMALL_BOLD, border_width=0,
            command=self._choose_folder,
        ).grid(row=0, column=2, padx=(8, 0))

        pgf = ctk.CTkFrame(card, fg_color="transparent")
        pgf.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 8))
        pgf.grid_columnconfigure(0, weight=1)

        self._prog = ctk.CTkProgressBar(
            pgf, fg_color=GLASS_BG_SOFT, progress_color=PRI,
            corner_radius=8, height=10, border_width=0,
        )
        self._prog.set(0)
        self._prog.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        self._pct_lbl = ctk.CTkLabel(
            pgf, text="0%", width=44, font=BODY_BOLD, text_color=PRI, anchor="e",
        )
        self._pct_lbl.grid(row=0, column=1)

        self._status_lbl = ctk.CTkLabel(
            card, text="В ожидании ссылки...",
            font=BODY, text_color=TEXT_TERT, anchor="w",
        )
        self._status_lbl.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 10))

        br = ctk.CTkFrame(card, fg_color="transparent")
        br.grid(row=3, column=0, padx=20, pady=(0, 16), sticky="ew")
        br.grid_columnconfigure(0, weight=1)
        br.grid_columnconfigure(1, weight=1)

        self._add_q_btn = ctk.CTkButton(
            br, text="В очередь", height=42,
            fg_color=PLUM_L, hover_color=mix_color(PLUM_L, "#FFFFFF", 0.12),
            text_color=PLUM_H, corner_radius=12, font=BODY_BOLD, border_width=0,
            command=self._add_to_queue, state="disabled",
        )
        self._add_q_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self._dl_btn = ctk.CTkButton(
            br, text="Скачать сейчас", height=42,
            fg_color=OK, hover_color=OK_H, text_color="white",
            corner_radius=12, font=BODY_BOLD, border_width=0,
            command=self._do_download, state="disabled",
        )
        self._dl_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _build_queue_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(tab, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 12))
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr, text="Очередь загрузок", font=H1, text_color=TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            hdr, text="Очистить", width=100, height=38,
            fg_color=GLASS_BG_SOFT, hover_color=PRI_L, text_color=TEXT_SEC,
            corner_radius=10, font=BODY_BOLD, border_width=0,
            command=self._clear_queue,
        ).grid(row=0, column=1, padx=(0, 8))

        HeroButton(
            hdr, text="Запустить очередь", width=160, height=38,
            command=self._run_queue,
        ).grid(row=0, column=2)

        self._queue_scroll = ctk.CTkScrollableFrame(
            tab, fg_color=GLASS_BG_SOFT, corner_radius=14,
            border_width=1, border_color=GLASS_BORDER,
        )
        self._queue_scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._queue_scroll.grid_columnconfigure(0, weight=1)

        self._queue_ph = ctk.CTkLabel(
            self._queue_scroll,
            text="Очередь пока пустая\nДобавьте один или несколько роликов",
            font=BODY_L, text_color=TEXT_TERT, justify="center",
        )
        self._queue_ph.grid(row=0, column=0, pady=100)

    def _build_history_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(tab, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 12))
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr, text="История загрузок", font=H1, text_color=TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            hdr, text="Очистить", width=100, height=38,
            fg_color=GLASS_BG_SOFT, hover_color=PRI_L, text_color=TEXT_SEC,
            corner_radius=10, font=BODY_BOLD, border_width=0,
            command=self._clear_history,
        ).grid(row=0, column=1)

        self._hist_scroll = ctk.CTkScrollableFrame(
            tab, fg_color=GLASS_BG_SOFT, corner_radius=14,
            border_width=1, border_color=GLASS_BORDER,
        )
        self._hist_scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._hist_scroll.grid_columnconfigure(0, weight=1)

        self._hist_ph = ctk.CTkLabel(
            self._hist_scroll,
            text="История пока пуста.\nСкачайте первый файл.",
            font=BODY_L, text_color=TEXT_TERT,
        )
        self._hist_ph.grid(row=0, column=0, pady=100)

    def _build_settings_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(tab, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 12))
        ctk.CTkLabel(hdr, text="Настройки", font=H1, text_color=TEXT_MAIN).pack(
            anchor="w"
        )

        sc = ctk.CTkScrollableFrame(
            tab,
            fg_color=GLASS_BG_SOFT,
            corner_radius=16,
            border_width=1,
            border_color=GLASS_BORDER,
        )
        sc.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        sc.grid_columnconfigure(0, weight=1)

        def sec(title, icon=""):
            f = GlassCard(sc)
            f.pack(fill="x", pady=(0, 16), padx=12)
            ctk.CTkLabel(
                f, text=f"{icon}  {title}", font=H2, text_color=TEXT_MAIN
            ).grid(row=0, column=0, padx=32, pady=(32, 24), sticky="w", columnspan=4)
            f.grid_columnconfigure(1, weight=1)
            return f

        # FFmpeg
        ff = sec("Движок FFmpeg", "🎬")
        ctk.CTkLabel(
            ff,
            text="Статус интеграции:",
            font=BODY_BOLD,
            text_color=TEXT_SEC,
        ).grid(row=1, column=0, padx=32, pady=(0, 16), sticky="w")

        ff_status = (
            get_ffmpeg() or "Не найден (требуется установка)"
        )
        ff_color = OK if self._ffmpeg_ok else ERR
        ctk.CTkLabel(
            ff, text=ff_status, font=BODY_BOLD, text_color=ff_color, anchor="w"
        ).grid(row=1, column=1, padx=16, pady=(0, 16), sticky="ew")

        HeroButton(
            ff,
            text="Скачать FFmpeg",
            width=150,
            command=lambda: self._open_url("https://ffmpeg.org/download.html"),
        ).grid(row=1, column=2, padx=32, pady=(0, 16))

        msg = (
            "✓ Доступно студийное качество. Видео и аудио склеиваются идеально."
            if self._ffmpeg_ok
            else "⚠ Без FFmpeg видео скачается, но без склейки высшего качества."
        )
        ctk.CTkLabel(ff, text=msg, font=BODY, text_color=TEXT_SEC, justify="left").grid(
            row=2, column=0, columnspan=3, padx=32, pady=(0, 32), sticky="w"
        )

        # Шаблоны
        out = sec("Шаблон имени - одиночное видео", "📄")
        ctk.CTkLabel(
            out, text="Формат:", font=BODY_BOLD, text_color=TEXT_SEC
        ).grid(row=1, column=0, padx=32, pady=(0, 16), sticky="w")
        FloatingEntry(out, textvariable=self._tmpl_var, font=CODE).grid(
            row=1, column=1, padx=16, pady=(0, 16), sticky="ew", columnspan=2
        )
        ctk.CTkLabel(
            out,
            text="Доступно: %(title)s, %(id)s, %(ext)s, %(uploader)s, %(upload_date)s",
            font=SMALL,
            text_color=TEXT_TERT,
            anchor="w",
        ).grid(row=2, column=0, columnspan=3, padx=32, pady=(0, 32), sticky="w")

        pl_s = sec("Шаблон имени - плейлист", "📁")
        ctk.CTkLabel(
            pl_s, text="Формат:", font=BODY_BOLD, text_color=TEXT_SEC
        ).grid(row=1, column=0, padx=32, pady=(0, 16), sticky="w")
        FloatingEntry(pl_s, textvariable=self._pl_tmpl_var, font=CODE).grid(
            row=1, column=1, padx=16, pady=(0, 16), sticky="ew", columnspan=2
        )
        ctk.CTkLabel(
            pl_s,
            text="Доступно: %(playlist_title)s, %(playlist_index)s, %(title)s, %(id)s",
            font=SMALL,
            text_color=TEXT_TERT,
            anchor="w",
        ).grid(row=2, column=0, columnspan=3, padx=32, pady=(0, 32), sticky="w")

        # Лимит
        sp = sec("Лимит скорости загрузки", "⚡")
        ctk.CTkLabel(
            sp, text="Скорость:", font=BODY_BOLD, text_color=TEXT_SEC
        ).grid(row=1, column=0, padx=32, pady=(0, 32), sticky="w")
        FloatingEntry(
            sp,
            textvariable=self._speed_var,
            placeholder_text="напр. 5M или 500K (пусто = максимум)",
        ).grid(row=1, column=1, padx=16, pady=(0, 32), sticky="ew", columnspan=2)

        # Метаданные
        emb = sec("Метаданные (требует FFmpeg)", "🏷")
        ctk.CTkCheckBox(
            emb,
            text="Встроить обложку (Thumbnail)",
            variable=self._embed_thumb,
            font=BODY_BOLD,
            text_color=TEXT_SEC,
            fg_color=PRI,
            hover_color=PRI_H,
            corner_radius=8,
            checkbox_width=24,
            checkbox_height=24,
        ).grid(row=1, column=0, padx=32, pady=(0, 16), sticky="w")
        ctk.CTkCheckBox(
            emb,
            text="Встроить теги (Название, Автор, Дата)",
            variable=self._embed_meta,
            font=BODY_BOLD,
            text_color=TEXT_SEC,
            fg_color=PRI,
            hover_color=PRI_H,
            corner_radius=8,
            checkbox_width=24,
            checkbox_height=24,
        ).grid(row=2, column=0, padx=32, pady=(0, 32), sticky="w")

        # О программе
        abt = sec("О программе Vidra", "ℹ")
        ctk.CTkLabel(
            abt,
            text="Vidra 2026 Liquid Edition • powered by Sheri Akhtamov\nОсновано на открытом движке yt-dlp.",
            font=BODY,
            text_color=TEXT_SEC,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, padx=32, pady=(0, 24), sticky="w")
        bf = ctk.CTkFrame(abt, fg_color="transparent")
        bf.grid(row=2, column=0, padx=32, pady=(0, 32), sticky="w")
        MotionButton(
            bf,
            text="GitHub yt-dlp",
            width=140,
            height=40,
            fg_color=GLASS_BG_SOFT,
            hover_color=PRI_L,
            border_color=GLASS_BORDER,
            text_color=TEXT_MAIN,
            corner_radius=12,
            font=BODY_BOLD,
            command=lambda: self._open_url("https://github.com/yt-dlp/yt-dlp"),
        ).pack(side="left", padx=(0, 16))
        MotionButton(
            bf,
            text="Поддерживаемые сайты",
            width=220,
            height=40,
            fg_color=GLASS_BG_SOFT,
            hover_color=PRI_L,
            border_color=GLASS_BORDER,
            text_color=TEXT_MAIN,
            corner_radius=12,
            font=BODY_BOLD,
            command=lambda: self._open_url(
                "https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md"
            ),
        ).pack(side="left")

    # ==========================================
    # 🧠 ЛОГИКА И СВЯЗУЮЩИЕ ФУНКЦИИ (НЕТРОНУТО)
    # ==========================================
    def _paste(self):
        try:
            self._url_var.set(self.clipboard_get())
        except Exception:
            pass

    def _on_url_paste_shortcut(self, _event=None):
        try:
            clip = self.clipboard_get().strip()
            self._url_var.set(clip)
            self._url_entry.icursor("end")
        except Exception:
            pass
        return "break"

    def _normalize_url_from_entry(self):
        val = (self._url_var.get() or "").strip()
        if val != self._url_var.get():
            self._url_var.set(val)

    def _choose_folder(self):
        d = filedialog.askdirectory(initialdir=self._dl_dir)
        if d:
            self._dl_dir = d
            self._folder_lbl.configure(text=d)

    def _open_url(self, url):
        webbrowser.open(url)

    def _log(self, msg, color=None):
        self._mq.put(("log", msg, color))

    def _set_status(self, msg, c=TEXT_TERT):
        self._mq.put(("status", msg, c))

    def _set_prog(self, v, instant=False):
        self._mq.put(("prog", v, None))

    def _apply_prog(self, v):
        self._target_prog_value = v
        self._prog.set(v)
        pct = int(v * 100)
        self._pct_lbl.configure(text=f"{pct}%" if v > 0.01 else "0%")

    def _poll(self):
        try:
            while True:
                k, a, b = self._mq.get_nowait()
                if k == "log":
                    self._write_log(a, b)
                elif k == "status":
                    self._status_lbl.configure(text=a, text_color=b or TEXT_SEC)
                elif k == "prog":
                    self._apply_prog(a)
                elif k == "fetch_done":
                    self._on_fetch_done(a)
                elif k == "dl_done":
                    self._on_dl_done(a)
                elif k == "q_refresh":
                    self._refresh_queue()
                elif k == "h_refresh":
                    self._refresh_history()
        except queue.Empty:
            pass
        self.after(150, self._poll)

    def _write_log(self, msg, color=None):
        self._log_box.configure(state="normal")
        tag = None
        if color:
            tag = f"c_{color}"
            try:
                self._log_box.tag_config(tag, foreground=color)
            except Exception:
                tag = None
        prefix = f"[{ts()}] "
        self._log_box.insert("end", prefix)
        if tag:
            start_idx = self._log_box.index("end-1c linestart")
            self._log_box.insert("end", f"{msg}\n")
            end_idx = self._log_box.index("end-1c")
            self._log_box.tag_add(tag, f"{start_idx}+{len(prefix)}c", end_idx)
        else:
            self._log_box.insert("end", f"{msg}\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _clear_log(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    # Fetch
    def _do_fetch(self):
        url = self._url_var.get().strip()
        if not url:
            messagebox.showwarning(
                "Внимание",
                "Пожалуйста, вставь ссылку на видео!",
            )
            return

        if self._fetch_thread and self._fetch_thread.is_alive():
            return

        self._fetch_btn.configure(state="disabled", text="Анализирую...")
        self._dl_btn.configure(state="disabled")
        self._add_q_btn.configure(state="disabled")

        self._clear_fmt_list()
        self._fmt_ph.configure(text="⏳ Подключаюсь к сервису...")
        self._fmt_ph.grid()
        self._hide_pl()
        self._info_lbl.configure(text="")

        self._log(f"Запрос инфо: {url[:80]}...")
        self._set_status(
            "Получаю информацию о видео...", TEXT_TERT
        )

        def worker():
            try:
                r = _run_hidden(
                    [get_ytdlp(), "--flat-playlist", "--dump-single-json", url],
                    capture_output=True,
                    text=True,
                    timeout=45,
                    encoding="utf-8",
                    errors="replace",
                )
                if r.returncode != 0:
                    lines = (r.stderr or "").strip().splitlines()
                    raise RuntimeError(lines[-1] if lines else "yt-dlp error")

                info = json.loads(r.stdout)
                is_pl = (
                    info.get("_type") in ("playlist", "multi_video")
                    or "entries" in info
                )

                if is_pl:
                    entries = info.get("entries") or []
                    self._mq.put(
                        (
                            "fetch_done",
                            {
                                "type": "playlist",
                                "title": info.get("title") or "Плейлист",
                                "uploader": info.get("uploader")
                                or info.get("channel", ""),
                                "count": len(entries),
                                "url": url,
                                "entries": [
                                    {
                                        "idx": e.get("playlist_index") or (i + 1),
                                        "title": e.get(
                                            "title", "Видео " + str(i + 1)
                                        ),
                                        "id": e.get("id", ""),
                                        "url": e.get("url") or e.get("webpage_url", ""),
                                    }
                                    for i, e in enumerate(entries)
                                    if e
                                ],
                            },
                            None,
                        )
                    )
                else:
                    r2 = _run_hidden(
                        [get_ytdlp(), "--dump-json", "--no-playlist", url],
                        capture_output=True,
                        text=True,
                        timeout=45,
                        encoding="utf-8",
                        errors="replace",
                    )
                    if r2.returncode != 0:
                        lines = (r2.stderr or "").strip().splitlines()
                        raise RuntimeError(lines[-1] if lines else "yt-dlp error")

                    full = json.loads(r2.stdout)
                    self._mq.put(
                        (
                            "fetch_done",
                            {
                                "type": "single",
                                "info": full,
                                "raw_formats": parse_raw_formats(full),
                            },
                            None,
                        )
                    )

            except Exception as e:
                self._mq.put(("fetch_done", {"type": "error", "msg": str(e)}, None))

        self._fetch_thread = threading.Thread(target=worker, daemon=True)
        self._fetch_thread.start()

    def _on_fetch_done(self, p):
        self._fetch_btn.configure(state="normal", text="Анализировать")
        self._fetch_thread = None

        if p["type"] == "error":
            self._log(f"ОШИБКА: {p['msg']}", ERR)
            self._set_status("Ошибка получения данных", ERR)
            self._fmt_ph.configure(
                text="❌ Не удалось получить информацию.\nПроверь ссылку или подключение к сети."
            )
            return

        if p["type"] == "playlist":
            self._is_playlist = True
            self._info = p
            title = str(p.get("title") or "Плейлист")
            uploader = str(p.get("uploader") or "Неизвестный канал")
            count = int(p.get("count") or 0)
            self._info_lbl.configure(
                text=f"🎬 {title[:60]}  •  {count} видео  •  👤 {uploader[:28]}"
            )
            self._log(
                f"Найден плейлист «{title[:55]}» ({count} видео)"
            )
            self._set_status(
                f"Плейлист обработан ({count} шт.). Выбери качество.",
                OK,
            )
            self._show_pl(p.get("entries") or [])
            self._populate_presets_only()
        else:
            self._is_playlist = False
            fi = p.get("info") or {}
            self._info = fi
            self._raw_formats = p.get("raw_formats") or []
            dur = fmt_dur(fi.get("duration"))
            title = str(fi.get("title") or "Без названия")
            upl = str(
                fi.get("uploader")
                or fi.get("channel")
                or "Неизвестный автор"
            )[:28]
            self._info_lbl.configure(text=f"🎬 {title[:68]}   ⏱ {dur}   👤 {upl}")
            self._log(
                f"Найдено видео «{title[:55]}» ({len(self._raw_formats)} форматов)"
            )
            self._set_status(
                "Форматы загружены. Можно скачивать!", OK
            )
            self._populate_all_formats()

        has_formats = (
            self._is_playlist or bool(self._raw_formats) or self._quality_idx.get() >= 0
        )
        self._dl_btn.configure(state="normal" if has_formats else "disabled")
        self._add_q_btn.configure(state="normal" if has_formats else "disabled")

    def _clear_fmt_list(self):
        for w in self._fmt_scroll.winfo_children():
            if w != self._fmt_ph:
                w.destroy()
        self._fmt_radio_btns = []  # В нашем случае это будут кастомные пилюли
        self._raw_fmt_var.set("")
        self._quality_idx.set(-1)

    def _render_fmt_pills(self):
        """Обновление стилей пилюль для имитации RadioButton."""
        sel_idx = self._quality_idx.get()
        sel_raw = self._raw_fmt_var.get()

        for p in self._fmt_radio_btns:
            is_active = False
            if p["type"] == "preset" and sel_idx == p["val"]:
                is_active = True
            elif p["type"] == "raw" and sel_raw == p["val"]:
                is_active = True

            btn = p["btn"]
            if is_active:
                btn.configure(fg_color=PRI_L, border_color=PRI, text_color=PRI)
            else:
                btn.configure(
                    fg_color=GLASS_BG_SOFT,
                    border_color=GLASS_BORDER,
                    text_color=TEXT_MAIN,
                )

    def _add_preset_row(self, row, idx, preset):
        # Пилюля как кнопка на всю ширину
        btn = PillButton(
            self._fmt_scroll,
            text=f"  {preset['label']}   •   {preset['sub']}",
            anchor="w",
            command=lambda i=idx: [
                self._quality_idx.set(i),
                self._raw_fmt_var.set(""),
                self._render_fmt_pills(),
                self._on_q_pick(),
            ],
        )
        btn.grid(row=row, column=0, padx=16, pady=4, sticky="ew")
        self._fmt_radio_btns.append({"type": "preset", "val": idx, "btn": btn})

    def _populate_presets_only(self):
        self._fmt_ph.grid_remove()
        self._clear_fmt_list()
        self._fmt_title_lbl.configure(text="Максимальное качество")
        self._fmt_cnt_lbl.configure(text="Для плейлиста")

        msg = "Каждое видео будет скачано в лучшем качестве\nдо выбранного ограничения:"
        ctk.CTkLabel(
            self._fmt_scroll, text=msg, font=BODY, text_color=TEXT_SEC, justify="left"
        ).grid(row=0, column=0, padx=20, pady=(12, 20), sticky="w")

        for i, p in enumerate(QUALITY_PRESETS):
            self._add_preset_row(i + 1, i, p)

        self._quality_idx.set(2)
        self._render_fmt_pills()

    def _populate_all_formats(self):
        self._fmt_ph.grid_remove()
        self._clear_fmt_list()
        self._fmt_title_lbl.configure(text="Выбор качества")
        max_h = max((f.get("h", 0) or 0) for f in self._raw_formats) if self._raw_formats else 9999
        filtered_presets = [
            (i, p) for i, p in enumerate(QUALITY_PRESETS)
            if p["h"] <= max_h or p["h"] == 0 or p["h"] == 9999
        ]
        self._fmt_cnt_lbl.configure(
            text=f"{len(filtered_presets) + len(self._raw_formats)} вариантов"
        )

        sep1 = ctk.CTkLabel(
            self._fmt_scroll,
            text="УМНЫЕ ПРЕСЕТЫ",
            font=(FONT_FAMILY, 11, "bold"),
            text_color=TEXT_TERT,
        )
        sep1.grid(row=0, column=0, padx=20, pady=(20, 12), sticky="w")

        for row_n, (i, p) in enumerate(filtered_presets):
            self._add_preset_row(row_n + 1, i, p)

        if self._raw_formats:
            sep2 = ctk.CTkLabel(
                self._fmt_scroll,
                text="Сырые форматы (серверные источники)",
                font=(FONT_FAMILY, 13, "bold"),
                text_color=TEXT_TERT,
            )
            n_presets = len(filtered_presets)
            sep2.grid(
                row=n_presets + 1,
                column=0,
                padx=20,
                pady=(32, 12),
                sticky="w",
            )

            for j, fmt in enumerate(self._raw_formats):
                fid = fmt["id"]
                btn = PillButton(
                    self._fmt_scroll,
                    text=f"  {fmt['label']}",
                    anchor="w",
                    command=lambda f=fid: [
                        self._raw_fmt_var.set(f),
                        self._quality_idx.set(-1),
                        self._render_fmt_pills(),
                        self._on_raw_pick(),
                    ],
                )
                btn.grid(
                    row=n_presets + 2 + j,
                    column=0,
                    padx=16,
                    pady=4,
                    sticky="ew",
                )
                self._fmt_radio_btns.append({"type": "raw", "val": fid, "btn": btn})

        default_idx = filtered_presets[0][0] if filtered_presets else 0
        self._quality_idx.set(default_idx)
        self._render_fmt_pills()

    def _on_q_pick(self):
        self._raw_fmt_var.set("")
        self._dl_btn.configure(state="normal")
        self._add_q_btn.configure(state="normal")

    def _on_raw_pick(self):
        self._quality_idx.set(-1)
        self._dl_btn.configure(state="normal")
        self._add_q_btn.configure(state="normal")

    def _find_raw_format(self, fmt_id):
        for fmt in self._raw_formats:
            if fmt.get("id") == fmt_id:
                return fmt
        return None

    def _selector_from_raw_format(self, fmt):
        if fmt.get("audio_only"):
            return fmt["id"], True
        if fmt.get("has_audio"):
            return fmt["id"], False
        return f'{fmt["id"]}+bestaudio/{fmt["id"]}', False

    def _raw_format_from_selector(self, fmt):
        selector = (fmt or "").split("/", 1)[0].split("+", 1)[0]
        return self._find_raw_format(selector)

    def _is_unsafe_video_postprocess_format(self, fmt):
        raw_fmt = self._raw_format_from_selector(fmt)
        if raw_fmt:
            proto = str(raw_fmt.get("protocol") or "").lower()
            if "m3u8" in proto:
                return True

        selector = (fmt or "").lower()
        return selector.startswith("m3u8-") or selector.startswith("default-")

    def _resolve_fmt(self):
        raw = self._raw_fmt_var.get()
        if raw:
            raw_fmt = self._find_raw_format(raw)
            if raw_fmt:
                return self._selector_from_raw_format(raw_fmt)
            return raw, False

        idx = self._quality_idx.get()
        if not (0 <= idx < len(QUALITY_PRESETS)):
            return "bestvideo+bestaudio/best", False

        preset = QUALITY_PRESETS[idx]
        if preset["h"] == 0:
            return preset["fmt"], True

        video_fmts = [
            f
            for f in self._raw_formats
            if not f.get("audio_only") and f.get("h", 0) > 0
        ]
        if video_fmts:
            target_h = preset["h"]
            rank = lambda f: (f["h"], 1 if f.get("has_audio") else 0, f.get("tbr", 0))
            if target_h < 9999:
                matching = [f for f in video_fmts if f["h"] <= target_h]
                best = max(matching, key=rank) if matching else max(video_fmts, key=rank)
            else:
                best = max(video_fmts, key=rank)
            return self._selector_from_raw_format(best)

        return preset["fmt"], False

    def _get_fmt(self):
        return self._resolve_fmt()[0]

    def _show_pl(self, entries):
        self._pl_card.grid(
            row=1, column=0, sticky="ew", pady=(0, 24), in_=self._pl_card.master
        )
        self._pl_pill.configure(text=f"{len(entries)} видео")
        for w in self._pl_scroll.winfo_children():
            w.destroy()

        for i, e in enumerate(entries[:60]):
            row = ctk.CTkFrame(self._pl_scroll, fg_color="transparent")
            row.grid(row=i, column=0, sticky="ew", pady=4)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                row, text=f"{e['idx']:>3}.", font=CODE, text_color=TEXT_TERT, width=40
            ).grid(row=0, column=0, padx=(4, 12))
            ctk.CTkLabel(
                row, text=e["title"], font=BODY, text_color=TEXT_MAIN, anchor="w"
            ).grid(row=0, column=1, sticky="w")

        if len(entries) > 60:
            ctk.CTkLabel(
                self._pl_scroll,
                text=f"... и еще {len(entries) - 60} видео",
                font=BODY_BOLD,
                text_color=TEXT_TERT,
            ).grid(row=60, column=0, pady=12)

        self._render_fmt_pills()

    def _hide_pl(self):
        try:
            self._pl_card.grid_remove()
        except Exception:
            pass

    # Download Engine
    def _build_cmd(self, url, fmt, is_pl=False, audio_only=False):
        ff = get_ffmpeg()
        ff_dir = os.path.dirname(os.path.abspath(ff)) if ff else None
        tmpl = os.path.join(
            self._dl_dir, self._pl_tmpl_var.get() if is_pl else self._tmpl_var.get()
        )
        pl_flag = ["--yes-playlist"] if is_pl else ["--no-playlist"]

        cmd = [get_ytdlp(), "-f", fmt, "--format-sort", "res,br", "--force-overwrites",
               "--progress", "--newline", "-o", tmpl] + pl_flag

        if audio_only:
            cmd += ["--extract-audio", "--audio-format", "mp3", "--audio-quality", "0"]
            if ff_dir:
                cmd += ["--ffmpeg-location", ff_dir]
        else:
            if ff_dir:
                unsafe_video_post = self._is_unsafe_video_postprocess_format(fmt)
                if unsafe_video_post:
                    cmd += ["--remux-video", "mkv", "--ffmpeg-location", ff_dir]
                    self._log(
                        "WARN: Для HLS/m3u8-потоков сохраняю видео в MKV: такой контейнер стабильно открывается, в отличие от битого MP4.",
                        WARN,
                    )
                else:
                    cmd += ["--merge-output-format", "mp4", "--ffmpeg-location", ff_dir]
                if unsafe_video_post and (self._embed_thumb.get() or self._embed_meta.get()):
                    self._log(
                        "WARN: Для HLS/m3u8-потоков пропускаю встраивание метаданных и обложки: это может повредить видеофайл.",
                        WARN,
                    )
                else:
                    if self._embed_thumb.get():
                        cmd += ["--embed-thumbnail"]
                    if self._embed_meta.get():
                        cmd += ["--add-metadata"]

        if self._sub_var.get():
            cmd += [
                "--write-subs",
                "--write-auto-subs",
                "--sub-langs",
                "ru,en",
                "--embed-subs",
            ]

        lim = self._speed_var.get().strip()
        if lim:
            cmd += ["--limit-rate", lim]

        cmd.append(url)
        return cmd

    def _do_download(self):
        url = self._url_var.get().strip()
        if not url:
            return
        if self._dl_thread and self._dl_thread.is_alive():
            messagebox.showinfo(
                "Процесс занят",
                "Пожалуйста, дождись окончания текущей загрузки!",
            )
            return

        fmt, audio_only = self._resolve_fmt()
        is_pl = self._is_playlist
        title = self._info.get("title", "?")

        self._dl_btn.configure(state="disabled", text="Скачивание...")
        self._set_prog(0, instant=True)

        self._log(
            f"▶ Начинаю загрузку: {'[ПЛЕЙЛИСТ]' if is_pl else '[ВИДЕО]'} {title[:50]}  |  Формат: {fmt}"
        )
        cmd = self._build_cmd(url, fmt, is_pl, audio_only)

        def worker():
            if is_pl:
                ok, path, warn = self._run_playlist(cmd, self._info.get("count", 1))
            else:
                ok, path, warn = self._run_single(cmd)

            if ok:
                self._history.append(
                    {
                        "title": title,
                        "url": url,
                        "path": path,
                        "is_pl": is_pl,
                        "ts": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    }
                )
            self._mq.put(("dl_done", (ok, path, warn), None))

        self._dl_thread = threading.Thread(target=worker, daemon=True)
        self._dl_thread.start()

    def _run_single(self, cmd):
        pct_re = re.compile(r"\[download\]\s+([\d.]+)%")
        dest_re = re.compile(r"Destination:\s*(.+)")
        merge_re = re.compile(r'Merging formats into ["\'](.+)["\']')
        already_dl_re = re.compile(
            r"\[download\]\s+(.*?)\s+has already been downloaded"
        )

        last_path = ""
        ffmpeg_warn = False

        try:
            proc = _popen_hidden(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            saw_activity = False
            stream = proc.stdout or []
            for line in stream:
                line = line.rstrip()

                m = pct_re.search(line)
                if m:
                    saw_activity = True
                    self._set_prog(float(m.group(1)) / 100)
                    self._set_status(
                        f"Загрузка файла... {m.group(1)}%", PRI
                    )
                    continue

                dm = dest_re.search(line)
                if dm:
                    saw_activity = True
                    last_path = dm.group(1).strip()

                mm = merge_re.search(line)
                if mm:
                    saw_activity = True
                    last_path = mm.group(1).strip()

                al = already_dl_re.search(line)
                if al:
                    saw_activity = True
                    last_path = al.group(1).strip()

                lo = line.lower()
                if "ffmpeg not found" in lo or (
                    "postprocessing" in lo and "error" in lo
                ):
                    ffmpeg_warn = True
                    self._log(f"WARN: {line}", WARN)
                    continue

                if line and "[download]  " not in line:
                    self._log(line)

            proc.wait()

            if last_path and os.path.isfile(last_path):
                return True, last_path, ffmpeg_warn
            if proc.returncode == 0:
                return True, last_path, ffmpeg_warn
            if ffmpeg_warn and (saw_activity or proc.returncode == 0):
                return True, last_path, True
            return False, "", ffmpeg_warn

        except FileNotFoundError:
            self._log(
                "yt-dlp не найден! Положи его в папку с программой.",
                ERR,
            )
            return False, "", False
        except Exception as e:
            self._log(f"Критическая ошибка: {e}", ERR)
            return False, "", False

    def _run_playlist(self, cmd, total):
        pct_re = re.compile(r"\[download\]\s+([\d.]+)%")
        vidnum_re = re.compile(
            r"\[download\] Downloading (?:item|video) (\d+) of (\d+)"
        )
        dest_re = re.compile(r"Destination:\s*(.+)")
        merge_re = re.compile(r'Merging formats into ["\'](.+)["\']')
        already_dl_re = re.compile(
            r"\[download\]\s+(.*?)\s+has already been downloaded"
        )

        current = 0
        last_path = ""
        ffmpeg_warn = False

        try:
            proc = _popen_hidden(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            saw_activity = False
            stream = proc.stdout or []
            for line in stream:
                line = line.rstrip()

                m2 = vidnum_re.search(line)
                if m2:
                    saw_activity = True
                    current = int(m2.group(1))
                    tot = int(m2.group(2))
                    self._set_status(
                        f"Обработка видео {current} из {tot}...", PRI
                    )
                    self._set_prog((current - 1) / max(tot, 1))
                    self._log(f"▶ Скачивание видео {current}/{tot}")
                    continue

                m = pct_re.search(line)
                if m:
                    saw_activity = True
                    if current <= 0:
                        current = 1
                    pct = float(m.group(1)) / 100
                    overall = (max(current - 1, 0) + pct) / max(total, 1)
                    self._set_prog(min(overall, 1.0))
                    self._set_status(
                        f"Видео {current}/{total}  —  {m.group(1)}%", PRI
                    )
                    continue

                dm = dest_re.search(line)
                if dm:
                    saw_activity = True
                    last_path = dm.group(1).strip()

                mm = merge_re.search(line)
                if mm:
                    saw_activity = True
                    last_path = mm.group(1).strip()

                al = already_dl_re.search(line)
                if al:
                    saw_activity = True
                    last_path = al.group(1).strip()

                lo = line.lower()
                if "ffmpeg not found" in lo or (
                    "postprocessing" in lo and "error" in lo
                ):
                    ffmpeg_warn = True
                    self._log(f"WARN: {line}", WARN)
                    continue

                if line and "[download]  " not in line:
                    self._log(line)

            proc.wait()
            folder = os.path.dirname(last_path) if last_path else self._dl_dir
            if proc.returncode == 0:
                return True, folder, ffmpeg_warn
            if ffmpeg_warn and (saw_activity or proc.returncode == 0):
                return True, folder, True
            return False, "", ffmpeg_warn

        except FileNotFoundError:
            self._log("yt-dlp не найден!", ERR)
            return False, "", False
        except Exception as e:
            self._log(f"Ошибка: {e}", ERR)
            return False, "", False

    def _on_dl_done(self, payload):
        ok, path, warn = payload
        self._dl_btn.configure(state="normal", text="Скачать сейчас")

        if ok:
            self._set_prog(1)
            if warn:
                self._log(
                    "Успешно завершено! (но без ffmpeg-склейки)",
                    WARN,
                )
                self._set_status(
                    "Готово. Рекомендуется установить FFmpeg",
                    WARN,
                )
            else:
                self._log("Успешно завершено!", OK)
                self._set_status(
                    "Загрузка успешно завершена! 🎉", OK
                )

            self._refresh_history()
            folder = (
                os.path.dirname(path)
                if path and os.path.isfile(path)
                else path
                if path and os.path.isdir(path)
                else self._dl_dir
            )

            if messagebox.askyesno(
                "Отличные новости!",
                "Загрузка успешно завершена!\n\nОткрыть папку с файлами?",
            ):
                self._reveal(folder)
        else:
            self._log(
                "Загрузка завершилась с ошибкой. См. журнал.",
                ERR,
            )
            self._set_status("Сбой при загрузке ❌", ERR)

    def _reveal(self, path):
        if os.path.isfile(path):
            folder = os.path.dirname(path)
        else:
            folder = path

        if sys.platform == "win32":
            if os.path.isfile(path):
                subprocess.Popen(["explorer", "/select,", path])
            else:
                subprocess.Popen(["explorer", folder])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path])
        else:
            subprocess.Popen(["xdg-open", folder])

    # Queue Logic
    def _add_to_queue(self):
        url = self._url_var.get().strip()
        fmt, audio_only = self._resolve_fmt()
        if not url or not fmt:
            return

        is_pl = self._is_playlist
        title = self._info.get("title", "Неизвестное видео")
        count = self._info.get("count", 0) if is_pl else 0

        cmd = self._build_cmd(url, fmt, is_pl, audio_only)
        self._dl_queue.append(
            QueueItem(url, fmt, title, is_pl, count, cmd, audio_only=audio_only)
        )
        self._refresh_queue()
        self._mq.put(
            ("status", f"Добавлено в очередь: {title[:40]}", PRI)
        )

        self._log(
            f"+ Добавлено в очередь: {'плейлист (' + str(count) + ' видео)' if is_pl else 'видео'}  «{title[:40]}»"
        )

        orig_color = self._add_q_btn.cget("fg_color")
        self._add_q_btn.configure(fg_color=OK_L, text_color=OK_H, text="Добавлено")
        self.after(
            1500,
            lambda: self._add_q_btn.configure(
                fg_color=orig_color, text_color=PLUM_H, text="В очередь"
            ),
        )

    def _refresh_queue(self):
        for w in self._queue_scroll.winfo_children():
            if w != self._queue_ph:
                w.destroy()

        if not self._dl_queue:
            self._queue_ph.grid()
            return

        self._queue_ph.grid_remove()

        STATUS_STYLES = {
            "waiting": (TEXT_SEC, "Ожидает", GLASS_BG, GLASS_BORDER),
            "running": (PRI, "В процессе", PRI_L, PRI_MUTED),
            "done": (OK, "Готово", OK_L, OK),
            "fail": (ERR, "Ошибка", ERR_L, ERR),
        }

        for i, item in enumerate(self._dl_queue):
            text_color, icon_text, bg_color, border_col = STATUS_STYLES.get(
                item.status, STATUS_STYLES["waiting"]
            )

            row = GlassCard(
                self._queue_scroll, fg_color=GLASS_BG, border_color=border_col
            )
            row.grid(row=i, column=0, sticky="ew", padx=16, pady=8)
            row.grid_columnconfigure(1, weight=1)

            badge = ctk.CTkLabel(
                row,
                text=icon_text,
                font=SMALL_BOLD,
                text_color=text_color,
                fg_color=bg_color,
                corner_radius=10,
            )
            badge.grid(row=0, column=0, padx=(24, 20), pady=24, ipadx=16, ipady=8)

            inf = ctk.CTkFrame(row, fg_color="transparent")
            inf.grid(row=0, column=1, sticky="ew")

            title_text = item.title[:70] + ("..." if len(item.title) > 70 else "")
            sub_text = (
                f"Плейлист • {item.count} видео" if item.is_pl else "Одиночное видео"
            )

            ctk.CTkLabel(
                inf, text=title_text, font=H3, text_color=TEXT_MAIN, anchor="w"
            ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(
                inf, text=sub_text, font=BODY, text_color=TEXT_TERT, anchor="w"
            ).grid(row=1, column=0, sticky="w", pady=(2, 0))

            if item.status != "running":
                MotionButton(
                    row,
                    text="Удалить",
                    width=92,
                    height=44,
                    fg_color=GLASS_BG_SOFT,
                    hover_color=ERR_L,
                    text_color=ERR,
                    border_color=GLASS_BORDER,
                    corner_radius=12,
                    font=BODY_BOLD,
                    command=lambda idx=i: self._remove_q(idx),
                ).grid(row=0, column=2, padx=(0, 24))

    def _remove_q(self, idx):
        if 0 <= idx < len(self._dl_queue):
            self._dl_queue.pop(idx)
            self._refresh_queue()

    def _clear_queue(self):
        self._dl_queue = [q for q in self._dl_queue if q.status == "running"]
        self._refresh_queue()

    def _run_queue(self):
        if not self._dl_queue:
            messagebox.showinfo(
                "Очередь пуста",
                "Добавь видео или плейлисты в очередь!",
            )
            return

        if self._dl_thread and self._dl_thread.is_alive():
            messagebox.showinfo(
                "Занято",
                "Сначала дождись окончания текущего процесса.",
            )
            return

        def worker():
            while True:
                item = None
                for q in self._dl_queue:
                    if q.status == "waiting":
                        item = q
                        break

                if not item:
                    break

                item.status = "running"
                self._mq.put(("q_refresh", None, None))
                self._log(
                    f"⚡ Запуск из очереди: {'[PL]' if item.is_pl else '[V]'} {item.title[:50]}",
                    PRI,
                )

                cmd = (
                    item.cmd
                    if item.cmd
                    else self._build_cmd(item.url, item.fmt, item.is_pl, item.audio_only)
                )
                if item.is_pl:
                    ok, path, warn = self._run_playlist(cmd, item.count)
                else:
                    ok, path, warn = self._run_single(cmd)

                item.status = "done" if ok else "fail"

                if ok:
                    self._history.append(
                        {
                            "title": item.title,
                            "url": item.url,
                            "path": path,
                            "is_pl": item.is_pl,
                            "ts": datetime.now().strftime("%d.%m.%Y %H:%M"),
                        }
                    )

                self._mq.put(
                    (
                        "log",
                        f"{'УСПЕХ' if ok else 'ОШИБКА'}: {item.title[:50]}",
                        OK if ok else ERR,
                    )
                )
                self._mq.put(("q_refresh", None, None))

            self._mq.put(
                (
                    "status",
                    "Очередь полностью обработана! 🎉",
                    OK,
                )
            )
            self._mq.put(("h_refresh", None, None))
            self._mq.put(("q_refresh", None, None))

        self._dl_thread = threading.Thread(target=worker, daemon=True)
        self._dl_thread.start()

    # History Logic
    def _refresh_history(self):
        for w in self._hist_scroll.winfo_children():
            if w != self._hist_ph:
                w.destroy()

        if not self._history:
            self._hist_ph.grid()
            return

        self._hist_ph.grid_remove()

        for i, item in enumerate(reversed(self._history)):
            is_pl = item.get("is_pl", False)

            row = GlassCard(self._hist_scroll)
            row.grid(row=i, column=0, sticky="ew", padx=16, pady=8)
            row.grid_columnconfigure(1, weight=1)

            badge_color, badge_bg, badge_txt = (
                (TEAL, TEAL_L, "ПЛЕЙЛИСТ") if is_pl else (PRI, PRI_L, "ВИДЕО")
            )
            ctk.CTkLabel(
                row,
                text=badge_txt,
                font=SMALL_BOLD,
                text_color=badge_color,
                fg_color=badge_bg,
                corner_radius=10,
            ).grid(row=0, column=0, padx=(24, 20), pady=24, ipadx=16, ipady=8)

            inf = ctk.CTkFrame(row, fg_color="transparent")
            inf.grid(row=0, column=1, sticky="ew")

            title_text = item["title"][:75] + ("..." if len(item["title"]) > 75 else "")
            ctk.CTkLabel(
                inf, text=title_text, font=H3, text_color=TEXT_MAIN, anchor="w"
            ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(
                inf, text=item["ts"], font=BODY, text_color=TEXT_TERT, anchor="w"
            ).grid(row=1, column=0, sticky="w", pady=(2, 0))

            p = item.get("path", "")
            exists = bool(p) and (os.path.isfile(p) or os.path.isdir(p))

            btn_text = (
                "Открыть файл" if exists and os.path.isfile(p) else "Открыть папку"
            )
            btn_color = PRI if exists else GLASS_BG_SOFT
            btn_txt_col = "white" if exists else TEXT_SEC
            btn_hover = PRI_H if exists else PRI_L

            MotionButton(
                row,
                text=btn_text,
                width=150,
                height=44,
                fg_color=btn_color,
                hover_color=btn_hover,
                text_color=btn_txt_col,
                border_color=mix_color(GLASS_BORDER, PRI, 0.16),
                corner_radius=12,
                font=BODY_BOLD,
                command=lambda pp=p: self._reveal(pp or self._dl_dir),
            ).grid(row=0, column=2, padx=(0, 24))

    def _clear_history(self):
        if messagebox.askyesno(
            "Очистить историю?",
            "Удалить все записи о загрузках из истории?",
        ):
            self._history.clear()
            self._refresh_history()


if __name__ == "__main__":
    app = App()
    app.mainloop()
