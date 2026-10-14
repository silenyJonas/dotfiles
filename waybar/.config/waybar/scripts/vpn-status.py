#!/usr/bin/env python3
"""Ikona VPN do Waybaru: štít, zbarvený když je připojená VPN (WireGuard / OpenVPN v NetworkManageru)."""
import json, os, subprocess, sys, time

ICON = ""
ENV = dict(os.environ, LC_ALL="C.UTF-8")
COUNTRIES = {"nl": "Netherlands", "pl": "Poland", "ro": "Romania", "rum": "Romania", "jp": "Japan",
             "us": "United States", "de": "Germany", "at": "Austria", "ch": "Switzerland"}


def pretty(name):
    provider, _, code = name.rpartition("-")
    country = COUNTRIES.get(code.lower())
    return f"{provider.capitalize()} · {country}" if provider and country else name


last = None
while True:
    try:
        out = subprocess.run(["nmcli", "-t", "-f", "TYPE,NAME", "connection", "show", "--active"],
                             capture_output=True, text=True, env=ENV, timeout=5).stdout
        active = [line.split(":", 1)[1] for line in out.splitlines()
                  if line.split(":", 1)[0] in ("wireguard", "vpn")]
    except Exception:
        active = []
    if active:
        data = {"text": ICON, "class": "on", "tooltip": f"VPN on: {pretty(active[0])}\nYour IP is hidden"}
    else:
        data = {"text": ICON, "class": "off", "tooltip": "VPN off\nYour IP is visible"}
    if data != last:
        print(json.dumps(data), flush=True)
        last = data
    time.sleep(3)
