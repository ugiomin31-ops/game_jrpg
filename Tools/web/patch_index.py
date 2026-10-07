"""Make Unity's default WebGL page phone-friendly after the build (run by .github/workflows/phone-build.yml).

- drops the old "WebGL builds are not supported on mobile devices" banner if the template still has it
- caps the canvas pixel ratio at 2 so 3x phone screens do not render 9x the pixels
- shows "rotate to landscape" in portrait on touch screens, and on the first tap asks for full screen + landscape lock
  (Android Chrome honours both; iOS Safari ignores them and the rotate notice still helps)

Usage: python Tools/web/patch_index.py build/WebGL/Web/index.html
"""
import re
import sys

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


def patch(html):
    notes = []
    if 'id="abyss-phone"' in html:
        return html, ["already patched"]
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
    result, notes = patch(source)
    with open(path, "w", encoding="utf-8") as f:
        f.write(result)
    print(path + ": " + ", ".join(notes))
