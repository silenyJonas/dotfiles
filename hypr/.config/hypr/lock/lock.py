#!/usr/bin/env python3
"""Zamykací obrazovka ve stylu Island panelu.

Pro každý monitor vygeneruje nastavení hyprlocku (velikosti podle rozlišení a měřítka monitoru,
protože hyprlock počítá ve skutečných pixelech) a hyprlock spustí.
Spustit:  python3 ~/.config/hypr/lock/lock.py      (--config jen vypíše cestu k vygenerovanému souboru)
"""
import getpass
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INFO = f"python3 {HERE}/lockinfo.py"
sys.path.insert(0, HERE)
import lockinfo  # noqa: E402  (údaje se zjistí rovnou tady, ať je zámek hned celý vyplněný)


def bake(what):
    """Hodnota zjištěná v okamžiku zamknutí, zapsaná rovnou do nastavení (žádné čekání na příkaz)."""
    try:
        value = lockinfo.out(what)
    except Exception:
        value = ""
    return value.replace("#", "##").replace("\n", "<br/>")
CACHE = os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "island-lock")
STATE = os.path.join(os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"), "island-panel")

# ---------------------------------------------------------------- nastavení
FONT = "Nunito"
MONO = "JetBrainsMono Nerd Font"
ICONS = "JetBrainsMono Nerd Font"
CARD_W, CARD_H = 1100, 580          # velikost karty v logických pixelech
SHOW_NOTIFICATIONS = True           # vpravo seznam oznámení (jen aplikace a nadpis, ne text zprávy)
AVATAR = ""                         # prázdné = obrázek uživatele ze systému (/var/lib/AccountsService/icons)
BLUR = 3                            # rozmazání tapety (0 = žádné)
FINGERPRINT = True                  # odemykání otiskem prstu, pokud máš otisk nahraný (fprintd-enroll)
PLACEHOLDER = "Password"
FETCH = ""

# barvy Islandu (rgba v šestnáctkové soustavě: RRGGBBAA)
CARD = "0a1e2cd9"
BORDER = "7dbedc40"
TILE = "ffffff0e"
FG = "dbe7eeff"
DIM = "7f97a5ff"
ACCENT = "7dbedcff"
PILL = "e6eef2ff"
BAD = "bf616aff"


def monitors():
    try:
        out = subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, text=True, timeout=3).stdout
        found = []
        for m in json.loads(out):
            scale = float(m.get("scale") or 1)
            w, h = m["width"], m["height"]
            if m.get("transform", 0) % 2:
                w, h = h, w
            found.append((m["name"], w / scale, h / scale, scale))
        if found:
            return found
    except Exception:
        pass
    return [("", 1920, 1080, 1.0)]


def wallpaper():
    path = os.path.expanduser(open(os.path.join(STATE, "wallpaper")).read().strip()) \
        if os.path.exists(os.path.join(STATE, "wallpaper")) else ""
    if path.startswith(os.path.join(os.path.expanduser("~/.cache"), "island-panel")) or not os.path.exists(path):
        # přepínač tapet ukládá zmenšenou kopii; najít ji nevadí, jinak snímek obrazovky
        return path if os.path.exists(path) else "screenshot"
    if os.path.splitext(path)[1].lower() in (".mp4", ".mkv", ".webm", ".mov", ".gif", ".avi", ".m4v"):
        return "screenshot"
    return path


def avatar():
    for path in (AVATAR, os.path.expanduser("~/.face.icon"), os.path.expanduser("~/.face"),
                 f"/var/lib/AccountsService/icons/{getpass.getuser()}"):
        if path and os.access(os.path.expanduser(path), os.R_OK):
            try:
                return lockinfo.square(os.path.expanduser(path), 340)
            except Exception:
                return os.path.expanduser(path)
    return os.path.join(HERE, "no-art.png")


class Layout:
    """Kreslí do jednoho monitoru; souřadnice jsou logické pixely od levého horního rohu karty."""

    def __init__(self, name, width, height, scale):
        self.name = name
        fit = min(1.0, (width - 40) / CARD_W, (height - 40) / CARD_H)   # malý monitor = karta se zmenší
        self.s = scale * fit                     # násobek pro skutečné pixely
        self.ox = (width / fit - CARD_W) / 2      # levý horní roh karty (v jednotkách karty)
        self.oy = (height / fit - CARD_H) / 2
        self.cx = width / fit / 2
        self.blocks = []

    def px(self, v):
        return round(v * self.s)

    def add(self, kind, **props):
        lines = [f"{kind} {{", f"    monitor = {self.name}"]
        lines += [f"    {k} = {v}" for k, v in props.items()]
        self.blocks.append("\n".join(lines) + "\n}")

    def box(self, x, y, w, h, color=TILE, rounding=20, border=0, border_color=BORDER, z=0):
        self.add("shape", size=f"{self.px(w)}, {self.px(h)}", color=f"rgba({color})", rounding=self.px(rounding),
                 border_size=self.px(border), border_color=f"rgba({border_color})",
                 position=f"{self.px(self.ox + x)}, {-self.px(self.oy + y)}", halign="left", valign="top", zindex=z)

    def text(self, x, y, text, size=14, color=FG, font=FONT, align="left", z=2, **extra):
        """align: left = x je levý okraj, center = x je střed, right = x je pravý okraj."""
        if align == "left":
            pos, halign = self.px(self.ox + x), "left"
        elif align == "center":
            pos, halign = self.px(self.ox + x - self.cx), "center"
        else:
            pos, halign = -self.px(2 * self.cx - self.ox - x), "right"
        self.add("label", text=text, color=f"rgba({color})", font_size=self.px(size), font_family=font,
                 position=f"{pos}, {-self.px(self.oy + y)}", halign=halign, valign="top", zindex=z, **extra)

    def image(self, x, y, size, path, rounding=-1, border=0, z=2, **extra):
        self.add("image", path=path, size=self.px(size), rounding=rounding if rounding < 0 else self.px(rounding),
                 border_size=self.px(border), border_color=f"rgba({ACCENT})",
                 position=f"{self.px(self.ox + x)}, {-self.px(self.oy + y)}", halign="left", valign="top",
                 zindex=z, **extra)

    # ------------------------------------------------------------ obsah
    def build(self):
        self.box(0, 0, CARD_W, CARD_H, CARD, 30, 1, BORDER)
        self.left(14)
        self.center(364 + 10, 372 - 20)
        self.right(736)

    def left(self, x):
        w = 350
        # počasí (město je nastavené v lockinfo.py)
        self.box(x, 14, w, 200)
        cx = x + w / 2
        self.text(cx, 36, bake("weather-desc"), 14, DIM, align="center")
        self.text(cx - 12, 64, bake("weather-temp"), 46, FG, align="right", text_align="right")
        self.text(cx + 4, 68, bake("weather-icon"), 40, FG, ICONS)
        self.text(cx, 146, bake("weather-more"), 13, DIM, align="center", text_align="center")
        # fetch
        self.box(x, 226, w, 340)
        lines = FETCH.count("<br/>") + 1
        self.text(x + w / 2, 226 + (340 - lines * 27) / 2, FETCH, 15, FG, MONO, align="center", text_align="left")

    def center(self, x, w):
        cx = x + w / 2
        self.text(cx, 44, "<span font_weight='800'>$TIME</span>", 84, FG, align="center",
                  shadow_passes=2, shadow_size=6, shadow_color="rgba(00000055)")
        self.text(cx, 168, "cmd[update:60000] LC_ALL=C date +'%A • %-d %b' | tr a-z A-Z", 15, FG,
                  f"{FONT} Bold", align="center")
        self.image(cx - 85, 222, 170, avatar(), -1, 3)
        self.add("input-field", size=f"{self.px(290)}, {self.px(46)}", outline_thickness=self.px(1),
                 dots_size=0.28, dots_spacing=0.35, dots_center="true", dots_rounding=-1,
                 outer_color=f"rgba({BORDER})", inner_color=f"rgba({TILE})", font_color=f"rgba({FG})",
                 font_family=FONT, fade_on_empty="false", placeholder_text=f"<span foreground='##7f97a5'>{PLACEHOLDER}</span>",
                 hide_input="false", rounding=-1, check_color=f"rgba({ACCENT})", fail_color=f"rgba({BAD})",
                 fail_text="<i>$FAIL</i>", capslock_color="rgba(ebcb8bff)",
                 position=f"{self.px(self.ox + cx - self.cx)}, {-self.px(self.oy + 448)}", halign="center",
                 valign="top", zindex=3)
        self.text(cx, 508, f"  {getpass.getuser()}", 12, DIM, align="center")

    def right(self, x):
        w = 350
        self.box(x, 14, w, 552)
        if SHOW_NOTIFICATIONS:
            self.text(x + 20, 34, bake("notif-head"), 13, DIM, MONO)
            self.text(x + 20, 68, bake("notif-list") or " ", 13, FG)
        else:
            self.text(x + w / 2, 260, "", 40, DIM, ICONS, align="center")


FP_FILE = os.path.join(CACHE, "fingerprint")


def fingerprint(refresh=False):
    """Má uživatel nahraný otisk prstu? Zjišťování trvá, proto se výsledek pamatuje
    a obnovuje až po zamknutí (projeví se příště)."""
    if not FINGERPRINT:
        return False
    if not refresh:
        return lockinfo.read(FP_FILE) == "yes"
    found = False
    if shutil.which("fprintd-list"):
        try:
            out = subprocess.run(["fprintd-list", getpass.getuser()], capture_output=True, text=True,
                                 timeout=5).stdout
            found = " - #" in out
        except (OSError, subprocess.TimeoutExpired):
            pass
    os.makedirs(CACHE, exist_ok=True)
    with open(FP_FILE, "w") as f:
        f.write("yes" if found else "no")
    return found


def config():
    fp = fingerprint()
    global PLACEHOLDER, FETCH
    FETCH = bake("fetch")
    PLACEHOLDER = "Password or fingerprint" if fp else "Password"
    parts = [f"""# Vygenerováno skriptem {HERE}/lock.py, úpravy dělej tam (tenhle soubor se přepisuje).
auth:fingerprint:enabled = {"true" if fp else "false"}
auth:fingerprint:ready_message = Password or fingerprint
auth:fingerprint:present_message = Reading fingerprint…
general {{
    hide_cursor = false
    ignore_empty_input = true
    fail_timeout = 1500
}}
animations {{
    enabled = true
    bezier = ease, 0.25, 0.1, 0.25, 1
    animation = fadeIn, 1, 1.5, ease
    animation = fadeOut, 1, 3, ease
    animation = inputFieldDots, 1, 2, ease
}}
"""]
    bg = lockinfo.background(wallpaper())
    for name, w, h, scale in monitors():
        parts.append(f"""background {{
    monitor = {name}
    path = {bg}
    color = rgba(0a1e2cff)
    blur_passes = {BLUR}
    blur_size = 6
    brightness = 0.75
    vibrancy = 0.2
}}""")
        layout = Layout(name, w, h, scale)
        layout.build()
        parts += layout.blocks
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "hyprlock.conf")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(parts) + "\n")
    return path


if __name__ == "__main__":
    if subprocess.run(["pidof", "hyprlock"], capture_output=True).returncode == 0 and "--config" not in sys.argv:
        sys.exit(0)                     # už je zamčeno
    conf = config()
    if "--config" in sys.argv:
        print(conf)
        sys.exit(0)
    lock = subprocess.Popen(["hyprlock", "-c", conf] + sys.argv[1:])
    # až po zamknutí: zastavit přehrávání, připravit věci na příště
    for job in ("pause-all", "weather-refresh", "background-cache"):
        subprocess.Popen([sys.executable, os.path.join(HERE, "lockinfo.py"), job],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    fingerprint(refresh=True)
    sys.exit(lock.wait())
