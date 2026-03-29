import tkinter as tk
from tkinter import ttk, messagebox
import requests
from bs4 import BeautifulSoup
import threading
import webbrowser
import urllib.parse


# ===================== TEMA =====================
class T:
    BG = "#0b0b0f"
    BG2 = "#12121a"
    CARD = "#161625"
    CARD_H = "#1c1c30"
    INPUT = "#0e0e18"
    RED = "#e94560"
    RED2 = "#ff6b81"
    BLUE = "#0f3460"
    BLUE2 = "#533483"
    TXT = "#ffffff"
    TXT2 = "#a8a8b3"
    TXT3 = "#555566"
    BORDER = "#2a2a40"
    GREEN = "#00e676"
    GREEN2 = "#00c853"
    ORANGE = "#ff9100"
    GOLD = "#ffd700"
    HEADER = "#08080d"


BASE = "https://www.oyunindir.vip"
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
}


# ===================== BUTON =====================
class Btn(tk.Frame):
    def __init__(self, parent, text="", icon="", cmd=None,
                 color=T.RED, hover=T.RED2, fs=11, **kw):
        super().__init__(parent, bg=self._pbg(parent))
        self.cmd = cmd
        self.c1, self.c2 = color, hover
        lbl_text = f" {icon}  {text}" if icon else f"  {text}  "
        self.lbl = tk.Label(self, text=lbl_text,
                            font=("Segoe UI", fs, "bold"),
                            fg=T.TXT, bg=color, cursor="hand2",
                            padx=14, pady=5)
        self.lbl.pack(padx=1, pady=1)
        self.lbl.bind("<Enter>", lambda e: self.lbl.config(bg=self.c2))
        self.lbl.bind("<Leave>", lambda e: self.lbl.config(bg=self.c1))
        self.lbl.bind("<Button-1>", lambda e: self.cmd() if self.cmd else None)

    def _pbg(self, p):
        try: return p.cget("bg")
        except: return T.BG


# ===================== STATUS =====================
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
            self.after(350, self._go)

    def done(self, t):
        self._on = False
        self.config(text=t)


# ===================== ANA UYGULAMA =====================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Aras Oyun İndirici")
        self.root.geometry("1050x720")
        self.root.configure(bg=T.BG)
        self.root.minsize(850, 600)
        self.session = requests.Session()
        self.page = 1
        self.query = ""
        self.busy = False

        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except: pass

        self._ui()
        self._center()

    def _center(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        self.root.geometry(f"+{(self.root.winfo_screenwidth()-w)//2}+{(self.root.winfo_screenheight()-h)//2}")

    # =================== UI ===================
    def _ui(self):
        # HEADER
        hdr = tk.Frame(self.root, bg=T.HEADER, height=140)
        hdr.pack(fill="x"); hdr.pack_propagate(False)

        top = tk.Frame(hdr, bg=T.HEADER)
        top.pack(fill="x", padx=30, pady=(18, 0))
        tk.Label(top, text="🎮", font=("Segoe UI", 28),
                 bg=T.HEADER, fg=T.RED).pack(side="left")
        tc = tk.Frame(top, bg=T.HEADER)
        tc.pack(side="left", padx=(10, 0))
        tk.Label(tc, text="Aras Oyun İndirici",
                 font=("Segoe UI", 20, "bold"),
                 bg=T.HEADER, fg=T.TXT).pack(anchor="w")
        tk.Label(tc, text="Oyun Ara • İndir • Keyfini Çıkar",
                 font=("Segoe UI", 9),
                 bg=T.HEADER, fg=T.TXT3).pack(anchor="w")

        # SEARCH
        sr = tk.Frame(hdr, bg=T.HEADER)
        sr.pack(pady=(12, 0))

        eb = tk.Frame(sr, bg=T.RED, padx=2, pady=2)
        eb.pack(side="left")
        ei = tk.Frame(eb, bg=T.INPUT)
        ei.pack()
        tk.Label(ei, text=" 🔍", font=("Segoe UI", 13),
                 bg=T.INPUT, fg=T.TXT3).pack(side="left")
        self.entry = tk.Entry(ei, font=("Segoe UI", 13), width=35,
                              bg=T.INPUT, fg=T.TXT,
                              insertbackground=T.RED,
                              relief="flat", border=0)
        self.entry.pack(side="left", ipady=8, padx=(5, 12))
        self.entry.insert(0, "Oyun adı yazın...")
        self.entry.config(fg=T.TXT3)
        self.entry.bind("<FocusIn>", self._fi)
        self.entry.bind("<FocusOut>", self._fo)
        self.entry.bind("<Return>", lambda e: self.search())

        Btn(sr, "Ara", "🔍", self.search,
            T.RED, T.RED2, 12).pack(side="left", padx=(8, 4))
        Btn(sr, "Popüler", "🔥", self.home,
            T.BLUE2, "#6b44a0", 11).pack(side="left", padx=4)

        # STATUS
        sf = tk.Frame(self.root, bg=T.BG)
        sf.pack(fill="x", padx=25, pady=(8, 0))
        self.status = Status(sf, text="🎮  Hoş geldiniz! Bir oyun arayın.",
                             font=("Segoe UI", 10), bg=T.BG,
                             fg=T.TXT2, anchor="w")
        self.status.pack(side="left")
        self.cnt = tk.Label(sf, text="", font=("Segoe UI", 10, "bold"),
                            bg=T.BG, fg=T.RED)
        self.cnt.pack(side="right")

        # PROGRESS
        sty = ttk.Style()
        sty.theme_use("clam")
        sty.configure("r.Horizontal.TProgressbar",
                       troughcolor=T.BG2, background=T.RED,
                       darkcolor=T.RED, lightcolor=T.RED2, borderwidth=0)
        self.prog = ttk.Progressbar(self.root, style="r.Horizontal.TProgressbar",
                                     mode="indeterminate")

        # CONTENT
        cf = tk.Frame(self.root, bg=T.BG)
        cf.pack(fill="both", expand=True, padx=25, pady=(8, 0))

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
        self.cv.bind("<Configure>", lambda e: self.cv.itemconfig(self.iid, width=e.width))
        self.inner.bind("<Configure>", lambda e: self.cv.configure(scrollregion=self.cv.bbox("all")))

        self.cv.bind("<Enter>", lambda e: self.cv.bind_all("<MouseWheel>", self._wh))
        self.cv.bind("<Leave>", lambda e: self.cv.unbind_all("<MouseWheel>"))

        # FOOTER
        ft = tk.Frame(self.root, bg=T.HEADER, height=50)
        ft.pack(fill="x", side="bottom"); ft.pack_propagate(False)
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

    # =================== ARAMA ===================
    def search(self):
        q = self.entry.get().strip()
        if q == "Oyun adı yazın..." or not q:
            messagebox.showinfo("Bilgi", "Lütfen bir oyun adı girin!")
            return
        self.query = q
        self.page = 1
        self._do_search()

    def home(self):
        self.query = ""
        self.page = 1
        self._load("Ana sayfa yükleniyor", BASE + "/")

    def _do_search(self):
        q = urllib.parse.quote(self.query)
        url = f"{BASE}/page/{self.page}/?s={q}" if self.page > 1 else f"{BASE}/?s={q}"
        self._load(f"'{self.query}' aranıyor", url)

    def _load(self, msg, url):
        self.busy = True
        self.prog.pack(fill="x", padx=25, pady=(4, 0))
        self.prog.start(12)
        self.status.loading(msg)
        self.cnt.config(text="")
        threading.Thread(target=self._fetch, args=(url,), daemon=True).start()

    def _stop(self):
        self.busy = False
        self.prog.stop()
        self.prog.pack_forget()

    def _fetch(self, url):
        try:
            r = self.session.get(url, headers=UA, timeout=15)
            r.encoding = "utf-8"
            if r.status_code != 200:
                self.root.after(0, self._err, f"HTTP {r.status_code}")
                return
            soup = BeautifulSoup(r.text, "html.parser")
            games = self._parse(soup)
            self.root.after(0, self._show, games)
        except requests.exceptions.Timeout:
            self.root.after(0, self._err, "Zaman aşımı!")
        except requests.exceptions.ConnectionError:
            self.root.after(0, self._err, "İnternet bağlantısı yok!")
        except Exception as e:
            self.root.after(0, self._err, str(e))

    def _parse(self, soup):
        games = []
        arts = soup.find_all("article")
        if not arts:
            arts = soup.find_all("div", class_="post")
        if not arts:
            for a in soup.select("h2 a, h3 a, .post-title a, .entry-title a"):
                t, h = a.get_text(strip=True), a.get("href", "")
                if t and h and len(t) > 3:
                    games.append({"title": t, "url": h, "cat": "", "date": "", "desc": ""})
            return games

        for art in arts:
            try:
                g = {}
                tt = art.find("h2") or art.find("h3") or art.find("a")
                if tt:
                    a = tt.find("a") if tt.name != "a" else tt
                    if not a: a = art.find("a", href=True)
                    if a:
                        g["title"] = a.get_text(strip=True)
                        g["url"] = a.get("href", "")
                if not g.get("title") or not g.get("url"): continue

                c = art.find("span", class_="cat") or art.find("a", rel="category")
                g["cat"] = c.get_text(strip=True) if c else ""
                d = art.find("time") or art.find("span", class_="date")
                g["date"] = d.get_text(strip=True) if d else ""
                p = art.find("p")
                g["desc"] = p.get_text(strip=True)[:150] if p else ""
                games.append(g)
            except: continue
        return games

    # =================== SONUÇLAR ===================
    def _show(self, games):
        self._stop()
        for w in self.inner.winfo_children(): w.destroy()

        if not games:
            self.status.done("❌  Sonuç bulunamadı")
            f = tk.Frame(self.inner, bg=T.BG)
            f.pack(pady=80)
            tk.Label(f, text="😔", font=("Segoe UI", 50), bg=T.BG, fg=T.TXT3).pack()
            tk.Label(f, text="Sonuç Bulunamadı", font=("Segoe UI", 18, "bold"),
                     bg=T.BG, fg=T.TXT2).pack(pady=(10, 5))
            tk.Label(f, text="Farklı bir oyun adı deneyin",
                     font=("Segoe UI", 11), bg=T.BG, fg=T.TXT3).pack()
            return

        self.status.done(f"✅  {len(games)} oyun bulundu")
        self.cnt.config(text=f"Sayfa {self.page}  •  {len(games)} sonuç")
        self.plbl.config(text=f"Sayfa {self.page}")

        for i, g in enumerate(games):
            self._card(i, g)
        self.cv.yview_moveto(0)

    def _err(self, msg):
        self._stop()
        self.status.done(f"❌  {msg}")
        messagebox.showerror("Hata", msg)

    # =================== KART ===================
    def _card(self, idx, game):
        card = tk.Frame(self.inner, bg=T.CARD,
                        highlightbackground=T.BORDER, highlightthickness=1)
        card.pack(fill="x", padx=8, pady=4)

        row = tk.Frame(card, bg=T.CARD)
        row.pack(fill="x", padx=14, pady=11)

        # Numara
        nc = T.RED if idx % 2 == 0 else T.BLUE2
        nf = tk.Frame(row, bg=nc, width=36, height=36)
        nf.pack(side="left", padx=(0, 14)); nf.pack_propagate(False)
        tk.Label(nf, text=str(idx+1), font=("Segoe UI", 12, "bold"),
                 fg=T.TXT, bg=nc).place(relx=.5, rely=.5, anchor="center")

        # Bilgiler
        info = tk.Frame(row, bg=T.CARD)
        info.pack(side="left", fill="both", expand=True)
        tk.Label(info, text=game["title"], font=("Segoe UI", 12, "bold"),
                 fg=T.TXT, bg=T.CARD, anchor="w",
                 wraplength=480, justify="left").pack(anchor="w")

        meta = tk.Frame(info, bg=T.CARD)
        meta.pack(anchor="w", pady=(2, 0))
        if game.get("cat"):
            tk.Label(meta, text=f"📁 {game['cat']}", font=("Segoe UI", 9),
                     fg=T.RED, bg=T.CARD).pack(side="left", padx=(0, 12))
        if game.get("date"):
            tk.Label(meta, text=f"📅 {game['date']}", font=("Segoe UI", 9),
                     fg=T.TXT3, bg=T.CARD).pack(side="left")

        if game.get("desc"):
            d = game["desc"][:90] + "..." if len(game["desc"]) > 90 else game["desc"]
            tk.Label(info, text=d, font=("Segoe UI", 9),
                     fg=T.TXT3, bg=T.CARD, anchor="w",
                     wraplength=480, justify="left").pack(anchor="w", pady=(2, 0))

        # Butonlar
        bf = tk.Frame(row, bg=T.CARD)
        bf.pack(side="right", padx=(12, 0))
        Btn(bf, "Detay", "🔍", lambda g=game: self._detail(g),
            T.BLUE, T.BLUE2, 10).pack(pady=(0, 4))
        Btn(bf, "İndir", "⬇️", lambda g=game: self._download(g),
            T.GREEN2, T.GREEN, 10).pack()

        card.bind("<Enter>", lambda e, c=card: c.config(highlightbackground=T.RED, highlightthickness=2))
        card.bind("<Leave>", lambda e, c=card: c.config(highlightbackground=T.BORDER, highlightthickness=1))

    # =================== DETAY ===================
    def _detail(self, game):
        win = tk.Toplevel(self.root)
        win.title(f"🎮 {game.get('title', '')}")
        win.geometry("720x580")
        win.configure(bg=T.BG)

        hdr = tk.Frame(win, bg=T.CARD)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"🎮  {game.get('title', '')}",
                 font=("Segoe UI", 14, "bold"), fg=T.TXT, bg=T.CARD,
                 wraplength=680, anchor="w").pack(fill="x", padx=20, pady=15)

        load = Status(win, text="", font=("Segoe UI", 11),
                       fg=T.RED, bg=T.BG)
        load.pack(pady=6)
        load.loading("Detaylar yükleniyor")

        # Text
        tf = tk.Frame(win, bg=T.BG)
        tf.pack(fill="both", expand=True, padx=20, pady=(0, 8))

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

        # Mouse wheel SADECE bu text üzerinde
        def _tw(e):
            txt.yview_scroll(int(-1 * (e.delta / 120)), "units")
        txt.bind("<Enter>", lambda e: txt.bind_all("<MouseWheel>", _tw))
        txt.bind("<Leave>", lambda e: txt.unbind_all("<MouseWheel>"))

        # Butonlar
        bf = tk.Frame(win, bg=T.BG)
        bf.pack(fill="x", padx=20, pady=(0, 12))
        Btn(bf, "Sayfayı Aç", "🌐",
            lambda: webbrowser.open(game.get("url", "")),
            T.BLUE, T.BLUE2).pack(side="left", padx=(0, 8))
        Btn(bf, "İndir", "⬇️",
            lambda: self._download(game),
            T.GREEN2, T.GREEN).pack(side="left")
        Btn(bf, "Kapat", "✖", win.destroy,
            T.RED, "#ff4466").pack(side="right")

        def fetch():
            try:
                r = self.session.get(game["url"], headers=UA, timeout=15)
                r.encoding = "utf-8"
                soup = BeautifulSoup(r.text, "html.parser")

                content = ""
                alt_links = []

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

                    # Alternatif linkleri bul
                    for a in div.find_all("a", href=True):
                        href = a.get("href", "").strip()
                        atxt = a.get_text(strip=True)
                        atxt_low = atxt.lower()

                        is_alt = any(k in atxt_low for k in [
                            "alternatif", "alternative", "link",
                            "indir", "download", "torrent", "magnet",
                            "google drive", "mega", "mediafire",
                            "yandex", "uptobox", "part",
                        ])
                        is_host = any(h in href.lower() for h in [
                            "mega.nz", "mediafire", "drive.google",
                            "yandex", "uptobox", "rapidgator",
                            "1fichier", "turbobit",
                        ])

                        if (is_alt or is_host) and href.startswith("http"):
                            if BASE.replace("https://www.", "") not in href or "indir" in href.lower():
                                alt_links.append({"text": atxt or href, "url": href})

                # Tekrarları kaldır
                seen = set()
                unique_links = []
                for l in alt_links:
                    if l["url"] not in seen:
                        seen.add(l["url"])
                        unique_links.append(l)

                if not content.strip():
                    content = "  Detay bilgisi bulunamadı."

                win.after(0, lambda: show(content, unique_links))
            except Exception as ex:
                win.after(0, lambda: show(f"  Hata: {ex}", []))

        def show(text, alt_links):
            load.done("")
            txt.config(state="normal")
            txt.delete("1.0", "end")

            txt.tag_configure("title", font=("Segoe UI", 14, "bold"), foreground=T.RED)
            txt.tag_configure("body", font=("Segoe UI", 11), foreground=T.TXT)
            txt.tag_configure("link_tag", font=("Segoe UI", 11, "bold"),
                               foreground=T.GREEN, underline=True)

            txt.insert("end", f"🎮 {game.get('title', '')}\n\n", "title")
            if game.get("cat"):
                txt.insert("end", f"  📁 Kategori: {game['cat']}\n", "body")
            if game.get("date"):
                txt.insert("end", f"  📅 Tarih: {game['date']}\n", "body")
            txt.insert("end", "\n" + "─" * 50 + "\n\n", "body")
            txt.insert("end", text, "body")

            # Alternatif linkler - tıklanabilir
            if alt_links:
                txt.insert("end", "\n\n" + "━" * 50 + "\n", "body")
                txt.insert("end", "  ⬇️  ALTERNATİF İNDİRME LİNKLERİ\n", "title")
                txt.insert("end", "━" * 50 + "\n\n", "body")

                for i, link in enumerate(alt_links):
                    tag_name = f"alink_{i}"
                    url = link["url"]

                    # İkon belirle
                    lt = link["text"].lower()
                    icon = "🔗"
                    if "mega" in lt or "mega" in url.lower(): icon = "☁️"
                    elif "drive" in lt or "google" in url.lower(): icon = "📁"
                    elif "mediafire" in lt or "mediafire" in url.lower(): icon = "🔥"
                    elif "torrent" in lt or "magnet" in lt: icon = "🧲"
                    elif "yandex" in lt or "yandex" in url.lower(): icon = "💿"

                    display = f"  {icon}  <<< {link['text']} >>>\n\n"

                    txt.tag_configure(tag_name,
                                      font=("Segoe UI", 12, "bold"),
                                      foreground=T.GREEN,
                                      underline=True)

                    # Hover efekti
                    txt.tag_bind(tag_name, "<Enter>",
                                  lambda e, tn=tag_name: txt.tag_configure(tn, foreground=T.GOLD))
                    txt.tag_bind(tag_name, "<Leave>",
                                  lambda e, tn=tag_name: txt.tag_configure(tn, foreground=T.GREEN))
                    # Tıklama
                    txt.tag_bind(tag_name, "<Button-1>",
                                  lambda e, u=url: webbrowser.open(u))

                    txt.insert("end", display, tag_name)

                txt.insert("end", "─" * 50 + "\n", "body")
                txt.insert("end", f"  Toplam {len(alt_links)} alternatif link\n", "body")

            txt.config(state="disabled")

        threading.Thread(target=fetch, daemon=True).start()

    # =================== İNDİRME (SADECE ALTERNATİF) ===================
    def _download(self, game):
        self.status.loading("Alternatif linkler aranıyor")

        def fetch():
            try:
                r = self.session.get(game["url"], headers=UA, timeout=15)
                r.encoding = "utf-8"
                soup = BeautifulSoup(r.text, "html.parser")

                links = []
                div = (soup.find("div", class_="entry-content")
                       or soup.find("div", class_="post-content")
                       or soup.find("article")
                       or soup)

                for a in div.find_all("a", href=True):
                    href = a.get("href", "").strip()
                    atxt = a.get_text(strip=True)
                    atxt_low = atxt.lower()

                    is_alt = any(k in atxt_low for k in [
                        "alternatif", "alternative", "link",
                        "indir", "download", "torrent", "magnet",
                        "google drive", "mega", "mediafire",
                        "yandex", "uptobox", "part",
                    ])
                    is_host = any(h in href.lower() for h in [
                        "mega.nz", "mediafire", "drive.google",
                        "yandex", "uptobox", "rapidgator",
                        "1fichier", "turbobit", "hitfile",
                    ])

                    if (is_alt or is_host) and href.startswith("http"):
                        if BASE.replace("https://www.", "") not in href or "indir" in href.lower():
                            links.append({"text": atxt or href, "url": href})

                seen = set()
                unique = []
                for l in links:
                    if l["url"] not in seen:
                        seen.add(l["url"])
                        unique.append(l)

                self.root.after(0, lambda: self._dlg(game, unique))
            except Exception as ex:
                self.root.after(0, lambda: self._err(str(ex)))

        threading.Thread(target=fetch, daemon=True).start()

    def _dlg(self, game, links):
        self.status.done("✅  Hazır")

        if not links:
            if messagebox.askyesno("Bilgi",
                                    "Alternatif link bulunamadı.\nOyun sayfasını açmak ister misiniz?"):
                webbrowser.open(game.get("url", ""))
            return

        win = tk.Toplevel(self.root)
        win.title("⬇️  Alternatif Linkler")
        win.geometry("580x460")
        win.configure(bg=T.BG)
        win.resizable(False, True)

        # Header
        hdr = tk.Frame(win, bg=T.CARD)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⬇️  Alternatif İndirme Linkleri",
                 font=("Segoe UI", 14, "bold"),
                 fg=T.TXT, bg=T.CARD).pack(pady=(12, 3), padx=20, anchor="w")

        t = game.get("title", "")
        if len(t) > 55: t = t[:55] + "..."
        tk.Label(hdr, text=t, font=("Segoe UI", 10),
                 fg=T.TXT2, bg=T.CARD).pack(padx=20, anchor="w")
        tk.Label(hdr, text=f"📦  {len(links)} alternatif link bulundu",
                 font=("Segoe UI", 10, "bold"),
                 fg=T.GREEN, bg=T.CARD).pack(pady=(3, 10), padx=20, anchor="w")

        # Liste
        lf = tk.Frame(win, bg=T.BG)
        lf.pack(fill="both", expand=True, padx=12, pady=8)

        lc = tk.Canvas(lf, bg=T.BG, highlightthickness=0, bd=0)
        ls = tk.Scrollbar(lf, orient="vertical", command=lc.yview,
                           bg=T.BG2, troughcolor=T.BG,
                           activebackground=T.RED,
                           highlightthickness=0, bd=0, width=8)
        li = tk.Frame(lc, bg=T.BG)
        li.bind("<Configure>", lambda e: lc.configure(scrollregion=lc.bbox("all")))
        lid = lc.create_window((0, 0), window=li, anchor="nw")
        lc.configure(yscrollcommand=ls.set)
        lc.bind("<Configure>", lambda e: lc.itemconfig(lid, width=e.width))
        ls.pack(side="right", fill="y")
        lc.pack(side="left", fill="both", expand=True)

        def _lwh(e): lc.yview_scroll(int(-1*(e.delta/120)), "units")
        lc.bind("<Enter>", lambda e: lc.bind_all("<MouseWheel>", _lwh))
        lc.bind("<Leave>", lambda e: lc.unbind_all("<MouseWheel>"))

        for i, link in enumerate(links):
            row = tk.Frame(li, bg=T.CARD,
                           highlightbackground=T.BORDER, highlightthickness=1)
            row.pack(fill="x", pady=3)

            inf = tk.Frame(row, bg=T.CARD)
            inf.pack(side="left", fill="x", expand=True, padx=12, pady=8)

            lt = link["text"].lower()
            icon = "🔗"
            if "mega" in lt or "mega" in link["url"].lower(): icon = "☁️"
            elif "drive" in lt or "google" in link["url"].lower(): icon = "📁"
            elif "mediafire" in lt or "mediafire" in link["url"].lower(): icon = "🔥"
            elif "torrent" in lt: icon = "🧲"
            elif "yandex" in lt: icon = "💿"

            tk.Label(inf, text=f"{icon}  Alternatif: {link['text']}",
                     font=("Segoe UI", 10, "bold"),
                     fg=T.TXT, bg=T.CARD, anchor="w",
                     wraplength=350).pack(anchor="w")

            su = link["url"][:50] + "..." if len(link["url"]) > 50 else link["url"]
            tk.Label(inf, text=su, font=("Segoe UI", 8),
                     fg=T.TXT3, bg=T.CARD, anchor="w").pack(anchor="w", pady=(2, 0))

            u = link["url"]
            Btn(row, "Aç", "🔗", lambda url=u: webbrowser.open(url),
                T.GREEN2, T.GREEN, 10).pack(side="right", padx=10, pady=6)

        # Alt butonlar
        bf = tk.Frame(win, bg=T.BG)
        bf.pack(fill="x", padx=12, pady=(0, 12))
        Btn(bf, "Hepsini Aç", "🚀",
            lambda: [webbrowser.open(l["url"]) for l in links[:5]],
            T.ORANGE, T.GOLD, 10).pack(side="left", padx=(0, 8))
        Btn(bf, "Kapat", "✖", win.destroy,
            T.RED, "#ff4466", 10).pack(side="right")

    # =================== SAYFALAMA ===================
    def pnext(self):
        if self.busy: return
        self.page += 1
        self.plbl.config(text=f"Sayfa {self.page}")
        if self.query:
            self._do_search()
        else:
            self._load("Sayfa yükleniyor", f"{BASE}/page/{self.page}/")

    def pprev(self):
        if self.busy or self.page <= 1: return
        self.page -= 1
        self.plbl.config(text=f"Sayfa {self.page}")
        if self.query:
            self._do_search()
        else:
            url = f"{BASE}/page/{self.page}/" if self.page > 1 else BASE + "/"
            self._load("Sayfa yükleniyor", url)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()