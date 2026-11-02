#!/usr/bin/env bash
# Obnova celého prostředí z dotfiles (Fedora) na čerstvém Arch Linuxu.
#
#   curl -fsSLo ~/arch-restore.sh https://raw.githubusercontent.com/silenyJonas/dotfiles/main/system/arch-restore.sh
#   bash ~/arch-restore.sh
#
# Spouštěj jako svůj uživatel (ne root), v běžícím Hyprlandu, s připojeným internetem.
# Skript jde spustit znovu kdykoli (co je hotové, přeskočí). Celý výpis: ~/arch-restore.log
#
# Co udělá:
#   1  základ (git, stow, paru pro AUR)                 8  systémové drobnosti (cache, kamera, Gaming, klíčenka)
#   2  stáhne dotfiles z GitHubu                        9  Flatpak aplikace + Spicetify
#   3  balíčky (Hyprland, Caelestia, aplikace, AUR)    10  VSCodium rozšíření
#   4  úpravy dotfiles pro Arch (fungují i na Fedoře)  11  služby (Bluetooth, NetworkManager…)
#   5  oh-my-zsh, propojení konfigurací (stow)         12  optimalizace (zram, rychlejší start, úklid)
#   6  vzhled (tmavé GTK, šedé ikony, Thunar)          13  Caelestia shell (lišta, panely) + kontrola
#   7  přihlašovací obrazovka SDDM "island"
#
# Navíc (volitelně): bash ~/dotfiles/system/arch-extras.sh   virt-manager + ArtCraft (náhrady Adobe)
set -uo pipefail

DOT="$HOME/dotfiles"
SYS="$DOT/system"
REPO=https://github.com/silenyJonas/dotfiles.git
BK="$HOME/.pre-dotfiles-backup/$(date +%Y%m%d-%H%M%S)"
UNRES="$HOME/arch-unresolved.txt"
LOG="$HOME/arch-restore.log"
exec > >(tee -a "$LOG") 2>&1

step() { printf '\n\033[1;37m== %s\033[0m\n' "$*"; }
ok()   { printf '   %s\n' "$*"; }
warn() { printf '\033[1;33m   ! %s\033[0m\n' "$*"; WARNINGS+=("$*"); }
have() { command -v "$1" >/dev/null 2>&1; }
ask()  { local a; read -r -p "   $1 [A/n] " a || true; [[ ! $a =~ ^[nN] ]]; }
WARNINGS=()

[[ $EUID -eq 0 ]] && { echo "Nespouštěj jako root, spusť jako svůj uživatel (sudo si řekne o heslo)."; exit 1; }
have pacman || { echo "Tohle není Arch (chybí pacman)."; exit 1; }
[[ $USER == joncl ]] || warn "Uživatel není 'joncl': cesty /home/joncl ve spicetify configu bude potřeba upravit."
sudo -v || exit 1
while true; do sudo -n true; sleep 50; kill -0 "$$" 2>/dev/null || exit; done 2>/dev/null &

###############################################################################
step "1/13 základ: aktualizace, git, stow, paru (AUR)"
sudo pacman -Syu --needed --noconfirm base-devel git stow github-cli curl wget unzip rsync || { echo "pacman selhal"; exit 1; }
if ! have paru; then
  tmp=$(mktemp -d)
  git clone --depth 1 https://aur.archlinux.org/paru-bin.git "$tmp/paru-bin" && (cd "$tmp/paru-bin" && makepkg -si --noconfirm)
  rm -rf "$tmp"
fi
have paru && ok "paru $(paru --version | head -1 | awk '{print $2}')" || warn "paru se nenainstaloval, AUR balíčky (Brave, VSCodium) se přeskočí"

###############################################################################
step "2/13 dotfiles"
if [[ -d $DOT/.git ]]; then
  git -C "$DOT" pull --ff-only || warn "git pull selhal (máš v ~/dotfiles neuložené změny?), pokračuji s tím, co tam je"
else
  git clone "$REPO" "$DOT" || { echo "Nepovedlo se stáhnout dotfiles."; exit 1; }
fi
ok "$(git -C "$DOT" log -1 --format='%h %s')"

###############################################################################
step "3/13 balíčky"
# Co tvoje prostředí potřebuje (Hyprland, Caelestia, přihlášení, aplikace), jména pro Arch
CORE=(
  # Hyprland a okolí
  hyprland hypridle hyprlock hyprpaper hyprland-guiutils xdg-desktop-portal-hyprland xdg-desktop-portal-gtk
  qt5-wayland qt6-wayland lxqt-policykit gnome-keyring libsecret seahorse python-secretstorage
  # knihovny pro vlastní skripty (pozadí přihlášení, help…)
  python python-gobject python-cairo gtk3 gtk-layer-shell gdk-pixbuf2 librsvg libnotify glib2 gsettings-desktop-schemas
  networkmanager bluez bluez-utils pipewire pipewire-pulse pipewire-alsa wireplumber pavucontrol alsa-utils
  sof-firmware alsa-ucm-conf alsa-firmware libva-utils
  brightnessctl playerctl power-profiles-daemon lm_sensors pciutils iputils gnome-system-monitor
  grim slurp swappy wl-clipboard cliphist fuzzel xdg-utils xdg-user-dirs ffmpeg ffmpegthumbnailer mpv
  # terminál a nástroje
  zsh kitty alacritty rofi yazi neovim btop fastfetch cava ripgrep fd fzf zoxide jq 7zip mpc acpi cmatrix
  # soubory a vzhled
  thunar thunar-archive-plugin thunar-volman tumbler gvfs file-roller papirus-icon-theme gnome-themes-extra
  noto-fonts noto-fonts-emoji
  # přihlašovací obrazovka (SDDM běží na X11, proto xorg-server)
  sddm qt6-declarative qt6-svg xorg-server
  flatpak pacman-contrib zram-generator
)
# procesor a grafika: mikrokód, video přes GPU (Brave, mpv), Vulkan pro hry, hlídání teploty
case $(awk -F': ' '/vendor_id/{print $2; exit}' /proc/cpuinfo) in
  GenuineIntel) CORE+=(intel-ucode intel-media-driver vulkan-intel thermald) ;;
  AuthenticAMD) CORE+=(amd-ucode libva-mesa-driver vulkan-radeon) ;;
esac
AUR_CORE=(brave-bin vscodium-bin mpvpaper tty-clock caelestia-shell caelestia-cli)

declare -A MAP
if [[ -f $SYS/pkgmap.txt ]]; then
  while IFS='=' read -r k v; do [[ -z $k || $k == \#* ]] && continue; MAP["$k"]="$v"; done < "$SYS/pkgmap.txt"
fi
mapfile -t REPOPKGS < <(pacman -Slq 2>/dev/null)
declare -A INREPO; for p in "${REPOPKGS[@]}"; do INREPO["$p"]=1; done
PAC=() AUR=()
add() { local t; for t in "$@"; do
  if [[ $t == aur:* ]]; then AUR+=("${t#aur:}")
  elif [[ -n ${INREPO[$t]:-} ]]; then PAC+=("$t")
  else AUR+=("$t"); fi
done; }
add "${CORE[@]}"; AUR+=("${AUR_CORE[@]}")
# ostatní programy z Fedory: jen ty se známým překladem v pkgmap.txt, zbytek do seznamu k ruční kontrole
: > "$UNRES"
if [[ -f $SYS/packages.txt ]]; then
  while IFS= read -r p; do
    [[ -z $p ]] && continue
    if [[ -n ${MAP[$p]+x} ]]; then
      [[ ${MAP[$p]} == "-" ]] && continue
      add ${MAP[$p]}
    else
      echo "$p" >> "$UNRES"
    fi
  done < "$SYS/packages.txt"
fi
mapfile -t PAC < <(printf '%s\n' "${PAC[@]}" | sort -u)
mapfile -t AUR < <(printf '%s\n' "${AUR[@]}" | sort -u | grep -vxF -f <(printf '%s\n' "${PAC[@]}"))
ok "z repozitářů: ${#PAC[@]}, z AUR: ${#AUR[@]} (${AUR[*]})"
if ! sudo pacman -S --needed --noconfirm "${PAC[@]}"; then
  warn "hromadná instalace selhala, zkouším po jednom"
  for p in "${PAC[@]}"; do sudo pacman -S --needed --noconfirm "$p" >/dev/null 2>&1 || { echo "pacman: $p" >> "$UNRES"; warn "nejde nainstalovat: $p"; }; done
fi
if have paru; then
  for p in "${AUR[@]}"; do
    pacman -Qq "$p" >/dev/null 2>&1 && continue
    paru -S --needed --noconfirm --skipreview "$p" >/dev/null 2>&1 && ok "AUR: $p" || { echo "aur: $p" >> "$UNRES"; warn "AUR: $p se nepovedl"; }
  done
fi
ok "Fedora balíčky bez překladu (většinou knihovny, nic se neinstaluje): $(grep -vc '^\(pacman\|aur\):' "$UNRES") v $UNRES"

###############################################################################
step "4/13 úpravy dotfiles pro Arch (zůstávají funkční i na Fedoře)"
python3 - "$DOT" <<'PY'
import os, re, sys
D = sys.argv[1]
def edit(rel, pairs, note):
    p = os.path.join(D, rel)
    if not os.path.exists(p):
        return
    s = open(p, encoding="utf-8").read()
    new = s
    for a, b in pairs:
        if a in new and not (b and b in new):   # opakované spuštění nic nezdvojí
            new = new.replace(a, b)
    if new != s:
        open(p, "w", encoding="utf-8").write(new)
        print(f"   {rel}: {note}")
# polkit agent: Fedora ho má v /usr/libexec, Arch v /usr/bin
edit("hypr/.config/hypr/hyprland.lua",
     [('hl.exec_cmd("/usr/libexec/lxqt-policykit-agent")',
       'hl.exec_cmd("/usr/libexec/lxqt-policykit-agent || /usr/bin/lxqt-policykit-agent")')], "polkit agent na Fedoře i Archu")
edit("hypr/.config/hypr/hyprland.conf",
     [("exec-once = /usr/libexec/lxqt-policykit-agent\n",
       "exec-once = /usr/libexec/lxqt-policykit-agent || /usr/bin/lxqt-policykit-agent\n")], "polkit agent na Fedoře i Archu")
# zsh: aktualizace systému podle distribuce, Brave se na Archu jmenuje "brave"
edit("zsh/.zshrc", [
    ("alias update='sudo dnf update -y && sudo dnf upgrade -y'",
     "if command -v pacman >/dev/null; then alias update='paru -Syu'; else alias update='sudo dnf update -y && sudo dnf upgrade -y'; fi"),
    ('alias brave="nohup brave-browser > /dev/null 2>&1 & disown"',
     'alias brave="nohup $(command -v brave-browser || command -v brave) > /dev/null 2>&1 & disown"'),
    ("alias brave-browser='brave-browser --disable-gpu-compositing'\n", ""),
], "update/brave pro Arch, bez starého --disable-gpu-compositing")
# Brave: volba --disable-gpu-compositing už není potřeba (zbytečně zatěžovala procesor)
p = os.path.join(D, "local/.config/brave-flags.conf")
if os.path.exists(p):
    lines = [l for l in open(p).read().splitlines() if "disable-gpu-compositing" not in l]
    open(p, "w").write("\n".join(lines) + ("\n" if lines else ""))
for rel in ("local/.local/share/applications/brave-browser.desktop",
            "local/.local/share/applications/com.brave.Browser.desktop"):
    p = os.path.join(D, rel)
    if os.path.exists(p) and "brave-browser-stable" in open(p).read():
        os.remove(p)   # jen Fedora přepis kvůli staré volbě; na Archu by Brave nespustil
        print(f"   {rel}: odstraněn (Brave používá svůj vlastní spouštěč)")
# instalátor přihlašovací obrazovky: sddm přes pacman
edit("login/sddm-install.sh", [
    ("rpm -q sddm >/dev/null 2>&1 || sudo dnf install -y sddm\nrpm -q sddm | sed 's/^/   /'",
     "if command -v pacman >/dev/null; then pacman -Q sddm >/dev/null 2>&1 || sudo pacman -S --needed --noconfirm sddm; pacman -Q sddm | sed 's/^/   /'\n"
     "else rpm -q sddm >/dev/null 2>&1 || sudo dnf install -y sddm; rpm -q sddm | sed 's/^/   /'; fi")], "sddm přes pacman")
PY

###############################################################################
step "5/13 oh-my-zsh a propojení konfigurací (stow)"
if [[ ! -d ~/.oh-my-zsh ]]; then
  RUNZSH=no CHSH=no KEEP_ZSHRC=yes sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" >/dev/null && ok "oh-my-zsh"
fi
ZP=~/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting
[[ -d $ZP ]] || git clone -q --depth 1 https://github.com/zsh-users/zsh-syntax-highlighting.git "$ZP" && ok "plugin zsh-syntax-highlighting"
PKGS=(apps bin btop caelestia cava fastfetch fonts git gtk hypr hyprpaper icons kde-colors kitty local nvim rofi
      superfile swaylock vscodium wallpapers wezterm yazi zsh)
# Caelestia si do ~/.config/caelestia zapisuje i vlastní věci: složka musí být skutečná, ne odkaz do dotfiles
mkdir -p ~/.config/caelestia
cd "$DOT" || exit 1
moved=0
for pkg in "${PKGS[@]}"; do
  [[ -d $pkg ]] || continue
  # co by stow nepropojil (soubor tam už je, třeba výchozí config Hyprlandu), přesunout do zálohy
  while IFS= read -r -d '' f; do
    rel=${f#"$pkg"/}; t="$HOME/$rel"
    if [[ -e $t || -L $t ]] && [[ $(readlink -f "$t") != "$(readlink -f "$f")" ]]; then
      mkdir -p "$BK/$(dirname "$rel")"; mv "$t" "$BK/$rel"; moved=$((moved + 1))
    fi
  done < <(find "$pkg" \( -type f -o -type l \) -print0)
  stow -R "$pkg" 2>&1 | sed 's/^/   /' || warn "stow: $pkg"
done
ok "propojeno ${#PKGS[@]} balíčků$( ((moved)) && echo ", $moved původních souborů přesunuto do $BK")"
fc-cache -f >/dev/null
update-desktop-database ~/.local/share/applications 2>/dev/null
chmod +x ~/.local/bin/* ~/.config/hypr/scripts/* 2>/dev/null
[[ $(getent passwd "$USER" | cut -d: -f7) == */zsh ]] || { sudo chsh -s "$(command -v zsh)" "$USER" && ok "výchozí shell: zsh"; }

###############################################################################
step "6/13 vzhled: tmavé GTK, ikony Papirus (šedé složky), Thunar"
gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark' 2>/dev/null
gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita-dark' 2>/dev/null
gsettings set org.gnome.desktop.interface icon-theme 'Papirus-Dark' 2>/dev/null
gsettings set org.gnome.desktop.interface cursor-theme 'Kitty' 2>/dev/null
gsettings set org.gnome.desktop.wm.preferences button-layout ':' 2>/dev/null   # okna bez tlačítek zavřít/minimalizovat
ok "GTK: Adwaita-dark, Papirus-Dark"
TMP=$(mktemp)
if curl -fsSL https://raw.githubusercontent.com/PapirusDevelopmentTeam/papirus-folders/master/papirus-folders -o "$TMP"; then
  sudo bash "$TMP" -C grey --theme Papirus-Dark >/dev/null 2>&1 && ok "šedé složky"
fi
rm -f "$TMP"
X=~/.config/xfce4/xfconf/xfce-perchannel-xml
mkdir -p "$X"
[[ -f $DOT/thunar/thunar.xml ]] && cp "$DOT/thunar/thunar.xml" "$X/thunar.xml" && ok "Thunar: nastavení (lišta, zobrazení, velikost ikon)"
xdg-mime default thunar.desktop inode/directory 2>/dev/null && ok "Thunar je výchozí správce souborů"
xdg-user-dirs-update 2>/dev/null

###############################################################################
step "7/13 přihlašovací obrazovka SDDM (téma island)"
sudo localectl set-x11-keymap cz 2>/dev/null && ok "klávesnice na přihlášení: cz"
if ask "Nainstalovat téma 'island' a zapnout SDDM? (otevře se náhled, zavřeš ho Super+Q; na otázku o přepnutí odpověz a)"; then
  # jiný správce přihlášení vypnout, ať se nepere s SDDM
  for dm in gdm lightdm ly greetd lxdm; do systemctl is-enabled "$dm" >/dev/null 2>&1 && sudo systemctl disable "$dm" && ok "vypnut $dm"; done
  bash "$DOT/login/install.sh" || warn "instalace přihlašovací obrazovky hlásila chybu (viz výše)"
  sudo systemctl enable sddm >/dev/null 2>&1
fi

###############################################################################
step "8/13 systémové drobnosti"
# pomocníci, které volají zkratky bez hesla: uvolnění cache, Gaming (Super+G)
for h in island-drop-caches island-gaming; do
  [[ -f $SYS/usr-local-bin/$h ]] || continue
  sudo install -Dm755 "$SYS/usr-local-bin/$h" "/usr/local/bin/$h"
  printf '%s ALL=(root) NOPASSWD: /usr/local/bin/%s\n' "$USER" "$h" > /tmp/island-sudoers
  if sudo visudo -cf /tmp/island-sudoers >/dev/null; then
    sudo install -Dm440 /tmp/island-sudoers "/etc/sudoers.d/$h" && ok "$h: bez hesla"
  fi
  rm -f /tmp/island-sudoers
done
# kamera jen přes cam-on (sudo)
if [[ -f $SYS/etc/modprobe.d/island-camera.conf ]]; then
  sudo install -Dm644 "$SYS/etc/modprobe.d/island-camera.conf" /etc/modprobe.d/island-camera.conf && ok "kamera po startu vypnutá (zapnutí: cam-on)"
fi
# klíčenka se odemyká heslem při přihlášení (jinak okno "Authentication required")
F=/etc/pam.d/sddm
if [[ -f $F ]] && ! grep -qE '^\s*-?auth\s+optional\s+pam_gnome_keyring.so' "$F"; then
  sudo cp "$F" "$F.bak-keyring"
  sudo python3 - "$F" <<'PY'
import sys
p = sys.argv[1]; lines = open(p).read().rstrip("\n").split("\n")
last = max((i for i, l in enumerate(lines) if l.lstrip("-").startswith("auth")), default=len(lines) - 1)
lines.insert(last + 1, "-auth       optional    pam_gnome_keyring.so")
if not any("pam_gnome_keyring" in l and l.lstrip("-").startswith("session") for l in lines):
    lines.append("-session    optional    pam_gnome_keyring.so auto_start")
open(p, "w").write("\n".join(lines) + "\n")
PY
  ok "klíčenka se odemyká při přihlášení"
else
  ok "klíčenka: PAM už odemykání má"
fi
[[ -f /etc/pam.d/hyprlock ]] && ok "zámek obrazovky: PAM z balíčku hyprlock" || warn "/etc/pam.d/hyprlock chybí, přeinstaluj hyprlock"

###############################################################################
step "9/13 Flatpak aplikace (Spotify, Vesktop, OBS…) a Spicetify"
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
if [[ -f $SYS/flatpaks.txt ]]; then
  while IFS= read -r app; do
    [[ -z $app ]] && continue
    flatpak info "$app" >/dev/null 2>&1 && continue
    flatpak install -y --noninteractive flathub "$app" >/dev/null 2>&1 && ok "flatpak: $app" || warn "flatpak: $app se nepovedl"
  done < "$SYS/flatpaks.txt"
fi
# téma OBS
O=~/.var/app/com.obsproject.Studio/config/obs-studio/themes
[[ -f $DOT/obs/Island.ovt ]] && mkdir -p "$O" && cp "$DOT/obs/Island.ovt" "$O/" && ok "OBS: téma Island (v OBS: Settings → Appearance)"
SP=/var/lib/flatpak/app/com.spotify.Client/x86_64/stable/active/files/extra/share/spotify
if [[ -d $SP ]]; then
  [[ -x ~/.spicetify/spicetify ]] || curl -fsSL https://raw.githubusercontent.com/spicetify/cli/main/install.sh | sh >/dev/null 2>&1
  sudo chmod a+wr "$SP"; sudo chmod a+wr -R "$SP/Apps"
  mkdir -p ~/src ~/.config/spicetify/Themes
  [[ -d ~/src/spicetify-themes ]] || git clone -q --depth 1 https://github.com/spicetify/spicetify-themes.git ~/src/spicetify-themes
  cp -r ~/src/spicetify-themes/text ~/.config/spicetify/Themes/
  S=~/.spicetify/spicetify
  "$S" config spotify_path "$SP" >/dev/null
  "$S" config prefs_path "$HOME/.var/app/com.spotify.Client/config/spotify/prefs" >/dev/null
  "$S" config current_theme text color_scheme Spotify >/dev/null
  if [[ -f ~/.var/app/com.spotify.Client/config/spotify/prefs ]]; then "$S" backup apply >/dev/null 2>&1 && ok "Spicetify použit"
  else warn "Spotify jednou spusť a přihlas se, pak:  ~/.spicetify/spicetify backup apply"; fi
fi

###############################################################################
step "10/13 VSCodium rozšíření"
if have codium && [[ -f $SYS/vscodium-extensions.txt ]]; then
  have_ext=$(codium --list-extensions 2>/dev/null | tr 'A-Z' 'a-z')
  n=0; f=0
  while IFS= read -r e; do
    [[ -z $e ]] && continue
    grep -qxF "${e,,}" <<<"$have_ext" && continue
    codium --install-extension "$e" >/dev/null 2>&1 && n=$((n + 1)) || { f=$((f + 1)); echo "vscodium: $e" >> "$UNRES"; }
  done < "$SYS/vscodium-extensions.txt"
  ok "nainstalováno $n rozšíření$( ((f)) && echo ", $f není v Open VSX (seznam v $UNRES)")"
else
  warn "VSCodium chybí (AUR vscodium-bin), rozšíření přeskočena"
fi

###############################################################################
step "11/13 služby"
sudo systemctl enable --now bluetooth >/dev/null 2>&1 && ok "Bluetooth"
sudo systemctl enable --now power-profiles-daemon >/dev/null 2>&1 && ok "režimy výkonu (panel)"
sudo systemctl enable --now fstrim.timer >/dev/null 2>&1
systemctl is-enabled --quiet thermald 2>/dev/null || { pacman -Q thermald >/dev/null 2>&1 && sudo systemctl enable --now thermald >/dev/null 2>&1 && ok "thermald (teplota procesoru)"; }
sudo systemctl disable NetworkManager-wait-online.service >/dev/null 2>&1   # start nečeká na Wi-Fi (o 3–4 s rychlejší)
systemctl --user enable --now pipewire-pulse.socket wireplumber >/dev/null 2>&1
if systemctl is-active --quiet NetworkManager; then
  ok "NetworkManager běží"
else
  OTHER=$(for s in iwd systemd-networkd dhcpcd connman; do systemctl is-enabled "$s" >/dev/null 2>&1 && echo "$s"; done | xargs)
  echo "   Caelestia (Wi-Fi, Bluetooth, VPN) potřebuje NetworkManager. Teď síť spravuje: ${OTHER:-nic}"
  if ask "Přepnout správu sítě na NetworkManager? (Wi-Fi se na chvíli odpojí, pak se připojíš z panelu nebo: nmtui)"; then
    for s in $OTHER; do sudo systemctl disable --now "$s" >/dev/null 2>&1; done
    sudo systemctl enable --now NetworkManager && ok "NetworkManager zapnutý"
  else
    warn "NetworkManager nezapnutý, Wi-Fi v Caelestii nebude fungovat"
  fi
fi

###############################################################################
step "12/13 optimalizace (stejné jako arch-tune.sh)"
# zram: komprimovaný swap v RAM + nastavení jádra pro něj
if [[ ! -f /etc/systemd/zram-generator.conf ]]; then
  printf '[zram0]\nzram-size = min(ram / 2, 8192)\ncompression-algorithm = zstd\n' | sudo tee /etc/systemd/zram-generator.conf >/dev/null
  sudo systemctl daemon-reload; sudo systemctl start systemd-zram-setup@zram0 2>/dev/null
fi
[[ -f /etc/sysctl.d/99-zram.conf ]] || printf 'vm.swappiness = 180\nvm.watermark_boost_factor = 0\nvm.watermark_scale_factor = 125\nvm.page-cluster = 0\n' | sudo tee /etc/sysctl.d/99-zram.conf >/dev/null
sudo sysctl -q --system
ok "zram + paměť nastavená pro zram"
# watchdog k ničemu na notebooku, zdržuje vypínání
[[ -f /etc/modprobe.d/nowatchdog.conf ]] || printf 'blacklist iTCO_wdt\nblacklist iTCO_vendor_support\n' | sudo tee /etc/modprobe.d/nowatchdog.conf >/dev/null
# staré balíčky: nechat jednu verzi, mazat každý týden
sudo mkdir -p /etc/systemd/system/paccache.service.d
printf '[Service]\nEnvironment=PACCACHE_ARGS=-rk1\n' | sudo tee /etc/systemd/system/paccache.service.d/keep1.conf >/dev/null
sudo systemctl daemon-reload; sudo systemctl enable --now paccache.timer >/dev/null 2>&1
# Docker (když je): spustit až při použití
if systemctl is-enabled --quiet docker.service 2>/dev/null; then
  sudo systemctl disable --now docker.service containerd.service >/dev/null 2>&1; sudo systemctl enable docker.socket >/dev/null 2>&1
fi
# nabídka zavaděče bez čekání (systemd-boot)
LC=/boot/loader/loader.conf
if sudo test -f "$LC" && ! sudo grep -qE '^\s*timeout\s+0\s*$' "$LC"; then
  sudo sed -i -E '/^\s*timeout/d' "$LC"; echo "timeout 0" | sudo tee -a "$LC" >/dev/null
fi
ok "watchdog vypnutý, úklid balíčků, rychlejší start"

###############################################################################
step "13/13 Caelestia shell a kontrola"
hyprctl reload >/dev/null 2>&1
pgrep -f 'workspaces.py daemon' >/dev/null || (setsid python3 ~/.config/hypr/scripts/workspaces.py daemon >/dev/null 2>&1 &)
# instalace a úpravy Caelestie (tlačítko disku, karta GPU, panely), tapeta, barvy; spustí ji
if [[ -f $SYS/caelestia/caelestia-mix.sh ]]; then
  bash "$SYS/caelestia/caelestia-mix.sh" || warn "Caelestia: instalace hlásila chybu (výpis výše)"
else
  warn "chybí $SYS/caelestia/caelestia-mix.sh"
fi
V=$(hyprctl -j version 2>/dev/null | grep -o '"tag": *"[^"]*"' | grep -o 'v[0-9.]*')
ok "Hyprland ${V:-?}"
E=$(hyprctl configerrors 2>/dev/null | grep -v '^$')
if [[ -z $E || $E == "no errors" ]]; then ok "config Hyprlandu bez chyb"; else warn "config: $(echo "$E" | head -3 | tr '\n' ' ')"; fi
sleep 2
for c in "pgrep -f 'qs -c caelestia'" "command -v brave" "command -v codium" "command -v thunar" "command -v help"; do
  if eval "$c" >/dev/null 2>&1; then ok "OK  $c"; else warn "nefunguje: $c"; fi
done

echo
echo "================================================================"
echo " Hotovo. RESTARTUJ počítač (přihlásíš se přes nové SDDM, vyber Hyprland)."
echo "================================================================"
echo " Ručně zbývá (není v dotfiles záměrně):"
echo "   - SSH/GPG klíče, VPN profily (~/.local/share/island-vpn), heslo k OBS (~/.config/obs-rec/password)"
echo "   - gh auth login   (GitHub)"
echo "   - Vesktop: Vencord → Themes → Online: https://refact0r.github.io/system24/build/system24.css"
echo "   - XAMPP na Archu není; místo něj: sudo pacman -S apache php php-apache mariadb"
echo "   - virt-manager a ArtCraft (náhrady Adobe):  bash ~/dotfiles/system/arch-extras.sh"
echo "   - přehled zkratek, aliasů a příkazů:  help"
[[ -d $BK ]] && echo "   - původní soubory, které překážely: $BK"
echo "   - balíčky z Fedory bez překladu (většinou knihovny): $UNRES"
if ((${#WARNINGS[@]})); then
  echo; echo " Upozornění během obnovy:"; printf '   - %s\n' "${WARNINGS[@]}"
fi
if git -C "$DOT" status --porcelain | grep -q .; then
  echo
  if ask "Odeslat úpravy dotfiles pro Arch na GitHub?"; then
    git -C "$DOT" add -A && git -C "$DOT" commit -qm "Arch: obnova na novém počítači" \
      && git -C "$DOT" push && ok "odesláno" || warn "push se nepovedl (gh auth login a pak: cd ~/dotfiles && git push)"
  fi
fi
echo " Celý výpis: $LOG"
