#!/bin/bash
# Spustí Yazi/Superfile jako root
# Přenese proměnné pro Wayland/X

TERMINAL="alacritty"
BACKGROUND_OPACITY=0.8

pkexec env DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY $TERMINAL -o background_opacity=$BACKGROUND_OPACITY -e yazi
