#!/usr/bin/env bash
dir="$1"

before=$(hyprctl activewindow | awk 'NR==1{print $2}')
hyprctl dispatch movefocus "$dir" >/dev/null
after=$(hyprctl activewindow | awk 'NR==1{print $2}')

# fokus se nezměnil = v tom směru už žádné okno není
if [ "$before" = "$after" ]; then
    case "$dir" in
        l) hyprctl dispatch workspace r-1 >/dev/null ;;
        r) hyprctl dispatch workspace r+1 >/dev/null ;;
    esac
fi
