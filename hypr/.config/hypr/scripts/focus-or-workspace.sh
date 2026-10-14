#!/usr/bin/env bash
# Super + šipka vlevo/vpravo -> workspaces.py (fokus na okno vedle, jinak sousední plocha s okny)
exec python3 ~/.config/hypr/scripts/workspaces.py nav "$1"
