#!/usr/bin/env bash
# backup-fedora.sh – spusť na Fedoře PŘED přechodem na Arch.
#
# Použití:  bash backup-fedora.sh /cesta/na/externi/disk
#   WITH_DATA=0 bash backup-fedora.sh /cesta   # bez Documents/Pictures/... (jen konfigurace)
#
# Co dělá:
#   A) VEŘEJNÉ věci (seznamy balíčků, rozšíření, /etc konfigurace bez hesel)
#      ulozi do ~/dotfiles/system/ -> bude to v gitu.
#   B) SOUKROMÉ věci (ssh/gpg klíče, Wi-Fi/VPN, profily aplikací, historie, XAMPP DB)
#      zabalí do tar.zst archivů v cílové složce -> NIKDY do gitu.
#
# Cílový disk dej na ext4/btrfs/exFAT – archivy jsou tar, takže práva se zachovají na čemkoliv.

set -uo pipefail

DOT="$HOME/dotfiles"
SYS="$DOT/system"
OUT="${1:-$HOME/migration-backup}"
WITH_DATA="${WITH_DATA:-1}"

mkdir -p "$SYS/etc" "$OUT"
cd "$HOME" || exit 1

say()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

###############################################################################
# A) VEŘEJNÉ – do ~/dotfiles/system
###############################################################################
say "A1) Seznamy balíčků"
dnf repoquery --userinstalled --queryformat '%{name}\n' 2>/dev/null | sort -u > "$SYS/packages.txt"
dnf copr list 2>/dev/null                                           > "$SYS/copr.txt"
have flatpak && flatpak list --app --columns=application,origin     > "$SYS/flatpaks-with-origin.txt"
have flatpak && flatpak list --app --columns=application            > "$SYS/flatpaks.txt"
have snap    && snap list | awk 'NR>1{print $1}'                    > "$SYS/snaps.txt"
dnf repolist --enabled 2>/dev/null                                  > "$SYS/dnf-repos.txt"

say "A2) pip / pipx / cargo / npm / VSCodium rozšíření"
have pip3  && pip3 list --user --format=freeze 2>/dev/null          > "$SYS/pip-user.txt"
have pipx  && pipx list --short 2>/dev/null                         > "$SYS/pipx.txt"
if have cargo; then
  cargo install --list 2>/dev/null | grep -E '^[A-Za-z0-9_-]+ v' | awk '{print $1}' > "$SYS/cargo.txt"
fi
have npm   && npm ls -g --depth=0 --parseable 2>/dev/null | tail -n +2 | xargs -r -n1 basename > "$SYS/npm-global.txt"
for c in codium vscodium code; do
  if have "$c"; then "$c" --list-extensions > "$SYS/vscodium-extensions.txt" 2>/dev/null; break; fi
done

say "A3) Povolené služby, GNOME/dconf nastavení, ručně instalované věci"
systemctl list-unit-files --state=enabled --type=service --no-legend 2>/dev/null | awk '{print $1}' > "$SYS/services-system.txt"
systemctl --user list-unit-files --state=enabled --no-legend 2>/dev/null | awk '{print $1}'        > "$SYS/services-user.txt"
have dconf && dconf dump / > "$SYS/dconf.ini"
{ echo "# /opt";           ls -1 /opt 2>/dev/null
  echo "# ~/Apps";         ls -1 ~/Apps 2>/dev/null
  echo "# ~/.local/bin";   ls -1 ~/.local/bin 2>/dev/null
  echo "# ~/.cargo/bin";   ls -1 ~/.cargo/bin 2>/dev/null
} > "$SYS/manual-installs.txt"

say "A4) /etc konfigurace bez tajemství"
for f in /etc/pam.d/hyprlock /etc/sddm.conf.d/zz-island.conf /etc/hosts /etc/vconsole.conf \
         /etc/locale.conf /etc/environment /etc/systemd/logind.conf; do
  [[ -f $f ]] && install -D "$f" "$SYS/etc/${f#/etc/}"
done
[[ -d /etc/sddm.conf.d ]]       && sudo cp -r /etc/sddm.conf.d       "$SYS/etc/" 2>/dev/null
[[ -d /etc/udev/rules.d ]]      && sudo cp -r /etc/udev/rules.d      "$SYS/etc/udev-rules.d" 2>/dev/null
[[ -d /etc/systemd/system ]]    && sudo cp -r /etc/systemd/system    "$SYS/etc/systemd-system" 2>/dev/null
sudo chown -R "$USER:" "$SYS/etc" 2>/dev/null
cp ~/.config/spicetify/config-xpui.ini "$DOT/spicetify/" 2>/dev/null

say "A5) Seznam gitových repozitářů v domovském adresáři (a nenacommitované změny!)"
: > "$SYS/git-repos.txt"
while IFS= read -r g; do
  d="$(dirname "$g")"
  url="$(git -C "$d" remote get-url origin 2>/dev/null || echo '-')"
  echo "${d#$HOME/} $url" >> "$SYS/git-repos.txt"
  if [[ -n "$(git -C "$d" status --porcelain 2>/dev/null)" ]]; then warn "Necommitnuté změny: $d"; fi
  if [[ -n "$(git -C "$d" log --branches --not --remotes --oneline 2>/dev/null)" ]]; then warn "Nepushnuté commity: $d"; fi
done < <(find "$HOME" -maxdepth 4 -name .git -not -path '*/.cache/*' -not -path '*/.oh-my-zsh/*' \
                 -not -path '*/.cargo/*' -not -path '*/.local/share/*' -not -path '*/.spicetify/*' 2>/dev/null)

say "A6) Co v ~/.config a ~/.local/share NENÍ v dotfiles (kandidáti na přidání)"
{
  echo "## ~/.config – adresáře, které nejsou symlink do dotfiles"
  for p in ~/.config/*; do [[ -L $p ]] || echo "${p#$HOME/}"; done
  echo; echo "## ~/.local/share"
  for p in ~/.local/share/*; do [[ -L $p ]] || echo "${p#$HOME/}"; done
  echo; echo "## skryté soubory v ~"
  for p in ~/.[A-Za-z]*; do [[ -f $p && ! -L $p ]] && echo "${p#$HOME/}"; done
} > "$OUT/not-in-dotfiles-report.txt"
echo "Report: $OUT/not-in-dotfiles-report.txt (projdi a co chceš, přidej do dotfiles)"

###############################################################################
# B) SOUKROMÉ – tar.zst do $OUT
###############################################################################
say "B1) Databáze z XAMPPu (XAMPP musí běžet: sudo /opt/lampp/lampp start)"
mkdir -p "$OUT/xampp"
if [[ -x /opt/lampp/bin/mysqldump ]]; then
  sudo /opt/lampp/bin/mysqldump -u root --all-databases --routines --events > "$OUT/xampp/all-databases.sql" \
    || warn "mysqldump selhal – spusť XAMPP a zkus znovu (nebo: -u root -p)"
  sudo tar -C /opt/lampp -I 'zstd -T0' -cpf "$OUT/xampp/htdocs.tar.zst" htdocs 2>/dev/null
  sudo tar -C /opt/lampp -I 'zstd -T0' -cpf "$OUT/xampp/etc.tar.zst"   etc    2>/dev/null
  sudo chown -R "$USER:" "$OUT/xampp"
fi

say "B2) Domovský adresář – konfigurace a tajemství"
HOME_PATHS=(
  .ssh .gnupg
  .local/share/keyrings           # hesla z GNOME Keyringu (Wi-Fi, aplikace)
  .local/share/island-vpn         # WireGuard profily Proton VPN
  .oh-my-zsh/custom               # vlastní pluginy/témata
  .zsh_history .bash_history .zshenv .zprofile .p10k.zsh
  .config/BraveSoftware           # Brave profil (záložky, rozšíření, hesla)
  .mozilla                        # Firefox, pokud existuje
  .config/obs-studio
  .config/Postman
  .config/spicetify .spicetify
  .config/VSCodium                # kompletní profil (dotfiles má jen settings/keybindings)
  .config/mpv .config/gh .config/discord .config/vesktop
  .config/fcitx5 .config/ibus .config/gtk-4.0 .config/qt5ct .config/qt6ct .config/kdeglobals
  .config/mimeapps.list .config/user-dirs.dirs .config/monitors.xml
  .config/systemd/user
  .local/share/applications
  .local/share/zoxide .local/share/nvim/site     # zoxide DB
  .local/state/island-panel
  .var/app                        # Flatpak data: Spotify, Vesktop, ...
  Apps                            # Postman, pipes.sh, ...
  .local/bin
  .cargo/bin
)
EXCLUDES=(
  --exclude='.var/app/*/cache' --exclude='.var/app/*/.cache'
  --exclude='*/Cache' --exclude='*/Code Cache' --exclude='*/GPUCache' --exclude='*/ShaderCache'
  --exclude='*/Service Worker/CacheStorage' --exclude='*/CachedData' --exclude='*/blob_storage'
  --exclude='.config/BraveSoftware/*/component_crx_cache'
  --exclude='.var/app/com.spotify.Client/data/*/storage'      # offline cache písní (může být GB)
)
EXISTING=()
for p in "${HOME_PATHS[@]}"; do p="${p%% *}"; [[ -e $p ]] && EXISTING+=("$p"); done
tar -C "$HOME" -I 'zstd -T0' -cpf "$OUT/home-private.tar.zst" --ignore-failed-read "${EXCLUDES[@]}" "${EXISTING[@]}" 2>/dev/null
chmod 600 "$OUT/home-private.tar.zst"

say "B3) Systémová připojení NetworkManageru (Wi-Fi hesla, VPN) a /etc"
sudo tar -C / -I 'zstd -T0' -cpf "$OUT/etc-private.tar.zst" --ignore-failed-read \
  etc/NetworkManager/system-connections 2>/dev/null
sudo chown "$USER:" "$OUT/etc-private.tar.zst"; chmod 600 "$OUT/etc-private.tar.zst"

if [[ $WITH_DATA == 1 ]]; then
  say "B4) Uživatelská data (Documents, Pictures, Downloads, Music, Videos, Desktop, Projects)"
  DATA=()
  for d in Documents Pictures Downloads Music Videos Desktop Projects Projekty projects work dev src repos Public Templates; do
    [[ -d $d ]] && DATA+=("$d")
  done
  tar -C "$HOME" -I 'zstd -T0' -cpf "$OUT/userdata.tar.zst" --exclude='node_modules' --exclude='.git/objects/pack/*.tmp' \
      --exclude='*/vendor' --exclude='*/.venv' --exclude='*/target' "${DATA[@]}" 2>/dev/null
fi

say "C) Automatické kontroly na závěr"
grep -rniE "token|password|passwd|secret|api_key|privatekey" "$DOT" --exclude-dir=.git -l 2>/dev/null | head -20 \
  | sed 's/^/ Možné tajemství v dotfiles: /'

cp "$0" "$OUT/" 2>/dev/null
( cd "$OUT" && sha256sum *.tar.zst xampp/* 2>/dev/null > SHA256SUMS )
du -sh "$OUT"/* 2>/dev/null

cat <<EOF

HOTOVO.
  1) cd ~/dotfiles && git add . && git commit -m "pred prechodem na Arch" && git push
  2) $OUT zkopíruj NA EXTERNÍ DISK (home-private.tar.zst obsahuje ssh klíče a hesla -> nikam do cloudu nešifrované)
  3) Ověř, že disk obsahuje: home-private.tar.zst, etc-private.tar.zst, xampp/, userdata.tar.zst, SHA256SUMS
  4) Před instalací Archu si ještě ručně: odhlas se z účtů, které mají vázání na zařízení (Brave Sync zapni, 2FA kódy, atd.)
EOF
