#!/usr/bin/env bash
# Arch: virt-manager (virtuální počítače) + sada ArtCraft (zdarma náhrady Adobe z github.com/storytold)
#   photo  PhotoCraft   ~ Photoshop        film    FilmCraft    ~ Premiere Pro
#   vector VectorCraft  ~ Illustrator      effect  EffectCraft  ~ After Effects
#   light  LightCraft   ~ Lightroom        design  DesignCraft  ~ InDesign
#   pdf    PdfCraft     ~ Acrobat
#
#   bash ~/Downloads/arch-extras.sh                 všechno (virt-manager + všech 7 aplikací)
#   bash ~/Downloads/arch-extras.sh virt            jen virt-manager
#   bash ~/Downloads/arch-extras.sh craft           jen ArtCraft (všech 7)
#   bash ~/Downloads/arch-extras.sh photo film      jen vybrané aplikace
#   bash ~/Downloads/arch-extras.sh --remove photo  odinstalovat (bez názvu = všech 7)
# Aktualizace ArtCraft: spusť znovu (stáhne nejnovější verze).
#
# Aplikace vydávají balíčky jen pro Fedoru/Ubuntu (.rpm/.deb), proto z nich skript poskládá
# normální pacman balíček (photocraft-bin…): jde odinstalovat přes pacman a nic nezůstane rozházené.
set -uo pipefail
have() { command -v "$1" >/dev/null 2>&1; }
[[ $EUID -eq 0 ]] && { echo "Spusť jako svůj uživatel (ne sudo)."; exit 1; }
have pacman || { echo "Tohle je skript pro Arch."; exit 1; }

declare -A REPO=([photo]=photocraft [vector]=vectorcraft [film]=filmcraft [effect]=effectcraft
                 [light]=lightcraft [design]=designcraft [pdf]=pdfcraft)
ORDER=(photo film vector effect light design pdf)

REMOVE=0; DO_VIRT=0; SEL=()
[[ ${1:-} == --remove ]] && { REMOVE=1; shift; }
if [[ $# -eq 0 ]]; then ((REMOVE)) && SEL=("${ORDER[@]}") || { DO_VIRT=1; SEL=("${ORDER[@]}"); }
fi
for a in "$@"; do
  case $a in
    virt) DO_VIRT=1 ;;
    craft) SEL+=("${ORDER[@]}") ;;
    *) [[ -n ${REPO[$a]:-} ]] || { echo "Neznámé: $a (možnosti: virt craft ${ORDER[*]})"; exit 1; }; SEL+=("$a") ;;
  esac
done

if ((REMOVE)); then
  PK=(); for k in "${SEL[@]}"; do pacman -Q "${REPO[$k]}-bin" >/dev/null 2>&1 && PK+=("${REPO[$k]}-bin"); done
  ((${#PK[@]})) && sudo pacman -Rns --noconfirm "${PK[@]}" || echo "Nic z toho není nainstalované."
  exit 0
fi
sudo -v || exit 1

###############################################################################
if ((DO_VIRT)); then
  echo "== virt-manager"
  [[ -e /dev/kvm ]] || echo "   ! /dev/kvm chybí: zapni v BIOSu virtualizaci (Intel VT-x), jinak budou virtuály extrémně pomalé"
  sudo pacman -S --needed --noconfirm virt-manager qemu-desktop libvirt dnsmasq nftables edk2-ovmf swtpm virt-viewer || exit 1
  sudo systemctl enable --now libvirtd.service >/dev/null 2>&1 && echo "   služba libvirtd běží"
  sudo usermod -aG libvirt,kvm "$USER" && echo "   $USER přidán do skupin libvirt a kvm (platí po novém přihlášení)"
  # výchozí síť pro virtuály (NAT, internet z hosta)
  sudo virsh net-info default >/dev/null 2>&1 || sudo virsh net-define /usr/share/libvirt/networks/default.xml >/dev/null
  sudo virsh net-autostart default >/dev/null 2>&1
  sudo virsh net-start default >/dev/null 2>&1
  sudo virsh net-info default 2>/dev/null | grep -q 'Active: *yes' && echo "   síť 'default' aktivní" || echo "   ! síť 'default' se nespustila: sudo virsh net-start default"
  echo
fi

###############################################################################
((${#SEL[@]})) || exit 0
mapfile -t SEL < <(printf '%s\n' "${SEL[@]}" | awk '!s[$0]++')
echo "== ArtCraft: knihovny, které aplikace potřebují"
sudo pacman -S --needed --noconfirm base-devel libarchive webkit2gtk-4.1 gtk3 libayatana-appindicator \
  librsvg gst-plugins-base gst-plugins-good gst-libav ffmpeg fuse2 >/dev/null || echo "   ! některé knihovny se nenainstalovaly"
sudo pacman -Fy >/dev/null 2>&1   # databáze souborů: kdyby chyběla knihovna, najde se balíček, který ji má

ARCH=$(uname -m)
WORK=$(mktemp -d); trap 'rm -rf "$WORK"' EXIT
echo "== ArtCraft: stahování a instalace"
for k in "${SEL[@]}"; do
  r=${REPO[$k]}
  json=$(curl -fsSL "https://api.github.com/repos/storytold/$r/releases/latest") || { echo "   $r: GitHub neodpověděl, přeskočeno"; continue; }
  read -r tag kind url sums < <(python3 -c '
import json, re, sys
d = json.loads(sys.stdin.read()); arch = sys.argv[1]
deb = {"x86_64": "amd64", "aarch64": "arm64"}.get(arch, arch)
a = {x["name"]: x["browser_download_url"] for x in d.get("assets", [])}
def pick(pred):
    return next((u for n, u in a.items() if pred(n)), None)
cand = [("appimage", pick(lambda n: n.lower().endswith(".appimage") and (arch in n or deb in n))),
        ("deb",      pick(lambda n: n.endswith(".deb") and (deb in n or arch in n))),
        ("rpm",      pick(lambda n: n.endswith(".rpm") and arch in n)),
        ("tar",      pick(lambda n: re.search(r"linux.*\.(tar\.gz|tgz|tar\.xz)$", n, re.I) and (arch in n or deb in n)))]
# .deb/.rpm první: obsahují .desktop soubor i ikony; AppImage jen když nic jiného není
order = {"deb": 0, "rpm": 1, "appimage": 2, "tar": 3}
cand = sorted([c for c in cand if c[1]], key=lambda c: order[c[0]])
kind, url = cand[0] if cand else ("-", "-")
sums = pick(lambda n: n.upper().startswith("SHA256SUMS") or n.lower().endswith("sha256sums.txt")) or "-"
print(d.get("tag_name", "0"), kind, url, sums)' "$ARCH" <<<"$json")
  [[ $kind == - ]] && { echo "   $r $tag: žádný balíček pro Linux $ARCH, přeskočeno"; continue; }
  ver=$(sed 's/^[vV]//; s/[^A-Za-z0-9.+]/_/g' <<<"$tag")
  if pacman -Q "$r-bin" 2>/dev/null | grep -qx "$r-bin $ver-1"; then echo "   $r $tag: už nainstalováno"; continue; fi

  d="$WORK/$r"; mkdir -p "$d"; f="$d/$(basename "$url")"
  curl -fsSL -o "$f" "$url" || { echo "   $r: stahování selhalo"; continue; }
  if [[ $sums != - ]] && curl -fsSL -o "$d/sums" "$sums"; then
    want=$(grep -F "$(basename "$f")" "$d/sums" | awk '{print $1}' | head -1)
    if [[ -n $want && $want != "$(sha256sum "$f" | awk '{print $1}')" ]]; then echo "   $r: KONTROLNÍ SOUČET NESEDÍ, přeskočeno"; continue; fi
  fi

  # pacman balíček z .deb / .rpm / AppImage
  cat > "$d/PKGBUILD" <<EOF
pkgname=$r-bin
pkgver=$ver
pkgrel=1
pkgdesc="$r (ArtCraft, github.com/storytold/$r), přebaleno z $kind"
arch=('$ARCH')
url="https://github.com/storytold/$r"
license=('custom')
provides=('$r')
conflicts=('$r')
options=('!strip' '!debug')
source=('$(basename "$f")')
noextract=('$(basename "$f")')
sha256sums=('SKIP')
package() {
  local f="\$srcdir/$(basename "$f")"
  case "$kind" in
    deb) local data=\$(bsdtar -tf "\$f" | grep '^data\.tar'); bsdtar -xOf "\$f" "\$data" | bsdtar -xf - -C "\$pkgdir" ;;
    rpm) bsdtar -xf "\$f" -C "\$pkgdir" ;;
    tar) install -d "\$pkgdir/opt/$r"; bsdtar -xf "\$f" -C "\$pkgdir/opt/$r" --strip-components=1
         local exe=\$(find "\$pkgdir/opt/$r" -maxdepth 2 -type f -perm -u+x | head -1)
         install -d "\$pkgdir/usr/bin"; ln -s "/\${exe#\$pkgdir/}" "\$pkgdir/usr/bin/$r" ;;
    appimage)
         install -Dm755 "\$f" "\$pkgdir/opt/$r/$r.AppImage"
         install -d "\$pkgdir/usr/bin"; ln -s "/opt/$r/$r.AppImage" "\$pkgdir/usr/bin/$r"
         cd "\$srcdir"; chmod +x "\$f"; "\$f" --appimage-extract '*.desktop' >/dev/null 2>&1; "\$f" --appimage-extract 'usr/share/icons/*' >/dev/null 2>&1
         local desk=\$(ls squashfs-root/*.desktop 2>/dev/null | head -1)
         if [ -n "\$desk" ]; then
           sed "s|^Exec=[^ ]*|Exec=/usr/bin/$r|" "\$desk" | install -Dm644 /dev/stdin "\$pkgdir/usr/share/applications/\$(basename "\$desk")"
         fi
         [ -d squashfs-root/usr/share/icons ] && cp -r squashfs-root/usr/share/icons "\$pkgdir/usr/share/" ;;
  esac
  # Fedora/Ubuntu zvyklosti, které by se na Archu praly s jinými balíčky
  rm -rf "\$pkgdir/usr/lib/.build-id" "\$pkgdir/usr/lib64/.build-id"
  if [ -d "\$pkgdir/usr/lib64" ]; then mkdir -p "\$pkgdir/usr/lib"; cp -a "\$pkgdir/usr/lib64/." "\$pkgdir/usr/lib/"; rm -rf "\$pkgdir/usr/lib64"; fi
  [ -d "\$pkgdir/usr/local" ] && { cp -a "\$pkgdir/usr/local/." "\$pkgdir/usr/"; rm -rf "\$pkgdir/usr/local"; }
  rm -rf "\$pkgdir/etc/apt" "\$pkgdir/etc/yum.repos.d"
}
EOF
  if (cd "$d" && makepkg -f --noconfirm >"$d/build.log" 2>&1) && sudo pacman -U --noconfirm "$d"/"$r"-bin-*.pkg.tar.* >/dev/null 2>&1; then
    echo "   $r $tag  nainstalováno (z .$kind)"
  else
    echo "   ! $r: nepovedlo se, posledních pár řádků:"; tail -5 "$d/build.log" | sed 's/^/     /'; continue
  fi

  # chybějící knihovny dohledat a doinstalovat
  missing=$(pacman -Qlq "$r-bin" | while read -r p; do [[ -f $p && -x $p ]] && file -b "$p" | grep -q ELF && ldd "$p" 2>/dev/null; done \
            | awk '/not found/{print $1}' | sort -u)
  for lib in $missing; do
    pkg=$(pacman -Fq "$lib" 2>/dev/null | head -1)
    if [[ -n $pkg ]]; then sudo pacman -S --needed --noconfirm "${pkg##*/}" >/dev/null 2>&1 && echo "     + doinstalováno ${pkg##*/} (kvůli $lib)"
    else echo "     ! chybí knihovna $lib (na Archu jsem ji nenašel)"; fi
  done
done

update-desktop-database ~/.local/share/applications 2>/dev/null
sudo update-desktop-database /usr/share/applications 2>/dev/null
gtk-update-icon-cache -q /usr/share/icons/hicolor 2>/dev/null

echo
echo "== hotovo"
for k in "${SEL[@]}"; do r=${REPO[$k]}; pacman -Q "$r-bin" 2>/dev/null | sed 's/^/   /'; done
# skript do dotfiles, ať jde vše na dalším počítači stejně
if [[ -d ~/dotfiles/system && $(readlink -f "$0") != $(readlink -f ~/dotfiles/system/arch-extras.sh) ]]; then
  cp "$0" ~/dotfiles/system/arch-extras.sh && echo "   skript uložen do ~/dotfiles/system/arch-extras.sh"
fi
echo
echo "ArtCraft najdeš v panelu (Aplikace, hledání funguje i na 'photoshop', 'premiere'…) a v rofi."
echo "Jsou to velmi nové verze (0.x): počítej s chybami a důležité soubory si zálohuj."
((DO_VIRT)) && echo "virt-manager: odhlas se a přihlas (kvůli skupině libvirt), pak ho spusť z panelu nebo příkazem virt-manager."
