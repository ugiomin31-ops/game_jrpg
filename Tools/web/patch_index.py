"""Make Unity's default WebGL page phone-friendly after the build (run by .github/workflows/phone-build.yml).

- drops the old "WebGL builds are not supported on mobile devices" banner if the template still has it
- caps the canvas pixel ratio at 2 so 3x phone screens do not render 9x the pixels
- shows "rotate to landscape" in portrait on touch screens, and on the first tap asks for full screen + landscape lock
  (Android Chrome honours both; iOS Safari ignores them and the rotate notice still helps)
- splits build files over 90 MB into parts (GitHub Pages refuses files over 100 MB) and adds a fetch shim that
  streams the parts back as one response, so the Unity loader sees the original file

Usage: python Tools/web/patch_index.py build/WebGL/Web/index.html
"""
import json
import os
import re
import sys

PART_BYTES = 90 * 1024 * 1024

SPLIT_JS = """
<script id="abyss-split">
  (function () {
    var parts = %s, realFetch = window.fetch.bind(window);
    window.fetch = function (input, init) {
      var url = typeof input === "string" ? input : (input && input.url) || "";
      var name = url.split("?")[0].split("/").pop(), info = parts[name];
      if (!info) return realFetch(input, init);
      var base = url.split("?")[0], i = 0, reader = null;
      function next(controller) {
        var step = reader ? reader.read() : Promise.resolve({ done: true });
        return step.then(function (r) {
          if (!r.done) { controller.enqueue(r.value); return; }
          if (i >= info.count) { controller.close(); return; }
          return realFetch(base + ".part" + (i++), init).then(function (res) {
            if (!res.ok) throw new Error("part " + (i - 1) + ": HTTP " + res.status);
            reader = res.body.getReader();
            return next(controller);
          });
        });
      }
      var body = new ReadableStream({ pull: next });
      return Promise.resolve(new Response(body, { status: 200, headers: {
        "Content-Type": "application/octet-stream", "Content-Length": String(info.size) } }));
    };
  })();
</script>
"""


def split_big_files(folder):
    """Split files over PART_BYTES into name.part0, name.part1, ... and return {name: {count, size}}."""
    parts = {}
    for root, _, files in os.walk(folder):
        for name in files:
            path = os.path.join(root, name)
            size = os.path.getsize(path)
            if size <= PART_BYTES or ".part" in name:
                continue
            count = 0
            with open(path, "rb") as src:
                while True:
                    chunk = src.read(PART_BYTES)
                    if not chunk:
                        break
                    with open(f"{path}.part{count}", "wb") as dst:
                        dst.write(chunk)
                    count += 1
            os.remove(path)
            parts[name] = {"count": count, "size": size}
    return parts

STYLE = """
<style id="abyss-phone">
  html, body { background: #0b0a10; margin: 0; overscroll-behavior: none; touch-action: none; }
  #abyss-rotate { display: none; position: fixed; inset: 0; z-index: 10; background: #0b0a10; color: #f2e6c9;
    font: 600 20px/1.6 system-ui, sans-serif; align-items: center; justify-content: center; text-align: center; }
  #abyss-rotate span { display: block; font-size: 56px; }
  @media (orientation: portrait) and (pointer: coarse) { #abyss-rotate { display: flex; } }
</style>
"""

BODY = """
<div id="abyss-rotate"><div><span>&#x21bb;</span>휴대폰을 가로로 돌려 주세요<br><small>화면을 한 번 누르면 전체 화면이 됩니다</small></div></div>
<script id="abyss-phone-js">
  (function () {
    if (!matchMedia("(pointer: coarse)").matches) return;
    function go() {
      var el = document.documentElement, req = el.requestFullscreen || el.webkitRequestFullscreen;
      if (!req || document.fullscreenElement) return;
      Promise.resolve(req.call(el)).then(function () {
        if (screen.orientation && screen.orientation.lock) return screen.orientation.lock("landscape");
      }).catch(function () {});
    }
    document.addEventListener("touchend", go, { passive: true });
  })();
</script>
"""


def patch(html, parts=None):
    notes = []
    if 'id="abyss-phone"' in html:
        return html, ["already patched"]
    if parts:
        html = re.sub(r"<head[^>]*>", lambda m: m.group(0) + SPLIT_JS % json.dumps(parts), html, count=1)
        notes.append("split " + ", ".join(f"{n} into {p['count']} parts" for n, p in parts.items()))
    html, n = re.subn(r"unityShowBanner\(\s*['\"]WebGL builds are not supported on mobile devices\.?['\"]\s*\)\s*;?", "", html)
    if n:
        notes.append("removed mobile banner")
    html, n = re.subn(r"createUnityInstance\(\s*canvas\s*,\s*config\s*,",
                      "createUnityInstance(canvas, Object.assign(config, { devicePixelRatio: Math.min(window.devicePixelRatio || 1, 2) }),",
                      html, count=1)
    notes.append("capped pixel ratio" if n else "pixel ratio left as is (createUnityInstance call not found)")
    html = html.replace("</head>", STYLE + "</head>", 1)
    html = html.replace("</body>", BODY + "</body>", 1)
    html = re.sub(r'<html lang="[^"]*"', '<html lang="ko"', html, count=1)
    return html, notes


if __name__ == "__main__":
    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        source = f.read()
    if "</head>" not in source or "</body>" not in source:
        sys.exit(f"{path}: not an HTML page with head and body")
    parts = {} if 'id="abyss-phone"' in source else split_big_files(os.path.dirname(os.path.abspath(path)))
    result, notes = patch(source, parts)
    with open(path, "w", encoding="utf-8") as f:
        f.write(result)
    print(path + ": " + ", ".join(notes))
