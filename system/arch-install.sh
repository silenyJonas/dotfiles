#!/usr/bin/env bash
# arch-install.sh – spusť na čerstvém Archu jako OBYČNÝ uživatel (ne root).
#
#   bash arch-install.sh /cesta/k/zaloze        # složka vytvořená backup-fedora.sh
#
# Předpoklady: nainstalovaný základní Arch (archinstall stačí), síť, uživatel s sudo,
#              ideálně se STEJNÝM jménem (joncl) – v hyprland.conf jsou cesty /home/joncl/.
#
# Skript je opakovatelný (idempotentní) – když něco spadne, oprav a spusť znovu.

set -uo pipefail

BACKUP="${1:-}"
DOT="$HOME/dotfiles"
SYS="$DOT/system"
UNRESOLVED="$HOME/arch-unresolved.txt"
STOW_BK="$HOME/.pre-stow-backup"

say()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }
ask()  { read -r -p "$1 [y/N] " a; [[ $a == [yYaA]* ]]; }

[[ $EUID -eq 0 ]] && { echo "Nespouštěj jako root."; exit 1; }
[[ $USER != joncl ]] && warn "Uživatel není 'joncl' – cesty /home/joncl v configu budou potřeba přepsat: grep -rl /home/joncl ~/dotfiles"

###############################################################################
say "1) Základ: aktualizace, git, stow, build nástroje"
sudo pacman -Syu --needed --noconfirm base-devel git stow github-cli zsh curl rsync zstd unzip openssh

if ! have paru; then
  say "   Instaluji paru (AUR helper)"
  tmp="$(mktemp -d)"
  git clone https://aur.archlinux.org/paru-bin.git "$tmp/paru-bin" \
    && (cd "$tmp/paru-bin" && makepkg -si --noconfirm)
  rm -rf "$tmp"
fi

###############################################################################
say "2) Obnova soukromých dat ze zálohy (ssh klíče hned, ať jde klonovat privátní repa)"
if [[ -n $BACKUP && -d $BACKUP ]]; then
  [[ -f $BACKUP/SHA256SUMS ]] && (cd "$BACKUP" && sha256sum -c SHA256SUMS --quiet) || warn "Kontrolní součty nesedí/nejsou!"
  if [[ -f $BACKUP/home-private.tar.zst ]]; then
    # Vytáhne všechno; existující soubory přepíše (jen čistý systém, takže OK)
    tar -C "$HOME" -I zstd -xpf "$BACKUP/home-private.tar.zst" && echo "home-private obnoveno"
    chmod 700 ~/.ssh ~/.gnupg 2>/dev/null; chmod 600 ~/.ssh/* 2>/dev/null
  fi
else
  warn "Záloha nezadána/nenalezena – přeskakuji (spusť později: bash arch-install.sh /cesta)"
fi

###############################################################################
say "3) Dotfiles"
if [[ ! -d $DOT/.git ]]; then
  git clone https://github.com/silenyJonas/dotfiles.git "$DOT"
fi
cd "$DOT" && git pull --ff-only 2>/dev/null
# Pozor: nové soubory z tohoto balíčku (pkgmap.txt, arch-install.sh) patří do $SYS
[[ -f $(dirname "$0")/pkgmap.txt && ! -f $SYS/pkgmap.txt ]] && cp "$(dirname "$0")/pkgmap.txt" "$SYS/"

###############################################################################
say "4) Balíčky: překlad dnf -> pacman/AUR"
declare -A MAP
if [[ -f $SYS/pkgmap.txt ]]; then
  while IFS='=' read -r k v; do
    [[ -z $k || $k == \#* ]] && continue
    MAP["$k"]="$v"
  done < "$SYS/pkgmap.txt"
fi

SKIP_RE='^(fedora-|rpmfusion-|kernel|dnf|rpm|langpacks-|glibc-|selinux-|grub2-|shim-|dracut|anaconda|plymouth|gnome-shell-extension|google-noto-.*-fonts$)'

# Pevný základ pro tvoje prostředí (kdyby chybělo v packages.txt)
CORE=(
  hyprland hypridle hyprlock xdg-desktop-portal-hyprland xdg-desktop-portal-gtk
  waybar rofi swaybg swappy grim slurp wl-clipboard kitty yazi neovim
  python-gobject gtk3 gtk-layer-shell networkmanager bluez bluez-utils
  pipewire pipewire-pulse pipewire-alsa wireplumber pavucontrol playerctl brightnessctl
  polkit polkit-gnome gnome-keyring fprintd
  ffmpeg 7zip jq poppler fd ripgrep fzf zoxide imagemagick btop cava fastfetch
  thunar gvfs tumbler dolphin kate kwrite okular gwenview ark
  papirus-icon-theme noto-fonts noto-fonts-emoji ttf-jetbrains-mono ttf-nerd-fonts-symbols
  sddm qt6-declarative qt6-svg qt6-5compat
  flatpak obs-studio python-pipx
)
PAC=("${CORE[@]}"); AUR=(); : > "$UNRESOLVED"

resolve() {
  local n="$1" target="${MAP[$1]-__none__}" t
  [[ $n =~ $SKIP_RE ]] && return
  if [[ $target == "-" ]]; then return; fi
  if [[ $target != "__none__" ]]; then
    for t in $target; do
      if [[ $t == aur:* ]]; then AUR+=("${t#aur:}"); else PAC+=("$t"); fi
    done
    return
  fi
  if pacman -Si "$n" &>/dev/null;   then PAC+=("$n")
  elif paru -Si "$n" &>/dev/null;   then AUR+=("$n")
  else echo "$n" >> "$UNRESOLVED"; fi
}

if [[ -f $SYS/packages.txt ]]; then
  while IFS= read -r p; do [[ -n $p ]] && resolve "$p"; done < "$SYS/packages.txt"
fi

# Povinné AUR extra: Brave, VSCodium, rofi pokud chybí...
for a in brave-bin vscodium-bin; do AUR+=("$a"); done
mapfile -t PAC < <(printf '%s\n' "${PAC[@]}" | sort -u)
mapfile -t AUR < <(printf '%s\n' "${AUR[@]}" | sort -u)

echo "Oficiální repa: ${#PAC[@]} balíčků, AUR: ${#AUR[@]}, nepřeložené: $(wc -l < "$UNRESOLVED") (viz $UNRESOLVED)"
# Instalace po jednom, aby jeden neexistující balíček nezastavil všechno
sudo pacman -S --needed --noconfirm "${PAC[@]}" 2>/dev/null || {
  warn "Hromadná instalace selhala, zkouším po jednom…"
  for p in "${PAC[@]}"; do sudo pacman -S --needed --noconfirm "$p" || echo "pacman: $p" >> "$UNRESOLVED"; done
}
paru -S --needed --noconfirm "${AUR[@]}" 2>/dev/null || {
  for p in "${AUR[@]}"; do paru -S --needed --noconfirm "$p" || echo "aur: $p" >> "$UNRESOLVED"; done
}

###############################################################################
say "5) Flatpaky (Spotify, Vesktop, …)"
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
[[ -f $SYS/flatpaks.txt ]] && xargs -r -a "$SYS/flatpaks.txt" flatpak install -y flathub

###############################################################################
say "6) oh-my-zsh (před stow, ať nepřepíše .zshrc)"
if [[ ! -d ~/.oh-my-zsh ]]; then
  RUNZSH=no CHSH=no KEEP_ZSHRC=yes sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
fi
# custom pluginy ze zálohy už jsou vytažené v kroku 2

###############################################################################
say "7) Propojení konfigurací (stow). Co překáží, jde do $STOW_BK"
mkdir -p "$STOW_BK"
cd "$DOT" || exit 1
for pkg in */; do
  pkg="${pkg%/}"
  [[ $pkg == system || $pkg == spicetify ]] && continue
  while IFS= read -r -d '' f; do
    rel="${f#"$pkg"/}"; t="$HOME/$rel"
    if [[ -e $t && $(readlink -f "$t") != "$(readlink -f "$f")" ]]; then
      mkdir -p "$STOW_BK/$(dirname "$rel")"; mv "$t" "$STOW_BK/$rel"
    fi
  done < <(find "$pkg" -type f -print0)
  stow -R "$pkg" || warn "stow selhal pro: $pkg"
done
fc-cache -f
update-desktop-database ~/.local/share/applications 2>/dev/null
chmod +x ~/bin/* ~/.local/bin/* ~/.config/hypr/scripts/* ~/.config/waybar/scripts/* 2>/dev/null

###############################################################################
say "8) Shell, služby, skupiny"
[[ $SHELL != */zsh ]] && chsh -s "$(command -v zsh)"
sudo systemctl enable --now NetworkManager bluetooth
sudo systemctl enable fstrim.timer
sudo systemctl enable sddm 2>/dev/null
have docker && { sudo systemctl enable docker; sudo usermod -aG docker "$USER"; }
sudo usermod -aG video,input "$USER"

# Wi-Fi/VPN profily
if [[ -n $BACKUP && -f $BACKUP/etc-private.tar.zst ]]; then
  sudo tar -C / -I zstd -xpf "$BACKUP/etc-private.tar.zst"
  sudo chown -R root:root /etc/NetworkManager/system-connections
  sudo chmod 600 /etc/NetworkManager/system-connections/* 2>/dev/null
  sudo nmcli connection reload
fi

# Zámek obrazovky: na Archu NEKOPÍRUJ Fedora PAM soubor (password-auth tu neexistuje).
# Balíček hyprlock si vlastní /etc/pam.d/hyprlock nese sám.
[[ -f /etc/pam.d/hyprlock ]] || warn "/etc/pam.d/hyprlock chybí – přeinstaluj hyprlock"

# SDDM téma "island"
if [[ -f $DOT/login/install.sh ]] && ask "Nainstalovat SDDM téma 'island' (login/install.sh)? Na otázku o přepnutí z GDM odpověz ne."; then
  bash "$DOT/login/install.sh"
fi
[[ -f $SYS/etc/sddm.conf.d/zz-island.conf ]] && ! [[ -f /etc/sddm.conf.d/zz-island.conf ]] \
  && sudo install -D "$SYS/etc/sddm.conf.d/zz-island.conf" /etc/sddm.conf.d/zz-island.conf

###############################################################################
say "9) Spotify + Spicetify"
SP=/var/lib/flatpak/app/com.spotify.Client/x86_64/stable/active/files/extra/share/spotify
if [[ -d $SP ]]; then
  if [[ ! -x ~/.spicetify/spicetify ]]; then curl -fsSL https://raw.githubusercontent.com/spicetify/cli/main/install.sh | sh; fi
  sudo chmod a+wr "$SP"; sudo chmod a+wr -R "$SP/Apps"
  mkdir -p ~/src ~/.config/spicetify/Themes
  [[ -d ~/src/spicetify-themes ]] || git clone --depth=1 https://github.com/spicetify/spicetify-themes.git ~/src/spicetify-themes
  cp -r ~/src/spicetify-themes/text ~/.config/spicetify/Themes/
  S=~/.spicetify/spicetify
  "$S" config spotify_path "$SP"
  "$S" config prefs_path "$HOME/.var/app/com.spotify.Client/config/spotify/prefs"
  "$S" config current_theme text color_scheme Spotify
  if [[ -f ~/.var/app/com.spotify.Client/config/spotify/prefs ]]; then "$S" backup apply
  else warn "Spotify jednou spusť a přihlas se, pak: ~/.spicetify/spicetify backup apply"; fi
else
  warn "Spotify flatpak nenalezen – přeskočeno"
fi

###############################################################################
say "10) VSCodium rozšíření, cargo/pip nástroje"
if [[ -f $SYS/vscodium-extensions.txt ]] && have codium; then
  xargs -r -n1 -a "$SYS/vscodium-extensions.txt" codium --install-extension
fi
# Arch zakazuje 'pip install --user' (PEP 668) -> pipx
if [[ -f $SYS/pipx.txt ]]; then xargs -r -n1 -a "$SYS/pipx.txt" pipx install; fi
[[ -f $SYS/pip-user.txt ]] && warn "pip balíčky zkontroluj ručně v $SYS/pip-user.txt (pipx install <nástroj>, nebo venv)"
[[ -f $SYS/cargo.txt ]]    && warn "cargo nástroje zkontroluj v $SYS/cargo.txt (většina je v pacman/AUR)"

###############################################################################
say "11) Uživatelská data, XAMPP"
if [[ -n $BACKUP && -f $BACKUP/userdata.tar.zst ]]; then
  ask "Obnovit Documents/Pictures/… z userdata.tar.zst?" && tar -C "$HOME" -I zstd -xpf "$BACKUP/userdata.tar.zst"
fi
if [[ -f $BACKUP/xampp/all-databases.sql ]]; then
cat <<'EOF'

XAMPP na Archu není v oficiálních repozitářích. Doporučený nativní náhrada:
    sudo pacman -S apache php php-apache mariadb phpmyadmin
    sudo mariadb-install-db --user=mysql --basedir=/usr --datadir=/var/lib/mysql
    sudo systemctl enable --now mariadb httpd
    sudo mariadb < /cesta/zaloha/xampp/all-databases.sql
Projekty z xampp/htdocs.tar.zst rozbal do /srv/http (nebo ~/projects a použij `php -S localhost:8000`).
EOF
fi

###############################################################################
say "12) Kontrola"
cat <<EOF

HOTOVO. Zbývá:
  - Nepřeložené balíčky:      cat $UNRESOLVED
  - Co stow přesunul stranou: ls $STOW_BK
  - GPU ovladače (nvidia/mesa/vulkan) a mikrokód (intel-ucode/amd-ucode) nainstaluj dle hardwaru.
  - gh auth login            (GitHub přihlášení)
  - Odhlásit/přihlásit nebo reboot, v SDDM zvolit Hyprland.
  - V Hyprlandu: hyprctl configerrors   (Arch má novější verzi, než měla Fedora – syntaxe se mohla změnit)
  - Zkontroluj monitory v hyprland.conf (HDMI-A-1 …): hyprctl monitors
  - Vesktop: Vencord -> Themes -> Online Themes: https://refact0r.github.io/system24/build/system24.css
  - Barvy Dolphinu: plasma-apply-colorscheme Island
EOF
