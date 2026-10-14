"""Compile the engine-free game logic (Assets/_Game/Scripts/Logic/**/*.cs) together with the
console test harness (Tools/LogicTests/**/*.cs) using Unity's bundled Roslyn + Mono, then run it.
Falls back to .NET SDK 8+ on Linux/macOS or machines without Unity.
No Unity editor needed. Exit code = test exit code.

Usage: python Tools/logic_test.py [args passed to the test exe, e.g. a test-name filter]
"""
import glob
import os
import subprocess
import sys
import shutil
from xml.sax.saxutils import escape

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
UNITY = os.environ.get("ABYSS_UNITY_DATA", r"C:\Program Files\Unity 6000.3.25f1\Editor\Data")
CSC = os.path.join(UNITY, "DotNetSdkRoslyn", "csc.dll")
MONO = os.path.join(UNITY, "MonoBleedingEdge", "bin", "mono.exe")
LIB = os.path.join(UNITY, "MonoBleedingEdge", "lib", "mono", "4.5")
OUT = os.path.join(ROOT, "Temp", "LogicTests")


def newtonsoft():
    hits = glob.glob(os.path.join(ROOT, "Library", "PackageCache", "com.unity.nuget.newtonsoft-json@*", "Runtime", "Newtonsoft.Json.dll"))
    return hits[0] if hits else None


def portable_main():
    """Run the same sources/tests on a machine with .NET 8+, without Unity or a game license."""
    if shutil.which("dotnet") is None:
        print("Install .NET SDK 8+ or set ABYSS_UNITY_DATA to the Unity Editor/Data directory.")
        return 2
    os.makedirs(OUT, exist_ok=True)
    project = os.path.join(OUT, "LogicTests.csproj")
    # Absolute globs avoid depending on the current directory; XML escaping also handles path spaces.
    logic = escape(os.path.join(ROOT, "Assets", "_Game", "Scripts", "Logic", "**", "*.cs"))
    tests = escape(os.path.join(ROOT, "Tools", "LogicTests", "**", "*.cs"))
    with open(project, "w", encoding="utf-8") as f:
        f.write(f"""<Project Sdk="Microsoft.NET.Sdk">
<PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework>
<EnableDefaultCompileItems>false</EnableDefaultCompileItems><DefineConstants>ABYSS_LOGIC_TESTS</DefineConstants>
<LangVersion>9.0</LangVersion><Nullable>disable</Nullable></PropertyGroup>
<ItemGroup><Compile Include="{logic}"/><Compile Include="{tests}"/>
<PackageReference Include="Newtonsoft.Json" Version="13.0.3"/></ItemGroup>
</Project>
""")
    env = dict(os.environ)
    env["ABYSS_DATA_DIR"] = os.path.join(ROOT, "Assets", "_Game", "Resources", "Data")
    return subprocess.run(["dotnet", "run", "--project", project, "--"] + sys.argv[1:], cwd=ROOT, env=env).returncode


def main():
    if not os.path.isfile(CSC) or not os.path.isfile(MONO):
        sys.exit(portable_main())
    os.makedirs(OUT, exist_ok=True)
    srcs = glob.glob(os.path.join(ROOT, "Assets", "_Game", "Scripts", "Logic", "**", "*.cs"), recursive=True)
    srcs += glob.glob(os.path.join(ROOT, "Tools", "LogicTests", "**", "*.cs"), recursive=True)
    nj = newtonsoft()
    refs = [os.path.join(LIB, n) for n in ("mscorlib.dll", "System.dll", "System.Core.dll", "System.Runtime.Serialization.dll", "System.Xml.dll", "System.Numerics.dll")]
    if os.path.exists(os.path.join(LIB, "Facades", "netstandard.dll")):
        refs.append(os.path.join(LIB, "Facades", "netstandard.dll"))
    if nj:
        refs.append(nj)
    exe = os.path.join(OUT, "LogicTests.exe")
    args = ["dotnet", CSC, "-nologo", "-noconfig", "-nostdlib+", "-langversion:9.0", "-nullable:disable", "-target:exe",
            "-define:ABYSS_LOGIC_TESTS", f"-out:{exe}", "-warn:1"] + [f"-r:{r}" for r in refs] + srcs
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        print(out)
        print("BUILD FAILED")
        sys.exit(2)
    if out:
        print(out)
    if nj:
        import shutil
        shutil.copy(nj, OUT)
    env = dict(os.environ)
    env["ABYSS_DATA_DIR"] = os.path.join(ROOT, "Assets", "_Game", "Resources", "Data")
    rr = subprocess.run([MONO, exe] + sys.argv[1:], cwd=OUT, env=env)
    sys.exit(rr.returncode)


if __name__ == "__main__":
    main()
