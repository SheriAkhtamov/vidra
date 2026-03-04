"""Vidra — powered by Sheri  |  v6"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading, subprocess, json, os, sys, re, queue, shutil
from datetime import datetime
from PIL import Image as PilImage

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Palette
BG="#F0F5FF"; PANEL="#FFFFFF"; CARD="#F5F9FF"; CARD2="#EAF1FF"; BORDER="#B8CEED"; BORDER2="#D0E1F8"
PRI="#1A5FBE"; PRI_H="#1348A0"; PRI_L="#DDEAFC"
TEAL="#0D8A7A"; TEAL_H="#0A6E61"; TEAL_L="#D5F0EC"
PLUM="#5B4BBF"; PLUM_H="#4A3CAA"; PLUM_L="#E4E0F8"
TEXT="#0D1B38"; TEXT2="#3D5278"; TEXT3="#7A90B8"
OK="#1A7840"; OK_H="#145E30"; OK_L="#D8F0E3"
ERR="#C0392B"; ERR_L="#FDECEA"
INFO_C="#1A5FBE"; WARN_C="#B06010"; WARN_L="#FEF3E2"

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

QUALITY_PRESETS = [
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
    def __init__(self,master,**kw):
        kw.setdefault("fg_color",PANEL); kw.setdefault("corner_radius",16)
        kw.setdefault("border_width",1); kw.setdefault("border_color",BORDER)
        super().__init__(master,**kw)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Vidra"); self.geometry("1080x800"); self.minsize(900,660)
        self.configure(fg_color=BG)
        self._info={}; self._raw_formats=[]; self._is_playlist=False
        self._fetch_thread=None; self._dl_thread=None; self._mq=queue.Queue()
        self._dl_dir=os.path.join(os.path.expanduser("~"),"Downloads")
        self._dl_queue=[]; self._history=[]; self._ffmpeg_ok=bool(get_ffmpeg())
        self._fmt_radio_btns=[]
        self._quality_idx=ctk.IntVar(value=2); self._raw_fmt_var=ctk.StringVar(value="")
        self._sub_var=ctk.BooleanVar(value=False); self._speed_var=ctk.StringVar(value="")
        self._tmpl_var=ctk.StringVar(value="%(title)s [%(id)s].%(ext)s")
        self._pl_tmpl_var=ctk.StringVar(value="%(playlist_title)s/%(playlist_index)s - %(title)s [%(id)s].%(ext)s")
        self._embed_thumb=ctk.BooleanVar(value=True); self._embed_meta=ctk.BooleanVar(value=True)
        self._build_ui(); self._poll()
        self._log("ffmpeg найден — полный функционал" if self._ffmpeg_ok else
                  "ffmpeg не найден — видео скачается без склейки дорожек. Установи ffmpeg для лучшего качества.",
                  OK if self._ffmpeg_ok else WARN_C)

    def _build_ui(self):
        self.grid_columnconfigure(0,weight=1); self.grid_rowconfigure(1,weight=1)
        self._build_header()
        nb=ctk.CTkTabview(self,fg_color=BG,corner_radius=0,
            segmented_button_fg_color=CARD2,segmented_button_selected_color=PRI,
            segmented_button_selected_hover_color=PRI_H,
            segmented_button_unselected_color=CARD2,segmented_button_unselected_hover_color=BORDER,
            text_color=TEXT2,text_color_disabled=TEXT3)
        nb.grid(row=1,column=0,sticky="nsew")
        T=["    Скачать    ","    Очередь    ","    История    ","    Настройки    "]
        for t in T: nb.add(t)
        self._build_dl_tab(nb.tab(T[0])); self._build_queue_tab(nb.tab(T[1]))
        self._build_history_tab(nb.tab(T[2])); self._build_settings_tab(nb.tab(T[3]))

    def _build_header(self):
        h=ctk.CTkFrame(self,fg_color=PRI,corner_radius=0,height=80)
        h.grid(row=0,column=0,sticky="ew"); h.grid_propagate(False); h.grid_columnconfigure(1,weight=1)
        # Logo image
        try:
            logo_path = resource_path("vidra_logo_48.png")
            pil_img = PilImage.open(logo_path).resize((52,52), PilImage.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(52,52))
            logo_lbl = ctk.CTkLabel(h, image=ctk_img, text="", fg_color="transparent")
            logo_lbl.grid(row=0,column=0,padx=(18,12),pady=14)
        except Exception:
            icon=ctk.CTkFrame(h,fg_color="#1348A0",corner_radius=12,width=52,height=52)
            icon.grid(row=0,column=0,padx=(18,12),pady=14); icon.grid_propagate(False)
            ctk.CTkLabel(icon,text="↓",font=("Georgia",26,"bold"),text_color="white").place(relx=.5,rely=.5,anchor="center")
        tf=ctk.CTkFrame(h,fg_color="transparent"); tf.grid(row=0,column=1,sticky="w")
        ctk.CTkLabel(tf,text="Vidra",font=("Palatino Linotype",26,"bold"),text_color="white").grid(row=0,column=0,sticky="w")
        ctk.CTkLabel(tf,text="Видеозагрузчик  •  1000+ сайтов",font=("Trebuchet MS",11),text_color="#A8C8F8").grid(row=1,column=0,sticky="w")


    def _build_dl_tab(self,tab):
        tab.grid_columnconfigure(0,weight=58); tab.grid_columnconfigure(1,weight=36); tab.grid_rowconfigure(0,weight=1)
        left=ctk.CTkFrame(tab,fg_color="transparent"); left.grid(row=0,column=0,sticky="nsew",padx=(14,6),pady=8)
        left.grid_rowconfigure(2,weight=1); left.grid_columnconfigure(0,weight=1)
        right=ctk.CTkFrame(tab,fg_color="transparent"); right.grid(row=0,column=1,sticky="nsew",padx=(6,14),pady=8)
        right.grid_rowconfigure(0,weight=1); right.grid_columnconfigure(0,weight=1)
        self._build_url_card(left); self._build_pl_panel(left); self._build_fmt_card(left)
        self._build_log_card(right); self._build_footer_card(right)

    def _build_url_card(self,parent):
        card=StyledCard(parent); card.grid(row=0,column=0,sticky="ew",pady=(0,10)); card.grid_columnconfigure(0,weight=1)
        top=ctk.CTkFrame(card,fg_color="transparent"); top.grid(row=0,column=0,sticky="ew",padx=16,pady=(16,8)); top.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(top,text="Ссылка на видео или плейлист",font=("Trebuchet MS",12,"bold"),text_color=TEXT).grid(row=0,column=0,sticky="w")
        ctk.CTkLabel(top,text="YouTube  •  RuTube  •  TikTok  •  Vimeo  •  VK  •  и 1000+ других",font=("Trebuchet MS",10),text_color=TEXT3).grid(row=1,column=0,sticky="w")
        self._url_var=ctk.StringVar()
        self._url_entry=ctk.CTkEntry(card,textvariable=self._url_var,placeholder_text="https://...",
            font=("Trebuchet MS",13),height=46,fg_color=CARD2,border_color=BORDER,
            text_color=TEXT,placeholder_text_color=TEXT3,corner_radius=12)
        self._url_entry.grid(row=1,column=0,padx=16,pady=(0,8),sticky="ew")
        self._url_entry.bind("<Return>",lambda _:self._do_fetch())
        br=ctk.CTkFrame(card,fg_color="transparent"); br.grid(row=2,column=0,padx=16,pady=(0,8),sticky="ew"); br.grid_columnconfigure(2,weight=1)
        ctk.CTkButton(br,text="Вставить",width=84,height=32,fg_color=CARD2,hover_color=BORDER,text_color=TEXT2,corner_radius=8,font=("Trebuchet MS",11),command=self._paste).grid(row=0,column=0,padx=(0,6))
        ctk.CTkButton(br,text="✕",width=34,height=32,fg_color=CARD2,hover_color=BORDER,text_color=TEXT3,corner_radius=8,font=("Trebuchet MS",11),command=lambda:self._url_var.set("")).grid(row=0,column=1,padx=(0,10))
        ctk.CTkCheckBox(br,text="Субтитры",variable=self._sub_var,font=("Trebuchet MS",11),text_color=TEXT2,fg_color=TEAL,hover_color=TEAL_H,checkbox_width=18,checkbox_height=18).grid(row=0,column=2,sticky="w",padx=(0,10))
        self._fetch_btn=ctk.CTkButton(br,text="🔍  Найти форматы",height=38,fg_color=PRI,hover_color=PRI_H,text_color="white",corner_radius=10,font=("Trebuchet MS",13,"bold"),command=self._do_fetch)
        self._fetch_btn.grid(row=0,column=3,sticky="e")
        self._info_lbl=ctk.CTkLabel(card,text="",font=("Trebuchet MS",11),text_color=TEXT2,wraplength=540,justify="left",anchor="w")
        self._info_lbl.grid(row=3,column=0,padx=16,pady=(0,12),sticky="w")

    def _build_pl_panel(self,parent):
        self._pl_card=StyledCard(parent,fg_color=TEAL_L,border_color="#B0DDD6")
        self._pl_card.grid_columnconfigure(0,weight=1)
        ph=ctk.CTkFrame(self._pl_card,fg_color="transparent"); ph.grid(row=0,column=0,sticky="ew",padx=14,pady=(10,6)); ph.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(ph,text="Плейлист",font=("Trebuchet MS",12,"bold"),text_color=TEAL).grid(row=0,column=0,sticky="w")
        self._pl_pill=ctk.CTkLabel(ph,text="0 видео",font=("Trebuchet MS",10),text_color=TEAL,fg_color="#C8EDE9",corner_radius=99)
        self._pl_pill.grid(row=0,column=1,ipadx=8,ipady=2)
        self._pl_scroll=ctk.CTkScrollableFrame(self._pl_card,fg_color="transparent",corner_radius=8,height=105)
        self._pl_scroll.grid(row=1,column=0,sticky="ew",padx=10,pady=(0,10)); self._pl_scroll.grid_columnconfigure(0,weight=1)

    def _build_fmt_card(self,parent):
        card=StyledCard(parent); card.grid(row=2,column=0,sticky="nsew"); card.grid_rowconfigure(1,weight=1); card.grid_columnconfigure(0,weight=1)
        fh=ctk.CTkFrame(card,fg_color="transparent"); fh.grid(row=0,column=0,sticky="ew",padx=16,pady=(14,6)); fh.grid_columnconfigure(0,weight=1)
        self._fmt_title_lbl=ctk.CTkLabel(fh,text="Качество",font=("Palatino Linotype",13,"bold"),text_color=TEXT); self._fmt_title_lbl.grid(row=0,column=0,sticky="w")
        self._fmt_cnt_lbl=ctk.CTkLabel(fh,text="",font=("Trebuchet MS",10),text_color=TEXT3); self._fmt_cnt_lbl.grid(row=0,column=1)
        self._fmt_scroll=ctk.CTkScrollableFrame(card,fg_color=CARD2,corner_radius=10)
        self._fmt_scroll.grid(row=1,column=0,sticky="nsew",padx=12,pady=(0,12)); self._fmt_scroll.grid_columnconfigure(0,weight=1)
        self._fmt_ph=ctk.CTkLabel(self._fmt_scroll,text="Введи ссылку и нажми «Найти форматы» ↑",font=("Trebuchet MS",12),text_color=TEXT3)
        self._fmt_ph.grid(row=0,column=0,pady=50)

    def _build_log_card(self,parent):
        card=StyledCard(parent); card.grid(row=0,column=0,sticky="nsew",pady=(0,10)); card.grid_rowconfigure(1,weight=1); card.grid_columnconfigure(0,weight=1)
        lh=ctk.CTkFrame(card,fg_color="transparent"); lh.grid(row=0,column=0,sticky="ew",padx=14,pady=(12,4)); lh.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(lh,text="Журнал",font=("Palatino Linotype",13,"bold"),text_color=TEXT).grid(row=0,column=0,sticky="w")
        ctk.CTkButton(lh,text="Очистить",width=64,height=24,fg_color=CARD2,hover_color=BORDER,text_color=TEXT3,corner_radius=6,font=("Trebuchet MS",10),command=self._clear_log).grid(row=0,column=1)
        self._log_box=ctk.CTkTextbox(card,fg_color=CARD2,corner_radius=10,font=("Consolas",10),text_color=TEXT,wrap="word",state="disabled")
        self._log_box.grid(row=1,column=0,sticky="nsew",padx=12,pady=(0,12))

    def _build_footer_card(self,parent):
        card=StyledCard(parent,fg_color=CARD); card.grid(row=1,column=0,sticky="ew"); card.grid_columnconfigure(0,weight=1)
        fr=ctk.CTkFrame(card,fg_color="transparent"); fr.grid(row=0,column=0,sticky="ew",padx=14,pady=(12,8)); fr.grid_columnconfigure(1,weight=1)
        ctk.CTkLabel(fr,text="Папка:",font=("Trebuchet MS",11,"bold"),text_color=TEXT2).grid(row=0,column=0,padx=(0,8))
        self._folder_lbl=ctk.CTkLabel(fr,text=self._dl_dir,font=("Trebuchet MS",10),text_color=TEXT2,anchor="w",wraplength=230); self._folder_lbl.grid(row=0,column=1,sticky="ew")
        ctk.CTkButton(fr,text="...",width=32,height=26,fg_color=CARD2,hover_color=BORDER,text_color=TEXT2,corner_radius=7,font=("Trebuchet MS",11),command=self._choose_folder).grid(row=0,column=2)
        pgf=ctk.CTkFrame(card,fg_color="transparent"); pgf.grid(row=1,column=0,sticky="ew",padx=14,pady=(0,4)); pgf.grid_columnconfigure(0,weight=1)
        self._prog=ctk.CTkProgressBar(pgf,fg_color=CARD2,progress_color=PRI,corner_radius=99,height=12); self._prog.set(0); self._prog.grid(row=0,column=0,sticky="ew",padx=(0,8))
        self._pct_lbl=ctk.CTkLabel(pgf,text="",width=42,font=("Trebuchet MS",10,"bold"),text_color=PRI,anchor="e"); self._pct_lbl.grid(row=0,column=1)
        sf=ctk.CTkFrame(card,fg_color="transparent"); sf.grid(row=2,column=0,sticky="w",padx=14,pady=(2,8))
        self._status_dot=ctk.CTkLabel(sf,text="●",font=("Arial",12),text_color=TEXT3); self._status_dot.grid(row=0,column=0,padx=(0,5))
        self._status_lbl=ctk.CTkLabel(sf,text="Готов к работе",font=("Trebuchet MS",11),text_color=TEXT2,anchor="w"); self._status_lbl.grid(row=0,column=1)
        br=ctk.CTkFrame(card,fg_color="transparent"); br.grid(row=3,column=0,padx=14,pady=(0,14),sticky="ew"); br.grid_columnconfigure(0,weight=1)
        self._add_q_btn=ctk.CTkButton(br,text="+ В очередь",width=110,height=40,fg_color=PLUM_L,hover_color="#DDD5F5",text_color=PLUM,corner_radius=10,font=("Trebuchet MS",12,"bold"),command=self._add_to_queue,state="disabled")
        self._add_q_btn.grid(row=0,column=0,sticky="w",padx=(0,10))
        self._dl_btn=ctk.CTkButton(br,text="⬇   Скачать",height=44,fg_color=OK,hover_color=OK_H,text_color="white",corner_radius=10,font=("Trebuchet MS",14,"bold"),command=self._do_download,state="disabled")
        self._dl_btn.grid(row=0,column=1,sticky="e")

    def _build_queue_tab(self,tab):
        tab.grid_columnconfigure(0,weight=1); tab.grid_rowconfigure(1,weight=1)
        hdr=ctk.CTkFrame(tab,fg_color="transparent"); hdr.grid(row=0,column=0,sticky="ew",padx=14,pady=(12,8)); hdr.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(hdr,text="Очередь загрузок",font=("Palatino Linotype",16,"bold"),text_color=TEXT).grid(row=0,column=0,sticky="w")
        ctk.CTkButton(hdr,text="▶  Запустить всё",height=38,fg_color=PRI,hover_color=PRI_H,text_color="white",corner_radius=10,font=("Trebuchet MS",12,"bold"),command=self._run_queue).grid(row=0,column=1,padx=(0,8))
        ctk.CTkButton(hdr,text="Очистить",height=38,fg_color=CARD2,hover_color=BORDER,text_color=TEXT2,corner_radius=10,font=("Trebuchet MS",11),command=self._clear_queue).grid(row=0,column=2)
        self._queue_scroll=ctk.CTkScrollableFrame(tab,fg_color=PANEL,corner_radius=16,border_width=1,border_color=BORDER)
        self._queue_scroll.grid(row=1,column=0,sticky="nsew",padx=14,pady=(0,12)); self._queue_scroll.grid_columnconfigure(0,weight=1)
        self._queue_ph=ctk.CTkLabel(self._queue_scroll,text="Очередь пуста\nДобавляй видео или плейлисты кнопкой «+ В очередь»",font=("Trebuchet MS",12),text_color=TEXT3,justify="center")
        self._queue_ph.grid(row=0,column=0,pady=60)

    def _build_history_tab(self,tab):
        tab.grid_columnconfigure(0,weight=1); tab.grid_rowconfigure(1,weight=1)
        hdr=ctk.CTkFrame(tab,fg_color="transparent"); hdr.grid(row=0,column=0,sticky="ew",padx=14,pady=(12,8)); hdr.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(hdr,text="История загрузок",font=("Palatino Linotype",16,"bold"),text_color=TEXT).grid(row=0,column=0,sticky="w")
        ctk.CTkButton(hdr,text="Очистить",height=34,fg_color=CARD2,hover_color=BORDER,text_color=TEXT2,corner_radius=9,font=("Trebuchet MS",11),command=self._clear_history).grid(row=0,column=1)
        self._hist_scroll=ctk.CTkScrollableFrame(tab,fg_color=PANEL,corner_radius=16,border_width=1,border_color=BORDER)
        self._hist_scroll.grid(row=1,column=0,sticky="nsew",padx=14,pady=(0,12)); self._hist_scroll.grid_columnconfigure(0,weight=1)
        self._hist_ph=ctk.CTkLabel(self._hist_scroll,text="История пуста — скачай что-нибудь!",font=("Trebuchet MS",12),text_color=TEXT3)
        self._hist_ph.grid(row=0,column=0,pady=60)

    def _build_settings_tab(self,tab):
        tab.grid_columnconfigure(0,weight=1); tab.grid_rowconfigure(0,weight=1)
        sc=ctk.CTkScrollableFrame(tab,fg_color="transparent"); sc.grid(row=0,column=0,sticky="nsew",padx=14,pady=8); sc.grid_columnconfigure(0,weight=1)
        def sec(title):
            f=StyledCard(sc); f.pack(fill="x",pady=(0,10),padx=2)
            ctk.CTkLabel(f,text=title,font=("Palatino Linotype",13,"bold"),text_color=TEXT).grid(row=0,column=0,padx=16,pady=(14,8),sticky="w",columnspan=4)
            f.grid_columnconfigure(1,weight=1); return f
        ff=sec("🎬  FFmpeg")
        ctk.CTkLabel(ff,text="Статус:",font=("Trebuchet MS",11),text_color=TEXT2).grid(row=1,column=0,padx=16,pady=(0,6),sticky="w")
        ctk.CTkLabel(ff,text=get_ffmpeg() or "Не найден",font=("Consolas",10),text_color=OK if self._ffmpeg_ok else ERR,anchor="w").grid(row=1,column=1,padx=4,pady=(0,6),sticky="ew")
        ctk.CTkButton(ff,text="Скачать ffmpeg",width=130,height=30,fg_color=TEAL,hover_color=TEAL_H,text_color="white",corner_radius=8,font=("Trebuchet MS",11),command=lambda:self._open_url("https://ffmpeg.org/download.html")).grid(row=1,column=2,padx=16,pady=(0,6))
        ctk.CTkLabel(ff,text="Полный функционал доступен!" if self._ffmpeg_ok else "Без ffmpeg: видео скачается, но без склейки и тегов. Установи ffmpeg + добавь в PATH.",font=("Trebuchet MS",10),text_color=OK if self._ffmpeg_ok else WARN_C,justify="left").grid(row=2,column=0,columnspan=3,padx=16,pady=(0,14),sticky="w")
        out=sec("📄  Шаблон имени — одиночное видео")
        ctk.CTkLabel(out,text="Шаблон:",font=("Trebuchet MS",11),text_color=TEXT2).grid(row=1,column=0,padx=16,pady=(0,6),sticky="w")
        ctk.CTkEntry(out,textvariable=self._tmpl_var,font=("Consolas",11),height=34,fg_color=CARD2,border_color=BORDER,text_color=TEXT,corner_radius=8).grid(row=1,column=1,padx=4,pady=(0,6),sticky="ew",columnspan=2)
        ctk.CTkLabel(out,text="%(title)s  %(id)s  %(ext)s  %(uploader)s  %(upload_date)s",font=("Trebuchet MS",10),text_color=TEXT3,anchor="w").grid(row=2,column=0,columnspan=3,padx=16,pady=(0,12),sticky="w")
        pl_s=sec("📁  Шаблон имени — плейлист")
        ctk.CTkLabel(pl_s,text="Шаблон:",font=("Trebuchet MS",11),text_color=TEXT2).grid(row=1,column=0,padx=16,pady=(0,6),sticky="w")
        ctk.CTkEntry(pl_s,textvariable=self._pl_tmpl_var,font=("Consolas",11),height=34,fg_color=CARD2,border_color=BORDER,text_color=TEXT,corner_radius=8).grid(row=1,column=1,padx=4,pady=(0,6),sticky="ew",columnspan=2)
        ctk.CTkLabel(pl_s,text="%(playlist_title)s  %(playlist_index)s  %(title)s  %(id)s",font=("Trebuchet MS",10),text_color=TEXT3,anchor="w").grid(row=2,column=0,columnspan=3,padx=16,pady=(0,12),sticky="w")
        sp=sec("⚡  Лимит скорости")
        ctk.CTkLabel(sp,text="Скорость:",font=("Trebuchet MS",11),text_color=TEXT2).grid(row=1,column=0,padx=16,pady=(0,12),sticky="w")
        ctk.CTkEntry(sp,textvariable=self._speed_var,placeholder_text="напр. 5M  или  500K  — пусто = без лимита",font=("Trebuchet MS",11),height=34,fg_color=CARD2,border_color=BORDER,text_color=TEXT,corner_radius=8).grid(row=1,column=1,padx=4,pady=(0,12),sticky="ew",columnspan=2)
        emb=sec("🏷  Метаданные (требует ffmpeg)")
        ctk.CTkCheckBox(emb,text="Встроить обложку",variable=self._embed_thumb,font=("Trebuchet MS",11),text_color=TEXT2,fg_color=PRI,hover_color=PRI_H,checkbox_width=18,checkbox_height=18).grid(row=1,column=0,padx=16,pady=(0,6),sticky="w")
        ctk.CTkCheckBox(emb,text="Встроить метаданные (название, автор, дата)",variable=self._embed_meta,font=("Trebuchet MS",11),text_color=TEXT2,fg_color=PRI,hover_color=PRI_H,checkbox_width=18,checkbox_height=18).grid(row=2,column=0,padx=16,pady=(0,14),sticky="w")
        abt=sec("ℹ  О программе")
        ctk.CTkLabel(abt,text="Vidra  •  powered by Sheri\nОснован на yt-dlp",font=("Trebuchet MS",11),text_color=TEXT2,justify="left",anchor="w").grid(row=1,column=0,padx=16,pady=(0,8),sticky="w")
        bf=ctk.CTkFrame(abt,fg_color="transparent"); bf.grid(row=2,column=0,padx=16,pady=(0,14),sticky="w")
        ctk.CTkButton(bf,text="GitHub yt-dlp",width=120,height=30,fg_color=TEAL,hover_color=TEAL_H,text_color="white",corner_radius=8,font=("Trebuchet MS",11),command=lambda:self._open_url("https://github.com/yt-dlp/yt-dlp")).pack(side="left",padx=(0,8))
        ctk.CTkButton(bf,text="Список сайтов",width=120,height=30,fg_color=PLUM,hover_color=PLUM_H,text_color="white",corner_radius=8,font=("Trebuchet MS",11),command=lambda:self._open_url("https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md")).pack(side="left")

    # Helpers
    def _paste(self):
        try: self._url_var.set(self.clipboard_get())
        except: pass
    def _choose_folder(self):
        d=filedialog.askdirectory(initialdir=self._dl_dir)
        if d: self._dl_dir=d; self._folder_lbl.configure(text=d)
    def _open_url(self,url):
        import webbrowser; webbrowser.open(url)
    def _log(self,msg,color=None): self._mq.put(("log",msg,color))
    def _set_status(self,msg,c=TEXT3): self._mq.put(("status",msg,c))
    def _set_prog(self,v): self._mq.put(("prog",v,None))

    def _poll(self):
        try:
            while True:
                k,a,b=self._mq.get_nowait()
                if k=="log": self._write_log(a,b)
                elif k=="status": self._status_lbl.configure(text=a,text_color=b or TEXT2); self._status_dot.configure(text_color=b or TEXT3)
                elif k=="prog": self._prog.set(a); self._pct_lbl.configure(text=f"{int(a*100)}%" if a>0 else "")
                elif k=="fetch_done": self._on_fetch_done(a)
                elif k=="dl_done": self._on_dl_done(a)
                elif k=="q_refresh": self._refresh_queue()
                elif k=="h_refresh": self._refresh_history()
        except queue.Empty: pass
        self.after(80,self._poll)

    def _write_log(self,msg,color=None):
        self._log_box.configure(state="normal")
        self._log_box.insert("end",f"[{ts()}] {msg}\n")
        self._log_box.see("end"); self._log_box.configure(state="disabled")
    def _clear_log(self):
        self._log_box.configure(state="normal"); self._log_box.delete("1.0","end"); self._log_box.configure(state="disabled")

    # Fetch
    def _do_fetch(self):
        url=self._url_var.get().strip()
        if not url: messagebox.showwarning("Ой","Вставь ссылку!"); return
        if self._fetch_thread and self._fetch_thread.is_alive(): return
        self._fetch_btn.configure(state="disabled",text="Проверяю...")
        self._dl_btn.configure(state="disabled"); self._add_q_btn.configure(state="disabled")
        self._clear_fmt_list(); self._fmt_ph.configure(text="Определяю тип ссылки..."); self._fmt_ph.grid()
        self._hide_pl(); self._info_lbl.configure(text="")
        self._log(f"Запрос: {url[:80]}"); self._set_status("Получаю информацию...",TEXT3)
        def worker():
            try:
                r=_run_hidden([get_ytdlp(),"--flat-playlist","--dump-single-json",url],capture_output=True,text=True,timeout=45,encoding="utf-8",errors="replace")
                if r.returncode!=0:
                    lines=(r.stderr or "").strip().splitlines(); raise RuntimeError(lines[-1] if lines else "yt-dlp error")
                info=json.loads(r.stdout)
                is_pl=info.get("_type") in ("playlist","multi_video") or "entries" in info
                if is_pl:
                    entries=info.get("entries") or []
                    self._mq.put(("fetch_done",{"type":"playlist","title":info.get("title") or "Плейлист",
                        "uploader":info.get("uploader") or info.get("channel",""),
                        "count":len(entries),"url":url,
                        "entries":[{"idx":e.get("playlist_index") or (i+1),"title":e.get("title","Видео "+str(i+1)),"id":e.get("id",""),"url":e.get("url") or e.get("webpage_url","")} for i,e in enumerate(entries) if e]},None))
                else:
                    r2=_run_hidden([get_ytdlp(),"--dump-json","--no-playlist",url],capture_output=True,text=True,timeout=45,encoding="utf-8",errors="replace")
                    if r2.returncode!=0:
                        lines=(r2.stderr or "").strip().splitlines(); raise RuntimeError(lines[-1] if lines else "yt-dlp error")
                    full=json.loads(r2.stdout)
                    self._mq.put(("fetch_done",{"type":"single","info":full,"raw_formats":parse_raw_formats(full)},None))
            except Exception as e: self._mq.put(("fetch_done",{"type":"error","msg":str(e)},None))
        self._fetch_thread=threading.Thread(target=worker,daemon=True); self._fetch_thread.start()

    def _on_fetch_done(self,p):
        self._fetch_btn.configure(state="normal",text="🔍  Найти форматы")
        if p["type"]=="error":
            self._log(f"ОШИБКА: {p['msg']}",ERR); self._set_status(f"Ошибка: {p['msg']}",ERR)
            self._fmt_ph.configure(text="Не удалось получить информацию"); return
        if p["type"]=="playlist":
            self._is_playlist=True; self._info=p
            self._info_lbl.configure(text=f"ПЛЕЙЛИСТ  •  {p['title'][:60]}  •  {p['count']} видео  •  {p['uploader'][:28]}")
            self._log(f"Плейлист «{p['title'][:55]}» — {p['count']} видео"); self._set_status(f"Плейлист: {p['count']} видео. Выбери качество.",OK)
            self._show_pl(p["entries"]); self._populate_presets_only()
        else:
            self._is_playlist=False; fi=p["info"]; self._info=fi; self._raw_formats=p["raw_formats"]
            self._info_lbl.configure(text=f"{fi.get('title','?')[:68]}   {fmt_dur(fi.get('duration'))}   {(fi.get('uploader') or fi.get('channel',''))[:28]}")
            self._log(f"Видео «{fi.get('title','?')[:55]}» — {len(self._raw_formats)} форматов"); self._set_status("Выбери формат и нажми «Скачать»",OK)
            self._populate_all_formats()
        self._dl_btn.configure(state="normal"); self._add_q_btn.configure(state="normal")

    def _clear_fmt_list(self):
        for w in self._fmt_scroll.winfo_children():
            if w!=self._fmt_ph: w.destroy()
        self._fmt_radio_btns=[]; self._raw_fmt_var.set("")

    def _add_preset_row(self,row,idx,preset):
        f=ctk.CTkFrame(self._fmt_scroll,fg_color="transparent"); f.grid(row=row,column=0,padx=8,pady=2,sticky="ew"); f.grid_columnconfigure(1,weight=1)
        btn=ctk.CTkRadioButton(f,text=preset["label"],variable=self._quality_idx,value=idx,
            font=("Trebuchet MS",12,"bold"),text_color=TEXT,fg_color=PRI,hover_color=PRI_H,border_color=BORDER,command=self._on_q_pick)
        btn.grid(row=0,column=0,sticky="w")
        ctk.CTkLabel(f,text=preset["sub"],font=("Trebuchet MS",10),text_color=TEXT3).grid(row=0,column=1,padx=(6,0),sticky="w")
        self._fmt_radio_btns.append(btn)

    def _populate_presets_only(self):
        self._fmt_ph.grid_remove(); self._clear_fmt_list()
        self._fmt_title_lbl.configure(text="Максимальное качество"); self._fmt_cnt_lbl.configure(text="")
        ctk.CTkLabel(self._fmt_scroll,text="Каждое видео скачается в лучшем доступном\nкачестве до выбранного максимума:",font=("Trebuchet MS",11),text_color=TEXT2,justify="left").grid(row=0,column=0,padx=10,pady=(6,10),sticky="w")
        for i,p in enumerate(QUALITY_PRESETS): self._add_preset_row(i+1,i,p)
        self._quality_idx.set(2)

    def _populate_all_formats(self):
        self._fmt_ph.grid_remove(); self._clear_fmt_list()
        self._fmt_title_lbl.configure(text="Качество"); self._fmt_cnt_lbl.configure(text=f"{len(QUALITY_PRESETS)+len(self._raw_formats)} форматов")
        ctk.CTkLabel(self._fmt_scroll,text="— Умные пресеты —",font=("Trebuchet MS",10),text_color=TEXT3).grid(row=0,column=0,padx=8,pady=(8,2),sticky="w")
        for i,p in enumerate(QUALITY_PRESETS): self._add_preset_row(i+1,i,p)
        if self._raw_formats:
            ctk.CTkLabel(self._fmt_scroll,text="— Конкретные форматы с сайта —",font=("Trebuchet MS",10),text_color=TEXT3).grid(row=len(QUALITY_PRESETS)+1,column=0,padx=8,pady=(8,2),sticky="w")
            for j,fmt in enumerate(self._raw_formats):
                btn=ctk.CTkRadioButton(self._fmt_scroll,text=fmt["label"],variable=self._raw_fmt_var,value=fmt["id"],
                    font=("Trebuchet MS",11),text_color=TEXT2,fg_color=PRI,hover_color=PRI_H,border_color=BORDER,command=self._on_raw_pick)
                btn.grid(row=len(QUALITY_PRESETS)+2+j,column=0,padx=10,pady=2,sticky="w"); self._fmt_radio_btns.append(btn)
        self._quality_idx.set(2)

    def _on_q_pick(self): self._raw_fmt_var.set(""); self._dl_btn.configure(state="normal"); self._add_q_btn.configure(state="normal")
    def _on_raw_pick(self): self._quality_idx.set(-1); self._dl_btn.configure(state="normal"); self._add_q_btn.configure(state="normal")
    def _get_fmt(self):
        raw=self._raw_fmt_var.get()
        if raw: return raw
        idx=self._quality_idx.get()
        return QUALITY_PRESETS[idx]["fmt"] if 0<=idx<len(QUALITY_PRESETS) else "bestvideo+bestaudio/best"

    def _show_pl(self,entries):
        self._pl_card.grid(row=1,column=0,sticky="ew",pady=(0,10),in_=self._pl_card.master)
        self._pl_pill.configure(text=f"{len(entries)} видео")
        for w in self._pl_scroll.winfo_children(): w.destroy()
        for i,e in enumerate(entries[:60]):
            row=ctk.CTkFrame(self._pl_scroll,fg_color="transparent"); row.grid(row=i,column=0,sticky="ew",pady=1); row.grid_columnconfigure(1,weight=1)
            ctk.CTkLabel(row,text=f"{e['idx']:>3}.",font=("Consolas",10),text_color=TEXT3,width=32).grid(row=0,column=0,padx=(4,6))
            ctk.CTkLabel(row,text=e["title"][:72],font=("Trebuchet MS",10),text_color=TEXT,anchor="w").grid(row=0,column=1,sticky="w")
        if len(entries)>60: ctk.CTkLabel(self._pl_scroll,text=f"... и ещё {len(entries)-60} видео",font=("Trebuchet MS",10),text_color=TEXT3).grid(row=60,column=0,pady=4)
    def _hide_pl(self):
        try: self._pl_card.grid_remove()
        except: pass

    # Download
    def _build_cmd(self,url,fmt,is_pl=False):
        ff=get_ffmpeg(); audio_only=fmt=="bestaudio/best"
        tmpl=os.path.join(self._dl_dir,self._pl_tmpl_var.get() if is_pl else self._tmpl_var.get())
        pl_flag=["--yes-playlist"] if is_pl else ["--no-playlist"]
        cmd=[get_ytdlp(),"-f",fmt,"--progress","--newline","-o",tmpl]+pl_flag
        if audio_only:
            cmd+=["--extract-audio","--audio-format","mp3","--audio-quality","0"]
            if ff: cmd+=["--ffmpeg-location",ff]
        else:
            if ff:
                cmd+=["--merge-output-format","mp4","--ffmpeg-location",ff]
                if self._embed_thumb.get(): cmd+=["--embed-thumbnail"]
                if self._embed_meta.get():  cmd+=["--add-metadata"]
        if self._sub_var.get(): cmd+=["--write-sub","--write-auto-sub","--sub-langs","ru,en"]
        lim=self._speed_var.get().strip()
        if lim: cmd+=["--limit-rate",lim]
        cmd.append(url); return cmd

    def _do_download(self):
        url=self._url_var.get().strip()
        if not url: return
        if self._dl_thread and self._dl_thread.is_alive(): messagebox.showinfo("Занято","Подожди окончания!"); return
        fmt=self._get_fmt(); is_pl=self._is_playlist; title=self._info.get("title","?")
        self._dl_btn.configure(state="disabled",text="Скачиваю..."); self._prog.set(0); self._pct_lbl.configure(text="0%")
        self._log(f"Начинаю: {'[PL]' if is_pl else '[V]'} {title[:50]}  |  {fmt}")
        cmd=self._build_cmd(url,fmt,is_pl)
        def worker():
            if is_pl: ok,path,warn=self._run_playlist(cmd,self._info.get("count",1))
            else: ok,path,warn=self._run_single(cmd)
            if ok: self._history.append({"title":title,"url":url,"path":path,"is_pl":is_pl,"ts":datetime.now().strftime("%d.%m.%Y %H:%M")})
            self._mq.put(("dl_done",(ok,path,warn),None))
        self._dl_thread=threading.Thread(target=worker,daemon=True); self._dl_thread.start()

    def _run_single(self,cmd):
        pct_re=re.compile(r"\[download\]\s+([\d.]+)%"); dest_re=re.compile(r"Destination:\s*(.+)"); merge_re=re.compile(r'Merging formats into ["\'](.+)["\']')
        last_path=""; ffmpeg_warn=False
        try:
            proc=_popen_hidden(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace")
            for line in proc.stdout:
                line=line.rstrip(); m=pct_re.search(line)
                if m: self._set_prog(float(m.group(1))/100); self._set_status(f"Скачиваю... {m.group(1)}%",INFO_C); continue
                dm=dest_re.search(line)
                if dm: last_path=dm.group(1).strip()
                mm=merge_re.search(line)
                if mm: last_path=mm.group(1).strip()
                lo=line.lower()
                if "ffmpeg not found" in lo or ("postprocessing" in lo and "error" in lo): ffmpeg_warn=True; self._log(f"WARN: {line}",WARN_C); continue
                if line and "[download]  " not in line: self._log(line)
            proc.wait()
            if last_path and os.path.isfile(last_path): return True,last_path,ffmpeg_warn
            if proc.returncode==0: return True,last_path,ffmpeg_warn
            if ffmpeg_warn: return True,last_path,True
            return False,"",False
        except FileNotFoundError: self._log("yt-dlp не найден!",ERR); return False,"",False
        except Exception as e: self._log(f"Ошибка: {e}",ERR); return False,"",False

    def _run_playlist(self,cmd,total):
        pct_re=re.compile(r"\[download\]\s+([\d.]+)%"); vidnum_re=re.compile(r"\[download\] Downloading (?:item|video) (\d+) of (\d+)")
        dest_re=re.compile(r"Destination:\s*(.+)"); merge_re=re.compile(r'Merging formats into ["\'](.+)["\']')
        current=0; last_path=""; ffmpeg_warn=False
        try:
            proc=_popen_hidden(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace")
            for line in proc.stdout:
                line=line.rstrip(); m2=vidnum_re.search(line)
                if m2:
                    current=int(m2.group(1)); tot=int(m2.group(2))
                    self._set_status(f"Видео {current} из {tot}...",INFO_C); self._set_prog((current-1)/max(tot,1)); self._log(f"▶ Видео {current}/{tot}"); continue
                m=pct_re.search(line)
                if m:
                    pct=float(m.group(1))/100; overall=(max(current-1,0)+pct)/max(total,1)
                    self._set_prog(min(overall,1.0)); self._set_status(f"Видео {current}/{total}  —  {m.group(1)}%",INFO_C); continue
                dm=dest_re.search(line)
                if dm: last_path=dm.group(1).strip()
                mm=merge_re.search(line)
                if mm: last_path=mm.group(1).strip()
                lo=line.lower()
                if "ffmpeg not found" in lo or ("postprocessing" in lo and "error" in lo): ffmpeg_warn=True; self._log(f"WARN: {line}",WARN_C); continue
                if line and "[download]  " not in line: self._log(line)
            proc.wait()
            folder=os.path.dirname(last_path) if last_path else self._dl_dir
            if proc.returncode==0 or ffmpeg_warn: return True,folder,ffmpeg_warn
            return False,"",False
        except FileNotFoundError: self._log("yt-dlp не найден!",ERR); return False,"",False
        except Exception as e: self._log(f"Ошибка: {e}",ERR); return False,"",False

    def _on_dl_done(self,payload):
        ok,path,warn=payload; self._dl_btn.configure(state="normal",text="⬇   Скачать")
        if ok:
            self._set_prog(1); self._pct_lbl.configure(text="100%")
            if warn: self._log("Готово! (без ffmpeg-обработки)",WARN_C); self._set_status("Готово — рекомендуется установить ffmpeg",WARN_C)
            else: self._log("Готово!",OK); self._set_status("Файл(ы) скачаны!",OK)
            self._refresh_history()
            folder=(os.path.dirname(path) if path and os.path.isfile(path) else path if path and os.path.isdir(path) else self._dl_dir)
            if messagebox.askyesno("Готово!","Скачивание завершено!\n\nОткрыть папку?"): self._reveal(folder)
        else: self._log("Загрузка не удалась — смотри журнал",ERR); self._set_status("Ошибка загрузки",ERR)

    def _reveal(self,path):
        if os.path.isfile(path): folder=os.path.dirname(path)
        else: folder=path
        if sys.platform=="win32":
            if os.path.isfile(path): subprocess.Popen(["explorer","/select,",path])
            else: subprocess.Popen(["explorer",folder])
        elif sys.platform=="darwin": subprocess.Popen(["open","-R",path])
        else: subprocess.Popen(["xdg-open",folder])

    # Queue
    def _add_to_queue(self):
        url=self._url_var.get().strip(); fmt=self._get_fmt()
        if not url or not fmt: return
        is_pl=self._is_playlist; title=self._info.get("title","?"); count=self._info.get("count",0) if is_pl else 0
        self._dl_queue.append(QueueItem(url,fmt,title,is_pl,count)); self._refresh_queue()
        self._log(f"+ Очередь: {'плейлист ('+str(count)+' видео)' if is_pl else 'видео'}  «{title[:40]}»")

    def _refresh_queue(self):
        for w in self._queue_scroll.winfo_children():
            if w!=self._queue_ph: w.destroy()
        if not self._dl_queue: self._queue_ph.grid(); return
        self._queue_ph.grid_remove()
        S={"waiting":(TEXT3,"[ ]"),"running":(INFO_C,">>>"),"done":(OK,"[OK]"),"fail":(ERR,"[!]")}
        for i,item in enumerate(self._dl_queue):
            col,icon=S.get(item.status,(TEXT3,"[ ]"))
            row=ctk.CTkFrame(self._queue_scroll,fg_color=CARD2,corner_radius=10); row.grid(row=i,column=0,sticky="ew",padx=6,pady=4); row.grid_columnconfigure(1,weight=1)
            ctk.CTkLabel(row,text=icon,font=("Consolas",12),text_color=col).grid(row=0,column=0,padx=(12,8),pady=10)
            ctk.CTkLabel(row,text=(f"[PL {item.count}v]  " if item.is_pl else "[V]  ")+item.title[:58],font=("Trebuchet MS",11),text_color=TEXT,anchor="w").grid(row=0,column=1,sticky="ew")
            ctk.CTkButton(row,text="✕",width=28,height=28,fg_color=ERR_L,hover_color="#FDDCD9",text_color=ERR,corner_radius=6,font=("Trebuchet MS",11),command=lambda idx=i:self._remove_q(idx)).grid(row=0,column=2,padx=10)

    def _remove_q(self,idx):
        if 0<=idx<len(self._dl_queue): self._dl_queue.pop(idx); self._refresh_queue()
    def _clear_queue(self): self._dl_queue.clear(); self._refresh_queue()

    def _run_queue(self):
        if not self._dl_queue: messagebox.showinfo("Пусто","Добавь видео!"); return
        if self._dl_thread and self._dl_thread.is_alive(): messagebox.showinfo("Занято","Дождись окончания"); return
        def worker():
            for item in self._dl_queue:
                if item.status=="done": continue
                item.status="running"; self._mq.put(("q_refresh",None,None))
                self._log(f"Очередь: {'[PL]' if item.is_pl else '[V]'} {item.title[:50]}",INFO_C)
                cmd=self._build_cmd(item.url,item.fmt,item.is_pl)
                if item.is_pl: ok,path,warn=self._run_playlist(cmd,item.count)
                else: ok,path,warn=self._run_single(cmd)
                item.status="done" if ok else "fail"
                if ok: self._history.append({"title":item.title,"url":item.url,"path":path,"is_pl":item.is_pl,"ts":datetime.now().strftime("%d.%m.%Y %H:%M")})
                self._mq.put(("log",f"{'OK' if ok else 'FAIL'}: {item.title[:50]}",OK if ok else ERR))
                self._mq.put(("q_refresh",None,None))
            self._mq.put(("status","Очередь завершена!",OK)); self._mq.put(("h_refresh",None,None))
        self._dl_thread=threading.Thread(target=worker,daemon=True); self._dl_thread.start()

    # History
    def _refresh_history(self):
        for w in self._hist_scroll.winfo_children():
            if w!=self._hist_ph: w.destroy()
        if not self._history: self._hist_ph.grid(); return
        self._hist_ph.grid_remove()
        for i,item in enumerate(reversed(self._history)):
            is_pl=item.get("is_pl",False)
            row=ctk.CTkFrame(self._hist_scroll,fg_color=CARD2,corner_radius=10); row.grid(row=i,column=0,sticky="ew",padx=6,pady=4); row.grid_columnconfigure(1,weight=1)
            ctk.CTkLabel(row,text="PL" if is_pl else "OK",font=("Trebuchet MS",10,"bold"),text_color=TEAL if is_pl else OK,fg_color=TEAL_L if is_pl else OK_L,corner_radius=6).grid(row=0,column=0,padx=(12,10),pady=12,ipadx=6,ipady=2)
            inf=ctk.CTkFrame(row,fg_color="transparent"); inf.grid(row=0,column=1,sticky="ew")
            ctk.CTkLabel(inf,text=item["title"][:68],font=("Trebuchet MS",11),text_color=TEXT,anchor="w").grid(row=0,column=0,sticky="w")
            ctk.CTkLabel(inf,text=item["ts"],font=("Trebuchet MS",9),text_color=TEXT3,anchor="w").grid(row=1,column=0,sticky="w")
            p=item.get("path",""); exists=bool(p) and (os.path.isfile(p) or os.path.isdir(p))
            ctk.CTkButton(row,text="Открыть" if exists else "Папка",width=78,height=30,fg_color=TEAL_L if exists else CARD2,hover_color="#B8E8E2" if exists else BORDER,text_color=TEAL if exists else TEXT2,corner_radius=8,font=("Trebuchet MS",10),command=lambda pp=p:self._reveal(pp or self._dl_dir)).grid(row=0,column=2,padx=10)

    def _clear_history(self): self._history.clear(); self._refresh_history()


if __name__=="__main__":
    App().mainloop()
