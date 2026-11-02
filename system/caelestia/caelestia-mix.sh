#!/usr/bin/env bash
# Caelestia shell v TVÉM Hyprlandu (hlavní účet joncl):
#   - tvůj config, zkratky, pravidla oken, plochy (workspaces.py) zůstávají; Caelestia nahradí jen Island panel
#   - klávesy, které dřív otevíraly Island panel, teď otevírají totéž v Caelestii (Super+D, A, W, X, L…)
#   - funkce Caelestie navíc na volných klávesách (schránka, emoji, oznámení, nahrávání, Gaming…)
#   - oblíbené aplikace; aliasy Adobe (photoshop → PhotoCraft)
#   - barvy GTK, terminálu, Vesktopu, Spotify… Caelestia NEMĚNÍ (vše vypnuto v cli.json)
#
#   (potřebuje Files.qml ve stejné složce)
#   bash ~/Downloads/caelestia-mix.sh            nainstalovat / znovu nastavit (i po aktualizaci Caelestie)
#   shell-switch                                 přepnout Island ⇄ Caelestia hned, bez odhlášení
#   bash ~/Downloads/caelestia-mix.sh --undo     úplně zpět na Island panel (vrátí i úpravy configu)
#
set -uo pipefail
D=~/dotfiles
H=$D/hypr/.config/hypr
HL=$H/hyprland.lua
SRC="$(cd "$(dirname "$0")" && pwd)"
STATE=~/.local/state/caelestia-mix
QS=~/.config/quickshell/caelestia
[[ $EUID -eq 0 ]] && { echo "Spusť jako svůj uživatel (ne sudo)."; exit 1; }
[[ -f $HL ]] || { echo "Chybí $HL"; exit 1; }
ok()   { printf '   %s\n' "$*"; }
fail() { printf '   ! %s\n' "$*"; exit 1; }

# ---------------------------------------------------------------- úpravy hyprland.lua (vrátitelné)
patch_hypr() {
python3 - "$HL" "$1" <<'PY'
import re, sys
p, mode = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8").read()
TAG = "-- caelestia-mix"
lines = s.split("\n")
if mode == "undo":
    out = []
    for l in lines:
        m = re.match(r"^(\s*)if not CAELESTIA then (.*) end " + re.escape(TAG) + r"$", l)
        if m:
            out.append(m.group(1) + m.group(2))
        elif l.rstrip().endswith(TAG):
            continue
        else:
            out.append(l)
    open(p, "w", encoding="utf-8").write("\n".join(out))
    print("   hyprland.lua vrácen do původního stavu")
    sys.exit(0)
if '/.config/hypr/caelestia.lua")' in s and "CAELESTIA" not in s:
    print("   hyprland.lua: Caelestia je napevno (bez Island panelu)"); sys.exit(0)
if any(l.rstrip().endswith(TAG) for l in lines):
    print("   hyprland.lua už upravený"); sys.exit(0)
# věci Island panelu, které v režimu Caelestia nemají běžet / mají jinou akci
PATTERNS = {
    "Super+D (panel)":      r'^\s*hl\.bind\(mainMod \.\. " \+ D",',
    "Super+A (aplikace)":   r'^\s*hl\.bind\(mainMod \.\. " \+ A",',
    "Super+W (tapety)":     r'^\s*hl\.bind\(mainMod \.\. " \+ W",',
    "Super+X (vypnutí)":    r'^\s*hl\.bind\(mainMod \.\. " \+ X",',
    "Super+O (vypnutí)":    r'^\s*hl\.bind\(mainMod \.\. " \+ O",',
    "Super+L (zámek)":      r'^\s*hl\.bind\(mainMod \.\. " \+ L",',
    "jas nahoru":           r'^\s*hl\.bind\("XF86MonBrightnessUp"',
    "jas dolů":             r'^\s*hl\.bind\("XF86MonBrightnessDown"',
    "tapeta swaybg":        r'^\s*hl\.exec_cmd\(.*swaybg ',
    "Island panel":         r'^\s*hl\.exec_cmd\("/usr/bin/python3 ~/\.config/island-panel/panel\.py"\)',
    "hypridle":             r'^\s*hl\.exec_cmd\("hypridle"\)',
}
found = {k: 0 for k in PATTERNS}
out = []
for l in lines:
    hit = next((k for k, rx in PATTERNS.items() if re.match(rx, l)), None)
    if hit:
        found[hit] += 1
        ind = l[:len(l) - len(l.lstrip())]
        out.append(f"{ind}if not CAELESTIA then {l.strip()} end {TAG}")
    else:
        out.append(l)
missing = [k for k, n in found.items() if n == 0]
if missing:
    print("   ! v hyprland.lua jsem nenašel: " + ", ".join(missing) + " (nic jsem nezměnil)"); sys.exit(1)
head = [
    f"-- Caelestia shell místo Island panelu? Přepíná příkaz shell-switch (soubor ~/.local/state/caelestia-mix/on) {TAG}",
    f'local CAELESTIA = (function() local f = io.open(os.getenv("HOME") .. "/.local/state/caelestia-mix/on") if f then f:close() return true end return false end)() {TAG}',
    f"{TAG}",
]
tail = [f'if CAELESTIA then dofile(os.getenv("HOME") .. "/.config/hypr/caelestia.lua") end {TAG}']
while out and out[-1] == "":
    out.pop()
open(p, "w", encoding="utf-8").write("\n".join(head + out + tail) + "\n")
print("   hyprland.lua: " + str(sum(found.values())) + " řádků Island panelu se v režimu Caelestia přeskočí")
PY
}

if [[ ${1:-} == --undo ]]; then
  echo "== zpět na Island panel"
  [[ -x ~/.local/bin/shell-switch ]] && ~/.local/bin/shell-switch island >/dev/null 2>&1
  patch_hypr undo
  rm -f "$H/caelestia.lua" "$D/local/.local/bin/shell-switch" ~/.local/bin/shell-switch
  (cd "$D" && stow -D caelestia 2>/dev/null); rm -rf "$D/caelestia" "$QS" "$STATE"
  rm -f ~/.local/share/applications/ai.storyteller.*.desktop
  hyprctl reload >/dev/null 2>&1
  ok "Hotovo. Balíčky Caelestie zůstaly, odebereš je: paru -Rns caelestia-shell caelestia-cli"
  exit 0
fi


echo "== 1/7 záloha"
mkdir -p "$STATE/backup"
if [[ ! -f $STATE/backup/hyprland.lua ]]; then
  cp "$HL" "$STATE/backup/hyprland.lua"
  git -C "$D" tag -f pred-caelestia >/dev/null 2>&1
  ok "hyprland.lua → $STATE/backup, stav dotfiles označen tagem 'pred-caelestia'"
else
  ok "záloha už existuje"
fi

echo "== 2/7 balíčky (caelestia-shell, caelestia-cli)"
paru -S --needed --noconfirm caelestia-shell caelestia-cli || fail "instalace selhala (výpis výše)"

echo "== 3/7 nastavení Caelestie (do dotfiles, balíček 'caelestia')"
CD=$D/caelestia/.config/caelestia
mkdir -p "$CD"
FAV='[]'
[[ -f ~/.config/island-panel/quick-apps ]] && \
  FAV=$(python3 -c 'import json,re,sys; print(json.dumps([l.strip() for l in open(sys.argv[1]) if l.strip()] + ["codium"]))' ~/.config/island-panel/quick-apps)
python3 - "$CD/shell.json" "$FAV" <<'PY'
import json, os, sys
path, fav = sys.argv[1], json.loads(sys.argv[2])
cfg = json.load(open(path)) if os.path.exists(path) else {}
def put(keys, value):
    d = cfg
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value
if fav and not cfg.get("launcher", {}).get("favouriteApps"):
    put(["launcher", "favouriteApps"], fav)      # jen poprvé, pak si je spravuješ v Super+W → Apps
put(["general", "apps", "terminal"], ["kitty"])
put(["general", "apps", "explorer"], ["thunar"])
put(["general", "apps", "audio"], ["pavucontrol"])
put(["general", "idle", "timeouts"], [])          # jako dřív: samo nezamyká ani neuspává
put(["paths", "wallpaperDir"], "~/Pictures/wallpapers")
put(["paths", "sessionGif"], "")                   # vypínací panel bez animovaného obrázku
put(["services", "smartScheme"], False)             # barvy zůstanou černobílé, i když změníš tapetu
put(["bar", "entries"], [{"id": i, "enabled": True} for i in
    ("logo", "workspaces", "spacer", "tray", "clock", "statusIcons", "files", "power")])
put(["bar", "clock", "showDate"], False)
put(["bar", "statusIcons"], [
    {"id": "lockStatus", "enabled": False}, {"id": "audio", "enabled": True},
    {"id": "microphone", "enabled": False}, {"id": "kbLayout", "enabled": False},
    {"id": "network", "enabled": True}, {"id": "bluetooth", "enabled": True}, {"id": "battery", "enabled": True}])
put(["dashboard", "showOnHover"], True)
put(["launcher", "showOnHover"], True)             # myš k dolnímu okraji uprostřed = spouštěč aplikací
put(["border", "thickness"], 0)                    # bez rámečku kolem obrazovky (Caelestia nechá 2 px na najetí myší)
put(["border", "rounding"], 20)                    # zaoblené rohy u lišty, souběžné s okny (10 + mezera)
put(["sidebar", "showOnHover"], True)               # najetí do pravého horního rohu = oznámení + přepínače
put(["background", "wallpaperTransition"], "Iris")  # nová tapeta se rozvine z kruhu uprostřed
put(["services", "weatherLocation"], "Prague")
put(["services", "clockFormat"], "TwentyFourHour")
put(["services", "weatherUnits"], "Celsius")
put(["services", "sensorUnits"], "Celsius")
put(["dashboard", "performance", "showCpu"], True)
put(["dashboard", "performance", "showGpu"], True)
put(["services", "defaultPlayer"], "Spotify")
put(["utilities", "quickToggles"], [{"id": i, "enabled": True} for i in
    ("wifi", "bluetooth", "mic", "settings", "gameMode", "dnd", "vpn")])
json.dump(cfg, open(path, "w"), indent=4, ensure_ascii=False)
PY
# Caelestia by jinak přebarvila GTK, terminály, Vesktop, Spotify, btop… podle tapety: všechno vypnout
python3 - "$CD/cli.json" <<'PY'
import json, os, sys
p = sys.argv[1]
cfg = json.load(open(p)) if os.path.exists(p) else {}
theme = cfg.setdefault("theme", {})
for k in ("Term", "Hypr", "Discord", "Spicetify", "Pandora", "Btop", "Nvtop", "Htop", "Gtk", "Qt",
          "Warp", "Chromium", "Zed", "Cava"):
    theme["enable" + k] = False
theme["enableFuzzel"] = True      # jen výběr ze schránky/emoji (fuzzel) v barvách Caelestie
json.dump(cfg, open(p, "w"), indent=4)
PY
mkdir -p ~/.config/caelestia
(cd "$D" && stow --no-folding -R caelestia 2>&1 | sed 's/^/   /')
ok "shell.json + cli.json (Caelestia nesahá na barvy ostatních aplikací)"

echo "== 4/7 lišta: tlačítko disku (Thunar) vlevo dole"
SYSQS=/etc/xdg/quickshell/caelestia
[[ -d $SYSQS ]] || fail "$SYSQS chybí (caelestia-shell se nenainstaloval?)"
# Files.qml: vedle skriptu, jinak z dotfiles (tam ho skript ukládá)
[[ -f $SRC/Files.qml ]] || { [[ -f $D/system/caelestia/Files.qml ]] && SRC=$D/system/caelestia; }
[[ -f $SRC/Files.qml ]] || fail "Chybí Files.qml (stáhni ho do stejné složky jako skript)"
# vlastní kopie shellu v ~/.config má přednost před systémovou; po aktualizaci Caelestie skript spusť znovu
rm -rf "$QS"; mkdir -p "$(dirname "$QS")"; cp -r "$SYSQS" "$QS"
mkdir -p "$D/system/caelestia"; [[ $SRC == "$D/system/caelestia" ]] || cp "$SRC/Files.qml" "$D/system/caelestia/Files.qml"
cp "$SRC/Files.qml" "$QS/modules/bar/components/Files.qml"
python3 - "$QS/modules/bar/Bar.qml" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
anchor = '            DelegateChoice {\n                roleValue: "spacer"'
add = ('            DelegateChoice {\n                roleValue: "files"\n                delegate: EntryWrapper {\n'
       '                    Files {\n                        objectName: "taskbarFiles"\n                    }\n'
       '                }\n            }\n')
if anchor not in s:
    print("   ! Bar.qml je v této verzi jiný, tlačítko se nepřidalo (zbytek funguje)"); sys.exit(0)
open(p, "w").write(s.replace(anchor, add + anchor, 1)); print("   tlačítko přidáno (kopie shellu v ~/.config/quickshell/caelestia)")
PY

# panel vpravo: nezavírat, dokud je myš ve sloupci panelu (i dole u nahrávání a přepínačů)
python3 - "$QS/modules/drawers/Interactions.qml" <<'PY'
import re, sys
p = sys.argv[1]; s = open(p).read()
TAG = "// island: celý sloupec panelu"
if TAG in s:
    print("   panel vpravo: už upraveno"); sys.exit(0)
rx = re.compile(r"(const inSidebarArea = [^;\n]*);")
if not rx.search(s):
    print("   ! Interactions.qml je v této verzi jiný, panel vpravo se nezměnil"); sys.exit(0)
s = rx.sub(lambda m: m.group(1) + " || x > Math.min(width - Config.border.minThickness, bar.implicitWidth + panels.sidebar.x); " + TAG, s, count=1)
open(p, "w").write(s); print("   panel vpravo zůstane otevřený, dokud je myš v jeho sloupci")
PY

# vypínací panel (vysunutý spolu s pravým panelem) se zavře, když se zavře pravý panel
python3 - "$QS/modules/drawers/Interactions.qml" <<'PY'
import re, sys
p = sys.argv[1]; s = open(p).read()
TAG = "// island: vypínací panel se zavře s pravým panelem"
if TAG in s:
    print("   vypínací panel: už upraveno"); sys.exit(0)
n = 0
def fix(m):
    ind_if, ind_body = m.group(1), m.group(m.lastindex)
    return (f"\n{ind_if}{m.group(2)} {{\n{ind_body}if (screenState.sidebar) screenState.session = false; {TAG}\n"
            f"{ind_body}screenState.sidebar = false;\n{ind_if}}}")
for rx in (r"\n([ \t]*)(if \(!inSidebarArea\))\n([ \t]*)screenState\.sidebar = false;",
           r"\n([ \t]*)(if \(Config\.sidebar\.showOnHover(?: && !sidebarShortcutActive)?\))\n([ \t]*)screenState\.sidebar = false;"):
    s, k = re.subn(rx, fix, s, count=1); n += k
open(p, "w").write(s)
print(f"   vypínací panel: zavře se spolu s pravým panelem ({n} místa)" if n else "   ! vypínací panel: Interactions.qml je jiný, beze změny")
PY

# spouštěč dole: otevřít po krátkém najetí (jako přehled nahoře), zavřít po odjetí myši
python3 - "$QS/modules/drawers/Interactions.qml" <<'PY'
import re, sys
p = sys.argv[1]; s = open(p).read()
TAG = "// island: spouštěč dole"
if TAG in s:
    print("   spouštěč dole: už upraveno"); sys.exit(0)
ok = True
# 1) vlastnosti + časovač (stejné zpoždění jako přehled nahoře)
a = "    property point dragStart\n"
if a in s:
    s = s.replace(a, a + f"    property bool launcherByHover {TAG}\n", 1)
else:
    ok = False
timer = f"""
    Timer {{ {TAG}
        id: launcherHoverTimer

        interval: 200
        onTriggered: {{
            root.screenState.launcher = true;
            root.launcherByHover = true;
        }}
    }}
"""
i = s.rstrip().rfind("}")
s = s[:i].rstrip() + "\n" + timer + "}\n"
# 2) najetí: otevřít po zpoždění, odjetí: zavřít (jen když se otevřel najetím)
rx = re.compile(r"(\n([ \t]*)if \(Config\.launcher\.showOnHover\) \{\n)[ \t]*if \(!screenState\.launcher && inBottomPanel\(panels\.launcher, x, y\)\)\n[ \t]*screenState\.launcher = true;\n")
m = rx.search(s)
if m:
    ind = m.group(2) + "    "
    body = (f"{ind}const inLauncher = inBottomPanel(panels.launcher, x, y); {TAG}\n"
            f"{ind}if (!screenState.launcher) {{\n"
            f"{ind}    if (inLauncher && !launcherHoverTimer.running)\n"
            f"{ind}        launcherHoverTimer.restart();\n"
            f"{ind}    else if (!inLauncher)\n"
            f"{ind}        launcherHoverTimer.stop();\n"
            f"{ind}}} else if (root.launcherByHover && !inLauncher) {{\n"
            f"{ind}    screenState.launcher = false;\n"
            f"{ind}}}\n")
    s = s[:m.start()] + m.group(1) + body + s[m.end():]
else:
    ok = False
# 3) myš opustila celou plochu: zrušit čekání, zavřít spouštěč otevřený najetím
a = "        if (!containsMouse) {\n"
if a in s:
    s = s.replace(a, a + f"            launcherHoverTimer.stop(); {TAG}\n            if (launcherByHover)\n                screenState.launcher = false;\n", 1)
else:
    ok = False
# 4) spouštěč zavřený jinak (Esc, spuštění aplikace): příště ho najetí zase hlídá od začátku
a = "        function onLauncherChanged() {\n"
if a in s:
    s = s.replace(a, a + f"            if (!root.screenState.launcher) root.launcherByHover = false; {TAG}\n", 1)
else:
    ok = False
if not ok:
    print("   ! Interactions.qml je v této verzi jiný, spouštěč dole se nezměnil"); sys.exit(0)
open(p, "w").write(s)
print("   spouštěč dole: otevře se po 0,2 s najetí, zavře se, když myš odjede")
PY

# přehled → Performance: karta GPU i pro grafiku Intel (Caelestia umí vytížení jen u AMD/NVIDIA)
IGPU=$(for f in /sys/class/drm/card[0-9]/gt/gt0/rc6_residency_ms /sys/class/drm/card[0-9]/power/rc6_residency_ms; do [[ -r $f ]] && echo "$f" && break; done)
if [[ -n $IGPU ]]; then
python3 - "$QS/modules/dashboard/Performance.qml" "$IGPU" <<'PY'
import sys
p, rc6 = sys.argv[1], sys.argv[2]
s = open(p).read()
TAG = "// island: Intel GPU"
if TAG in s:
    print("   karta GPU: už upraveno"); sys.exit(0)
edits = [
    ("active: Config.dashboard.performance.showGpu && Gpu.type !== GpuType.None\n",
     "active: Config.dashboard.performance.showGpu " + TAG + "\n"),
    ("subLabel: Gpu.name ||", "subLabel: (Gpu.type === GpuType.None ? intelGpu.name : Gpu.name) ||"),
    ("usage: Gpu.percentage", "usage: Gpu.type === GpuType.None ? intelGpu.load : Gpu.percentage"),
    ("temperature: Gpu.temperature", "temperature: Gpu.type === GpuType.None ? Cpu.temperature : Gpu.temperature"),
]
for a, b in edits:
    if s.count(a) != 1:
        print("   ! Performance.qml je v této verzi jiný, karta GPU se nepřidala"); sys.exit(0)
for a, b in edits:
    s = s.replace(a, b, 1)
s = s.replace("import Quickshell.Services.UPower\n", "import Quickshell.Io\nimport Quickshell.Services.UPower\n", 1)
block = """
    // island: Intel GPU nemá v jádře údaj o vytížení. Počítá se z RC6 (čas, kdy grafika spí):
    // vytížení = 1 - podíl spánku za poslední sekundu, vyhlazené, ať neskáče
    Item {
        id: intelGpu

        property real load: 0
        property real lastRc6: -1
        property real lastTime: 0
        readonly property string name: "Intel Iris Xe Graphics"

        FileView {
            id: intelGpuRc6

            path: "RC6"
            printErrors: false
            onLoaded: {
                const rc6 = parseFloat(text());
                const now = Date.now();
                if (!isNaN(rc6) && intelGpu.lastRc6 >= 0 && now > intelGpu.lastTime) {
                    const busy = 1 - (rc6 - intelGpu.lastRc6) / (now - intelGpu.lastTime);
                    const v = Math.max(0, Math.min(1, busy));
                    intelGpu.load = intelGpu.load * 0.6 + v * 0.4;
                }
                intelGpu.lastRc6 = rc6;
                intelGpu.lastTime = now;
            }
        }

        Timer {
            interval: 1000
            repeat: true
            running: root.visible
            triggeredOnStart: true
            onTriggered: intelGpuRc6.reload()
        }
    }
}
""".replace("RC6", rc6)
i = s.rstrip().rfind("}")
s = s[:i].rstrip() + "\n" + block
open(p, "w").write(s)
print("   karta GPU: Intel Iris Xe (skutečné vytížení z RC6, teplota čipu)")
PY
fi

# vypínací panel: bez mezery po vypnutém obrázku a bez odsazení od pravého kraje (rámeček je vypnutý)
python3 - "$QS/modules/session/Content.qml" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
n = 0
a = "        active: Config.paths.sessionGif.trim() !== \"\"\n"
if a in s and "visible: active // island" not in s:
    s = s.replace(a, a + "        visible: active // island\n", 1); n += 1
# starší verze (2.5): obrázek přímo v panelu, bez Loaderu
import re
src = "source: Paths.absolutePath(Config.paths.sessionGif)"
blk = s[s.rfind("AnimatedImage {", 0, s.find(src)):s.find(src)] if src in s else ""
if src in s and "visible:" not in blk and "visible: active // island" not in s:
    ind = re.search(r"\n(\s*)" + re.escape(src), s).group(1)
    s = s.replace(src, 'visible: Config.paths.sessionGif.trim() !== "" // island\n' + ind + src, 1); n += 1
b = "rightPadding: CUtils.clamp(padding - Config.border.thickness, 0, padding)"
if b in s:
    s = s.replace(b, "rightPadding: CUtils.clamp(padding - 10, 0, padding) // island", 1); n += 1
open(p, "w").write(s)
print(f"   vypínací panel: {n} úpravy" if n else "   vypínací panel: už upraveno / jiná verze")
PY

echo "== 5/7 Hyprland: tvůj config + ovládání Caelestie"
cat > "$H/caelestia.lua" <<'LUA'
-- Caelestia shell v tvém Hyprlandu. Načítá se jen v režimu Caelestia (shell-switch).
-- Tvoje zkratky z hyprland.lua platí dál; tady jsou jen ty, které ovládají Caelestii.
local g = hl.dsp.global

hl.on("hyprland.start", function()
    hl.exec_cmd("caelestia shell -d")
    hl.exec_cmd("wl-paste --type text --watch cliphist store")    -- historie schránky (Super+Shift+V)
    hl.exec_cmd("wl-paste --type image --watch cliphist store")
end)

-- tvoje klávesy, které dřív otevíraly Island panel
hl.bind("SUPER + D", g("caelestia:dashboard"))              -- přehled: kalendář, počasí, média, výkon
hl.bind("SUPER + A", g("caelestia:launcher"))               -- aplikace (oblíbené nahoře)
hl.bind("SUPER + W", g("caelestia:nexus"))                  -- nastavení Caelestie a tapety
hl.bind("SUPER + X", g("caelestia:session"))                -- vypnout / restart / odhlásit
hl.bind("SUPER + O", g("caelestia:session"))
hl.bind("SUPER + L", g("caelestia:lock"))                   -- zámek obrazovky Caelestie
hl.bind("XF86MonBrightnessUp",   g("caelestia:brightnessUp"),   { locked = true })
hl.bind("XF86MonBrightnessDown", g("caelestia:brightnessDown"), { locked = true })

-- navíc z Caelestie (klávesy, které jsi nepoužíval)
hl.bind("SUPER + SUPER_L", g("caelestia:launcher"), { release = true })  -- jen Super = aplikace
hl.bind("SUPER + K", g("caelestia:showall"))                -- všechny panely najednou
hl.bind("SUPER + U", g("caelestia:utilities"))              -- rychlé přepínače (Wi-Fi, BT, Game mode, VPN…)
hl.bind("SUPER + SHIFT + N", g("caelestia:sidebar"))        -- oznámení
hl.bind("CTRL + ALT + C", g("caelestia:clearNotifs"), { locked = true })
hl.bind("CTRL + ALT + Delete", g("caelestia:session"))
hl.bind("SUPER + SHIFT + V", hl.dsp.exec_cmd("pkill fuzzel || caelestia clipboard"))      -- historie schránky
hl.bind("SUPER + Period", hl.dsp.exec_cmd("pkill fuzzel || caelestia emoji -p"))          -- emoji
hl.bind("SUPER + SHIFT + ALT + S", g("caelestia:screenshotFreeze"))                       -- snímek se zmrazením
hl.bind("CTRL + ALT + R", hl.dsp.exec_cmd("caelestia record"))                            -- nahrávání obrazovky
hl.bind("SUPER + SHIFT + ALT + R", hl.dsp.exec_cmd("caelestia record -r"))                -- nahrávání výřezu
-- tvůj Gaming (procesor + grafika přes island-gaming), zapnout/vypnout
hl.bind("SUPER + G", hl.dsp.exec_cmd(
    "if [ -f /run/island-gaming ]; then sudo -n /usr/local/bin/island-gaming off && notify-send -a Gaming 'Gaming vypnuto'; " ..
    "else sudo -n /usr/local/bin/island-gaming on && notify-send -a Gaming 'Gaming zapnuto' 'procesor bez horkých turbo stupňů, grafika drží takt'; fi"))

-- animace panelů Caelestie
hl.layer_rule({ match = { namespace = "caelestia-(border-exclusion|area-picker)" }, no_anim = true })
hl.layer_rule({ match = { namespace = "caelestia-(drawers|background)" }, animation = "fade" })
LUA
patch_hypr apply || fail "hyprland.lua se nepodařilo upravit"
(cd "$D" && stow -R hypr 2>&1 | sed 's/^/   /')   # nový soubor caelestia.lua propojit do ~/.config/hypr
[[ -e ~/.config/hypr/caelestia.lua ]] || fail "~/.config/hypr/caelestia.lua se nepropojil (stow hypr)"

if [[ -d $D/island-panel ]]; then   # přepínač jen dokud Island panel v dotfiles existuje
mkdir -p "$D/local/.local/bin"
cat > "$D/local/.local/bin/shell-switch" <<'SH'
#!/bin/sh
# Přepnutí Island panel ⇄ Caelestia hned, bez odhlášení.
#   shell-switch             přepnout
#   shell-switch caelestia   / shell-switch island
F=~/.local/state/caelestia-mix/on
mode=$1
[ -z "$mode" ] && { [ -f "$F" ] && mode=island || mode=caelestia; }
case $mode in
caelestia)
  mkdir -p "${F%/*}"; touch "$F"
  /usr/bin/python3 ~/.config/island-panel/panel.py --quit >/dev/null 2>&1
  pkill -x swaybg; pkill -x hypridle
  hyprctl reload >/dev/null
  pgrep -f 'qs -c caelestia' >/dev/null || caelestia shell -d >/dev/null 2>&1
  pgrep -f 'cliphist store' >/dev/null || {
    setsid -f wl-paste --type text --watch cliphist store >/dev/null 2>&1
    setsid -f wl-paste --type image --watch cliphist store >/dev/null 2>&1; }
  echo "Caelestia zapnutá (zpět: shell-switch island)" ;;
island)
  rm -f "$F"
  caelestia shell -k >/dev/null 2>&1; pkill -f 'qs -c caelestia' 2>/dev/null
  hyprctl reload >/dev/null
  pgrep -x swaybg >/dev/null || setsid -f swaybg -i "$(cat ~/.local/state/island-panel/wallpaper 2>/dev/null || echo ~/Pictures/wallpapers/my_name.jpg)" -m fill >/dev/null 2>&1
  pgrep -f island-panel/panel.py >/dev/null || setsid -f /usr/bin/python3 ~/.config/island-panel/panel.py >/dev/null 2>&1
  pgrep -x hypridle >/dev/null || setsid -f hypridle >/dev/null 2>&1
  echo "Island panel zapnutý (zpět: shell-switch caelestia)" ;;
*) echo "použití: shell-switch [caelestia|island]"; exit 1 ;;
esac
SH
chmod +x "$D/local/.local/bin/shell-switch"
(cd "$D" && stow -R local 2>&1 | sed 's/^/   /')
fi
ok "hotovo: ~/.config/hypr/caelestia.lua, příkaz shell-switch"

echo "== 6/7 aliasy Adobe ve vyhledávání (photoshop → PhotoCraft)"
mkdir -p ~/.local/share/applications
for pair in photocraft:Photoshop filmcraft:"Premiere Pro" vectorcraft:Illustrator effectcraft:"After Effects" \
            lightcraft:Lightroom designcraft:InDesign pdfcraft:Acrobat; do
  app=${pair%%:*}; alias=${pair#*:}
  src=$(ls /usr/share/applications/*"$app"*.desktop 2>/dev/null | head -1)
  [[ -n $src ]] || continue
  sed -E "0,/^Name=/{s/^Name=(.*)$/Name=\1 ($alias)/}" "$src" > ~/.local/share/applications/"$(basename "$src")"
done
update-desktop-database ~/.local/share/applications 2>/dev/null
ok "např. 'PhotoCraft (Photoshop)'"

echo "== 7/7 zapnutí"
# tapeta: ta z Caelestie, jinak z Island panelu, jinak první obrázek ve ~/Pictures/wallpapers
WP=$(cat ~/.local/state/caelestia/wallpaper/path.txt 2>/dev/null || cat ~/.local/state/island-panel/wallpaper 2>/dev/null)
[[ -f $WP ]] || WP=$(find ~/Pictures/wallpapers -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' \) 2>/dev/null | sort | head -1)
caelestia shell -k >/dev/null 2>&1; pkill -f 'qs -c caelestia' 2>/dev/null; sleep 1   # restart, ať se načte nová lišta
if [[ -x ~/.local/bin/shell-switch ]]; then
  ~/.local/bin/shell-switch caelestia | sed 's/^/   /'
else
  hyprctl reload >/dev/null; caelestia shell -d >/dev/null 2>&1
  pgrep -f 'cliphist store' >/dev/null || { setsid -f wl-paste --type text --watch cliphist store >/dev/null 2>&1; setsid -f wl-paste --type image --watch cliphist store >/dev/null 2>&1; }
fi
sleep 3
[[ -n $WP && -f $WP ]] && caelestia wallpaper -f "$WP" >/dev/null 2>&1 && ok "tapeta: $(basename "$WP")"
caelestia scheme set -n dynamic -v monochrome -m dark >/dev/null 2>&1 && ok "barvy: černobílé (bílá – šedá – černá)"
E=$(hyprctl configerrors 2>/dev/null | grep -v '^$')
[[ -z $E || $E == "no errors" ]] && ok "config Hyprlandu bez chyb" || echo "   ! chyby v configu: $E"
pgrep -f 'qs -c caelestia' >/dev/null && ok "Caelestia běží" || echo "   ! Caelestia neběží: spusť 'caelestia shell' v terminálu a pošli mi výpis"

cat <<'EOF'

Hotovo. Tvoje zkratky platí dál (Super+C zavře okno, Super+Q terminál, Super+šipky, plochy…).
Změnilo se jen, co otevírají klávesy Island panelu, a přibyly funkce Caelestie:

  Super (samotný) / Super+A   aplikace, oblíbené nahoře      Super+D      přehled (výkon, média, počasí)
  Super+W                     nastavení a tapety             Super+X / O  vypnout, restart, odhlásit
  Super+L                     zámek                          Super+U      rychlé přepínače (Wi-Fi, BT, VPN, Game mode)
  Super+Shift+N               oznámení                       Super+K      všechny panely
  Super+Shift+V               historie schránky              Super+.      emoji
  Super+G                     tvůj Gaming (procesor/grafika) Ctrl+Alt+R   nahrávání obrazovky

Přepnutí zpět na Island panel hned:  shell-switch      (znovu shell-switch = zase Caelestia)
Po aktualizaci Caelestie (paru) spusť tenhle skript znovu (vrátí tlačítko disku).
Úplné odebrání:                      bash ~/Downloads/caelestia-mix.sh --undo
Až budeš spokojený:  cd ~/dotfiles && git add -A && git commit -m "Caelestia shell" && git push
EOF
