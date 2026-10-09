#!/usr/bin/env bash
# Super + šipka vlevo/vpravo:
#   - vedle je okno      -> přepne na něj fokus
#   - jsi na kraji plochy -> přepne na sousední plochu
#   - jsi na prázdné ploše a napravo už žádná okna nejsou -> neudělá nic
#     (aby se nedaly "naskládat" prázdné plochy za sebou)
dir="$1"

before=$(hyprctl activewindow | awk 'NR==1{print $2}')
hyprctl dispatch movefocus "$dir" >/dev/null
after=$(hyprctl activewindow | awk 'NR==1{print $2}')

# fokus se změnil = vedle bylo okno, hotovo
[ "$before" != "$after" ] && exit 0

case "$dir" in
    l)
        hyprctl dispatch workspace r-1 >/dev/null
        ;;
    r)
        cur=$(hyprctl activeworkspace | awk 'NR==1{print $3}')
        wins=$(hyprctl activeworkspace | awk '$1=="windows:"{print $2}')
        # je někde napravo plocha, na které jsou okna?
        further=$(hyprctl workspaces | awk -v cur="$cur" '
            $1=="workspace" && $2=="ID" { id = $3 }
            $1=="windows:" && id > cur && $2 > 0 { found = 1 }
            END { print found + 0 }')

        if [ "${wins:-0}" -gt 0 ] || [ "$further" -eq 1 ]; then
            hyprctl dispatch workspace r+1 >/dev/null
        fi
        ;;
esac
