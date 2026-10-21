#!/usr/bin/env python3
"""Plochy bez děr uprostřed, každý monitor zvlášť.

  workspaces.py nav l|r   Super + šipka: fokus na okno vedle; na kraji plochy skok na sousední
                          plochu S OKNY (prázdné uprostřed se přeskočí). Za poslední plochou
                          (a před první) smí být jedna prázdná, víc ne.
  workspaces.py daemon    hlídá Hyprland; když se plocha uprostřed vyprázdní (zavřené / přesunuté
                          okno), posune okna z dalších ploch o jednu doleva, takže díra zmizí.
"""
import json
import os
import socket
import subprocess
import sys
import time


def hypr(*args):
    out = subprocess.run(["hyprctl", *args], capture_output=True, text=True).stdout
    return out


_LUA = None


def lua():
    """Hyprland s Lua configem (hyprland.lua) má jiný tvar příkazů "hyprctl dispatch"."""
    global _LUA
    if _LUA is None:
        try:
            _LUA = json.loads(hypr("-j", "status")).get("configProvider") == "lua"
        except (json.JSONDecodeError, AttributeError):
            _LUA = False
    return _LUA


def q(text):
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


# příkazy pro "hyprctl dispatch" ve starém i Lua tvaru
def d_focus_dir(direction):
    return f"hl.dsp.focus({{ direction = {q(direction)} }})" if lua() else f"movefocus {direction}"


def d_focus_monitor(mon):
    return f"hl.dsp.focus({{ monitor = {q(mon)} }})" if lua() else f"focusmonitor {mon}"


def d_focus_window(address):
    return f"hl.dsp.focus({{ window = {q('address:' + address)} }})" if lua() else f"focuswindow address:{address}"


def d_workspace(ws):
    return f"hl.dsp.focus({{ workspace = {int(ws)} }})" if lua() else f"workspace {ws}"


def d_move_silent(ws, address):
    if lua():
        return f"hl.dsp.window.move({{ workspace = {int(ws)}, follow = false, window = {q('address:' + address)} }})"
    return f"movetoworkspacesilent {ws},address:{address}"


def d_ws_to_monitor(ws, mon):
    return f"hl.dsp.workspace.move({{ workspace = {int(ws)}, monitor = {q(mon)} }})" if lua() \
        else f"moveworkspacetomonitor {ws} {mon}"


def dispatch(cmd):
    hypr("dispatch", cmd)


def hj(what):
    try:
        return json.loads(hypr("-j", what))
    except json.JSONDecodeError:
        return [] if what != "activeworkspace" and what != "activewindow" else {}


def state():
    """(id monitoru se fokusem, aktivní plocha, {monitor: {id plochy: počet oken}}, plochy aktivní na monitorech)"""
    spaces, monitors = hj("workspaces"), hj("monitors")
    per = {}
    for w in spaces:
        if w["id"] > 0:                                   # speciální plochy (scratchpad) nechat být
            per.setdefault(w["monitor"], {})[w["id"]] = w["windows"]
    active = {m["name"]: m["activeWorkspace"]["id"] for m in monitors}
    focused = next((m["name"] for m in monitors if m.get("focused")), None)
    return focused, active, per


def used_ids(per):
    return {i for spaces in per.values() for i in spaces}


# ------------------------------------------------------------------ navigace
def plan_nav(direction, cur, cur_windows, mine, taken):
    """Kam skočit z plochy cur. mine = {id: okna} na tomto monitoru, taken = id na všech monitorech.
    Vrací id cílové plochy nebo None (zůstat)."""
    full = sorted(i for i, n in mine.items() if n > 0 and i != cur)
    if direction == "r":
        right = [i for i in full if i > cur]
        if right:
            return right[0]                               # nejbližší plocha s okny (prázdné se přeskočí)
        if cur_windows == 0:
            return None                                    # už jsi na prázdné ploše na kraji
        nxt = cur + 1
        while nxt in taken:                                # první volné číslo napravo
            nxt += 1
        return nxt
    left = [i for i in full if i < cur]
    if left:
        return left[-1]
    if cur_windows == 0 or cur <= 1:
        return None
    prv = cur - 1                                          # jedna prázdná plocha smí být i na levém kraji
    while prv >= 1 and prv in taken:
        prv -= 1
    return prv if prv >= 1 else None


def nav(direction):
    before = hj("activewindow").get("address")
    _f, _a, _p = state()
    mon = _f
    dispatch(d_focus_dir(direction))
    focused, active, per = state()
    after = hj("activewindow").get("address")
    if focused != mon:                                     # fokus utekl na jiný monitor -> vrátit, brát jako kraj
        dispatch(d_focus_monitor(mon))
        if before:
            dispatch(d_focus_window(before))
    elif before != after:
        return                                             # vedle bylo okno, hotovo
    cur = active.get(mon)
    mine = per.get(mon, {})
    target = plan_nav(direction, cur, mine.get(cur, 0), mine, used_ids(per))
    if target is not None and target != cur:
        dispatch(d_workspace(target))


# ------------------------------------------------------------------ zacelení děr
def plan_compact(mine, others, active_id):
    """Přesuny (z, do), aby plochy s okny na monitoru šly za sebou bez díry.
    others = id ploch na ostatních monitorech (ty se nesmí obsadit)."""
    full = sorted(i for i, n in mine.items() if n > 0)
    if len(full) < 2:
        return []
    moves, slot = [], full[0]
    for i in full:
        while slot in others:                              # číslo patří jinému monitoru -> přeskočit
            slot += 1
        if i != slot:
            moves.append((i, slot))
        slot += 1
    return moves


def compact():
    focused, active, per = state()
    clients = hj("clients")
    for mon, mine in per.items():
        others = {i for m, sp in per.items() if m != mon for i in sp}
        # prázdná plocha, na které právě jsi, není díra (smí být na kraji); díra je jen mezi plochami s okny
        moves = plan_compact(mine, others, active.get(mon))
        if not moves:
            continue
        follow = None
        batch = []
        for src, dst in moves:
            for c in clients:
                if c["workspace"]["id"] == src:
                    batch.append("dispatch " + d_move_silent(dst, c["address"]))
            # Plocha s novým číslem vznikne na monitoru s fokusem, ne na tomhle. Když je fokus na druhé
            # obrazovce, okna by na ni přeskočila, proto plochu hned vrátit na její monitor.
            batch.append("dispatch " + d_ws_to_monitor(dst, mon))
            if active.get(mon) == src:
                follow = dst
        if follow is not None:
            batch.append("dispatch " + d_focus_monitor(mon))
            batch.append("dispatch " + d_workspace(follow))   # zůstat u svých oken
        if focused and focused != mon:
            batch.append("dispatch " + d_focus_monitor(focused))
        hypr("--batch", " ; ".join(batch))


def daemon():
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    run = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    path = os.path.join(run, "hypr", sig or "", ".socket2.sock")
    triggers = ("closewindow>>", "movewindow>>", "movewindowv2>>", "destroyworkspace>>", "workspace>>",
                "focusedmon>>")
    while True:
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(path)
            sock.settimeout(0.35)
            buf, pending = b"", False
            compact()
            while True:
                try:
                    data = sock.recv(4096)
                    if not data:
                        break
                    buf += data
                    *lines, buf = buf.split(b"\n")
                    if any(line.decode(errors="ignore").startswith(triggers) for line in lines):
                        pending = True
                except socket.timeout:
                    if pending:                            # chvíli počkat, až Hyprland doběhne
                        pending = False
                        compact()
        except OSError:
            pass
        time.sleep(2)


if __name__ == "__main__":
    if sys.argv[1:2] == ["nav"] and sys.argv[2:3] in (["l"], ["r"]):
        nav(sys.argv[2])
    elif sys.argv[1:2] == ["daemon"]:
        daemon()
    elif sys.argv[1:2] == ["compact"]:
        compact()
    else:
        print(__doc__)
