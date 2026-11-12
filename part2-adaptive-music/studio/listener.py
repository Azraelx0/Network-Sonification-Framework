"""Receives timeline events over UDP and drives the FMOD score.

    python listener.py           listen on UDP 9500 for timeline.py --play
    python listener.py --demo    cycle baseline -> infection -> c2 without the laptop

Press q (or Ctrl+C) to stop.
"""
import argparse
import ctypes
import json
import msvcrt
import os
import socket
import time
from pathlib import Path

PORT = 9500
FMOD_VERSION = 0x00020315  # must match the installed FMOD Engine (2.03.15)
HERE = Path(__file__).resolve().parent
BANKS = HERE / "fmod" / "Build" / "Desktop"
API = Path(r"C:\Program Files (x86)\FMOD SoundSystem\FMOD Studio API Windows\api")


def load_fmod():
    for d in (HERE / "lib", API / "core" / "lib" / "x64", API / "studio" / "lib" / "x64"):
        if d.is_dir():
            os.add_dll_directory(str(d))
    core = ctypes.CDLL("fmod.dll")
    studio = ctypes.CDLL("fmodstudio.dll")
    return core, studio


class Score:
    def __init__(self):
        self.core, self.fmod = load_fmod()
        self.system = ctypes.c_void_p()
        self.music = ctypes.c_void_p()
        self.checkin_desc = ctypes.c_void_p()
        self.state = None

        self.check(self.fmod.FMOD_Studio_System_Create(ctypes.byref(self.system), FMOD_VERSION),
                   "create system", "FMOD Engine version must match FMOD_VERSION")
        self.check(self.fmod.FMOD_Studio_System_Initialize(self.system, 64, 0, 0, None),
                   "initialize")

        for name in ("Master.bank", "Master.strings.bank"):
            bank = ctypes.c_void_p()
            self.check(self.fmod.FMOD_Studio_System_LoadBankFile(
                self.system, str(BANKS / name).encode(), 0, ctypes.byref(bank)),
                f"load {name}", f"build the project in FMOD Studio (F7), expected it in {BANKS}")

        music_desc = self.get_event("event:/Network")
        self.check(self.fmod.FMOD_Studio_EventDescription_CreateInstance(
            music_desc, ctypes.byref(self.music)), "create Network instance")
        self.check(self.fmod.FMOD_Studio_EventInstance_Start(self.music), "start Network")
        self.checkin_desc = self.get_event("event:/Checkin")
        self.set_state("baseline")

    def check(self, result, what, hint=""):
        if result != 0:
            raise RuntimeError(f"FMOD error {result} on {what}" + (f" ({hint})" if hint else ""))

    def get_event(self, path):
        desc = ctypes.c_void_p()
        self.check(self.fmod.FMOD_Studio_System_GetEvent(self.system, path.encode(), ctypes.byref(desc)),
                   f"find {path}", "check the event name and that it's assigned to Master, then rebuild")
        return desc

    def set_state(self, label):
        if label == self.state:
            return
        self.check(self.fmod.FMOD_Studio_EventInstance_SetParameterByNameWithLabel(
            self.music, b"State", label.encode(), 0), f"set State={label}")
        self.state = label
        print(f"  >> State = {label}")

    def checkin(self):
        inst = ctypes.c_void_p()
        self.check(self.fmod.FMOD_Studio_EventDescription_CreateInstance(
            self.checkin_desc, ctypes.byref(inst)), "create Checkin")
        self.fmod.FMOD_Studio_EventInstance_Start(inst)
        self.fmod.FMOD_Studio_EventInstance_Release(inst)

    def update(self):
        self.fmod.FMOD_Studio_System_Update(self.system)

    def close(self):
        if self.music:
            self.fmod.FMOD_Studio_EventInstance_Stop(self.music, 0)
            for _ in range(25):
                self.update()
                time.sleep(0.02)
        self.fmod.FMOD_Studio_System_Release(self.system)


def handle(score, msg):
    if msg.get("type") != "activity":
        print(f"{msg.get('time', ''):<20} {msg.get('type', ''):<9} {msg.get('state', ''):<10} {msg.get('detail', '')}")
    if msg.get("state"):
        score.set_state(msg["state"])
    if msg.get("type") == "c2":
        score.checkin()


def check_quit():
    # press q to exit
    if msvcrt.kbhit() and msvcrt.getwch().lower() == "q":
        raise KeyboardInterrupt


def wait(score, seconds):
    end = time.time() + seconds
    while time.time() < end:
        check_quit()
        score.update()
        time.sleep(0.02)


def demo(score):
    for state, seconds, checkins in (("baseline", 8, 0), ("infection", 8, 0), ("c2", 12, 10)):
        score.set_state(state)
        if checkins:
            for _ in range(checkins):
                score.checkin()
                wait(score, seconds / checkins)
        else:
            wait(score, seconds)


def listen(score):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PORT))
    sock.settimeout(0.02)  # short timeout keeps FMOD updating and lets Ctrl+C through
    print(f"Listening on UDP {PORT}, press q to stop")
    try:
        while True:
            try:
                data, _ = sock.recvfrom(65535)
                handle(score, json.loads(data))
            except socket.timeout:
                pass
            except ValueError:
                print("  (skipped bad message)")
            check_quit()
            score.update()
    finally:
        sock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    score = Score()
    try:
        demo(score) if args.demo else listen(score)
    except KeyboardInterrupt:
        pass
    finally:
        score.close()
        print("Stopped")
