import tkinter as tk
from tkinter import ttk, messagebox
import requests
from bs4 import BeautifulSoup
import threading
import webbrowser
import urllib.parse
import re
import json
import os


class T:
    BG = "#080810"
    BG2 = "#0e0e1a"
    BG3 = "#141422"
    CARD = "#161628"
    CARD_H = "#1e1e35"
    INPUT = "#0c0c16"
    RED = "#e94560"
    RED2 = "#ff6b81"
    BLUE = "#0f3460"
    BLUE2 = "#533483"
    PURPLE = "#7c3aed"
    PURPLE2 = "#a78bfa"
    CYAN = "#06b6d4"
    CYAN2 = "#22d3ee"
    TXT = "#ffffff"
    TXT2 = "#b0b0c0"
    TXT3 = "#555570"
    BORDER = "#252545"
    BORDER2 = "#353560"
    GREEN = "#00e676"
    GREEN2 = "#00c853"
    ORANGE = "#ff9100"
    GOLD = "#ffd700"
    HEADER = "#06060c"
    PINK = "#ec4899"
    YELLOW = "#eab308"


SOURCES = {
    "oyunindir.vip": {
        "name": "OyunIndir VIP",
        "base": "https://www.oyunindir.vip",
        "icon": "🟣",
        "color": T.PURPLE,
    },
    "oyunindir.cafe": {
        "name": "OyunIndir Cafe",
        "base": "https://oyunindir.cafe",
        "icon": "🟠",
        "color": T.ORANGE,
    },
}

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
}


def fix_url(url, base):
    """Eksik URL'leri düzeltir"""
    if not url:
        return ""
    url = url.strip()
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return base.rstrip("/") + url
    return base.rstrip("/") + "/" + url


class Btn(tk.Frame):
    def __init__(self, parent, text="", icon="", cmd=None,
                 color=T.RED, hover=T.RED2, fs=11, pad_x=14, pad_y=5):
        try:
            pbg = parent.cget("bg")
        except Exception:
            pbg = T.BG
        super().__init__(parent, bg=pbg)
        self.cmd = cmd
        self.c1, self.c2 = color, hover
        lt = f" {icon}  {text}" if icon else f"  {text}  "
        self.lbl = tk.Label(self, text=lt, font=("Segoe UI", fs, "bold"),
                            fg=T.TXT, bg=color, cursor="hand2",
                            padx=pad_x, pady=pad_y)
        self.lbl.pack(padx=1, pady=1)
        self.lbl.bind("<Enter>", lambda e: self.lbl.config(bg=self.c2))
        self.lbl.bind("<Leave>", lambda e: self.lbl.config(bg=self.c1))
        self.lbl.bind("<Button-1>", lambda e: self.cmd() if self.cmd else None)

    def set_text(self, text, icon=""):
        lt = f" {icon}  {text}" if icon else f"  {text}  "
        self.lbl.config(text=lt)


class ToggleBtn(tk.Frame):
    def __init__(self, parent, options, callback, active=0):
        try:
            pbg = parent.cget("bg")
        except Exception:
            pbg = T.BG
        super().__init__(parent, bg=pbg)
        self.options = options
        self.callback = callback
        self.active = active
        self.btns = []
        container = tk.Frame(self, bg=T.BORDER, padx=1, pady=1)
        container.pack()
        inner = tk.Frame(container, bg=T.BG3)
        inner.pack()
        for i, opt in enumerate(options):
            lbl = tk.Label(inner, text=f" {opt['icon']}  {opt['name']} ",
                           font=("Segoe UI", 10, "bold"),
                           fg=T.TXT, cursor="hand2", padx=12, pady=5)
            lbl.pack(side="left", padx=1, pady=1)
            lbl.bind("<Button-1>", lambda e, idx=i: self._sel(idx))
            self.btns.append(lbl)
        self._upd()

    def _sel(self, idx):
        if idx != self.active:
            self.active = idx
            self._upd()
            self.callback(idx)

    def _upd(self):
        for i, b in enumerate(self.btns):
            if i == self.active:
                b.config(bg=self.options[i].get("color", T.RED), fg=T.TXT)
            else:
                b.config(bg=T.BG3, fg=T.TXT3)


class Status(tk.Label):
    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self._on = False
        self._base = ""
        self._d = 0

    def loading(self, t):
        self._base, self._on, self._d = t, True, 0
        self._go()

    def _go(self):
        if self._on:
            self._d = (self._d + 1) % 4
            self.config(text=f"{self._base}{'.' * self._d}")
            self.after(300, self._go)

    def done(self, t):
        self._on = False
        self.config(text=t)


def find_password(soup):
    password = ""
    body = (soup.find("div", class_="entry-content")
            or soup.find("div", class_="post-content")
            or soup.find("article")
            or soup.find("body"))
    if not body:
        return ""

    full_text = body.get_text(" ", strip=False)
    patterns = [
        r'[Şş]ifre\s*[:\-=\s]\s*([^\s<\n,]+)',
        r'[Ss]ifre\s*[:\-=\s]\s*([^\s<\n,]+)',
        r'[Pp]arola\s*[:\-=\s]\s*([^\s<\n,]+)',
        r'[Pp]assword\s*[:\-=\s]\s*([^\s<\n,]+)',
        r'[Aa]rşiv\s+[Şş]ifresi\s*[:\-=\s]\s*([^\s<\n,]+)',
        r'[Rr]ar\s+[Şş]ifresi\s*[:\-=\s]\s*([^\s<\n,]+)',
        r'[Zz]ip\s+[Şş]ifresi\s*[:\-=\s]\s*([^\s<\n,]+)',
    ]
    for pat in patterns:
        m = re.search(pat, full_text)
        if m:
            pw = m.group(1).strip().rstrip(".,;:)\"'")
            if len(pw) >= 2 and pw.lower() not in ["yok", "none", "var", "varsa"]:
                password = pw
                break

    if not password:
        keywords = ["şifre", "sifre", "parola", "password", "şifresi"]
        for tag in body.find_all(["p", "li", "span", "strong", "b", "em", "td", "div", "h3", "h4"]):
            text = tag.get_text(strip=True)
            text_lower = text.lower()
            for kw in keywords:
                if kw in text_lower:
                    parts = re.split(r'[:\-=]', text, maxsplit=1)
                    if len(parts) > 1:
                        words = parts[1].strip().rstrip(".,;:)\"'").split()
                        if words:
                            pw = words[0].strip().rstrip(".,;:)\"'")
                            if len(pw) >= 2 and pw.lower() not in ["yok", "none", "var", "varsa"]:
                                password = pw
                                break
            if password:
                break

    if not password:
        for tag in body.find_all(["p", "li", "div", "span"]):
            text_lower = tag.get_text(strip=True).lower()
            if any(kw in text_lower for kw in ["şifre", "sifre", "password", "parola"]):
                bold = tag.find(["strong", "b", "em", "code"])
                if bold:
                    pw = bold.get_text(strip=True).strip().rstrip(".,;:)\"'")
                    if len(pw) >= 2 and not any(kw in pw.lower() for kw in ["şifre", "sifre", "password", "parola", "yok"]):
                        password = pw
                        break
    return password


def find_alt_links(soup, base_url):
    links = []
    div = (soup.find("div", class_="entry-content")
           or soup.find("div", class_="post-content")
           or soup.find("article")
           or soup)
    if not div:
        return []

    base_domain = base_url.replace("https://", "").replace("http://", "").replace("www.", "")

    for a in div.find_all("a", href=True):
        href = a.get("href", "").strip()
        atxt = a.get_text(strip=True)
        atxt_low = atxt.lower()

        # URL düzelt
        if not href.startswith("http"):
            href = fix_url(href, base_url)

        if not href.startswith("http"):
            continue

        href_low = href.lower()

        is_alt = any(k in atxt_low for k in [
            "alternatif", "alternative", "link",
            "indir", "download", "torrent", "magnet",
            "google drive", "mega", "mediafire",
            "yandex", "uptobox", "part", "bölüm",
        ])
        is_host = any(h in href_low for h in [
            "mega.nz", "mega.co", "mediafire.com", "drive.google",
            "yandex.disk", "yandex.com", "uptobox", "rapidgator",
            "1fichier", "turbobit", "hitfile", "uploaded",
            "userscloud", "clicknupload", "racaty",
        ])

        if is_alt or is_host:
            if base_domain not in href_low or "indir" in href_low:
                links.append({"text": atxt or href, "url": href})

    seen = set()
    unique = []
    for l in links:
        if l["url"] not in seen:
            seen.add(l["url"])
            unique.append(l)
    return unique


def get_link_icon(text, url):
    c = (text + " " + url).lower()
    if "mega" in c: return "☁️"
    if "drive" in c or "google" in c: return "📁"
    if "mediafire" in c: return "🔥"
    if "torrent" in c or "magnet" in c: return "🧲"
    if "yandex" in c: return "💿"
    if "rapidgator" in c: return "⚡"
    if "1fichier" in c: return "📦"
    return "🔗"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Aras Oyun İndirici")
        self.root.geometry("1100x780")
        self.root.configure(bg=T.BG)
        self.root.minsize(900, 650)

        self.session = requests.Session()
        self.page = 1
        self.query = ""
        self.busy = False
        self.games = []
        self.history = []
        self.favorites = []
        self.source_key = "oyunindir.vip"
        self.source = SOURCES[self.source_key]

        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        self._load_favs()
        self._ui()
        self._center()

    def _center(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"+{x}+{y}")

    def _load_favs(self):
        try:
            if os.path.exists("aras_favs.json"):
                with open("aras_favs.json", "r", encoding="utf-8") as f:
                    self.favorites = json.load(f)
        except Exception:
            self.favorites = []

    def _save_favs(self):
        try:
            with open("aras_favs.json", "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _ui(self):
        # HEADER
        hdr = tk.Frame(self.root, bg=T.HEADER, height=165)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        top = tk.Frame(hdr, bg=T.HEADER)
        top.pack(fill="x", padx=25, pady=(12, 0))

        logo_f = tk.Frame(top, bg=T.HEADER)
        logo_f.pack(side="left")
        tk.Label(logo_f, text="🎮", font=("Segoe UI", 30),
                 bg=T.HEADER, fg=T.RED).pack(side="left")
        tc = tk.Frame(logo_f, bg=T.HEADER)
        tc.pack(side="left", padx=(8, 0))
        tk.Label(tc, text="Aras Oyun İndirici",
                 font=("Segoe UI", 19, "bold"),
                 bg=T.HEADER, fg=T.TXT).pack(anchor="w")
        self.source_lbl = tk.Label(
            tc, text=f"Kaynak: {self.source['icon']} {self.source['name']}",
            font=("Segoe UI", 9), bg=T.HEADER, fg=T.TXT3)
        self.source_lbl.pack(anchor="w")

        right_top = tk.Frame(top, bg=T.HEADER)
        right_top.pack(side="right")

        src_opts = [
            {"name": "VIP", "icon": "🟣", "color": T.PURPLE},
            {"name": "Cafe", "icon": "🟠", "color": T.ORANGE},
        ]
        ToggleBtn(right_top, src_opts, self._switch_source, active=0).pack(
            side="left", padx=(0, 10))
        Btn(right_top, "Favoriler", "⭐", self._show_favs,
            T.GOLD, T.ORANGE, 10, pad_y=3).pack(side="left", padx=(0, 5))
        Btn(right_top, "Geçmiş", "📜", self._show_history,
            T.BLUE, T.BLUE2, 10, pad_y=3).pack(side="left")

        # SEARCH
        sr = tk.Frame(hdr, bg=T.HEADER)
        sr.pack(pady=(10, 0))

        eb = tk.Frame(sr, bg=T.RED, padx=2, pady=2)
        eb.pack(side="left")
        ei = tk.Frame(eb, bg=T.INPUT)
        ei.pack()
        tk.Label(ei, text=" 🔍", font=("Segoe UI", 13),
                 bg=T.INPUT, fg=T.TXT3).pack(side="left")

        self.entry = tk.Entry(ei, font=("Segoe UI", 13), width=38,
                              bg=T.INPUT, fg=T.TXT,
                              insertbackground=T.RED,
                              relief="flat", border=0)
        self.entry.pack(side="left", ipady=8, padx=(5, 8))
        self.entry.insert(0, "Oyun adı yazın...")
        self.entry.config(fg=T.TXT3)
        self.entry.bind("<FocusIn>", self._fi)
        self.entry.bind("<FocusOut>", self._fo)
        self.entry.bind("<Return>", lambda e: self.search())

        clr = tk.Label(ei, text="✕", font=("Segoe UI", 12, "bold"),
                       bg=T.INPUT, fg=T.TXT3, cursor="hand2", padx=8)
        clr.pack(side="left")
        clr.bind("<Button-1>", lambda e: self._clear_entry())
        clr.bind("<Enter>", lambda e: clr.config(fg=T.RED))
        clr.bind("<Leave>", lambda e: clr.config(fg=T.TXT3))

        Btn(sr, "Ara", "🔍", self.search,
            T.RED, T.RED2, 12).pack(side="left", padx=(8, 4))
        Btn(sr, "Popüler", "🔥", self.home,
            T.PURPLE, T.PURPLE2, 11).pack(side="left", padx=4)

        cat_row = tk.Frame(hdr, bg=T.HEADER)
        cat_row.pack(pady=(8, 0))
        for name, icon in [("Aksiyon", "🎯"), ("Macera", "🗺️"), ("Strateji", "♟️"),
                           ("Yarış", "🏎️"), ("Spor", "⚽"), ("Korku", "👻"),
                           ("RPG", "⚔️"), ("FPS", "🔫")]:
            cb = tk.Label(cat_row, text=f"{icon} {name}",
                          font=("Segoe UI", 9), fg=T.TXT2,
                          bg=T.HEADER, cursor="hand2", padx=8, pady=2)
            cb.pack(side="left", padx=2)
            cb.bind("<Enter>", lambda e, w=cb: w.config(fg=T.RED, bg=T.BG3))
            cb.bind("<Leave>", lambda e, w=cb: w.config(fg=T.TXT2, bg=T.HEADER))
            cb.bind("<Button-1>", lambda e, n=name: self._cat_search(n))

        tk.Frame(self.root, bg=T.RED, height=2).pack(fill="x")

        # STATUS
        sf = tk.Frame(self.root, bg=T.BG, height=30)
        sf.pack(fill="x", padx=25, pady=(6, 0))
        self.status = Status(sf, text="🎮  Hoş geldiniz! Bir oyun arayın.",
                             font=("Segoe UI", 10), bg=T.BG, fg=T.TXT2, anchor="w")
        self.status.pack(side="left")
        self.cnt = tk.Label(sf, text="", font=("Segoe UI", 10, "bold"),
                            bg=T.BG, fg=T.RED)
        self.cnt.pack(side="right")

        sty = ttk.Style()
        sty.theme_use("clam")
        sty.configure("r.Horizontal.TProgressbar",
                       troughcolor=T.BG2, background=T.RED,
                       darkcolor=T.RED, lightcolor=T.RED2, borderwidth=0)
        self.prog = ttk.Progressbar(self.root, style="r.Horizontal.TProgressbar",
                                     mode="indeterminate")

        # CONTENT
        cf = tk.Frame(self.root, bg=T.BG)
        cf.pack(fill="both", expand=True, padx=25, pady=(6, 0))

        self.sb = tk.Scrollbar(cf, orient="vertical", bg=T.BG2,
                                troughcolor=T.BG, activebackground=T.RED,
                                highlightthickness=0, bd=0, width=10)
        self.sb.pack(side="right", fill="y")

        self.cv = tk.Canvas(cf, bg=T.BG, highlightthickness=0, bd=0,
                             yscrollcommand=self.sb.set)
        self.cv.pack(side="left", fill="both", expand=True)
        self.sb.config(command=self.cv.yview)

        self.inner = tk.Frame(self.cv, bg=T.BG)
        self.iid = self.cv.create_window((0, 0), window=self.inner, anchor="nw")
        self.cv.bind("<Configure>",
                      lambda e: self.cv.itemconfig(self.iid, width=e.width))
        self.inner.bind("<Configure>",
                         lambda e: self.cv.configure(scrollregion=self.cv.bbox("all")))
        self.cv.bind("<Enter>",
                      lambda e: self.cv.bind_all("<MouseWheel>", self._wh))
        self.cv.bind("<Leave>",
                      lambda e: self.cv.unbind_all("<MouseWheel>"))

        # FOOTER
        ft = tk.Frame(self.root, bg=T.HEADER, height=50)
        ft.pack(fill="x", side="bottom")
        ft.pack_propagate(False)
        nav = tk.Frame(ft, bg=T.HEADER)
        nav.pack(pady=8)
        Btn(nav, "◀ Önceki", "", self.pprev,
            T.BLUE, T.BLUE2, 10).pack(side="left", padx=5)
        self.plbl = tk.Label(nav, text="Sayfa 1",
                             font=("Segoe UI", 12, "bold"),
                             fg=T.TXT, bg=T.HEADER)
        self.plbl.pack(side="left", padx=20)
        Btn(nav, "Sonraki ▶", "", self.pnext,
            T.BLUE, T.BLUE2, 10).pack(side="left", padx=5)

        self.footer_src = tk.Label(
            ft, text=f"{self.source['icon']} {self.source['name']}",
            font=("Segoe UI", 9, "bold"),
            fg=self.source["color"], bg=T.HEADER)
        self.footer_src.pack(side="right", padx=20)

    # ========== HELPERS ==========
    def _wh(self, e):
        self.cv.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def _fi(self, e):
        if self.entry.get() == "Oyun adı yazın...":
            self.entry.delete(0, "end")
            self.entry.config(fg=T.TXT)

    def _fo(self, e):
        if not self.entry.get().strip():
            self.entry.insert(0, "Oyun adı yazın...")
            self.entry.config(fg=T.TXT3)

    def _clear_entry(self):
        self.entry.delete(0, "end")
        self.entry.config(fg=T.TXT)
        self.entry.focus()

    def _switch_source(self, idx):
        keys = list(SOURCES.keys())
        self.source_key = keys[idx]
        self.source = SOURCES[self.source_key]
        self.source_lbl.config(
            text=f"Kaynak: {self.source['icon']} {self.source['name']}")
        self.footer_src.config(
            text=f"{self.source['icon']} {self.source['name']}",
            fg=self.source["color"])
        self.status.done(f"✅  Kaynak: {self.source['icon']} {self.source['name']}")

    def _cat_search(self, cat):
        self.entry.delete(0, "end")
        self.entry.insert(0, cat)
        self.entry.config(fg=T.TXT)
        self.search()

    # ========== FAV & HISTORY ==========
    def _add_fav(self, game):
        for f in self.favorites:
            if f.get("url") == game.get("url"):
                messagebox.showinfo("Bilgi", "Zaten favorilerde!")
                return
        self.favorites.append(game)
        self._save_favs()
        self.status.done("⭐  Favorilere eklendi!")

    def _show_favs(self):
        win = tk.Toplevel(self.root)
        win.title("⭐ Favoriler")
        win.geometry("600x500")
        win.configure(bg=T.BG)
        tk.Label(win, text="⭐  Favori Oyunlarım",
                 font=("Segoe UI", 16, "bold"),
                 fg=T.GOLD, bg=T.BG).pack(pady=(15, 10))
        if not self.favorites:
            tk.Label(win, text="Henüz favori eklenmemiş",
                     font=("Segoe UI", 12), fg=T.TXT3, bg=T.BG).pack(pady=30)
            return

        ff = tk.Frame(win, bg=T.BG)
        ff.pack(fill="both", expand=True, padx=15, pady=5)
        fc = tk.Canvas(ff, bg=T.BG, highlightthickness=0, bd=0)
        fs = tk.Scrollbar(ff, orient="vertical", command=fc.yview,
                           bg=T.BG2, troughcolor=T.BG, width=8,
                           highlightthickness=0, bd=0)
        fi = tk.Frame(fc, bg=T.BG)
        fi.bind("<Configure>", lambda e: fc.configure(scrollregion=fc.bbox("all")))
        fid = fc.create_window((0, 0), window=fi, anchor="nw")
        fc.configure(yscrollcommand=fs.set)
        fc.bind("<Configure>", lambda e: fc.itemconfig(fid, width=e.width))
        fs.pack(side="right", fill="y")
        fc.pack(side="left", fill="both", expand=True)
        fc.bind("<Enter>", lambda e: fc.bind_all("<MouseWheel>",
                lambda ev: fc.yview_scroll(int(-1*(ev.delta/120)), "units")))
        fc.bind("<Leave>", lambda e: fc.unbind_all("<MouseWheel>"))

        for fav in self.favorites:
            row = tk.Frame(fi, bg=T.CARD, highlightbackground=T.BORDER,
                           highlightthickness=1)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"⭐  {fav.get('title', '')}",
                     font=("Segoe UI", 11, "bold"), fg=T.TXT, bg=T.CARD,
                     anchor="w", wraplength=350).pack(side="left", padx=12, pady=8)
            bf2 = tk.Frame(row, bg=T.CARD)
            bf2.pack(side="right", padx=8, pady=5)
            Btn(bf2, "Aç", "🔍", lambda g=fav: self._detail(g),
                T.BLUE, T.BLUE2, 9, pad_y=2).pack(side="left", padx=2)
            Btn(bf2, "Sil", "🗑️", lambda g=fav, w=win: self._del_fav(g, w),
                T.RED, T.RED2, 9, pad_y=2).pack(side="left", padx=2)

    def _del_fav(self, game, win):
        self.favorites = [f for f in self.favorites if f.get("url") != game.get("url")]
        self._save_favs()
        win.destroy()
        self._show_favs()

    def _show_history(self):
        win = tk.Toplevel(self.root)
        win.title("📜 Arama Geçmişi")
        win.geometry("450x400")
        win.configure(bg=T.BG)
        tk.Label(win, text="📜  Arama Geçmişi",
                 font=("Segoe UI", 16, "bold"),
                 fg=T.CYAN, bg=T.BG).pack(pady=(15, 10))
        if not self.history:
            tk.Label(win, text="Henüz arama yapılmamış",
                     font=("Segoe UI", 12), fg=T.TXT3, bg=T.BG).pack(pady=30)
            return
        for h in self.history:
            hf = tk.Frame(win, bg=T.CARD, highlightbackground=T.BORDER,
                          highlightthickness=1)
            hf.pack(fill="x", padx=15, pady=2)
            tk.Label(hf, text=f"🔍  {h}", font=("Segoe UI", 11),
                     fg=T.TXT, bg=T.CARD, anchor="w").pack(
                side="left", padx=12, pady=6)
            Btn(hf, "Ara", "🔍",
                lambda q=h, w=win: (w.destroy(), self._hist_search(q)),
                T.BLUE, T.BLUE2, 9, pad_y=2).pack(side="right", padx=8, pady=4)

    def _hist_search(self, q):
        self.entry.delete(0, "end")
        self.entry.insert(0, q)
        self.entry.config(fg=T.TXT)
        self.search()

    # ========== SEARCH ==========
    def search(self):
        q = self.entry.get().strip()
        if q == "Oyun adı yazın..." or not q:
            messagebox.showinfo("Bilgi", "Lütfen bir oyun adı girin!")
            return
        self.query = q
        self.page = 1
        if q not in self.history:
            self.history.insert(0, q)
            self.history = self.history[:20]
        self._do_search()

    def home(self):
        self.query = ""
        self.page = 1
        self._load("Popüler oyunlar yükleniyor", self.source["base"] + "/")

    def _do_search(self):
        q = urllib.parse.quote(self.query)
        base = self.source["base"]
        url = f"{base}/page/{self.page}/?s={q}" if self.page > 1 else f"{base}/?s={q}"
        self._load(f"'{self.query}' aranıyor ({self.source['name']})", url)

    def _load(self, msg, url):
        self.busy = True
        self.prog.pack(fill="x", padx=25, pady=(3, 0))
        self.prog.start(12)
        self.status.loading(msg)
        self.cnt.config(text="")
        base = self.source["base"]
        threading.Thread(target=self._fetch, args=(url, base), daemon=True).start()

    def _stop(self):
        self.busy = False
        self.prog.stop()
        self.prog.pack_forget()

    def _fetch(self, url, base):
        try:
            r = self.session.get(url, headers=UA, timeout=15)
            r.encoding = "utf-8"
            if r.status_code != 200:
                self.root.after(0, self._err, f"HTTP {r.status_code}")
                return
            soup = BeautifulSoup(r.text, "html.parser")
            games = self._parse(soup, base)
            self.root.after(0, self._show, games)
        except Exception as e:
            msg = str(e)
            self.root.after(0, self._err, msg)

    def _parse(self, soup, base):
        games = []
        arts = soup.find_all("article")
        if not arts:
            arts = soup.find_all("div", class_="post")

        if not arts:
            for a in soup.select("h2 a, h3 a, .post-title a, .entry-title a"):
                t = a.get_text(strip=True)
                h = a.get("href", "")
                h = fix_url(h, base)
                if t and h and len(t) > 3:
                    games.append({"title": t, "url": h,
                                  "cat": "", "date": "", "desc": ""})
            return games

        for art in arts:
            try:
                g = {}
                tt = art.find("h2") or art.find("h3") or art.find("a")
                if tt:
                    a = tt.find("a") if tt.name != "a" else tt
                    if not a:
                        a = art.find("a", href=True)
                    if a:
                        g["title"] = a.get_text(strip=True)
                        raw_url = a.get("href", "")
                        g["url"] = fix_url(raw_url, base)

                if not g.get("title") or not g.get("url"):
                    continue

                c = art.find("span", class_="cat") or art.find("a", rel="category")
                g["cat"] = c.get_text(strip=True) if c else ""
                d = art.find("time") or art.find("span", class_="date")
                g["date"] = d.get_text(strip=True) if d else ""
                p = art.find("p")
                g["desc"] = p.get_text(strip=True)[:150] if p else ""
                games.append(g)
            except Exception:
                continue
        return games

    # ========== RESULTS ==========
    def _show(self, games):
        self._stop()
        for w in self.inner.winfo_children():
            w.destroy()

        if not games:
            self.status.done("❌  Sonuç bulunamadı")
            f = tk.Frame(self.inner, bg=T.BG)
            f.pack(pady=80)
            tk.Label(f, text="😔", font=("Segoe UI", 50),
                     bg=T.BG, fg=T.TXT3).pack()
            tk.Label(f, text="Sonuç Bulunamadı",
                     font=("Segoe UI", 18, "bold"),
                     bg=T.BG, fg=T.TXT2).pack(pady=(10, 5))
            tk.Label(f, text="Farklı anahtar kelime veya kaynak deneyin",
                     font=("Segoe UI", 11), bg=T.BG, fg=T.TXT3).pack()
            return

        self.games = games
        si, sn = self.source["icon"], self.source["name"]
        self.status.done(f"✅  {len(games)} oyun bulundu • {si} {sn}")
        self.cnt.config(text=f"Sayfa {self.page}  •  {len(games)} sonuç")
        self.plbl.config(text=f"Sayfa {self.page}")

        for i, g in enumerate(games):
            self._card(i, g)
        self.cv.yview_moveto(0)

    def _err(self, msg):
        self._stop()
        self.status.done(f"❌  {msg}")
        messagebox.showerror("Hata", msg)

    # ========== CARD ==========
    def _card(self, idx, game):
        card = tk.Frame(self.inner, bg=T.CARD,
                        highlightbackground=T.BORDER, highlightthickness=1)
        card.pack(fill="x", padx=6, pady=4)

        row = tk.Frame(card, bg=T.CARD)
        row.pack(fill="x", padx=14, pady=10)

        colors = [T.RED, T.PURPLE, T.CYAN, T.BLUE2, T.ORANGE]
        nc = colors[idx % len(colors)]
        nf = tk.Frame(row, bg=nc, width=36, height=36)
        nf.pack(side="left", padx=(0, 12))
        nf.pack_propagate(False)
        tk.Label(nf, text=str(idx + 1), font=("Segoe UI", 12, "bold"),
                 fg=T.TXT, bg=nc).place(relx=.5, rely=.5, anchor="center")

        info = tk.Frame(row, bg=T.CARD)
        info.pack(side="left", fill="both", expand=True)
        tk.Label(info, text=game["title"], font=("Segoe UI", 12, "bold"),
                 fg=T.TXT, bg=T.CARD, anchor="w",
                 wraplength=480, justify="left").pack(anchor="w")

        meta = tk.Frame(info, bg=T.CARD)
        meta.pack(anchor="w", pady=(2, 0))
        if game.get("cat"):
            tk.Label(meta, text=f"📁 {game['cat']}", font=("Segoe UI", 9),
                     fg=T.CYAN, bg=T.CARD).pack(side="left", padx=(0, 10))
        if game.get("date"):
            tk.Label(meta, text=f"📅 {game['date']}", font=("Segoe UI", 9),
                     fg=T.TXT3, bg=T.CARD).pack(side="left", padx=(0, 10))
        tk.Label(meta, text=f"{self.source['icon']} {self.source['name']}",
                 font=("Segoe UI", 8), fg=self.source["color"],
                 bg=T.CARD).pack(side="left")

        if game.get("desc"):
            d = game["desc"][:85] + "..." if len(game["desc"]) > 85 else game["desc"]
            tk.Label(info, text=d, font=("Segoe UI", 9), fg=T.TXT3,
                     bg=T.CARD, anchor="w", wraplength=480,
                     justify="left").pack(anchor="w", pady=(2, 0))

        bf = tk.Frame(row, bg=T.CARD)
        bf.pack(side="right", padx=(10, 0))
        Btn(bf, "Detay", "🔍", lambda g=game: self._detail(g),
            T.BLUE, T.BLUE2, 10, pad_y=3).pack(pady=(0, 3))
        Btn(bf, "İndir", "⬇️", lambda g=game: self._download(g),
            T.GREEN2, T.GREEN, 10, pad_y=3).pack(pady=(0, 3))
        Btn(bf, "⭐", "", lambda g=game: self._add_fav(g),
            T.GOLD, T.ORANGE, 10, pad_y=3).pack()

        card.bind("<Enter>", lambda e, c=card: c.config(
            highlightbackground=T.RED, highlightthickness=2))
        card.bind("<Leave>", lambda e, c=card: c.config(
            highlightbackground=T.BORDER, highlightthickness=1))

    # ========== DETAIL ==========
    def _detail(self, game):
        win = tk.Toplevel(self.root)
        win.title(f"🎮 {game.get('title', '')}")
        win.geometry("750x620")
        win.configure(bg=T.BG)

        hdr = tk.Frame(win, bg=T.CARD)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"🎮  {game.get('title', '')}",
                 font=("Segoe UI", 14, "bold"), fg=T.TXT, bg=T.CARD,
                 wraplength=700, anchor="w").pack(fill="x", padx=20, pady=12)
        tk.Label(hdr, text=f"{self.source['icon']} {self.source['name']}",
                 font=("Segoe UI", 9), fg=self.source["color"],
                 bg=T.CARD).pack(padx=20, anchor="w", pady=(0, 8))
        tk.Frame(win, bg=T.RED, height=2).pack(fill="x")

        # Şifre alanı (dinamik)
        pw_container = tk.Frame(win, bg=T.BG)

        load = Status(win, text="", font=("Segoe UI", 11),
                       fg=T.RED, bg=T.BG)
        load.pack(pady=5)
        load.loading("Detaylar yükleniyor")

        tf = tk.Frame(win, bg=T.BG)
        tf.pack(fill="both", expand=True, padx=18, pady=(0, 6))

        txt = tk.Text(tf, bg=T.CARD, fg=T.TXT, font=("Segoe UI", 11),
                      wrap="word", relief="flat", padx=15, pady=15,
                      insertbackground=T.TXT, selectbackground=T.RED,
                      state="disabled", cursor="arrow")
        tsb = tk.Scrollbar(tf, command=txt.yview, bg=T.CARD,
                            troughcolor=T.BG, activebackground=T.RED,
                            highlightthickness=0, bd=0, width=10)
        txt.config(yscrollcommand=tsb.set)
        tsb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)

        txt.bind("<Enter>", lambda e: txt.bind_all("<MouseWheel>",
                 lambda ev: txt.yview_scroll(int(-1*(ev.delta/120)), "units")))
        txt.bind("<Leave>", lambda e: txt.unbind_all("<MouseWheel>"))

        bf = tk.Frame(win, bg=T.BG)
        bf.pack(fill="x", padx=18, pady=(0, 12))
        Btn(bf, "Sayfayı Aç", "🌐",
            lambda: webbrowser.open(game.get("url", "")),
            T.BLUE, T.BLUE2).pack(side="left", padx=(0, 6))
        Btn(bf, "İndir", "⬇️",
            lambda: self._download(game),
            T.GREEN2, T.GREEN).pack(side="left", padx=(0, 6))
        Btn(bf, "Favori", "⭐",
            lambda: self._add_fav(game),
            T.GOLD, T.ORANGE).pack(side="left")
        Btn(bf, "Kapat", "✖", win.destroy,
            T.RED, "#ff4466").pack(side="right")

        game_url = game.get("url", "")
        base_url = self.source["base"]

        # URL düzelt
        game_url = fix_url(game_url, base_url)

        def fetch():
            content = ""
            alt_links = []
            password = ""
            error_text = ""

            try:
                r = self.session.get(game_url, headers=UA, timeout=15)
                r.encoding = "utf-8"
                soup = BeautifulSoup(r.text, "html.parser")

                password = find_password(soup)
                alt_links = find_alt_links(soup, base_url)

                div = (soup.find("div", class_="entry-content")
                       or soup.find("div", class_="post-content")
                       or soup.find("article"))
                if div:
                    for tag in div.find_all(["p", "li", "h2", "h3", "h4"]):
                        t = tag.get_text(strip=True)
                        if t and len(t) > 2:
                            if tag.name in ("h2", "h3", "h4"):
                                content += f"\n{'━'*45}\n  ▶ {t}\n{'━'*45}\n\n"
                            else:
                                content += f"  {t}\n\n"
                if not content.strip():
                    content = "  Detay bilgisi bulunamadı."

            except Exception as exc:
                error_text = str(exc)

            # Sonuçları kaydet ve UI thread'de göster
            result = {
                "content": content,
                "alt_links": alt_links,
                "password": password,
                "error": error_text,
            }
            win.after(0, show_result, result)

        def show_result(result):
            load.done("")

            content = result["content"]
            alt_links = result["alt_links"]
            password = result["password"]
            error_text = result["error"]

            if error_text:
                content = f"  Hata: {error_text}"

            # Şifre göster
            if password:
                pw_container.pack(fill="x", padx=18, pady=(6, 0))
                for w in pw_container.winfo_children():
                    w.destroy()

                pw_inner = tk.Frame(pw_container, bg=T.BG3,
                                     highlightbackground=T.GOLD,
                                     highlightthickness=1)
                pw_inner.pack(fill="x")
                pw_row = tk.Frame(pw_inner, bg=T.BG3)
                pw_row.pack(fill="x", padx=12, pady=8)

                tk.Label(pw_row, text="🔐  Arşiv Şifresi:",
                         font=("Segoe UI", 11, "bold"),
                         fg=T.GOLD, bg=T.BG3).pack(side="left")

                pw_entry = tk.Entry(pw_row, font=("Consolas", 13, "bold"),
                                    fg=T.GOLD, bg=T.INPUT, relief="flat",
                                    width=25, readonlybackground=T.INPUT)
                pw_entry.insert(0, password)
                pw_entry.config(state="readonly")
                pw_entry.pack(side="left", padx=(10, 8), ipady=4)

                pw_val = password  # closure için kopyala

                def copy_pw():
                    win.clipboard_clear()
                    win.clipboard_append(pw_val)
                    cp_btn.set_text("Kopyalandı! ✓", "")
                    win.after(2000, lambda: cp_btn.set_text("Kopyala", "📋"))

                cp_btn = Btn(pw_row, "Kopyala", "📋", copy_pw,
                             T.GOLD, T.ORANGE, 10, pad_y=3)
                cp_btn.pack(side="left")

            # Text
            txt.config(state="normal")
            txt.delete("1.0", "end")

            txt.tag_configure("title", font=("Segoe UI", 14, "bold"),
                               foreground=T.RED)
            txt.tag_configure("body", font=("Segoe UI", 11),
                               foreground=T.TXT)
            txt.tag_configure("pw_tag", font=("Consolas", 13, "bold"),
                               foreground=T.GOLD, background=T.BG3)

            txt.insert("end", f"🎮 {game.get('title', '')}\n\n", "title")
            if game.get("cat"):
                txt.insert("end", f"  📁 Kategori: {game['cat']}\n", "body")
            if game.get("date"):
                txt.insert("end", f"  📅 Tarih: {game['date']}\n", "body")
            txt.insert("end", "\n" + "─" * 50 + "\n\n", "body")

            if password:
                txt.insert("end", "  🔐  ARŞİV ŞİFRESİ\n", "title")
                txt.insert("end", f"  ➤  {password}\n\n", "pw_tag")
                txt.insert("end", "─" * 50 + "\n\n", "body")

            txt.insert("end", content, "body")

            if alt_links:
                txt.insert("end", "\n\n" + "━" * 50 + "\n", "body")
                txt.insert("end", "  ⬇️  ALTERNATİF İNDİRME LİNKLERİ\n", "title")
                txt.insert("end", "━" * 50 + "\n\n", "body")

                for i, link in enumerate(alt_links):
                    tag_name = f"alink_{i}"
                    link_url = link["url"]
                    icon = get_link_icon(link["text"], link_url)
                    display = f"  {icon}  <<< Alternatif: {link['text']} >>>\n\n"

                    txt.tag_configure(tag_name,
                                      font=("Segoe UI", 12, "bold"),
                                      foreground=T.GREEN, underline=True)
                    txt.tag_bind(tag_name, "<Enter>",
                                  lambda e, tn=tag_name:
                                  txt.tag_configure(tn, foreground=T.GOLD))
                    txt.tag_bind(tag_name, "<Leave>",
                                  lambda e, tn=tag_name:
                                  txt.tag_configure(tn, foreground=T.GREEN))
                    txt.tag_bind(tag_name, "<Button-1>",
                                  lambda e, u=link_url: webbrowser.open(u))
                    txt.insert("end", display, tag_name)

                txt.insert("end", "─" * 50 + "\n", "body")
                txt.insert("end", f"  Toplam {len(alt_links)} alternatif link\n", "body")

            txt.config(state="disabled")

        threading.Thread(target=fetch, daemon=True).start()

    # ========== DOWNLOAD ==========
    def _download(self, game):
        self.status.loading("Alternatif linkler aranıyor")
        base_url = self.source["base"]
        game_url = fix_url(game.get("url", ""), base_url)

        def fetch():
            unique_links = []
            password = ""
            error_text = ""

            try:
                r = self.session.get(game_url, headers=UA, timeout=15)
                r.encoding = "utf-8"
                soup = BeautifulSoup(r.text, "html.parser")
                password = find_password(soup)
                unique_links = find_alt_links(soup, base_url)
            except Exception as exc:
                error_text = str(exc)

            result = {
                "links": unique_links,
                "password": password,
                "error": error_text,
            }
            self.root.after(0, handle_result, result)

        def handle_result(result):
            if result["error"]:
                self._err(result["error"])
            else:
                self._dlg(game, result["links"], result["password"])

        threading.Thread(target=fetch, daemon=True).start()

    def _dlg(self, game, links, password=""):
        self.status.done("✅  Hazır")

        if not links and not password:
            if messagebox.askyesno("Bilgi",
                                    "Alternatif link bulunamadı.\nOyun sayfasını açmak ister misiniz?"):
                webbrowser.open(fix_url(game.get("url", ""), self.source["base"]))
            return

        win = tk.Toplevel(self.root)
        win.title("⬇️  Alternatif Linkler")
        win.geometry("620x540")
        win.configure(bg=T.BG)
        win.resizable(False, True)

        hdr = tk.Frame(win, bg=T.CARD)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⬇️  Alternatif İndirme Linkleri",
                 font=("Segoe UI", 14, "bold"),
                 fg=T.TXT, bg=T.CARD).pack(pady=(12, 3), padx=20, anchor="w")

        t = game.get("title", "")
        if len(t) > 50:
            t = t[:50] + "..."
        tk.Label(hdr, text=t, font=("Segoe UI", 10),
                 fg=T.TXT2, bg=T.CARD).pack(padx=20, anchor="w")
        tk.Label(hdr, text=f"📦  {len(links)} alternatif link bulundu",
                 font=("Segoe UI", 10, "bold"),
                 fg=T.GREEN, bg=T.CARD).pack(pady=(3, 8), padx=20, anchor="w")
        tk.Frame(win, bg=T.RED, height=2).pack(fill="x")

        # ŞİFRE
        if password:
            pw_frame = tk.Frame(win, bg=T.BG3,
                                 highlightbackground=T.GOLD,
                                 highlightthickness=1)
            pw_frame.pack(fill="x", padx=12, pady=(10, 5))
            pw_row = tk.Frame(pw_frame, bg=T.BG3)
            pw_row.pack(fill="x", padx=12, pady=8)

            tk.Label(pw_row, text="🔐  Arşiv Şifresi:",
                     font=("Segoe UI", 11, "bold"),
                     fg=T.GOLD, bg=T.BG3).pack(side="left")

            pw_entry = tk.Entry(pw_row, font=("Consolas", 13, "bold"),
                                fg=T.GOLD, bg=T.INPUT, relief="flat",
                                width=22, readonlybackground=T.INPUT)
            pw_entry.insert(0, password)
            pw_entry.config(state="readonly")
            pw_entry.pack(side="left", padx=(10, 8), ipady=4)

            pw_val = password

            def copy_pw():
                win.clipboard_clear()
                win.clipboard_append(pw_val)
                cp_btn.set_text("Kopyalandı! ✓", "")
                win.after(2000, lambda: cp_btn.set_text("Kopyala", "📋"))

            cp_btn = Btn(pw_row, "Kopyala", "📋", copy_pw,
                         T.GOLD, T.ORANGE, 10, pad_y=3)
            cp_btn.pack(side="left")

        # LİNKLER
        if links:
            lf = tk.Frame(win, bg=T.BG)
            lf.pack(fill="both", expand=True, padx=12, pady=6)

            lc = tk.Canvas(lf, bg=T.BG, highlightthickness=0, bd=0)
            ls = tk.Scrollbar(lf, orient="vertical", command=lc.yview,
                               bg=T.BG2, troughcolor=T.BG,
                               activebackground=T.RED,
                               highlightthickness=0, bd=0, width=8)
            li = tk.Frame(lc, bg=T.BG)
            li.bind("<Configure>",
                     lambda e: lc.configure(scrollregion=lc.bbox("all")))
            lid = lc.create_window((0, 0), window=li, anchor="nw")
            lc.configure(yscrollcommand=ls.set)
            lc.bind("<Configure>", lambda e: lc.itemconfig(lid, width=e.width))
            ls.pack(side="right", fill="y")
            lc.pack(side="left", fill="both", expand=True)

            lc.bind("<Enter>", lambda e: lc.bind_all("<MouseWheel>",
                    lambda ev: lc.yview_scroll(int(-1*(ev.delta/120)), "units")))
            lc.bind("<Leave>", lambda e: lc.unbind_all("<MouseWheel>"))

            for i, link in enumerate(links):
                row = tk.Frame(li, bg=T.CARD,
                               highlightbackground=T.BORDER, highlightthickness=1)
                row.pack(fill="x", pady=3)

                inf = tk.Frame(row, bg=T.CARD)
                inf.pack(side="left", fill="x", expand=True, padx=12, pady=8)

                icon = get_link_icon(link["text"], link["url"])
                tk.Label(inf, text=f"{icon}  Alternatif: {link['text']}",
                         font=("Segoe UI", 10, "bold"), fg=T.TXT,
                         bg=T.CARD, anchor="w",
                         wraplength=360).pack(anchor="w")

                su = link["url"][:48] + "..." if len(link["url"]) > 48 else link["url"]
                tk.Label(inf, text=su, font=("Segoe UI", 8),
                         fg=T.TXT3, bg=T.CARD, anchor="w").pack(anchor="w", pady=(2, 0))

                u = link["url"]
                Btn(row, "Aç", "🔗", lambda url=u: webbrowser.open(url),
                    T.GREEN2, T.GREEN, 10, pad_y=3).pack(side="right", padx=10, pady=6)

                row.bind("<Enter>", lambda e, r=row: r.config(
                    highlightbackground=T.GREEN, highlightthickness=2))
                row.bind("<Leave>", lambda e, r=row: r.config(
                    highlightbackground=T.BORDER, highlightthickness=1))
        else:
            tk.Label(win, text="Alternatif link bulunamadı",
                     font=("Segoe UI", 11), fg=T.TXT3, bg=T.BG).pack(pady=20)

        bf = tk.Frame(win, bg=T.BG)
        bf.pack(fill="x", padx=12, pady=(0, 12))
        if links:
            Btn(bf, "Hepsini Aç", "🚀",
                lambda: [webbrowser.open(l["url"]) for l in links[:5]],
                T.ORANGE, T.GOLD, 10).pack(side="left", padx=(0, 6))
        Btn(bf, "Sayfaya Git", "🌐",
            lambda: webbrowser.open(fix_url(game.get("url", ""), self.source["base"])),
            T.BLUE, T.BLUE2, 10).pack(side="left")
        Btn(bf, "Kapat", "✖", win.destroy,
            T.RED, "#ff4466", 10).pack(side="right")

    # ========== PAGES ==========
    def pnext(self):
        if self.busy:
            return
        self.page += 1
        self.plbl.config(text=f"Sayfa {self.page}")
        if self.query:
            self._do_search()
        else:
            self._load("Sayfa yükleniyor",
                       f"{self.source['base']}/page/{self.page}/")

    def pprev(self):
        if self.busy or self.page <= 1:
            return
        self.page -= 1
        self.plbl.config(text=f"Sayfa {self.page}")
        if self.query:
            self._do_search()
        else:
            url = f"{self.source['base']}/page/{self.page}/" \
                if self.page > 1 else self.source["base"] + "/"
            self._load("Sayfa yükleniyor", url)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()