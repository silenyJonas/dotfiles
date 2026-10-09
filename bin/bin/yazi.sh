#!/bin/bash
# Spustí Yazi/Superfile s průhledným terminálem

TERMINAL="alacritty"    # můžeš změnit na kitty/wezterm
BACKGROUND_OPACITY=0.8  # průhlednost

# Spuštění běžného uživatele
$TERMINAL -o background_opacity=$BACKGROUND_OPACITY -e yazi
