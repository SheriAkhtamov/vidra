"""Vidra — powered by Sheri  |  v6 (2026 UI/UX Redesign)"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading, subprocess, json, os, sys, re, queue, shutil
from datetime import datetime
from PIL import Image as PilImage

# Форсируем светлую тему и отключаем базовые цветовые стили CTk
ctk.set_appearance_mode("light")

# --- СОВРЕМЕННАЯ ПАЛИТРА 2026 (Светлая / Синяя) ---
BG_MAIN = "#F1F5F9"         # Воздушный серо-голубой фон приложения
PANEL_BG = "#FFFFFF"        # Чистый белый для карточек и панелей
SIDEBAR_BG = "#FFFFFF"      # Фон боковой панели
BORDER = "#E2E8F0"          # Мягкие границы
BORDER_FOCUS = "#CBD5E1"

PRI = "#2563EB"             # Яркий, современный Primary синий
PRI_H = "#1D4ED8"           # Синий при наведении
PRI_L = "#EFF6FF"           # Очень светлый синий для фонов активных элементов
PRI_MUTED = "#93C5FD"

TEAL = "#0EA5E9"            # Свежий бирюзово-голубой (вместо старого темного)
TEAL_H = "#0284C7"
TEAL_L = "#E0F2FE"

PLUM = "#6366F1"            # Мягкий индиго
PLUM_H = "#4F46E5"
PLUM_L = "#EEF2FF"

TEXT_MAIN = "#0F172A"       # Глубокий темный (почти черный, но мягче)
TEXT_SEC = "#475569"        # Вторичный текст
TEXT_TERT = "#94A3B8"       # Плейсхолдеры и мелкий текст

OK = "#10B981"              # Изумрудный зеленый (успех)
OK_H = "#059669"
OK_L = "#D1FAE5"

ERR = "#EF4444"             # Мягкий красный (ошибка)
ERR_H = "#DC2626"
ERR_L = "#FEE2E2"

WARN = "#F59E0B"            # Янтарный (предупреждение)
WARN_L = "#FEF3C7"

# --- ТИПОГРАФИКА ---
FONT_FAMILY = "Segoe UI" # Современный шрифт по умолчанию
H1 = (FONT_FAMILY, 24, "bold")
H2 = (FONT_FAMILY, 18, "bold")
H3 = (FONT_FAMILY, 14, "bold")
BODY = (FONT_FAMILY, 13)
BODY_BOLD = (FONT_FAMILY, 13, "bold")
SMALL = (FONT_FAMILY, 11)
SMALL_BOLD = (FONT_FAMILY, 11, "bold")
CODE = ("Consolas", 11)


def _popen_hidden(cmd, **kw):
    """Popen without visible console window on Windows."""
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        kw["startupinfo"] = si
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    return subprocess.Popen(cmd, **kw)

def _run_hidden(cmd, **kw):
    """subprocess.run without console window."""
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
    for n in ("yt-dlp_bundled.exe","yt-dlp.exe","yt-dlp"):
        p = resource_path(n)
        if os.path.isfile(p): return p
    return shutil.which("yt-dlp") or shutil.which("yt-dlp.exe") or "yt-dlp"

def get_ffmpeg():
    for n in ("ffmpeg_bundled.exe","ffmpeg.exe","ffmpeg"):
        p = resource_path(n)
        if os.path.isfile(p): return p
    return shutil.which("ffmpeg")

def friendly_size(b):
    if not b: return ""
    for u in ("B","KB","MB","GB"):
        if b<1024: return f"{b:.1f} {u}"
        b/=1024
    return f"{b:.1f} TB"

def fmt_dur(s):
    if not s: return "—"
    h,r=divmod(int(s),3600); m,sec=divmod(r,60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"

def ts(): return datetime.now().strftime("%H:%M:%S")

QUALITY_PRESETS =[
    {"label":"Лучшее качество", "sub":"авто",    "fmt":"bestvideo+bestaudio/best",                                        "h":9999},
    {"label":"4K",              "sub":"до 2160p", "fmt":"bestvideo[height<=2160]+bestaudio/best[height<=2160]/best",       "h":2160},
    {"label":"Full HD",         "sub":"до 1080p", "fmt":"bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",       "h":1080},
    {"label":"HD",              "sub":"до 720p",  "fmt":"bestvideo[height<=720]+bestaudio/best[height<=720]/best",         "h": 720},
    {"label":"SD",              "sub":"до 480p",  "fmt":"bestvideo[height<=480]+bestaudio/best[height<=480]/best",         "h": 480},
    {"label":"360p",            "sub":"до 360p",  "fmt":"bestvideo[height<=360]+bestaudio/best[height<=360]/best",         "h": 360},
    {"label":"Только аудио",    "sub":"MP3",      "fmt":"bestaudio/best",                                                  "h":   0},
]

def parse_raw_formats(info):
    out=[]; seen=set()
    for fmt in reversed(info.get("formats",[])):
        vid=fmt.get("vcodec","none"); aud=fmt.get("acodec","none")
        if not vid or vid=="none": continue
        h=fmt.get("height"); fps=fmt.get("fps"); ext=fmt.get("ext","?")
        fs=fmt.get("filesize") or fmt.get("filesize_approx"); tbr=fmt.get("tbr"); fid=fmt.get("format_id","")
        ha=bool(aud and aud!="none")
        key=(h,fps,ext,ha)
        if key in seen: continue
        seen.add(key)
        parts=[]
        if h: parts.append(f"{h}p")
        if fps and fps>30: parts.append(f"{int(fps)}fps")
        parts.append(ext.upper())
        if fs: parts.append(friendly_size(fs))
        elif tbr: parts.append(f"~{tbr:.0f}k")
        lbl=" · ".join(parts)+("" if ha else "  (без звука)")
        out.append({"id":fid,"label":lbl,"h":h or 0})
    out.sort(key=lambda x:x["h"],reverse=True)
    return out[:25]

class QueueItem:
    def __init__(self,url,fmt,title,is_pl=False,count=0):
        self.url=url;self.fmt=fmt;self.title=title;self.is_pl=is_pl;self.count=count;self.status="waiting"

class StyledCard(ctk.CTkFrame):
    """Современная карточка с плавными углами и чистым фоном."""
    def __init__(self,master,**kw):
        kw.setdefault("fg_color", PANEL_BG)
        kw.setdefault("corner_radius", 20)
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", BORDER)
        super().__init__(master,**kw)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Vidra 2026")
        self.geometry("1150x850")
        self.minsize(1000, 700)
        self.configure(fg_color=BG_MAIN)
        
        # Данные
        self._info={}; self._raw_formats=[]; self._is_playlist=False
        self._fetch_thread=None; self._dl_thread=None; self._mq=queue.Queue()
        self._dl_dir=os.path.join(os.path.expanduser("~"),"Downloads")
        self._dl_queue=[]; self._history=[]; self._ffmpeg_ok=bool(get_ffmpeg())
        self._fmt_radio_btns=[]
        
        # Анимация прогресс-бара
        self._current_prog_value = 0.0
        self._target_prog_value = 0.0
        
        # Переменные UI
        self._quality_idx=ctk.IntVar(value=2); self._raw_fmt_var=ctk.StringVar(value="")
        self._sub_var=ctk.BooleanVar(value=False); self._speed_var=ctk.StringVar(value="")
        self._tmpl_var=ctk.StringVar(value="%(title)s [%(id)s].%(ext)s")
        self._pl_tmpl_var=ctk.StringVar(value="%(playlist_title)s/%(playlist_index)s - %(title)s [%(id)s].%(ext)s")
        self._embed_thumb=ctk.BooleanVar(value=True); self._embed_meta=ctk.BooleanVar(value=True)
        
        self._build_ui()
        self._poll()
        
        self._log("ffmpeg найден — полный функционал" if self._ffmpeg_ok else
                  "ffmpeg не найден — видео скачается без склейки дорожек. Установи ffmpeg для лучшего качества.",
                  OK if self._ffmpeg_ok else WARN)

    def _build_ui(self):
        # Разделяем окно на Боковую панель (0) и Контент (1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._build_sidebar()
        
        # Контейнер для вкладок
        self._content_container = ctk.CTkFrame(self, fg_color="transparent")
        self._content_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self._content_container.grid_rowconfigure(0, weight=1)
        self._content_container.grid_columnconfigure(0, weight=1)
        
        # Инициализируем фреймы вкладок
        self._tabs = {}
        TABS =["download", "queue", "history", "settings"]
        
        self._tabs["download"] = ctk.CTkFrame(self._content_container, fg_color="transparent")
        self._tabs["queue"] = ctk.CTkFrame(self._content_container, fg_color="transparent")
        self._tabs["history"] = ctk.CTkFrame(self._content_container, fg_color="transparent")
        self._tabs["settings"] = ctk.CTkFrame(self._content_container, fg_color="transparent")
        
        for frame in self._tabs.values():
            frame.grid(row=0, column=0, sticky="nsew")
            
        self._build_dl_tab(self._tabs["download"])
        self._build_queue_tab(self._tabs["queue"])
        self._build_history_tab(self._tabs["history"])
        self._build_settings_tab(self._tabs["settings"])
        
        # Выбираем первую вкладку
        self._select_tab("download")

    def _build_sidebar(self):
        """Современный Sidebar с анимированным индикатором."""
        sb = ctk.CTkFrame(self, fg_color=SIDEBAR_BG, width=240, corner_radius=0, border_width=1, border_color=BORDER)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(6, weight=1) # Push version to bottom
        
        # Логотип и заголовок
        logo_container = ctk.CTkFrame(sb, fg_color="transparent")
        logo_container.grid(row=0, column=0, sticky="ew", padx=24, pady=(32, 40))
        
        try:
            logo_path = resource_path("vidra_logo_48.png")
            pil_img = PilImage.open(logo_path).resize((40,40), PilImage.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=pil_img, size=(40,40))
            logo_lbl = ctk.CTkLabel(logo_container, image=ctk_img, text="", fg_color="transparent")
            logo_lbl.pack(side="left")
        except Exception:
            # Fallback logo (Modern Pill shape)
            icon = ctk.CTkFrame(logo_container, fg_color=PRI, corner_radius=12, width=42, height=42)
            icon.pack(side="left", padx=(0,0))
            icon.pack_propagate(False)
            ctk.CTkLabel(icon, text="↓", font=(FONT_FAMILY, 24, "bold"), text_color="white").place(relx=.5, rely=.5, anchor="center")
            
        text_container = ctk.CTkFrame(logo_container, fg_color="transparent")
        text_container.pack(side="left", padx=(14, 0))
        ctk.CTkLabel(text_container, text="Vidra", font=H1, text_color=TEXT_MAIN).pack(anchor="w", pady=0)
        ctk.CTkLabel(text_container, text="by Sheri", font=SMALL, text_color=PRI).pack(anchor="w", pady=0)

        # Контейнер для навигации с относительным позиционированием для индикатора
        self._nav_frame = ctk.CTkFrame(sb, fg_color="transparent")
        self._nav_frame.grid(row=1, column=0, sticky="ew", padx=16)
        
        # Анимированный индикатор
        self._indicator = ctk.CTkFrame(self._nav_frame, fg_color=PRI, width=4, height=42, corner_radius=2)
        self._indicator.place(x=0, y=0)
        
        self._nav_buttons = {}
        
        def create_nav_btn(row_idx, tab_id, icon, text):
            btn = ctk.CTkButton(self._nav_frame, text=f"   {icon}   {text}", anchor="w", 
                                height=46, fg_color="transparent", text_color=TEXT_SEC,
                                hover_color=PRI_L, font=BODY_BOLD, corner_radius=12,
                                command=lambda: self._select_tab(tab_id))
            btn.grid(row=row_idx, column=0, sticky="ew", padx=(12, 0), pady=4)
            self._nav_buttons[tab_id] = btn

        create_nav_btn(0, "download", "⬇", "Скачать")
        create_nav_btn(1, "queue", "📋", "Очередь")
        create_nav_btn(2, "history", "🕒", "История")
        create_nav_btn(3, "settings", "⚙", "Настройки")
        
        # Footer Sidebar
        footer = ctk.CTkFrame(sb, fg_color="transparent")
        footer.grid(row=6, column=0, sticky="s", pady=24, padx=24)
        ctk.CTkLabel(footer, text="v6.0 • 2026 Edition", font=("Consolas", 10), text_color=TEXT_TERT).pack()

    def _select_tab(self, tab_id):
        # Анимация индикатора
        target_y = list(self._nav_buttons.keys()).index(tab_id) * 54 + 4 # 54 = 46(height) + 8(padding)
        self._animate_indicator(target_y)
        
        # Обновление стилей кнопок
        for t_id, btn in self._nav_buttons.items():
            if t_id == tab_id:
                btn.configure(fg_color=PRI_L, text_color=PRI)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SEC)
                
        # Переключение фреймов (tkraise выводит поверх остальных)
        self._tabs[tab_id].tkraise()

    def _animate_indicator(self, target_y):
        """Плавное перемещение индикатора вкладок."""
        current_y = float(self._indicator.place_info()['y'])
        diff = target_y - current_y
        if abs(diff) < 1.0:
            self._indicator.place(y=target_y)
            return
        # Идем на 25% за кадр
        self._indicator.place(y=current_y + diff * 0.25)
        self.after(16, lambda: self._animate_indicator(target_y))

    def _build_dl_tab(self, tab):
        tab.grid_columnconfigure(0, weight=6)
        tab.grid_columnconfigure(1, weight=4)
        tab.grid_rowconfigure(0, weight=1)
        
        left_col = ctk.CTkFrame(tab, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_col.grid_rowconfigure(2, weight=1)
        left_col.grid_columnconfigure(0, weight=1)
        
        right_col = ctk.CTkFrame(tab, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_col.grid_rowconfigure(0, weight=1)
        right_col.grid_columnconfigure(0, weight=1)
        
        self._build_url_card(left_col)
        self._build_pl_panel(left_col)
        self._build_fmt_card(left_col)
        
        self._build_log_card(right_col)
        self._build_footer_card(right_col)

    def _build_url_card(self, parent):
        card = StyledCard(parent)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        card.grid_columnconfigure(0, weight=1)
        
        # Заголовок
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text="Что будем скачивать?", font=H2, text_color=TEXT_MAIN).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(top, text="YouTube • RuTube • TikTok • VK • и 1000+ других", font=SMALL, text_color=TEXT_TERT).grid(row=1, column=0, sticky="w", pady=(2,0))
        
        # Поле ввода
        self._url_var = ctk.StringVar()
        self._url_entry = ctk.CTkEntry(
            card, textvariable=self._url_var, placeholder_text="Вставь ссылку сюда...",
            font=BODY, height=54, fg_color=BG_MAIN, border_color=BORDER,
            text_color=TEXT_MAIN, placeholder_text_color=TEXT_TERT, corner_radius=14
        )
        self._url_entry.grid(row=1, column=0, padx=24, pady=(0, 16), sticky="ew")
        self._url_entry.bind("<Return>", lambda _: self._do_fetch())
        
        # Панель кнопок под вводом
        br = ctk.CTkFrame(card, fg_color="transparent")
        br.grid(row=2, column=0, padx=24, pady=(0, 24), sticky="ew")
        br.grid_columnconfigure(2, weight=1)
        
        ctk.CTkButton(br, text="Вставить", width=90, height=36, fg_color=BG_MAIN, hover_color=BORDER, 
                      text_color=TEXT_SEC, corner_radius=10, font=BODY, command=self._paste).grid(row=0, column=0, padx=(0, 8))
        ctk.CTkButton(br, text="✕", width=36, height=36, fg_color=BG_MAIN, hover_color=BORDER, 
                      text_color=TEXT_TERT, corner_radius=10, font=BODY, command=lambda: self._url_var.set("")).grid(row=0, column=1, padx=(0, 16))
        
        ctk.CTkCheckBox(br, text="Субтитры", variable=self._sub_var, font=BODY, text_color=TEXT_SEC, 
                        fg_color=PRI, hover_color=PRI_H, border_color=BORDER, corner_radius=6, checkbox_width=20, checkbox_height=20).grid(row=0, column=2, sticky="w")
        
        self._fetch_btn = ctk.CTkButton(br, text="Найти форматы  🔍", height=42, fg_color=PRI, hover_color=PRI_H, 
                                        text_color="white", corner_radius=12, font=BODY_BOLD, command=self._do_fetch)
        self._fetch_btn.grid(row=0, column=3, sticky="e")
        
        # Строка с информацией о видео (появляется после поиска)
        self._info_lbl = ctk.CTkLabel(card, text="", font=SMALL_BOLD, text_color=PRI, wraplength=500, justify="left", anchor="w")
        self._info_lbl.grid(row=3, column=0, padx=24, pady=(0, 16), sticky="w")

    def _build_pl_panel(self, parent):
        self._pl_card = StyledCard(parent, fg_color=TEAL_L, border_color="#BDE4FB")
        self._pl_card.grid_columnconfigure(0, weight=1)
        
        ph = ctk.CTkFrame(self._pl_card, fg_color="transparent")
        ph.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        ph.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(ph, text="Обнаружен Плейлист", font=H3, text_color=TEAL_H).grid(row=0, column=0, sticky="w")
        self._pl_pill = ctk.CTkLabel(ph, text="0 видео", font=SMALL_BOLD, text_color="white", fg_color=TEAL_H, corner_radius=12)
        self._pl_pill.grid(row=0, column=1, ipadx=10, ipady=4)
        
        self._pl_scroll = ctk.CTkScrollableFrame(self._pl_card, fg_color="transparent", corner_radius=0, height=130)
        self._pl_scroll.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))
        self._pl_scroll.grid_columnconfigure(0, weight=1)

    def _build_fmt_card(self, parent):
        card = StyledCard(parent)
        card.grid(row=2, column=0, sticky="nsew")
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)
        
        fh = ctk.CTkFrame(card, fg_color="transparent")
        fh.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        fh.grid_columnconfigure(0, weight=1)
        
        self._fmt_title_lbl = ctk.CTkLabel(fh, text="Качество загрузки", font=H3, text_color=TEXT_MAIN)
        self._fmt_title_lbl.grid(row=0, column=0, sticky="w")
        self._fmt_cnt_lbl = ctk.CTkLabel(fh, text="", font=SMALL, text_color=TEXT_TERT)
        self._fmt_cnt_lbl.grid(row=0, column=1)
        
        # Рамка со списком форматов
        self._fmt_scroll = ctk.CTkScrollableFrame(card, fg_color=BG_MAIN, corner_radius=14)
        self._fmt_scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self._fmt_scroll.grid_columnconfigure(0, weight=1)
        
        self._fmt_ph = ctk.CTkLabel(self._fmt_scroll, text="Введи ссылку и нажми «Найти форматы» ⬆", font=BODY, text_color=TEXT_TERT)
        self._fmt_ph.grid(row=0, column=0, pady=60)

    def _build_log_card(self, parent):
        card = StyledCard(parent)
        card.grid(row=0, column=0, sticky="nsew", pady=(0, 16))
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)
        
        lh = ctk.CTkFrame(card, fg_color="transparent")
        lh.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        lh.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(lh, text="Журнал работы", font=H3, text_color=TEXT_MAIN).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(lh, text="Очистить", width=70, height=28, fg_color=BG_MAIN, hover_color=BORDER, 
                      text_color=TEXT_SEC, corner_radius=8, font=SMALL, command=self._clear_log).grid(row=0, column=1)
        
        # Терминало-подобный стиль
        self._log_box = ctk.CTkTextbox(card, fg_color="#F8FAFC", border_width=1, border_color=BORDER, corner_radius=12, 
                                       font=CODE, text_color=TEXT_SEC, wrap="word", state="disabled")
        self._log_box.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def _build_footer_card(self, parent):
        card = StyledCard(parent, fg_color=PANEL_BG)
        card.grid(row=1, column=0, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        
        # Папка сохранения
        fr = ctk.CTkFrame(card, fg_color="transparent")
        fr.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))
        fr.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(fr, text="📁 Сохранить в:", font=BODY_BOLD, text_color=TEXT_SEC).grid(row=0, column=0, padx=(0, 12))
        self._folder_lbl = ctk.CTkLabel(fr, text=self._dl_dir, font=BODY, text_color=TEXT_MAIN, anchor="w")
        self._folder_lbl.grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(fr, text="Изменить", width=80, height=30, fg_color=BG_MAIN, hover_color=BORDER, 
                      text_color=TEXT_SEC, corner_radius=8, font=SMALL, command=self._choose_folder).grid(row=0, column=2)
        
        # Анимированный прогресс-бар (поверхностный UI)
        pgf = ctk.CTkFrame(card, fg_color="transparent")
        pgf.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 12))
        pgf.grid_columnconfigure(0, weight=1)
        
        self._prog = ctk.CTkProgressBar(pgf, fg_color=BG_MAIN, progress_color=PRI, corner_radius=10, height=14)
        self._prog.set(0)
        self._prog.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        
        self._pct_lbl = ctk.CTkLabel(pgf, text="0%", width=46, font=BODY_BOLD, text_color=PRI, anchor="e")
        self._pct_lbl.grid(row=0, column=1)
        
        # Статус бар
        sf = ctk.CTkFrame(card, fg_color="transparent")
        sf.grid(row=2, column=0, sticky="w", padx=24, pady=(0, 16))
        
        self._status_dot = ctk.CTkLabel(sf, text="●", font=("Arial", 14), text_color=TEXT_TERT)
        self._status_dot.grid(row=0, column=0, padx=(0, 8))
        self._status_lbl = ctk.CTkLabel(sf, text="Ожидание ссылки...", font=BODY, text_color=TEXT_SEC, anchor="w")
        self._status_lbl.grid(row=0, column=1)
        
        # Основные кнопки действий
        br = ctk.CTkFrame(card, fg_color="transparent")
        br.grid(row=3, column=0, padx=24, pady=(0, 24), sticky="ew")
        br.grid_columnconfigure(1, weight=1)
        
        self._add_q_btn = ctk.CTkButton(br, text="➕  В очередь", width=130, height=48, fg_color=PLUM_L, 
                                        hover_color="#E0E7FF", text_color=PLUM_H, corner_radius=14, 
                                        font=BODY_BOLD, command=self._add_to_queue, state="disabled")
        self._add_q_btn.grid(row=0, column=0, sticky="w")
        
        self._dl_btn = ctk.CTkButton(br, text="⬇  Скачать сейчас", height=48, fg_color=OK, hover_color=OK_H, 
                                     text_color="white", corner_radius=14, font=H3, command=self._do_download, state="disabled")
        self._dl_btn.grid(row=0, column=1, sticky="e", padx=(12, 0))

    def _build_queue_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        hdr = ctk.CTkFrame(tab, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(0, 16))
        hdr.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(hdr, text="Очередь загрузок", font=H1, text_color=TEXT_MAIN).grid(row=0, column=0, sticky="w")
        
        ctk.CTkButton(hdr, text="Очистить", height=40, fg_color=BG_MAIN, hover_color=BORDER, 
                      text_color=TEXT_SEC, corner_radius=12, font=BODY, command=self._clear_queue).grid(row=0, column=1, padx=(0, 12))
        ctk.CTkButton(hdr, text="▶  Запустить всё", height=40, fg_color=PRI, hover_color=PRI_H, 
                      text_color="white", corner_radius=12, font=BODY_BOLD, command=self._run_queue).grid(row=0, column=2)
        
        self._queue_scroll = ctk.CTkScrollableFrame(tab, fg_color=PANEL_BG, corner_radius=20, border_width=1, border_color=BORDER)
        self._queue_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        self._queue_scroll.grid_columnconfigure(0, weight=1)
        
        self._queue_ph = ctk.CTkLabel(self._queue_scroll, text="Очередь пуста\nДобавляй видео кнопкой «➕ В очередь»", font=BODY, text_color=TEXT_TERT, justify="center")
        self._queue_ph.grid(row=0, column=0, pady=100)

    def _build_history_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        
        hdr = ctk.CTkFrame(tab, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(0, 16))
        hdr.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(hdr, text="История загрузок", font=H1, text_color=TEXT_MAIN).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(hdr, text="Очистить", height=40, fg_color=BG_MAIN, hover_color=BORDER, 
                      text_color=TEXT_SEC, corner_radius=12, font=BODY, command=self._clear_history).grid(row=0, column=1)
        
        self._hist_scroll = ctk.CTkScrollableFrame(tab, fg_color=PANEL_BG, corner_radius=20, border_width=1, border_color=BORDER)
        self._hist_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        self._hist_scroll.grid_columnconfigure(0, weight=1)
        
        self._hist_ph = ctk.CTkLabel(self._hist_scroll, text="История пуста. Скачай что-нибудь интересное!", font=BODY, text_color=TEXT_TERT)
        self._hist_ph.grid(row=0, column=0, pady=100)

    def _build_settings_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        
        # Главный заголовок настроек вне скролла для красоты
        hdr = ctk.CTkFrame(tab, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(0, 16))
        ctk.CTkLabel(hdr, text="Настройки программы", font=H1, text_color=TEXT_MAIN).pack(anchor="w")
        
        sc = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        sc.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        sc.grid_columnconfigure(0, weight=1)
        
        def sec(title, icon=""):
            f = StyledCard(sc)
            f.pack(fill="x", pady=(0, 16), padx=4)
            ctk.CTkLabel(f, text=f"{icon}  {title}", font=H3, text_color=TEXT_MAIN).grid(row=0, column=0, padx=24, pady=(20, 12), sticky="w", columnspan=4)
            f.grid_columnconfigure(1, weight=1)
            return f
            
        # FFmpeg
        ff = sec("Движок FFmpeg", "🎬")
        ctk.CTkLabel(ff, text="Статус интеграции:", font=BODY, text_color=TEXT_SEC).grid(row=1, column=0, padx=24, pady=(0, 12), sticky="w")
        
        ff_status = get_ffmpeg() or "Не найден (требуется установка)"
        ff_color = OK if self._ffmpeg_ok else ERR
        ctk.CTkLabel(ff, text=ff_status, font=BODY_BOLD, text_color=ff_color, anchor="w").grid(row=1, column=1, padx=8, pady=(0, 12), sticky="ew")
        
        ctk.CTkButton(ff, text="Скачать FFmpeg", width=140, height=36, fg_color=TEAL, hover_color=TEAL_H, 
                      text_color="white", corner_radius=10, font=BODY, command=lambda: self._open_url("https://ffmpeg.org/download.html")).grid(row=1, column=2, padx=24, pady=(0, 12))
        
        msg = "✓ Полный функционал доступен. Видео и аудио склеиваются автоматически." if self._ffmpeg_ok else "⚠ Без FFmpeg: видео скачается, но без склейки высшего качества. Установи FFmpeg и добавь в PATH."
        ctk.CTkLabel(ff, text=msg, font=SMALL, text_color=OK if self._ffmpeg_ok else WARN, justify="left").grid(row=2, column=0, columnspan=3, padx=24, pady=(0, 24), sticky="w")
        
        # Шаблоны
        out = sec("Шаблон имени — Одиночное видео", "📄")
        ctk.CTkLabel(out, text="Формат:", font=BODY, text_color=TEXT_SEC).grid(row=1, column=0, padx=24, pady=(0, 12), sticky="w")
        ctk.CTkEntry(out, textvariable=self._tmpl_var, font=CODE, height=40, fg_color=BG_MAIN, border_color=BORDER, text_color=TEXT_MAIN, corner_radius=10).grid(row=1, column=1, padx=8, pady=(0, 12), sticky="ew", columnspan=2)
        ctk.CTkLabel(out, text="Доступно: %(title)s, %(id)s, %(ext)s, %(uploader)s, %(upload_date)s", font=SMALL, text_color=TEXT_TERT, anchor="w").grid(row=2, column=0, columnspan=3, padx=24, pady=(0, 24), sticky="w")
        
        pl_s = sec("Шаблон имени — Плейлист", "📁")
        ctk.CTkLabel(pl_s, text="Формат:", font=BODY, text_color=TEXT_SEC).grid(row=1, column=0, padx=24, pady=(0, 12), sticky="w")
        ctk.CTkEntry(pl_s, textvariable=self._pl_tmpl_var, font=CODE, height=40, fg_color=BG_MAIN, border_color=BORDER, text_color=TEXT_MAIN, corner_radius=10).grid(row=1, column=1, padx=8, pady=(0, 12), sticky="ew", columnspan=2)
        ctk.CTkLabel(pl_s, text="Доступно: %(playlist_title)s, %(playlist_index)s, %(title)s, %(id)s", font=SMALL, text_color=TEXT_TERT, anchor="w").grid(row=2, column=0, columnspan=3, padx=24, pady=(0, 24), sticky="w")
        
        # Лимит скорости
        sp = sec("Лимит скорости загрузки", "⚡")
        ctk.CTkLabel(sp, text="Скорость:", font=BODY, text_color=TEXT_SEC).grid(row=1, column=0, padx=24, pady=(0, 24), sticky="w")
        ctk.CTkEntry(sp, textvariable=self._speed_var, placeholder_text="напр. 5M или 500K (оставь пустым для максимума)", font=BODY, height=40, fg_color=BG_MAIN, border_color=BORDER, text_color=TEXT_MAIN, corner_radius=10).grid(row=1, column=1, padx=8, pady=(0, 24), sticky="ew", columnspan=2)
        
        # Метаданные
        emb = sec("Метаданные (требует FFmpeg)", "🏷")
        ctk.CTkCheckBox(emb, text="Встроить обложку (Thumbnail)", variable=self._embed_thumb, font=BODY, text_color=TEXT_SEC, fg_color=PRI, hover_color=PRI_H, corner_radius=6, checkbox_width=20, checkbox_height=20).grid(row=1, column=0, padx=24, pady=(0, 12), sticky="w")
        ctk.CTkCheckBox(emb, text="Встроить теги (Название, Автор, Дата)", variable=self._embed_meta, font=BODY, text_color=TEXT_SEC, fg_color=PRI, hover_color=PRI_H, corner_radius=6, checkbox_width=20, checkbox_height=20).grid(row=2, column=0, padx=24, pady=(0, 24), sticky="w")
        
        # О программе
        abt = sec("О программе Vidra", "ℹ")
        ctk.CTkLabel(abt, text="Vidra 2026 Edition • powered by Sheri\nОсновано на открытом движке yt-dlp.", font=BODY, text_color=TEXT_SEC, justify="left", anchor="w").grid(row=1, column=0, padx=24, pady=(0, 16), sticky="w")
        bf = ctk.CTkFrame(abt, fg_color="transparent")
        bf.grid(row=2, column=0, padx=24, pady=(0, 24), sticky="w")
        ctk.CTkButton(bf, text="GitHub yt-dlp", width=130, height=36, fg_color=BG_MAIN, hover_color=BORDER, text_color=TEXT_MAIN, corner_radius=10, font=BODY_BOLD, command=lambda: self._open_url("https://github.com/yt-dlp/yt-dlp")).pack(side="left", padx=(0, 12))
        ctk.CTkButton(bf, text="Список поддерживаемых сайтов", width=220, height=36, fg_color=BG_MAIN, hover_color=BORDER, text_color=TEXT_MAIN, corner_radius=10, font=BODY_BOLD, command=lambda: self._open_url("https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md")).pack(side="left")

    # Helpers
    def _paste(self):
        try: self._url_var.set(self.clipboard_get())
        except: pass

    def _choose_folder(self):
        d = filedialog.askdirectory(initialdir=self._dl_dir)
        if d: 
            self._dl_dir = d
            self._folder_lbl.configure(text=d)

    def _open_url(self, url):
        import webbrowser; webbrowser.open(url)

    def _log(self, msg, color=None): self._mq.put(("log", msg, color))
    def _set_status(self, msg, c=TEXT_TERT): self._mq.put(("status", msg, c))
    
    def _set_prog(self, v): 
        # Вместо резкого прыжка обновляем целевое значение для анимации
        self._target_prog_value = v

    def _poll(self):
        # 1. Обработка очереди сообщений
        try:
            while True:
                k, a, b = self._mq.get_nowait()
                if k == "log": self._write_log(a, b)
                elif k == "status": 
                    self._status_lbl.configure(text=a, text_color=b or TEXT_SEC)
                    self._status_dot.configure(text_color=b or TEXT_TERT)
                elif k == "fetch_done": self._on_fetch_done(a)
                elif k == "dl_done": self._on_dl_done(a)
                elif k == "q_refresh": self._refresh_queue()
                elif k == "h_refresh": self._refresh_history()
        except queue.Empty: pass

        # 2. Плавная анимация прогресс-бара (Tweening)
        if abs(self._current_prog_value - self._target_prog_value) > 0.001:
            # Двигаемся на 15% дистанции каждый тик (создает приятный эффект замедления)
            self._current_prog_value += (self._target_prog_value - self._current_prog_value) * 0.15
            self._prog.set(self._current_prog_value)
            pct = int(self._current_prog_value * 100)
            self._pct_lbl.configure(text=f"{pct}%" if self._current_prog_value > 0.01 else "0%")
        else:
            # Защита от бесконечных микро-вычислений
            self._current_prog_value = self._target_prog_value
            self._prog.set(self._current_prog_value)

        self.after(30, self._poll) # Частота кадров UI ~30-33 FPS

    def _write_log(self, msg, color=None):
        self._log_box.configure(state="normal")
        # В CTkText цвет для отдельных строк сделать сложно, но формат оставляем чистым
        self._log_box.insert("end", f"[{ts()}] {msg}\n")
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
            messagebox.showwarning("Внимание", "Пожалуйста, вставь ссылку на видео!")
            return
            
        if self._fetch_thread and self._fetch_thread.is_alive(): return
        
        self._fetch_btn.configure(state="disabled", text="Анализирую...")
        self._dl_btn.configure(state="disabled")
        self._add_q_btn.configure(state="disabled")
        
        self._clear_fmt_list()
        self._fmt_ph.configure(text="⏳ Подключаюсь к сервису, ищу форматы...")
        self._fmt_ph.grid()
        self._hide_pl()
        self._info_lbl.configure(text="")
        
        self._log(f"Запрос инфо: {url[:80]}...")
        self._set_status("Получаю информацию о видео...", TEXT_TERT)
        
        def worker():
            try:
                r = _run_hidden([get_ytdlp(), "--flat-playlist", "--dump-single-json", url], capture_output=True, text=True, timeout=45, encoding="utf-8", errors="replace")
                if r.returncode != 0:
                    lines = (r.stderr or "").strip().splitlines()
                    raise RuntimeError(lines[-1] if lines else "yt-dlp error")
                
                info = json.loads(r.stdout)
                is_pl = info.get("_type") in ("playlist", "multi_video") or "entries" in info
                
                if is_pl:
                    entries = info.get("entries") or[]
                    self._mq.put(("fetch_done", {
                        "type": "playlist", "title": info.get("title") or "Плейлист",
                        "uploader": info.get("uploader") or info.get("channel", ""),
                        "count": len(entries), "url": url,
                        "entries":[{"idx": e.get("playlist_index") or (i+1), "title": e.get("title", "Видео "+str(i+1)), "id": e.get("id", ""), "url": e.get("url") or e.get("webpage_url", "")} for i, e in enumerate(entries) if e]
                    }, None))
                else:
                    r2 = _run_hidden([get_ytdlp(), "--dump-json", "--no-playlist", url], capture_output=True, text=True, timeout=45, encoding="utf-8", errors="replace")
                    if r2.returncode != 0:
                        lines = (r2.stderr or "").strip().splitlines()
                        raise RuntimeError(lines[-1] if lines else "yt-dlp error")
                    
                    full = json.loads(r2.stdout)
                    self._mq.put(("fetch_done", {"type": "single", "info": full, "raw_formats": parse_raw_formats(full)}, None))
                    
            except Exception as e: 
                self._mq.put(("fetch_done", {"type": "error", "msg": str(e)}, None))
                
        self._fetch_thread = threading.Thread(target=worker, daemon=True)
        self._fetch_thread.start()

    def _on_fetch_done(self, p):
        self._fetch_btn.configure(state="normal", text="Найти форматы  🔍")
        
        if p["type"] == "error":
            self._log(f"ОШИБКА: {p['msg']}", ERR)
            self._set_status(f"Ошибка получения данных", ERR)
            self._fmt_ph.configure(text="❌ Не удалось получить информацию.\nПроверь ссылку или подключение к сети.")
            return
            
        if p["type"] == "playlist":
            self._is_playlist = True
            self._info = p
            self._info_lbl.configure(text=f"🎬 {p['title'][:60]}  •  {p['count']} видео  •  👤 {p['uploader'][:28]}")
            self._log(f"Найден плейлист «{p['title'][:55]}» ({p['count']} видео)")
            self._set_status(f"Плейлист обработан ({p['count']} шт.). Выбери качество.", OK)
            self._show_pl(p["entries"])
            self._populate_presets_only()
        else:
            self._is_playlist = False
            fi = p["info"]
            self._info = fi
            self._raw_formats = p["raw_formats"]
            dur = fmt_dur(fi.get('duration'))
            upl = (fi.get('uploader') or fi.get('channel', ''))[:28]
            self._info_lbl.configure(text=f"🎬 {fi.get('title','?')[:68]}   ⏱ {dur}   👤 {upl}")
            self._log(f"Найдено видео «{fi.get('title','?')[:55]}» ({len(self._raw_formats)} форматов)")
            self._set_status("Форматы загружены. Можно скачивать!", OK)
            self._populate_all_formats()
            
        self._dl_btn.configure(state="normal")
        self._add_q_btn.configure(state="normal")

    def _clear_fmt_list(self):
        for w in self._fmt_scroll.winfo_children():
            if w != self._fmt_ph: w.destroy()
        self._fmt_radio_btns =[]
        self._raw_fmt_var.set("")

    def _add_preset_row(self, row, idx, preset):
        f = ctk.CTkFrame(self._fmt_scroll, fg_color="transparent")
        f.grid(row=row, column=0, padx=12, pady=4, sticky="ew")
        f.grid_columnconfigure(1, weight=1)
        
        btn = ctk.CTkRadioButton(
            f, text=preset["label"], variable=self._quality_idx, value=idx,
            font=BODY_BOLD, text_color=TEXT_MAIN, fg_color=PRI, hover_color=PRI_H, 
            border_color=BORDER_FOCUS, radiobutton_width=20, radiobutton_height=20, command=self._on_q_pick
        )
        btn.grid(row=0, column=0, sticky="w")
        
        sub_badge = ctk.CTkLabel(f, text=preset["sub"], font=SMALL, text_color=TEXT_SEC, fg_color=BG_MAIN, corner_radius=6)
        sub_badge.grid(row=0, column=1, padx=(12, 0), sticky="w", ipadx=8, ipady=2)
        
        self._fmt_radio_btns.append(btn)

    def _populate_presets_only(self):
        self._fmt_ph.grid_remove()
        self._clear_fmt_list()
        self._fmt_title_lbl.configure(text="Максимальное качество")
        self._fmt_cnt_lbl.configure(text="Пресеты для плейлиста")
        
        msg = "Каждое видео скачается в лучшем доступном\nкачестве до выбранного максимума:"
        ctk.CTkLabel(self._fmt_scroll, text=msg, font=BODY, text_color=TEXT_SEC, justify="left").grid(row=0, column=0, padx=16, pady=(10, 16), sticky="w")
        
        for i, p in enumerate(QUALITY_PRESETS): 
            self._add_preset_row(i+1, i, p)
            
        self._quality_idx.set(2)

    def _populate_all_formats(self):
        self._fmt_ph.grid_remove()
        self._clear_fmt_list()
        self._fmt_title_lbl.configure(text="Выбор качества")
        self._fmt_cnt_lbl.configure(text=f"{len(QUALITY_PRESETS) + len(self._raw_formats)} вариантов")
        
        # Разделитель Умные пресеты
        sep1 = ctk.CTkLabel(self._fmt_scroll, text="УМНЫЕ ПРЕСЕТЫ", font=("Segoe UI", 10, "bold"), text_color=TEXT_TERT)
        sep1.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")
        
        for i, p in enumerate(QUALITY_PRESETS): 
            self._add_preset_row(i+1, i, p)
            
        if self._raw_formats:
            sep2 = ctk.CTkLabel(self._fmt_scroll, text="ПРЯМЫЕ ФОРМАТЫ С СЕРВЕРА", font=("Segoe UI", 10, "bold"), text_color=TEXT_TERT)
            sep2.grid(row=len(QUALITY_PRESETS)+1, column=0, padx=16, pady=(24, 8), sticky="w")
            
            for j, fmt in enumerate(self._raw_formats):
                btn = ctk.CTkRadioButton(
                    self._fmt_scroll, text=fmt["label"], variable=self._raw_fmt_var, value=fmt["id"],
                    font=BODY, text_color=TEXT_SEC, fg_color=PRI, hover_color=PRI_H, 
                    border_color=BORDER_FOCUS, radiobutton_width=18, radiobutton_height=18, command=self._on_raw_pick
                )
                btn.grid(row=len(QUALITY_PRESETS) + 2 + j, column=0, padx=16, pady=6, sticky="w")
                self._fmt_radio_btns.append(btn)
                
        self._quality_idx.set(2)

    def _on_q_pick(self): 
        self._raw_fmt_var.set("")
        self._dl_btn.configure(state="normal")
        self._add_q_btn.configure(state="normal")
        
    def _on_raw_pick(self): 
        self._quality_idx.set(-1)
        self._dl_btn.configure(state="normal")
        self._add_q_btn.configure(state="normal")
        
    def _get_fmt(self):
        raw = self._raw_fmt_var.get()
        if raw: return raw
        idx = self._quality_idx.get()
        return QUALITY_PRESETS[idx]["fmt"] if 0 <= idx < len(QUALITY_PRESETS) else "bestvideo+bestaudio/best"

    def _show_pl(self, entries):
        self._pl_card.grid(row=1, column=0, sticky="ew", pady=(0, 16), in_=self._pl_card.master)
        self._pl_pill.configure(text=f"{len(entries)} видео")
        for w in self._pl_scroll.winfo_children(): w.destroy()
        
        for i, e in enumerate(entries[:60]):
            row = ctk.CTkFrame(self._pl_scroll, fg_color="transparent")
            row.grid(row=i, column=0, sticky="ew", pady=2)
            row.grid_columnconfigure(1, weight=1)
            
            ctk.CTkLabel(row, text=f"{e['idx']:>3}.", font=CODE, text_color=TEXT_TERT, width=36).grid(row=0, column=0, padx=(4, 8))
            ctk.CTkLabel(row, text=e["title"][:72], font=BODY, text_color=TEXT_MAIN, anchor="w").grid(row=0, column=1, sticky="w")
            
        if len(entries) > 60: 
            ctk.CTkLabel(self._pl_scroll, text=f"... и ещё {len(entries)-60} видео", font=BODY, text_color=TEXT_TERT).grid(row=60, column=0, pady=8)
            
    def _hide_pl(self):
        try: self._pl_card.grid_remove()
        except: pass

    # Download Engine
    def _build_cmd(self, url, fmt, is_pl=False):
        ff = get_ffmpeg()
        audio_only = fmt == "bestaudio/best"
        tmpl = os.path.join(self._dl_dir, self._pl_tmpl_var.get() if is_pl else self._tmpl_var.get())
        pl_flag = ["--yes-playlist"] if is_pl else ["--no-playlist"]
        
        cmd =[get_ytdlp(), "-f", fmt, "--progress", "--newline", "-o", tmpl] + pl_flag
        
        if audio_only:
            cmd +=["--extract-audio", "--audio-format", "mp3", "--audio-quality", "0"]
            if ff: cmd += ["--ffmpeg-location", ff]
        else:
            if ff:
                cmd +=["--merge-output-format", "mp4", "--ffmpeg-location", ff]
                if self._embed_thumb.get(): cmd += ["--embed-thumbnail"]
                if self._embed_meta.get():  cmd += ["--add-metadata"]
                
        if self._sub_var.get(): 
            cmd +=["--write-sub", "--write-auto-sub", "--sub-langs", "ru,en"]
            
        lim = self._speed_var.get().strip()
        if lim: cmd += ["--limit-rate", lim]
        
        cmd.append(url)
        return cmd

    def _do_download(self):
        url = self._url_var.get().strip()
        if not url: return
        if self._dl_thread and self._dl_thread.is_alive(): 
            messagebox.showinfo("Процесс занят", "Пожалуйста, дождись окончания текущей загрузки!")
            return
            
        fmt = self._get_fmt()
        is_pl = self._is_playlist
        title = self._info.get("title", "?")
        
        self._dl_btn.configure(state="disabled", text="Скачивание...")
        self._set_prog(0)
        
        self._log(f"▶ Начинаю загрузку: {'[ПЛЕЙЛИСТ]' if is_pl else '[ВИДЕО]'} {title[:50]}  |  Формат: {fmt}")
        cmd = self._build_cmd(url, fmt, is_pl)
        
        def worker():
            if is_pl: 
                ok, path, warn = self._run_playlist(cmd, self._info.get("count", 1))
            else: 
                ok, path, warn = self._run_single(cmd)
                
            if ok: 
                self._history.append({
                    "title": title, "url": url, "path": path, "is_pl": is_pl, 
                    "ts": datetime.now().strftime("%d.%m.%Y %H:%M")
                })
            self._mq.put(("dl_done", (ok, path, warn), None))
            
        self._dl_thread = threading.Thread(target=worker, daemon=True)
        self._dl_thread.start()

    def _run_single(self, cmd):
        pct_re = re.compile(r"\[download\]\s+([\d.]+)%")
        dest_re = re.compile(r"Destination:\s*(.+)")
        merge_re = re.compile(r'Merging formats into ["\'](.+)["\']')
        
        last_path = ""
        ffmpeg_warn = False
        
        try:
            proc = _popen_hidden(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
            for line in proc.stdout:
                line = line.rstrip()
                
                m = pct_re.search(line)
                if m: 
                    self._set_prog(float(m.group(1)) / 100)
                    self._set_status(f"Загрузка файла... {m.group(1)}%", PRI)
                    continue
                    
                dm = dest_re.search(line)
                if dm: last_path = dm.group(1).strip()
                
                mm = merge_re.search(line)
                if mm: last_path = mm.group(1).strip()
                
                lo = line.lower()
                if "ffmpeg not found" in lo or ("postprocessing" in lo and "error" in lo): 
                    ffmpeg_warn = True
                    self._log(f"WARN: {line}", WARN)
                    continue
                    
                if line and "[download]  " not in line: 
                    self._log(line)
                    
            proc.wait()
            
            if last_path and os.path.isfile(last_path): return True, last_path, ffmpeg_warn
            if proc.returncode == 0: return True, last_path, ffmpeg_warn
            if ffmpeg_warn: return True, last_path, True
            return False, "", False
            
        except FileNotFoundError: 
            self._log("yt-dlp не найден! Положи его в папку с программой.", ERR)
            return False, "", False
        except Exception as e: 
            self._log(f"Критическая ошибка: {e}", ERR)
            return False, "", False

    def _run_playlist(self, cmd, total):
        pct_re = re.compile(r"\[download\]\s+([\d.]+)%")
        vidnum_re = re.compile(r"\[download\] Downloading (?:item|video) (\d+) of (\d+)")
        dest_re = re.compile(r"Destination:\s*(.+)")
        merge_re = re.compile(r'Merging formats into ["\'](.+)["\']')
        
        current = 0
        last_path = ""
        ffmpeg_warn = False
        
        try:
            proc = _popen_hidden(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
            for line in proc.stdout:
                line = line.rstrip()
                
                m2 = vidnum_re.search(line)
                if m2:
                    current = int(m2.group(1))
                    tot = int(m2.group(2))
                    self._set_status(f"Обработка видео {current} из {tot}...", PRI)
                    self._set_prog((current - 1) / max(tot, 1))
                    self._log(f"▶ Скачивание видео {current}/{tot}")
                    continue
                    
                m = pct_re.search(line)
                if m:
                    pct = float(m.group(1)) / 100
                    overall = (max(current - 1, 0) + pct) / max(total, 1)
                    self._set_prog(min(overall, 1.0))
                    self._set_status(f"Видео {current}/{total}  —  {m.group(1)}%", PRI)
                    continue
                    
                dm = dest_re.search(line)
                if dm: last_path = dm.group(1).strip()
                
                mm = merge_re.search(line)
                if mm: last_path = mm.group(1).strip()
                
                lo = line.lower()
                if "ffmpeg not found" in lo or ("postprocessing" in lo and "error" in lo): 
                    ffmpeg_warn = True
                    self._log(f"WARN: {line}", WARN)
                    continue
                    
                if line and "[download]  " not in line: 
                    self._log(line)
                    
            proc.wait()
            folder = os.path.dirname(last_path) if last_path else self._dl_dir
            if proc.returncode == 0 or ffmpeg_warn: return True, folder, ffmpeg_warn
            return False, "", False
            
        except FileNotFoundError: 
            self._log("yt-dlp не найден!", ERR)
            return False, "", False
        except Exception as e: 
            self._log(f"Ошибка: {e}", ERR)
            return False, "", False

    def _on_dl_done(self, payload):
        ok, path, warn = payload
        self._dl_btn.configure(state="normal", text="⬇  Скачать сейчас")
        
        if ok:
            self._set_prog(1)
            if warn: 
                self._log("Успешно завершено! (но без ffmpeg-склейки)", WARN)
                self._set_status("Готово. Рекомендуется установить FFmpeg", WARN)
            else: 
                self._log("Успешно завершено!", OK)
                self._set_status("Загрузка успешно завершена! 🎉", OK)
                
            self._refresh_history()
            folder = (os.path.dirname(path) if path and os.path.isfile(path) else path if path and os.path.isdir(path) else self._dl_dir)
            
            # Custom Success Message Box
            if messagebox.askyesno("Отличные новости!", "Загрузка успешно завершена!\n\nОткрыть папку с файлами?"): 
                self._reveal(folder)
        else: 
            self._log("Загрузка завершилась с ошибкой. См. журнал.", ERR)
            self._set_status("Сбой при загрузке ❌", ERR)

    def _reveal(self, path):
        if os.path.isfile(path): folder = os.path.dirname(path)
        else: folder = path
        
        if sys.platform == "win32":
            if os.path.isfile(path): subprocess.Popen(["explorer", "/select,", path])
            else: subprocess.Popen(["explorer", folder])
        elif sys.platform == "darwin": 
            subprocess.Popen(["open", "-R", path])
        else: 
            subprocess.Popen(["xdg-open", folder])

    # Queue Logic
    def _add_to_queue(self):
        url = self._url_var.get().strip()
        fmt = self._get_fmt()
        if not url or not fmt: return
        
        is_pl = self._is_playlist
        title = self._info.get("title", "Неизвестное видео")
        count = self._info.get("count", 0) if is_pl else 0
        
        self._dl_queue.append(QueueItem(url, fmt, title, is_pl, count))
        self._refresh_queue()
        
        self._log(f"+ Добавлено в очередь: {'плейлист ('+str(count)+' видео)' if is_pl else 'видео'}  «{title[:40]}»")
        
        # Визуальная обратная связь для пользователя - мигание кнопки
        orig_color = self._add_q_btn.cget("fg_color")
        self._add_q_btn.configure(fg_color=OK_L, text_color=OK_H, text="✓ Добавлено")
        self.after(1500, lambda: self._add_q_btn.configure(fg_color=orig_color, text_color=PLUM_H, text="➕  В очередь"))

    def _refresh_queue(self):
        for w in self._queue_scroll.winfo_children():
            if w != self._queue_ph: w.destroy()
            
        if not self._dl_queue: 
            self._queue_ph.grid()
            return
            
        self._queue_ph.grid_remove()
        
        # Дизайн карточек очереди
        STATUS_STYLES = {
            "waiting": (TEXT_TERT, "⏳ Ожидает", BG_MAIN, BORDER),
            "running": (PRI, "▶ В процессе", PRI_L, PRI_MUTED),
            "done":    (OK, "✓ Готово", OK_L, OK),
            "fail":    (ERR, "✕ Ошибка", ERR_L, ERR)
        }
        
        for i, item in enumerate(self._dl_queue):
            text_color, icon_text, bg_color, border_col = STATUS_STYLES.get(item.status, STATUS_STYLES["waiting"])
            
            row = ctk.CTkFrame(self._queue_scroll, fg_color=PANEL_BG, border_color=border_col, border_width=1, corner_radius=14)
            row.grid(row=i, column=0, sticky="ew", padx=8, pady=6)
            row.grid_columnconfigure(1, weight=1)
            
            # Badge Status
            badge = ctk.CTkLabel(row, text=icon_text, font=SMALL_BOLD, text_color=text_color, fg_color=bg_color, corner_radius=8)
            badge.grid(row=0, column=0, padx=(16, 12), pady=16, ipadx=10, ipady=4)
            
            # Title
            title_text = f"📁 Плейлист ({item.count} шт) • " if item.is_pl else "🎬 Видео • "
            title_text += item.title[:65] + ("..." if len(item.title) > 65 else "")
            ctk.CTkLabel(row, text=title_text, font=BODY_BOLD, text_color=TEXT_MAIN, anchor="w").grid(row=0, column=1, sticky="ew")
            
            # Delete Button
            if item.status != "running":
                ctk.CTkButton(row, text="✕", width=36, height=36, fg_color="transparent", hover_color=ERR_L, 
                              text_color=ERR, corner_radius=10, font=BODY, command=lambda idx=i: self._remove_q(idx)).grid(row=0, column=2, padx=(0, 16))

    def _remove_q(self, idx):
        if 0 <= idx < len(self._dl_queue): 
            self._dl_queue.pop(idx)
            self._refresh_queue()
            
    def _clear_queue(self): 
        self._dl_queue =[q for q in self._dl_queue if q.status == "running"] # Оставляем только те, что качаются
        self._refresh_queue()

    def _run_queue(self):
        if not self._dl_queue: 
            messagebox.showinfo("Очередь пуста", "Добавь видео или плейлисты в очередь!")
            return
            
        if self._dl_thread and self._dl_thread.is_alive(): 
            messagebox.showinfo("Занято", "Сначала дождись окончания текущего процесса.")
            return
            
        def worker():
            for item in self._dl_queue:
                if item.status == "done": continue
                
                item.status = "running"
                self._mq.put(("q_refresh", None, None))
                self._log(f"⚡ Запуск из очереди: {'[PL]' if item.is_pl else '[V]'} {item.title[:50]}", PRI)
                
                cmd = self._build_cmd(item.url, item.fmt, item.is_pl)
                if item.is_pl: ok, path, warn = self._run_playlist(cmd, item.count)
                else: ok, path, warn = self._run_single(cmd)
                
                item.status = "done" if ok else "fail"
                
                if ok: 
                    self._history.append({
                        "title": item.title, "url": item.url, "path": path, 
                        "is_pl": item.is_pl, "ts": datetime.now().strftime("%d.%m.%Y %H:%M")
                    })
                    
                self._mq.put(("log", f"{'УСПЕХ' if ok else 'ОШИБКА'}: {item.title[:50]}", OK if ok else ERR))
                self._mq.put(("q_refresh", None, None))
                
            self._mq.put(("status", "Очередь полностью обработана! 🎉", OK))
            self._mq.put(("h_refresh", None, None))
            
        self._dl_thread = threading.Thread(target=worker, daemon=True)
        self._dl_thread.start()

    # History Logic
    def _refresh_history(self):
        for w in self._hist_scroll.winfo_children():
            if w != self._hist_ph: w.destroy()
            
        if not self._history: 
            self._hist_ph.grid()
            return
            
        self._hist_ph.grid_remove()
        
        for i, item in enumerate(reversed(self._history)):
            is_pl = item.get("is_pl", False)
            
            row = ctk.CTkFrame(self._hist_scroll, fg_color=PANEL_BG, border_color=BORDER, border_width=1, corner_radius=14)
            row.grid(row=i, column=0, sticky="ew", padx=8, pady=6)
            row.grid_columnconfigure(1, weight=1)
            
            # Badge
            badge_color, badge_bg, badge_txt = (TEAL, TEAL_L, "ПЛЕЙЛИСТ") if is_pl else (OK, OK_L, "ВИДЕО")
            ctk.CTkLabel(row, text=badge_txt, font=SMALL_BOLD, text_color=badge_color, fg_color=badge_bg, corner_radius=8).grid(row=0, column=0, padx=(16, 12), pady=16, ipadx=10, ipady=4)
            
            # Info
            inf = ctk.CTkFrame(row, fg_color="transparent")
            inf.grid(row=0, column=1, sticky="ew")
            
            title_text = item["title"][:75] + ("..." if len(item["title"]) > 75 else "")
            ctk.CTkLabel(inf, text=title_text, font=BODY_BOLD, text_color=TEXT_MAIN, anchor="w").grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(inf, text=item["ts"], font=SMALL, text_color=TEXT_TERT, anchor="w").grid(row=1, column=0, sticky="w", pady=(2, 0))
            
            # Action Button
            p = item.get("path", "")
            exists = bool(p) and (os.path.isfile(p) or os.path.isdir(p))
            
            btn_text = "Открыть файл" if exists and os.path.isfile(p) else "Открыть папку"
            btn_color = PRI_L if exists else BG_MAIN
            btn_txt_col = PRI if exists else TEXT_SEC
            
            ctk.CTkButton(row, text=btn_text, width=120, height=36, fg_color=btn_color, hover_color=BORDER_FOCUS if not exists else "#DBEAFE", 
                          text_color=btn_txt_col, corner_radius=10, font=BODY_BOLD, 
                          command=lambda pp=p: self._reveal(pp or self._dl_dir)).grid(row=0, column=2, padx=(0, 16))

    def _clear_history(self): 
        if messagebox.askyesno("Очистить историю?", "Удалить все записи о загрузках из истории?"):
            self._history.clear()
            self._refresh_history()

if __name__ == "__main__":
    app = App()
    # Запуск приложения
    app.mainloop()