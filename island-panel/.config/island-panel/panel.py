#!/usr/bin/env python3
"""
Island panel: rozbalovací panel pro Hyprland ve stylu ostrůvků Waybaru.

Najetím kurzoru na horní okraj obrazovky (uprostřed) panel vyjede dolů,
po odjetí kurzoru se zase schová. Záložky: Dashboard, Media, Performance, Apps.

Najetím na pravý okraj (uprostřed výšky) vyjede úzký boční panel
s hlasitostí a jasem. Když kurzor na okraji zůstane asi vteřinu, otevře se
ovládací centrum: oznámení, otevřená okna, rychlé přepínače a vypnutí.

Přepínač tapet (--wallpapers) ukáže přes celou šířku obrazovky pás náhledů
ze složky s tapetami; vybraná se nastaví Enterem nebo kliknutím.

Spuštění:   python3 panel.py            (běží na pozadí)
Ovládání:   python3 panel.py --toggle   (otevřít / zavřít, třeba z klávesové zkratky)
            python3 panel.py --apps     (otevřít rovnou na seznamu aplikací s hledáním)
            python3 panel.py --side     (otevřít / zavřít boční panel s hlasitostí a jasem)
            python3 panel.py --center   (otevřít / zavřít ovládací centrum)
            python3 panel.py --wallpapers        (otevřít / zavřít přepínač tapet)
            python3 panel.py --wallpaper-next    (další tapeta bez otevírání přepínače)
            python3 panel.py --wallpaper-prev    (předchozí tapeta)
            python3 panel.py --wallpaper-random  (náhodná tapeta)
            python3 panel.py --quit     (ukončit)

Vzhled se upravuje v souboru style.css vedle tohoto skriptu, změny se načtou samy.
"""

import calendar
import colorsys
import datetime
import getpass
import hashlib
import html
import json
import math
import os
import random
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.parse
import urllib.request

import cairo
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk, GtkLayerShell, Pango, PangoCairo  # noqa: E402

# ----------------------------------------------------------------------------
# Nastavení
# ----------------------------------------------------------------------------
PANEL_WIDTH = 680        # šířka panelu v pixelech
TRIGGER_WIDTH = 680      # šířka citlivého pruhu u horního okraje (je uprostřed)
TRIGGER_HEIGHT = 3       # výška citlivého pruhu
OPEN_DELAY_MS = 120      # jak dlouho musí kurzor na pruhu zůstat, než panel vyjede
CLOSE_DELAY_MS = 350     # za jak dlouho po odjetí kurzoru se panel schová

SIDE_ENABLED = True      # boční panel s hlasitostí a jasem u pravého okraje
SIDE_TRIGGER_HEIGHT = 320  # výška citlivého pruhu u pravého okraje (je uprostřed výšky)
SIDE_TRIGGER_WIDTH = 3     # šířka citlivého pruhu
SLIDER_HEIGHT = 130      # výška posuvníků v bočním panelu
SIDE_OPEN_DELAY_MS = 300   # po jak dlouhé době na pravém okraji vyjede hlasitost a jas

CENTER_ENABLED = True      # ovládací centrum u pravého okraje
CENTER_OPEN_DELAY_MS = 1000  # po jak dlouhé době na pravém okraji se otevře ovládací centrum
CENTER_WIDTH = 380         # šířka ovládacího centra
WINDOW_LIST_HEIGHT = 230   # největší výška seznamu oken, pak se posouvá

NOTIFICATIONS_ENABLED = True  # panel přijímá systémová oznámení a ukazuje je (False = nechat jinému programu)
TOAST_SECONDS = 6          # jak dlouho zůstane bublina s novým oznámením
TOAST_WIDTH = 340          # šířka bubliny
TOAST_TOP_MARGIN = 50      # odsazení bublin od horního okraje (pod lištou)

# O kolik pixelů přesahují okna u pravého okraje za hranu obrazovky. Kurzor dotlačený
# až na pravý okraj má souřadnici přesně rovnou šířce okna a GTK by ho pak bralo jako
# "mimo okno", takže by panel nevyjel. S přesahem je kurzor vždy uvnitř.
EDGE_OVERHANG = 2

WALL_ENABLED = True          # přepínač tapet (panel.py --wallpapers)
WALLPAPER_DIRS = ["~/Pictures/wallpapers"]   # složky s tapetami, prohledávají se i podsložky
WALL_CARD_W, WALL_CARD_H = 92, 250   # šířka a výška úzkých náhledů
WALL_BIG_W, WALL_BIG_H = 430, 300    # šířka a výška vybraného náhledu uprostřed
WALL_GAP = 8                 # mezera mezi náhledy
WALL_SLANT = 0.20            # zkosení náhledů: 0 = rovné, záporné číslo = nakloněné na druhou stranu
WALL_RADIUS = 10             # zaoblení rohů náhledů
WALL_DIM = 0.35              # ztmavení plochy pod přepínačem (0 = žádné, 1 = černá)
WALL_SHADE = 0.45            # o kolik jsou nevybrané náhledy tmavší než vybraný (0 = stejně světlé)
WALL_EDGE_FADE = 120         # jak daleko od krajů obrazovky se náhledy začnou ztrácet (0 = vůbec)
WALL_TAGS = True             # štítky PIC / VID v rohu náhledů
WALL_FILL_MODE = "fill"      # jak se obrázek na plochu umístí: fill, fit, stretch, center, tile
WALL_VIDEO_OPTIONS = "no-audio loop"   # volby přehrávače u video tapet (ty potřebují program mpvpaper)

WEATHER_ENABLED = True   # False = počasí se nestahuje vůbec
WEATHER_CITY = ""        # např. "Praha"; prázdné = služba odhadne místo podle IP adresy
WEATHER_URL = "https://wttr.in/{city}?format=j1&lang=cs"

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(GLib.get_user_cache_dir(), "island-panel")
STATE_DIR = os.path.join(os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"), "island-panel")

# Ikony z Nerd Fontu (zapsané kódem, aby se při kopírování neztratily)
I = {
    "dashboard": "\uf009", "media": "\uf001", "performance": "\uf0e4", "apps": "\uf00a",
    "cpu": "\uf2db", "ram": "\uf233", "disk": "\uf0a0", "temp": "\uf2c9",
    "user": "\uf007", "desktop": "\uf108", "clock": "\uf017", "distro": "\uf30a",
    "bat": ["\uf244", "\uf243", "\uf242", "\uf241", "\uf240"], "plug": "\uf1e6",
    "prev": "\uf048", "play": "\uf04b", "pause": "\uf04c", "next": "\uf051",
    "left": "\uf053", "right": "\uf054", "search": "\uf002", "music": "\uf001",
    "vol_high": "\uf028", "vol_low": "\uf027", "vol_off": "\uf026", "sun": "\uf185",
    "lock": "\uf023", "moon": "\uf186", "signout": "\uf08b", "refresh": "\uf021", "power": "\uf011",
    "wifi": "\uf1eb", "bt": "\uf293", "mic": "\uf130", "mic_off": "\uf131",
    "bell": "\uf0f3", "bell_off": "\uf1f6", "coffee": "\uf0f4", "times": "\uf00d", "trash": "\uf1f8",
    "image": "\uf03e", "film": "\uf008", "shuffle": "\uf074", "folder": "\uf07c", "check": "\uf00c",
    "w_sun": "\ue30d", "w_moon": "\ue32b", "w_partly": "\ue302", "w_cloud": "\ue312",
    "w_fog": "\ue313", "w_rain": "\ue318", "w_snow": "\ue31a", "w_storm": "\ue31d",
}

MONTHS = ["Leden", "Únor", "Březen", "Duben", "Květen", "Červen", "Červenec",
          "Srpen", "Září", "Říjen", "Listopad", "Prosinec"]
WEEKDAYS = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]


# ----------------------------------------------------------------------------
# Pomocné funkce
# ----------------------------------------------------------------------------
def read(path, default=""):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except OSError:
        return default


def css(widget, *classes):
    ctx = widget.get_style_context()
    for c in classes:
        ctx.add_class(c)
    return widget


def set_class(widget, name, on):
    ctx = widget.get_style_context()
    (ctx.add_class if on else ctx.remove_class)(name)


def label(text="", *classes, xalign=0.5, ellipsize=False, lines=1):
    lab = Gtk.Label(label=text, xalign=xalign)
    if ellipsize:
        lab.set_ellipsize(Pango.EllipsizeMode.END)
        lab.set_max_width_chars(1)
        if lines > 1:
            lab.set_line_wrap(True)
            lab.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            lab.set_lines(lines)
            lab.set_justify(Gtk.Justification.CENTER)
    return css(lab, *classes)


def hbox(spacing=0, *classes):
    return css(Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=spacing), *classes)


def vbox(spacing=0, *classes):
    return css(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=spacing), *classes)


def fmt_duration(seconds):
    seconds = int(seconds)
    d, h, m = seconds // 86400, seconds % 86400 // 3600, seconds % 3600 // 60
    if d:
        return f"{d} d {h} h"
    if h:
        return f"{h} h {m} min"
    return f"{m} min"


def fmt_time(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


# ----------------------------------------------------------------------------
# Data: systém
# ----------------------------------------------------------------------------
def find_temp_sensor():
    """Najde čidlo teploty procesoru (číslo hwmon se mezi starty mění, proto podle jména)."""
    base = "/sys/class/hwmon"
    found = {}
    try:
        for entry in sorted(os.listdir(base)):
            name = read(f"{base}/{entry}/name")
            if os.path.exists(f"{base}/{entry}/temp1_input"):
                found.setdefault(name, f"{base}/{entry}/temp1_input")
    except OSError:
        pass
    for name in ("coretemp", "k10temp", "zenpower", "cpu_thermal", "thinkpad", "acpitz"):
        if name in found:
            return found[name]
    if found:
        return next(iter(found.values()))
    zone = "/sys/class/thermal/thermal_zone0/temp"
    return zone if os.path.exists(zone) else None


class Stats:
    def __init__(self):
        self.cpu = 0.0
        self.history = [0.0] * 60
        self._prev = None
        self.temp_path = find_temp_sensor()
        self.sample()

    def sample(self):
        try:
            vals = [int(v) for v in read("/proc/stat").splitlines()[0].split()[1:9]]
        except (IndexError, ValueError):
            return
        total, idle = sum(vals), vals[3] + vals[4]
        if self._prev and total > self._prev[0]:
            self.cpu = 100.0 * (1 - (idle - self._prev[1]) / (total - self._prev[0]))
        self._prev = (total, idle)
        self.history = self.history[1:] + [self.cpu]

    @staticmethod
    def ram():
        info = {}
        for line in read("/proc/meminfo").splitlines():
            key, _, rest = line.partition(":")
            if key in ("MemTotal", "MemAvailable"):
                info[key] = int(rest.split()[0])
        total, avail = info.get("MemTotal", 0), info.get("MemAvailable", 0)
        used = total - avail
        return used / 1048576, total / 1048576, (100.0 * used / total if total else 0.0)

    @staticmethod
    def disk():
        try:
            st = os.statvfs("/")
        except OSError:
            return 0.0, 0.0, 0.0
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        used = total - free
        return used / 1e9, total / 1e9, (100.0 * used / total if total else 0.0)

    def temp(self):
        if not self.temp_path:
            return None
        try:
            return int(read(self.temp_path)) / 1000.0
        except ValueError:
            return None

    @staticmethod
    def battery():
        base = "/sys/class/power_supply"
        try:
            bats = sorted(e for e in os.listdir(base) if e.startswith("BAT"))
        except OSError:
            return None
        if not bats:
            return None
        try:
            return int(read(f"{base}/{bats[0]}/capacity")), read(f"{base}/{bats[0]}/status")
        except ValueError:
            return None

    @staticmethod
    def uptime():
        try:
            return float(read("/proc/uptime").split()[0])
        except (IndexError, ValueError):
            return 0.0


class ProcTop:
    """Procesy seřazené podle vytížení procesoru za poslední interval (sečtené podle jména)."""

    def __init__(self):
        self.hz = os.sysconf("SC_CLK_TCK")
        self.page = os.sysconf("SC_PAGE_SIZE")
        self.ncpu = os.cpu_count() or 1
        self.prev, self.prev_t, self.rows = {}, None, []

    def sample(self):
        now, cur = time.monotonic(), {}
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                with open(f"/proc/{pid}/stat", encoding="utf-8", errors="replace") as f:
                    data = f.read()
                close = data.rfind(")")
                fields = data[close + 2:].split()
                cur[pid] = (data[data.find("(") + 1:close], int(fields[11]) + int(fields[12]), int(fields[21]))
            except (OSError, IndexError, ValueError):
                continue
        if self.prev_t is not None and now > self.prev_t:
            dt, agg = now - self.prev_t, {}
            for pid, (name, ticks, rss) in cur.items():
                old = self.prev.get(pid)
                cpu = (ticks - old[1]) / self.hz / dt * 100 / self.ncpu if old and old[0] == name else 0.0
                entry = agg.setdefault(name, [0.0, 0])
                entry[0] += cpu
                entry[1] += rss
            rows = [(n, c, r * self.page / 1048576) for n, (c, r) in agg.items()]
            self.rows = sorted(rows, key=lambda row: (-row[1], -row[2]))[:5]
        self.prev, self.prev_t = cur, now


# ----------------------------------------------------------------------------
# Data: přehrávače (MPRIS přes D-Bus, funguje se Spotify, prohlížeči, VLC, ...)
# ----------------------------------------------------------------------------
class Mpris:
    PREFIX = "org.mpris.MediaPlayer2."
    PATH = "/org/mpris/MediaPlayer2"

    def __init__(self):
        try:
            self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except GLib.Error:
            self.bus = None
        self.current = None

    def _call(self, dest, path, iface, method, args=None):
        return self.bus.call_sync(dest, path, iface, method, args, None, Gio.DBusCallFlags.NONE, 250, None)

    def poll(self):
        """Vrátí informace o přehrávači (přednost má ten, který právě hraje), nebo None."""
        self.current = None
        if not self.bus:
            return None
        try:
            names = self._call("org.freedesktop.DBus", "/org/freedesktop/DBus",
                               "org.freedesktop.DBus", "ListNames").unpack()[0]
        except GLib.Error:
            return None
        best = None
        for name in sorted(n for n in names if n.startswith(self.PREFIX)):
            try:
                props = self._call(name, self.PATH, "org.freedesktop.DBus.Properties", "GetAll",
                                   GLib.Variant("(s)", ("org.mpris.MediaPlayer2.Player",))).unpack()[0]
            except GLib.Error:
                continue
            meta = props.get("Metadata") or {}
            artist = meta.get("xesam:artist") or ""
            if isinstance(artist, (list, tuple)):
                artist = ", ".join(str(a) for a in artist)
            info = {
                "bus": name,
                "player": name[len(self.PREFIX):].split(".")[0].capitalize(),
                "playing": props.get("PlaybackStatus") == "Playing",
                "title": str(meta.get("xesam:title") or ""),
                "artist": str(artist),
                "album": str(meta.get("xesam:album") or ""),
                "art": str(meta.get("mpris:artUrl") or ""),
                "length": (meta.get("mpris:length") or 0) / 1e6,
                "position": (props.get("Position") or 0) / 1e6,
            }
            if not (info["title"] or info["artist"]):
                continue
            if info["playing"]:
                best = info
                break
            best = best or info
        self.current = best["bus"] if best else None
        return best

    def command(self, method):
        if self.bus and self.current:
            self.bus.call(self.current, self.PATH, "org.mpris.MediaPlayer2.Player", method,
                          None, None, Gio.DBusCallFlags.NONE, 500, None, None, None)


# ----------------------------------------------------------------------------
# Data: počasí
# ----------------------------------------------------------------------------
def weather_icon(code, hour):
    code = int(code)
    if code == 113:
        return I["w_sun"] if 6 <= hour < 20 else I["w_moon"]
    if code == 116:
        return I["w_partly"]
    if code in (119, 122):
        return I["w_cloud"]
    if code in (143, 248, 260):
        return I["w_fog"]
    if code in (200, 386, 389, 392, 395):
        return I["w_storm"]
    if code in (179, 182, 185, 227, 230, 281, 284, 311, 314, 317, 320, 323, 326, 329, 332, 335,
                338, 350, 362, 365, 368, 371, 374, 377):
        return I["w_snow"]
    return I["w_rain"]


def fetch_weather():
    """Stáhne aktuální počasí. Vrací (ikona, teplota, popis, místo) nebo None."""
    url = WEATHER_URL.format(city=urllib.parse.quote(WEATHER_CITY))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        cur = data["current_condition"][0]
        desc = (cur.get("lang_cs") or cur.get("weatherDesc") or [{}])[0].get("value", "")
        area = data.get("nearest_area", [{}])[0].get("areaName", [{}])[0].get("value", "")
        icon = weather_icon(cur.get("weatherCode", 113), datetime.datetime.now().hour)
        return icon, f"{cur['temp_C']}°C", desc.strip(), WEATHER_CITY or area
    except Exception:  # síť nemusí být dostupná, panel musí fungovat i bez ní
        return None


# ----------------------------------------------------------------------------
# Kreslené prvky
# ----------------------------------------------------------------------------
class Gauge(Gtk.DrawingArea):
    """Kruhový ukazatel 0-100 % s textem nebo ikonou uprostřed."""

    def __init__(self, size, center="", thickness=5):
        super().__init__()
        self.value, self.center, self.thickness = 0.0, center, thickness
        self.set_size_request(size, size)
        self.set_halign(Gtk.Align.CENTER)
        css(self, "gauge")
        self.connect("draw", self.on_draw)

    def set(self, value, center=None):
        value = max(0.0, min(100.0, value or 0.0))
        if center is not None:
            self.center = center
        self.value = value
        set_class(self, "high", value >= 85)
        self.queue_draw()

    def on_draw(self, _widget, cr):
        w, h = self.get_allocated_width(), self.get_allocated_height()
        fg = self.get_style_context().get_color(Gtk.StateFlags.NORMAL)
        radius = min(w, h) / 2 - self.thickness
        start, sweep = math.radians(135), math.radians(270)
        cr.set_line_width(self.thickness)
        cr.set_line_cap(1)  # zaoblené konce
        cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.13)
        cr.arc(w / 2, h / 2, radius, start, start + sweep)
        cr.stroke()
        if self.value > 0.5:
            cr.set_source_rgba(fg.red, fg.green, fg.blue, fg.alpha)
            cr.arc(w / 2, h / 2, radius, start, start + sweep * self.value / 100)
            cr.stroke()
        if self.center:
            layout = self.create_pango_layout(self.center)
            tw, th = layout.get_pixel_size()
            cr.move_to((w - tw) / 2, (h - th) / 2)
            cr.set_source_rgba(fg.red, fg.green, fg.blue, fg.alpha)
            PangoCairo.show_layout(cr, layout)
        return False


class Sparkline(Gtk.DrawingArea):
    """Graf průběhu (hodnoty 0-100)."""

    def __init__(self, height=64):
        super().__init__()
        self.values = []
        self.set_size_request(-1, height)
        self.set_hexpand(True)
        css(self, "sparkline")
        self.connect("draw", self.on_draw)

    def set(self, values):
        self.values = list(values)
        self.queue_draw()

    def on_draw(self, _widget, cr):
        w, h = self.get_allocated_width(), self.get_allocated_height()
        fg = self.get_style_context().get_color(Gtk.StateFlags.NORMAL)
        if len(self.values) < 2:
            return False
        step = w / (len(self.values) - 1)
        pts = [(i * step, h - 2 - (h - 6) * max(0, min(100, v)) / 100) for i, v in enumerate(self.values)]
        cr.move_to(0, h)
        for x, y in pts:
            cr.line_to(x, y)
        cr.line_to(w, h)
        cr.close_path()
        cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.12)
        cr.fill()
        cr.move_to(*pts[0])
        for x, y in pts[1:]:
            cr.line_to(x, y)
        cr.set_line_width(1.5)
        cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.9)
        cr.stroke()
        return False


class Art(Gtk.DrawingArea):
    """Obal alba se zaoblenými rohy, bez obalu ikona noty."""

    def __init__(self, size, radius=12):
        super().__init__()
        self.pixbuf, self.radius, self.url = None, radius, None
        self.set_size_request(size, size)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        css(self, "art")
        self.connect("draw", self.on_draw)

    def set_url(self, url):
        if url == self.url:
            return
        self.url, self.pixbuf = url, None
        self.queue_draw()
        if not url:
            return
        if url.startswith("file://"):
            self._load(url, urllib.parse.unquote(url[7:]))
        elif url.startswith(("http://", "https://")):
            path = os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest())
            if os.path.exists(path):
                self._load(url, path)
            else:
                threading.Thread(target=self._download, args=(url, path), daemon=True).start()

    def _download(self, url, path):
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            with urllib.request.urlopen(url, timeout=8) as resp:
                data = resp.read()
            with open(path + ".part", "wb") as f:
                f.write(data)
            os.replace(path + ".part", path)
            GLib.idle_add(self._load, url, path)
        except Exception:
            pass

    def _load(self, url, path):
        if url != self.url:
            return False
        try:
            self.pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
        except GLib.Error:
            self.pixbuf = None
        self.queue_draw()
        return False

    def on_draw(self, _widget, cr):
        w, h = self.get_allocated_width(), self.get_allocated_height()
        r = self.radius
        cr.new_sub_path()
        cr.arc(w - r, r, r, -math.pi / 2, 0)
        cr.arc(w - r, h - r, r, 0, math.pi / 2)
        cr.arc(r, h - r, r, math.pi / 2, math.pi)
        cr.arc(r, r, r, math.pi, 3 * math.pi / 2)
        cr.close_path()
        cr.clip()
        fg = self.get_style_context().get_color(Gtk.StateFlags.NORMAL)
        if self.pixbuf:
            pw, ph = self.pixbuf.get_width(), self.pixbuf.get_height()
            scale = max(w / pw, h / ph)
            cr.translate((w - pw * scale) / 2, (h - ph * scale) / 2)
            cr.scale(scale, scale)
            Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, 0, 0)
            cr.paint()
        else:
            cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.07)
            cr.paint()
            layout = self.create_pango_layout(I["music"])
            font = self.get_pango_context().get_font_description().copy()
            font.set_absolute_size(min(w, h) * 0.34 * Pango.SCALE)
            layout.set_font_description(font)
            tw, th = layout.get_pixel_size()
            cr.move_to((w - tw) / 2, (h - th) / 2)
            cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.45)
            PangoCairo.show_layout(cr, layout)
        return False


# ----------------------------------------------------------------------------
# Kalendář
# ----------------------------------------------------------------------------
class Calendar(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        css(self, "tile", "calendar")
        today = datetime.date.today()
        self.year, self.month = today.year, today.month

        head = hbox(0, "cal-head")
        prev_btn = css(Gtk.Button(label=I["left"]), "flat", "cal-nav")
        next_btn = css(Gtk.Button(label=I["right"]), "flat", "cal-nav")
        prev_btn.connect("clicked", lambda *_: self.shift(-1))
        next_btn.connect("clicked", lambda *_: self.shift(1))
        self.title = label("", "cal-title")
        self.title.set_hexpand(True)
        head.pack_start(prev_btn, False, False, 0)
        head.pack_start(self.title, True, True, 0)
        head.pack_start(next_btn, False, False, 0)
        self.pack_start(head, False, False, 0)

        self.grid = Gtk.Grid(column_homogeneous=True, row_homogeneous=True, row_spacing=1, column_spacing=1)
        self.grid.set_vexpand(True)
        for col, name in enumerate(WEEKDAYS):
            self.grid.attach(label(name, "cal-weekday"), col, 0, 1, 1)
        self.days = []
        for row in range(6):
            for col in range(7):
                day = label("", "cal-day")
                self.grid.attach(day, col, row + 1, 1, 1)
                self.days.append(day)
        self.pack_start(self.grid, True, True, 0)
        self.render()

    def shift(self, delta):
        month = self.month - 1 + delta
        self.year, self.month = self.year + month // 12, month % 12 + 1
        self.render()

    def reset(self):
        today = datetime.date.today()
        self.year, self.month = today.year, today.month
        self.render()

    def render(self):
        self.title.set_text(f"{MONTHS[self.month - 1]} {self.year}")
        today = datetime.date.today()
        dates = calendar.Calendar(firstweekday=0).itermonthdates(self.year, self.month)
        dates = list(dates)
        while len(dates) < 42:
            dates.append(dates[-1] + datetime.timedelta(days=1))
        for lab, date in zip(self.days, dates):
            lab.set_text(str(date.day))
            set_class(lab, "other", date.month != self.month)
            set_class(lab, "today", date == today)


# ----------------------------------------------------------------------------
# Panel
# ----------------------------------------------------------------------------
def layer_window(app, namespace, edge=GtkLayerShell.Edge.TOP, overhang=0):
    win = Gtk.Window(application=app)
    win.set_decorated(False)
    win.set_app_paintable(True)
    visual = win.get_screen().get_rgba_visual()
    if visual:
        win.set_visual(visual)
    if GtkLayerShell.is_supported():
        GtkLayerShell.init_for_window(win)
        GtkLayerShell.set_namespace(win, namespace)
        GtkLayerShell.set_layer(win, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_anchor(win, edge, True)
        if overhang:
            GtkLayerShell.set_margin(win, edge, -overhang)
        GtkLayerShell.set_exclusive_zone(win, -1)  # nad lištou, ne pod ní
    return win


class AutoHide:
    """Společné chování vysouvacích panelů: po odjetí kurzoru se panel schová.

    Třída, která ho používá, musí mít self.win, self.close_timer a metodu hide().
    """

    def watch_pointer(self):
        self.companions = []   # další okna, která se počítají jako "kurzor je pořád nad panelem"
        self.win.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.win.connect("enter-notify-event", self.on_enter)
        self.win.connect("leave-notify-event", self.on_leave)

    def close_unless_entered(self):
        """Po otevření najetím: když kurzor do panelu vůbec nevjede, zase ho schovat."""
        self.cancel_close()
        self.close_timer = GLib.timeout_add(1500, self.close_if_outside)

    def cancel_close(self):
        if self.close_timer is not None:
            GLib.source_remove(self.close_timer)
            self.close_timer = None

    def pointer_inside(self):
        """Je kurzor právě nad panelem? Ptáme se přímo, události enter/leave chodí i při klikání."""
        gdk_win = self.win.get_window()
        if gdk_win is None:
            return False
        pointer = gdk_win.get_display().get_default_seat().get_pointer()
        if pointer is None:
            return False
        under = pointer.get_window_at_position()[0]
        if under is None:
            return False
        top = under.get_toplevel()
        return top == gdk_win or any(top == c.get_window() for c in self.companions if c.get_window() is not None)

    def close_if_outside(self):
        self.close_timer = None
        if not self.pointer_inside():
            self.hide()
        return False

    def on_enter(self, _win, _event):
        self.cancel_close()
        return False

    def on_leave(self, _win, _event):
        self.cancel_close()
        self.close_timer = GLib.timeout_add(CLOSE_DELAY_MS, self.close_if_outside)
        return False


class Panel(AutoHide):
    TABS = [("dashboard", "Dashboard"), ("media", "Media"), ("performance", "Performance"), ("apps", "Apps")]

    def __init__(self, app):
        self.app = app
        self.stats, self.procs, self.mpris = Stats(), ProcTop(), Mpris()
        self.visible = False
        self.close_timer = self.tick_timer = None
        self.weather_at, self.weather_busy = 0.0, False
        self.apps_built = False
        self.media = None

        self.win = layer_window(app, "island-panel")
        self.watch_pointer()
        self.win.connect("key-press-event", self.on_key)
        self.win.connect("delete-event", lambda *_: self.hide() or True)

        root = vbox(0)
        root.set_name("panel")
        root.set_size_request(PANEL_WIDTH, -1)
        self.win.add(root)

        # --- záložky
        tabs = hbox(0, "tabs")
        tabs.set_homogeneous(True)
        self.tab_buttons = {}
        for name, title in self.TABS:
            btn = css(Gtk.Button(), "flat", "tab")
            inner = vbox(2)
            inner.pack_start(label(I[name], "tab-icon"), False, False, 0)
            inner.pack_start(label(title, "tab-label"), False, False, 0)
            btn.add(inner)
            btn.connect("clicked", lambda _b, n=name: self.select(n))
            tabs.pack_start(btn, True, True, 0)
            self.tab_buttons[name] = btn
        root.pack_start(tabs, False, False, 0)

        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE, transition_duration=160)
        self.stack.set_hhomogeneous(True)
        self.stack.set_vhomogeneous(True)
        root.pack_start(self.stack, True, True, 0)
        self.stack.add_named(self.build_dashboard(), "dashboard")
        self.stack.add_named(self.build_media(), "media")
        self.stack.add_named(self.build_performance(), "performance")
        self.stack.add_named(self.build_apps(), "apps")
        root.show_all()
        self.select("dashboard")

        GLib.timeout_add_seconds(2, self.background_sample)

    # ------------------------------------------------------------ stránky
    def build_dashboard(self):
        page = hbox(8, "page")

        left = vbox(8)
        top = hbox(8)

        weather = hbox(12, "tile", "weather")
        self.w_icon = label(I["w_cloud"], "weather-icon", "dim")
        wtext = vbox(0)
        wtext.set_valign(Gtk.Align.CENTER)
        self.w_temp = label("—", "weather-temp", xalign=0)
        self.w_desc = label("načítám", "dim", xalign=0, ellipsize=True)
        wtext.pack_start(self.w_temp, False, False, 0)
        wtext.pack_start(self.w_desc, False, False, 0)
        weather.pack_start(self.w_icon, False, False, 0)
        weather.pack_start(wtext, True, True, 0)
        weather.set_size_request(170, -1)
        if WEATHER_ENABLED:
            top.pack_start(weather, False, False, 0)

        system = hbox(12, "tile", "system")
        logo = label(I["distro"], "logo")
        logo.set_valign(Gtk.Align.CENTER)
        lines = vbox(3)
        lines.set_valign(Gtk.Align.CENTER)
        self.s_user = label(f"{I['user']}  {getpass.getuser()}@{socket.gethostname()}", xalign=0, ellipsize=True)
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "") or "Hyprland"
        self.s_desktop = label(f"{I['desktop']}  {desktop}", "dim", xalign=0, ellipsize=True)
        self.s_uptime = label("", "dim", xalign=0, ellipsize=True)
        for lab in (self.s_user, self.s_desktop, self.s_uptime):
            lines.pack_start(lab, False, False, 0)
        system.pack_start(logo, False, False, 0)
        system.pack_start(lines, True, True, 0)
        top.pack_start(system, True, True, 0)
        left.pack_start(top, False, False, 0)

        bottom = hbox(8)
        clock = vbox(2, "tile", "clock")
        clock.set_valign(Gtk.Align.FILL)
        self.c_hour = label("00", "clock-digits")
        self.c_min = label("00", "clock-digits")
        cinner = vbox(0)
        cinner.set_valign(Gtk.Align.CENTER)
        cinner.pack_start(self.c_hour, False, False, 0)
        cinner.pack_start(label("•••", "clock-dots"), False, False, 0)
        cinner.pack_start(self.c_min, False, False, 0)
        clock.pack_start(cinner, True, False, 0)
        clock.set_size_request(76, -1)
        bottom.pack_start(clock, False, False, 0)

        self.calendar = Calendar()
        bottom.pack_start(self.calendar, True, True, 0)

        gauges = vbox(6, "tile", "gauges")
        self.g_cpu, self.g_ram, self.g_disk = Gauge(50, I["cpu"], 4), Gauge(50, I["ram"], 4), Gauge(50, I["disk"], 4)
        for g in (self.g_cpu, self.g_ram, self.g_disk):
            gauges.pack_start(g, True, False, 0)
        bottom.pack_start(gauges, False, False, 0)
        left.pack_start(bottom, True, True, 0)
        page.pack_start(left, True, True, 0)

        mini = vbox(6, "tile", "mini-media")
        mini.set_size_request(168, -1)
        self.m_art = Art(112)
        self.m_title = label("Nic nehraje", "media-title", ellipsize=True)
        self.m_artist = label("", "dim", ellipsize=True)
        mini.pack_start(self.m_art, True, False, 4)
        mini.pack_start(self.m_title, False, False, 0)
        mini.pack_start(self.m_artist, False, False, 0)
        ctrl, self.m_play = self.media_controls(small=True)
        mini.pack_start(ctrl, False, False, 4)
        page.pack_start(mini, False, False, 0)
        return page

    def media_controls(self, small):
        row = hbox(8, "media-controls")
        row.set_halign(Gtk.Align.CENTER)
        prev_btn = css(Gtk.Button(label=I["prev"]), "flat", "media-btn")
        play_btn = css(Gtk.Button(label=I["play"]), "flat", "media-btn", "primary")
        next_btn = css(Gtk.Button(label=I["next"]), "flat", "media-btn")
        if not small:
            for b in (prev_btn, play_btn, next_btn):
                css(b, "large")
        prev_btn.connect("clicked", lambda *_: self.media_command("Previous"))
        play_btn.connect("clicked", lambda *_: self.media_command("PlayPause"))
        next_btn.connect("clicked", lambda *_: self.media_command("Next"))
        for b in (prev_btn, play_btn, next_btn):
            row.pack_start(b, False, False, 0)
        return row, play_btn

    def build_media(self):
        page = hbox(20, "page", "tile", "media-page")
        self.b_art = Art(210, 16)
        page.pack_start(self.b_art, False, False, 0)
        info = vbox(6)
        info.set_valign(Gtk.Align.CENTER)
        self.b_player = label("", "chip", xalign=0)
        self.b_player.set_halign(Gtk.Align.START)
        self.b_title = label("Nic nehraje", "media-big-title", xalign=0, ellipsize=True)
        self.b_artist = label("Spusť hudbu nebo video a objeví se tady.", xalign=0, ellipsize=True)
        self.b_album = label("", "dim", xalign=0, ellipsize=True)
        self.b_progress = css(Gtk.ProgressBar(), "progress")
        self.b_progress.set_margin_top(14)
        times = hbox(0)
        self.b_pos = label("", "dim", xalign=0)
        self.b_len = label("", "dim", xalign=1)
        times.pack_start(self.b_pos, True, True, 0)
        times.pack_start(self.b_len, True, True, 0)
        ctrl, self.b_play = self.media_controls(small=False)
        ctrl.set_margin_top(10)
        for w in (self.b_player, self.b_title, self.b_artist, self.b_album, self.b_progress, times, ctrl):
            info.pack_start(w, False, False, 0)
        page.pack_start(info, True, True, 0)
        return page

    def build_performance(self):
        page = vbox(8, "page")
        row = hbox(8)
        row.set_homogeneous(True)
        self.p_gauges = {}
        for key, title in (("cpu", "Procesor"), ("ram", "Paměť"), ("temp", "Teplota"), ("disk", "Disk")):
            tile = vbox(4, "tile", "perf-tile")
            gauge = css(Gauge(84, "0%", 6), "big")
            name = label(f"{I[key]}  {title}", "perf-name")
            detail = label("", "dim")
            tile.pack_start(gauge, False, False, 0)
            tile.pack_start(name, False, False, 0)
            tile.pack_start(detail, False, False, 0)
            row.pack_start(tile, True, True, 0)
            self.p_gauges[key] = (gauge, detail)
        page.pack_start(row, False, False, 0)

        lower = hbox(8)
        chart = vbox(6, "tile")
        chart.pack_start(label("Procesor za poslední 2 minuty", "dim", xalign=0), False, False, 0)
        self.p_spark = Sparkline(84)
        chart.pack_start(self.p_spark, True, True, 0)
        lower.pack_start(chart, True, True, 0)

        procs = vbox(3, "tile", "procs")
        procs.set_size_request(280, -1)
        head = hbox(0)
        head.pack_start(label("Nejvytíženější", "dim", xalign=0), True, True, 0)
        head.pack_start(css(label("CPU", "dim", xalign=1), "proc-col"), False, False, 0)
        head.pack_start(css(label("RAM", "dim", xalign=1), "proc-col"), False, False, 0)
        procs.pack_start(head, False, False, 0)
        self.p_rows = []
        for _ in range(5):
            line = hbox(0)
            name = label("", xalign=0, ellipsize=True)
            cpu = css(label("", xalign=1), "proc-col")
            mem = css(label("", "dim", xalign=1), "proc-col")
            line.pack_start(name, True, True, 0)
            line.pack_start(cpu, False, False, 0)
            line.pack_start(mem, False, False, 0)
            procs.pack_start(line, False, False, 0)
            self.p_rows.append((name, cpu, mem))
        lower.pack_start(procs, False, False, 0)
        page.pack_start(lower, True, True, 0)
        return page

    def build_apps(self):
        page = vbox(8, "page")
        self.search = css(Gtk.SearchEntry(placeholder_text="Hledat aplikaci"), "search")
        self.search.connect("search-changed", lambda *_: (self.flow.invalidate_filter(), self.select_first_app()))
        self.search.connect("activate", lambda *_: self.launch_first())
        page.pack_start(self.search, False, False, 0)
        scroll = css(Gtk.ScrolledWindow(), "tile", "apps-scroll")
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.flow = Gtk.FlowBox(homogeneous=True, column_spacing=4, row_spacing=4,
                                min_children_per_line=6, max_children_per_line=6,
                                selection_mode=Gtk.SelectionMode.SINGLE, activate_on_single_click=True)
        self.flow.set_valign(Gtk.Align.START)
        self.flow.set_filter_func(self.app_filter)
        self.flow.connect("child-activated", lambda _f, child: self.launch(child.app))
        scroll.add(self.flow)
        page.pack_start(scroll, True, True, 0)
        Gio.AppInfoMonitor.get().connect("changed", lambda *_: setattr(self, "apps_built", False))
        return page

    # ------------------------------------------------------------ aplikace
    def ensure_apps(self):
        if self.apps_built:
            return
        self.apps_built = True
        for child in self.flow.get_children():
            self.flow.remove(child)
        apps = [a for a in Gio.AppInfo.get_all() if a.should_show()]
        apps.sort(key=lambda a: (a.get_display_name() or "").lower())
        for app in apps:
            item = vbox(4, "app")
            icon = app.get_icon()
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.DND) if icon else \
                Gtk.Image.new_from_icon_name("application-x-executable", Gtk.IconSize.DND)
            image.set_pixel_size(40)
            item.pack_start(image, False, False, 0)
            item.pack_start(label(app.get_display_name() or "", "app-name", ellipsize=True, lines=2), False, False, 0)
            child = Gtk.FlowBoxChild()
            child.app = app
            child.keywords = " ".join(filter(None, [
                app.get_display_name(), app.get_name(), app.get_executable(), app.get_description()])).lower()
            child.add(item)
            self.flow.add(child)
        self.flow.show_all()

    def app_filter(self, child):
        words = self.search.get_text().lower().split()
        return all(w in child.keywords for w in words)

    def first_visible_app(self):
        for child in self.flow.get_children():
            if child.get_mapped() and child.get_child_visible():
                return child
        return None

    def select_first_app(self):
        child = self.first_visible_app()
        if child:
            self.flow.select_child(child)
        else:
            self.flow.unselect_all()

    def launch_first(self):
        child = self.first_visible_app()
        if child:
            self.launch(child.app)

    def launch(self, app):
        try:
            app.launch([], None)
        except GLib.Error as err:
            print(f"island-panel: {err.message}", file=sys.stderr)
        self.hide()

    # ------------------------------------------------------------ záložky
    def select(self, name):
        self.stack.set_visible_child_name(name)
        for key, btn in self.tab_buttons.items():
            set_class(btn, "active", key == name)
        if name == "apps":
            self.ensure_apps()
            self.search.grab_focus()
        self.refresh()

    @property
    def tab(self):
        return self.stack.get_visible_child_name()

    # ------------------------------------------------------------ obnova dat
    def background_sample(self):
        self.stats.sample()
        if self.visible and self.tab == "performance":
            self.procs.sample()
            self.refresh_performance()
        return True

    def tick(self):
        if not self.visible:
            self.tick_timer = None
            return False
        self.refresh()
        return True

    def refresh(self):
        if not self.visible:
            return
        now = datetime.datetime.now()
        self.c_hour.set_text(f"{now.hour:02d}")
        self.c_min.set_text(f"{now.minute:02d}")
        self.refresh_media()
        if self.tab == "dashboard":
            up = f"{I['clock']}  běží {fmt_duration(self.stats.uptime())}"
            bat = self.stats.battery()
            if bat:
                icon = I["plug"] if bat[1] in ("Charging", "Full", "Not charging") else I["bat"][min(4, bat[0] // 20)]
                up += f"   {icon}  {bat[0]} %"
            self.s_uptime.set_text(up)
            self.g_cpu.set(self.stats.cpu)
            self.g_ram.set(self.stats.ram()[2])
            self.g_disk.set(self.stats.disk()[2])
            self.maybe_fetch_weather()
        elif self.tab == "performance":
            self.refresh_performance()

    def refresh_performance(self):
        used, total, pct = self.stats.ram()
        dused, dtotal, dpct = self.stats.disk()
        temp = self.stats.temp()
        gauge, detail = self.p_gauges["cpu"]
        gauge.set(self.stats.cpu, f"{self.stats.cpu:.0f}%")
        detail.set_text(f"{os.cpu_count() or 1} vláken")
        gauge, detail = self.p_gauges["ram"]
        gauge.set(pct, f"{pct:.0f}%")
        detail.set_text(f"{used:.1f} / {total:.1f} GB")
        gauge, detail = self.p_gauges["temp"]
        gauge.set(temp or 0, f"{temp:.0f}°" if temp is not None else "—")
        detail.set_text("čidlo procesoru" if temp is not None else "čidlo nenalezeno")
        gauge, detail = self.p_gauges["disk"]
        gauge.set(dpct, f"{dpct:.0f}%")
        detail.set_text(f"{dused:.0f} / {dtotal:.0f} GB")
        self.p_spark.set(self.stats.history)
        rows = self.procs.rows + [("", None, None)] * 5
        for (name, cpu, mem), (n, c, m) in zip(self.p_rows, rows):
            name.set_text(n)
            cpu.set_text(f"{c:.1f}%" if c is not None else "")
            mem.set_text(f"{m:.0f} MB" if m is not None else "")

    def refresh_media(self):
        info = self.media = self.mpris.poll()
        playing = bool(info and info["playing"])
        for btn in (self.m_play, self.b_play):
            btn.set_label(I["pause"] if playing else I["play"])
        if not info:
            self.m_title.set_text("Nic nehraje")
            self.m_artist.set_text("")
            self.m_art.set_url(None)
            self.b_player.hide()
            self.b_title.set_text("Nic nehraje")
            self.b_artist.set_text("Spusť hudbu nebo video a objeví se tady.")
            self.b_album.set_text("")
            self.b_progress.set_fraction(0)
            self.b_pos.set_text("")
            self.b_len.set_text("")
            self.b_art.set_url(None)
            return
        self.m_title.set_text(info["title"] or "Bez názvu")
        self.m_artist.set_text(info["artist"])
        self.m_art.set_url(info["art"])
        self.b_player.set_text(info["player"])
        self.b_player.show()
        self.b_title.set_text(info["title"] or "Bez názvu")
        self.b_artist.set_text(info["artist"])
        self.b_album.set_text(info["album"])
        self.b_art.set_url(info["art"])
        if info["length"] > 0:
            self.b_progress.set_fraction(max(0.0, min(1.0, info["position"] / info["length"])))
            self.b_pos.set_text(fmt_time(info["position"]))
            self.b_len.set_text(fmt_time(info["length"]))
        else:
            self.b_progress.set_fraction(0)
            self.b_pos.set_text("")
            self.b_len.set_text("")

    def media_command(self, method):
        self.mpris.command(method)
        GLib.timeout_add(250, lambda: self.refresh_media() and False)

    def maybe_fetch_weather(self):
        if not WEATHER_ENABLED or self.weather_busy or time.monotonic() < self.weather_at:
            return
        self.weather_busy = True

        def work():
            result = fetch_weather()
            GLib.idle_add(done, result)

        def done(result):
            self.weather_busy = False
            if result:
                icon, temp, desc, area = result
                self.w_icon.set_text(icon)
                set_class(self.w_icon, "dim", False)
                self.w_temp.set_text(temp)
                self.w_desc.set_text(desc or area)
                self.weather_at = time.monotonic() + 1800   # další dotaz za 30 minut
            else:
                if self.w_temp.get_text() == "—":
                    self.w_desc.set_text("nedostupné")
                self.weather_at = time.monotonic() + 300    # nepovedlo se, zkusit za 5 minut
            return False

        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------ zobrazení
    def show(self, by_key=False, tab=None):
        self.cancel_close()
        if tab:
            self.select(tab)
        if self.visible:
            return
        self.visible = True
        if GtkLayerShell.is_supported():
            mode = GtkLayerShell.KeyboardMode.EXCLUSIVE if by_key else GtkLayerShell.KeyboardMode.ON_DEMAND
            GtkLayerShell.set_keyboard_mode(self.win, mode)
        self.calendar.reset()
        self.win.show()
        self.refresh()
        if self.tab == "apps":
            self.search.grab_focus()
        if self.tick_timer is None:
            self.tick_timer = GLib.timeout_add_seconds(1, self.tick)
        if not by_key:
            self.close_unless_entered()

    def hide(self):
        self.cancel_close()
        if not self.visible:
            return
        self.visible = False
        self.win.hide()
        self.search.set_text("")
        self.select("dashboard")   # příště zase začít přehledem

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show(by_key=True)

    def on_key(self, _win, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
            return True
        return False


# ----------------------------------------------------------------------------
# Boční panel: hlasitost a jas
# ----------------------------------------------------------------------------
class Audio:
    """Hlasitost výchozího výstupu přes wpctl (PipeWire), záložně přes pactl."""

    def __init__(self):
        self.wpctl, self.pactl = shutil.which("wpctl"), shutil.which("pactl")

    @staticmethod
    def _run(*cmd):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=1.5).stdout
        except (OSError, subprocess.SubprocessError):
            return ""

    def get(self):
        """Vrátí (hlasitost 0-1, ztlumeno) nebo None, když se to nepodaří zjistit."""
        if self.wpctl:
            out = self._run(self.wpctl, "get-volume", "@DEFAULT_AUDIO_SINK@")
            match = re.search(r"Volume:\s*([0-9.]+)", out)
            if match:
                return float(match.group(1)), "MUTED" in out
        if self.pactl:
            match = re.search(r"(\d+)%", self._run(self.pactl, "get-sink-volume", "@DEFAULT_SINK@"))
            if match:
                muted = "yes" in self._run(self.pactl, "get-sink-mute", "@DEFAULT_SINK@")
                return int(match.group(1)) / 100, muted
        return None

    def set(self, value):
        value = max(0.0, min(1.0, value))
        if self.wpctl:
            self._run(self.wpctl, "set-mute", "@DEFAULT_AUDIO_SINK@", "0")
            self._run(self.wpctl, "set-volume", "@DEFAULT_AUDIO_SINK@", f"{value:.2f}")
        elif self.pactl:
            self._run(self.pactl, "set-sink-mute", "@DEFAULT_SINK@", "0")
            self._run(self.pactl, "set-sink-volume", "@DEFAULT_SINK@", f"{round(value * 100)}%")

    def toggle_mute(self):
        if self.wpctl:
            self._run(self.wpctl, "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle")
        elif self.pactl:
            self._run(self.pactl, "set-sink-mute", "@DEFAULT_SINK@", "toggle")


class Backlight:
    """Jas displeje. Čte se ze /sys, nastavuje přes systémovou službu logind
    (nepotřebuje žádný další program), záložně přes brightnessctl."""

    BASE = "/sys/class/backlight"
    MIN = 0.02   # nikdy displej úplně nezhasnout

    def __init__(self):
        self.name, self.max = None, 0
        try:
            names = sorted(os.listdir(self.BASE))
        except OSError:
            names = []
        candidates = []
        for name in names:
            try:
                maximum = int(read(f"{self.BASE}/{name}/max_brightness"))
            except ValueError:
                continue
            if maximum > 0:
                # "raw" je přímo panel displeje (např. intel_backlight), ten má přednost
                order = {"raw": 0, "platform": 1, "firmware": 2}.get(read(f"{self.BASE}/{name}/type"), 3)
                candidates.append((order, name, maximum))
        if candidates:
            _order, self.name, self.max = min(candidates)
        self.bus, self.use_logind = None, True
        self.brightnessctl = shutil.which("brightnessctl")

    @property
    def available(self):
        return bool(self.name and self.max > 0)

    def get(self):
        if not self.available:
            return None
        try:
            return int(read(f"{self.BASE}/{self.name}/brightness")) / self.max
        except ValueError:
            return None

    def set(self, value):
        if not self.available:
            return
        raw = max(1, round(max(self.MIN, min(1.0, value)) * self.max))
        if self.use_logind and self._logind(raw):
            return
        if self.brightnessctl:
            try:
                subprocess.run([self.brightnessctl, "-q", "-d", self.name, "set", str(raw)],
                               capture_output=True, timeout=1.5)
            except (OSError, subprocess.SubprocessError):
                pass
        else:
            print("island-panel: jas se nepodařilo nastavit (logind odmítl a brightnessctl není nainstalovaný)",
                  file=sys.stderr)

    def _logind(self, raw):
        try:
            if self.bus is None:
                self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
            self.bus.call_sync("org.freedesktop.login1", "/org/freedesktop/login1/session/auto",
                               "org.freedesktop.login1.Session", "SetBrightness",
                               GLib.Variant("(ssu)", ("backlight", self.name, raw)),
                               None, Gio.DBusCallFlags.NONE, 800, None)
            return True
        except GLib.Error:
            self.use_logind = False   # příště rovnou záložní cesta
            return False


class VSlider(Gtk.DrawingArea):
    """Svislý posuvník 0-1: tažení myší nebo kolečko."""

    def __init__(self, on_change, width=38, height=130):
        super().__init__()
        self.value, self.dim, self.dragging, self.on_change = 0.0, False, False, on_change
        self.set_size_request(width, height)
        self.set_halign(Gtk.Align.CENTER)
        css(self, "vslider")
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.BUTTON1_MOTION_MASK | Gdk.EventMask.SCROLL_MASK |
                        Gdk.EventMask.SMOOTH_SCROLL_MASK)
        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_press)
        self.connect("motion-notify-event", self.on_motion)
        self.connect("button-release-event", self.on_release)
        self.connect("scroll-event", self.on_scroll)

    def set(self, value, dim=False):
        """Nastaví zobrazenou hodnotu zvenku (během tažení se ignoruje)."""
        if self.dragging:
            return
        self.value, self.dim = max(0.0, min(1.0, value)), dim
        self.queue_draw()

    def _change(self, value):
        self.value, self.dim = max(0.0, min(1.0, value)), False
        self.queue_draw()
        self.on_change(self.value)

    def _from_y(self, y):
        # pár pixelů rezervy nahoře i dole, aby šlo snadno trefit 0 % a 100 %
        height = self.get_allocated_height()
        return (height - 6 - y) / max(1, height - 12)

    def on_press(self, _w, event):
        if event.button == 1:
            self.dragging = True
            self._change(self._from_y(event.y))
        return True

    def on_motion(self, _w, event):
        if self.dragging:
            self._change(self._from_y(event.y))
        return True

    def on_release(self, _w, event):
        if event.button == 1:
            self.dragging = False
        return True

    def on_scroll(self, _w, event):
        if event.direction == Gdk.ScrollDirection.UP:
            self._change(self.value + 0.05)
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self._change(self.value - 0.05)
        elif event.direction == Gdk.ScrollDirection.SMOOTH:
            ok, _dx, dy = event.get_scroll_deltas()
            if ok and dy:
                self._change(self.value - dy * 0.03)
        return True

    def on_draw(self, _widget, cr):
        w, h = self.get_allocated_width(), self.get_allocated_height()
        ctx = self.get_style_context()
        fg = ctx.get_color(Gtk.StateFlags.NORMAL)
        found, fill = ctx.lookup_color("pill")
        if not found:
            fill = fg
        r = min(12, w / 2)
        cr.new_sub_path()
        cr.arc(w - r, r, r, -math.pi / 2, 0)
        cr.arc(w - r, h - r, r, 0, math.pi / 2)
        cr.arc(r, h - r, r, math.pi / 2, math.pi)
        cr.arc(r, r, r, math.pi, 3 * math.pi / 2)
        cr.close_path()
        cr.clip()
        cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.10)
        cr.paint()
        filled = h * self.value
        if filled > 0.5:
            cr.set_source_rgba(fill.red, fill.green, fill.blue, 0.35 if self.dim else 1.0)
            cr.rectangle(0, h - filled, w, filled)
            cr.fill()
        return False


class SidePanel(AutoHide):
    """Úzký panel u pravého okraje s hlasitostí a jasem."""

    def __init__(self, app):
        self.audio, self.backlight = Audio(), Backlight()
        self.visible, self.close_timer, self.poll_timer = False, None, None
        self.pending, self.apply_timer = {}, None

        self.win = layer_window(app, "island-side", GtkLayerShell.Edge.RIGHT, EDGE_OVERHANG)
        self.watch_pointer()
        root = vbox(8)
        root.set_name("side")
        root.set_margin_end(EDGE_OVERHANG)   # vyrovná přesah okna, panel zůstane na stejném místě
        self.win.add(root)

        self.v_value = label("", "side-value")
        self.v_slider = VSlider(self.set_volume, height=SLIDER_HEIGHT)
        self.v_button = css(Gtk.Button(label=I["vol_high"]), "flat", "side-btn")
        self.v_button.connect("clicked", lambda *_: self.toggle_mute())
        for widget in (self.v_value, self.v_slider, self.v_button):
            root.pack_start(widget, False, False, 0)

        self.b_value = self.b_slider = None
        if self.backlight.available:
            root.pack_start(css(Gtk.Box(), "side-sep"), False, False, 0)
            self.b_value = label("", "side-value")
            self.b_slider = VSlider(self.set_brightness, height=SLIDER_HEIGHT)
            for widget in (self.b_value, self.b_slider, label(I["sun"], "side-icon")):
                root.pack_start(widget, False, False, 0)
        root.show_all()

    # ------------------------------------------------------------ hodnoty
    def refresh(self):
        vol = self.audio.get()
        if vol is not None and not self.v_slider.dragging:
            value, muted = vol
            self.v_slider.set(value, dim=muted)
            self.show_volume(value, muted)
        if self.b_slider is not None and not self.b_slider.dragging:
            value = self.backlight.get()
            if value is not None:
                self.b_slider.set(value)
                self.b_value.set_text(f"{round(value * 100)}")

    def show_volume(self, value, muted):
        self.v_value.set_text(f"{round(value * 100)}")
        icon = I["vol_off"] if muted or value <= 0.005 else I["vol_low"] if value < 0.5 else I["vol_high"]
        self.v_button.set_label(icon)
        set_class(self.v_button, "muted", muted)

    def set_volume(self, value):
        self.show_volume(value, False)
        self.apply("volume", lambda: self.audio.set(value))

    def set_brightness(self, value):
        value = max(Backlight.MIN, value)
        self.b_value.set_text(f"{round(value * 100)}")
        self.apply("brightness", lambda: self.backlight.set(value))

    def toggle_mute(self):
        self.audio.toggle_mute()
        self.refresh()

    def apply(self, key, func):
        """Při tažení chodí desítky změn za vteřinu, do systému se pošle vždy jen ta poslední."""
        self.pending[key] = func
        if self.apply_timer is None:
            self.apply_timer = GLib.timeout_add(40, self.flush)

    def flush(self):
        self.apply_timer = None
        pending, self.pending = self.pending, {}
        for func in pending.values():
            func()
        return False

    # ------------------------------------------------------------ zobrazení
    def poll(self):
        if not self.visible:
            self.poll_timer = None
            return False
        self.refresh()
        return True

    def show(self, by_key=False):
        self.cancel_close()
        if self.visible:
            return
        self.visible = True
        self.refresh()
        self.win.show()
        if self.poll_timer is None:
            self.poll_timer = GLib.timeout_add(700, self.poll)
        if not by_key:
            self.close_unless_entered()

    def hide(self):
        self.cancel_close()
        if not self.visible:
            return
        self.visible = False
        self.win.hide()

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show(by_key=True)


# ----------------------------------------------------------------------------
# Oznámení: panel sám funguje jako služba oznámení (org.freedesktop.Notifications)
# ----------------------------------------------------------------------------
def run(*cmd, timeout=3):
    """Spustí příkaz a vrátí jeho výstup; při jakékoli chybě prázdný text."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def spawn(*cmd):
    """Spustí program na pozadí, nezávisle na panelu."""
    try:
        subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError as err:
        print(f"island-panel: {' '.join(cmd)}: {err}", file=sys.stderr)


def plain_text(text):
    """Oznámení smí obsahovat jednoduché značky (<b>, <a>...), zobrazujeme jen čistý text."""
    text = re.sub(r"<[^>]{1,200}>", "", text or "")
    return " ".join(html.unescape(text).split())


def fmt_ago(timestamp):
    seconds = max(0, int(time.time() - timestamp))
    if seconds < 60:
        return "teď"
    if seconds < 3600:
        return f"{seconds // 60} min"
    if seconds < 86400:
        return f"{seconds // 3600} h"
    return f"{seconds // 86400} d"


class IconIndex:
    """Najde ikonu aplikace podle jména okna nebo odesílatele oznámení."""

    def __init__(self):
        self.map = None
        Gio.AppInfoMonitor.get().connect("changed", lambda *_: setattr(self, "map", None))

    def build(self):
        self.map = {}
        for app in Gio.AppInfo.get_all():
            icon = app.get_icon()
            if icon is None:
                continue
            keys = [app.get_display_name(), app.get_name()]
            app_id = app.get_id() or ""
            if app_id.endswith(".desktop"):
                keys += [app_id[:-8], app_id[:-8].split(".")[-1]]
            exe = app.get_executable()
            if exe:
                keys.append(os.path.basename(exe))
            wm_class = getattr(app, "get_startup_wm_class", None)
            if wm_class:
                try:
                    keys.append(wm_class())
                except Exception:
                    pass
            for key in keys:
                if key:
                    self.map.setdefault(key.lower(), icon)

    def image(self, name, size):
        if self.map is None:
            self.build()
        name = (name or "").strip()
        icon = None
        for key in (name, name.split(".")[-1], name.replace(" ", "-"), name.replace(" ", "")):
            icon = self.map.get(key.lower())
            if icon:
                break
        if icon:
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.DND)
        elif name and Gtk.IconTheme.get_default().has_icon(name.lower()):
            image = Gtk.Image.new_from_icon_name(name.lower(), Gtk.IconSize.DND)
        else:
            image = Gtk.Image.new_from_icon_name("application-x-executable", Gtk.IconSize.DND)
        image.set_pixel_size(size)
        return image


class Notification:
    def __init__(self, nid):
        self.id = nid
        self.app = self.icon = self.summary = self.body = ""
        self.pixbuf, self.has_default, self.urgency, self.timeout = None, False, 1, -1
        self.time = time.time()


NOTIFICATIONS_XML = """<node><interface name="org.freedesktop.Notifications">
  <method name="GetCapabilities"><arg type="as" direction="out"/></method>
  <method name="Notify">
    <arg type="s" direction="in"/><arg type="u" direction="in"/><arg type="s" direction="in"/>
    <arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="as" direction="in"/>
    <arg type="a{sv}" direction="in"/><arg type="i" direction="in"/><arg type="u" direction="out"/>
  </method>
  <method name="CloseNotification"><arg type="u" direction="in"/></method>
  <method name="GetServerInformation">
    <arg type="s" direction="out"/><arg type="s" direction="out"/>
    <arg type="s" direction="out"/><arg type="s" direction="out"/>
  </method>
  <signal name="NotificationClosed"><arg type="u"/><arg type="u"/></signal>
  <signal name="ActionInvoked"><arg type="u"/><arg type="s"/></signal>
</interface></node>"""


class NotificationServer:
    NAME = "org.freedesktop.Notifications"
    PATH = "/org/freedesktop/Notifications"
    KEEP = 60   # kolik posledních oznámení si pamatovat

    def __init__(self, own=True):
        self.items = []           # nejnovější první
        self.next_id, self.conn = 1, None
        self.active, self.other = False, ""   # other = jméno cizího programu, který oznámení už obsluhuje
        self.dnd = False
        self.on_change, self.on_new = [], []  # funkce, které se zavolají při změně / novém oznámení
        if own:
            Gio.bus_own_name(Gio.BusType.SESSION, self.NAME, Gio.BusNameOwnerFlags.NONE,
                             self._on_bus, self._on_name, self._on_lost)

    # --- spojení se sběrnicí
    def _on_bus(self, conn, _name):
        self.conn = conn
        info = Gio.DBusNodeInfo.new_for_xml(NOTIFICATIONS_XML).interfaces[0]
        conn.register_object(self.PATH, info, self._on_call, None, None)

    def _on_name(self, _conn, _name):
        self.active, self.other = True, ""
        self._changed()

    def _on_lost(self, conn, _name):
        self.active = False
        self.other = "jiný program"
        if conn is not None:
            try:
                pid = conn.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
                                     "GetConnectionUnixProcessID", GLib.Variant("(s)", (self.NAME,)),
                                     None, Gio.DBusCallFlags.NONE, 500, None).unpack()[0]
                self.other = read(f"/proc/{pid}/comm") or self.other
            except GLib.Error:
                pass
        self._changed()

    def _changed(self):
        for func in self.on_change:
            func()

    def _signal(self, name, *args):
        if self.conn:
            kind = "(uu)" if name == "NotificationClosed" else "(us)"
            self.conn.emit_signal(None, self.PATH, self.NAME, name, GLib.Variant(kind, args))

    # --- volání od aplikací
    def _on_call(self, _conn, _sender, _path, _iface, method, params, invocation):
        if method == "GetCapabilities":
            invocation.return_value(GLib.Variant("(as)", (["body", "actions", "icon-static", "persistence"],)))
        elif method == "GetServerInformation":
            invocation.return_value(GLib.Variant("(ssss)", ("island-panel", "island", "1.0", "1.2")))
        elif method == "CloseNotification":
            self.remove(params.get_child_value(0).get_uint32(), reason=3)
            invocation.return_value(None)
        elif method == "Notify":
            invocation.return_value(GLib.Variant("(u)", (self._notify(params),)))
        else:
            invocation.return_dbus_error("org.freedesktop.DBus.Error.UnknownMethod", method)

    def _notify(self, params):
        replaces = params.get_child_value(1).get_uint32()
        note = next((n for n in self.items if n.id == replaces), None) if replaces else None
        if note is None:
            note = Notification(self.next_id)
            self.next_id += 1
        else:
            self.items.remove(note)
            note.time = time.time()
        note.app = params.get_child_value(0).get_string() or "Oznámení"
        note.icon = params.get_child_value(2).get_string()
        note.summary = plain_text(params.get_child_value(3).get_string())
        note.body = plain_text(params.get_child_value(4).get_string())
        actions = params.get_child_value(5).unpack()
        note.has_default = "default" in actions[0::2]
        note.timeout = params.get_child_value(7).get_int32()
        hints = params.get_child_value(6)
        urgency = hints.lookup_value("urgency", GLib.VariantType.new("y"))
        note.urgency = urgency.get_byte() if urgency else 1
        note.pixbuf = None
        for key in ("image-data", "image_data", "icon_data"):
            data = hints.lookup_value(key, None)
            if data is not None:
                note.pixbuf = self._pixbuf(data)
                break
        if note.pixbuf is None:
            for key in ("image-path", "image_path"):
                path = hints.lookup_value(key, GLib.VariantType.new("s"))
                if path:
                    note.icon = path.get_string()
                    break
        self.items.insert(0, note)
        del self.items[self.KEEP:]
        self._changed()
        if not self.dnd:
            for func in self.on_new:
                func(note)
        return note.id

    @staticmethod
    def _pixbuf(data):
        try:
            width, height, stride, alpha, bits, _channels = (data.get_child_value(i).unpack() for i in range(6))
            raw = data.get_child_value(6).get_data_as_bytes()
            return GdkPixbuf.Pixbuf.new_from_bytes(raw, GdkPixbuf.Colorspace.RGB, alpha, bits, width, height, stride)
        except Exception:
            return None

    # --- akce uživatele
    def remove(self, nid, reason=2):
        before = len(self.items)
        self.items = [n for n in self.items if n.id != nid]
        if len(self.items) != before:
            self._signal("NotificationClosed", nid, reason)
            self._changed()

    def activate(self, note):
        """Klik na oznámení: aplikace dostane zprávu (typicky se přepne do popředí) a oznámení zmizí."""
        if note.has_default:
            self._signal("ActionInvoked", note.id, "default")
        self.remove(note.id)

    def remove_app(self, app):
        for note in [n for n in self.items if n.app == app]:
            self.remove(note.id)

    def clear(self):
        for note in list(self.items):
            self.remove(note.id)


def notification_image(note, icons, size):
    """Obrázek k oznámení: přiložený obrázek, ikona z oznámení, jinak ikona aplikace."""
    pixbuf = note.pixbuf
    if pixbuf is None and note.icon:
        path = urllib.parse.unquote(note.icon[7:]) if note.icon.startswith("file://") else note.icon
        if os.path.isabs(path) and os.path.exists(path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
            except GLib.Error:
                pixbuf = None
        elif Gtk.IconTheme.get_default().has_icon(note.icon):
            image = Gtk.Image.new_from_icon_name(note.icon, Gtk.IconSize.DND)
            image.set_pixel_size(size)
            return image
    if pixbuf is not None:
        scale = 2
        scaled = pixbuf.scale_simple(size * scale, size * scale, GdkPixbuf.InterpType.BILINEAR)
        surface = Gdk.cairo_surface_create_from_pixbuf(scaled, scale, None)
        return Gtk.Image.new_from_surface(surface)
    return icons.image(note.app, size)


class Toasts:
    """Vyskakovací bubliny s novými oznámeními, vpravo nahoře pod lištou."""

    MAX = 3

    def __init__(self, app, server, icons):
        self.server, self.icons = server, icons
        self.win = layer_window(app, "island-toast", GtkLayerShell.Edge.TOP)
        if GtkLayerShell.is_supported():
            GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.RIGHT, True)
            GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.TOP, TOAST_TOP_MARGIN)
            GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.RIGHT, 10)
        self.box = vbox(8)
        self.box.set_name("toasts")
        self.win.add(self.box)
        self.box.show()
        self.entries = {}   # id oznámení -> (widget, časovač)
        self.blocked = lambda: False   # True = bubliny teď neukazovat (je otevřené ovládací centrum)
        server.on_new.append(self.push)
        server.on_change.append(self.sync)

    def dismiss_all(self):
        for nid in list(self.entries):
            self.drop(nid)

    def push(self, note):
        self.drop(note.id)
        if self.blocked():
            return
        while len(self.entries) >= self.MAX:
            self.drop(next(iter(self.entries)))
        button = css(Gtk.Button(), "flat", "toast")
        row = hbox(12)
        image = notification_image(note, self.icons, 36)
        image.set_valign(Gtk.Align.START)
        row.pack_start(image, False, False, 0)
        text = vbox(2)
        head = hbox(8)
        head.pack_start(label(note.summary or note.app, "toast-title", xalign=0, ellipsize=True), True, True, 0)
        head.pack_start(label(note.app, "dim", "toast-app", xalign=1), False, False, 0)
        text.pack_start(head, False, False, 0)
        if note.body:
            body = label(note.body, "dim", xalign=0, ellipsize=True, lines=2)
            body.set_justify(Gtk.Justification.LEFT)
            text.pack_start(body, False, False, 0)
        row.pack_start(text, True, True, 0)
        button.add(row)
        button.set_size_request(TOAST_WIDTH, -1)
        button.connect("clicked", lambda *_: self.server.activate(note))
        button.show_all()
        self.box.pack_start(button, False, False, 0)
        self.box.reorder_child(button, 0)   # nejnovější nahoře
        timer = None
        if note.urgency < 2:   # kritická oznámení zůstávají, dokud na ně neklikneš
            delay = note.timeout if note.timeout > 0 else TOAST_SECONDS * 1000
            timer = GLib.timeout_add(min(delay, 15000), self.expire, note.id)
        self.entries[note.id] = (button, timer)
        self.win.show()

    def expire(self, nid):
        entry = self.entries.get(nid)
        if entry:
            self.entries[nid] = (entry[0], None)
            self.drop(nid)
        return False

    def drop(self, nid):
        entry = self.entries.pop(nid, None)
        if not entry:
            return
        widget, timer = entry
        if timer is not None:
            GLib.source_remove(timer)
        self.box.remove(widget)
        if not self.entries:
            self.win.hide()

    def sync(self):
        """Oznámení zavřené jinde (v centru nebo aplikací) zmizí i z bublin."""
        alive = {n.id for n in self.server.items}
        for nid in [i for i in self.entries if i not in alive]:
            self.drop(nid)
        if self.server.dnd:
            for nid in list(self.entries):
                self.drop(nid)


# ----------------------------------------------------------------------------
# Ovládací centrum u pravého okraje
# ----------------------------------------------------------------------------
class ControlCenter(AutoHide):
    """Oznámení, otevřená okna, rychlé přepínače a sloupec vypnout / odhlásit."""

    SESSION = [   # klíč, ikona, popis, chce potvrzení druhým kliknutím
        ("lock", "lock", "Zamknout", False),
        ("suspend", "moon", "Uspat", False),
        ("logout", "signout", "Odhlásit", True),
        ("reboot", "refresh", "Restartovat", True),
        ("poweroff", "power", "Vypnout", True),
    ]

    def __init__(self, app, server, icons):
        self.server, self.icons = server, icons
        self.visible, self.close_timer, self.tick_timer = False, None, None
        self.armed, self.armed_timer = None, None
        self.toggle_busy, self.inhibit = False, None
        self.toasts = None
        self.hyprctl = shutil.which("hyprctl")

        self.win = layer_window(app, "island-center", GtkLayerShell.Edge.RIGHT, EDGE_OVERHANG)
        if GtkLayerShell.is_supported():
            GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.TOP, True)
            GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.BOTTOM, True)
        self.watch_pointer()
        outer = hbox(10)
        outer.set_margin_end(EDGE_OVERHANG)
        self.win.add(outer)
        outer.pack_start(self.build_session(), False, False, 0)

        main = vbox(10)
        main.set_name("center")
        main.set_size_request(CENTER_WIDTH, -1)
        outer.pack_start(main, False, False, 0)
        main.pack_start(self.build_notifications(), True, True, 0)
        main.pack_start(self.build_windows(), False, False, 0)
        main.pack_start(self.build_toggles(), False, False, 0)
        outer.show_all()
        self.session_box, self.main_box = outer.get_children()
        self.input_shape = None
        self.win.connect("size-allocate", self.update_input_region)
        server.on_change.append(self.on_notifications_changed)

    def update_input_region(self, *_):
        """Průhledné místo nad a pod sloupcem vypínání nemá chytat myš ani kliknutí."""
        gdk_win = self.win.get_window()
        if gdk_win is None:
            return
        width, height = self.win.get_allocated_width(), self.win.get_allocated_height()
        main, session = self.main_box.get_allocation(), self.session_box.get_allocation()
        shape = (width, height, main.x, session.x, session.y, session.height)
        if shape == self.input_shape:
            return
        self.input_shape = shape
        region = cairo.Region(cairo.RectangleInt(main.x, 0, max(1, width - main.x), height))
        region.union(cairo.RectangleInt(session.x, session.y, main.x - session.x, session.height))
        gdk_win.input_shape_combine_region(region, 0, 0)

    # ------------------------------------------------------------ vypnout / odhlásit
    def build_session(self):
        column = vbox(8)
        column.set_name("session")
        column.set_valign(Gtk.Align.CENTER)
        self.session_buttons = {}
        for key, icon, title, _confirm in self.SESSION:
            button = css(Gtk.Button(), "flat", "session-btn")
            inner = vbox(3)
            inner.pack_start(label(I[icon], "session-icon"), False, False, 0)
            inner.pack_start(label(title, "session-label"), False, False, 0)
            button.add(inner)
            button.title_label = inner.get_children()[1]
            button.title = title
            button.connect("clicked", lambda _b, k=key: self.session_clicked(k))
            column.pack_start(button, False, False, 0)
            self.session_buttons[key] = button
        return column

    def session_command(self, key):
        if key == "lock":
            for cmd in (("swaylock",), ("hyprlock",), ("loginctl", "lock-session")):
                if shutil.which(cmd[0]):
                    return cmd
            return None
        return {
            "suspend": ("systemctl", "suspend"),
            "logout": (self.hyprctl or "hyprctl", "dispatch", "exit"),
            "reboot": ("systemctl", "reboot"),
            "poweroff": ("systemctl", "poweroff"),
        }[key]

    def session_clicked(self, key):
        confirm = next(c for k, _i, _t, c in self.SESSION if k == key)
        if confirm and self.armed != key:
            self.disarm()
            self.armed = key
            button = self.session_buttons[key]
            set_class(button, "armed", True)
            button.title_label.set_text("Opravdu?")
            self.armed_timer = GLib.timeout_add(3000, self.disarm)
            return
        self.disarm()
        cmd = self.session_command(key)
        self.hide()
        if cmd:
            spawn(*cmd)

    def disarm(self):
        if self.armed_timer is not None:
            GLib.source_remove(self.armed_timer)
            self.armed_timer = None
        if self.armed:
            button = self.session_buttons[self.armed]
            set_class(button, "armed", False)
            button.title_label.set_text(button.title)
            self.armed = None
        return False

    # ------------------------------------------------------------ oznámení
    def build_notifications(self):
        section = vbox(8)
        head = hbox(8)
        self.n_title = label("Oznámení", "section-title", xalign=0)
        head.pack_start(self.n_title, True, True, 0)
        self.n_clear = css(Gtk.Button(label=f"{I['trash']}  Smazat vše"), "flat", "chip-btn")
        self.n_clear.connect("clicked", lambda *_: self.server.clear())
        head.pack_start(self.n_clear, False, False, 0)
        section.pack_start(head, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.n_list = vbox(8)
        self.n_list.set_valign(Gtk.Align.START)
        scroll.add(self.n_list)
        section.pack_start(scroll, True, True, 0)
        return section

    def on_notifications_changed(self):
        if self.visible:
            self.refresh_notifications()

    def refresh_notifications(self):
        for child in self.n_list.get_children():
            self.n_list.remove(child)
        count = len(self.server.items)
        self.n_title.set_text(f"Oznámení ({count})" if count else "Oznámení")
        self.n_clear.set_visible(count > 0)
        if not self.server.active:
            text = (f"Oznámení teď obsluhuje program „{self.server.other}“,\nproto se tady nezobrazují."
                    if self.server.other else "Služba oznámení se nespustila.")
            self.n_list.pack_start(css(label(text, "dim", "empty"), "tile"), False, False, 0)
        elif not count:
            self.n_list.pack_start(css(label("Žádná oznámení", "dim", "empty"), "tile"), False, False, 0)
        groups = {}
        for note in self.server.items:
            groups.setdefault(note.app, []).append(note)
        for app, notes in groups.items():
            self.n_list.pack_start(self.notification_group(app, notes), False, False, 0)
        self.n_list.show_all()

    def notification_group(self, app, notes):
        group = vbox(4, "tile", "notif-group")
        head = hbox(8)
        head.pack_start(notification_image(notes[0], self.icons, 28), False, False, 0)
        head.pack_start(label(app, "notif-app", xalign=0, ellipsize=True), True, True, 0)
        head.pack_start(label(fmt_ago(notes[0].time), "dim"), False, False, 0)
        if len(notes) > 1:
            head.pack_start(label(str(len(notes)), "badge"), False, False, 0)
        close = css(Gtk.Button(label=I["times"]), "flat", "close-btn")
        close.connect("clicked", lambda *_: self.server.remove_app(app))
        head.pack_start(close, False, False, 0)
        group.pack_start(head, False, False, 0)
        for note in notes[:4]:
            line = css(Gtk.Button(), "flat", "notif-line")
            text = label("", xalign=0, ellipsize=True)
            summary = GLib.markup_escape_text(note.summary or note.body)
            body = GLib.markup_escape_text(note.body if note.summary else "")
            text.set_markup(f"<b>{summary}</b>  <span alpha='60%'>{body}</span>" if body else f"<b>{summary}</b>")
            line.add(text)
            line.connect("clicked", lambda _b, n=note: self.server.activate(n))
            group.pack_start(line, False, False, 0)
        if len(notes) > 4:
            group.pack_start(label(f"a dalších {len(notes) - 4}", "dim", xalign=0), False, False, 0)
        return group

    # ------------------------------------------------------------ otevřená okna
    def build_windows(self):
        section = vbox(8)
        self.w_title = label("Otevřená okna", "section-title", xalign=0)
        section.pack_start(self.w_title, False, False, 0)
        scroll = css(Gtk.ScrolledWindow(), "tile", "window-list")
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_propagate_natural_height(True)
        scroll.set_max_content_height(WINDOW_LIST_HEIGHT)
        self.w_list = vbox(2)
        scroll.add(self.w_list)
        section.pack_start(scroll, False, False, 0)
        self.w_signature = None
        return section

    def clients(self):
        if not self.hyprctl:
            return None
        try:
            data = json.loads(run(self.hyprctl, "clients", "-j") or "[]")
        except ValueError:
            return None
        found = []
        for client in data:
            if not client.get("mapped", True) or client.get("hidden", False):
                continue
            workspace = client.get("workspace") or {}
            found.append({
                "address": client.get("address", ""),
                "class": client.get("class") or client.get("initialClass") or "",
                "title": client.get("title") or client.get("class") or "Okno",
                "workspace": workspace.get("id", 0),
                "workspace_name": str(workspace.get("name", "")),
            })
        return sorted(found, key=lambda c: (c["workspace"] < 0, c["workspace"], c["title"].lower()))

    def refresh_windows(self):
        clients = self.clients()
        signature = json.dumps(clients, sort_keys=True)
        if signature == self.w_signature:
            return
        self.w_signature = signature
        for child in self.w_list.get_children():
            self.w_list.remove(child)
        if clients is None:
            self.w_title.set_text("Otevřená okna")
            self.w_list.pack_start(label("Seznam oken je dostupný jen v Hyprlandu", "dim", "empty"), False, False, 0)
        elif not clients:
            self.w_title.set_text("Otevřená okna")
            self.w_list.pack_start(label("Žádná otevřená okna", "dim", "empty"), False, False, 0)
        else:
            self.w_title.set_text(f"Otevřená okna ({len(clients)})")
        for client in clients or []:
            row = hbox(2, "window-row")
            focus = css(Gtk.Button(), "flat", "window-btn")
            inner = hbox(10)
            inner.pack_start(self.icons.image(client["class"], 26), False, False, 0)
            text = vbox(0)
            text.pack_start(label(client["title"], xalign=0, ellipsize=True), False, False, 0)
            place = f"plocha {client['workspace_name'] or client['workspace']}"
            text.pack_start(label(f"{client['class']} · {place}", "dim", "small", xalign=0, ellipsize=True),
                            False, False, 0)
            inner.pack_start(text, True, True, 0)
            focus.add(inner)
            focus.connect("clicked", lambda _b, a=client["address"]: self.focus_window(a))
            close = css(Gtk.Button(label=I["times"]), "flat", "close-btn")
            close.set_valign(Gtk.Align.CENTER)
            close.connect("clicked", lambda _b, a=client["address"]: self.close_window(a))
            row.pack_start(focus, True, True, 0)
            row.pack_start(close, False, False, 0)
            self.w_list.pack_start(row, False, False, 0)
        self.w_list.show_all()

    def focus_window(self, address):
        self.hide()
        if self.hyprctl:
            spawn(self.hyprctl, "dispatch", "focuswindow", f"address:{address}")

    def close_window(self, address):
        if self.hyprctl:
            run(self.hyprctl, "dispatch", "closewindow", f"address:{address}")
        GLib.timeout_add(350, lambda: self.refresh_windows() and False)

    # ------------------------------------------------------------ rychlé přepínače
    def build_toggles(self):
        section = vbox(8)
        section.pack_start(label("Rychlé přepínače", "section-title", xalign=0), False, False, 0)
        row = hbox(8)
        row.set_homogeneous(True)
        nmcli, btctl, wpctl = shutil.which("nmcli"), shutil.which("bluetoothctl"), shutil.which("wpctl")
        inhibit = shutil.which("systemd-inhibit")
        mic = "@DEFAULT_AUDIO_SOURCE@"
        self.toggles = [   # klíč, ikona zapnuto, ikona vypnuto, popis, dostupné, zjisti stav, nastav stav
            ("wifi", "wifi", "wifi", "Wi-Fi", bool(nmcli),
             lambda: "enabled" in run(nmcli, "-t", "-f", "WIFI", "radio"),
             lambda on: run(nmcli, "radio", "wifi", "on" if on else "off", timeout=8)),
            ("bluetooth", "bt", "bt", "Bluetooth", bool(btctl),
             lambda: "Powered: yes" in run(btctl, "show"),
             lambda on: run(btctl, "power", "on" if on else "off", timeout=8)),
            ("mic", "mic", "mic_off", "Mikrofon", bool(wpctl),
             lambda: bool(run(wpctl, "get-volume", mic)) and "MUTED" not in run(wpctl, "get-volume", mic),
             lambda on: run(wpctl, "set-mute", mic, "0" if on else "1")),
            ("dnd", "bell_off", "bell", "Nerušit", True,
             lambda: self.server.dnd,
             self.set_dnd),
            ("awake", "coffee", "coffee", "Neusínat", bool(inhibit),
             lambda: self.inhibit is not None and self.inhibit.poll() is None,
             lambda on: self.set_awake(on, inhibit)),
        ]
        self.toggle_buttons, self.toggle_state = {}, {}
        for key, _on, off, title, available, _get, _set in self.toggles:
            button = css(Gtk.Button(), "flat", "toggle")
            inner = vbox(4)
            icon = label(I[off], "toggle-icon")
            inner.pack_start(icon, False, False, 0)
            inner.pack_start(label(title, "toggle-label"), False, False, 0)
            button.add(inner)
            button.icon = icon
            button.set_sensitive(available)
            button.connect("clicked", lambda _b, k=key: self.toggle_clicked(k))
            row.pack_start(button, True, True, 0)
            self.toggle_buttons[key] = button
        section.pack_start(row, False, False, 0)
        return section

    def set_dnd(self, on):
        self.server.dnd = on
        self.server._changed()

    def set_awake(self, on, program):
        if on and (self.inhibit is None or self.inhibit.poll() is not None):
            try:
                self.inhibit = subprocess.Popen(
                    [program, "--what=idle:sleep", "--who=Island panel", "--why=Zapnuto Neusínat", "sleep", "infinity"],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError:
                self.inhibit = None
        elif not on and self.inhibit is not None:
            self.inhibit.terminate()
            self.inhibit = None

    def show_toggle(self, key, state):
        self.toggle_state[key] = state
        entry = next(t for t in self.toggles if t[0] == key)
        button = self.toggle_buttons[key]
        set_class(button, "on", bool(state))
        button.icon.set_text(I[entry[1] if state else entry[2]])

    def refresh_toggles(self):
        """Stavy se zjišťují na pozadí, některé příkazy (bluetooth, wifi) trvají desetiny vteřiny."""
        if self.toggle_busy:
            return
        self.toggle_busy = True
        jobs = [(t[0], t[5]) for t in self.toggles if t[4]]

        def work():
            results = {}
            for key, getter in jobs:
                try:
                    results[key] = bool(getter())
                except Exception:
                    results[key] = False
            GLib.idle_add(done, results)

        def done(results):
            self.toggle_busy = False
            for key, state in results.items():
                self.show_toggle(key, state)
            return False

        threading.Thread(target=work, daemon=True).start()

    def toggle_clicked(self, key):
        entry = next(t for t in self.toggles if t[0] == key)
        target = not self.toggle_state.get(key, False)
        self.show_toggle(key, target)   # hned ukázat nový stav, skutečný se potvrdí po provedení

        def work():
            try:
                entry[6](target)
            except Exception as err:
                print(f"island-panel: přepínač {key}: {err}", file=sys.stderr)
            GLib.idle_add(lambda: self.refresh_toggles() and False)

        if key in ("dnd", "awake"):
            work()
        else:
            threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------ zobrazení
    def tick(self):
        if not self.visible:
            self.tick_timer = None
            return False
        self.refresh_windows()
        self.refresh_toggles()
        return True

    def show(self, by_key=False):
        self.cancel_close()
        if self.visible:
            return
        self.visible = True
        self.w_signature = None
        if self.toasts is not None:
            self.toasts.dismiss_all()   # oznámení jsou vidět v seznamu, bubliny by ho jen překrývaly
        self.refresh_notifications()
        self.refresh_windows()
        self.refresh_toggles()
        self.win.show()
        if self.tick_timer is None:
            self.tick_timer = GLib.timeout_add_seconds(2, self.tick)
        if not by_key:
            self.close_unless_entered()

    def hide(self):
        self.cancel_close()
        self.disarm()
        if not self.visible:
            return
        self.visible = False
        self.win.hide()

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show(by_key=True)

    def shutdown(self):
        if self.inhibit is not None:
            self.inhibit.terminate()


class RightEdge:
    """Pravý okraj obrazovky: krátké najetí ukáže hlasitost a jas,
    delší setrvání kurzoru na okraji otevře ovládací centrum."""

    ZONE = 4   # kolik pixelů od okraje se ještě počítá jako "na okraji"

    def __init__(self, app, side, center):
        self.side, self.center = side, center
        self.side_timer = self.center_timer = None
        self.on_edge, self.edge_since, self.edge_lost = False, None, 0.0
        self.win = layer_window(app, "island-side-trigger", GtkLayerShell.Edge.RIGHT, EDGE_OVERHANG)
        self.win.set_size_request(SIDE_TRIGGER_WIDTH + EDGE_OVERHANG, SIDE_TRIGGER_HEIGHT)
        self.win.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.win.connect("enter-notify-event", self.on_trigger_enter)
        self.win.connect("leave-notify-event", self.on_trigger_leave)
        self.win.show()
        # Citlivý pruh leží na stejném místě jako pravý kraj obou panelů a může být nad nimi,
        # takže kurzor na pruhu se počítá jako kurzor nad panelem.
        for panel in (side, center):
            if panel is not None:
                panel.companions.append(self.win)
        if side is not None:
            side.win.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
            for name in ("motion-notify-event", "enter-notify-event"):
                side.win.connect(name, self.on_side_pointer)
            side.win.connect("leave-notify-event", self.on_side_leave)

    # --- kurzor na citlivém pruhu
    def on_trigger_enter(self, *_):
        if self.center is not None and self.center.visible:
            self.center.cancel_close()
            return False
        self.at_edge(True)
        if self.side is None:
            return False
        if self.side.visible:
            self.side.cancel_close()
        elif self.side_timer is None:
            self.side_timer = GLib.timeout_add(SIDE_OPEN_DELAY_MS, self.open_side)
        return False

    def on_trigger_leave(self, *_):
        if self.side_timer is not None:
            GLib.source_remove(self.side_timer)
            self.side_timer = None
        self.at_edge(False)
        # kurzor z pruhu buď vjel do otevřeného panelu (ten zavírání zruší), nebo odjel pryč
        for panel in (self.center, self.side):
            if panel is not None and panel.visible:
                panel.on_leave(None, None)
        return False

    def open_side(self):
        self.side_timer = None
        self.side.show()
        return False

    # --- kurzor nad panelem s hlasitostí
    def on_side_pointer(self, *_):
        gdk_win = self.side.win.get_window()
        if gdk_win is None:
            return False
        pointer = gdk_win.get_display().get_default_seat().get_pointer()
        if pointer is None:
            return False
        _win, x, _y, _mask = gdk_win.get_device_position(pointer)
        self.at_edge(x >= self.side.win.get_allocated_width() - EDGE_OVERHANG - self.ZONE)
        return False

    def on_side_leave(self, *_):
        self.at_edge(False)
        return False

    # --- odpočet do otevření ovládacího centra
    def at_edge(self, yes):
        now = time.monotonic()
        if not yes:
            if self.on_edge:
                self.on_edge, self.edge_lost = False, now
            if self.center_timer is not None:
                GLib.source_remove(self.center_timer)
                self.center_timer = None
            return
        if self.center is None or self.center.visible:
            return
        if not self.on_edge:
            self.on_edge = True
            # krátký přechod kurzoru mezi pruhem a panelem s hlasitostí odpočet nepřerušuje
            if self.edge_since is None or now - self.edge_lost > 0.15:
                self.edge_since = now
        if self.center_timer is None:
            remaining = max(1, int(CENTER_OPEN_DELAY_MS - (now - self.edge_since) * 1000))
            self.center_timer = GLib.timeout_add(remaining, self.open_center)

    def open_center(self):
        self.center_timer = None
        self.on_edge, self.edge_since = False, None
        if self.side_timer is not None:
            GLib.source_remove(self.side_timer)
            self.side_timer = None
        if self.side is not None:
            self.side.hide()
        # Kurzor stojí na okraji a některé kompozitory oknu, které se pod stojícím kurzorem
        # teprve objeví, nedají vědět, že je nad ním. Proto se centrum nezavírá samo po chvíli,
        # ale až když kurzor z okraje nebo z centra opravdu odjede.
        self.center.show(by_key=True)
        return False


class Trigger:
    """Neviditelný pruh u okraje obrazovky, který po najetí kurzorem otevře panel."""

    def __init__(self, app, target, namespace, edge, width, height, overhang=0):
        self.target, self.timer = target, None
        self.win = layer_window(app, namespace, edge, overhang)
        self.win.set_size_request(width, height)
        self.win.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.win.connect("enter-notify-event", self.on_enter)
        self.win.connect("leave-notify-event", self.on_leave)
        self.win.show()

    def on_enter(self, *_):
        if self.timer is None:
            self.timer = GLib.timeout_add(OPEN_DELAY_MS, self.fire)
        return False

    def on_leave(self, *_):
        if self.timer is not None:
            GLib.source_remove(self.timer)
            self.timer = None
        return False

    def fire(self):
        self.timer = None
        self.target.show()
        return False


# ----------------------------------------------------------------------------
# Přepínač tapet
# ----------------------------------------------------------------------------
THUMB_H = 2 * max(WALL_BIG_H, WALL_CARD_H)   # výška náhledů uložených v mezipaměti (ostré i na HiDPI displeji)
THUMB_MAX_W = THUMB_H * 8 // 3
WALL_SHADE_COLOR = (0.02, 0.07, 0.10)
PICTURE_EXTS = {".jpg", ".jpeg", ".jpe", ".png", ".webp", ".avif", ".bmp", ".gif", ".tif", ".tiff",
                ".jxl", ".heic", ".heif"}
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi"}

# Barvy pro filtr: klíč, barva čtverečku v liště, rozsah odstínu ve stupních
HUES = [
    ("red", "#bf616a", 345, 15), ("orange", "#d08770", 15, 42), ("yellow", "#ebcb8b", 42, 70),
    ("green", "#a3be8c", 70, 160), ("teal", "#7dc4c0", 160, 200), ("blue", "#6f9bd1", 200, 250),
    ("purple", "#a48ad4", 250, 290), ("pink", "#d48ab8", 290, 345), ("mono", "#9aa7b0", None, None),
]


def fold(text):
    """Text pro hledání: malá písmena bez háčků a čárek."""
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).casefold()


def natural(text):
    """Klíč pro řazení, aby 'tapeta2' byla před 'tapeta10'."""
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", text)]


def processes(*names):
    """Moje běžící programy daného jména: seznam (PID, příkazová řádka)."""
    found, uid = [], os.getuid()
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            if os.stat(f"/proc/{pid}").st_uid != uid:
                continue
            with open(f"/proc/{pid}/comm", encoding="utf-8", errors="replace") as f:
                if f.read().strip() not in names:
                    continue
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                cmd = [a.decode(errors="replace") for a in f.read().split(b"\0") if a]
            if cmd:           # bez příkazové řádky = už ukončený proces
                found.append((int(pid), cmd))
        except OSError:
            continue
    return found


def picture_extensions():
    """Formáty obrázků, které tento systém umí načíst (podle nainstalovaných knihoven)."""
    known = set()
    for fmt in GdkPixbuf.Pixbuf.get_formats():
        if not fmt.is_disabled():
            known.update("." + ext.lower() for ext in fmt.get_extensions())
    return known & PICTURE_EXTS


def dominant_hues(pixbuf):
    """Jaké barvy v obrázku převládají (klíče z HUES), nejvýše dvě a případně 'mono'."""
    side = 24
    small = pixbuf.scale_simple(side, side, GdkPixbuf.InterpType.BILINEAR)
    data, stride, channels = small.get_pixels(), small.get_rowstride(), small.get_n_channels()
    weights, mono = {}, 0
    for y in range(side):
        for x in range(side):
            o = y * stride + x * channels
            hue, sat, val = colorsys.rgb_to_hsv(data[o] / 255, data[o + 1] / 255, data[o + 2] / 255)
            if sat < 0.2 or val < 0.15:
                mono += 1
                continue
            deg = hue * 360
            for key, _color, start, end in HUES:
                if start is None:
                    continue
                if (start <= deg < end) if start < end else (deg >= start or deg < end):
                    weights[key] = weights.get(key, 0.0) + sat * val
                    break
    total = side * side
    ranked = sorted(weights.items(), key=lambda kv: -kv[1])
    hues = []
    if ranked and ranked[0][1] / total >= 0.02:
        hues = [key for key, weight in ranked[:2] if weight >= ranked[0][1] * 0.5]
    if mono / total >= 0.65 or not hues:
        hues.append("mono")
    return hues


def rounded_polygon(cr, points, radius):
    """Cesta mnohoúhelníku se zaoblenými rohy."""
    count = len(points)
    cr.new_sub_path()
    for i in range(count):
        vx, vy = points[i]
        ends = []
        for tx, ty in (points[i - 1], points[(i + 1) % count]):
            dist = math.hypot(tx - vx, ty - vy) or 1.0
            r = min(radius, dist / 2)
            ends.append((vx + (tx - vx) * r / dist, vy + (ty - vy) * r / dist))
        (ax, ay), (bx, by) = ends
        cr.line_to(ax, ay)
        cr.curve_to(ax + (vx - ax) * 0.55, ay + (vy - ay) * 0.55,
                    bx + (vx - bx) * 0.55, by + (vy - by) * 0.55, bx, by)
    cr.close_path()


class WallItem:
    """Jedna tapeta ze složky."""
    __slots__ = ("path", "name", "folder", "kind", "key", "search", "small", "surface", "made_for",
                 "busy", "failed")

    def __init__(self, path, root):
        st = os.stat(path)
        self.path = path
        self.name, ext = os.path.splitext(os.path.basename(path))
        rel = os.path.relpath(path, root)
        self.folder = rel.split(os.sep)[0] if os.sep in rel else ""
        self.kind = "vid" if ext.lower() in VIDEO_EXTS else "pic"
        # klíč náhledu: když se soubor změní, vznikne nový náhled
        self.key = hashlib.sha1(f"{path}|{st.st_mtime_ns}|{st.st_size}|{THUMB_H}".encode()).hexdigest()
        self.search = fold(self.name + " " + self.folder)
        # small = výřez pro úzkou kartu, surface = celý náhled pro vybranou kartu; oba už ve velikosti,
        # v jaké se kreslí (made_for = pro jaké měřítko displeje), takže se při kreslení nemusí zmenšovat
        self.small, self.surface, self.made_for, self.busy, self.failed = None, None, 0, False, False


class Wallpapers:
    """Seznam tapet, jejich náhledy v mezipaměti a nastavení tapety."""

    def __init__(self):
        self.cache = os.path.join(CACHE_DIR, "wallpapers")
        self.index_file = os.path.join(self.cache, "index.json")
        self.state_file = os.path.join(STATE_DIR, "wallpaper")
        self.items, self.by_path = [], {}
        self.exts = picture_extensions()
        self.video = bool(shutil.which("mpvpaper"))    # video tapety jen s programem mpvpaper
        self.video_frames = bool(shutil.which("ffmpegthumbnailer") or shutil.which("ffmpeg"))
        self.scale = 1                                 # měřítko displeje, pro které se náhledy chystají
        self.cond = threading.Condition()
        self.queue, self.warm = [], []                 # náhledy potřeba hned / připravit do zásoby
        self.dirty, self.started = False, False
        self.on_loaded = None
        self.children = []                             # programy s tapetou, které spustil panel
        try:
            with open(self.index_file, encoding="utf-8") as f:
                self.index = json.load(f)
        except (OSError, ValueError):
            self.index = {}
        if not isinstance(self.index, dict):
            self.index = {}

    # --- seznam ---
    def scan(self):
        found, seen, visited = [], set(), set()
        for root in WALLPAPER_DIRS:
            root = os.path.expanduser(root)
            for folder, dirs, files in os.walk(root, followlinks=True):
                real = os.path.realpath(folder)
                if real in visited:          # odkaz vedoucí zpátky do už prošlé složky
                    dirs[:] = []
                    continue
                visited.add(real)
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for name in files:
                    ext = os.path.splitext(name)[1].lower()
                    if name.startswith(".") or not (ext in self.exts or (self.video and ext in VIDEO_EXTS)):
                        continue
                    path = os.path.join(folder, name)
                    if path in seen:
                        continue
                    seen.add(path)
                    try:
                        item = WallItem(path, root)
                    except OSError:
                        continue
                    old = self.by_path.get(path)
                    if old is not None and old.key == item.key:
                        item = old
                    elif self.info(item).get("failed"):
                        item.failed = True      # minule nešel načíst a od té doby se nezměnil
                    found.append(item)
        found.sort(key=lambda i: (natural(i.folder), natural(i.name)))
        self.items = found
        self.by_path = {i.path: i for i in found}

    def info(self, item):
        return self.index.get(item.key) or {}

    def thumb_path(self, item):
        return os.path.join(self.cache, item.key + ".jpg")

    def cached(self, item):
        return item.key in self.index and os.path.exists(self.thumb_path(item))

    # --- náhledy (vytvářejí se ve vedlejších vláknech) ---
    def start(self):
        if not self.started:
            self.started = True
            for _ in range(2):
                threading.Thread(target=self.worker, daemon=True).start()

    def workable(self, item):
        """Dá se pro tapetu vyrobit náhled? (Video bez ffmpegu zůstane jen s ikonou.)"""
        return not item.busy and not item.failed and (item.kind == "pic" or self.video_frames)

    def needs(self, item, big):
        if not self.workable(item):
            return False
        return item.small is None or item.made_for != self.scale or (big and item.surface is None)

    def request(self, wanted):
        """Náhledy, které jsou potřeba hned, v pořadí od nejdůležitějšího: dvojice (tapeta, chci i velký)."""
        self.start()
        with self.cond:
            self.queue = [(item, big) for item, big in wanted if self.needs(item, big)]
            self.cond.notify_all()

    def warm_up(self):
        """Na pozadí připraví náhledy všech tapet, aby první otevření přepínače nečekalo."""
        self.scan()
        self.start()
        with self.cond:
            self.warm = [i for i in self.items if not self.cached(i)]
            self.cond.notify_all()
        return False

    def worker(self):
        while True:
            with self.cond:
                while True:
                    item, keep, big = None, False, False
                    while self.queue and item is None:
                        candidate, big = self.queue.pop(0)
                        if self.needs(candidate, big):
                            item, keep = candidate, True
                    while self.warm and item is None:
                        candidate = self.warm.pop(0)
                        if self.workable(candidate) and not self.cached(candidate):
                            item = candidate
                    if item is not None:
                        break
                    if self.dirty:
                        self.save_index()
                    self.cond.wait()
                item.busy = True
                scale = self.scale
            surfaces, ok = (None, None), True
            try:
                surfaces = self.thumbnail(item, scale if keep else 0, big)
            except Exception as err:   # poškozený nebo nečitelný soubor
                ok = False
                print(f"island-panel: náhled {item.path}: {err}", file=sys.stderr)
                with self.cond:
                    self.index[item.key] = {"failed": True}
                    self.dirty = True
            GLib.idle_add(self.finished, item, surfaces, scale, ok)

    def finished(self, item, surfaces, scale, ok):
        small, large = surfaces
        item.busy = False
        if not ok:
            item.failed = True
        elif small is not None:
            if item.made_for != scale:
                item.surface = None          # velký náhled pro jiné měřítko už neplatí
            item.small, item.made_for = small, scale
            if large is not None:
                item.surface = large
        if self.on_loaded:
            self.on_loaded(item)
        return False

    def thumbnail(self, item, scale, big=False):
        """Vytvoří náhled v mezipaměti (pokud chybí). S měřítkem > 0 vrátí i obrázky připravené
        ke kreslení: výřez pro úzkou kartu a (když je big) celý náhled pro vybranou kartu."""
        os.makedirs(self.cache, exist_ok=True)
        thumb, pixbuf = self.thumb_path(item), None
        if self.cached(item):
            if not scale:
                return None, None
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(thumb)
            except GLib.Error:
                pixbuf = None
        if pixbuf is None:
            source, size = item.path, None
            if item.kind == "vid":
                source = self.video_frame(item)
            else:
                fmt, width, tall = GdkPixbuf.Pixbuf.get_file_info(item.path)
                if fmt is not None:
                    size = [width, tall]
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(source, THUMB_MAX_W, THUMB_H, True)
            finally:
                if source != item.path:
                    os.remove(source)
            pixbuf = pixbuf.apply_embedded_orientation() or pixbuf
            if pixbuf.get_has_alpha():   # průhledná místa podložit tmavou barvou
                pixbuf = pixbuf.composite_color_simple(pixbuf.get_width(), pixbuf.get_height(),
                                                       GdkPixbuf.InterpType.NEAREST, 255, 64, 0x0A1E2C, 0x0A1E2C)
            part = f"{thumb}.{threading.get_ident()}.part"
            pixbuf.savev(part, "jpeg", ["quality"], ["90"])
            os.replace(part, thumb)
            hues = dominant_hues(pixbuf)
            with self.cond:
                self.index[item.key] = {"hues": hues, "size": size}
                self.dirty = True
        if not scale:
            return None, None

        def fit(height):
            height = min(height, pixbuf.get_height())
            if height == pixbuf.get_height():
                return pixbuf
            width = max(1, round(pixbuf.get_width() * height / pixbuf.get_height()))
            return pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        narrow = fit(WALL_CARD_H * scale)
        # z úzké karty je vidět jen prostřední pruh obrázku, zbytek se do paměti nebere
        crop = math.ceil((WALL_CARD_W + abs(WALL_SLANT) * WALL_CARD_H) * scale) + 4
        if narrow.get_width() > crop:
            narrow = narrow.new_subpixbuf((narrow.get_width() - crop) // 2, 0, crop, narrow.get_height())
        small = Gdk.cairo_surface_create_from_pixbuf(narrow, 1, None)
        shade = cairo.Context(small)             # nevybrané karty jsou ztmavené, rovnou to do výřezu zapéct
        shade.set_source_rgba(*WALL_SHADE_COLOR, WALL_SHADE)
        shade.paint()
        large = Gdk.cairo_surface_create_from_pixbuf(fit(WALL_BIG_H * scale), 1, None) if big else None
        return small, large

    def video_frame(self, item):
        """Uloží jeden snímek videa jako obrázek a vrátí cestu k němu."""
        out = os.path.join(self.cache, f"{item.key}.{threading.get_ident()}.frame.jpg")
        if shutil.which("ffmpegthumbnailer"):
            commands = [["ffmpegthumbnailer", "-i", item.path, "-o", out, "-s", "0", "-t", "10%"]]
        else:
            base = ["ffmpeg", "-y", "-loglevel", "error"]
            tail = ["-i", item.path, "-frames:v", "1", "-update", "1", out]
            commands = [base + ["-ss", "2"] + tail, base + tail]
        for cmd in commands:
            try:
                subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, timeout=30)
            except (OSError, subprocess.SubprocessError):
                pass
            if os.path.exists(out) and os.path.getsize(out) > 0:
                return out
        raise RuntimeError("z videa se nepodařilo získat snímek")

    def save_index(self):
        """Uloží poznámky k náhledům a smaže náhledy tapet, které už neexistují (volá se se zámkem)."""
        self.dirty = False
        valid = {i.key for i in self.items}
        if not valid:
            return
        self.index = {k: v for k, v in self.index.items() if k in valid}
        try:
            with open(self.index_file + ".part", "w", encoding="utf-8") as f:
                json.dump(self.index, f)
            os.replace(self.index_file + ".part", self.index_file)
            for name in os.listdir(self.cache):
                if re.fullmatch(r"[0-9a-f]{40}\.jpg", name) and name[:40] not in valid:
                    os.remove(os.path.join(self.cache, name))
        except OSError:
            pass

    def drop_surfaces(self):
        with self.cond:
            self.queue = []
        for item in self.items:
            item.small = item.surface = None

    # --- nastavení tapety ---
    def current(self):
        """Cesta k právě nastavené tapetě."""
        path = read(self.state_file)
        if path:
            return path
        for _pid, cmd in processes("swaybg"):
            for flag, value in zip(cmd, cmd[1:]):
                if flag in ("-i", "--image"):
                    return value
        return ""

    def apply(self, path, remember=True):
        """Nastaví tapetu. Nová se spustí přes starou a stará se ukončí až potom, takže plocha neproblikne."""
        old = [pid for pid, _cmd in processes("swaybg", "mpvpaper")]
        if os.path.splitext(path)[1].lower() in VIDEO_EXTS:
            cmd = ["mpvpaper", "-o", WALL_VIDEO_OPTIONS, "*", path]
        else:
            cmd = ["swaybg", "-i", path, "-m", WALL_FILL_MODE]
        try:
            self.children.append(subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                                  stderr=subprocess.DEVNULL, start_new_session=True))
        except OSError as err:
            print(f"island-panel: {cmd[0]}: {err}", file=sys.stderr)
            return
        GLib.timeout_add(900, self.stop, old)
        if remember:
            try:
                os.makedirs(STATE_DIR, exist_ok=True)
                with open(self.state_file, "w", encoding="utf-8") as f:
                    f.write(path + "\n")
            except OSError as err:
                print(f"island-panel: {self.state_file}: {err}", file=sys.stderr)

    def stop(self, pids):
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
        GLib.timeout_add(1000, self.reap)
        return False

    def reap(self):
        """Vyzvedne ukončené programy, které spustil panel, aby po nich v systému nezůstávaly mrtvé záznamy."""
        self.children = [child for child in self.children if child.poll() is None]
        return False

    def restore(self):
        """Po startu vrátí naposledy vybranou tapetu (pokud už neběží)."""
        path = read(self.state_file)
        if not path or not os.path.isfile(path):
            return
        if any(path in cmd for _pid, cmd in processes("swaybg", "mpvpaper")):
            return
        self.apply(path, remember=False)

    def step(self, delta=None):
        """Další / předchozí tapeta bez otevírání přepínače; bez čísla náhodná."""
        self.scan()
        if not self.items:
            return
        current = self.by_path.get(self.current())
        if delta is None:
            choice = random.choice([i for i in self.items if i is not current] or self.items)
        else:
            index = self.items.index(current) if current is not None else -1
            choice = self.items[(index + delta) % len(self.items)]
        self.apply(choice.path)


class WallpaperPicker:
    """Přepínač tapet: pás zkosených náhledů přes celou šířku obrazovky, vybraný je uprostřed větší."""

    def __init__(self, app, store):
        self.store = store
        store.on_loaded = self.on_loaded
        self.visible = False
        self.items, self.sel, self.pos = [], 0, 0.0       # pos se plynule dotahuje k sel
        self.cards, self.hover, self.appear = [], -1, 1.0
        self.filter, self.hue, self.query, self.current = "all", None, "", ""
        self.filters, self.chips, self.swatches = [], {}, {}
        self.tick_id, self.last_time, self.scroll = None, 0.0, 0.0
        self.drop_timer, self.refresh_timer = None, None
        self.layouts = {}
        self.pressed, self.outside = -1, False        # na čem byl stisknut knoflík myši

        self.win = layer_window(app, "island-wall")
        if GtkLayerShell.is_supported():
            for edge in (GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT, GtkLayerShell.Edge.BOTTOM):
                GtkLayerShell.set_anchor(self.win, edge, True)
            GtkLayerShell.set_keyboard_mode(self.win, GtkLayerShell.KeyboardMode.EXCLUSIVE)
        self.win.add_events(Gdk.EventMask.KEY_PRESS_MASK | Gdk.EventMask.BUTTON_PRESS_MASK
                            | Gdk.EventMask.BUTTON_RELEASE_MASK
                            | Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)
        self.win.connect("draw", self.draw_dim)
        self.win.connect("key-press-event", self.on_key)
        self.win.connect("scroll-event", self.on_scroll)
        self.win.connect("button-press-event", self.on_outside_press)   # klik mimo = zavřít
        self.win.connect("button-release-event", self.on_outside_release)
        self.win.connect("notify::scale-factor", lambda *_: self.want())

        root = vbox(12)
        root.set_valign(Gtk.Align.CENTER)
        self.win.add(root)

        # --- lišta s filtry ---
        holder = Gtk.EventBox()
        holder.set_visible_window(False)
        holder.set_halign(Gtk.Align.CENTER)
        holder.connect("button-press-event", lambda *_: True)
        bar = hbox(8)
        bar.set_name("wall-bar")
        holder.add(bar)
        self.chip_box = hbox(2)
        bar.pack_start(self.chip_box, False, False, 0)
        bar.pack_start(css(Gtk.Box(), "wall-sep"), False, False, 0)
        for icon, action in (("shuffle", self.random), ("folder", self.open_folder)):
            btn = self.button(label(I[icon]), "flat", "wall-icon")
            btn.connect("clicked", lambda _b, a=action: a())
            bar.pack_start(btn, False, False, 0)
        bar.pack_start(css(Gtk.Box(), "wall-sep"), False, False, 0)
        swatch_box = hbox(5)
        swatch_box.set_valign(Gtk.Align.CENTER)
        for key, color, _start, _end in HUES:
            btn = self.button(None, "wall-swatch")
            provider = Gtk.CssProvider()
            provider.load_from_data(f"button {{ background-color: {color}; }}".encode())
            btn.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER + 1)
            btn.connect("clicked", lambda _b, k=key: self.set_hue(k))
            swatch_box.pack_start(btn, False, False, 0)
            self.swatches[key] = btn
        bar.pack_start(swatch_box, False, False, 0)
        bar.pack_start(css(Gtk.Box(), "wall-sep"), False, False, 0)
        self.query_label = label("", "wall-query")
        self.query_label.set_no_show_all(True)
        bar.pack_start(self.query_label, False, False, 0)
        self.count = label("0", "wall-count")
        bar.pack_start(self.count, False, False, 0)
        root.pack_start(holder, False, False, 0)

        # --- pás náhledů ---
        self.area = Gtk.DrawingArea()
        self.area.set_size_request(-1, max(WALL_BIG_H, WALL_CARD_H) + 28)
        self.area.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_PRESS_MASK
                             | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.ENTER_NOTIFY_MASK
                             | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.area.connect("draw", self.on_draw)
        self.area.connect("motion-notify-event", self.on_motion)
        self.area.connect("enter-notify-event", self.on_motion)
        self.area.connect("leave-notify-event", self.on_area_leave)
        self.area.connect("button-press-event", self.on_press)
        self.area.connect("button-release-event", self.on_release)
        self.area.connect("size-allocate", lambda *_: self.want())
        root.pack_start(self.area, False, False, 0)

        # --- popisek ---
        caption = self.caption = vbox(1)
        caption.set_name("wall-caption")
        caption.set_halign(Gtk.Align.CENTER)
        self.name_label = label("", "wall-name")
        self.info_label = label("", "dim", "small")
        caption.pack_start(self.name_label, False, False, 0)
        caption.pack_start(self.info_label, False, False, 0)
        root.pack_start(caption, False, False, 0)
        hint = label("← →  vybrat      Enter  nastavit      Mezerník  náhled"
                     "      písmena  hledat      Esc  zavřít", "wall-hint")
        hint.set_halign(Gtk.Align.CENTER)
        root.pack_start(hint, False, False, 0)
        root.show_all()

    @staticmethod
    def button(child, *classes):
        btn = Gtk.Button()
        if child is not None:
            btn.add(child)
        btn.set_can_focus(False)      # klávesy patří celému přepínači, ne tlačítkům
        return css(btn, *classes)

    # --- co se zobrazuje ---
    def build_chips(self):
        """Filtry v liště: vše, obrázky / videa (jsou-li nějaká videa) a podsložky."""
        for child in self.chip_box.get_children():
            self.chip_box.remove(child)
        self.filters = [("all", "VŠE")]
        if any(i.kind == "vid" for i in self.store.items):
            self.filters += [("pic", "OBR"), ("vid", "VID")]
        folders = sorted({i.folder for i in self.store.items if i.folder}, key=natural)
        self.filters += [("dir:" + name, name.upper()[:14]) for name in folders[:8]]
        if self.filter not in [key for key, _text in self.filters]:
            self.filter = "all"
        self.chips = {}
        for key, text in self.filters:
            btn = self.button(label(text), "flat", "wall-chip")
            btn.connect("clicked", lambda _b, k=key: self.set_filter(k))
            self.chip_box.pack_start(btn, False, False, 0)
            self.chips[key] = btn
        self.chip_box.show_all()

    def matches(self, item):
        if item.failed:                       # poškozený soubor, nejde načíst
            return False
        if self.filter in ("pic", "vid") and item.kind != self.filter:
            return False
        if self.filter.startswith("dir:") and item.folder != self.filter[4:]:
            return False
        return not self.query or fold(self.query) in item.search

    def refilter(self, keep=None, soft=False):
        """Sestaví seznam podle filtrů; vybraná tapeta zůstane vybraná, pokud ve výběru zbyla.

        soft = jen obnovit (přibyly údaje o barvách); když se seznam nezměnil, nic se nehýbe."""
        if keep is None and self.items:
            keep = self.items[min(self.sel, len(self.items) - 1)]
        before = self.items
        base = [i for i in self.store.items if self.matches(i)]
        present = set()
        for item in base:
            present.update(self.store.info(item).get("hues") or ())
        if self.hue:
            self.items = [i for i in base if self.hue in (self.store.info(i).get("hues") or ())]
        else:
            self.items = base
        for key, btn in self.chips.items():
            set_class(btn, "active", key == self.filter)
        for key, btn in self.swatches.items():
            btn.set_sensitive(key in present or key == self.hue)
            set_class(btn, "active", key == self.hue)
        self.count.set_text(str(len(self.items)))
        self.query_label.set_text(f"{I['search']} {self.query}")
        self.query_label.set_visible(bool(self.query))
        if soft and len(before) == len(self.items) and all(a is b for a, b in zip(before, self.items)):
            self.update_caption()
            return
        index = next((n for n, i in enumerate(self.items) if i is keep), 0)
        self.select(index, jump=True)

    def set_filter(self, key):
        self.filter = key
        self.refilter()

    def set_hue(self, key):
        self.hue = None if self.hue == key else key
        self.refilter()

    def select(self, index, jump=False):
        count = len(self.items)
        self.sel = min(max(index, 0), count - 1) if count else 0
        if jump or not count:
            self.pos = float(self.sel)
        elif abs(self.sel - self.pos) > 10:      # dlouhý skok: většinu cesty přeskočit, zbytek dojet
            self.pos = self.sel - math.copysign(10, self.sel - self.pos)
        self.update_caption()
        self.want()
        self.animate()

    def move(self, delta):
        self.select(self.sel + delta)

    def update_caption(self):
        self.caption.set_opacity(1.0 if self.items else 0.0)   # bez tapet popisek skrýt (místo mu zůstane)
        if not self.items:
            return
        item = self.items[self.sel]
        parts = [f"{self.sel + 1} / {len(self.items)}"]
        size = self.store.info(item).get("size")
        if size:
            parts.append(f"{size[0]} × {size[1]}")
        if item.folder:
            parts.append(item.folder)
        if item.path == self.current:
            parts.append("nastavená")
        self.name_label.set_text(item.name)
        self.info_label.set_text("   ·   ".join(parts))

    def want(self):
        """Řekne si o náhledy kolem vybrané tapety a ty hodně vzdálené uvolní z paměti."""
        count = len(self.items)
        if not self.visible or not count:
            return
        self.store.scale = self.win.get_scale_factor()
        width = self.area.get_allocated_width()
        reach = int((width if width > 1 else 1920) / (WALL_CARD_W + WALL_GAP)) // 2 + 6
        near = sorted(range(max(0, self.sel - reach), min(count, self.sel + reach + 1)),
                      key=lambda i: abs(i - self.sel))
        # velký náhled jen pro vybranou kartu a pár sousedů, na které se dá hned přejít
        self.store.request([(self.items[i], abs(i - self.sel) <= 3) for i in near])
        keep = {id(i) for i in self.items[max(0, self.sel - reach - 8):self.sel + reach + 9]}
        keep_big = {id(i) for i in self.items[max(0, self.sel - 6):self.sel + 7]}
        for item in self.store.items:
            if item.small is not None and id(item) not in keep:
                item.small = item.surface = None
            elif item.surface is not None and id(item) not in keep_big:
                item.surface = None

    def on_loaded(self, item):
        if not self.visible:
            return
        if item.failed:
            self.refilter(soft=True)
        self.area.queue_draw()
        self.want()
        if self.refresh_timer is None:      # nově spočítané barvy promítnout do filtru, ale ne po každém obrázku
            self.refresh_timer = GLib.timeout_add(400, self.refresh)

    def refresh(self):
        self.refresh_timer = None
        if self.visible:
            self.refilter(soft=True)
        return False

    # --- kreslení ---
    def draw_dim(self, _win, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0.01, 0.04, 0.06, WALL_DIM)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        return False

    def palette(self):
        ctx = self.area.get_style_context()
        colors = {}
        for name, fallback in (("accent", (0.49, 0.75, 0.86)), ("fg", (0.86, 0.91, 0.93)),
                               ("pill", (0.90, 0.93, 0.95)), ("pill_fg", (0.04, 0.12, 0.17))):
            found, rgba = ctx.lookup_color(name)
            colors[name] = (rgba.red, rgba.green, rgba.blue) if found else fallback
        return colors

    def card_size(self, index):
        focus = max(0.0, 1.0 - abs(index - self.pos))
        focus = focus * focus * (3 - 2 * focus)
        return (WALL_CARD_W + (WALL_BIG_W - WALL_CARD_W) * focus,
                WALL_CARD_H + (WALL_BIG_H - WALL_CARD_H) * focus, focus)

    def layout(self, width):
        """Karty, které jsou vidět: (pořadí, střed x, šířka, výška, jak moc je vybraná 0-1)."""
        count = len(self.items)
        if not count:
            return []
        pos = min(max(self.pos, 0.0), count - 1.0)
        base = min(int(pos), count - 1)
        reach = int(width / (WALL_CARD_W + WALL_GAP)) // 2 + 3
        first, last = max(0, base - reach), min(count - 1, base + 1 + reach)
        cards, x = [], 0.0
        for index in range(first, last + 1):
            w, h, focus = self.card_size(index)
            cards.append([index, x + w / 2, w, h, focus])
            x += w + WALL_GAP
        anchor = cards[base - first][1]
        if base + 1 <= last:
            anchor += (cards[base + 1 - first][1] - anchor) * (pos - base)
        spread = 0.86 + 0.14 * (1 - (1 - self.appear) ** 3)      # při otevření se karty rozjedou od středu
        reach_x = abs(WALL_SLANT) * max(WALL_BIG_H, WALL_CARD_H) / 2
        visible = []
        for index, cx, w, h, focus in cards:
            cx = width / 2 + (cx - anchor) * spread
            if cx + w / 2 + reach_x > 0 and cx - w / 2 - reach_x < width:
                visible.append((index, cx, w, h, focus))
        return visible

    def text_layout(self, text, size, bold=True):
        key = (text, size, bold)
        if key not in self.layouts:
            layout = self.area.create_pango_layout(text)
            font = self.area.get_pango_context().get_font_description().copy()
            font.set_absolute_size(size * Pango.SCALE)
            font.set_weight(Pango.Weight.BOLD if bold else Pango.Weight.NORMAL)
            layout.set_font_description(font)
            self.layouts[key] = layout
        return self.layouts[key]

    def on_draw(self, area, cr):
        width, height = area.get_allocated_width(), area.get_allocated_height()
        self.cards = self.layout(width)
        if not self.cards:
            self.draw_message(cr, width, height)
            return False
        colors, device = self.palette(), area.get_scale_factor()
        cy = height / 2 + (1 - self.appear) ** 3 * 12
        for index, cx, w, h, focus in self.cards:
            # karty u okrajů obrazovky se ztrácejí do průhledna
            alpha = min(1.0, max(0.0, min(cx, width - cx) / WALL_EDGE_FADE)) if WALL_EDGE_FADE else 1.0
            if alpha <= 0.01:
                continue
            if alpha < 1.0:
                reach = w / 2 + abs(WALL_SLANT) * h / 2 + 2
                cr.save()
                cr.rectangle(cx - reach, cy - h / 2 - 2, 2 * reach, h + 4)
                cr.clip()
                cr.push_group()
                self.draw_card(cr, colors, device, index, cx, cy, w, h, focus)
                cr.pop_group_to_source()
                cr.paint_with_alpha(alpha)
                cr.restore()
            else:
                self.draw_card(cr, colors, device, index, cx, cy, w, h, focus)
        return False

    def draw_message(self, cr, width, height):
        if self.store.items:
            text = "Filtru neodpovídá žádná tapeta"
        else:
            text = "Ve složce " + ", ".join(WALLPAPER_DIRS) + " nejsou žádné obrázky"
        layout = self.text_layout(text, 14, bold=False)
        tw, th = layout.get_pixel_size()
        x, y, w, h = (width - tw) / 2 - 22, (height - th) / 2 - 14, tw + 44, th + 28
        rounded_polygon(cr, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], 14)
        cr.set_source_rgba(0.04, 0.12, 0.17, 0.93)
        cr.fill_preserve()
        cr.set_source_rgba(0.49, 0.75, 0.86, 0.25)
        cr.set_line_width(1)
        cr.stroke()
        cr.set_source_rgb(0.86, 0.91, 0.93)
        cr.move_to((width - tw) / 2, (height - th) / 2)
        PangoCairo.show_layout(cr, layout)

    def draw_card(self, cr, colors, device, index, cx, cy, w, h, focus):
        item = self.items[index]
        lean = WALL_SLANT * h / 2
        corners = [(cx - w / 2 + lean, cy - h / 2), (cx + w / 2 + lean, cy - h / 2),
                   (cx + w / 2 - lean, cy + h / 2), (cx - w / 2 - lean, cy + h / 2)]
        rounded_polygon(cr, corners, WALL_RADIUS * (0.6 + 0.4 * focus))
        # Úzká karta v klidu má vlastní výřez přesně ve své velikosti (už ztmavený), vybraná celý náhled.
        # Oba se tak kreslí bod na bod, rychle a ostře; přepočítávají se jen karty, které mění velikost.
        image = item.small if focus < 0.001 and item.small is not None else item.surface or item.small
        if image is not None:
            sw, sh = image.get_width(), image.get_height()
            scale = max((w + 2 * abs(lean)) / sw, h / sh)
            # posun zaokrouhlený na celé pixely displeje
            x0 = round((cx - sw * scale / 2) * device) / device
            y0 = round((cy - sh * scale / 2) * device) / device
            pattern = cairo.SurfacePattern(image)
            pattern.set_matrix(cairo.Matrix(xx=1 / scale, yy=1 / scale, x0=-x0 / scale, y0=-y0 / scale))
            pattern.set_filter(cairo.FILTER_BILINEAR)
            cr.set_source(pattern)
        else:
            cr.set_source_rgba(0.05, 0.14, 0.20, 0.95)
        cr.fill_preserve()
        shade = 0.0 if image is item.small and image is not None else WALL_SHADE * (1 - focus)
        if shade > 0.004:
            cr.set_source_rgba(*WALL_SHADE_COLOR, shade)
            cr.fill_preserve()
        if index == self.hover and focus < 0.999:      # karta pod kurzorem trochu zesvětlá
            cr.set_source_rgba(1, 1, 1, 0.08 * (1 - focus))
            cr.fill_preserve()
        # okraj: u vybrané karty silnější a světlejší
        glow = max(focus, 0.4 if index == self.hover else 0.0)
        cr.set_source_rgba(*colors["accent"], 0.28 + 0.62 * glow)
        cr.set_line_width(1 + focus)
        cr.stroke()
        if image is None:
            icon = self.text_layout(I["film" if item.kind == "vid" else "image"], 20, bold=False)
            tw, th = icon.get_pixel_size()
            cr.set_source_rgba(*colors["fg"], 0.25)
            cr.move_to(cx - tw / 2, cy - th / 2)
            PangoCairo.show_layout(cr, icon)
        # štítky v levém horním rohu (levá hrana je šikmá, proto se x počítá podle výšky)
        x = cx - w / 2 + WALL_SLANT * (h / 2 - (7 if WALL_SLANT > 0 else 23)) + 7
        y = cy - h / 2 + 7
        tags = []
        if WALL_TAGS:
            tags.append(("VID" if item.kind == "vid" else "PIC", False))
        if item.path == self.current:
            tags.append((I["check"], True))
        for text, light in tags:
            layout = self.text_layout(text, 9)
            tw, th = layout.get_pixel_size()
            bw, bh = tw + 10, 16
            rounded_polygon(cr, [(x, y), (x + bw, y), (x + bw, y + bh), (x, y + bh)], 5)
            if light:
                cr.set_source_rgba(*colors["pill"], 0.95)
            else:
                cr.set_source_rgba(0.04, 0.12, 0.17, 0.78)
            cr.fill()
            cr.set_source_rgb(*(colors["pill_fg"] if light else colors["fg"]))
            cr.move_to(x + 5, y + (bh - th) / 2)
            PangoCairo.show_layout(cr, layout)
            x += bw + 4

    # --- animace ---
    def animate(self):
        if self.tick_id is None and self.visible:
            self.last_time = 0.0
            self.tick_id = self.area.add_tick_callback(self.on_tick)
        self.area.queue_draw()

    def on_tick(self, _area, clock):
        now = clock.get_frame_time() / 1e6
        dt = min(0.05, now - self.last_time) if self.last_time else 1 / 60
        self.last_time = now
        moving = False
        if self.appear < 1.0:
            self.appear = min(1.0, self.appear + dt / 0.30)
            moving = True
        gap = self.sel - self.pos
        if abs(gap) > 0.002:
            self.pos += gap * (1 - math.exp(-dt * 13))
            moving = True
        else:
            self.pos = float(self.sel)
        self.area.queue_draw()
        if not moving:
            self.tick_id = None
            return GLib.SOURCE_REMOVE
        return GLib.SOURCE_CONTINUE

    # --- myš ---
    def card_at(self, x, y):
        cy = self.area.get_allocated_height() / 2
        for index, cx, w, h, _focus in self.cards:
            if abs(y - cy) <= h / 2 and abs(x - WALL_SLANT * (cy - y) - cx) <= w / 2:
                return index
        return -1

    def on_motion(self, _area, event):
        hover = self.card_at(event.x, event.y)
        if hover != self.hover:
            self.hover = hover
            self.area.queue_draw()
        return False

    def on_area_leave(self, *_):
        if self.hover != -1:
            self.hover = -1
            self.area.queue_draw()
        return False

    # Na kliknutí se reaguje až při uvolnění tlačítka. Kdyby se okno schovalo už při stisku,
    # GTK by si dál myslelo, že je tlačítko stisknuté, a po dalším otevření by první klik šel jinam.
    def on_press(self, _area, event):
        self.pressed = self.card_at(event.x, event.y) if event.button == 1 else -1
        return self.pressed >= 0              # mimo karty: bere se jako klik vedle (zavřít)

    def on_release(self, _area, event):
        index, self.pressed = self.pressed, -1
        if index < 0 or event.button != 1:
            return False
        if index == self.card_at(event.x, event.y):
            if index == self.sel:
                self.apply(close=True)        # klik na vybranou = nastavit
            else:
                self.select(index)            # klik na jinou = vybrat
        return True

    def on_outside_press(self, _win, event):
        self.outside = event.type == Gdk.EventType.BUTTON_PRESS
        return True

    def on_outside_release(self, _win, _event):
        if self.outside:
            self.outside = False
            self.hide()
        return True

    def on_scroll(self, _win, event):
        if event.direction == Gdk.ScrollDirection.SMOOTH:
            # touchpad posílá drobné kousky, kolečko myši jeden větší: sčítat a po překročení
            # jedné "zarážky" se posunout o jednu tapetu (zbytek zahodit, ať kolečko nepřeskakuje)
            _ok, dx, dy = event.get_scroll_deltas()
            self.scroll += dx if abs(dx) > abs(dy) else dy
            if event.is_stop:
                self.scroll = 0.0
            elif abs(self.scroll) >= 1.0:
                step = 1 if self.scroll > 0 else -1
                self.scroll = 0.0
                self.move(step)
        elif event.get_pointer_emulated():
            pass          # kolečko přijde dvakrát (plynule i po krocích), bereme jen to plynulé
        elif event.direction in (Gdk.ScrollDirection.DOWN, Gdk.ScrollDirection.RIGHT):
            self.move(1)
        elif event.direction in (Gdk.ScrollDirection.UP, Gdk.ScrollDirection.LEFT):
            self.move(-1)
        return True

    # --- klávesnice ---
    def on_key(self, _win, event):
        key = event.keyval
        mods = event.state & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK | Gdk.ModifierType.SUPER_MASK)
        if key == Gdk.KEY_Escape:
            if self.query:
                self.query = ""
                self.refilter()
            else:
                self.hide()
        elif key in (Gdk.KEY_Left, Gdk.KEY_KP_Left):
            self.move(-1)
        elif key in (Gdk.KEY_Right, Gdk.KEY_KP_Right):
            self.move(1)
        elif key in (Gdk.KEY_Up, Gdk.KEY_Page_Up):
            self.move(-5)
        elif key in (Gdk.KEY_Down, Gdk.KEY_Page_Down):
            self.move(5)
        elif key == Gdk.KEY_Home:
            self.select(0)
        elif key == Gdk.KEY_End:
            self.select(len(self.items) - 1)
        elif key in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self.apply(close=True)
        elif key == Gdk.KEY_space and not self.query:
            self.apply(close=False)
        elif key in (Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab):
            keys = [k for k, _text in self.filters]
            step = -1 if key == Gdk.KEY_ISO_Left_Tab else 1
            self.set_filter(keys[(keys.index(self.filter) + step) % len(keys)])
        elif key == Gdk.KEY_F5 or (key in (Gdk.KEY_r, Gdk.KEY_R) and mods == Gdk.ModifierType.CONTROL_MASK):
            self.random()
        elif key == Gdk.KEY_BackSpace:
            if self.query:
                self.query = self.query[:-1]
                self.refilter()
        elif not mods:
            char = chr(Gdk.keyval_to_unicode(key) or 0)
            if char.isprintable() and (char != " " or self.query) and len(self.query) < 40:
                self.query += char
                self.refilter()
        return True

    # --- akce ---
    def apply(self, close):
        if not self.items:
            return
        item = self.items[self.sel]
        self.store.apply(item.path)
        self.current = item.path
        if close:
            self.hide()
        else:
            self.update_caption()
            self.area.queue_draw()

    def random(self):
        if len(self.items) > 1:
            self.select(random.choice([i for i in range(len(self.items)) if i != self.sel]))
            self.apply(close=False)

    def open_folder(self):
        folder = os.path.dirname(self.items[self.sel].path) if self.items else os.path.expanduser(WALLPAPER_DIRS[0])
        spawn("xdg-open", folder)
        self.hide()

    def show(self):
        if self.visible:
            return
        if self.drop_timer is not None:
            GLib.source_remove(self.drop_timer)
            self.drop_timer = None
        self.store.scan()
        self.current = self.store.current()
        self.query, self.hue, self.hover, self.scroll = "", None, -1, 0.0
        self.pressed, self.outside = -1, False
        self.build_chips()
        self.visible = True
        self.appear = 0.0
        self.refilter(keep=self.store.by_path.get(self.current))
        self.win.show()

    def hide(self):
        if not self.visible:
            return
        self.visible = False
        if self.tick_id is not None:
            self.area.remove_tick_callback(self.tick_id)
            self.tick_id = None
        self.win.hide()
        self.store.request([])
        # náhledy ještě chvíli držet v paměti, kdyby se přepínač hned otevřel znovu
        self.drop_timer = GLib.timeout_add_seconds(30, self.drop)

    def drop(self):
        self.drop_timer = None
        self.store.drop_surfaces()
        return False

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show()


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="io.github.island_panel",
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.panel = self.trigger = self.side = self.center = self.edge = self.css_monitor = None
        self.server = self.toasts = self.icons = None
        self.walls = self.picker = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-theme-name", "Adwaita")   # stejný základ bez ohledu na systémové GTK téma
        settings.set_property("gtk-application-prefer-dark-theme", True)
        self.provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.provider,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_USER)
        style = Gio.File.new_for_path(os.path.join(HERE, "style.css"))
        self.load_css(style)
        self.css_monitor = style.monitor_file(Gio.FileMonitorFlags.NONE, None)
        self.css_monitor.connect("changed", lambda _m, f, _o, ev: ev in (
            Gio.FileMonitorEvent.CHANGES_DONE_HINT, Gio.FileMonitorEvent.CREATED) and self.load_css(style))
        self.panel = Panel(self)
        self.trigger = Trigger(self, self.panel, "island-panel-trigger", GtkLayerShell.Edge.TOP,
                               TRIGGER_WIDTH, TRIGGER_HEIGHT)
        self.icons = IconIndex()
        self.server = NotificationServer(own=NOTIFICATIONS_ENABLED)
        if NOTIFICATIONS_ENABLED:
            self.toasts = Toasts(self, self.server, self.icons)
        if SIDE_ENABLED:
            self.side = SidePanel(self)
        if CENTER_ENABLED:
            self.center = ControlCenter(self, self.server, self.icons)
            if self.toasts is not None:
                self.center.toasts = self.toasts
                self.toasts.blocked = lambda: self.center.visible
        if self.side or self.center:
            self.edge = RightEdge(self, self.side, self.center)
        if WALL_ENABLED:
            self.walls = Wallpapers()
            self.walls.restore()                               # po přihlášení vrátit vybranou tapetu
            self.picker = WallpaperPicker(self, self.walls)
            GLib.timeout_add_seconds(5, self.walls.warm_up)    # náhledy připravit předem na pozadí
        self.hold()

    def do_shutdown(self):
        if self.center:
            self.center.shutdown()
        Gtk.Application.do_shutdown(self)

    def load_css(self, style):
        try:
            self.provider.load_from_file(style)
        except GLib.Error as err:
            print(f"island-panel: chyba ve style.css: {err.message}", file=sys.stderr)

    def do_command_line(self, command_line):
        args = command_line.get_arguments()[1:]
        if "--quit" in args:
            self.quit()
        elif "--wallpapers" in args:
            if self.picker:
                self.picker.toggle()
        elif "--wallpaper-next" in args or "--wallpaper-prev" in args or "--wallpaper-random" in args:
            if self.walls:
                if self.picker:
                    self.picker.hide()
                self.walls.step(None if "--wallpaper-random" in args else 1 if "--wallpaper-next" in args else -1)
        elif "--toggle" in args:
            self.panel.toggle()
        elif "--apps" in args:
            if self.panel.visible and self.panel.tab == "apps":
                self.panel.hide()
            else:
                self.panel.show(by_key=True, tab="apps")
        elif "--side" in args:
            if self.side:
                self.side.toggle()
        elif "--center" in args:
            if self.center:
                self.center.toggle()
        elif "--show" in args:
            self.panel.show(by_key=True)
        elif "--hide" in args:
            self.panel.hide()
        return 0


if __name__ == "__main__":
    sys.exit(App().run(sys.argv))
