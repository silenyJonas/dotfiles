#!/usr/bin/env python3
"""
Island panel: rozbalovací panel pro Hyprland ve stylu ostrůvků Waybaru.

Najetím kurzoru na horní okraj obrazovky (uprostřed) panel vyjede dolů,
po odjetí kurzoru se zase schová. Záložky: Dashboard, Media, Performance, Apps.

Najetím na pravý okraj (uprostřed výšky) vyjede úzký boční panel
s hlasitostí a jasem. Když kurzor na okraji zůstane asi vteřinu, otevře se
ovládací centrum: oznámení, otevřená okna, rychlé přepínače a vypnutí.

Okno Wi-Fi a Bluetooth (--wifi, --bluetooth) vyjede pod pravým koncem lišty:
seznam sítí s připojením a heslem, seznam Bluetooth zařízení s připojením a párováním.

Přepínač tapet (--wallpapers) ukáže přes celou šířku obrazovky pás náhledů
ze složky s tapetami; vybraná se nastaví Enterem nebo kliknutím.

Spuštění:   python3 panel.py            (běží na pozadí)
Ovládání:   python3 panel.py --toggle   (otevřít / zavřít, třeba z klávesové zkratky)
            python3 panel.py --apps     (otevřít rovnou na seznamu aplikací s hledáním)
            python3 panel.py --side     (otevřít / zavřít boční panel s hlasitostí a jasem)
            python3 panel.py --center   (otevřít / zavřít ovládací centrum)
            python3 panel.py --wifi     (otevřít / zavřít okno se sítěmi Wi-Fi)
            python3 panel.py --bluetooth  (otevřít / zavřít okno s Bluetooth zařízeními)
            python3 panel.py --wallpapers        (otevřít / zavřít přepínač tapet)
            python3 panel.py --wallpaper-next    (další tapeta bez otevírání přepínače)
            python3 panel.py --wallpaper-prev    (předchozí tapeta)
            python3 panel.py --wallpaper-random  (náhodná tapeta)
            python3 panel.py --quit     (ukončit)

Vzhled se upravuje v souboru style.css vedle tohoto skriptu, změny se načtou samy.
"""

import base64
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
import secrets
import re
import shlex
import shutil
import signal
import socket
import struct
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
PANEL_WIDTH = 760        # šířka panelu v pixelech
TRIGGER_WIDTH = 760      # šířka citlivého pruhu u horního okraje (je uprostřed)
TRIGGER_HEIGHT = 3       # výška citlivého pruhu
OPEN_DELAY_MS = 120      # jak dlouho musí kurzor na pruhu zůstat, než panel vyjede
CLOSE_DELAY_MS = 350     # za jak dlouho po odjetí kurzoru se panel schová

SIDE_ENABLED = True      # boční panel s hlasitostí a jasem u pravého okraje
SIDE_TRIGGER_HEIGHT = 320  # výška citlivého pruhu u pravého okraje (je uprostřed výšky)
SIDE_TRIGGER_WIDTH = 3     # šířka citlivého pruhu
SLIDER_HEIGHT = 150      # výška posuvníků v bočním panelu
SPIN_SECONDS = 8         # za jak dlouho se obal alba (deska) otočí jednou dokola; 0 = netočí se
SPIN_FPS = 15            # kolikrát za sekundu se deska překreslí
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

# Rychlé aplikace nahoře v záložce Apps. Pravým kliknutím na aplikaci v seznamu se přidá nebo odebere,
# výběr se uloží do souboru quick-apps vedle panel.py. Tohle je jen výchozí výběr: z každé dvojice
# se vezme první nainstalovaná verze (např. Brave z RPM, jinak z Flatpaku).
QUICK_APPS = ["brave-browser|com.brave.Browser", "com.spotify.Client", "codium|com.vscodium.codium",
              "dev.vencord.Vesktop"]
# Aplikace, které se mají spouštět vlastním příkazem místo toho z jejich .desktop souboru
APP_COMMANDS = {"codium": "codium --ozone-platform=wayland"}
LOCK_COMMAND = "~/.config/hypr/lock/lock.py"   # zamykací obrazovka; když soubor chybí, zkusí se hyprlock, swaylock
# vlastní jméno a ikona v rychlých aplikacích: id aplikace -> (jméno, [ikony k vyzkoušení])
QUICK_APP_LOOK = {
    "dev.vencord.Vesktop": ("Discord", ["discord", "com.discordapp.Discord", "dev.vencord.Vesktop"]),
    "com.spotify.Client": ("Spotify", ["spotify-client", "spotify", "com.spotify.Client"]),
}
# režimy výkonu (záložka Performance): profil napájení, jas, obnovovací frekvence vestavěného displeje,
# efekty Hyprlandu (rozmazání, animace) a zákaz uspání. brightness None = jas se nemění.
POWER_MODES = [
    ("powersave",   "Powersave",   "\uf06c", dict(profile="power-saver", brightness=0.35, hz="min", effects=False, awake=False)),
    ("balanced",    "Balanced",    "\uf24e", dict(profile="balanced",    brightness=0.70, hz="max", effects=True,  awake=False)),
    ("performance", "Performance", "\uf0e4", dict(profile="performance", brightness=1.00, hz="max", effects=True,  awake=False)),
    ("turbo",       "Turbo",       "\uf135", dict(profile="performance", brightness=1.00, hz="max", effects=True,  awake=True)),
]
IND_SECONDS = 0.28
QUICK_APPS_MAX = 6         # kolik rychlých aplikací se vejde do řádku

BAR_ENABLED = True           # vlastní lišta nahoře místo Waybaru (okna z ní vyrůstají)
BAR_GAP = 6                  # mezera nad ostrůvky (jako margin u Waybaru)
BAR_BOTTOM = 2               # mezera pod ostrůvky
BAR_MARGIN = 10              # odsazení levého a pravého ostrůvku od kraje obrazovky
BAR_RADIUS = 16              # zaoblení ostrůvků
BAR_CLOCK = "%H:%M %d.%m."   # formát času uprostřed
MORPH_MS = 240               # jak dlouho ostrůvek roste a okno z něj vyjíždí
BAR_FADE_GAP = 24            # na užším monitoru: boční ostrůvek blíž než tohle k rozšířenému středu se schová

NET_ENABLED = True           # okno Wi-Fi a Bluetooth (panel.py --wifi, --bluetooth)
NET_WIDTH = 340              # šířka okna
NET_TOP_MARGIN = 6           # mezera pod lištou
NET_RIGHT_MARGIN = 8         # odsazení od pravého okraje obrazovky
BAR_ZONE = 48                # výška lišty nahoře; dokud je kurzor v ní, okno Wi-Fi zůstane otevřené
NET_LIST_HEIGHT = 420        # největší výška seznamu, pak se posouvá
BT_SCAN_SECONDS = 10         # jak dlouho se po otevření hledají nová Bluetooth zařízení

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
WALL_TAGS = False            # štítek PIC v rohu obrázků (GIF a VID se značí vždy)
WALL_CAPTION = False         # pod náhledy název a rozlišení vybrané tapety
WALL_HINT = False            # úplně dole nápověda ke klávesám
WALL_TRANSITION = True       # při změně tapety se nová rozroste v kruhu (False = vymění se hned)
WALL_TRANSITION_MS = 1100    # jak dlouho kruh roste
WALL_TRANSITION_POS = (1.0, 0.0)   # odkud kruh roste: (0, 0) levý horní roh, (1, 0) pravý horní, (0.5, 0.5) střed
WALL_FILL_MODE = "fill"      # jak se obrázek na plochu umístí: fill, fit, stretch, center, tile
WALL_VIDEO_OPTIONS = "no-audio loop"   # volby přehrávače u video tapet (ty potřebují program mpvpaper)

WEATHER_ENABLED = True   # False = počasí se nestahuje vůbec
WEATHER_CITY = ""        # např. "Praha"; prázdné = služba odhadne místo podle IP adresy
WEATHER_URL = "https://wttr.in/{city}?format=j1&lang=en"

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
    "star": "\uf005", "eye": "\uf06e", "eye_off": "\uf070", "headphones": "\uf025", "mobile": "\uf10b", "keyboard": "\uf11c",
    "mouse": "\uf245", "gamepad": "\uf11b", "laptop": "\uf109", "tv": "\uf26c",
    "gpu": "\uf26c", "updown": "\uf0ec", "bolt": "\uf0e7", "caret": "\uf0d7",
    "download": "\uf019", "upload": "\uf093", "repeat": "\uf01e", "chip": "\uf2db", "rec": "\uf111", "stop": "\uf04d", "ethernet": "\uf0e8", "bluetooth": "\uf293", "shield": "\uf132", "globe": "\uf0ac",
    "w_sun": "\ue30d", "w_moon": "\ue32b", "w_partly": "\ue302", "w_cloud": "\ue312",
    "w_fog": "\ue313", "w_rain": "\ue318", "w_snow": "\ue31a", "w_storm": "\ue31d",
}

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


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
    def cache():
        """Mezipaměť souborů, kterou jde uvolnit (bez tmpfs a sdílené paměti), v bajtech."""
        info = {}
        for line in read("/proc/meminfo").splitlines():
            key, _, rest = line.partition(":")
            if key in ("Buffers", "Cached", "SReclaimable", "Shmem"):
                info[key] = int(rest.split()[0]) * 1024
        return max(0, info.get("Buffers", 0) + info.get("Cached", 0) + info.get("SReclaimable", 0)
                   - info.get("Shmem", 0))

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


def cpu_model():
    """Název procesoru, zkrácený o zbytečné přívlastky."""
    for line in read("/proc/cpuinfo").splitlines():
        if line.startswith("model name"):
            name = line.split(":", 1)[1]
            name = re.sub(r"\((R|TM|tm|r)\)|CPU|Processor|\d+-Core|with Radeon.*|@.*", "", name)
            return " ".join(name.split()) or "Processor"
    return f"{os.cpu_count() or 1} threads"


# ----------------------------------------------------------------------------
# Data: přehrávače (MPRIS přes D-Bus, funguje se Spotify, prohlížeči, VLC, ...)
# ----------------------------------------------------------------------------
class Mpris:
    """Přehrávače přes D-Bus (MPRIS): Spotify, prohlížeče, VLC... Jeden je hlavní (ten, co hraje),
    ostatní se ukazují malé a kliknutím se na ně dá přepnout."""
    PREFIX = "org.mpris.MediaPlayer2."
    PATH = "/org/mpris/MediaPlayer2"
    PLAYER = "org.mpris.MediaPlayer2.Player"

    def __init__(self):
        try:
            self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except GLib.Error:
            self.bus = None
        self.main, self.names = None, {}

    def _call(self, dest, path, iface, method, args=None, timeout=250):
        return self.bus.call_sync(dest, path, iface, method, args, None, Gio.DBusCallFlags.NONE, timeout, None)

    def identity(self, name):
        """Hezké jméno přehrávače (Spotify, Brave...), zjišťuje se jen jednou."""
        if name not in self.names:
            try:
                value = self._call(name, self.PATH, "org.freedesktop.DBus.Properties", "Get",
                                   GLib.Variant("(ss)", ("org.mpris.MediaPlayer2", "Identity"))).unpack()[0]
            except GLib.Error:
                value = ""
            self.names[name] = str(value or name[len(self.PREFIX):].split(".")[0].capitalize())
        return self.names[name]

    def players(self):
        if not self.bus:
            return []
        try:
            names = self._call("org.freedesktop.DBus", "/org/freedesktop/DBus",
                               "org.freedesktop.DBus", "ListNames").unpack()[0]
        except GLib.Error:
            return []
        found = []
        for name in sorted(n for n in names if n.startswith(self.PREFIX)):
            try:
                props = self._call(name, self.PATH, "org.freedesktop.DBus.Properties", "GetAll",
                                   GLib.Variant("(s)", (self.PLAYER,))).unpack()[0]
            except GLib.Error:
                continue
            meta = props.get("Metadata") or {}
            artist = meta.get("xesam:artist") or ""
            if isinstance(artist, (list, tuple)):
                artist = ", ".join(str(a) for a in artist)
            info = {
                "bus": name,
                "player": self.identity(name),
                "playing": props.get("PlaybackStatus") == "Playing",
                "title": str(meta.get("xesam:title") or ""),
                "artist": str(artist),
                "album": str(meta.get("xesam:album") or ""),
                "art": str(meta.get("mpris:artUrl") or ""),
                "length": (meta.get("mpris:length") or 0) / 1e6,
                "position": (props.get("Position") or 0) / 1e6,
                "trackid": str(meta.get("mpris:trackid") or ""),
                "can_seek": bool(props.get("CanSeek")),
                "shuffle": props.get("Shuffle"),          # None = přehrávač to neumí
                "loop": props.get("LoopStatus"),
            }
            if info["title"] or info["artist"]:
                found.append(info)
        return found

    def poll(self):
        """Vrátí (hlavní přehrávač nebo None, seznam ostatních)."""
        players = self.players()
        main = next((p for p in players if p["bus"] == self.main), None)
        if main is None or not main["playing"]:
            # hlavní je vždy ten, co právě hraje; když nehraje nic, zůstává poslední
            main = next((p for p in players if p["playing"]), None) or main or (players[0] if players else None)
        self.main = main["bus"] if main else None
        return main, [p for p in players if p is not main]

    def command(self, method, bus=None):
        bus = bus or self.main
        if self.bus and bus:
            self.bus.call(bus, self.PATH, self.PLAYER, method,
                          None, None, Gio.DBusCallFlags.NONE, 500, None, None, None)

    def switch(self, bus, playing):
        """Kliknutí na malý přehrávač: hlavní se pozastaví a kliknutý začne hrát a stane se hlavním."""
        if self.main and self.main != bus and playing:
            self.command("Pause")
        self.command("Play", bus)
        self.main = bus

    def set_property(self, name, value):
        if self.bus and self.main:
            self.bus.call(self.main, self.PATH, "org.freedesktop.DBus.Properties", "Set",
                          GLib.Variant("(ssv)", (self.PLAYER, name, value)), None,
                          Gio.DBusCallFlags.NONE, 500, None, None, None)

    def seek(self, trackid, seconds):
        if self.bus and self.main and trackid:
            self.bus.call(self.main, self.PATH, self.PLAYER, "SetPosition",
                          GLib.Variant("(ox)", (trackid, int(seconds * 1e6))), None,
                          Gio.DBusCallFlags.NONE, 500, None, None, None)


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
# Obal alba jako vinylová deska, která se při přehrávání točí
# ----------------------------------------------------------------------------
class SpinArt(Art):
    """Deska s obalem alba uprostřed; když hraje, pomalu se točí, při pauze se zastaví.
    Deska se vykreslí jednou do obrázku a pak se jen otáčí, takže to procesor skoro nepozná."""

    def __init__(self, size):
        super().__init__(size)
        self.angle, self.playing, self.timer = 0.0, False, None
        self.disc, self.disc_key = None, None
        self.connect("unmap", lambda *_: self.stop_spin())
        self.connect("map", lambda *_: self.set_playing(self.playing))
        css(self, "spin-art")

    def set_playing(self, playing):
        self.playing = playing
        if playing and SPIN_SECONDS > 0 and self.get_mapped():
            if self.timer is None:
                self.last = time.monotonic()
                self.timer = GLib.timeout_add(max(15, 1000 // SPIN_FPS), self.on_timer)
        else:
            self.stop_spin()

    def stop_spin(self):
        if self.timer is not None:
            GLib.source_remove(self.timer)
            self.timer = None

    def on_timer(self):
        now = time.monotonic()
        self.angle = (self.angle + 2 * math.pi * (now - self.last) / SPIN_SECONDS) % (2 * math.pi)
        self.last = now
        self.queue_draw()
        return True

    def _load(self, url, path):
        self.disc = None                     # nový obal = desku vykreslit znovu
        return super()._load(url, path)

    def set_url(self, url):
        if url != self.url:
            self.disc = None
        super().set_url(url)

    def render_disc(self, size, scale):
        """Deska (tmavá s drážkami) a obal alba uprostřed jako kulatá nálepka."""
        ctx = self.get_style_context()
        fg = ctx.get_color(Gtk.StateFlags.NORMAL)
        found, accent = ctx.lookup_color("accent")
        accent = accent if found else fg
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(size * scale), int(size * scale))
        cr = cairo.Context(surface)
        cr.scale(scale, scale)
        c, r = size / 2, size / 2 - 1
        cr.arc(c, c, r, 0, 2 * math.pi)
        cr.set_source_rgb(0.03, 0.03, 0.03)
        cr.fill()
        cr.set_line_width(0.6)
        for i in range(9):                    # drážky
            cr.arc(c, c, r * (0.66 + i * 0.037), 0, 2 * math.pi)
            cr.set_source_rgba(1, 1, 1, 0.05 if i % 2 else 0.09)
            cr.stroke()
        cr.arc(c, c, r - 0.8, 0, 2 * math.pi)  # okraj v barvě panelu
        cr.set_line_width(1.6)
        cr.set_source_rgba(accent.red, accent.green, accent.blue, 0.55)
        cr.stroke()
        label_r = r * 0.6
        cr.save()
        cr.arc(c, c, label_r, 0, 2 * math.pi)
        cr.clip()
        if self.pixbuf:
            pw, ph = self.pixbuf.get_width(), self.pixbuf.get_height()
            k = max(2 * label_r / pw, 2 * label_r / ph)
            cr.translate(c - pw * k / 2, c - ph * k / 2)
            cr.scale(k, k)
            Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, 0, 0)
            cr.paint()
        else:
            cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.10)
            cr.paint()
            layout = self.create_pango_layout(I["music"])
            font = self.get_pango_context().get_font_description().copy()
            font.set_absolute_size(label_r * 0.7 * Pango.SCALE)
            layout.set_font_description(font)
            tw, th = layout.get_pixel_size()
            cr.move_to(c - tw / 2, c - th / 2)
            cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.5)
            PangoCairo.show_layout(cr, layout)
        cr.restore()
        cr.arc(c, c, r * 0.045, 0, 2 * math.pi)   # dírka uprostřed
        cr.set_source_rgb(0.03, 0.03, 0.03)
        cr.fill()
        return surface

    def on_draw(self, _widget, cr):
        w, h = self.get_allocated_width(), self.get_allocated_height()
        size = min(w, h)
        scale = self.get_scale_factor()
        key = (size, scale, id(self.pixbuf))
        if self.disc is None or self.disc_key != key:
            self.disc, self.disc_key = self.render_disc(size, scale), key
        cr.translate(w / 2, h / 2)
        cr.rotate(self.angle)
        cr.translate(-size / 2, -size / 2)
        cr.scale(1 / scale, 1 / scale)
        cr.set_source_surface(self.disc, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_GOOD)
        cr.paint()
        return False


# ----------------------------------------------------------------------------
# Kreslené prvky pro záložku Performance
# ----------------------------------------------------------------------------
class ScallopBadge(Gtk.DrawingArea):
    """Vlnitý kruh s velkým číslem (vytížení v %)."""

    def __init__(self, size=78):
        super().__init__()
        self.text = "—"
        self.set_size_request(size, size)
        self.set_valign(Gtk.Align.CENTER)
        css(self, "badge-wave")
        self.connect("draw", self.on_draw)

    def set(self, text):
        if text != self.text:
            self.text = text
            self.queue_draw()

    def on_draw(self, _widget, cr):
        w, h = self.get_allocated_width(), self.get_allocated_height()
        cx, cy, radius = w / 2, h / 2, min(w, h) / 2 - 2
        fg = self.get_style_context().get_color(Gtk.StateFlags.NORMAL)
        steps = 180
        for i in range(steps + 1):
            angle = 2 * math.pi * i / steps
            r = radius * (0.93 + 0.07 * math.cos(12 * angle))
            (cr.line_to if i else cr.move_to)(cx + r * math.cos(angle), cy + r * math.sin(angle))
        cr.close_path()
        cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.10)
        cr.fill()
        layout = self.create_pango_layout(self.text)
        font = self.get_pango_context().get_font_description().copy()
        font.set_absolute_size(radius * 0.52 * Pango.SCALE)
        font.set_weight(Pango.Weight.BOLD)
        layout.set_font_description(font)
        tw, th = layout.get_pixel_size()
        cr.move_to(cx - tw / 2, cy - th / 2)
        cr.set_source_rgba(fg.red, fg.green, fg.blue, 1.0)
        PangoCairo.show_layout(cr, layout)
        return False


class RingGauge(Gtk.DrawingArea):
    """Velký kruhový ukazatel s procenty a popiskem uvnitř (Storage, Memory)."""

    def __init__(self, size=96, caption="Used"):
        super().__init__()
        self.value, self.caption = 0.0, caption
        self.set_size_request(size, size)
        self.set_valign(Gtk.Align.CENTER)
        css(self, "ring-gauge")
        self.connect("draw", self.on_draw)

    def set(self, value):
        self.value = max(0.0, min(100.0, value or 0.0))
        set_class(self, "high", self.value >= 85)
        self.queue_draw()

    def on_draw(self, _widget, cr):
        w, h = self.get_allocated_width(), self.get_allocated_height()
        fg = self.get_style_context().get_color(Gtk.StateFlags.NORMAL)
        thickness = max(5.0, min(w, h) * 0.07)
        radius = min(w, h) / 2 - thickness
        start, sweep = math.radians(125), math.radians(290)
        cr.set_line_width(thickness)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.12)
        cr.arc(w / 2, h / 2, radius, start, start + sweep)
        cr.stroke()
        if self.value > 0.5:
            cr.set_source_rgba(fg.red, fg.green, fg.blue, 1.0)
            cr.arc(w / 2, h / 2, radius, start, start + sweep * self.value / 100)
            cr.stroke()
        def text(value, size, bold, dy):
            layout = self.create_pango_layout(value)
            font = self.get_pango_context().get_font_description().copy()
            font.set_absolute_size(size * Pango.SCALE)
            font.set_weight(Pango.Weight.BOLD if bold else Pango.Weight.NORMAL)
            layout.set_font_description(font)
            tw, th = layout.get_pixel_size()
            cr.move_to((w - tw) / 2, h / 2 + dy - th / 2)
            PangoCairo.show_layout(cr, layout)
        cr.set_source_rgba(fg.red, fg.green, fg.blue, 1.0)
        text(f"{self.value:.0f}%", radius * 0.42, True, -radius * 0.1)
        cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.65)
        text(self.caption, radius * 0.22, False, radius * 0.3)
        return False


class BatteryCard(Gtk.DrawingArea):
    """Vysoká dlaždice baterie: zdola se plní podle nabití, dole velké procento."""

    def __init__(self):
        super().__init__()
        self.capacity, self.status = None, ""
        self.set_size_request(104, -1)
        css(self, "battery-card")
        self.connect("draw", self.on_draw)

    def set(self, capacity, status):
        if (capacity, status) != (self.capacity, self.status):
            self.capacity, self.status = capacity, status
            self.queue_draw()

    def text(self, cr, text, size, x, y, color, alpha=1.0, bold=False, right=False, bottom=False):
        layout = self.create_pango_layout(text)
        font = self.get_pango_context().get_font_description().copy()
        font.set_absolute_size(size * Pango.SCALE)
        font.set_weight(Pango.Weight.BOLD if bold else Pango.Weight.NORMAL)
        layout.set_font_description(font)
        tw, th = layout.get_pixel_size()
        cr.move_to(x - tw if right else x, y - th if bottom else y)
        cr.set_source_rgba(color.red, color.green, color.blue, alpha)
        PangoCairo.show_layout(cr, layout)

    def on_draw(self, _widget, cr):
        w, h = self.get_allocated_width(), self.get_allocated_height()
        ctx = self.get_style_context()
        fg = ctx.get_color(Gtk.StateFlags.NORMAL)
        found, pill = ctx.lookup_color("pill")
        found2, dark = ctx.lookup_color("pill_fg")
        pill = pill if found else fg
        dark = dark if found2 else fg
        radius = 14
        rounded_polygon(cr, [(0, 0), (w, 0), (w, h), (0, h)], radius)
        cr.save()
        cr.clip()
        cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.055)
        cr.paint()
        level = (self.capacity or 0) / 100
        fill_top = h * (1 - level)
        cr.rectangle(0, fill_top, w, h - fill_top)
        cr.set_source_rgba(pill.red, pill.green, pill.blue, 0.92)
        cr.fill()
        cr.restore()
        if self.capacity is None:
            self.text(cr, I["plug"], 18, 14, 14, fg, 0.7)
            self.text(cr, "Battery", 13, 14, 42, fg)
            self.text(cr, "no battery", 11, 14, h - 14, fg, 0.6, bottom=True)
            return False
        icon = I["bat"][min(4, self.capacity // 20)]
        status = {"Not charging": "Plugged in"}.get(self.status, self.status or "")
        charging = self.status in ("Charging", "Full", "Not charging")
        # text se kreslí dvakrát: nad výplní světle, na výplni tmavě (i když hrana výplně jde přes písmeno)
        for top, bottom, color in ((0, fill_top, fg), (fill_top, h, dark)):
            if bottom <= top:
                continue
            cr.save()
            cr.rectangle(0, top, w, bottom - top)
            cr.clip()
            self.text(cr, icon, 18, 14, 14, color, 0.85)
            self.text(cr, "Battery", 13, 14, 42, color)
            self.text(cr, status, 11, w - 12, h - 46, color, 0.75, right=True, bottom=True)
            self.text(cr, (I["bolt"] + " " if charging else "") + f"{self.capacity}%", 24, w - 12, h - 12,
                      color, 1.0, bold=True, right=True, bottom=True)
            cr.restore()
        return False


class NetGraph(Gtk.DrawingArea):
    """Graf rychlosti stahování (vyplněný) a odesílání (čára) za poslední dvě minuty."""

    def __init__(self, height=58):
        super().__init__()
        self.down, self.up = [], []
        self.set_size_request(-1, height)
        self.set_hexpand(True)
        css(self, "net-graph")
        self.connect("draw", self.on_draw)

    def set(self, down, up):
        self.down, self.up = list(down), list(up)
        self.queue_draw()

    def on_draw(self, _widget, cr):
        w, h = self.get_allocated_width(), self.get_allocated_height()
        fg = self.get_style_context().get_color(Gtk.StateFlags.NORMAL)
        if len(self.down) < 2:
            return False
        top = max(max(self.down), max(self.up or [0]), 1024)
        step = w / (len(self.down) - 1)

        def points(values):
            return [(i * step, h - 1 - (h - 4) * v / top) for i, v in enumerate(values)]
        down = points(self.down)
        cr.move_to(0, h)
        for x, y in down:
            cr.line_to(x, y)
        cr.line_to(w, h)
        cr.close_path()
        cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.28)
        cr.fill_preserve()
        cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.9)
        cr.set_line_width(1.2)
        cr.new_path()
        for i, (x, y) in enumerate(down):
            (cr.line_to if i else cr.move_to)(x, y)
        cr.stroke()
        if len(self.up) == len(self.down):
            cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.45)
            cr.set_dash([3, 3])
            for i, (x, y) in enumerate(points(self.up)):
                (cr.line_to if i else cr.move_to)(x, y)
            cr.stroke()
        return False


# ----------------------------------------------------------------------------
# Data pro záložku Performance: grafická karta, síť, disky
# ----------------------------------------------------------------------------
def human_bytes(value, per_second=False):
    for unit in ("B", "kB", "MB", "GB", "TB"):
        if value < 999.5 or unit == "TB":
            number = f"{value:.1f}" if value < 10 and unit != "B" else f"{value:.0f}"
            return f"{number} {unit}" + ("/s" if per_second else "")
        value /= 1000


class PowerModes:
    """Přepínání režimů výkonu. Nic z toho nepotřebuje heslo: profil přes power-profiles-daemon / tuned,
    jas přes logind, displej a efekty přes hyprctl."""
    FILE = os.path.join(STATE_DIR, "power-mode")

    def __init__(self):
        self.current = read(self.FILE).strip() or None
        self.busy, self.awake_proc = False, None
        self.ppd = shutil.which("powerprofilesctl")
        self.tuned = shutil.which("tuned-adm")
        self.hyprctl = shutil.which("hyprctl")
        if self.current is None:               # ještě nevybráno: odhadnout podle profilu napájení
            self.current = {"power-saver": "powersave", "balanced": "balanced",
                            "performance": "performance"}.get(self.active_profile() or "")

    @staticmethod
    def config(key):
        return next((m[3] for m in POWER_MODES if m[0] == key), None)

    def profile(self, name):
        if self.ppd:
            tool(self.ppd, "set", name)
        elif self.tuned:
            tool(self.tuned, "profile", {"power-saver": "powersave", "balanced": "balanced",
                                         "performance": "throughput-performance"}[name])

    def refresh_rate(self, which):
        """Vestavěný displej (eDP) na nejnižší nebo nejvyšší frekvenci při stejném rozlišení."""
        if not self.hyprctl:
            return
        _ok, out, _err = tool(self.hyprctl, "-j", "monitors")
        try:
            monitors = json.loads(out)
        except ValueError:
            return
        for m in monitors:
            if not m["name"].startswith(("eDP", "LVDS", "DSI")):
                continue
            size = f"{m['width']}x{m['height']}@"
            rates = sorted({float(x.split("@")[1].rstrip("Hz")) for x in m.get("availableModes", [])
                            if x.startswith(size)})
            if not rates:
                continue
            rate = rates[0] if which == "min" else rates[-1]
            if abs(rate - m["refreshRate"]) < 0.5:
                continue
            tool(self.hyprctl, "keyword", "monitor",
                 f"{m['name']},{m['width']}x{m['height']}@{rate:.2f},{m['x']}x{m['y']},{m['scale']:g}")

    def effects(self, on):
        if self.hyprctl:
            value = "true" if on else "false"
            tool(self.hyprctl, "--batch", f"keyword decoration:blur:enabled {value} ; "
                                          f"keyword animations:enabled {value} ; "
                                          f"keyword decoration:shadow:enabled {value}")

    def awake(self, on):
        if on and self.awake_proc is None and shutil.which("systemd-inhibit"):
            self.awake_proc = subprocess.Popen(
                ["systemd-inhibit", "--what=idle:sleep", "--who=Island panel", "--why=Turbo mode",
                 "sleep", "infinity"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif not on and self.awake_proc is not None:
            self.awake_proc.terminate()
            self.awake_proc = None

    def apply(self, key, backlight=None, brightness=True):
        """(běží na pozadí) Nastaví režim; brightness=False = jas nechat (obnova po přihlášení)."""
        conf = self.config(key)
        if conf is None:
            return
        self.profile(conf["profile"])
        if brightness and backlight is not None and conf["brightness"] is not None:
            backlight.set(conf["brightness"])
        self.refresh_rate(conf["hz"])
        self.effects(conf["effects"])
        self.current = key
        try:
            os.makedirs(STATE_DIR, exist_ok=True)
            with open(self.FILE, "w") as f:
                f.write(key)
        except OSError:
            pass

    def active_profile(self):
        if self.ppd:
            _ok, out, _err = tool(self.ppd, "get")
            return out.strip()
        return None


class Gpu:
    """Grafická karta: vytížení (AMD, NVIDIA), u Intelu aktuální takt vůči maximu; teplota, je-li čidlo."""

    def __init__(self):
        self.name, self.kind, self.paths, self.temp_path = "GPU", None, {}, None
        self.usage, self.temp, self.metric = None, None, "Usage"
        try:
            cards = sorted(c for c in os.listdir("/sys/class/drm") if re.fullmatch(r"card\d+", c))
        except OSError:
            cards = []
        found = []
        for card in cards:
            base = f"/sys/class/drm/{card}"
            device = os.path.join(base, "device")
            driver = os.path.basename(os.path.realpath(os.path.join(device, "driver")))
            info = {"base": base, "device": device, "driver": driver, "slot": os.path.basename(os.path.realpath(device))}
            idle = [p for p in (f"{base}/gt/gt0/rc6_residency_ms", f"{base}/power/rc6_residency_ms",
                                f"{device}/tile0/gt0/gtidle/idle_residency_ms") if os.path.exists(p)]
            if os.path.exists(os.path.join(device, "gpu_busy_percent")):
                info["kind"] = "busy"
            elif idle:                                   # Intel: podíl času, kdy grafika nespí
                info["kind"], info["idle"] = "idle", idle[0]
            elif os.path.exists(os.path.join(base, "gt_act_freq_mhz")):
                info["kind"] = "freq"
            elif driver == "nvidia" and shutil.which("nvidia-smi"):
                info["kind"] = "nvidia"
            else:
                continue
            found.append(info)
        found.sort(key=lambda i: {"busy": 0, "nvidia": 1, "idle": 2, "freq": 3}[i["kind"]])
        if not found:
            return
        gpu = found[0]
        self.kind, self.paths = gpu["kind"], gpu
        self.metric = "Clock" if self.kind == "freq" else "Usage"
        try:
            for hw in os.listdir(os.path.join(gpu["device"], "hwmon")):
                path = os.path.join(gpu["device"], "hwmon", hw, "temp1_input")
                if os.path.exists(path):
                    self.temp_path = path
        except OSError:
            pass
        self.name = self.lookup_name(gpu)

    @staticmethod
    def lookup_name(gpu):
        vendor = {"amdgpu": "AMD", "radeon": "AMD", "i915": "Intel", "xe": "Intel", "nvidia": "NVIDIA",
                  "nouveau": "NVIDIA"}.get(gpu["driver"], "GPU")
        text = run("lspci", "-mm", "-s", gpu["slot"]) if shutil.which("lspci") else ""
        fields = re.findall(r'"([^"]*)"', text)
        if len(fields) >= 3:
            model = fields[2]
            inner = re.search(r"\[([^\]]+)\]", model)
            return f"{vendor} {inner.group(1) if inner else model}"
        return f"{vendor} graphics"

    def sample(self):
        try:
            if self.kind == "busy":
                self.usage = float(read(os.path.join(self.paths["device"], "gpu_busy_percent")))
            elif self.kind == "idle":
                now, idle = time.monotonic() * 1000, float(read(self.paths["idle"]))
                last, self.idle_last = getattr(self, "idle_last", None), (now, idle)
                if last and now - last[0] > 200:
                    self.usage = max(0.0, min(100.0, 100 * (1 - (idle - last[1]) / (now - last[0]))))
            elif self.kind == "freq":
                now = float(read(os.path.join(self.paths["base"], "gt_act_freq_mhz")))
                top = float(read(os.path.join(self.paths["base"], "gt_RP0_freq_mhz"), "0") or
                            read(os.path.join(self.paths["base"], "gt_max_freq_mhz")))
                self.usage = 100 * now / top if top else None
            elif self.kind == "nvidia":
                out = run("nvidia-smi", "--query-gpu=utilization.gpu,temperature.gpu",
                          "--format=csv,noheader,nounits", timeout=3).split(",")
                self.usage, self.temp = float(out[0]), float(out[1])
                return
        except (ValueError, IndexError, OSError):
            self.usage = None
        if self.temp_path:
            try:
                self.temp = int(read(self.temp_path)) / 1000
            except ValueError:
                self.temp = None


class NetStats:
    """Rychlost a celkový přenos přes skutečná síťová rozhraní (virtuální se nepočítají)."""
    SKIP = ("lo", "docker", "veth", "virbr", "br-", "tun", "wg")

    def __init__(self):
        self.down = self.up = 0.0
        self.history_down, self.history_up = [0.0] * 60, [0.0] * 60
        self.total = (0, 0)
        self.last, self.stamp = None, None

    def counters(self):
        down = up = 0
        for line in read("/proc/net/dev").splitlines()[2:]:
            name, _, data = line.partition(":")
            if name.strip().startswith(self.SKIP):
                continue
            fields = data.split()
            if len(fields) >= 9:
                down += int(fields[0])
                up += int(fields[8])
        return down, up

    def sample(self):
        now, moment = self.counters(), time.monotonic()
        if self.last is not None and moment > self.stamp:
            span = moment - self.stamp
            self.down, self.up = (now[0] - self.last[0]) / span, (now[1] - self.last[1]) / span
            self.history_down = self.history_down[1:] + [self.down]
            self.history_up = self.history_up[1:] + [self.up]
        self.last, self.stamp, self.total = now, moment, now


def list_mounts():
    """Připojené disky: (zařízení, kam je připojené), bez dočasných a virtuálních."""
    found, seen = [], set()
    for line in read("/proc/mounts").splitlines():
        parts = line.split()
        if len(parts) < 3 or not parts[0].startswith("/dev/") or parts[0].startswith("/dev/loop") \
                or parts[2] in ("squashfs", "iso9660"):
            continue
        device, point = parts[0], parts[1].replace("\\040", " ")
        if device in seen or point.startswith(("/boot", "/snap", "/var/lib/snapd")):
            continue
        seen.add(device)
        found.append((device, point))
    found.sort(key=lambda m: (m[1] != "/", m[1]))
    return found or [("/", "/")]


def disk_usage(point):
    try:
        st = os.statvfs(point)
    except OSError:
        return 0.0, 0.0, 0.0
    total, free = st.f_blocks * st.f_frsize, st.f_bavail * st.f_frsize
    return (total - free), total, (100.0 * (total - free) / total if total else 0.0)


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
def app_key(app):
    """Jméno .desktop souboru aplikace bez přípony (např. 'codium')."""
    key = app.get_id() or ""
    return key[:-8] if key.endswith(".desktop") else key


def app_by_key(key):
    try:
        return Gio.DesktopAppInfo.new(key + ".desktop")
    except TypeError:          # neexistuje
        return None


ICON_DIRS = ["/usr/share/icons/Papirus/64x64/apps", "/usr/share/icons/Papirus-Dark/64x64/apps",
             "/var/lib/flatpak/exports/share/icons/hicolor/scalable/apps",
             "/var/lib/flatpak/exports/share/icons/hicolor/256x256/apps",
             "/var/lib/flatpak/exports/share/icons/hicolor/128x128/apps",
             os.path.expanduser("~/.local/share/flatpak/exports/share/icons/hicolor/scalable/apps"),
             os.path.expanduser("~/.local/share/icons")]


def app_icon(app, names=(), size=36):
    """Ikona aplikace: nejdřív zadaná jména (téma ikon, pak i Papirus a Flatpak složky napřímo),
    potom ikona z .desktop souboru; když nic nejde načíst, obecná ikona programu."""
    theme = Gtk.IconTheme.get_default()
    candidates = list(names)
    icon = app.get_icon() if app else None
    if isinstance(icon, Gio.ThemedIcon):
        candidates += icon.get_names()
    elif isinstance(icon, Gio.FileIcon) and icon.get_file().get_path():
        candidates.append(icon.get_file().get_path())
    for name in candidates:
        paths = [name] if name.startswith("/") else []
        if not paths and theme.has_icon(name):
            info = theme.lookup_icon(name, size, Gtk.IconLookupFlags.FORCE_SIZE)
            if info and info.get_filename():
                paths.append(info.get_filename())
        if not name.startswith("/"):
            paths += [os.path.join(d, name + ext) for d in ICON_DIRS for ext in (".svg", ".png")]
        for path in paths:
            if os.path.exists(path):
                try:
                    display = Gdk.Display.get_default()
                    scale = max([display.get_monitor(i).get_scale_factor()
                                 for i in range(display.get_n_monitors())] or [1])   # ostrá i na HiDPI
                    pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, size * scale, size * scale, True)
                    return Gtk.Image.new_from_surface(Gdk.cairo_surface_create_from_pixbuf(pix, scale, None))
                except GLib.Error:
                    continue
    image = Gtk.Image.new_from_icon_name("application-x-executable", Gtk.IconSize.DND)
    image.set_pixel_size(size)
    return image


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


_locked_cache = [0.0, False]


def screen_locked():
    """Běží zamykací obrazovka? Pak se žádný panel nesmí vysunout (výsledek platí půl sekundy)."""
    now = time.monotonic()
    if now - _locked_cache[0] > 0.5:
        found = False
        for pid in os.listdir("/proc"):
            if pid.isdigit() and read(f"/proc/{pid}/comm") in ("hyprlock", "swaylock"):
                found = True
                break
        _locked_cache[:] = [now, found]
    return _locked_cache[1]


EDGE_RADIUS = 16      # zaoblení panelů u pravého okraje (vnější rohy i přechod do okraje obrazovky)


def css_box(widget):
    """Obdélník widgetu bez okrajů (margin) z CSS: x, y, šířka, výška."""
    m = widget.get_style_context().get_margin(Gtk.StateFlags.NORMAL)
    a = widget.get_allocation()
    return a.x + m.left, a.y + m.top, a.width - m.left - m.right, a.height - m.top - m.bottom


def draw_edge_panel(win, box, cr, bump=None):
    """Pozadí panelu přilepeného k pravému okraji obrazovky: vlevo zaoblené rohy, vpravo navazuje
    na okraj obrazovky vydutým zaoblením nahoře i dole (jako by z okraje vyrůstal).
    bump = menší část přilepená zleva (sloupec tlačítek), napojená stejným vydutým zaoblením."""
    if not box.get_visible():
        return False
    ctx = box.get_style_context()
    x, y, _w, h = css_box(box)
    right = win.get_allocated_width()
    r, f = min(EDGE_RADIUS, h / 2), EDGE_RADIUS
    if h <= 0 or right - x <= r:
        return False
    side = None
    if bump is not None and bump.get_visible():
        bx, by, _bw, bh = css_box(bump)
        if bx < x and by - f >= y + r and by + bh + f <= y + h - r:
            side = (bx, by, bh, min(EDGE_RADIUS, bh / 2))

    def outline(close):
        cr.new_path()
        cr.move_to(right, y - f)
        cr.arc(right - f, y - f, f, 0, math.pi / 2)                     # vydutí nahoře
        cr.line_to(x + r, y)
        cr.arc_negative(x + r, y + r, r, 3 * math.pi / 2, math.pi)     # levý horní roh
        if side:                                                       # sloupec tlačítek vlevo
            bx, by, bh, br = side
            cr.line_to(x, by - f)
            cr.arc(x - f, by - f, f, 0, math.pi / 2)
            cr.line_to(bx + br, by)
            cr.arc_negative(bx + br, by + br, br, 3 * math.pi / 2, math.pi)
            cr.line_to(bx, by + bh - br)
            cr.arc_negative(bx + br, by + bh - br, br, math.pi, math.pi / 2)
            cr.line_to(x - f, by + bh)
            cr.arc(x - f, by + bh + f, f, -math.pi / 2, 0)
        cr.line_to(x, y + h - r)
        cr.arc_negative(x + r, y + h - r, r, math.pi, math.pi / 2)     # levý dolní roh
        cr.line_to(right - f, y + h)
        cr.arc(right - f, y + h + f, f, -math.pi / 2, 0)               # vydutí dole
        if close:
            cr.close_path()

    outline(True)
    cr.set_source_rgba(*rgba_tuple(ctx, "island", (0.04, 0.12, 0.17, 0.93)))
    cr.fill()
    cr.save()
    cr.translate(0.5, 0)
    outline(False)
    cr.restore()
    cr.set_source_rgba(*rgba_tuple(ctx, "island_border", (0.49, 0.75, 0.86, 0.25)))
    cr.set_line_width(1)
    cr.stroke()
    return False


def hypr_socket(name):
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    run_dir = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    return os.path.join(run_dir, "hypr", sig, name) if sig else None


def hypr_json(what):
    """Rychlý dotaz na Hyprland přímo přes jeho socket (bez spouštění hyprctl)."""
    path = hypr_socket(".socket.sock")
    if not path:
        return None
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.3)
            sock.connect(path)
            sock.sendall(f"j/{what}".encode())
            data = b""
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                data += chunk
        return json.loads(data)
    except (OSError, ValueError):
        return None


class HyprEvents:
    """Poslouchá události Hyprlandu (změna aktivního okna, plochy…) a předává je posluchačům."""

    def __init__(self):
        self.listeners = []
        if hypr_socket(".socket2.sock"):
            threading.Thread(target=self.run, daemon=True).start()

    def connect(self, callback):
        self.listeners.append(callback)

    def emit(self, name, data):
        for callback in self.listeners:
            callback(name, data)
        return False

    def run(self):
        while True:
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                    sock.connect(hypr_socket(".socket2.sock"))
                    buf = b""
                    while True:
                        chunk = sock.recv(4096)
                        if not chunk:
                            break
                        buf += chunk
                        *lines, buf = buf.split(b"\n")
                        for line in lines:
                            name, _, data = line.decode(errors="ignore").partition(">>")
                            GLib.idle_add(self.emit, name, data)
            except OSError:
                pass
            time.sleep(2)


class AutoHide:
    """Společné chování vysouvacích panelů: po odjetí kurzoru se panel schová.

    Třída, která ho používá, musí mít self.win, self.close_timer a metodu hide().
    """

    def watch_pointer(self):
        self.hovering = False
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

    attach = None          # (okno lišty, ostrůvek), když okno vyrůstá z lišty

    def pointer_inside(self):
        """Je kurzor právě nad panelem? Ptáme se přímo, události enter/leave chodí i při klikání."""
        if self.attach and self.attach[0].pointer_in(self.attach[1]):
            return True            # kurzor je na ostrůvku, ze kterého okno vyrostlo
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

    def schedule_close(self):
        """Kurzor odjel z ostrůvku: za chvíli zavřít, pokud není nad oknem."""
        if self.close_timer is None:
            self.close_timer = GLib.timeout_add(CLOSE_DELAY_MS, self.close_if_outside)

    def attach_to_bar(self, key, width, origin=None):
        """Napojí okno na ostrůvek lišty (když lišta běží). Vrací šířku, kterou má okno mít."""
        bar = getattr(self.app, "bar", None)
        if bar is None:
            self.attach = None
            return width
        result = bar.attach(self, key, width, origin)
        if result is None:
            self.attach = None
            return width
        bw, key, width = result
        self.attach = (bw, key)
        return width

    def detach_from_bar(self):
        if self.attach:
            self.attach[0].close(self.attach[1])

    def morph_tick(self):
        """Ostrůvek, ze kterého okno vyrůstá, změnil šířku."""

    def close_if_outside(self):
        self.close_timer = None
        if not getattr(self, "hovering", False) and not self.pointer_inside():
            self.hide()
        return False

    def on_enter(self, _win, _event):
        self.hovering = True
        self.cancel_close()
        return False

    def on_leave(self, _win, event):
        if event.detail == Gdk.NotifyType.INFERIOR:
            return False          # kurzor jen přejel na prvek uvnitř okna
        self.hovering = False
        self.cancel_close()
        self.close_timer = GLib.timeout_add(CLOSE_DELAY_MS, self.close_if_outside)
        return False


class Panel(AutoHide):
    TABS = [("dashboard", "Dashboard"), ("media", "Media"), ("performance", "Performance"), ("apps", "Apps")]

    def __init__(self, app):
        self.app = app
        self.stats, self.mpris = Stats(), Mpris()
        self.gpu, self.net = Gpu(), NetStats()
        self.power = PowerModes()
        self.backlight = Backlight()
        if self.power.current:                  # po přihlášení obnovit režim (jas se nemění)
            mode = self.power.current
            threading.Thread(target=lambda: self.power.apply(mode, brightness=False), daemon=True).start()
            self.power.awake(bool((self.power.config(mode) or {}).get("awake")))
        self.mount_index = 0
        self.visible = False
        self.close_timer = self.tick_timer = None
        self.weather_at, self.weather_busy = 0.0, False
        self.apps_built = False
        self.media = None

        self.win = layer_window(app, "island-panel")
        self.watch_pointer()
        self.win.connect("key-press-event", self.on_key)
        self.win.connect("delete-event", lambda *_: self.hide() or True)

        root = self.root = vbox(0)
        root.set_name("panel")
        root.set_size_request(PANEL_WIDTH, -1)
        root.set_valign(Gtk.Align.START)
        # okno má stálou výšku (nejvyšší záložka) a nikdy se nezvětšuje ani nezmenšuje;
        # panel uvnitř je jen tak vysoký, jak je potřeba, zbytek okna je průhledný a propouští klikání
        outer = Gtk.Fixed()                     # panel vždy přilepený k hornímu okraji okna
        # panel vyjíždí shora (z ostrůvku s časem); hide_timer = schovat okno až po dojetí animace
        self.reveal = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN,
                                   transition_duration=MORPH_MS)
        self.reveal.add(root)
        self.reveal.connect("size-allocate", lambda *_: self.update_input())
        self.hide_timer = None
        outer.put(self.reveal, 0, 0)
        # dokud ostrůvek s časem roste, je panel ořízlý na jeho šířku (žádné schody mezi nimi)
        self.outer = outer
        outer.connect("draw", self.clip_to_island)
        outer.connect_after("draw", self.draw_morph_edge)
        outer.show()
        self.reveal.show()
        self.win.add(outer)
        self.win.connect("size-allocate", lambda *_: self.update_input())

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
        # čára pod aktivní záložkou: kreslí se zvlášť a k nové záložce přejede
        self.tabs_box = tabs
        self.ind = Gtk.DrawingArea()
        self.ind.set_size_request(-1, 2)
        self.ind.set_valign(Gtk.Align.END)
        self.ind.set_halign(Gtk.Align.FILL)
        css(self.ind, "tab-indicator")
        self.ind_pos, self.ind_tab, self.ind_tick = None, None, None
        self.ind.connect("draw", self.draw_indicator)
        tabs.connect("size-allocate", lambda *_: self.move_indicator(animate=False, layout=True))
        overlay = Gtk.Overlay()
        overlay.add(tabs)
        overlay.add_overlay(self.ind)
        overlay.set_overlay_pass_through(self.ind, True)
        overlay.set_margin_bottom(10)
        root.pack_start(overlay, False, False, 0)

        # přepnutí záložky obsah odsune do strany (směr podle pořadí záložek), nepřekreslí ho najednou
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT, transition_duration=260)
        self.stack.set_hhomogeneous(True)
        self.stack.set_vhomogeneous(False)      # každá záložka jen tak vysoká, jak potřebuje
        self.height_tick, self.body_h = None, None
        # obsah záložek je v "okénku" s výškou, kterou plynule měníme sami; lišta záložek nahoře se nehne
        self.body = Gtk.ScrolledWindow()
        self.body.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.EXTERNAL)
        self.body.set_propagate_natural_width(True)
        self.body.add(self.stack)
        root.pack_start(self.body, False, False, 0)
        self.stack.add_named(self.build_dashboard(), "dashboard")
        self.stack.add_named(self.build_media(), "media")
        self.stack.add_named(self.build_performance(), "performance")
        self.stack.add_named(self.build_apps(), "apps")
        root.show_all()
        self.select("dashboard")

        GLib.timeout_add_seconds(2, self.background_sample)
        # seznam aplikací připravit hned, ať se výška okna (podle nejvyšší záložky) nemusí měnit později
        GLib.idle_add(lambda: (self.ensure_apps(), self.fix_window_height()) and False)

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
        self.w_desc = label("loading", "dim", xalign=0, ellipsize=True)
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
        self.g_values = {}
        for key, caption in (("cpu", "CPU"), ("ram", "RAM"), ("disk", "Disk")):
            row = hbox(10)
            gauge = Gauge(44, I[key], 4)
            text = vbox(0)
            text.set_valign(Gtk.Align.CENTER)
            value = label("0%", "gauge-value", xalign=0)
            text.pack_start(value, False, False, 0)
            text.pack_start(label(caption, "dim", "small", xalign=0), False, False, 0)
            row.pack_start(gauge, False, False, 0)
            row.pack_start(text, True, True, 0)
            gauges.pack_start(row, True, False, 0)
            self.g_values[key] = (gauge, value)
        bottom.pack_start(gauges, False, False, 0)
        left.pack_start(bottom, True, True, 0)
        page.pack_start(left, True, True, 0)

        mini = vbox(6, "tile", "mini-media")
        mini.set_size_request(180, -1)
        self.m_art = SpinArt(150)
        self.m_title = label("Nothing playing", "media-title", ellipsize=True)
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
        page = hbox(22, "page", "tile", "media-page")
        self.b_art = SpinArt(176)
        self.b_art.set_valign(Gtk.Align.CENTER)
        page.pack_start(self.b_art, False, False, 0)

        info = vbox(4)
        info.set_valign(Gtk.Align.CENTER)
        self.b_player = label("", "chip", xalign=0)
        self.b_player.set_halign(Gtk.Align.START)
        self.b_title = label("Nothing playing", "media-big-title", xalign=0, ellipsize=True)
        self.b_artist = label("Play some music or a video and it shows up here.", xalign=0, ellipsize=True)
        self.b_album = label("", "dim", xalign=0, ellipsize=True)
        seek = Gtk.EventBox()                       # klik do lišty = skok na to místo
        seek.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        seek.connect("button-press-event", self.on_seek)
        self.b_progress = css(Gtk.ProgressBar(), "progress")
        self.b_progress.set_margin_top(7)          # větší plocha pro kliknutí
        self.b_progress.set_margin_bottom(5)
        seek.add(self.b_progress)
        seek.set_margin_top(5)
        times = hbox(0)
        self.b_pos = label("", "dim", "small", xalign=0)
        self.b_len = label("", "dim", "small", xalign=1)
        times.pack_start(self.b_pos, True, True, 0)
        times.pack_start(self.b_len, True, True, 0)

        row = hbox(8, "media-controls")
        row.set_halign(Gtk.Align.START)
        row.set_margin_top(8)
        self.b_shuffle = css(Gtk.Button(label=I["shuffle"]), "flat", "media-btn", "toggle-btn")
        prev_btn = css(Gtk.Button(label=I["prev"]), "flat", "media-btn", "large")
        self.b_play = css(Gtk.Button(label=I["play"]), "flat", "media-btn", "primary", "large", "wide")
        next_btn = css(Gtk.Button(label=I["next"]), "flat", "media-btn", "large")
        self.b_repeat = css(Gtk.Button(label=I["repeat"]), "flat", "media-btn", "toggle-btn")
        self.b_shuffle.connect("clicked", lambda *_: self.toggle_shuffle())
        prev_btn.connect("clicked", lambda *_: self.media_command("Previous"))
        self.b_play.connect("clicked", lambda *_: self.media_command("PlayPause"))
        next_btn.connect("clicked", lambda *_: self.media_command("Next"))
        self.b_repeat.connect("clicked", lambda *_: self.cycle_repeat())
        for button in (self.b_shuffle, prev_btn, self.b_play, next_btn, self.b_repeat):
            row.pack_start(button, False, False, 0)
        for widget in (self.b_player, self.b_title, self.b_artist, self.b_album, seek, times, row):
            info.pack_start(widget, False, False, 0)
        right = vbox(0)
        right.pack_start(info, True, True, 0)

        # ostatní přehrávače (třeba video v prohlížeči) malé dole; klik je prohodí s hlavním
        self.others = vbox(5, "others")
        self.others.pack_start(label("Also open", "dim", "small", xalign=0), False, False, 0)
        self.others_list = hbox(6)
        self.others.pack_start(self.others_list, False, False, 0)
        self.others.set_no_show_all(True)
        self.others_shown = None
        right.pack_start(self.others, False, False, 0)
        page.pack_start(right, True, True, 0)
        return page

    def other_card(self, info):
        button = css(Gtk.Button(), "flat", "other-player")
        button.set_size_request(214, -1)
        row = hbox(8)
        art = Art(38, 8)
        art.set_url(info["art"])
        row.pack_start(art, False, False, 0)
        text = vbox(0)
        text.set_valign(Gtk.Align.CENTER)
        text.pack_start(label(info["title"] or "Untitled", xalign=0, ellipsize=True), False, False, 0)
        text.pack_start(label(info["player"], "dim", "small", xalign=0, ellipsize=True), False, False, 0)
        row.pack_start(text, True, True, 0)
        row.pack_start(label(I["pause"] if info["playing"] else I["play"], "dim"), False, False, 2)
        button.add(row)
        button.connect("clicked", lambda _b, bus=info["bus"]: self.switch_player(bus))
        return button

    def switch_player(self, bus):
        self.mpris.switch(bus, bool(self.media and self.media["playing"]))
        GLib.timeout_add(300, lambda: self.refresh_media() and False)

    def toggle_shuffle(self):
        if self.media and self.media["shuffle"] is not None:
            self.mpris.set_property("Shuffle", GLib.Variant("b", not self.media["shuffle"]))
            GLib.timeout_add(250, lambda: self.refresh_media() and False)

    def cycle_repeat(self):
        if self.media and self.media["loop"] is not None:
            following = {"None": "Playlist", "Playlist": "Track", "Track": "None"}.get(self.media["loop"], "None")
            self.mpris.set_property("LoopStatus", GLib.Variant("s", following))
            GLib.timeout_add(250, lambda: self.refresh_media() and False)

    def on_seek(self, box, event):
        info = self.media
        if not info or info["length"] <= 0 or not info["can_seek"]:
            return False
        fraction = max(0.0, min(1.0, event.x / max(1, box.get_allocated_width())))
        try:
            self.mpris.seek(info["trackid"], fraction * info["length"])
        except (TypeError, GLib.Error):
            pass
        GLib.timeout_add(250, lambda: self.refresh_media() and False)
        return True

    def build_performance(self):
        page = hbox(8, "page")
        grid = vbox(8)
        top = hbox(8)
        top.set_homogeneous(True)
        self.p_cpu = self.perf_card(top, "cpu", "CPU", cpu_model())
        self.p_gpu = self.perf_card(top, "gpu", "GPU", self.gpu.name)
        grid.pack_start(top, False, False, 0)

        bottom = hbox(8)
        storage = hbox(12, "tile", "perf-card")
        self.p_disk = RingGauge(84)
        storage.pack_start(self.p_disk, False, False, 0)
        sinfo = vbox(6)
        sinfo.set_valign(Gtk.Align.CENTER)
        sinfo.pack_start(label("Storage", "perf-title", xalign=0), False, False, 0)
        self.p_mount_label = label("", "small")
        self.p_mount = css(Gtk.Button(), "flat", "chip-btn", "mount-btn")
        self.p_mount.add(self.p_mount_label)
        self.p_mount.connect("clicked", lambda *_: self.next_mount())
        sinfo.pack_start(self.p_mount, False, False, 0)
        self.p_disk_detail = label("", "dim", "small", xalign=0, ellipsize=True)
        self.p_disk_detail.set_max_width_chars(16)        # dlouhá cesta nesmí kartu roztáhnout
        self.p_disk_detail.set_width_chars(16)
        sinfo.pack_start(self.p_disk_detail, False, False, 0)
        storage.pack_start(sinfo, False, False, 0)
        column = vbox(8)
        column.pack_start(storage, True, True, 0)
        modes = vbox(6, "tile", "perf-card", "power-card")
        mode_grid = Gtk.Grid(column_spacing=6, row_spacing=6, column_homogeneous=True)
        self.p_modes = {}
        for index, (key, title, icon, _conf) in enumerate(POWER_MODES):
            button = css(Gtk.Button(), "flat", "power-mode")
            inner = hbox(8)
            inner.pack_start(label(icon, "power-icon"), False, False, 0)
            inner.pack_start(label(title, "power-name", xalign=0), True, True, 0)
            button.add(inner)
            button.set_can_focus(False)
            button.connect("clicked", lambda _b, k=key: self.set_power_mode(k))
            mode_grid.attach(button, index % 2, index // 2, 1, 1)
            self.p_modes[key] = button
        modes.pack_start(mode_grid, False, False, 0)
        column.pack_start(modes, False, False, 0)
        bottom.pack_start(column, False, False, 0)

        net = vbox(4, "tile", "perf-card")
        net.pack_start(label(f"{I['updown']}  Network", "perf-title", xalign=0), False, False, 0)
        self.p_net_graph = NetGraph(54)
        net.pack_start(self.p_net_graph, True, True, 2)
        self.p_net = {}
        for key, icon, title in (("down", "download", "Download"), ("up", "upload", "Upload"), ("total", "updown", "Total")):
            line = hbox(6)
            line.pack_start(label(f"{I[icon]}  {title}", "dim", "small", xalign=0), True, True, 0)
            value = label("", "small", xalign=1)
            line.pack_start(value, False, False, 0)
            net.pack_start(line, False, False, 0)
            self.p_net[key] = value
        bottom.pack_start(net, True, True, 0)

        memory = vbox(4, "tile", "perf-card")
        memory.pack_start(label(f"{I['ram']}  Memory", "perf-title", xalign=0), False, False, 0)
        self.p_ram = RingGauge(100)
        memory.pack_start(self.p_ram, True, True, 0)
        self.p_ram_detail = label("", "dim", "small")
        memory.pack_start(self.p_ram_detail, False, False, 0)
        bottom.pack_start(memory, False, False, 0)
        grid.pack_start(bottom, True, True, 0)
        page.pack_start(grid, True, True, 0)

        side = vbox(8)
        self.p_battery = BatteryCard()
        side.pack_start(self.p_battery, True, True, 0)
        cache = vbox(4, "tile", "perf-card", "cache-card")
        cache.pack_start(label("Cache", "dim", "small"), False, False, 0)
        self.p_cache = label("", "cache-value")
        cache.pack_start(self.p_cache, False, False, 0)
        self.p_cache_btn = css(Gtk.Button(label="Clear"), "flat", "cache-btn")
        self.p_cache_btn.set_can_focus(False)
        self.p_cache_btn.set_tooltip_text("Free the file cache (it fills up again as files are read)")
        self.p_cache_btn.connect("clicked", lambda *_: self.drop_cache())
        cache.pack_start(self.p_cache_btn, False, False, 0)
        self.cache_busy = False
        side.pack_start(cache, False, False, 0)
        page.pack_start(side, False, False, 0)
        return page

    def drop_cache(self):
        """Uvolní mezipaměť přes pomocníka s právy roota (/usr/local/bin/island-drop-caches)."""
        if self.cache_busy:
            return
        self.cache_busy = True
        before = self.stats.cache()
        self.p_cache_btn.set_label("Clearing…")
        self.p_cache_btn.set_sensitive(False)

        def work():
            helper = "/usr/local/bin/island-drop-caches"
            ok = subprocess.run(["sudo", "-n", helper], capture_output=True).returncode == 0 \
                if os.path.exists(helper) else False
            if not ok and shutil.which("pkexec"):            # bez pravidla v sudoers zeptá se na heslo
                ok = subprocess.run(["pkexec", "sh", "-c", "sync; echo 3 > /proc/sys/vm/drop_caches"],
                                    capture_output=True).returncode == 0
            GLib.idle_add(done, ok)

        def done(ok):
            freed = max(0, before - self.stats.cache())
            self.p_cache_btn.set_label(f"−{human_bytes(freed)}" if ok else "Failed")
            self.p_cache.set_text(human_bytes(self.stats.cache()))

            def reset():
                self.cache_busy = False
                self.p_cache_btn.set_label("Clear")
                self.p_cache_btn.set_sensitive(True)
                return False
            GLib.timeout_add(2000, reset)
            return False
        threading.Thread(target=work, daemon=True).start()

    def perf_card(self, parent, icon, title, subtitle):
        card = hbox(10, "tile", "perf-card")
        left = vbox(8)
        left.set_valign(Gtk.Align.CENTER)
        head = hbox(10)
        head.pack_start(label(I[icon], "perf-icon"), False, False, 0)
        names = vbox(0)
        names.set_valign(Gtk.Align.CENTER)
        names.pack_start(label(title, "perf-title", xalign=0), False, False, 0)
        names.pack_start(label(subtitle, "dim", "small", xalign=0, ellipsize=True), False, False, 0)
        head.pack_start(names, True, True, 0)
        left.pack_start(head, False, False, 0)
        temp_row = vbox(4)
        temp = label("", "small", xalign=0)
        bar = css(Gtk.ProgressBar(), "progress", "thin")
        temp_row.pack_start(temp, False, False, 0)
        temp_row.pack_start(bar, False, False, 0)
        temp_row.set_no_show_all(True)
        left.pack_start(temp_row, False, False, 0)
        card.pack_start(left, True, True, 0)
        right = vbox(2)
        right.set_valign(Gtk.Align.CENTER)
        metric = label("Usage", "dim", "small")
        badge = ScallopBadge(76)
        right.pack_start(metric, False, False, 0)
        right.pack_start(badge, False, False, 0)
        card.pack_start(right, False, False, 0)
        parent.pack_start(card, True, True, 0)
        return {"temp": temp, "bar": bar, "temp_row": temp_row, "badge": badge, "metric": metric}

    def next_mount(self):
        self.mount_index = (self.mount_index + 1) % max(1, len(list_mounts()))
        self.refresh_performance()

    def build_apps(self):
        page = vbox(8, "page")
        self.quick = vbox(6, "tile", "quick-apps")
        self.quick.pack_start(label("Quick apps", "section-title", xalign=0), False, False, 0)
        self.quick_row = hbox(4)
        self.quick.pack_start(self.quick_row, False, False, 0)
        page.pack_start(self.quick, False, False, 0)
        self.search = css(Gtk.SearchEntry(placeholder_text="Search apps"), "search")
        self.search.connect("search-changed", lambda *_: (self.flow.invalidate_filter(), self.select_first_app(),
                                                         self.quick.set_visible(not self.search.get_text())))
        self.search.connect("activate", lambda *_: self.launch_first())
        page.pack_start(self.search, False, False, 0)
        scroll = css(Gtk.ScrolledWindow(), "tile", "apps-scroll")
        scroll.set_size_request(-1, 250)        # seznam aplikací má pevnou výšku, posouvá se
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.flow = Gtk.FlowBox(homogeneous=True, column_spacing=4, row_spacing=4,
                                min_children_per_line=6, max_children_per_line=6,
                                selection_mode=Gtk.SelectionMode.SINGLE, activate_on_single_click=True)
        self.flow.set_valign(Gtk.Align.START)
        self.flow.set_filter_func(self.app_filter)
        self.flow.connect("child-activated", lambda _f, child: self.launch(child.app))
        self.flow.connect("button-press-event", self.on_app_press)     # pravé tlačítko = do rychlých aplikací
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
        favourites = set(self.quick_ids())
        for app in apps:
            item = vbox(4, "app")
            if app_key(app) in favourites:
                set_class(item, "favourite", True)
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
        self.build_quick()

    # ------------------------------------------------------------ rychlé aplikace
    QUICK_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "quick-apps")

    def quick_ids(self):
        """Oblíbené aplikace (jména .desktop souborů bez přípony), jen ty nainstalované."""
        saved = read(self.QUICK_FILE, None)
        wanted = saved.split() if saved is not None else QUICK_APPS
        found, names = [], set()
        for choice in wanted:
            for key in choice.split("|"):       # z alternativ první nainstalovaná
                app = app_by_key(key)
                if app is None:
                    continue
                name = (app.get_display_name() or key).casefold()
                if key not in found and name not in names:   # stejná aplikace dvakrát (RPM i Flatpak) jen jednou
                    found.append(key)
                    names.add(name)
                break
        return found

    def save_quick(self, keys):
        try:
            with open(self.QUICK_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(keys) + "\n")
        except OSError as err:
            print(f"island-panel: {self.QUICK_FILE}: {err}", file=sys.stderr)

    def toggle_quick(self, app):
        keys, key = self.quick_ids(), app_key(app)
        keys = [k for k in keys if k != key] if key in keys else keys + [key]
        self.save_quick(keys)
        self.apps_built = False
        self.ensure_apps()

    def build_quick(self):
        for child in self.quick_row.get_children():
            self.quick_row.remove(child)
        keys = self.quick_ids()
        for key in keys[:QUICK_APPS_MAX]:
            app = app_by_key(key)
            item = vbox(4)
            name, icons = QUICK_APP_LOOK.get(key, (None, []))
            image = app_icon(app, icons, 36)
            item.pack_start(image, False, False, 0)
            item.pack_start(label(name or app.get_display_name() or key, "app-name", ellipsize=True), False, False, 0)
            button = css(Gtk.Button(), "flat", "quick-app")
            button.add(item)
            button.set_can_focus(False)
            button.connect("clicked", lambda _b, a=app: self.launch(a))
            button.connect("button-press-event", lambda _b, ev, a=app: ev.button == 3 and (self.toggle_quick(a) or True))
            self.quick_row.pack_start(button, False, False, 0)
        if not keys:
            self.quick_row.pack_start(label("Right-click an app below to add it here.", "dim", "small", xalign=0),
                                      True, True, 0)
        self.quick_row.show_all()
        self.quick.set_visible(not self.search.get_text())

    def on_app_press(self, flow, event):
        if event.button != 3:
            return False
        child = flow.get_child_at_pos(int(event.x), int(event.y))
        if child is not None:
            self.toggle_quick(child.app)
        return True

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
        command = APP_COMMANDS.get(app_key(app))
        if command:
            spawn(*shlex.split(os.path.expanduser(command)))
        else:
            try:
                app.launch([], None)
            except GLib.Error as err:
                print(f"island-panel: {err.message}", file=sys.stderr)
        self.hide()

    # ------------------------------------------------------------ záložky
    def select(self, name):
        self.stack.set_visible_child_name(name)
        if self.visible:                          # nová záložka hned s čerstvými údaji
            GLib.idle_add(lambda: (self.refresh_performance() if name == "performance" else self.refresh()) and False)
        self.follow_height()
        GLib.idle_add(lambda: self.move_indicator() and False)
        for key, btn in self.tab_buttons.items():
            set_class(btn, "active", key == name)
        if name == "apps":
            self.ensure_apps()
            self.search.grab_focus()
        self.refresh()

    def indicator_target(self):
        btn = self.tab_buttons.get(self.stack.get_visible_child_name())
        if btn is None:
            return None
        a, base = btn.get_allocation(), self.tabs_box.get_allocation()
        if a.width <= 1:
            return None
        return (a.x - base.x, a.width)

    def move_indicator(self, animate=True, layout=False):
        target = self.indicator_target()
        if target is None:
            return
        tab = self.stack.get_visible_child_name()
        if layout and self.ind_pos is not None and tab != self.ind_tab:
            return                           # záložka se právě mění, čáru posune animace
        self.ind_tab = tab
        if self.ind_pos is None or not animate or not self.ind.get_mapped():
            if self.ind_tick is not None:
                return                       # běží animace, ta skončí na správném místě
            self.ind_pos = target
            self.ind.queue_draw()
            return
        start, began = self.ind_pos, time.monotonic()

        def tick(_widget, _clock):
            t = min(1.0, (time.monotonic() - began) / IND_SECONDS)
            e = 1 - (1 - t) ** 3
            goal = self.indicator_target() or target
            self.ind_pos = (start[0] + (goal[0] - start[0]) * e, start[1] + (goal[1] - start[1]) * e)
            self.ind.queue_draw()
            if t < 1.0:
                return GLib.SOURCE_CONTINUE
            self.ind_tick = None
            return GLib.SOURCE_REMOVE
        if self.ind_tick is not None:
            self.ind.remove_tick_callback(self.ind_tick)
        self.ind_tick = self.ind.add_tick_callback(tick)

    def draw_indicator(self, widget, cr):
        if self.ind_pos is None:
            return False
        x, width = self.ind_pos
        fg = widget.get_style_context().get_color(Gtk.StateFlags.NORMAL)
        cr.set_source_rgba(fg.red, fg.green, fg.blue, fg.alpha)
        h = widget.get_allocated_height()
        r = h / 2
        cr.new_sub_path()
        cr.arc(x + r, r, r, math.pi / 2, 3 * math.pi / 2)
        cr.arc(x + width - r, r, r, -math.pi / 2, math.pi / 2)
        cr.close_path()
        cr.fill()
        return False

    def follow_height(self, animate=True):
        """Výška obsahu podle viditelné záložky; mění se plynule a okno se přizpůsobuje každý snímek."""
        page = self.stack.get_visible_child()
        if page is None:
            return
        width = self.stack.get_allocated_width() or PANEL_WIDTH
        target = page.get_preferred_height_for_width(width)[1]
        start = self.body_h if self.body_h is not None else target
        if target == start and self.height_tick is None:
            if self.body_h != target:
                self.apply_height(target)
            return                                # výška sedí: nic nepřepočítávat (jinak by se celý panel přeskládal)
        if not animate or not self.win.get_mapped():
            self.apply_height(target)
            return
        began, length = time.monotonic(), 0.24

        def tick(_widget, _clock):
            t = min(1.0, (time.monotonic() - began) / length)
            eased = 1 - (1 - t) ** 3
            self.apply_height(round(start + (target - start) * eased))
            if t < 1.0:
                return GLib.SOURCE_CONTINUE
            self.height_tick = None
            return GLib.SOURCE_REMOVE
        if self.height_tick is not None:
            self.win.remove_tick_callback(self.height_tick)
        self.height_tick = self.win.add_tick_callback(tick)

    def apply_height(self, height):
        self.body_h = height
        self.body.set_max_content_height(-1)      # pořadí kvůli kontrole min <= max v GTK
        self.body.set_min_content_height(height)
        self.body.set_max_content_height(height)
        self.fix_window_height()
        self.update_input()

    def fix_window_height(self):
        """Stálá výška okna = lišta záložek + nejvyšší záložka (roste jen když některá záložka naroste)."""
        width = self.stack.get_allocated_width() or PANEL_WIDTH
        tallest = max(page.get_preferred_height_for_width(width)[1] for page in self.stack.get_children())
        tabs = self.root.get_preferred_height()[1] - (self.body_h or 0)
        need = tabs + tallest + 4
        if need > getattr(self, "win_h", 0):
            self.win_h = need
            self.win.set_size_request(-1, need)

    def update_input(self):
        """Klikat a najíždět jde jen na viditelný panel, ne na průhlednou část pod ním."""
        gdk_win = self.win.get_window()
        if gdk_win is None:
            return
        area = self.reveal.get_allocation()
        gdk_win.input_shape_combine_region(
            cairo.Region(cairo.RectangleInt(area.x, area.y, max(1, area.width), max(1, area.height))), 0, 0)

    @property
    def tab(self):
        return self.stack.get_visible_child_name()

    # ------------------------------------------------------------ obnova dat
    def background_sample(self):
        self.stats.sample()
        self.net.sample()
        if self.visible and self.tab == "performance":
            self.gpu.sample()
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
        if self.height_tick is None:            # obsah se změnil (např. přibyl přehrávač) -> výšku dorovnat
            GLib.idle_add(lambda: self.follow_height() and False)
        now = datetime.datetime.now()
        self.c_hour.set_text(f"{now.hour:02d}")
        self.c_min.set_text(f"{now.minute:02d}")
        if self.tab in ("dashboard", "media"):    # přehrávač je vidět jen na těchto dvou záložkách
            self.refresh_media()
        if self.tab == "dashboard":
            up = f"{I['clock']}  up {fmt_duration(self.stats.uptime())}"
            bat = self.stats.battery()
            if bat:
                icon = I["plug"] if bat[1] in ("Charging", "Full", "Not charging") else I["bat"][min(4, bat[0] // 20)]
                up += f"   {icon}  {bat[0]} %"
            self.s_uptime.set_text(up)
            for key, value in (("cpu", self.stats.cpu), ("ram", self.stats.ram()[2]), ("disk", self.stats.disk()[2])):
                gauge, text = self.g_values[key]
                gauge.set(value)
                text.set_text(f"{value:.0f}%")
            self.maybe_fetch_weather()
        # Performance obnovuje background_sample každé 2 s (spolu s měřením GPU), tady by to bylo dvakrát

    def set_power_mode(self, key):
        if self.power.busy:
            return
        self.power.busy = True
        self.power.awake(bool((self.power.config(key) or {}).get("awake")))
        self.power.current = key
        self.refresh_power_modes()

        def work():
            self.power.apply(key, self.backlight)
            GLib.idle_add(done)

        def done():
            self.power.busy = False
            self.refresh_power_modes()
            return False
        threading.Thread(target=work, daemon=True).start()

    def refresh_power_modes(self):
        for key, button in self.p_modes.items():
            set_class(button, "on", key == self.power.current)
            button.set_sensitive(not self.power.busy)

    def refresh_performance(self):
        self.refresh_power_modes()
        def card(widgets, usage, temp, metric="Usage"):
            widgets["badge"].set(f"{usage:.0f}%" if usage is not None else "—")
            widgets["metric"].set_text(metric)
            if temp is None:
                widgets["temp_row"].hide()
            else:
                widgets["temp"].set_text(f"{I['temp']}  {temp:.0f}°C")
                widgets["bar"].set_fraction(max(0.0, min(1.0, temp / 100)))
                widgets["temp_row"].show_all()
        card(self.p_cpu, self.stats.cpu, self.stats.temp())
        card(self.p_gpu, self.gpu.usage, self.gpu.temp, self.gpu.metric)
        bat = self.stats.battery()
        self.p_battery.set(bat[0] if bat else None, bat[1] if bat else "")
        mounts = list_mounts()
        device, point = mounts[self.mount_index % len(mounts)]
        used, total, pct = disk_usage(point)
        self.p_disk.set(pct)
        self.p_mount_label.set_text(f"{os.path.basename(device)}  {I['caret']}" if len(mounts) > 1
                                    else os.path.basename(device))
        self.p_disk_detail.set_text(f"{human_bytes(used)} / {human_bytes(total)}  ·  {point}")
        net = self.net
        self.p_net_graph.set(net.history_down, net.history_up)
        self.p_net["down"].set_text(human_bytes(net.down, True))
        self.p_net["up"].set_text(human_bytes(net.up, True))
        self.p_net["total"].set_text(f"{I['download']} {human_bytes(net.total[0])}   {I['upload']} {human_bytes(net.total[1])}")
        used, total, pct = self.stats.ram()
        self.p_ram.set(pct)
        self.p_ram_detail.set_text(f"{used:.1f} / {total:.1f} GB")
        if not self.cache_busy:
            self.p_cache.set_text(human_bytes(self.stats.cache()))

    def refresh_media(self):
        info, others = self.mpris.poll()
        self.media = info
        playing = bool(info and info["playing"])
        for btn in (self.m_play, self.b_play):
            btn.set_label(I["pause"] if playing else I["play"])
        for art in (self.m_art, self.b_art):
            art.set_playing(playing)
        signature = [(p["bus"], p["title"], p["playing"], p["art"]) for p in others]
        if signature != self.others_shown:
            self.others_shown = signature
            for child in self.others_list.get_children():
                self.others_list.remove(child)
            for other in others[:2]:
                self.others_list.pack_start(self.other_card(other), False, False, 0)
            self.others_list.show_all()
            self.others.set_visible(bool(others))
            for child in self.others.get_children():
                child.show_all()
        for button, key in ((self.b_shuffle, "shuffle"), (self.b_repeat, "loop")):
            supported = bool(info) and info[key] is not None
            button.set_sensitive(supported)
            set_class(button, "on", supported and info[key] not in (False, "None"))
        self.b_repeat.set_label(I["repeat"] + ("¹" if info and info["loop"] == "Track" else ""))
        if not info:
            self.m_title.set_text("Nothing playing")
            self.m_artist.set_text("")
            self.m_art.set_url(None)
            self.b_player.hide()
            self.b_title.set_text("Nothing playing")
            self.b_artist.set_text("Play some music or a video and it shows up here.")
            self.b_album.set_text("")
            self.b_progress.set_fraction(0)
            self.b_pos.set_text("")
            self.b_len.set_text("")
            self.b_art.set_url(None)
            return
        self.m_title.set_text(info["title"] or "Untitled")
        self.m_artist.set_text(info["artist"])
        self.m_art.set_url(info["art"])
        self.b_player.set_text(info["player"])
        self.b_player.show()
        self.b_title.set_text(info["title"] or "Untitled")
        self.b_artist.set_text(info["artist"])
        self.b_album.set_text(info["album"])
        self.b_album.set_visible(bool(info["album"]))
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
                    self.w_desc.set_text("unavailable")
                self.weather_at = time.monotonic() + 300    # nepovedlo se, zkusit za 5 minut
            return False

        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------ zobrazení
    def show(self, by_key=False, tab=None, origin=None):
        if screen_locked():
            return
        self.cancel_close()
        if tab:
            self.select(tab)
        if self.visible:
            return
        self.visible = True
        if self.hide_timer is not None:                 # ještě zajíždělo: jen se vrátí
            GLib.source_remove(self.hide_timer)
            self.hide_timer = None
        width = self.attach_to_bar("center", PANEL_WIDTH, origin)
        attached = self.attach is not None
        set_class(self.root, "attached", attached)
        self.root.set_size_request(width, -1)
        if GtkLayerShell.is_supported():
            mode = GtkLayerShell.KeyboardMode.EXCLUSIVE if by_key else GtkLayerShell.KeyboardMode.ON_DEMAND
            GtkLayerShell.set_keyboard_mode(self.win, mode)
            GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.TOP,
                                     self.attach[0].island_bottom() if attached else 0)
        self.calendar.reset()
        self.win.show()
        GLib.idle_add(lambda: self.visible and self.reveal.set_reveal_child(True) and False)
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
        self.reveal.set_reveal_child(False)
        self.detach_from_bar()
        if self.hide_timer is None:
            self.hide_timer = GLib.timeout_add(MORPH_MS + 30, self.finish_hide)

    def morph_rect(self):
        """Viditelná část panelu během narůstání: x, y, šířka, výška (None = celý panel)."""
        if not self.attach:
            return None
        bw, key = self.attach
        if bw.progress(key) >= 1:
            return None
        a = self.reveal.get_allocation()
        margin = self.root.get_style_context().get_margin(Gtk.StateFlags.NORMAL)
        height = a.height - margin.bottom
        width = min(bw.rect(key)[2], a.width)
        return a.x + (a.width - width) / 2, a.y, width, max(0, height)

    def clip_to_island(self, _widget, cr):
        rect = self.morph_rect()
        if rect is not None:
            x, y, w, h = rect
            island_path(cr, x, y, w, max(h, 0.1), 0, min(BAR_RADIUS, h / 2))
            cr.clip()
        return False

    def draw_morph_edge(self, widget, cr):
        rect = self.morph_rect()
        if rect is None or rect[3] < 1:
            return False
        x, y, w, h = rect
        open_outline(cr, x + 0.5, y, w - 1, h - 0.5, 0, max(0, min(BAR_RADIUS, h / 2) - 0.5), open_top=True)
        cr.set_source_rgba(*rgba_tuple(self.root.get_style_context(), "island_border", (0.49, 0.75, 0.86, 0.25)))
        cr.set_line_width(1)
        cr.stroke()
        return False

    def morph_tick(self):
        self.outer.queue_draw()

    def finish_hide(self):
        self.hide_timer = None
        if self.visible:
            return False
        self.win.hide()
        self.search.set_text("")
        self.select("dashboard")   # příště zase začít přehledem
        return False

    def toggle(self, origin=None):
        if self.visible:
            self.hide()
        else:
            self.show(by_key=origin is None, origin=origin)

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
            print("island-panel: could not set brightness (logind refused and brightnessctl is not installed)",
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
    """Svislý posuvník 0-1 ve tvaru kapsle: výplň zdola a nahoře na ní kolečko s ikonou.
    Táhnout se dá kdekoli, kolečko myši posouvá, klik na kolečko zavolá on_knob (např. ztlumit)."""

    def __init__(self, on_change, icon, on_knob=None, width=40, height=150):
        super().__init__()
        self.value, self.dim, self.on_change, self.on_knob = 0.0, False, on_change, on_knob
        self.icon = icon                  # funkce, která vrátí ikonu pro kolečko podle stavu
        self.dragging, self.knob_press = False, None
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

    def _geometry(self):
        width, height = self.get_allocated_width(), self.get_allocated_height()
        radius = width / 2
        knob_y = height - radius - self.value * (height - 2 * radius)   # střed kolečka
        return width, height, radius, knob_y

    def _from_y(self, y):
        _width, height, radius, _knob = self._geometry()
        return (height - radius - y) / max(1, height - 2 * radius)

    def on_press(self, _w, event):
        if event.button != 1:
            return True
        _width, _height, radius, knob_y = self._geometry()
        if self.on_knob is not None and abs(event.y - knob_y) <= radius:
            self.knob_press = event.y     # možná jen klik na kolečko; tažením se z toho stane posun
        else:
            self.dragging = True
            self._change(self._from_y(event.y))
        return True

    def on_motion(self, _w, event):
        if self.knob_press is not None and abs(event.y - self.knob_press) > 4:
            self.knob_press, self.dragging = None, True
        if self.dragging:
            self._change(self._from_y(event.y))
        return True

    def on_release(self, _w, event):
        if event.button == 1:
            if self.knob_press is not None:
                self.knob_press = None
                self.on_knob()
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
        width, height, radius, knob_y = self._geometry()
        ctx = self.get_style_context()
        fg = ctx.get_color(Gtk.StateFlags.NORMAL)
        colors = {}
        for name in ("pill", "pill_fg"):
            found, rgba = ctx.lookup_color(name)
            colors[name] = rgba if found else fg
        # kapsle
        cr.new_sub_path()
        cr.arc(radius, radius, radius, math.pi, 2 * math.pi)
        cr.arc(radius, height - radius, radius, 0, math.pi)
        cr.close_path()
        cr.clip()
        cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.10)
        cr.paint()
        # výplň od spodu ke středu kolečka
        pill = colors["pill"]
        cr.set_source_rgba(pill.red, pill.green, pill.blue, 0.45 if self.dim else 0.85)
        cr.rectangle(0, knob_y, width, height - knob_y)
        cr.fill()
        # hodnota 0-100 na té straně kapsle, kde zrovna není kolečko
        number = self.create_pango_layout(str(round(self.value * 100)))
        font = self.get_pango_context().get_font_description().copy()
        font.set_absolute_size(11 * Pango.SCALE)
        font.set_weight(Pango.Weight.BOLD)
        number.set_font_description(font)
        nw, nh = number.get_pixel_size()
        if knob_y < height / 2:      # kolečko nahoře -> číslo dole ve výplni (tmavé)
            cr.move_to(radius - nw / 2, height - radius - nh / 2)
            dark = colors["pill_fg"]
            cr.set_source_rgba(dark.red, dark.green, dark.blue, 0.75)
        else:                        # kolečko dole -> číslo nahoře v prázdné části (světlé)
            cr.move_to(radius - nw / 2, radius - nh / 2)
            cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.75)
        PangoCairo.show_layout(cr, number)
        # kolečko s ikonou, široké jako celý posuvník
        cr.new_path()
        cr.arc(radius, knob_y, radius - 1, 0, 2 * math.pi)
        cr.set_source_rgba(pill.red, pill.green, pill.blue, 1.0)
        cr.fill_preserve()
        dark = colors["pill_fg"]
        cr.set_source_rgba(dark.red, dark.green, dark.blue, 0.18)
        cr.set_line_width(1)
        cr.stroke()
        layout = self.create_pango_layout(self.icon())
        font = self.get_pango_context().get_font_description().copy()
        font.set_absolute_size(radius * 0.72 * Pango.SCALE)
        layout.set_font_description(font)
        tw, th = layout.get_pixel_size()
        cr.move_to(radius - tw / 2, knob_y - th / 2)
        cr.set_source_rgba(dark.red, dark.green, dark.blue, 0.5 if self.dim else 1.0)
        PangoCairo.show_layout(cr, layout)
        return False


class SidePanel(AutoHide):
    """Úzký panel u pravého okraje s hlasitostí a jasem."""

    def __init__(self, app):
        self.audio, self.backlight = Audio(), Backlight()
        self.visible, self.close_timer, self.poll_timer = False, None, None
        self.pending, self.apply_timer = {}, None
        self.muted = False

        self.win = layer_window(app, "island-side", GtkLayerShell.Edge.RIGHT, EDGE_OVERHANG)
        self.watch_pointer()
        root = vbox(10)
        root.set_name("side")
        root.set_margin_end(EDGE_OVERHANG)   # vyrovná přesah okna, panel zůstane na stejném místě
        self.win.add(root)
        self.win.connect("draw", lambda win, cr: draw_edge_panel(win, root, cr))

        # hlasitost: klik na kolečko ztlumí / zruší ztlumení
        self.v_slider = VSlider(self.set_volume, self.volume_icon, on_knob=self.toggle_mute, height=SLIDER_HEIGHT)
        root.pack_start(self.v_slider, False, False, 0)
        self.b_slider = None
        if self.backlight.available:
            self.b_slider = VSlider(self.set_brightness, lambda: I["sun"], height=SLIDER_HEIGHT)
            root.pack_start(self.b_slider, False, False, 0)
        root.show_all()

    def volume_icon(self):
        value = self.v_slider.value
        return I["vol_off"] if self.muted or value <= 0.005 else I["vol_low"] if value < 0.5 else I["vol_high"]

    # ------------------------------------------------------------ hodnoty
    def refresh(self):
        vol = self.audio.get()
        if vol is not None and not self.v_slider.dragging:
            value, self.muted = vol
            self.v_slider.set(value, dim=self.muted)
        if self.b_slider is not None and not self.b_slider.dragging:
            value = self.backlight.get()
            if value is not None:
                self.b_slider.set(value)

    def set_volume(self, value):
        self.muted = False
        self.apply("volume", lambda: self.audio.set(value))

    def set_brightness(self, value):
        value = max(Backlight.MIN, value)
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
        if screen_locked():
            return
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
        return "now"
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
        self.other = "another program"
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
        self.save_summary()

    def save_summary(self):
        """Krátký výpis pro zamykací obrazovku: jen aplikace, nadpis a čas (bez textu zpráv)."""
        if not self.active:
            return
        data = {"count": len(self.items), "dnd": self.dnd,
                "items": [{"app": n.app, "summary": n.summary, "time": n.time} for n in self.items[:8]]}
        path = os.path.join(STATE_DIR, "notifications.json")
        try:
            os.makedirs(STATE_DIR, exist_ok=True)
            with open(path + ".part", "w", encoding="utf-8") as f:
                json.dump(data, f)
            os.replace(path + ".part", path)
        except OSError:
            pass

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
        note.app = params.get_child_value(0).get_string() or "Notification"
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
# OBS: stav nahrávání přes vestavěný WebSocket (obs-websocket 5)
# ----------------------------------------------------------------------------
OBS_HOST, OBS_PORT = "127.0.0.1", 4455
OBS_PASS_FILE = os.path.expanduser("~/.config/obs-rec/password")


class WS:
    def __init__(self, host, port, timeout=2):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        key = base64.b64encode(secrets.token_bytes(16)).decode()
        self.sock.sendall((f"GET / HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\n"
                           f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                           f"Sec-WebSocket-Protocol: obswebsocket.json\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.sock.recv(1024)
            if not chunk:
                raise ConnectionError("closed during handshake")
            head += chunk
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise ConnectionError("handshake refused")
        self.buf = head.split(b"\r\n\r\n", 1)[1]

    def _read(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("closed")
            self.buf += chunk
        data, self.buf = self.buf[:n], self.buf[n:]
        return data

    def send(self, obj):
        data = json.dumps(obj).encode()
        head = bytes([0x81])
        n = len(data)
        if n < 126:
            head += bytes([0x80 | n])
        elif n < 65536:
            head += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            head += bytes([0x80 | 127]) + struct.pack(">Q", n)
        mask = secrets.token_bytes(4)
        self.sock.sendall(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self):
        while True:
            b1, b2 = self._read(2)
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            if b2 & 0x80:
                mask = self._read(4)
                payload = bytes(b ^ mask[i % 4] for i, b in enumerate(self._read(n)))
            else:
                payload = self._read(n)
            op = b1 & 0x0F
            if op == 8:
                raise ConnectionError("closed by server")
            if op == 9:                                    # ping -> pong
                self.sock.sendall(bytes([0x8A, 0x80]) + secrets.token_bytes(4))
                continue
            if op in (1, 2):
                return json.loads(payload)

    def close(self):
        try:
            self.sock.sendall(bytes([0x88, 0x80]) + secrets.token_bytes(4))   # slušné ukončení
            self.sock.close()
        except OSError:
            pass


class ObsClient:
    def __init__(self):
        self.ws = WS(OBS_HOST, OBS_PORT)
        hello = self.ws.recv()["d"]
        ident = {"rpcVersion": 1, "eventSubscriptions": 0}
        auth = hello.get("authentication")
        if auth:
            password = open(OBS_PASS_FILE).read().strip() if os.path.exists(OBS_PASS_FILE) else ""
            secret = base64.b64encode(hashlib.sha256((password + auth["salt"]).encode()).digest()).decode()
            ident["authentication"] = base64.b64encode(
                hashlib.sha256((secret + auth["challenge"]).encode()).digest()).decode()
        self.ws.send({"op": 1, "d": ident})
        reply = self.ws.recv()
        if reply.get("op") != 2:
            raise PermissionError("wrong password")
        self.counter = 0

    def request(self, kind):
        self.counter += 1
        rid = str(self.counter)
        self.ws.send({"op": 6, "d": {"requestType": kind, "requestId": rid}})
        while True:
            msg = self.ws.recv()
            if msg.get("op") == 7 and msg["d"].get("requestId") == rid:
                return msg["d"].get("responseData") or {}



class ObsRecorder:
    """Drží spojení s OBS; status() vrací None (OBS neběží / nenahrává) nebo (pauza?, milisekundy)."""

    def __init__(self):
        self.client, self.lock = None, threading.Lock()

    def call(self, kind):
        with self.lock:
            try:
                if self.client is None:
                    self.client = ObsClient()
                return self.client.request(kind)
            except (OSError, ConnectionError, ValueError, KeyError, PermissionError):
                if self.client is not None:
                    self.client.ws.close()
                self.client = None
                return None

    def status(self):
        st = self.call("GetRecordStatus")
        if not st or not st.get("outputActive"):
            return None
        return bool(st.get("outputPaused")), int(st.get("outputDuration", 0))


# ----------------------------------------------------------------------------
# Ovládací centrum u pravého okraje
# ----------------------------------------------------------------------------
class ControlCenter(AutoHide):
    """Oznámení, otevřená okna, rychlé přepínače a sloupec vypnout / odhlásit."""

    SESSION = [   # klíč, ikona, popis, chce potvrzení druhým kliknutím
        ("lock", "lock", "Lock", False),
        ("suspend", "moon", "Suspend", False),
        ("logout", "signout", "Log out", True),
        ("reboot", "refresh", "Restart", True),
        ("poweroff", "power", "Shut down", True),
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
        outer = hbox(0)                    # sloupec tlačítek přilepený k panelu
        outer.set_margin_end(EDGE_OVERHANG)
        self.win.add(outer)
        outer.pack_start(self.build_session(), False, False, 0)

        main = vbox(10)
        main.set_name("center")
        main.set_size_request(CENTER_WIDTH, -1)
        self.win.connect("draw", lambda win, cr: draw_edge_panel(win, main, cr, self.session_box))
        if GtkLayerShell.is_supported():
            GtkLayerShell.set_exclusive_zone(self.win, 0)       # začíná pod lištou, ne přes ni
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
            button.set_tooltip_text(title)
            button.title_label = label(I[icon], "session-icon")   # jen ikona; při potvrzování se změní na fajfku
            button.title = I[icon]
            button.add(button.title_label)
            button.connect("clicked", lambda _b, k=key: self.session_clicked(k))
            column.pack_start(button, False, False, 0)
            self.session_buttons[key] = button
        return column

    def session_command(self, key):
        if key == "lock":
            custom = os.path.expanduser(LOCK_COMMAND)
            if os.path.exists(custom):
                return (sys.executable, custom) if custom.endswith(".py") else (custom,)
            for cmd in (("hyprlock",), ("swaylock",), ("loginctl", "lock-session")):
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
            button.title_label.set_text(I["check"])     # druhé kliknutí potvrdí
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
        # nahrávání OBS: vždy úplně nahoře, jen když se nahrává
        self.obs = ObsRecorder()
        self.rec_busy, self.rec_timer = False, None
        self.rec_stopping = 0            # čas kliknutí na stop (0 = nezastavuje se)
        rec = self.rec_card = hbox(10, "tile", "rec-card")
        self.rec_dot = label(I["rec"], "rec-dot")
        rec.pack_start(self.rec_dot, False, False, 0)
        self.rec_spin = Gtk.Spinner()
        self.rec_spin.get_style_context().add_class("rec-spin")
        self.rec_spin.set_valign(Gtk.Align.CENTER)
        rec.pack_start(self.rec_spin, False, False, 0)
        text = vbox(0)
        text.set_valign(Gtk.Align.CENTER)
        self.rec_title = label("Recording", "rec-title", xalign=0)
        self.rec_time = label("00:00", "rec-time", xalign=0)
        text.pack_start(self.rec_title, False, False, 0)
        text.pack_start(self.rec_time, False, False, 0)
        rec.pack_start(text, True, True, 0)
        self.rec_pause = css(Gtk.Button(label=I["pause"]), "flat", "rec-btn")
        self.rec_pause.connect("clicked", lambda *_: self.obs_action("ToggleRecordPause"))
        stop = css(Gtk.Button(label=I["stop"]), "flat", "rec-btn", "rec-stop")
        stop.connect("clicked", lambda *_: self.stop_recording())
        self.rec_stop = stop
        for b in (self.rec_pause, stop):
            b.set_valign(Gtk.Align.CENTER)
            b.set_can_focus(False)
            rec.pack_start(b, False, False, 0)
        rec.show_all()
        self.rec_spin.hide()
        self.rec_spin.set_no_show_all(True)
        rec.set_no_show_all(True)
        rec.hide()
        section.pack_start(rec, False, False, 0)
        head = hbox(8)
        self.n_title = label("Notifications", "section-title", xalign=0)
        head.pack_start(self.n_title, True, True, 0)
        self.n_clear = css(Gtk.Button(label=f"{I['trash']}  Clear all"), "flat", "chip-btn")
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

    def poll_recording(self):
        """Každou sekundu, jen když je centrum otevřené; dotaz běží na pozadí."""
        if not self.visible:
            self.rec_timer = None
            return False
        if not self.rec_busy:
            self.rec_busy = True

            def work():
                result = self.obs.status()
                GLib.idle_add(done, result)

            def done(result):
                self.rec_busy = False
                if self.rec_stopping:
                    if result is None:
                        self.rec_finished()
                    elif time.monotonic() - self.rec_stopping > 20:
                        self.rec_set_stopping(False)      # OBS nezastavilo, vrátit normální stav
                    return False
                if getattr(self, "rec_saved", False):
                    return False
                if result is None:
                    self.rec_card.hide()
                else:
                    paused, ms = result
                    sec = ms // 1000
                    self.rec_time.set_text(f"{sec // 3600}:{sec // 60 % 60:02d}:{sec % 60:02d}" if sec >= 3600
                                           else f"{sec // 60:02d}:{sec % 60:02d}")
                    self.rec_title.set_text("Recording paused" if paused else "Recording")
                    self.rec_pause.set_label(I["rec"] if paused else I["pause"])
                    set_class(self.rec_card, "paused", paused)
                    self.rec_card.show()
                return False
            threading.Thread(target=work, daemon=True).start()
        return True

    def rec_set_stopping(self, on):
        self.rec_stopping = time.monotonic() if on else 0
        self.rec_dot.set_visible(not on)
        self.rec_spin.set_visible(on)
        (self.rec_spin.start if on else self.rec_spin.stop)()
        self.rec_pause.set_sensitive(not on)
        self.rec_stop.set_sensitive(not on)
        set_class(self.rec_card, "stopping", on)
        if on:
            set_class(self.rec_card, "paused", False)
            self.rec_title.set_text("Stopping…")
            self.rec_time.set_text("Saving the recording")

    def stop_recording(self):
        if self.rec_stopping:
            return
        self.rec_set_stopping(True)
        self.obs_action("StopRecord")

    def rec_finished(self):
        """Nahrávání skončilo: chvíli ukázat "Saved", pak kartu schovat."""
        self.rec_set_stopping(False)
        self.rec_title.set_text("Recording saved")
        self.rec_time.hide()
        self.rec_dot.set_text(I["check"])
        self.rec_pause.hide()
        self.rec_stop.hide()
        set_class(self.rec_card, "saved", True)
        self.rec_saved = True

        def reset():
            self.rec_card.hide()
            self.rec_dot.set_text(I["rec"])
            self.rec_time.set_text("00:00")
            self.rec_time.show()
            self.rec_pause.show()
            self.rec_stop.show()
            set_class(self.rec_card, "saved", False)
            self.rec_saved = False
            return False
        GLib.timeout_add(1800, reset)

    def obs_action(self, kind):
        def work():
            self.obs.call(kind)
            GLib.timeout_add(300, lambda: self.poll_recording() and False)
        threading.Thread(target=work, daemon=True).start()

    def on_notifications_changed(self):
        if self.visible:
            self.refresh_notifications()

    def refresh_notifications(self):
        for child in self.n_list.get_children():
            self.n_list.remove(child)
        count = len(self.server.items)
        self.n_title.set_text(f"Notifications ({count})" if count else "Notifications")
        self.n_clear.set_visible(count > 0)
        if not self.server.active:
            text = (f"Notifications are handled by \"{self.server.other}\" right now,\nso they are not shown here."
                    if self.server.other else "The notification service did not start.")
            self.n_list.pack_start(css(label(text, "dim", "empty"), "tile"), False, False, 0)
        elif not count:
            self.n_list.pack_start(css(label("No notifications", "dim", "empty"), "tile"), False, False, 0)
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
            group.pack_start(label(f"and {len(notes) - 4} more", "dim", xalign=0), False, False, 0)
        return group

    # ------------------------------------------------------------ otevřená okna
    def build_windows(self):
        section = vbox(8)
        self.w_title = label("Open windows", "section-title", xalign=0)
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
                "title": client.get("title") or client.get("class") or "Window",
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
            self.w_title.set_text("Open windows")
            self.w_list.pack_start(label("The window list needs Hyprland", "dim", "empty"), False, False, 0)
        elif not clients:
            self.w_title.set_text("Open windows")
            self.w_list.pack_start(label("No open windows", "dim", "empty"), False, False, 0)
        else:
            self.w_title.set_text(f"Open windows ({len(clients)})")
        for client in clients or []:
            row = hbox(2, "window-row")
            focus = css(Gtk.Button(), "flat", "window-btn")
            inner = hbox(10)
            inner.pack_start(self.icons.image(client["class"], 26), False, False, 0)
            text = vbox(0)
            text.pack_start(label(client["title"], xalign=0, ellipsize=True), False, False, 0)
            place = f"workspace {client['workspace_name'] or client['workspace']}"
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
        section.pack_start(label("Quick toggles", "section-title", xalign=0), False, False, 0)
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
            ("mic", "mic", "mic_off", "Mic", bool(wpctl),
             lambda: bool(run(wpctl, "get-volume", mic)) and "MUTED" not in run(wpctl, "get-volume", mic),
             lambda on: run(wpctl, "set-mute", mic, "0" if on else "1")),
            ("dnd", "bell_off", "bell", "Silent", True,
             lambda: self.server.dnd,
             self.set_dnd),
            ("awake", "coffee", "coffee", "Awake", bool(inhibit),
             lambda: self.inhibit is not None and self.inhibit.poll() is None,
             lambda on: self.set_awake(on, inhibit)),
        ]
        self.toggle_buttons, self.toggle_state = {}, {}
        for key, _on, off, title, available, _get, _set in self.toggles:
            button = css(Gtk.Button(), "flat", "toggle")
            icon = label(I[off], "toggle-icon")        # jen ikona, popis v bublině
            button.add(icon)
            button.set_tooltip_text(title)
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
                    [program, "--what=idle:sleep", "--who=Island panel", "--why=Awake is on", "sleep", "infinity"],
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
                print(f"island-panel: toggle {key}: {err}", file=sys.stderr)
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
        if screen_locked():
            return
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
        if self.rec_timer is None:
            self.poll_recording()
            self.rec_timer = GLib.timeout_add(1000, self.poll_recording)
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
WALL_SHADE_COLOR = (0.0, 0.0, 0.0)
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
    __slots__ = ("path", "name", "ext", "folder", "kind", "key", "search", "small", "surface", "made_for",
                 "busy", "failed")

    def __init__(self, path, root, moving=()):
        st = os.stat(path)
        self.path = path
        self.name, ext = os.path.splitext(os.path.basename(path))
        self.ext = ext.lower()
        rel = os.path.relpath(path, root)
        self.folder = rel.split(os.sep)[0] if os.sep in rel else ""
        self.kind = "vid" if self.ext in moving else "pic"      # vid = pohyblivá tapeta (video nebo GIF)
        # klíč náhledu: když se soubor změní, vznikne nový náhled
        self.key = hashlib.sha1(f"2|{path}|{st.st_mtime_ns}|{st.st_size}|{THUMB_H}".encode()).hexdigest()
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
        # Co se pouští jako pohyblivá tapeta. GIF umí animovaně jen mpvpaper; bez něj zůstane
        # obyčejným obrázkem a na ploše je vidět jeho první snímek.
        self.moving = VIDEO_EXTS | {".gif"} if self.video else set()
        self.video_frames = bool(shutil.which("ffmpegthumbnailer") or shutil.which("ffmpeg"))
        self.scale = 1                                 # měřítko displeje, pro které se náhledy chystají
        self.cond = threading.Condition()
        self.queue, self.warm = [], []                 # náhledy potřeba hned / připravit do zásoby
        self.dirty, self.started = False, False
        self.on_loaded = None
        self.children = []                             # programy s tapetou, které spustil panel
        self.fx = None                                 # přechod mezi tapetami (WallpaperFx), nastaví App
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
                    if name.startswith(".") or not (ext in self.exts or ext in self.moving):
                        continue
                    path = os.path.join(folder, name)
                    if path in seen:
                        continue
                    seen.add(path)
                    try:
                        item = WallItem(path, root, self.moving)
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
        return not item.busy and not item.failed and (item.ext not in VIDEO_EXTS or self.video_frames)

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
                print(f"island-panel: thumbnail {item.path}: {err}", file=sys.stderr)
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
            if item.ext in VIDEO_EXTS:
                source = self.video_frame(item)
            else:
                fmt, width, tall = GdkPixbuf.Pixbuf.get_file_info(item.path)
                if fmt is not None:
                    size = [width, tall]
            try:
                if item.ext == ".gif":
                    # animovaný GIF se zmenšený načíst nedá, proto celý a zmenšit až první snímek
                    frame = GdkPixbuf.Pixbuf.new_from_file(source)
                    ratio = min(THUMB_MAX_W / frame.get_width(), THUMB_H / frame.get_height())
                    pixbuf = frame.scale_simple(max(1, round(frame.get_width() * ratio)),
                                                max(1, round(frame.get_height() * ratio)),
                                                GdkPixbuf.InterpType.BILINEAR)
                else:
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
        raise RuntimeError("could not grab a frame from the video")

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

    def apply(self, path, remember=True, animate=True):
        """Nastaví tapetu, obvykle s přechodem (nová se rozroste v kruhu)."""
        if remember:
            try:
                os.makedirs(STATE_DIR, exist_ok=True)
                with open(self.state_file, "w", encoding="utf-8") as f:
                    f.write(path + "\n")
            except OSError as err:
                print(f"island-panel: {self.state_file}: {err}", file=sys.stderr)
        moving = os.path.splitext(path)[1].lower() in self.moving
        if animate and not moving and WALL_TRANSITION and self.fx is not None:
            self.fx.start(path, self.launch)
        else:
            self.launch(path)

    def launch(self, path):
        """Spustí program s tapetou a vrátí jeho PID. Nová tapeta se spustí přes starou
        a stará se ukončí až o chvíli později, takže plocha neproblikne."""
        old = [pid for pid, _cmd in processes("swaybg", "mpvpaper")]
        if os.path.splitext(path)[1].lower() in self.moving:
            cmd = ["mpvpaper", "-o", WALL_VIDEO_OPTIONS, "*", path]
        else:
            cmd = ["swaybg", "-i", path, "-m", WALL_FILL_MODE]
        try:
            child = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL, start_new_session=True)
        except OSError as err:
            print(f"island-panel: {cmd[0]}: {err}", file=sys.stderr)
            return None
        self.children.append(child)
        GLib.timeout_add(900, self.stop, old)
        return child.pid

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
        # Pohyblivou tapetu musí pouštět mpvpaper; swaybg spuštěný po přihlášení z ní umí nanejvýš první snímek.
        program = "mpvpaper" if os.path.splitext(path)[1].lower() in self.moving else "swaybg"
        for _pid, cmd in processes(program):
            # běží s ní, nebo s její zmenšenou kopií z přechodu (screen-*.jpg v mezipaměti)
            if path in cmd or any(arg.startswith(os.path.join(self.cache, "screen-")) for arg in cmd):
                return
        self.apply(path, remember=False, animate=False)

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


class WallpaperFx:
    """Přechod mezi tapetami: nad starou tapetou se z rohu rozroste kruh s novou.

    Kreslí se do průhledné vrstvy hned nad tapetou (pod okny a lištou). Až kruh zakryje celou
    plochu, spustí se swaybg se zmenšenou kopií obrázku (načte se hned), a jakmile se objeví,
    vrstva zmizí. Zmenšená kopie má velikost obrazovky, takže swaybg navíc zabírá méně paměti."""

    def __init__(self, app, store):
        self.app, self.store = app, store
        self.run, self.windows = 0, []

    def monitors(self):
        display = Gdk.Display.get_default()
        found = []
        for index in range(display.get_n_monitors()):
            monitor = display.get_monitor(index)
            area, scale = monitor.get_geometry(), monitor.get_scale_factor()
            found.append((monitor, area.width, area.height, scale))
        return found

    def start(self, path, launch):
        self.run += 1
        run = self.run
        self.close()                       # předchozí přechod, pokud ještě běží, se zahodí
        screens = self.monitors()
        sizes = [(w * s, h * s) for _m, w, h, s in screens]
        Connections.background(lambda: self.prepare(path, sizes),
                               lambda result: self.begin(run, path, launch, screens, result))

    def prepare(self, path, sizes):
        """(na pozadí) Zmenší obrázek na velikost obrazovky, uloží ho a připraví obrázek pro každý monitor."""
        fmt, width, height = GdkPixbuf.Pixbuf.get_file_info(path)
        if fmt is None:
            raise ValueError("neznámý formát")
        need_w, need_h = max(w for w, _h in sizes), max(h for _w, h in sizes)
        scale = min(1.0, max(need_w / width, need_h / height))
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, max(1, round(width * scale)),
                                                         max(1, round(height * scale)), False)
        pixbuf = pixbuf.apply_embedded_orientation() or pixbuf
        if pixbuf.get_has_alpha():
            pixbuf = pixbuf.composite_color_simple(pixbuf.get_width(), pixbuf.get_height(),
                                                   GdkPixbuf.InterpType.NEAREST, 255, 64, 0, 0)
        os.makedirs(self.store.cache, exist_ok=True)
        stamp = hashlib.sha1(f"{path}|{os.stat(path).st_mtime_ns}|{need_w}x{need_h}".encode()).hexdigest()[:16]
        screen = os.path.join(self.store.cache, f"screen-{stamp}.jpg")
        if not os.path.exists(screen):
            pixbuf.savev(screen + ".part", "jpeg", ["quality"], ["95"])
            os.replace(screen + ".part", screen)
        old = sorted((f for f in os.listdir(self.store.cache) if f.startswith("screen-") and f.endswith(".jpg")),
                     key=lambda f: os.path.getmtime(os.path.join(self.store.cache, f)))
        for name in old[:-3]:                 # pár posledních nechat, mohou ještě běžet
            try:
                os.remove(os.path.join(self.store.cache, name))
            except OSError:
                pass
        surfaces = []
        for width_px, height_px in sizes:       # obrázek přesně na velikost monitoru, ať se pak jen kopíruje
            surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width_px, height_px)
            cr = cairo.Context(surface)
            fit = max(width_px / pixbuf.get_width(), height_px / pixbuf.get_height())
            cr.translate((width_px - pixbuf.get_width() * fit) / 2, (height_px - pixbuf.get_height() * fit) / 2)
            cr.scale(fit, fit)
            Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
            cr.get_source().set_filter(cairo.FILTER_GOOD)
            cr.paint()
            surfaces.append(surface)
        return screen, surfaces

    def begin(self, run, path, launch, screens, result):
        if run != self.run:
            return
        if not isinstance(result, tuple):      # obrázek nejde připravit: vyměnit bez přechodu
            print(f"island-panel: přechod {path}: {result}", file=sys.stderr)
            launch(path)
            return
        screen, surfaces = result
        for (monitor, width, height, scale), surface in zip(screens, surfaces):
            win = layer_window(self.app, "island-wallfx")
            if GtkLayerShell.is_supported():
                GtkLayerShell.set_layer(win, GtkLayerShell.Layer.BOTTOM)     # nad tapetou, pod okny
                GtkLayerShell.set_monitor(win, monitor)
                for edge in (GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT, GtkLayerShell.Edge.BOTTOM):
                    GtkLayerShell.set_anchor(win, edge, True)
                GtkLayerShell.set_keyboard_mode(win, GtkLayerShell.KeyboardMode.NONE)
            ox, oy = width * WALL_TRANSITION_POS[0], height * WALL_TRANSITION_POS[1]
            win.fx = {"surface": surface, "scale": scale, "origin": (ox, oy), "radius": 0.0,
                      "reach": max(math.hypot(ox - cx, oy - cy) for cx in (0, width) for cy in (0, height))}
            win.connect("draw", self.draw)
            win.connect("realize", lambda w: w.get_window().input_shape_combine_region(cairo.Region(), 0, 0))
            win.show()
            self.windows.append(win)
        self.started = None
        self.windows[0].add_tick_callback(lambda _w, clock: self.tick(run, clock, screen, launch))

    def tick(self, run, clock, screen, launch):
        if run != self.run or not self.windows:
            return GLib.SOURCE_REMOVE
        now = clock.get_frame_time() / 1e6
        if self.started is None:
            self.started = now
        progress = min(1.0, (now - self.started) * 1000 / max(1, WALL_TRANSITION_MS))
        eased = 2 * progress ** 2 if progress < 0.5 else 1 - (-2 * progress + 2) ** 2 / 2   # plynulý rozjezd i dojezd
        for win in self.windows:
            old = win.fx["radius"]
            win.fx["radius"] = eased * win.fx["reach"] + (2 if progress >= 1 else 0)
            if progress >= 1:
                win.queue_draw()
            else:
                self.damage(win, old, win.fx["radius"])
        if progress < 1.0:
            return GLib.SOURCE_CONTINUE
        # kruh zakryl plochu: pod ním teď spustit skutečnou tapetu a počkat, až se ukáže
        pid = launch(screen)
        self.waited = 0
        GLib.timeout_add(100, self.wait_ready, run, pid)
        return GLib.SOURCE_REMOVE

    @staticmethod
    def damage(win, old, new):
        """Překreslit jen proužek mezi minulým a novým kruhem (po pruzích), ne celou obrazovku.
        Ušetří to hodně práce, hlavně na displeji s vysokým rozlišením."""
        ox, oy = win.fx["origin"]
        width, height = win.get_allocated_width(), win.get_allocated_height()
        band = 24
        for y0 in range(0, height, band):
            y1 = min(height, y0 + band)
            near = 0 if y0 <= oy <= y1 else min(abs(y0 - oy), abs(y1 - oy))
            far = max(abs(y0 - oy), abs(y1 - oy))
            if new <= near:
                continue
            reach = math.sqrt(new * new - near * near)
            left, right = max(0.0, ox - reach), min(float(width), ox + reach)
            spans = [(left, right)]
            if old > far:                    # tuhle část pruhu už pokrývá minulý kruh
                inner = math.sqrt(old * old - far * far)
                spans = [(left, max(left, ox - inner)), (min(right, ox + inner), right)]
            for x0, x1 in spans:
                if x1 > x0:
                    win.queue_draw_area(int(x0) - 1, y0, int(math.ceil(x1 - x0)) + 2, y1 - y0)

    def wait_ready(self, run, pid):
        """Počká, až se nová tapeta objeví (v Hyprlandu se to dá zjistit), a pak vrstvu schová."""
        if run != self.run:
            return False
        self.waited += 100
        hyprctl = shutil.which("hyprctl")
        ready = False
        if hyprctl and pid:
            try:
                ready = self.mapped(json.loads(run(hyprctl, "layers", "-j") or "{}"), pid)
            except ValueError:
                pass
        elif self.waited >= 1200:            # bez Hyprlandu se to zjistit nedá, stačí chvíle
            ready = True
        if ready or self.waited >= 5000:
            GLib.timeout_add(250, lambda: (run == self.run and self.close()) and False)
            return False
        return True

    @classmethod
    def mapped(cls, data, pid):
        """Je ve výpisu 'hyprctl layers -j' vrstva tapety (namespace wallpaper) od procesu pid?"""
        if isinstance(data, dict):
            if data.get("namespace") == "wallpaper" and data.get("pid") == pid:
                return True
            data = list(data.values())
        return isinstance(data, list) and any(cls.mapped(item, pid) for item in data)

    def draw(self, win, cr):
        fx = win.fx
        if fx["radius"] <= 0:
            return True
        cr.arc(fx["origin"][0], fx["origin"][1], fx["radius"], 0, 2 * math.pi)
        cr.clip()
        cr.scale(1 / fx["scale"], 1 / fx["scale"])
        cr.set_source_surface(fx["surface"], 0, 0)
        cr.paint()
        return True

    def close(self):
        for win in self.windows:
            win.destroy()
        self.windows = []


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
        caption.set_no_show_all(not WALL_CAPTION)
        root.pack_start(caption, False, False, 0)
        hint = label("← →  select      Enter  apply      Space  preview"
                     "      type  search      Esc  close", "wall-hint")
        hint.set_halign(Gtk.Align.CENTER)
        hint.set_no_show_all(not WALL_HINT)
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
        self.filters = [("all", "ALL")]
        if any(i.kind == "vid" for i in self.store.items):
            self.filters += [("pic", "PIC"), ("vid", "VID")]
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
            parts.append("current")
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
        cr.set_source_rgba(0.0, 0.0, 0.0, WALL_DIM)
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
            text = "No wallpaper matches the filter"
        else:
            text = "No pictures in " + ", ".join(WALLPAPER_DIRS)
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
        if item.ext == ".gif" or item.kind == "vid":
            tags.append(("GIF" if item.ext == ".gif" else "VID", False))
        elif WALL_TAGS:
            tags.append(("PIC", False))
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
        if screen_locked():
            return
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


# ----------------------------------------------------------------------------
# Wi-Fi a Bluetooth
# ----------------------------------------------------------------------------
TOOL_ENV = dict(os.environ, LC_ALL="C.UTF-8", LANGUAGE="C")   # nástroje ať odpovídají anglicky, výstup se čte strojově


def tool(*cmd, timeout=10):
    """Spustí systémový nástroj a vrátí (úspěch, standardní výstup, chybový výstup)."""
    try:
        done = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                              errors="replace", timeout=timeout, env=TOOL_ENV)
        return done.returncode == 0, done.stdout, done.stderr
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except OSError as err:
        return False, "", str(err)


def split_terse(line):
    """Rozdělí řádek z 'nmcli -t' na pole. Dvojtečky uvnitř hodnot jsou tam zapsané jako '\\:'."""
    fields, current, escaped = [], "", False
    for char in line:
        if escaped:
            current, escaped = current + char, False
        elif char == "\\":
            escaped = True
        elif char == ":":
            fields.append(current)
            current = ""
        else:
            current += char
    fields.append(current)
    return fields


class SignalBars(Gtk.DrawingArea):
    """Čtyři sloupečky síly signálu."""

    def __init__(self, percent):
        super().__init__()
        self.level = 0 if percent < 5 else 1 if percent < 35 else 2 if percent < 55 else 3 if percent < 75 else 4
        self.set_size_request(18, 14)
        self.set_valign(Gtk.Align.CENTER)
        css(self, "net-bars")
        self.connect("draw", self.on_draw)

    def on_draw(self, _widget, cr):
        color = self.get_style_context().get_color(Gtk.StateFlags.NORMAL)
        height = self.get_allocated_height()
        for bar in range(4):
            tall = 4 + bar * (height - 4) / 3
            cr.rectangle(bar * 5, height - tall, 3, tall)
            cr.set_source_rgba(color.red, color.green, color.blue, 1.0 if bar < self.level else 0.22)
            cr.fill()
        return False


class ConnPage:
    """Společný základ stránek Wi-Fi a Bluetooth: seznam položek, jedna může být rozbalená,
    dotazy na systém i akce běží na pozadí, aby okno nezamrzalo."""
    key, title, manager, manager_label = "", "", "", ""
    off_text, missing_text, empty_text = "", "", ""

    def __init__(self, owner):
        self.owner = owner
        self.items, self.power = [], None          # power: True / False / None = služba neodpovídá
        self.expanded, self.busy = None, None      # klíč rozbalené položky / položky, na které se pracuje
        self.message, self.failed = "", False      # hláška u rozbalené položky
        self.secret, self.reveal = "", False       # rozepsané heslo
        self.loading, self.deep, self.loaded_once, self.drawn = False, False, False, None
        self.entry = None
        self.switching, self.switch_error = None, ""      # cílový stav přepínače, dokud se pracuje
        self.settle = None                                # kdy práce skončila (čeká se na potvrzení stavu)

        self.box = vbox(8)
        self.note = label("", "dim", "small", xalign=0)
        self.note.set_no_show_all(True)
        self.box.pack_start(self.note, False, False, 0)
        self.rows = vbox(2)
        scroll = self.scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_no_show_all(True)
        scroll.add(self.rows)
        self.rows.show()
        self.box.pack_start(scroll, False, False, 0)
        if self.manager and shutil.which(self.manager):
            more = Connections.button(label(self.manager_label, "dim", "small"), "flat", "net-more")
            more.set_halign(Gtk.Align.START)
            more.connect("clicked", lambda _b: (spawn(self.manager), self.owner.hide()))
            self.box.pack_start(more, False, False, 0)
        self.box.show_all()

    # --- co si stránky doplní ---
    def load(self, deep):
        """(běží na pozadí) Vrátí (zapnuto, seznam položek). deep = smí to trvat déle (nové hledání)."""
        raise NotImplementedError

    def set_power(self, on):
        """(běží na pozadí) Zapne nebo vypne rádio."""
        raise NotImplementedError

    def describe(self, item):
        """Vrátí (ikona nebo widget vlevo, podtitulek, widgety vpravo) pro řádek položky."""
        raise NotImplementedError

    def actions(self, item):
        """Vrátí seznam (text, hlavní?, funkce pro běh na pozadí) pro rozbalenou položku."""
        raise NotImplementedError

    def needs_secret(self, _item):
        return False

    def hint(self, _item):
        """Poznámka pod rozbalenou položkou (když pro ni není žádná akce)."""
        return ""

    def scanning(self):
        return self.loading and self.deep

    # --- načítání ---
    def refresh(self, deep=False):
        if self.loading:
            return
        self.loading, self.deep = True, deep
        self.render()
        self.owner.background(lambda: self.load(deep), self.loaded)

    def loaded(self, result):
        self.loading, self.loaded_once = False, True
        if isinstance(result, tuple):
            self.power, self.items = result
        if self.settle is not None and (bool(self.power) == self.switching or self.switch_error
                                        or time.monotonic() - self.settle > 4):
            self.switching = self.settle = None
        if self.expanded is not None and not any(i["key"] == self.expanded for i in self.items):
            self.collapse()
        self.render()
        self.owner.page_changed(self)

    def typing(self):
        """Píše se právě heslo? (Pak se seznam sám neobnovuje, aby se pole pod rukama neměnilo.)"""
        item = self.find(self.expanded)
        return item is not None and self.needs_secret(item)

    def find(self, key):
        return next((i for i in self.items if i["key"] == key), None)

    def collapse(self):
        self.expanded, self.message, self.failed, self.secret, self.reveal = None, "", False, "", False

    # --- kreslení seznamu ---
    def note_text(self):
        if self.power is None:
            return self.missing_text if self.loaded_once else "Loading…"
        if not self.power:
            return self.off_text
        if not self.items:
            return "Searching…" if self.scanning() else self.empty_text
        return ""

    def shown_items(self):
        return self.items if self.power else []

    def render(self):
        note = self.note_text()
        self.owner.page_changed(self)
        if note != self.note.get_text():
            self.note.set_text(note)
            self.note.set_visible(bool(note))
            self.owner.fit()
        shown = self.shown_items()
        state = (repr(shown), self.expanded, self.busy, self.message, self.failed, self.reveal)
        if state == self.drawn:
            return
        self.drawn, self.entry = state, None
        for child in self.rows.get_children():
            self.rows.remove(child)
        for item in shown:
            self.rows.pack_start(self.row(item), False, False, 0)
        self.rows.show_all()
        # seznam je vysoký podle obsahu, nejvýš NET_LIST_HEIGHT (pak se v něm posouvá); okno se mu přizpůsobí
        self.scroll.set_size_request(-1, min(self.rows.get_preferred_height()[1], NET_LIST_HEIGHT))
        self.scroll.set_visible(bool(shown))
        self.owner.fit()
        GLib.idle_add(self.reveal_open)
        if self.entry is not None:
            self.entry.grab_focus_without_selecting()
            self.entry.set_position(-1)

    def reveal_open(self):
        """Posune seznam tak, aby rozbalená položka byla celá vidět."""
        for child in self.rows.get_children():
            if child.get_style_context().has_class("open"):
                area, adjust = child.get_allocation(), self.scroll.get_vadjustment()
                if area.y + area.height > adjust.get_value() + adjust.get_page_size():
                    adjust.set_value(area.y + area.height - adjust.get_page_size())
                if area.y < adjust.get_value():
                    adjust.set_value(area.y)
        return False

    def row(self, item):
        is_open = item["key"] == self.expanded
        box = vbox(0, "net-row")
        set_class(box, "open", is_open)
        left, subtitle, right = self.describe(item)
        line = hbox(10)
        if isinstance(left, str):
            left = label(left, "net-icon")
        line.pack_start(left, False, False, 0)
        text = vbox(1)
        name = label(item["name"], "net-name", xalign=0, ellipsize=True)
        set_class(name, "active", bool(item.get("active")))
        text.pack_start(name, False, False, 0)
        if subtitle:
            text.pack_start(label(subtitle, "dim", "small", xalign=0, ellipsize=True), False, False, 0)
        text.set_valign(Gtk.Align.CENTER)
        line.pack_start(text, True, True, 0)
        for widget in right:
            line.pack_start(widget, False, False, 0)
        head = Connections.button(line, "flat", "net-item")
        head.connect("clicked", lambda _b, key=item["key"]: self.toggle(key))
        box.pack_start(head, False, False, 0)
        if is_open:
            box.pack_start(self.details(item), False, False, 0)
        return box

    def details(self, item):
        box = vbox(8, "net-details")
        working = self.busy == item["key"]
        if self.needs_secret(item):
            line = hbox(6)
            entry = self.entry = Gtk.Entry()
            css(entry, "net-entry")
            entry.set_placeholder_text("Password")
            entry.set_visibility(self.reveal)
            entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
            entry.set_text(self.secret)
            entry.set_sensitive(not working)
            entry.connect("changed", self.secret_changed)
            entry.connect("activate", lambda _e: self.primary(item))
            line.pack_start(entry, True, True, 0)
            eye = Connections.button(label(I["eye_off" if self.reveal else "eye"]), "flat", "net-btn")
            eye.connect("clicked", lambda _b: self.toggle_reveal())
            line.pack_start(eye, False, False, 0)
            box.pack_start(line, False, False, 0)
        line = hbox(6)
        for text, primary, work in self.actions(item):
            btn = Connections.button(label("Working…" if working and primary else text), "flat", "net-btn")
            set_class(btn, "primary", primary)
            btn.set_sensitive(not working)
            btn.connect("clicked", lambda _b, w=work: self.act(item, w))
            line.pack_start(btn, primary, primary, 0)
        box.pack_start(line, False, False, 0)
        message = self.message or self.hint(item)
        if message:
            note = label(message, "small", "net-error" if self.failed else "dim", xalign=0)
            note.set_line_wrap(True)
            note.set_max_width_chars(34)
            box.pack_start(note, False, False, 0)
        return box

    # --- ovládání ---
    def toggle(self, key):
        if self.busy is not None:
            return
        opened = self.expanded != key
        self.collapse()
        if opened:
            self.expanded = key
        self.render()

    def secret_changed(self, entry):
        self.secret = entry.get_text()

    def toggle_reveal(self):
        self.reveal = not self.reveal
        self.render()

    def primary(self, item):
        for _text, primary, work in self.actions(item):
            if primary:
                self.act(item, work)
                return

    def act(self, item, work):
        """Spustí akci na pozadí; work vrátí None při úspěchu, jinak text chyby."""
        if self.busy is not None:
            return
        self.busy, self.message, self.failed = item["key"], "", False
        self.render()
        self.owner.background(work, self.acted)

    def acted(self, error):
        self.busy = None
        if error:
            self.message, self.failed = str(error), True
        else:
            self.collapse()
        self.render()
        self.refresh()


class WifiPage(ConnPage):
    key, title = "wifi", "Wi-Fi"
    manager, manager_label = "nm-connection-editor", "Edit saved networks…"
    off_text = "Wi-Fi is off."
    missing_text = "NetworkManager is not responding."
    empty_text = "No networks in range."

    def __init__(self, owner):
        self.nmcli = shutil.which("nmcli") or "nmcli"
        self.names = {}          # UUID uložené sítě -> její název (SSID), ať se neptáme pořád dokola
        super().__init__(owner)

    def saved(self):
        """Uložené Wi-Fi sítě: název sítě (SSID) -> UUID profilu."""
        _ok, out, _err = tool(self.nmcli, "-t", "-f", "UUID,TYPE", "connection", "show")
        uuids = [f[0] for f in map(split_terse, out.splitlines()) if len(f) >= 2 and f[1] == "802-11-wireless"]
        for uuid in uuids:
            if uuid not in self.names:
                _ok, name, _err = tool(self.nmcli, "-g", "802-11-wireless.ssid", "connection", "show", "uuid", uuid)
                self.names[uuid] = split_terse(name.strip())[0] if name.strip() else ""
        self.names = {uuid: self.names[uuid] for uuid in uuids}
        return {name: uuid for uuid, name in self.names.items() if name}

    def load(self, deep):
        ok, out, _err = tool(self.nmcli, "-t", "-f", "WIFI", "radio")
        if not ok or not out.strip():
            return None, []
        if "enabled" not in out:
            return False, []
        saved = self.saved()
        _ok, out, _err = tool(self.nmcli, "-t", "-f", "IN-USE,SIGNAL,SECURITY,SSID", "device", "wifi", "list",
                              "--rescan", "yes" if deep else "auto", timeout=25)
        best = {}
        for fields in map(split_terse, out.splitlines()):
            if len(fields) < 4 or not fields[3]:
                continue                         # skrytá síť bez názvu
            used, signal, security, ssid = fields[0], fields[1], fields[2].strip(), fields[3]
            item = {"key": ssid, "name": ssid, "active": used.strip() == "*",
                    "signal": int(signal) if signal.isdigit() else 0,
                    "secure": security not in ("", "--"), "enterprise": "802.1X" in security,
                    "uuid": saved.get(ssid)}
            old = best.get(ssid)                  # jedna síť může mít víc vysílačů, bere se ten nejsilnější
            if old is None or (item["active"], item["signal"]) > (old["active"], old["signal"]):
                best[ssid] = item
        items = sorted(best.values(), key=lambda i: (not i["active"], -i["signal"], i["name"].casefold()))
        for item in items:                         # sílu zaokrouhlit, ať se seznam nepřekresluje kvůli každému procentu
            item["signal"] = item["signal"] // 10 * 10
        return True, items

    def set_power(self, on):
        tool(self.nmcli, "radio", "wifi", "on" if on else "off")
        if on:
            time.sleep(2.0)        # rádiu chvíli trvá, než něco najde

    def describe(self, item):
        if item["active"]:
            subtitle = "Connected"
        elif item["uuid"]:
            subtitle = "Saved"
        elif not item["secure"]:
            subtitle = "Open network"
        else:
            subtitle = ""
        right = []
        if item["secure"]:
            right.append(label(I["lock"], "net-lock"))
        if item["active"]:
            right.append(label(I["check"], "net-check"))
        return SignalBars(item["signal"]), subtitle, right

    def needs_secret(self, item):
        return item["secure"] and not item["uuid"] and not item["active"] and not item["enterprise"]

    def hint(self, item):
        if item["enterprise"] and not item["uuid"]:
            return "Enterprise network with a username and password. Set it up in \"Edit saved networks\"."
        return ""

    def actions(self, item):
        if item["active"]:
            found = [("Disconnect", True, self.disconnect)]
        elif item["enterprise"] and not item["uuid"]:
            found = []
        else:
            found = [("Connect", True, lambda: self.connect(item))]
        if item["uuid"]:
            found.append(("Forget", False, lambda: self.forget(item)))
        return found

    def connect(self, item):
        if item["uuid"]:
            ok, out, err = tool(self.nmcli, "-w", "30", "connection", "up", "uuid", item["uuid"], timeout=40)
            if not ok and "ecrets" in out + err:
                return "The saved password no longer works. Forget the network and connect again."
        else:
            secret = self.secret
            if item["secure"] and len(secret) < 8:
                return "The password needs at least 8 characters."
            cmd = [self.nmcli, "-w", "30", "device", "wifi", "connect", item["name"]]
            ok, out, err = tool(*cmd, *(["password", secret] if item["secure"] else []), timeout=40)
            if not ok:      # nepovedený pokus po sobě nechává uložený profil se špatným heslem
                uuid = self.saved().get(item["name"])
                if uuid:
                    tool(self.nmcli, "connection", "delete", "uuid", uuid)
        if ok:
            return None
        text = (err or out).strip()
        if "ecrets" in text or "psk" in text:
            return "Wrong password."
        if "No network with SSID" in text:
            return "The network is out of range."
        if text == "timeout" or "imeout" in text:
            return "Connecting took too long."
        return (text.splitlines() or ["Could not connect."])[-1].removeprefix("Error: ")

    def disconnect(self):
        _ok, out, _err = tool(self.nmcli, "-t", "-f", "DEVICE,TYPE", "device", "status")
        device = next((f[0] for f in map(split_terse, out.splitlines()) if len(f) >= 2 and f[1] == "wifi"), None)
        if device is None:
            return "No Wi-Fi device found."
        ok, out, err = tool(self.nmcli, "device", "disconnect", device)
        return None if ok else (err or out).strip().removeprefix("Error: ")

    def forget(self, item):
        ok, out, err = tool(self.nmcli, "connection", "delete", "uuid", item["uuid"])
        return None if ok else (err or out).strip().removeprefix("Error: ")


class VpnPage(ConnPage):
    """VPN přes NetworkManager (WireGuard / OpenVPN profily). Přepínač nahoře = skrýt IP adresu."""
    key, title = "vpn", "VPN"
    manager, manager_label = "nm-connection-editor", "Edit VPN connections…"
    off_text = "VPN is off. Your real IP address is visible."
    missing_text = "NetworkManager is not responding."
    empty_text = "No VPN connections. Import a WireGuard .conf file first."
    TYPES = ("wireguard", "vpn")
    IP_URL = "https://ipinfo.io/json"

    def __init__(self, owner):
        self.nmcli = shutil.which("nmcli") or "nmcli"
        self.ip, self.ip_for, self.ip_at = None, None, 0.0
        self.open_groups, self.pings, self.pinged_at = set(), {}, 0.0
        super().__init__(owner)
        # karta s veřejnou IP adresou nad seznamem
        card = hbox(12, "net-row", "vpn-card")
        self.v_icon = label(I["shield"], "vpn-icon")
        card.pack_start(self.v_icon, False, False, 0)
        self.v_spin = Gtk.Spinner()
        self.v_spin.set_size_request(22, 22)
        self.v_spin.set_margin_start(6)
        self.v_spin.set_margin_end(6)
        self.v_spin.set_no_show_all(True)
        css(self.v_spin, "vpn-spin")
        card.pack_start(self.v_spin, False, False, 0)
        text = vbox(1)
        text.set_valign(Gtk.Align.CENTER)
        self.v_state = label("Checking…", "net-name", xalign=0)
        self.v_ip = label("", "dim", "small", xalign=0, ellipsize=True)
        text.pack_start(self.v_state, False, False, 0)
        text.pack_start(self.v_ip, False, False, 0)
        card.pack_start(text, True, True, 0)
        self.v_fast = Connections.button(label("Fastest"), "flat", "net-btn", "primary")
        self.v_fast.set_valign(Gtk.Align.CENTER)
        self.v_fast.connect("clicked", lambda _b: self.connect_fastest())
        card.pack_start(self.v_fast, False, False, 0)
        card.show_all()
        self.box.pack_start(card, False, False, 0)
        self.box.reorder_child(card, 0)

    def profiles(self):
        ok, out, _err = tool(self.nmcli, "-t", "-f", "UUID,TYPE,NAME,AUTOCONNECT,ACTIVE", "connection", "show")
        if not ok:
            return None
        found = []
        for f in map(split_terse, out.splitlines()):
            if len(f) >= 5 and f[1] in self.TYPES:
                country, number = self.parse(f[2])
                found.append({"key": f[0], "uuid": f[0], "conn": f[2], "country": country, "number": number,
                              "name": f"{country} {number}".strip(), "auto": f[3] == "yes",
                              "active": f[4] == "yes"})
        return sorted(found, key=lambda i: (i["country"], int(i["number"][1:] or 0) if i["number"] else 0))

    COUNTRIES = {"nl": "Netherlands", "pl": "Poland", "ro": "Romania", "rum": "Romania", "jp": "Japan",
                 "us": "United States", "de": "Germany", "at": "Austria", "ch": "Switzerland", "ca": "Canada",
                 "mx": "Mexico", "no": "Norway", "sg": "Singapore", "uk": "United Kingdom"}

    def parse(self, name):
        """proton-nl121 -> ("Netherlands", "#121"), proton-pl -> ("Poland", ""); jiné jméno zůstane, jak je."""
        match = re.fullmatch(r"(?:[a-z]+-)?([a-z]{2,3})-?(\d*)", name.lower())
        if match and match.group(1) in self.COUNTRIES:
            return self.COUNTRIES[match.group(1)], f"#{match.group(2)}" if match.group(2) else ""
        return name, ""

    CONF_DIR = os.path.expanduser("~/.local/share/island-vpn")

    def endpoint(self, conn):
        """Adresa serveru ze záložního .conf souboru (do NetworkManageru by to chtělo heslo roota)."""
        for line in read(os.path.join(self.CONF_DIR, conn + ".conf")).splitlines():
            key, _, value = line.partition("=")
            if key.strip().lower() == "endpoint":
                return value.strip().rsplit(":", 1)[0].strip("[]")
        return None

    def measure(self, items):
        """Odezva všech serverů najednou (ping), obnovuje se jednou za minutu."""
        if time.monotonic() - self.pinged_at < 60 and all(i["uuid"] in self.pings for i in items):
            return
        results = {}

        def one(item):
            host = self.endpoint(item["conn"])
            ok, out, _err = tool("ping", "-c", "2", "-i", "0.3", "-W", "1", "-q", host, timeout=5) if host else (False, "", "")
            match = re.search(r"= [\d.]+/([\d.]+)/", out)
            results[item["uuid"]] = float(match.group(1)) if ok and match else None

        threads = [threading.Thread(target=one, args=(i,), daemon=True) for i in items]
        for t in threads:
            t.start()
        for t in threads:
            t.join(6)
        self.pings, self.pinged_at = results, time.monotonic()

    def groups(self):
        """Seznam zemí: (země, servery)."""
        found = {}
        for item in self.items:
            found.setdefault(item["country"], []).append(item)
        return list(found.items())

    def shown_items(self):
        """Řádky: hlavička země (rozbalovací), pod ní její servery, když je rozbalená."""
        rows = []
        for country, servers in self.groups():
            if len(self.items) <= 3 or len(self.groups()) == 1:
                return list(self.items)           # pár serverů = bez skupin
            active = any(s["active"] for s in servers)
            opened = country in self.open_groups
            pings = [self.pings.get(s["uuid"]) for s in servers]
            best = min((p for p in pings if p is not None), default=None)
            rows.append({"key": "grp:" + country, "header": True, "name": country, "open": opened,
                         "count": len(servers), "best": best, "active": active})
            if opened:
                rows += [dict(s, name=s["number"] or s["name"], ping=self.pings.get(s["uuid"]), child=True)
                         for s in servers]
        return rows

    def find(self, key):
        return next((i for i in self.items if i["key"] == key), None)

    def toggle(self, key):
        if key.startswith("grp:"):
            country = key[4:]
            self.open_groups.symmetric_difference_update({country})
            self.render()
            return
        super().toggle(key)

    def row(self, item):
        box = super().row(item)
        set_class(box, "vpn-child", bool(item.get("child")))
        set_class(box, "vpn-group", bool(item.get("header")))
        return box

    def fastest(self):
        candidates = [(p, i) for i in self.items if (p := self.pings.get(i["uuid"])) is not None]
        return min(candidates, key=lambda c: c[0])[1] if candidates else (self.items[0] if self.items else None)

    def connect_fastest(self):
        target = self.fastest()
        if target is not None:
            self.act(target, lambda: self.up(target))

    def public_ip(self, active):
        """Veřejná IP a země; zjišťuje se jen po změně VPN nebo jednou za 2 minuty."""
        signature = tuple(i["uuid"] for i in active)
        if signature == self.ip_for and time.monotonic() - self.ip_at < 120:
            return self.ip
        if signature != self.ip_for and active:
            time.sleep(1.0)                   # trasa přes VPN se chvíli nastavuje
        try:
            req = urllib.request.Request(self.IP_URL, headers={"User-Agent": "curl/8", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            place = ", ".join(x for x in (data.get("city"), data.get("country")) if x)
            self.ip = (data.get("ip", "?"), place)
        except Exception:
            self.ip = None
        self.ip_for, self.ip_at = signature, time.monotonic()
        return self.ip

    def load(self, deep):
        items = self.profiles()
        if items is None:
            return None, []
        if deep:
            self.ip_for = None              # tlačítko obnovit = znovu zjistit IP adresu
        active = [i for i in items if i["active"]]
        self.public_ip(active)
        self.measure(items)
        if not self.loaded_once:            # poprvé rozbalit zemi, přes kterou se právě jede
            self.open_groups |= {i["country"] for i in active}
        return bool(active), items

    def render(self):
        super().render()
        on = bool(self.power)
        set_class(self.v_icon, "on", on)
        working = self.switching is not None or self.busy is not None
        self.v_icon.set_visible(not working)
        self.v_spin.set_visible(working)
        (self.v_spin.start if working else self.v_spin.stop)()
        self.v_fast.set_visible(len(self.items) > 1 and self.busy is None and self.switching is None)
        self.v_state.set_text("Your IP is hidden" if on else ("Your IP is visible" if self.power is not None else "Checking…"))
        if self.ip:
            ip, place = self.ip
            self.v_ip.set_text(f"{ip}  ·  {place}" if place else ip)
        else:
            self.v_ip.set_text("IP address unknown (offline?)" if self.loaded_once else "")
        if working:
            going = self.find(self.busy) if self.busy is not None else (self.target() if self.switching else None)
            busy_item = self.find(self.busy)
            leaving = self.switching is False or (busy_item is not None and busy_item["active"])
            self.v_state.set_text("Disconnecting…" if leaving else "Connecting…")
            if going is not None and not leaving:
                self.v_ip.set_text(f"to {going['name']}")
        elif self.switch_error:
            self.v_state.set_text("Could not connect")
            self.v_ip.set_text(self.switch_error)

    def note_text(self):
        if self.power is not None and not self.items:
            return self.empty_text
        return "" if self.power is not None else super().note_text()


    def scanning(self):
        return False

    def target(self):
        """Ke kterému serveru se přepínač připojí: s automatickým startem, jinak s nejlepší odezvou."""
        return next((i for i in self.items if i["auto"]), None) or self.fastest()

    def set_power(self, on):
        self.ip_for = None
        if on:
            target = self.target()
            if target is None:
                return "No VPN servers imported."
            ok, out, err = tool(self.nmcli, "-w", "25", "connection", "up", "uuid", target["uuid"], timeout=35)
            if not ok:
                return ((err or out).strip().splitlines() or ["Could not connect."])[-1].removeprefix("Error: ")
        else:
            for item in self.profiles() or []:
                if item["active"]:
                    tool(self.nmcli, "connection", "down", "uuid", item["uuid"])
        return None

    def describe(self, item):
        if item.get("header"):
            sub = f"{item['count']} server{'s' if item['count'] != 1 else ''}" + (f"  ·  best {item['best']:.0f} ms" if item["best"] is not None else "")
            if item["active"]:
                sub = "Connected  ·  " + sub
            caret = label(I["caret"], "dim", "vpn-caret")
            set_class(caret, "open", item["open"])
            return I["globe"], sub, [caret]
        parts = []
        if item["active"]:
            parts.append("Connected")
        ping = item.get("ping", self.pings.get(item["uuid"]))
        if ping is not None:
            parts.append(f"{ping:.0f} ms")
        if item["auto"]:
            parts.append("starts automatically")
        right = [label(I["check"], "net-check")] if item["active"] else []
        return ("" if item.get("child") else I["globe"]), "  ·  ".join(parts), right

    def actions(self, item):
        found = [("Disconnect", True, lambda: self.down(item))] if item["active"] else \
                [("Connect", True, lambda: self.up(item))]
        found.append(("Auto-start off" if item["auto"] else "Auto-start on", False, lambda: self.auto(item)))
        return found

    def up(self, item):
        self.switch_error = ""
        for other in self.items:                  # vždy jen jedna VPN najednou
            if other["active"] and other["uuid"] != item["uuid"]:
                tool(self.nmcli, "connection", "down", "uuid", other["uuid"])
        ok, out, err = tool(self.nmcli, "-w", "20", "connection", "up", "uuid", item["uuid"], timeout=30)
        self.ip_for = None
        return None if ok else ((err or out).strip().splitlines() or ["Could not connect."])[-1].removeprefix("Error: ")

    def down(self, item):
        ok, out, err = tool(self.nmcli, "connection", "down", "uuid", item["uuid"])
        self.ip_for = None
        return None if ok else (err or out).strip().removeprefix("Error: ")

    def auto(self, item):
        """Automatický start po přihlášení; smí ho mít jen jeden profil."""
        if not item["auto"]:
            for other in self.items:
                if other["auto"]:
                    tool(self.nmcli, "connection", "modify", "uuid", other["uuid"], "connection.autoconnect", "no")
        ok, out, err = tool(self.nmcli, "connection", "modify", "uuid", item["uuid"],
                            "connection.autoconnect", "no" if item["auto"] else "yes")
        return None if ok else (err or out).strip().removeprefix("Error: ")


class BluetoothPage(ConnPage):
    key, title = "bluetooth", "Bluetooth"
    manager, manager_label = "blueman-manager", "Bluetooth manager…"
    off_text = "Bluetooth is off."
    missing_text = "No Bluetooth adapter found."
    empty_text = "No devices. Search with the button above."
    ICONS = (("headset", "headphones"), ("headphone", "headphones"), ("audio", "vol_high"), ("phone", "mobile"),
             ("keyboard", "keyboard"), ("mouse", "mouse"), ("gaming", "gamepad"), ("computer", "laptop"),
             ("video", "tv"))

    def __init__(self, owner):
        self.btctl = shutil.which("bluetoothctl") or "bluetoothctl"
        self.scan_until, self.scanner = 0.0, None
        super().__init__(owner)

    def scanning(self):
        return time.time() < self.scan_until

    def load(self, _deep):
        ok, out, _err = tool(self.btctl, "show")
        if not ok or "Powered:" not in out:
            return None, []
        if "Powered: yes" not in out:
            return False, []
        _ok, out, _err = tool(self.btctl, "devices")
        items = []
        for line in out.splitlines()[:40]:
            match = re.match(r"Device ((?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}) ?(.*)", line.strip())
            if not match:
                continue
            mac = match.group(1)
            _ok, info, _err = tool(self.btctl, "info", mac)
            props = dict(re.findall(r"^\s*([A-Za-z ]+): (.*)$", info, re.M))
            name = props.get("Alias") or props.get("Name") or match.group(2) or mac
            paired, connected = props.get("Paired") == "yes", props.get("Connected") == "yes"
            if not paired and not connected:
                # cizí zařízení ukazovat jen když jsou právě v dosahu a mají jméno
                if "RSSI" not in props or name.replace("-", ":").upper() == mac.upper():
                    continue
            battery = re.search(r"\((\d+)\)", props.get("Battery Percentage", ""))
            items.append({"key": mac, "name": name, "active": connected, "paired": paired,
                          "kind": props.get("Icon", ""), "battery": int(battery.group(1)) if battery else None})
        items.sort(key=lambda i: (not i["active"], not i["paired"], i["name"].casefold()))
        return True, items

    def loaded(self, result):
        wanted = self.deep
        super().loaded(result)
        if wanted:
            self.scan()

    def scan(self):
        """Spustí na chvíli hledání nových zařízení."""
        if self.scanning() or not self.power:
            return False
        self.scan_until = time.time() + BT_SCAN_SECONDS
        try:
            self.scanner = subprocess.Popen([self.btctl, "--timeout", str(BT_SCAN_SECONDS), "scan", "on"],
                                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                            stderr=subprocess.DEVNULL, env=TOOL_ENV)
        except OSError:
            self.scan_until = 0.0
        self.render()
        return False

    def set_power(self, on):
        tool(self.btctl, "power", "on" if on else "off")
        if on:
            time.sleep(1.0)

    def describe(self, item):
        icon = next((I[name] for part, name in self.ICONS if part in item["kind"]), I["bt"])
        parts = []
        if item["active"]:
            parts.append("Connected")
        elif item["paired"]:
            parts.append("Paired")
        else:
            parts.append("New device")
        if item["battery"] is not None:
            parts.append(f"battery {item['battery']}%")
        right = [label(I["check"], "net-check")] if item["active"] else []
        return icon, "  ·  ".join(parts), right

    def actions(self, item):
        mac = item["key"]
        if item["active"]:
            found = [("Disconnect", True, lambda: self.command("disconnect", mac, "Successful disconnected"))]
        elif item["paired"]:
            found = [("Connect", True, lambda: self.command("connect", mac, "Connection successful", 25))]
        else:
            found = [("Pair and connect", True, lambda: self.pair(mac))]
        if item["paired"]:
            found.append(("Remove", False, lambda: self.command("remove", mac, "Device has been removed")))
        return found

    def command(self, verb, mac, success, timeout=12):
        """Pošle zařízení příkaz. bluetoothctl nevrací spolehlivě chybový kód, úspěch se pozná podle textu."""
        ok, out, err = tool(self.btctl, verb, mac, timeout=timeout)
        text = out + err
        if success in text:
            return None
        if err == "timeout" or "timeout" in text.lower():
            return "The device is not responding. Is it on and in range?"
        if "not available" in text:
            return "The device is out of range."
        failed = re.search(r"Failed to \w+: (\S+)(?: (\S+))?", text)
        if failed:
            return "Failed (" + (failed.group(2) or failed.group(1).rsplit(".", 1)[-1]) + ")."
        return None if ok and verb != "connect" else "Failed."

    def pair(self, mac):
        ok, out, err = tool(self.btctl, "pair", mac, timeout=35)
        text = out + err
        if "Pairing successful" not in text and "AlreadyExists" not in text:
            if "AuthenticationFailed" in text or "AuthenticationCanceled" in text or "passkey" in text.lower():
                return "The device wants a confirmation code. Pair it in the Bluetooth manager."
            return "Pairing failed. Is the device in pairing mode?"
        tool(self.btctl, "trust", mac)
        return self.command("connect", mac, "Connection successful", 25)


class Connections(AutoHide):
    """Okno pod pravým ostrůvkem lišty se záložkami Wi-Fi a Bluetooth."""

    def __init__(self, app):
        self.app = app
        self.visible, self.close_timer, self.tick_timer = False, None, None
        self.current, self.fitted = None, 0.0
        self.win = layer_window(app, "island-net")
        if GtkLayerShell.is_supported():
            GtkLayerShell.set_anchor(self.win, GtkLayerShell.Edge.RIGHT, True)
            GtkLayerShell.set_exclusive_zone(self.win, 0)          # pod lištou, ne přes ni
            GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.TOP, NET_TOP_MARGIN)
            GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.RIGHT, NET_RIGHT_MARGIN)
            # klávesnice jen po kliknutí do okna (heslo k Wi-Fi), ostatní okna a lišta zůstávají použitelné
            GtkLayerShell.set_keyboard_mode(self.win, GtkLayerShell.KeyboardMode.ON_DEMAND)
        self.watch_pointer()
        self.win.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.win.connect("key-press-event", self.on_key)
        self.shown_at, self.away_timer = 0.0, None
        app.hypr_events.connect(self.on_hypr_event)

        root = self.root = vbox(10)
        root.set_name("net")
        root.set_size_request(NET_WIDTH, -1)
        self.reveal = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN,
                                   transition_duration=MORPH_MS)
        self.reveal.add(root)
        self.reveal.show()
        self.hide_timer = None
        self.win.add(self.reveal)
        head = hbox(4)
        self.pages, self.tabs = {}, {}
        for page in (WifiPage(self), BluetoothPage(self), VpnPage(self)):
            self.pages[page.key] = page
            tab = self.button(label(page.title), "flat", "wall-chip")
            tab.connect("clicked", lambda _b, key=page.key: self.select(key))
            head.pack_start(tab, False, False, 0)
            self.tabs[page.key] = tab
        self.switch = Gtk.Switch()
        self.switch.set_can_focus(False)
        self.switch.set_valign(Gtk.Align.CENTER)
        css(self.switch, "net-switch")
        self.switch_handler = self.switch.connect("state-set", self.on_switch)
        head.pack_end(self.switch, False, False, 0)
        self.scan_btn = self.button(label(I["refresh"]), "flat", "wall-icon")
        self.scan_btn.connect("clicked", lambda _b: self.page().refresh(deep=True))
        head.pack_end(self.scan_btn, False, False, 4)
        root.pack_start(head, False, False, 0)
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(180)
        self.stack.set_vhomogeneous(False)
        self.stack.set_interpolate_size(True)
        for key, page in self.pages.items():
            self.stack.add_named(page.box, key)
        root.pack_start(self.stack, False, False, 0)
        root.show_all()
        self.select("wifi")

    @staticmethod
    def button(child, *classes):
        btn = Gtk.Button()
        btn.add(child)
        btn.set_can_focus(False)
        return css(btn, *classes)

    @staticmethod
    def background(work, done=None):
        """Spustí work ve vedlejším vlákně a jeho výsledek předá funkci done zpátky v hlavním vlákně."""
        def runner():
            try:
                result = work()
            except Exception as err:      # chyba nesmí shodit panel, jen se ukáže
                result = f"Chyba: {err}"
            if done is not None:
                GLib.idle_add(lambda: done(result) and False)
        threading.Thread(target=runner, daemon=True).start()

    def page(self):
        return self.pages[self.current]

    def fit(self):
        """Smrskne okno na velikost obsahu (samo od sebe by umělo jen růst)."""
        self.fitted = time.monotonic()
        self.win.resize(1, 1)

    def select(self, key):
        if key != self.current and self.current is not None:
            self.page().collapse()
            self.page().render()
        self.current = key
        for name, tab in self.tabs.items():
            set_class(tab, "active", name == key)
        self.stack.set_visible_child_name(key)
        self.page_changed(self.page())
        # okno se zmenší až po prolnutí, jinak by se animace useknula
        GLib.timeout_add(self.stack.get_transition_duration() + 20, lambda: self.fit() and False)
        if self.visible:
            GLib.timeout_add(self.stack.get_transition_duration() + 20,
                             lambda: self.page().refresh(deep=True) and False)

    def page_changed(self, page):
        """Stránka má nová data: srovnat přepínač nahoře."""
        if page is not self.page():
            return
        self.switch.handler_block(self.switch_handler)
        self.switch.set_sensitive(page.power is not None and page.switching is None)
        self.switch.set_state(bool(page.power) if page.switching is None else page.switching)
        self.switch.handler_unblock(self.switch_handler)
        self.scan_btn.set_sensitive(bool(page.power) and not page.scanning())
        set_class(self.scan_btn, "busy", page.scanning())     # probíhající hledání je vidět na tlačítku

    def on_switch(self, _switch, state):
        page = self.page()
        page.switching, page.switch_error = state, ""
        self.page_changed(page)
        page.render()

        def done(error):
            # přepínač drží cílový stav, dokud nové načtení nepotvrdí skutečný stav (žádné poskakování)
            page.switch_error = error if isinstance(error, str) else ""
            page.settle = time.monotonic()
            page.loading = False
            page.refresh(deep=state)
        self.background(lambda: page.set_power(state), done)
        return True

    def on_key(self, _win, event):
        if event.keyval == Gdk.KEY_Escape:
            if self.page().expanded is not None and self.page().busy is None:
                self.page().collapse()
                self.page().render()
            else:
                self.hide()
            return True
        return False

    def tick(self):
        page = self.page()
        if page.busy is None and (page.switching is None or page.settle is not None) and not page.typing():
            page.refresh()
        page.render()
        return True

    def close_if_outside(self):
        """Samo se zavře po odjetí kurzoru, ale ne uprostřed práce nebo psaní hesla."""
        self.close_timer = None
        page = self.page()
        if page.busy is not None or (page.typing() and page.secret):
            return False
        if time.monotonic() - self.fitted < 0.8:
            return False      # kurzor neodjel, to se jen okno pod ním zmenšilo (ubyla položka apod.)
        if page.switching is not None:
            return False      # právě se zapíná / vypíná
        if not self.hovering and not self.pointer_inside():
            self.hide()
        return False

    def show(self, key=None, origin=None):
        if screen_locked():
            return
        self.cancel_close()
        if key:
            self.select(key)
        if self.visible:
            return
        self.visible = True
        self.shown_at = time.monotonic()
        if self.hide_timer is not None:
            GLib.source_remove(self.hide_timer)
            self.hide_timer = None
        width = self.attach_to_bar("right", NET_WIDTH, origin)
        attached = self.attach is not None
        set_class(self.root, "attached", attached)
        self.root.set_size_request(width, -1)
        if GtkLayerShell.is_supported():
            GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.TOP,
                                     self.attach[0].island_bottom() if attached else NET_TOP_MARGIN)
            GtkLayerShell.set_margin(self.win, GtkLayerShell.Edge.RIGHT, BAR_MARGIN if attached else NET_RIGHT_MARGIN)
            # napojené okno se měří od horního okraje obrazovky, jinak se řadí pod lištu
            GtkLayerShell.set_exclusive_zone(self.win, -1 if attached else 0)
        self.win.set_size_request(-1, 1)          # prázdné (zasunuté) okno nesmí mít nulovou výšku
        self.win.show()
        GLib.idle_add(lambda: self.visible and self.reveal.set_reveal_child(True) and False)
        if self.away_timer is None:
            self.away_timer = GLib.timeout_add(250, self.check_away)
        self.page().refresh(deep=True)
        for other in self.pages.values():       # ostatní záložky načíst předem, ať se při přepnutí neskáče
            if other is not self.page():
                other.refresh()
        if self.tick_timer is None:
            self.tick_timer = GLib.timeout_add_seconds(3, self.tick)

    def hide(self):
        self.cancel_close()
        if not self.visible:
            return
        self.visible = False
        if self.tick_timer is not None:
            GLib.source_remove(self.tick_timer)
            self.tick_timer = None
        if self.away_timer is not None:
            GLib.source_remove(self.away_timer)
            self.away_timer = None
        self.reveal.set_reveal_child(False)
        self.detach_from_bar()
        if self.hide_timer is None:
            self.hide_timer = GLib.timeout_add(MORPH_MS + 30, self.finish_hide)

    def finish_hide(self):
        self.hide_timer = None
        if self.visible:
            return False
        self.win.hide()
        self.fit()
        for page in self.pages.values():
            if page.busy is None:
                page.collapse()
                page.render()
        return False

    def on_hypr_event(self, name, data):
        """Kliknutí na jiné okno nebo přepnutí plochy okno zavře (i během psaní hesla)."""
        if not self.visible or time.monotonic() - self.shown_at < 0.4:
            return
        if name == "activewindowv2" and data.strip(", ") or name in ("workspace", "focusedmon"):
            self.hide()

    def check_away(self):
        """Kurzor odjel z lišty i z okna (třeba na jiné okno), aniž by do okna vůbec vjel -> zavřít."""
        if not self.visible:
            self.away_timer = None
            return False
        if self.hovering or self.pointer_inside() or self.close_timer is not None:
            return True
        pos, monitors = hypr_json("cursorpos"), hypr_json("monitors")
        if not pos or not monitors:
            return True
        x, y = pos.get("x", 0), pos.get("y", 0)
        for m in monitors:
            scale = m.get("scale") or 1
            w, h = m["width"] / scale, m["height"] / scale
            if m.get("transform", 0) % 2:
                w, h = h, w
            if m["x"] <= x < m["x"] + w and m["y"] <= y < m["y"] + h:
                if y - m["y"] > BAR_ZONE:             # pod lištou a mimo okno
                    self.close_if_outside()
                break
        return True

    def toggle(self, key, origin=None):
        if self.visible and self.current == key:
            self.hide()
        else:
            self.show(key, origin)


# ----------------------------------------------------------------------------
# Lišta nahoře (místo Waybaru): tři ostrůvky; prostřední a pravý umí narůst a vysunout z nich okno.
# Vzhled i obsah je stejný jako u dřívějšího Waybaru (barvy a písmo v style.css, sekce "Lišta nahoře").
# ----------------------------------------------------------------------------
def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def island_path(cr, x, y, w, h, top, bottom):
    """Obdélník se zaoblením nahoře (top) a dole (bottom)."""
    top, bottom = max(0.0, min(top, h / 2, w / 2)), max(0.0, min(bottom, h / 2, w / 2))
    cr.new_sub_path()
    cr.arc(x + w - top, y + top, top, -math.pi / 2, 0)
    cr.arc(x + w - bottom, y + h - bottom, bottom, 0, math.pi / 2)
    cr.arc(x + bottom, y + h - bottom, bottom, math.pi / 2, math.pi)
    cr.arc(x + top, y + top, top, math.pi, 3 * math.pi / 2)
    cr.close_path()


def open_outline(cr, x, y, w, h, top, bottom, open_top=False, open_bottom=False):
    """Okraj obdélníku, u kterého může chybět horní nebo spodní hrana (tam navazuje druhá část)."""
    top, bottom = max(0.0, min(top, h / 2, w / 2)), max(0.0, min(bottom, h / 2, w / 2))
    if open_top:                                   # dolní část: levá hrana, spodek, pravá hrana
        cr.move_to(x, y)
        cr.arc_negative(x + bottom, y + h - bottom, bottom, math.pi, math.pi / 2)
        cr.arc_negative(x + w - bottom, y + h - bottom, bottom, math.pi / 2, 0)
        cr.line_to(x + w, y)
    elif open_bottom:                              # horní část: levá hrana, vršek, pravá hrana
        cr.move_to(x, y + h)
        cr.arc(x + top, y + top, top, math.pi, 3 * math.pi / 2)
        cr.arc(x + w - top, y + top, top, -math.pi / 2, 0)
        cr.line_to(x + w, y + h)
    else:
        island_path(cr, x, y, w, h, top, bottom)


def mix_rgba(a, b, p):
    return tuple(a[i] + (b[i] - a[i]) * p for i in range(4))


def rgba_tuple(ctx, name, fallback):
    ok, color = ctx.lookup_color(name)
    return (color.red, color.green, color.blue, color.alpha) if ok else fallback


class BarWindow:
    """Lišta na jednom monitoru."""
    KEYS = ("left", "center", "right")

    def __init__(self, bar, monitor):
        self.bar, self.monitor = bar, monitor
        self.anim = {k: {"p": 0.0, "from": 0.0, "to": 0.0, "start": 0.0, "width": 0} for k in self.KEYS}
        self.tick_id, self.hover_zone, self.open_timer, self.poll_id = None, None, None, None
        self.exclusive = 0
        self.collide, self.misses = {}, 0
        win = self.win = Gtk.Window(application=bar.app)
        win.set_decorated(False)
        win.set_app_paintable(True)
        visual = win.get_screen().get_rgba_visual()
        if visual:
            win.set_visual(visual)
        if GtkLayerShell.is_supported():
            GtkLayerShell.init_for_window(win)
            GtkLayerShell.set_namespace(win, "island-bar")
            GtkLayerShell.set_layer(win, GtkLayerShell.Layer.TOP)
            for edge in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT):
                GtkLayerShell.set_anchor(win, edge, True)
            GtkLayerShell.set_monitor(win, monitor)
        # kde je kurzor, se zjišťuje průběžně, dokud je nad lištou (tlačítka by pohyb myši spolkla)
        win.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK)
        win.connect("enter-notify-event", self.on_enter)

        # ostrůvky (pozadí) kreslí samo okno, moduly se nakreslí přes ně
        self.area = win
        win.get_style_context().add_class("bar-bg")
        win.connect("draw", self.on_draw)
        column = vbox(0)
        column.set_valign(Gtk.Align.START)
        spacer = Gtk.Box()
        spacer.set_size_request(-1, BAR_GAP)
        column.pack_start(spacer, False, False, 0)
        row = Gtk.Box()
        column.pack_start(row, False, False, 0)
        bottom = Gtk.Box()
        bottom.set_size_request(-1, BAR_BOTTOM)
        column.pack_start(bottom, False, False, 0)
        self.boxes, self.inner = {}, {}
        for key in self.KEYS:
            box = hbox(0, "bar-island", f"bar-{key}")
            inner = hbox(0)
            inner.set_valign(Gtk.Align.CENTER)
            # odsazení jako padding: 3px 5px u Waybaru (+1 px okraj)
            inner.set_margin_start(6)
            inner.set_margin_end(6)
            inner.set_margin_top(4)
            inner.set_margin_bottom(4)
            box.pack_start(inner, True, True, 0)
            self.boxes[key], self.inner[key] = box, inner
        self.boxes["left"].set_margin_start(BAR_MARGIN)
        self.boxes["right"].set_margin_end(BAR_MARGIN)
        row.pack_start(self.boxes["left"], False, False, 0)
        row.set_center_widget(self.boxes["center"])
        row.pack_end(self.boxes["right"], False, False, 0)
        win.add(column)
        self.mods = {}
        bar.build_modules(self)
        win.connect("size-allocate", lambda *_: self.on_allocate())
        column.show_all()
        bar.apply(self)
        win.show()

    def on_allocate(self):
        """Lišta zabírá oknům místo jako Waybar: mezera nahoře + ostrůvek + 2 px."""
        need = self.island_bottom() + BAR_BOTTOM
        if need != self.exclusive and GtkLayerShell.is_supported():
            self.exclusive = need
            GtkLayerShell.set_exclusive_zone(self.win, need)
        self.update_input()

    def island_bottom(self):
        a = self.boxes["center"].get_allocation()
        return a.y + a.height if a.height > 1 else BAR_GAP + 33

    # ------------------------------------------------------------ tvar
    def rect(self, key):
        """Kde je ostrůvek právě nakreslený (i s narůstáním): x, y, šířka, výška."""
        a = self.boxes[key].get_allocation()
        x, w = a.x, a.width
        st = self.anim[key]
        p = st["p"]
        if p > 0 and st["width"] > w:
            nw = w + (st["width"] - w) * p
            x = x + (w - nw) / 2 if key == "center" else x + w - nw if key == "right" else x
            w = nw
        return x, a.y, w, a.height

    def progress(self, key):
        return self.anim[key]["p"]

    def fade(self, key):
        """Jak moc je boční ostrůvek schovaný: na užším monitoru by do něj rozšířený střed narazil,
        tak se po dobu otevření přehledu rozplyne (na širokém monitoru se nic neděje)."""
        center = self.anim["center"]
        if key == "center" or center["p"] <= 0:
            return 0.0
        return center["p"] if self.collide.get(key) else 0.0

    def check_collisions(self):
        """Které boční ostrůvky by rozšířený střed zasáhl. Zjistí se jednou při otevření a platí,
        dokud přehled nezajede (jinak by ostrůvek blikal, když se mu mění šířka textu)."""
        center = self.anim["center"]
        c = self.boxes["center"].get_allocation()
        # pravý ostrůvek mění šířku (rychlost sítě), proto se řídí levým: schová se levý = schová se i pravý
        hide = self.collides("left", c, center)
        self.collide["left"] = self.collide["right"] = hide

    def collides(self, key, c, center):
        width = max(center["width"], c.width)
        left_edge = c.x + c.width / 2 - width / 2
        a = self.boxes[key].get_allocation()
        if key == "left":
            return a.x + a.width + BAR_FADE_GAP > left_edge
        return a.x < left_edge + width + BAR_FADE_GAP

    def natural_width(self, key):
        return self.boxes[key].get_allocation().width

    def on_draw(self, area, cr):
        ctx = area.get_style_context()
        bar_bg = rgba_tuple(ctx, "bar_island", (0.04, 0.12, 0.17, 0.80))
        open_bg = rgba_tuple(ctx, "island", (0.04, 0.12, 0.17, 0.93))
        line = rgba_tuple(ctx, "island_border", (0.49, 0.75, 0.86, 0.25))
        for key in self.KEYS:
            x, y, w, h = self.rect(key)
            fade = self.fade(key)
            if w <= 1 or fade >= 1:
                continue
            p = self.progress(key)
            bottom = BAR_RADIUS * (1 - p)
            # schovávaný ostrůvek zároveň vyjede nahoru za okraj obrazovky; rozmazání pod ním
            # (blur v Hyprlandu) se drží jeho tvaru, takže zmizí s ním a nezůstane po něm skvrna
            y -= fade * (y + h + 2)
            island_path(cr, x, y, w, h, BAR_RADIUS, bottom)
            # při otevírání ostrůvek plynule přejde do barvy vysunutého okna, ať spolu splynou
            r, g, b, alpha = mix_rgba(bar_bg, open_bg, p)
            cr.set_source_rgba(r, g, b, alpha * (1 - fade))
            cr.fill()
            open_outline(cr, x + 0.5, y + 0.5, w - 1, h - 0.5, BAR_RADIUS - 0.5, max(0, bottom - 0.5),
                         open_bottom=p > 0.02)
            cr.set_source_rgba(line[0], line[1], line[2], line[3] * (1 - fade))
            cr.set_line_width(1)
            cr.stroke()
        return False

    def update_input(self):
        gdk_win = self.win.get_window()
        if gdk_win is None:
            return
        region = cairo.Region()
        for key in self.KEYS:
            x, y, w, h = self.rect(key)
            if w > 1 and self.fade(key) < 0.5:
                # i pruh nad ostrůvkem až k hornímu okraji obrazovky (kurzor dotlačený nahoru)
                region.union(cairo.RectangleInt(int(x), 0, int(math.ceil(w)), int(y + h)))
        sx, sw = self.trigger_strip()
        region.union(cairo.RectangleInt(int(sx), 0, int(sw), BAR_GAP))
        gdk_win.input_shape_combine_region(region, 0, 0)

    # ------------------------------------------------------------ narůstání
    def open(self, key, width):
        self.anim[key]["width"] = width
        if key == "center" and self.anim["center"]["p"] <= 0:
            self.check_collisions()
        self.animate(key, 1.0)

    def close(self, key):
        self.animate(key, 0.0)

    def animate(self, key, target):
        st = self.anim[key]
        st["from"], st["to"], st["start"] = st["p"], target, GLib.get_monotonic_time() / 1e6
        if self.tick_id is None:
            # krok animace v rytmu obnovování displeje (90 Hz, 144 Hz…), ne podle vlastního časovače
            self.tick_id = self.win.add_tick_callback(self.on_tick)

    def on_tick(self, _widget, clock):
        busy = self.step(clock.get_frame_time() / 1e6)
        if not busy:
            self.tick_id = None
        return busy

    def step(self, now):
        busy = False
        for st in self.anim.values():
            if st["p"] == st["to"]:
                continue
            t = (now - st["start"]) / (MORPH_MS / 1000)
            # stejné zpomalení na konci při otevírání i zavírání (jako vysouvání okna)
            st["p"] = st["to"] if t >= 1 else st["from"] + (st["to"] - st["from"]) * ease_out(t)
            busy = busy or st["p"] != st["to"]
        self.area.queue_draw()
        self.update_input()
        for key in ("left", "right"):
            self.boxes[key].set_opacity(max(0.0, 1 - 2 * self.fade(key)))   # text zmizí v první polovině
        for popout in self.bar.popouts():          # okno pod ostrůvkem se překreslí se stejnou šířkou
            if popout.attach and popout.attach[0] is self:
                popout.morph_tick()
        return busy

    # ------------------------------------------------------------ kurzor
    def trigger_strip(self):
        """Pruh u horního okraje nad časem, po najetí do něj vyjede přehled (jako dřív bez lišty)."""
        x, _y, w, _h = self.rect("center")
        mid, half = x + w / 2, max(w, TRIGGER_WIDTH) / 2
        return mid - half, 2 * half

    def zone_at(self, x, y):
        for key in ("center", "left", "right"):
            if self.fade(key) >= 0.5:
                continue
            rx, ry, rw, rh = self.rect(key)
            if rx <= x < rx + rw and y < ry + rh:
                return key
        sx, sw = self.trigger_strip()
        if y < BAR_GAP and sx <= x < sx + sw:
            return "center"
        return None

    def pointer_in(self, key):
        gdk_win = self.win.get_window()
        if gdk_win is None:
            return False
        pointer = gdk_win.get_display().get_default_seat().get_pointer()
        under = pointer.get_window_at_position()[0] if pointer else None
        if under is not None and under.get_toplevel() == gdk_win:
            _w, x, y, _m = gdk_win.get_device_position(pointer)
            return self.zone_at(x, y) == key
        # GTK o kurzoru chvíli neví (Hyprland přeskládal okna): zeptat se přímo Hyprlandu
        pos = hypr_json("cursorpos")
        if not pos:
            return False
        g = self.monitor.get_geometry()
        x, y = pos.get("x", -1) - g.x, pos.get("y", -1) - g.y
        return 0 <= x < g.width and 0 <= y < self.island_bottom() and self.zone_at(x, y) == key

    def on_enter(self, *_):
        if self.poll_id is None:
            self.poll_id = GLib.timeout_add(50, self.poll)
        return False

    def poll(self):
        gdk_win = self.win.get_window()
        pointer = gdk_win.get_display().get_default_seat().get_pointer() if gdk_win else None
        under = pointer.get_window_at_position()[0] if pointer else None
        if under is None or under.get_toplevel() != gdk_win:
            # krátké "odjetí", když Hyprland přeskládá okna, nebrat vážně: až po 4 kontrolách
            self.misses += 1
            if self.misses < 4:
                return True
            self.misses = 0
            self.set_zone(None)
            self.poll_id = None
            return False
        self.misses = 0
        _w, x, y, _m = gdk_win.get_device_position(pointer)
        self.set_zone(self.zone_at(x, y))
        return True

    def set_zone(self, zone):
        if zone == self.hover_zone:
            return
        old, self.hover_zone = self.hover_zone, zone
        if self.open_timer is not None:
            GLib.source_remove(self.open_timer)
            self.open_timer = None
        if zone == "center" and not self.bar.app.panel.visible:
            self.open_timer = GLib.timeout_add(OPEN_DELAY_MS, self.open_dashboard)
        if old is not None:
            for popout in self.bar.popouts():
                if popout.visible and popout.attach == (self, old):
                    popout.schedule_close()

    def open_dashboard(self):
        self.open_timer = None
        if self.hover_zone == "center":
            self.bar.app.panel.show(origin=self)
        return False


class Bar:
    """Lišta na všech monitorech + data pro moduly (stejné jako dřív ve Waybaru)."""
    TEMP_PATH = "/sys/class/hwmon/hwmon8/temp1_input"     # čidlo, které používal Waybar

    def __init__(self, app):
        self.app = app
        self.windows = []
        self.gpu = Gpu()
        self.gpu.sample()
        self.state = {"net": None, "vpn": [], "bt": None}
        self.ap_path, self.ap_strength = None, None      # připojená Wi-Fi síť a její síla (od NetworkManageru)
        self.busy = False
        self.net_last, self.net_rate = None, (0.0, 0.0)
        self.temp_path = self.TEMP_PATH if os.path.exists(self.TEMP_PATH) else find_temp_sensor()
        display = Gdk.Display.get_default()
        display.connect("monitor-added", lambda *_: GLib.timeout_add(500, self.rebuild))
        display.connect("monitor-removed", lambda *_: GLib.timeout_add(500, self.rebuild))
        self.rebuild()
        self.slow_refresh()
        GLib.timeout_add_seconds(2, self.refresh)
        # síť, VPN a Bluetooth: místo dotazování každé 3 s se čeká na zprávy od NetworkManageru a BlueZ;
        # pro jistotu se jednou za minutu stav zjistí i tak
        self.pending = None
        self.watch_dbus()
        GLib.timeout_add_seconds(60, self.slow_refresh)

    def watch_dbus(self):
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        except GLib.Error:
            return
        self.system_bus = bus
        for sender in ("org.freedesktop.NetworkManager", "org.bluez"):
            bus.signal_subscribe(sender, "org.freedesktop.DBus.Properties", "PropertiesChanged", None, None,
                                 Gio.DBusSignalFlags.NONE, self.on_dbus_signal)
        bus.signal_subscribe("org.bluez", "org.freedesktop.DBus.ObjectManager", None, None, None,
                             Gio.DBusSignalFlags.NONE, self.on_dbus_signal)
        bus.signal_subscribe("org.freedesktop.NetworkManager", "org.freedesktop.NetworkManager", "StateChanged",
                             None, None, Gio.DBusSignalFlags.NONE, self.on_dbus_signal)

    def on_dbus_signal(self, _bus, _sender, path, _iface, member, params):
        if member == "PropertiesChanged":
            iface, changed = (params.unpack()[:2] if params else ("", {}))
            if iface.endswith(".AccessPoint"):
                # síla signálu: jen u připojené sítě, bez dalšího dotazování
                if path == self.ap_path and "Strength" in changed:
                    self.ap_strength = int(changed["Strength"])
                    self.refresh()
                return
            if iface.endswith((".Statistics", ".Device.Wireless")):
                return
        if self.pending is None:                  # víc zpráv najednou = jeden dotaz
            self.pending = GLib.timeout_add(400, self.on_pending)

    def on_pending(self):
        self.pending = None
        self.slow_refresh()
        return False

    def popouts(self):
        return [p for p in (self.app.panel, self.app.net) if p is not None]

    def rebuild(self):
        display = Gdk.Display.get_default()
        monitors = [display.get_monitor(i) for i in range(display.get_n_monitors())]
        keep = []
        for bw in self.windows:
            if bw.monitor in monitors:
                keep.append(bw)
            else:
                bw.win.destroy()
        known = [bw.monitor for bw in keep]
        for monitor in monitors:
            if monitor not in known:
                keep.append(BarWindow(self, monitor))
        self.windows = keep
        return False

    def window_for(self, origin=None):
        if origin in self.windows:
            return origin
        mons = hypr_json("monitors") or []
        focused = next((m for m in mons if m.get("focused")), None)
        if focused:
            for bw in self.windows:
                g = bw.monitor.get_geometry()
                if (g.x, g.y) == (focused.get("x"), focused.get("y")):
                    return bw
        return self.windows[0] if self.windows else None

    def attach(self, popout, key, width, origin=None):
        """Napojí okno na ostrůvek: okno se přesune na správný monitor, ostrůvek naroste na jeho šířku."""
        bw = self.window_for(origin)
        if bw is None:
            return None
        if GtkLayerShell.is_supported():
            if popout.attach and popout.attach[0] is not bw and popout.win.get_visible():
                popout.win.hide()                           # jiný monitor: okno se musí znovu zobrazit
            GtkLayerShell.set_monitor(popout.win, bw.monitor)
        width = max(width, bw.natural_width(key))
        bw.open(key, width)
        return bw, key, width

    # ------------------------------------------------------------ moduly
    def mod(self, bw, island, name, click=None, *classes):
        btn = css(Gtk.Button(), "flat", "bar-mod", f"bar-{name}", *classes)
        btn.set_can_focus(False)
        lab = label("", "bar-text")
        btn.add(lab)
        if click:
            btn.connect("clicked", lambda *_: click(bw))
        bw.mods[name] = (btn, lab)
        island.pack_start(btn, False, False, 0)
        return btn

    def build_modules(self, bw):
        left, center, right = bw.inner["left"], bw.inner["center"], bw.inner["right"]
        monitor = lambda _o: spawn("gnome-system-monitor")
        net = lambda key: (lambda origin: self.app.net and self.app.net.toggle(key, origin=origin))
        self.mod(bw, left, "cpu", monitor)
        self.mod(bw, left, "ram", monitor)
        self.mod(bw, left, "gpu", monitor)
        self.mod(bw, left, "temp", None, "bar-plain")
        self.mod(bw, left, "battery", None, "bar-plain")
        self.mod(bw, center, "clock", lambda origin: self.app.panel.toggle(origin=origin))
        self.mod(bw, right, "net", net("wifi"))
        self.mod(bw, right, "disk", lambda _o: self.open_files())
        self.mod(bw, right, "bt", net("bluetooth"))
        self.mod(bw, right, "vpn", net("vpn"))
        self.mod(bw, right, "power", lambda _o: spawn(os.path.expanduser("~/.config/rofi/powermenu/type-1/powermenu.sh")))

    @staticmethod
    def open_files():
        """Správce souborů v domovské složce (Thunar, jinak Dolphin, jinak výchozí)."""
        for cmd in ("thunar", "dolphin", "nautilus"):
            if shutil.which(cmd):
                spawn(cmd, os.path.expanduser("~"))
                return
        spawn("xdg-open", os.path.expanduser("~"))

    # ------------------------------------------------------------ data
    @staticmethod
    def vpn_name(name):
        """proton-nl -> Proton · Netherlands (stejně jako dřív ve Waybaru)."""
        provider, _, code = name.rpartition("-")
        country = VpnPage.COUNTRIES.get(code.lower())
        return f"{provider.capitalize()} · {country}" if provider and country else name

    @staticmethod
    def active_ap(dev):
        """Připojená Wi-Fi síť přes D-Bus NetworkManageru: (cesta, síla 0–100). Funguje u všech ovladačů,
        /proc/net/wireless u některých (třeba novějších Intel karet) zůstává prázdný."""
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
            nm = "org.freedesktop.NetworkManager"
            device = bus.call_sync(nm, "/org/freedesktop/NetworkManager", nm, "GetDeviceByIpIface",
                                   GLib.Variant("(s)", (dev,)), GLib.VariantType("(o)"),
                                   Gio.DBusCallFlags.NONE, 1500, None).unpack()[0]
            ap = bus.call_sync(nm, device, "org.freedesktop.DBus.Properties", "Get",
                               GLib.Variant("(ss)", (nm + ".Device.Wireless", "ActiveAccessPoint")),
                               GLib.VariantType("(v)"), Gio.DBusCallFlags.NONE, 1500, None).unpack()[0]
            if not ap or ap == "/":
                return None, None
            strength = bus.call_sync(nm, ap, "org.freedesktop.DBus.Properties", "Get",
                                     GLib.Variant("(ss)", (nm + ".AccessPoint", "Strength")),
                                     GLib.VariantType("(v)"), Gio.DBusCallFlags.NONE, 1500, None).unpack()[0]
            return ap, int(strength)
        except (GLib.Error, TypeError, ValueError):
            return None, None

    @staticmethod
    def wifi_strength(dev):
        """Síla Wi-Fi rovnou z jádra (/proc/net/wireless), levné čtení bez spouštění programů."""
        for line in read("/proc/net/wireless").splitlines()[2:]:
            name, _, rest = line.partition(":")
            if name.strip() == dev:
                try:
                    return min(100, round(float(rest.split()[1].rstrip(".")) * 100 / 70))
                except (IndexError, ValueError):
                    return 0
        return 0

    @staticmethod
    def rate(value):
        for unit in ("B/s", "kB/s", "MB/s", "GB/s"):
            if value < 999.5 or unit == "GB/s":
                return f"{value:.1f} {unit}" if value < 10 and unit != "B/s" else f"{value:.0f} {unit}"
            value /= 1000

    def net_speed(self):
        down = up = 0
        for line in read("/proc/net/dev").splitlines()[2:]:
            name, _, data = line.partition(":")
            if name.strip().startswith(NetStats.SKIP):
                continue
            fields = data.split()
            if len(fields) > 8:
                down += int(fields[0])
                up += int(fields[8])
        now = time.monotonic()
        if self.net_last:
            span = max(0.001, now - self.net_last[0])
            self.net_rate = ((down - self.net_last[1]) / span, (up - self.net_last[2]) / span)
        self.net_last = (now, down, up)
        return self.net_rate

    def values(self):
        stats = self.app.panel.stats
        out = {}
        out["cpu"] = (f"{stats.cpu:.0f}% CPU", f"CPU usage: {stats.cpu:.0f}%\nCores: {os.cpu_count()}", None)
        used, total, pct = stats.ram()
        out["ram"] = (f"{pct:.0f}% RAM", f"RAM in use: {used:.1f}GiB / {total:.1f}GiB ({pct:.0f}%)", None)
        self.gpu.sample()
        g = self.gpu.usage
        out["gpu"] = (f"{g:.0f}% GPU" if g is not None else "–% GPU",
                      f"{self.gpu.name}\nGPU usage: {g:.0f}%" if g is not None else self.gpu.name,
                      None if g is None else "critical" if g >= 90 else "warning" if g >= 70 else "normal")
        try:
            t = int(read(self.temp_path)) / 1000 if self.temp_path else None
        except ValueError:
            t = None
        out["temp"] = (f"{t:.0f}°C " if t is not None else "", f"CPU temperature: {t:.0f}°C"
                       if t is not None else "", "critical" if t and t >= 90 else "warning" if t and t >= 75 else None)
        bat = stats.battery()
        if bat:
            cap, status = bat
            if status == "Charging":
                text, cls = f"{cap}% ", "charging"
            elif status == "Not charging":
                text, cls = f"{cap}% ", "plugged"
            else:
                icons = ["", "", "", "", ""]
                text = f"{cap}% {icons[min(4, cap * 5 // 100)]}"
                cls = "critical" if cap <= 15 else "warning" if cap <= 30 else None
            out["battery"] = (text, f"Battery: {cap}%", cls)
        else:
            out["battery"] = ("", "", None)
        out["clock"] = (time.strftime(BAR_CLOCK), None, None)
        net = self.state["net"]
        if net is None or net[0] == "wifi":
            strength = self.ap_strength if self.ap_strength is not None else \
                (self.wifi_strength(net[3]) if net else 0)
            name = net[1] if net else ""
            out["net"] = (f"{strength}% ", f" {name} ({strength}%)", None)
        elif net[0] == "ethernet":
            out["net"] = (f"{net[1]} \U000f0200", f"{net[1]}", None)
        else:
            out["net"] = (" Disconnected", "Disconnected", "disconnected")
        vpn = self.state["vpn"]
        out["vpn"] = ("", f"VPN on: {vpn[0]}\nYour IP is hidden" if vpn else "VPN off\nYour IP is visible",
                      "on" if vpn else "off")
        bt = self.state["bt"]
        if bt is None or not bt[0]:
            out["bt"] = ("", "Bluetooth off", "off")
        elif bt[1]:
            out["bt"] = ("", " " + ", ".join(bt[1]), "connected")
        else:
            out["bt"] = ("", "Bluetooth on", None)
        try:
            st = os.statvfs("/")
            free, size = st.f_bavail * st.f_frsize, st.f_blocks * st.f_frsize
            out["disk"] = ("", f"Free space: {free / 2 ** 30:.1f}GiB / {size / 2 ** 30:.1f}GiB "
                           f"({100 * free / size:.0f}%)", None)
        except (OSError, ZeroDivisionError):
            out["disk"] = ("", "", None)
        out["power"] = ("⏻", "Power menu", None)
        return out

    def apply(self, bw, values=None):
        values = values or self.values()
        for name, (text, tip, cls) in values.items():
            if name not in bw.mods:
                continue
            btn, lab = bw.mods[name]
            if lab.get_text() != text:
                lab.set_text(text)
            btn.set_visible(bool(text))
            if tip and btn.get_tooltip_text() != tip:
                btn.set_tooltip_text(tip)
            for c in ("warning", "critical", "charging", "plugged", "connected", "off", "on", "disconnected"):
                set_class(btn, c, c == cls)

    def refresh(self):
        values = self.values()
        for bw in self.windows:
            self.apply(bw, values)
        return True

    def slow_refresh(self):
        """Síť, VPN a Bluetooth: dotazy, které chvíli trvají, běží na pozadí."""
        if self.busy:
            return True
        self.busy = True

        def work():
            net, vpn, bt = None, [], None
            ap = (None, None)
            wireless = {}
            for line in read("/proc/net/wireless").splitlines()[2:]:
                name, _, rest = line.partition(":")
                try:
                    wireless[name.strip()] = min(100, round(float(rest.split()[1].rstrip(".")) * 100 / 70))
                except (IndexError, ValueError):
                    pass
            for line in run("nmcli", "-t", "-f", "NAME,TYPE,DEVICE", "connection", "show", "--active").splitlines():
                parts = split_terse(line)
                if len(parts) < 3:
                    continue
                name, kind, dev = parts[:3]
                if kind in ("wireguard", "vpn"):
                    vpn.append(self.vpn_name(name))
                elif kind == "802-11-wireless" and (net is None or net[0] != "wifi"):
                    net = ("wifi", name, wireless.get(dev, 0), dev)
                    ap = self.active_ap(dev)
                elif kind == "802-3-ethernet" and net is None:
                    net = ("ethernet", dev, 0)
            if net is None:
                net = ("down", "", 0)
            try:
                bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
                res = bus.call_sync("org.bluez", "/", "org.freedesktop.DBus.ObjectManager", "GetManagedObjects",
                                    None, GLib.VariantType("(a{oa{sa{sv}}})"), Gio.DBusCallFlags.NONE, 1500, None)
                powered, devices = False, []
                for _path, ifaces in res.unpack()[0].items():
                    adapter = ifaces.get("org.bluez.Adapter1")
                    if adapter:
                        powered = powered or bool(adapter.get("Powered"))
                    dev = ifaces.get("org.bluez.Device1")
                    if dev and dev.get("Connected"):
                        devices.append(dev.get("Alias") or dev.get("Name") or "device")
                bt = (powered, devices)
            except GLib.Error:
                bt = None
            GLib.idle_add(done, net, vpn, bt, ap)

        def done(net, vpn, bt, ap):
            self.busy = False
            self.ap_path, self.ap_strength = ap
            self.state.update(net=net, vpn=vpn, bt=bt)
            self.refresh()
            return False
        threading.Thread(target=work, daemon=True).start()
        return True


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="io.github.island_panel",
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.panel = self.trigger = self.side = self.center = self.edge = self.css_monitor = None
        self.server = self.toasts = self.icons = None
        self.walls = self.picker = self.net = self.hypr_events = self.bar = None

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
        if not BAR_ENABLED:          # s lištou panel otevírá ostrůvek s časem (i pruh nad ním)
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
        if NET_ENABLED:
            self.hypr_events = HyprEvents()
            self.net = Connections(self)
        if WALL_ENABLED:
            self.walls = Wallpapers()
            self.walls.fx = WallpaperFx(self, self.walls)
            self.walls.restore()                               # po přihlášení vrátit vybranou tapetu
            self.picker = WallpaperPicker(self, self.walls)
            GLib.timeout_add_seconds(5, self.walls.warm_up)    # náhledy připravit předem na pozadí
        if BAR_ENABLED:
            self.bar = Bar(self)
        self.hold()

    def do_shutdown(self):
        if self.center:
            self.center.shutdown()
        Gtk.Application.do_shutdown(self)

    def load_css(self, style):
        try:
            self.provider.load_from_file(style)
        except GLib.Error as err:
            print(f"island-panel: error in style.css: {err.message}", file=sys.stderr)

    def do_command_line(self, command_line):
        args = command_line.get_arguments()[1:]
        if "--quit" in args:
            self.quit()
        elif "--wifi" in args or "--bluetooth" in args or "--vpn" in args:
            if self.net:
                self.net.toggle("wifi" if "--wifi" in args else "bluetooth" if "--bluetooth" in args else "vpn")
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
