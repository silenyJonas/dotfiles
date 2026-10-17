#!/usr/bin/env python3
"""Nahrávání OBS v liště (Waybar): "● 03:21 ■" jen když OBS nahrává.

  obs-rec.py            smyčka pro Waybar (každou sekundu jeden řádek JSON)
  obs-rec.py stop       zastaví nahrávání
  obs-rec.py pause      pozastaví / obnoví nahrávání
  obs-rec.py setup      zapne v OBS WebSocket server s náhodným heslem (OBS musí být zavřené)

Mluví s OBS přes jeho vestavěný WebSocket (obs-websocket 5), nic dalšího nepotřebuje.
"""
import base64
import hashlib
import json
import os
import secrets
import socket
import struct
import sys
import time

HOST, PORT = "127.0.0.1", 4455
PASS_FILE = os.path.expanduser("~/.config/obs-rec/password")   # NEPATŘÍ do dotfiles
OBS_CONF = [os.path.expanduser("~/.var/app/com.obsproject.Studio/config/obs-studio"),
            os.path.expanduser("~/.config/obs-studio")]
REC, PAUSE, STOP = "", "", ""   # kolečko, pauza, čtvereček (Font Awesome)


# ------------------------------------------------------------------ minimální WebSocket klient
class WS:
    def __init__(self, host, port, timeout=2):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        key = base64.b64encode(secrets.token_bytes(16)).decode()
        self.sock.sendall((f"GET / HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\n"
                           f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                           f"Sec-WebSocket-Protocol: obswebsocket.json\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.sock.recv(1024)
            if not chunk:
                raise ConnectionError("closed during handshake")
            head += chunk
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise ConnectionError("handshake refused")
        self.buf = head.split(b"\r\n\r\n", 1)[1]

    def _read(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("closed")
            self.buf += chunk
        data, self.buf = self.buf[:n], self.buf[n:]
        return data

    def send(self, obj):
        data = json.dumps(obj).encode()
        head = bytes([0x81])
        n = len(data)
        if n < 126:
            head += bytes([0x80 | n])
        elif n < 65536:
            head += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            head += bytes([0x80 | 127]) + struct.pack(">Q", n)
        mask = secrets.token_bytes(4)
        self.sock.sendall(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self):
        while True:
            b1, b2 = self._read(2)
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            if b2 & 0x80:
                mask = self._read(4)
                payload = bytes(b ^ mask[i % 4] for i, b in enumerate(self._read(n)))
            else:
                payload = self._read(n)
            op = b1 & 0x0F
            if op == 8:
                raise ConnectionError("closed by server")
            if op == 9:                                    # ping -> pong
                self.sock.sendall(bytes([0x8A, 0x80]) + secrets.token_bytes(4))
                continue
            if op in (1, 2):
                return json.loads(payload)

    def close(self):
        try:
            self.sock.sendall(bytes([0x88, 0x80]) + secrets.token_bytes(4))   # slušné ukončení
            self.sock.close()
        except OSError:
            pass


class OBS:
    def __init__(self):
        self.ws = WS(HOST, PORT)
        hello = self.ws.recv()["d"]
        ident = {"rpcVersion": 1, "eventSubscriptions": 0}
        auth = hello.get("authentication")
        if auth:
            password = open(PASS_FILE).read().strip() if os.path.exists(PASS_FILE) else ""
            secret = base64.b64encode(hashlib.sha256((password + auth["salt"]).encode()).digest()).decode()
            ident["authentication"] = base64.b64encode(
                hashlib.sha256((secret + auth["challenge"]).encode()).digest()).decode()
        self.ws.send({"op": 1, "d": ident})
        reply = self.ws.recv()
        if reply.get("op") != 2:
            raise PermissionError("wrong password")
        self.counter = 0

    def request(self, kind):
        self.counter += 1
        rid = str(self.counter)
        self.ws.send({"op": 6, "d": {"requestType": kind, "requestId": rid}})
        while True:
            msg = self.ws.recv()
            if msg.get("op") == 7 and msg["d"].get("requestId") == rid:
                return msg["d"].get("responseData") or {}


def clock(ms):
    s = int(ms // 1000)
    return f"{s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60:02d}:{s % 60:02d}"


def loop():
    obs, last = None, None
    while True:
        out = {"text": "", "class": "idle", "tooltip": ""}
        try:
            if obs is None:
                obs = OBS()
            st = obs.request("GetRecordStatus")
            if st.get("outputActive"):
                paused = st.get("outputPaused")
                out = {"text": f"{PAUSE if paused else REC}  {clock(st.get('outputDuration', 0))}  {STOP}",
                       "class": "paused" if paused else "rec",
                       "tooltip": "Recording – click to stop, right click to pause"}
        except PermissionError:
            out = {"text": "", "class": "idle", "tooltip": ""}
            obs = None
            time.sleep(10)
        except (OSError, ConnectionError, ValueError, KeyError):
            if obs is not None:
                obs.ws.close()
            obs = None                                     # OBS neběží, zkusit znovu za chvíli
        if out != last:
            print(json.dumps(out), flush=True)
            last = out
        time.sleep(1 if obs else 3)


def setup():
    password = secrets.token_urlsafe(18)
    os.makedirs(os.path.dirname(PASS_FILE), exist_ok=True)
    with open(PASS_FILE, "w") as f:
        f.write(password)
    os.chmod(PASS_FILE, 0o600)
    done = False
    for base in OBS_CONF:
        if not os.path.isdir(base):
            continue
        d = os.path.join(base, "plugin_config", "obs-websocket")
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "config.json")
        try:
            conf = json.load(open(path))
        except (OSError, ValueError):
            conf = {}
        conf.update({"server_enabled": True, "server_port": PORT, "auth_required": True,
                     "server_password": password, "alerts_enabled": False, "first_load": False})
        json.dump(conf, open(path, "w"), indent=4)
        os.chmod(path, 0o600)
        print("   nastaveno:", path)
        done = True
    if not done:
        print("   OBS jsem nenašel (spusť ho aspoň jednou a pak setup zopakuj)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "setup":
        setup()
    elif cmd in ("stop", "pause"):
        try:
            obs = OBS()
            obs.request("StopRecord" if cmd == "stop" else "ToggleRecordPause")
            obs.ws.close()
        except Exception as err:
            print(f"obs-rec: {err}", file=sys.stderr)
    else:
        loop()
