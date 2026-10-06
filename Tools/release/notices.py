"""Collect inspected notices, or stage them after the parent finishes a Windows build.

python Tools/release/notices.py --collect
python Tools/release/notices.py --stage Build/Windows
Neither mode starts Unity or builds a player. Staging never copies source or package caches.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
CREDITS = ROOT / "Assets/_Game/Resources/Credits"
PACKAGES = (
    "com.unity.ai.navigation", "com.unity.burst", "com.unity.collections",
    "com.unity.inputsystem", "com.unity.mathematics", "com.unity.nuget.newtonsoft-json",
    "com.unity.pipeline", "com.unity.render-pipelines.core", "com.unity.render-pipelines.universal",
    "com.unity.render-pipelines.universal-config", "com.unity.shadergraph",
    "com.unity.timeline", "com.unity.ugui",
)
PAGES = (
    "overview", "provenance", "pretendard", "black_han_sans", "liberation_sans",
    "newtonsoft", "rendering", "burst", "pipeline", "unity_packages",
    "unity_companion", "unity_distribution", "scope",
)


def collect():
    lock = json.loads((ROOT / "Packages/packages-lock.json").read_text(encoding="utf-8"))["dependencies"]
    manifest = json.loads((ROOT / "Packages/manifest.json").read_text(encoding="utf-8"))["dependencies"]
    packages = {}
    for name in PACKAGES:
        candidates = []
        for folder in sorted((ROOT / "Library/PackageCache").glob(name + "@*")):
            metadata = json.loads((folder / "package.json").read_text(encoding="utf-8"))
            if metadata["name"] == name and metadata["version"] == lock[name]["version"]:
                candidates.append(folder)
        if len(candidates) != 1:
            raise RuntimeError(f"Need exactly one local cache for {name} {lock[name]['version']}; found {len(candidates)}")
        packages[name] = candidates[0]

    inputs = []
    outputs = {}

    def notice(path, first=None, last=None):
        data = path.read_bytes()
        text = data.decode("utf-8-sig")
        source = path.relative_to(ROOT).as_posix()
        if first is not None:
            text = "".join(text.splitlines(keepends=True)[first - 1:last])
            source += f" (lines {first}-{last}; license comment verbatim)"
        inputs.append(f"{source}\nSHA-256 of complete source file: {hashlib.sha256(data).hexdigest()}")
        return f"Source: {source}\n\n{text}" + ("" if text.endswith("\n") else "\n")

    fonts = {
        "pretendard": "Assets/_Game/Fonts/Pretendard-LICENSE.txt",
        "black_han_sans": "Assets/_Game/Fonts/BlackHanSans-OFL.txt",
        "liberation_sans": "Assets/TextMesh Pro/Fonts/LiberationSans - OFL.txt",
    }
    for key, path in fonts.items():
        # The full source is appended without paraphrasing, including every copyright and OFL term.
        outputs[key] = notice(ROOT / path)
    outputs["newtonsoft"] = notice(packages["com.unity.nuget.newtonsoft-json"] / "Third Party Notices.md")
    outputs["burst"] = notice(packages["com.unity.burst"] / "Third Party Notices.md")
    outputs["pipeline"] = notice(packages["com.unity.pipeline"] / "Third Party Notices.md")
    core = packages["com.unity.render-pipelines.core"]
    urp = packages["com.unity.render-pipelines.universal"]
    outputs["rendering"] = "RENDERING AND MATHEMATICS — INSTALLED PACKAGE NOTICES\n\n" + "\n\n".join((
        notice(urp / "Third Party Notices.md"),
        notice(core / "ShaderLibrary/ACES.hlsl", 8, 59),
        notice(core / "ShaderLibrary/Coverage.hlsl", 1, 23),
        notice(urp / "Shaders/PostProcessing/SubpixelMorphologicalAntialiasing.hlsl", 1, 27),
        notice(packages["com.unity.mathematics"] / "Unity.Mathematics/Noise/LICENSE"),
    ))
    outputs["unity_packages"] = "UNITY PACKAGE COPYRIGHT AND LICENSE NOTICES\n\n" + "\n\n".join(
        notice(packages[name] / "LICENSE.md") for name in PACKAGES
    )
    inventory = "\n".join(f"{name}: local cache {lock[name]['version']}" for name in PACKAGES)
    discrepancies = "\n".join(
        f"{name}: manifest requests {manifest[name]}, lock/cache resolves {lock[name]['version']}"
        for name in PACKAGES if name in manifest and manifest[name] != lock[name]["version"]
    ) or "No manifest/lock version discrepancy for the inspected packages."
    outputs["scope"] = (
        "THIRD-PARTY NOTICES — SCOPE AND SOURCE RECORD\n\n"
        "Directly inspected facts\n"
        "The notices in this collection come from the local font sources and installed Unity runtime-capable packages listed below. "
        "Local license and notice texts are reproduced in full; shader license comments are reproduced verbatim with their source line ranges. "
        "Full Unity Companion and Unity Package Distribution terms are reproduced separately from Unity's primary-source pages, because the local packages contain links rather than the complete terms.\n\n"
        "Package inventory (not a claim that every package component ships in the player)\n" + inventory + "\n\n"
        "Version resolution record\n" + discrepancies + "\n\n"
        "Conservative notice inclusion / Legal interpretation boundary\n"
        "This collection retains the available notices for the listed installed packages without predicting linker stripping or shader inclusion. "
        "For example, the Burst notice includes compiler/development dependencies, and the renderer notices include source headers even when an individual shader may not be shipped. "
        "Their presence here does not claim that those components are present in the final binary, nor that copyright holders endorse the game. "
        "Editor IDE/test packages and authoring-tool executables are outside this player notice collection. "
        "No Blender, Python, NumPy or Pillow executable/library is copied into distribution by the notice-staging helper.\n\n"
        "Unity player engine boundary\n"
        "Unity runtime engine binaries and Unity built-in modules are governed separately by the applicable Unity engine terms. "
        "This collection is not a replacement for an engine license, and makes no claim of full engine/IP clearance or legal eligibility. "
        "The installed Editor/Data/PlaybackEngines/windowsstandalonesupport roots, its External and Variations/mono directories, "
        "and Editor/Data/MonoBleedingEdge roots inspected locally did not expose a distribution-wide Windows player/Mono notice bundle. "
        "Any engine-supplied notices included with the final player must remain with that player. Actual final binary contents and publisher engine-license eligibility require separate release review.\n\n"
        "Conditional missing source, not an asserted shipped dependency\n"
        "The installed URP Shaders/Terrain/WavingGrass.shader and WavingGrassBillboard.shader state: "
        "'Copyright (c) 2016 Unity Technologies. MIT license (see license.txt)'. "
        "The referenced license.txt is absent from the inspected package root and Terrain directory. "
        "This does not establish that these unused package shaders ship with the game; if a distribution later includes them, retrieve their actual referenced license from the applicable Unity source distribution. "
        "No missing license wording has been invented here.\n\n"
        "Publisher and asset-rights boundary\n"
        "A legal publisher identity, author identities, registrations, contracts, rights assignments and AI-service contractual rights cannot be established by the inspected repository. "
        "No such identities or clearance assertions are supplied. Project provenance is a source/process record, not a legal ownership guarantee.\n\n"
        "Source manifest\n" + "\n\n".join(inputs) + "\n\n"
        "Primary-source full terms\n"
        "https://unity.com/legal/licenses/unity-companion-license (body v1.4; retrieved 2026-10-06)\n"
        "https://unity.com/legal/licenses/unity-package-distribution-license (body v2.1; retrieved 2026-10-06)\n\n"
        "Reproduce local collection: python Tools/release/notices.py --collect\n"
        "Stage only after a completed Windows player build: python Tools/release/notices.py --stage Build/Windows\n"
        "The stage operation copies this collection only; it does not build, inspect or certify the player.\n"
    )
    CREDITS.mkdir(parents=True, exist_ok=True)
    # Read maintained provenance and primary-source terms before writing any generated output.
    for key in PAGES:
        if key not in outputs:
            outputs[key] = (CREDITS / (key + ".txt")).read_text(encoding="utf-8")
    for key, text in outputs.items():
        if key not in ("overview", "provenance", "unity_companion", "unity_distribution"):
            (CREDITS / (key + ".txt")).write_text(text, encoding="utf-8", newline="\n")
    combined = (
        "심연의 미궁 / ABYSS — THIRD-PARTY NOTICES AND SOURCE PROVENANCE\n"
        "See SCOPE AND SOURCE RECORD for inclusion boundaries. Original license text follows; "
        "the collection does not replace any license or establish ownership/clearance.\n\n"
    )
    for key in PAGES:
        combined += "=" * 72 + "\n" + key.upper() + "\n" + "=" * 72 + "\n\n" + outputs[key] + "\n\n"
    (ROOT / "THIRD_PARTY_NOTICES.txt").write_text(combined, encoding="utf-8", newline="\n")
    print("Collected full notices into Assets/_Game/Resources/Credits/ and THIRD_PARTY_NOTICES.txt")


def stage(target):
    target = Path(target)
    if not target.is_absolute():
        target = ROOT / target
    target = target.resolve()
    players = [exe for exe in target.glob("*.exe") if (target / (exe.stem + "_Data")).is_dir()]
    if not players:
        raise RuntimeError(f"No completed Unity Windows player layout at {target}; finish the build before staging notices")
    sources = [ROOT / "THIRD_PARTY_NOTICES.txt"] + [CREDITS / (key + ".txt") for key in PAGES]
    for source in sources:
        if not source.is_file():
            raise FileNotFoundError(source)
    destination = target / "Notices"
    destination.mkdir(exist_ok=True)
    shutil.copyfile(sources[0], target / sources[0].name)
    for source in sources[1:]:
        shutil.copyfile(source, destination / source.name)
    print(f"Staged THIRD_PARTY_NOTICES.txt and {len(PAGES)} readable notice files at {target}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--collect", action="store_true")
    mode.add_argument("--stage", metavar="PLAYER_DIRECTORY")
    args = parser.parse_args()
    if args.collect:
        collect()
    else:
        stage(args.stage)


if __name__ == "__main__":
    main()
