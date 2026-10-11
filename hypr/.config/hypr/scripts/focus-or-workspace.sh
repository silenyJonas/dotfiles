#!/usr/bin/env bash
# Super + šipka vlevo/vpravo, na každém monitoru zvlášť:
#   - vedle je okno na stejném monitoru -> přepne na něj fokus
#   - jsi na kraji plochy               -> přepne na sousední plochu téhož monitoru
#   - jsi na prázdné ploše a napravo už na tomto monitoru žádná okna nejsou -> neudělá nic
#     (aby se nedaly "naskládat" prázdné plochy za sebou)
# Fokus nikdy nepřeskočí na jiný monitor.
dir="$1"

monitor() { hyprctl activeworkspace | awk 'NR==1{sub(":", "", $7); print $7}'; }

before=$(hyprctl activewindow | awk 'NR==1{print $2}')
mon=$(monitor)
hyprctl dispatch movefocus "$dir" >/dev/null
after=$(hyprctl activewindow | awk 'NR==1{print $2}')

if [ "$(monitor)" != "$mon" ]; then
    # fokus utekl na jiný monitor: vrátit ho zpět a brát to jako kraj plochy
    hyprctl dispatch focusmonitor "$mon" >/dev/null
    [ -n "$before" ] && hyprctl dispatch focuswindow "address:0x$before" >/dev/null
elif [ "$before" != "$after" ]; then
    # fokus se změnil = vedle bylo okno, hotovo
    exit 0
fi

case "$dir" in
    l)
        hyprctl dispatch workspace r-1 >/dev/null
        ;;
    r)
        cur=$(hyprctl activeworkspace | awk 'NR==1{print $3}')
        wins=$(hyprctl activeworkspace | awk '$1=="windows:"{print $2}')
        # je na tomto monitoru někde napravo plocha, na které jsou okna?
        further=$(hyprctl workspaces | awk -v cur="$cur" -v mon="$mon" '
            $1=="workspace" && $2=="ID" { id = $3; m = $7; sub(":", "", m) }
            $1=="windows:" && m == mon && id > cur && $2 > 0 { found = 1 }
            END { print found + 0 }')

        if [ "${wins:-0}" -gt 0 ] || [ "$further" -eq 1 ]; then
            hyprctl dispatch workspace r+1 >/dev/null
        fi
        ;;
esac
