// External QA only; capture the real framebuffer, including screen-space UI.
Application.runInBackground = true;
Application.targetFrameRate = 20;
var path = System.IO.Path.GetFullPath("docs/verification/astra-enrichment-20261015/title-framebuffer.png");
ScreenCapture.CaptureScreenshot(path);
return new { screenshot = path, screen = Abyss.Runtime.GameApp.Instance == null ? "missing" : Abyss.Runtime.GameApp.Instance.Screen.ToString(), width = Screen.width, height = Screen.height };
