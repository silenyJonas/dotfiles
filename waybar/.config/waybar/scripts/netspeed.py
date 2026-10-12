#!/usr/bin/env python3
"""Rychlost sítě pro Waybar: každé 2 vteřiny vypíše stahování a odesílání (s mezerou před jednotkou)."""
import json
import sys
import time

INTERVAL = 2
SKIP = ("lo", "docker", "veth", "virbr", "br-", "tun", "wg")   # virtuální rozhraní se nepočítají


def counters():
    down = up = 0
    with open("/proc/net/dev") as f:
        for line in f.readlines()[2:]:
            name, data = line.split(":", 1)
            name = name.strip()
            if name.startswith(SKIP):
                continue
            fields = data.split()
            down += int(fields[0])
            up += int(fields[8])
    return down, up


def human(rate):
    for unit in ("B/s", "kB/s", "MB/s", "GB/s"):
        if rate < 999.5 or unit == "GB/s":
            return f"{rate:.1f} {unit}" if rate < 10 and unit != "B/s" else f"{rate:.0f} {unit}"
        rate /= 1000


last, stamp = counters(), time.monotonic()
while True:
    time.sleep(INTERVAL)
    now, moment = counters(), time.monotonic()
    span = max(0.001, moment - stamp)
    down, up = (now[0] - last[0]) / span, (now[1] - last[1]) / span
    last, stamp = now, moment
    text = f" {human(down)}   {human(up)}"
    print(json.dumps({"text": text, "tooltip": f"Download: {human(down)}\nUpload: {human(up)}"}), flush=True)
