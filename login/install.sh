#!/usr/bin/env bash
# Instalace přihlašovací obrazovky z dotfiles (téma SDDM "island", pozadí = tapeta z plochy).
# Spustit:  bash ~/dotfiles/login/install.sh
HERE=$(cd "$(dirname "$0")" && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
tar czf "$TMP/sddm-island.tar.gz" -C "$HERE/sddm-theme" island
cp "$HERE/island-sddm-bg" "$TMP/"
ISLAND_SRC="$TMP" bash "$HERE/sddm-install.sh"
