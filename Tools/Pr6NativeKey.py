"""Hold a real Windows scan-code key across several player input frames."""
import ctypes
import sys
import time

api = ctypes.windll.user32
buf = ctypes.create_unicode_buffer(512)
api.GetWindowTextW(api.GetForegroundWindow(), buf, 512)
if buf.value != "Abyss Labyrinth":
    raise SystemExit("Refusing key input: test player is not foreground")
keys = {"enter": 13, "esc": 27, "up": 38, "down": 40, "left": 37, "right": 39, "tab": 9}
key = sys.argv[1]
vk = keys.get(key, ord(key.upper()) if len(key) == 1 else 0)
if not vk:
    raise SystemExit("Unknown key")
scan = api.MapVirtualKeyW(vk, 0)
flags = 0x0008 | (0x0001 if key in ["up", "down", "left", "right"] else 0)
api.keybd_event(0, scan, flags, 0)
try:
    time.sleep(float(sys.argv[2]) if len(sys.argv) > 2 else 0.15)
finally:
    api.keybd_event(0, scan, flags | 0x0002, 0)
print("scan-code input:", key)
