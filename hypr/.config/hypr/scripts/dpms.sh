#!/usr/bin/env bash
# Obrazovka zapnout / vypnout:  dpms.sh on|off
# Funguje se starým (hyprland.conf) i novým Lua configem (hyprland.lua) Hyprlandu.
if hyprctl -j status 2>/dev/null | grep -q '"configProvider": *"lua"'; then
  hyprctl dispatch "hl.dsp.dpms({ action = \"$1\" })"
else
  hyprctl dispatch dpms "$1"
fi
