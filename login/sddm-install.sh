#!/usr/bin/env bash
# Přihlašovací obrazovka Island (SDDM): nejdřív velké hodiny, po stisku klávesy účet, heslo a výběr
# prostředí (Hyprland, GNOME…). Pozadí = aktuální tapeta z plochy, při změně tapety se samo obnoví.
# Spustit:  bash ~/Downloads/sddm-install.sh
# Návrat ke GDM:  sudo systemctl disable sddm && sudo systemctl enable gdm
set -e
DL=${ISLAND_SRC:-$HOME/Downloads}     # odkud vzít soubory (z dotfiles je to dočasná složka)
T=/usr/share/sddm/themes/island
for f in sddm-island.tar.gz island-sddm-bg; do
  [ -f "$DL/$f" ] || { echo "V $DL chybí $f"; exit 1; }
done
sudo -v

echo "== 1/7 SDDM"
rpm -q sddm >/dev/null 2>&1 || sudo dnf install -y sddm
rpm -q sddm | sed 's/^/   /'

echo "== 2/7 téma do $T"
sudo rm -rf "$T"
sudo tar xzf "$DL/sddm-island.tar.gz" -C /usr/share/sddm/themes/
# pozadí patří tobě, aby ho mohl měnit přepínač tapet; SDDM ho jen čte
for f in background.jpg background-blur.jpg; do
  sudo touch "$T/$f"
  sudo chown "$USER:$USER" "$T/$f"
  sudo chmod 644 "$T/$f"
done

echo "== 3/7 písma do systému (SDDM do tvé složky nevidí)"
# -L: ~/.local/share/fonts je odkaz do dotfiles, find by do něj jinak nevlezl
NUNITO=$(find -L ~/.local/share/fonts /usr/share/fonts -iname 'Nunito*wght*.ttf' ! -iname '*Italic*' 2>/dev/null | head -1)
ICONS=$(find -L ~/.local/share/fonts /usr/share/fonts -iname '*JetBrains*Mono*Nerd*' \( -iname '*.ttf' -o -iname '*.otf' \) 2>/dev/null \
        | grep -viE 'italic|bold|light|thin|medium|propo' | head -1)
sudo mkdir -p /usr/local/share/fonts/island
[ -n "$NUNITO" ] && sudo cp "$NUNITO" /usr/local/share/fonts/island/ && echo "   $NUNITO" || echo "   POZOR: písmo Nunito nenalezeno"
[ -n "$ICONS" ] && sudo cp "$ICONS" /usr/local/share/fonts/island/ && echo "   $ICONS" || echo "   POZOR: JetBrains Mono Nerd Font nenalezen (ikony nebudou vidět)"
sudo chmod 644 /usr/local/share/fonts/island/* 2>/dev/null || true
sudo fc-cache -f /usr/local/share/fonts/island >/dev/null

echo "== 4/7 fotka účtu"
# kratší strana obrázku v pixelech (0 = nejde přečíst)
img_size() {
  python3 -c '
import sys, gi
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf
info = GdkPixbuf.Pixbuf.get_file_info(sys.argv[1])
print(min(info[1], info[2]) if info and info[0] else 0)
' "$1" 2>/dev/null || echo 0
}
TMPF=$(mktemp -d)
FACE=""; BEST=0
for f in ~/.face.icon ~/.face "/var/lib/AccountsService/icons/$USER"; do
  if sudo test -f "$f"; then
    sudo cat "$f" > "$TMPF/face"
    W=$(img_size "$TMPF/face")
    if [ "$W" -gt "$BEST" ]; then FACE=$f; BEST=$W; fi
  fi
done
[ -n "$FACE" ] && echo "   nalezeno: $FACE (${BEST} px)"
if [ "$BEST" -lt 300 ]; then
  echo "   Tahle fotka je malá, na přihlášení by byla rozmazaná."
  echo "   Zadej cestu k původnímu obrázku (ideálně čtverec aspoň 512 px), nebo jen Enter:"
  read -r -e -p "   > " PICK
  PICK="${PICK/#\~/$HOME}"
  if [ -n "$PICK" ] && [ -f "$PICK" ]; then
    FACE="$PICK"
    echo "   použije se: $FACE ($(img_size "$FACE") px)"
    cp "$FACE" ~/.face.icon 2>/dev/null || true      # příště se najde sama
  fi
fi
if [ -n "$FACE" ]; then
  sudo mkdir -p /usr/share/sddm/faces
  sudo cat "$FACE" | sudo tee "/usr/share/sddm/faces/$USER.face.icon" >/dev/null
  sudo chmod 644 "/usr/share/sddm/faces/$USER.face.icon"
else
  echo "   žádná fotka (místo ní bude první písmeno jména)"
fi
rm -rf "$TMPF"

echo "== 5/7 pozadí = tapeta z plochy (obnovuje se samo)"
mkdir -p ~/.local/bin ~/.config/systemd/user
install -m 755 "$DL/island-sddm-bg" ~/.local/bin/island-sddm-bg
cat > ~/.config/systemd/user/island-sddm-bg.service <<'UNIT'
[Unit]
Description=Pozadí přihlašovací obrazovky podle tapety

[Service]
Type=oneshot
ExecStart=%h/.local/bin/island-sddm-bg
UNIT
cat > ~/.config/systemd/user/island-sddm-bg.path <<'UNIT'
[Unit]
Description=Hlídá změnu tapety (Island panel)

[Path]
PathChanged=%h/.local/state/island-panel/wallpaper
Unit=island-sddm-bg.service

[Install]
WantedBy=default.target
UNIT
systemctl --user daemon-reload
systemctl --user enable --now island-sddm-bg.path >/dev/null 2>&1
~/.local/bin/island-sddm-bg | sed 's/^/   /'

echo "== 6/7 nastavení SDDM"
if grep -q '^Current=' /etc/sddm.conf 2>/dev/null; then
  sudo sed -i 's/^Current=.*/Current=island/' /etc/sddm.conf
fi
sudo mkdir -p /etc/sddm.conf.d
# téma + pamatovat si posledního uživatele a prostředí (Hyprland/GNOME…), ať se nevybírá pokaždé
printf '[Theme]\nCurrent=island\n\n[Users]\nRememberLastUser=true\nRememberLastSession=true\n' \
  | sudo tee /etc/sddm.conf.d/zz-island.conf >/dev/null
# soubory se čtou podle abecedy a pozdější vyhrává (např. kde_settings.conf z KDE by téma přepsal)
sudo rm -f /etc/sddm.conf.d/island.conf
for f in /etc/sddm.conf.d/*.conf; do
  [ "$f" = /etc/sddm.conf.d/zz-island.conf ] || sudo sed -i 's/^Current=.*/Current=island/' "$f"
done
echo "   téma: island, pamatuje si poslední prostředí"
# dokud se přes SDDM nikdo nepřihlásil, předvybrat Hyprland
STATE=/var/lib/sddm/state.conf
HYPR=$(ls /usr/share/wayland-sessions/hyprland.desktop 2>/dev/null || ls /usr/share/wayland-sessions/*yprland*.desktop 2>/dev/null | head -1)
if [ -n "$HYPR" ] && ! sudo grep -q '^Session=' "$STATE" 2>/dev/null; then
  sudo mkdir -p /var/lib/sddm
  printf '[Last]\nSession=%s\nUser=%s\n' "$HYPR" "$USER" | sudo tee "$STATE" >/dev/null
  sudo chown sddm:sddm "$STATE" 2>/dev/null || true
  echo "   předvybráno: $(basename "$HYPR" .desktop)"
fi
echo "   rozložení klávesnice na přihlášení: $(localectl status | sed -n 's/.*X11 Layout: *//p')"

echo "== 7/7 náhled"
echo "   Otevře se náhled v okně (heslo v něm nic nedělá, prostředí jsou jen ukázka)."
echo "   Zavřeš ho Super+Q."
GREETER=$(command -v sddm-greeter-qt6 || command -v sddm-greeter)
QT_QPA_PLATFORM=wayland "$GREETER" --test-mode --theme "$T" >/tmp/sddm-preview.log 2>&1 || true

echo
if systemctl is-enabled sddm >/dev/null 2>&1; then
  echo "Hotovo. SDDM už je zapnuté, novou obrazovku uvidíš po odhlášení nebo restartu."
  exit 0
fi
read -r -p "Přepnout přihlašování z GDM na SDDM (projeví se po restartu)? [a/N] " ans
if [[ "$ans" =~ ^[aAyY] ]]; then
  sudo systemctl disable gdm 2>/dev/null || true
  sudo systemctl enable sddm
  echo "Hotovo. Po restartu uvidíš novou přihlašovací obrazovku."
  echo "Návrat zpět:  sudo systemctl disable sddm && sudo systemctl enable gdm"
else
  echo "Nic se nepřepnulo. Až budeš chtít:  sudo systemctl disable gdm && sudo systemctl enable sddm"
fi
