"""Capture the real test player's client pixels and foreground bounds."""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import sys
import time
from PIL import ImageGrab

sys.stdout.reconfigure(encoding="utf-8")
ctypes.windll.shcore.SetProcessDpiAwareness(2)
api = ctypes.windll.user32
handles = []
@ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
def enum(hwnd, _):
    buf = ctypes.create_unicode_buffer(512)
    api.GetWindowTextW(hwnd, buf, 512)
    if buf.value == "Abyss Labyrinth" and api.IsWindowVisible(hwnd):
        handles.append(hwnd)
    return True
api.EnumWindows(enum, 0)
if len(handles) != 1:
    raise SystemExit(f"Expected one test player, found {len(handles)}")
hwnd = handles[0]
if "--position" in sys.argv:
    api.ShowWindow(hwnd, 9)
    api.SetWindowPos(hwnd, 0, 24, 800, 720, 440, 0x0040)
if "--compact" in sys.argv:
    api.ShowWindow(hwnd, 9)
    api.SetWindowPos(hwnd, 0, 0, 800, 760, 439, 0x0040)
rect = wintypes.RECT()
api.GetClientRect(hwnd, ctypes.byref(rect))
point = wintypes.POINT(0, 0)
api.ClientToScreen(hwnd, ctypes.byref(point))
bbox = (point.x, point.y, point.x + rect.right, point.y + rect.bottom)
name = sys.argv[1]
time.sleep(0.3)
path = Path("docs/verification/pr6-improvements") / f"native-{name}.png"
ImageGrab.grab(bbox=bbox, all_screens=True).save(path)
print(json.dumps({"capture": str(path), "clientBounds": bbox, "foreground": api.GetForegroundWindow() == hwnd}, ensure_ascii=False))
