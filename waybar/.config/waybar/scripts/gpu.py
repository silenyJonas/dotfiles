#!/usr/bin/env python3
"""Vytížení grafiky pro Waybar ("12% GPU"), vypisuje jeden řádek JSON každé 2 s.

  gpu.py          smyčka pro Waybar
  gpu.py --debug  vypíše, jakou grafiku a jaký způsob měření našel

Intel (i915 i xe): vytížení = čas, kdy grafika NEspí (RC6 / idle residency), to odpovídá
"busy" v intel_gpu_top. AMD: gpu_busy_percent. NVIDIA: nvidia-smi.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

INTERVAL = 2


def read(path):
    with open(path) as f:
        return f.read().strip()


def first(*patterns):
    for pattern in patterns:
        for path in sorted(glob.glob(pattern)):
            if os.path.exists(path):
                return path
    return None


def find():
    """Vrací slovník s popisem nalezené grafiky, nebo None."""
    try:
        cards = sorted(c for c in os.listdir("/sys/class/drm") if re.fullmatch(r"card\d+", c))
    except OSError:
        return None
    found = []
    for card in cards:
        base = f"/sys/class/drm/{card}"
        dev = os.path.join(base, "device")
        driver = os.path.basename(os.path.realpath(os.path.join(dev, "driver")))
        g = {"card": card, "base": base, "dev": dev, "driver": driver,
             "slot": os.path.basename(os.path.realpath(dev))}
        if os.path.exists(os.path.join(dev, "gpu_busy_percent")):
            g["kind"], g["rank"] = "busy", 0
        elif driver == "nvidia" and shutil.which("nvidia-smi"):
            g["kind"], g["rank"] = "nvidia", 1
        else:
            idle = first(f"{base}/gt/gt0/rc6_residency_ms", f"{base}/power/rc6_residency_ms",      # i915
                         f"{dev}/tile0/gt0/gtidle/idle_residency_ms")                              # xe
            freq = first(f"{base}/gt_act_freq_mhz", f"{dev}/tile0/gt0/freq0/act_freq")
            if idle:
                g["kind"], g["rank"], g["idle"] = "idle", 2, idle
            elif freq:
                g["kind"], g["rank"] = "freq", 3
            else:
                continue
            g["freq"] = freq
            g["freq_max"] = first(f"{base}/gt_RP0_freq_mhz", f"{base}/gt_max_freq_mhz",
                                  f"{dev}/tile0/gt0/freq0/rp0_freq", f"{dev}/tile0/gt0/freq0/max_freq")
        g["temp"] = first(f"{dev}/hwmon/hwmon*/temp1_input")
        found.append(g)
    if not found:
        return None
    g = min(found, key=lambda x: x["rank"])
    g["name"] = name(g)
    return g


def name(g):
    vendor = {"amdgpu": "AMD", "radeon": "AMD", "i915": "Intel", "xe": "Intel", "nvidia": "NVIDIA",
              "nouveau": "NVIDIA"}.get(g["driver"], "GPU")
    try:
        text = subprocess.run(["lspci", "-mm", "-s", g["slot"]], capture_output=True, text=True,
                              timeout=3).stdout
        fields = re.findall(r'"([^"]*)"', text)
        if len(fields) >= 3:
            inner = re.search(r"\[([^\]]+)\]", fields[2])
            return f"{vendor} {inner.group(1) if inner else fields[2]}"
    except (OSError, subprocess.TimeoutExpired):
        pass
    return f"{vendor} graphics"


class Meter:
    def __init__(self, g):
        self.g, self.last = g, None

    def sample(self):
        """(vytížení %, takt MHz nebo None, teplota °C nebo None)"""
        g, usage, clock, temp = self.g, None, None, None
        if g["kind"] == "busy":
            usage = float(read(os.path.join(g["dev"], "gpu_busy_percent")))
        elif g["kind"] == "nvidia":
            out = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,temperature.gpu,clocks.gr",
                                  "--format=csv,noheader,nounits"], capture_output=True, text=True,
                                 timeout=3).stdout.split(",")
            usage, temp, clock = float(out[0]), float(out[1]), float(out[2])
        else:
            if g.get("freq"):
                clock = float(read(g["freq"]))
            if g["kind"] == "idle":
                now, idle = time.monotonic() * 1000, float(read(g["idle"]))
                if self.last:
                    dt, di = now - self.last[0], idle - self.last[1]
                    usage = max(0.0, min(100.0, 100 * (1 - di / dt))) if dt > 0 else None
                self.last = (now, idle)
            elif clock is not None and g.get("freq_max"):
                top = float(read(g["freq_max"]))
                usage = 100 * clock / top if top else None
        if temp is None and g.get("temp"):
            temp = int(read(g["temp"])) / 1000
        return usage, clock, temp


def loop():
    g = find()
    if not g:
        print(json.dumps({"text": "", "class": "none", "tooltip": "No GPU found"}), flush=True)
        while True:
            time.sleep(3600)
    meter, last = Meter(g), None
    try:
        meter.sample()                                     # první vzorek jen pro výchozí hodnotu
    except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
        pass
    time.sleep(0.5)
    while True:
        try:
            usage, clock, temp = meter.sample()
        except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
            usage = clock = temp = None
        if usage is None:
            out = {"text": "–% GPU", "class": "idle", "tooltip": g["name"]}
        else:
            tip = [g["name"], f"GPU usage: {usage:.0f}%"]
            if clock:
                tip.append(f"Clock: {clock:.0f} MHz")
            if temp:
                tip.append(f"Temperature: {temp:.0f}°C")
            cls = "critical" if usage >= 90 else "warning" if usage >= 70 else "normal"
            out = {"text": f"{usage:.0f}% GPU", "class": cls, "percentage": round(usage),
                   "tooltip": "\n".join(tip)}
        if out != last:
            print(json.dumps(out), flush=True)
            last = out
        time.sleep(INTERVAL)


if __name__ == "__main__":
    if "--debug" in sys.argv:
        g = find()
        print(json.dumps(g, indent=2) if g else "žádnou grafiku jsem nenašel")
        if g:
            m = Meter(g)
            m.sample()
            time.sleep(1)
            print("měření:", m.sample())
    else:
        loop()
