#!/usr/bin/env bash
# Sada ArtCraft (open-source náhrady Adobe) z GitHubu storytold, oficiální .rpm balíčky pro Fedoru:
#   photo  PhotoCraft   ~ Photoshop        film    FilmCraft    ~ Premiere Pro
#   vector VectorCraft  ~ Illustrator      effect  EffectCraft  ~ After Effects
#   light  LightCraft   ~ Lightroom        design  DesignCraft  ~ InDesign
#   pdf    PdfCraft     ~ Acrobat
#
# Spustit (vše):        bash ~/Downloads/craft-install.sh
# Jen některé:          bash ~/Downloads/craft-install.sh photo film
# Aktualizace:          stejný příkaz znovu (nainstaluje nejnovější verzi)
# Odinstalovat:         bash ~/Downloads/craft-install.sh --remove [photo film …]
set -e
declare -A REPO=([photo]=photocraft [vector]=vectorcraft [film]=filmcraft [effect]=effectcraft
                 [light]=lightcraft [design]=designcraft [pdf]=pdfcraft)
ORDER=(photo film vector effect light design pdf)

REMOVE=0
[ "$1" = "--remove" ] && { REMOVE=1; shift; }
SEL=("$@"); [ ${#SEL[@]} -eq 0 ] && SEL=("${ORDER[@]}")
for k in "${SEL[@]}"; do [ -n "${REPO[$k]}" ] || { echo "Neznámá aplikace: $k (možnosti: ${ORDER[*]})"; exit 1; }; done

if [ $REMOVE = 1 ]; then
  PK=(); for k in "${SEL[@]}"; do rpm -q "${REPO[$k]}" >/dev/null 2>&1 && PK+=("${REPO[$k]}"); done
  [ ${#PK[@]} -gt 0 ] && sudo dnf remove -y "${PK[@]}" || echo "Nic z toho není nainstalované."
  exit 0
fi

ARCH=$(uname -m)
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
RPMS=()
echo "== 1/3 stahování nejnovějších verzí"
for k in "${SEL[@]}"; do
  r=${REPO[$k]}
  json=$(curl -fsSL "https://api.github.com/repos/storytold/$r/releases/latest") || { echo "   $r: GitHub neodpověděl, přeskočeno"; continue; }
  read -r tag rpm_url sums_url < <(python3 -c '
import json, sys
d = json.loads(sys.stdin.read()); arch = sys.argv[1]
a = {x["name"]: x["browser_download_url"] for x in d.get("assets", [])}
rpm = next((u for n, u in a.items() if n.endswith(f"linux-{arch}.rpm")), "-")
sums = next((u for n, u in a.items() if n.upper().startswith("SHA256SUMS")), "-")
print(d.get("tag_name", "?"), rpm, sums)' "$ARCH" <<<"$json")
  if [ "$rpm_url" = "-" ]; then echo "   $r $tag: balíček .rpm pro $ARCH v této verzi není, přeskočeno"; continue; fi
  f="$TMP/$(basename "$rpm_url")"
  curl -fsSL -o "$f" "$rpm_url"
  if [ "$sums_url" != "-" ] && curl -fsSL -o "$TMP/$r.sums" "$sums_url"; then
    want=$(grep -F "$(basename "$f")" "$TMP/$r.sums" | awk '{print $1}' | head -1)
    have=$(sha256sum "$f" | awk '{print $1}')
    if [ -n "$want" ] && [ "$want" != "$have" ]; then echo "   $r: KONTROLNÍ SOUČET NESEDÍ, přeskočeno"; rm -f "$f"; continue; fi
    echo "   $r $tag  ok (kontrolní součet sedí)"
  else
    echo "   $r $tag  ok (bez kontrolního součtu)"
  fi
  RPMS+=("$f")
done
[ ${#RPMS[@]} -gt 0 ] || { echo "Nic ke stažení."; exit 1; }

echo "== 2/3 instalace"
sudo dnf install -y "${RPMS[@]}"

echo "== 3/3 hotovo"
for k in "${SEL[@]}"; do r=${REPO[$k]}; rpm -q "$r" >/dev/null 2>&1 && printf "   %-12s %s\n" "$r" "$(rpm -q --qf '%{VERSION}' "$r")"; done
update-desktop-database ~/.local/share/applications 2>/dev/null || true
# skript do dotfiles, ať jde sada na novém počítači nainstalovat stejně
if [ -d ~/dotfiles/system ] && [ "$(readlink -f "$0")" != "$(readlink -f ~/dotfiles/system/craft-install.sh)" ]; then
  cp "$0" ~/dotfiles/system/craft-install.sh && echo "   skript uložen do ~/dotfiles/system/craft-install.sh"
fi
echo
echo "Aplikace najdeš v rofi (Super+R) a v záložce Aplikace v panelu. Spuštění i z terminálu: photocraft, filmcraft, …"
echo "Jsou to velmi nové verze (0.x): počítej s chybami a důležité soubory si zálohuj."
