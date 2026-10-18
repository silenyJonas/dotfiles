#!/usr/bin/env python3
"""Údaje pro zamykací obrazovku (hyprlock je čte přes cmd[...] v popiscích).

Použití:  lockinfo.py <co>
  weather-icon | weather-temp | weather-desc | weather-more | weather-refresh
  fetch | dots
  cpu | ram | disk | cpu-temp
  media-title | media-artist | media-art | media-play | media <PlayPause|Next|Previous>
  notif-head | notif-list
Výstup je text s Pango značkami (barvy a tučné písmo), nebo cesta k obrázku.
"""
import datetime
import getpass
import hashlib
import json
import os
import socket
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "island-lock")
STATE = os.path.join(os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"), "island-panel")
ART_CACHE = os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "island-panel")

FG, DIM, ACCENT, PILL, PILL_FG = "#ffffff", "#a0a0a0", "#ffffff", "#ffffff", "#000000"
WEATHER_CITY = "Prague"   # pro které město se počasí stahuje (prázdné = odhad podle IP adresy)
WEATHER_LABEL = "Praha"   # jak se město ukáže na zamykací obrazovce


def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def read(path, default=""):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return default


def short(text, n):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


# ------------------------------------------------------------------ počasí
WEATHER_FILE = os.path.join(CACHE, f"weather-{WEATHER_CITY or 'auto'}.json")
ICONS = {113: "", 116: "", 119: "", 122: "", 143: "", 248: "", 260: ""}
STORM = {200, 386, 389, 392, 395}
SNOW = {179, 182, 185, 227, 230, 281, 284, 311, 314, 317, 320, 323, 326, 329, 332, 335, 338, 350, 362, 365,
        368, 371, 374, 377}


def weather_refresh(force=False):
    try:
        if not force and time.time() - os.path.getmtime(WEATHER_FILE) < 1800:
            return
    except OSError:
        pass
    url = f"https://wttr.in/{urllib.parse.quote(WEATHER_CITY)}?format=j1&lang=en"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        os.makedirs(CACHE, exist_ok=True)
        with open(WEATHER_FILE + ".part", "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(WEATHER_FILE + ".part", WEATHER_FILE)
    except Exception:
        pass


def weather():
    try:
        with open(WEATHER_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data["current_condition"][0], data.get("weather", [{}])[0]
    except Exception:
        return None, None


def weather_icon(code):
    hour = datetime.datetime.now().hour
    if code == 113 and not 6 <= hour < 20:
        return ""
    if code in ICONS:
        return ICONS[code]
    return "" if code in STORM else "" if code in SNOW else ""


# ------------------------------------------------------------------ systém
def uptime():
    secs = int(float(read("/proc/uptime", "0").split()[0]))
    h, m = secs // 3600, secs // 60 % 60
    return f"{h // 24}d {h % 24}h" if h >= 24 else f"{h}h {m}m" if h else f"{m}m"


def battery():
    base = "/sys/class/power_supply"
    try:
        bats = sorted(b for b in os.listdir(base) if b.startswith("BAT"))
    except OSError:
        return None
    if not bats:
        return None
    cap, status = read(f"{base}/{bats[0]}/capacity"), read(f"{base}/{bats[0]}/status")
    sign = "+" if status in ("Charging", "Full", "Not charging") else "-"
    return f"({sign}) {cap}%"


def cpu_percent():
    """Vytížení od minulého zavolání (stav se ukládá do souboru)."""
    vals = [int(v) for v in read("/proc/stat").splitlines()[0].split()[1:9]]
    total, idle = sum(vals), vals[3] + vals[4]
    path = os.path.join(CACHE, "cpu")
    prev = read(path).split()
    os.makedirs(CACHE, exist_ok=True)
    with open(path, "w") as f:
        f.write(f"{total} {idle}")
    if len(prev) == 2 and total > int(prev[0]):
        return 100 * (1 - (idle - int(prev[1])) / (total - int(prev[0])))
    return 0.0


def ram_percent():
    info = {}
    for line in read("/proc/meminfo").splitlines():
        key, _, rest = line.partition(":")
        info[key] = int(rest.split()[0])
    return 100 * (1 - info["MemAvailable"] / info["MemTotal"])


def disk_percent():
    st = os.statvfs("/")
    return 100 * (1 - st.f_bavail / st.f_blocks)


def cpu_temp():
    best = None
    try:
        for hw in os.listdir("/sys/class/hwmon"):
            name = read(f"/sys/class/hwmon/{hw}/name")
            if name in ("coretemp", "k10temp", "zenpower", "cpu_thermal", "acpitz"):
                value = read(f"/sys/class/hwmon/{hw}/temp1_input")
                if value.isdigit() and (best is None or name != "acpitz"):
                    best = int(value) / 1000
    except OSError:
        pass
    return best


# ------------------------------------------------------------------ přehrávač (MPRIS)
def players():
    import gi
    from gi.repository import Gio, GLib
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

    def call(dest, path, iface, method, args=None):
        return bus.call_sync(dest, path, iface, method, args, None, Gio.DBusCallFlags.NONE, 300, None).unpack()

    names = call("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", "ListNames")[0]
    found = []
    for name in sorted(n for n in names if n.startswith("org.mpris.MediaPlayer2.")):
        try:
            props = call(name, "/org/mpris/MediaPlayer2", "org.freedesktop.DBus.Properties", "GetAll",
                         GLib.Variant("(s)", ("org.mpris.MediaPlayer2.Player",)))[0]
        except GLib.Error:
            continue
        meta = props.get("Metadata") or {}
        artist = meta.get("xesam:artist") or ""
        if isinstance(artist, (list, tuple)):
            artist = ", ".join(map(str, artist))
        info = {"bus": name, "playing": props.get("PlaybackStatus") == "Playing",
                "title": str(meta.get("xesam:title") or ""), "artist": str(artist),
                "art": str(meta.get("mpris:artUrl") or "")}
        if info["title"] or info["artist"]:
            found.append(info)
    return bus, found


def main_player():
    try:
        bus, found = players()
    except Exception:
        return None, None
    return bus, next((p for p in found if p["playing"]), found[0] if found else None)


def art_path(url):
    if url.startswith("file://"):
        return urllib.parse.unquote(url[7:])
    if url.startswith(("http://", "https://")):
        path = os.path.join(ART_CACHE, hashlib.sha1(url.encode()).hexdigest())   # stejná mezipaměť jako panel
        if not os.path.exists(path):
            try:
                with urllib.request.urlopen(url, timeout=5) as resp:
                    data = resp.read()
                os.makedirs(ART_CACHE, exist_ok=True)
                with open(path + ".part", "wb") as f:
                    f.write(data)
                os.replace(path + ".part", path)
            except Exception:
                return None
        return path
    return None


def square(path, size=256):
    """Čtvercový výřez obrázku (hyprlock jinak kulatý obrázek roztáhne do elipsy)."""
    out = os.path.join(CACHE, "sq-" + hashlib.sha1(f"{path}|{os.path.getmtime(path)}|{size}".encode()).hexdigest() + ".png")
    if os.path.exists(out):
        return out
    import gi
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import GdkPixbuf
    pix = GdkPixbuf.Pixbuf.new_from_file(path)
    w, h = pix.get_width(), pix.get_height()
    side = min(w, h)
    pix = pix.new_subpixbuf((w - side) // 2, (h - side) // 2, side, side).scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
    os.makedirs(CACHE, exist_ok=True)
    for old in os.listdir(CACHE):                 # staré výřezy smazat, ať se nehromadí
        if old.startswith("sq-") and len(os.listdir(CACHE)) > 30:
            os.remove(os.path.join(CACHE, old))
    pix.savev(out, "png", [], [])
    return out


def background(path, refresh=False):
    """Zmenšená kopie tapety (rychlejší načtení zámku). Když ještě není, použije se originál."""
    if not path or path == "screenshot" or not os.path.exists(path):
        return path
    out = os.path.join(CACHE, "bg-" + hashlib.sha1(f"{path}|{os.path.getmtime(path)}".encode()).hexdigest() + ".jpg")
    if os.path.exists(out):
        return out
    if not refresh:
        return path
    import gi
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import GdkPixbuf
    pix = GdkPixbuf.Pixbuf.new_from_file(path)
    w, h = pix.get_width(), pix.get_height()
    k = min(1.0, 2560 / w)
    if k < 1.0:
        pix = pix.scale_simple(int(w * k), int(h * k), GdkPixbuf.InterpType.BILINEAR)
    os.makedirs(CACHE, exist_ok=True)
    for old in os.listdir(CACHE):
        if old.startswith("bg-"):
            os.remove(os.path.join(CACHE, old))
    pix.savev(out + ".part", "jpeg", ["quality"], ["92"])
    os.replace(out + ".part", out)
    return out


# ------------------------------------------------------------------ oznámení
def notifications():
    try:
        with open(os.path.join(STATE, "notifications.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"count": 0, "items": []}


def ago(t):
    d = time.time() - t
    if d < 60:
        return "now"
    if d < 3600:
        return f"{int(d // 60)}m"
    if d < 86400:
        return f"{int(d // 3600)}h"
    return f"{int(d // 86400)}d"


# ------------------------------------------------------------------ výstup
def out(what, arg=None):
    if what == "weather-refresh":
        weather_refresh(force=arg == "force")
        return ""
    if what.startswith("weather"):
        cur, day = weather()
        if not cur:
            return {"weather-icon": "", "weather-temp": "—", "weather-desc": esc(WEATHER_LABEL or "Weather"),
                    "weather-more": "unavailable"}[what]
        if what == "weather-icon":
            return weather_icon(int(cur.get("weatherCode", 113)))
        if what == "weather-temp":
            return f"{cur['temp_C']}°C"
        if what == "weather-desc":
            desc = esc((cur.get("weatherDesc") or [{}])[0].get("value", "").strip())
            return f"\uf041  {esc(WEATHER_LABEL)}  •  {desc}" if WEATHER_LABEL else desc
        if what == "weather-more":
            more = f"Feels like {cur.get('FeelsLikeC', '?')}°C"
            if day.get("maxtempC"):
                more += f"\nHigh {day['maxtempC']}°C • Low {day['mintempC']}°C"
            return more
    if what == "fetch":
        bat = battery()
        osname = ""
        for line in read("/etc/os-release").splitlines():
            if line.startswith("NAME="):
                osname = line.split("=", 1)[1].strip('"').replace(" Linux", "")
            elif line.startswith("VERSION_ID="):
                osname += " " + line.split("=", 1)[1].strip('"')
        rows = [("OS", osname.strip()), ("KERN", os.uname().release.split("-")[0]),
                ("WM", os.environ.get("XDG_CURRENT_DESKTOP") or "Hyprland"),
                ("SH", os.path.basename(os.environ.get("SHELL", "")))]
        rows += [
                ("USER", getpass.getuser()), ("HOST", socket.gethostname().split(".")[0]),
                ("UP", uptime())]
        if bat:
            rows.append(("BATT", bat))
        return "\n".join(f"<span foreground='{ACCENT}'>{k:<4}</span> : {esc(short(v, 16))}" for k, v in rows)
    if what == "cpu":
        return f"{cpu_percent():.0f}%"
    if what == "ram":
        return f"{ram_percent():.0f}%"
    if what == "disk":
        return f"{disk_percent():.0f}%"
    if what == "avatar":
        try:
            return square(arg, 340)
        except Exception:
            return os.path.join(HERE, "no-art.png")
    if what == "cpu-temp":
        t = cpu_temp()
        return f"{t:.0f}°C" if t is not None else ""
    if what == "background-cache":
        import importlib.util
        spec = importlib.util.spec_from_file_location("lock", os.path.join(HERE, "lock.py"))
        lock = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lock)
        background(lock.wallpaper(), refresh=True)
        return ""
    if what == "pause-all":
        bus, found = players()
        for player in found:
            if player["playing"]:
                bus.call_sync(player["bus"], "/org/mpris/MediaPlayer2", "org.mpris.MediaPlayer2.Player", "Pause",
                              None, None, 0, 1000, None)
        return ""
    if what == "media":
        bus, player = main_player()
        if player:
            bus.call_sync(player["bus"], "/org/mpris/MediaPlayer2", "org.mpris.MediaPlayer2.Player", arg or "PlayPause",
                          None, None, 0, 500, None)
        return ""
    if what.startswith("media-"):
        _bus, player = main_player()
        if what == "media-art":
            path = art_path(player["art"]) if player else None
            try:
                return square(path) if path else os.path.join(HERE, "no-art.png")
            except Exception:
                return os.path.join(HERE, "no-art.png")
        if not player:
            return {"media-title": "Nothing playing", "media-artist": "", "media-play": ""}[what]
        if what == "media-title":
            return esc(short(player["title"] or "Untitled", 19))
        if what == "media-artist":
            return esc(short(player["artist"], 28))
        if what == "media-play":
            return "" if player["playing"] else ""
    if what == "notif-head":
        n = notifications()["count"]
        return f"{n} notification{'s' if n != 1 else ''}" if n else "No notifications"
    if what == "notif-list":
        lines = []
        for item in notifications()["items"][:8]:
            app = esc(short(item.get("app") or "System", 24))
            summary = esc(short(item.get("summary") or "", 34))
            lines.append(f"<b>{app}</b>  <span foreground='{DIM}' size='smaller'>{ago(item.get('time', 0))}</span>\n"
                         f"<span foreground='{DIM}'>{summary}</span>")
        return "\n\n".join(lines)
    return ""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    try:
        print(out(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
    except Exception as err:            # zamykací obrazovka nesmí kvůli chybě ukazovat nesmysly
        print("")
        print(f"lockinfo {sys.argv[1]}: {err}", file=sys.stderr)
