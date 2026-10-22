"""Build and smoke-test native installers without changing personal data."""
import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from version import VERSION
TARGET = sys.argv[1]
PACKAGES = ROOT / "packages"
SOURCE = PACKAGES / f"Folio-{TARGET}"


def run(*args):
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True)


def smoke(binary):
    command = [sys.executable, ROOT / "test_executable.py", binary]
    if TARGET == "Linux":
        command = ["xvfb-run", "-a", *command]
    run(*command)


if TARGET == "Windows":
    compiler = shutil.which("iscc")
    if not compiler:
        candidates = sorted(Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")).glob("Inno Setup */ISCC.exe"))
        if not candidates:
            raise RuntimeError("Inno Setup compiler not installed")
        compiler = candidates[-1]
    artifact = PACKAGES / "Folio-Windows-Setup.exe"
    run(compiler, f"/DAppVersion={VERSION}", f"/DRepoRoot={ROOT}",
        f"/DSourceDir={SOURCE}", f"/DOutputDir={PACKAGES}", ROOT / "packaging/windows/Folio.iss")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        installation = Path(tmp) / "Folio"
        args = [artifact, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-", f"/DIR={installation}"]
        try:
            run(*args)
            sentinel = installation / "upgrade-preserved.txt"
            sentinel.write_text("synthetic upgrade fixture", encoding="utf-8")
            run(*args)
            assert sentinel.read_text(encoding="utf-8") == "synthetic upgrade fixture"
            smoke(installation / "Folio.exe")
        finally:
            uninstaller = installation / "unins000.exe"
            if uninstaller.exists():
                run(uninstaller, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART")
elif TARGET == "macOS":
    artifact = PACKAGES / "Folio-macOS.dmg"
    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / "Folio"
        staging.mkdir()
        shutil.copytree(SOURCE / "Folio.app", staging / "Folio.app", symlinks=True)
        (staging / "Applications").symlink_to("/Applications", target_is_directory=True)
        shutil.copy2(SOURCE / "LEGGIMI.txt", staging / "LEGGIMI.txt")
        run("hdiutil", "create", "-volname", "Folio", "-srcfolder", staging,
            "-ov", "-format", "UDZO", artifact)
        mount = Path(tmp) / "mounted"
        mount.mkdir()
        run("hdiutil", "attach", "-nobrowse", "-readonly", "-mountpoint", mount, artifact)
        try:
            smoke(mount / "Folio.app/Contents/MacOS/Folio")
        finally:
            run("hdiutil", "detach", mount)
elif TARGET == "Linux":
    artifact = PACKAGES / "Folio-Linux-amd64.deb"
    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / "deb"
        app = staging / "opt/folio"
        app.mkdir(parents=True)
        shutil.copytree(SOURCE, app, dirs_exist_ok=True)
        (app / "Folio").chmod(0o755)
        desktop = staging / "usr/share/applications/folio.desktop"
        desktop.parent.mkdir(parents=True)
        desktop.write_text("[Desktop Entry]\nType=Application\nName=Folio\nComment=Biblioteca offline\nExec=/opt/folio/Folio\nIcon=folio\nTerminal=false\nCategories=Education;Office;\n", encoding="utf-8")
        icon = staging / "usr/share/icons/hicolor/scalable/apps/folio.svg"
        icon.parent.mkdir(parents=True)
        shutil.copy2(ROOT / "assets/folio-logo.svg", icon)
        control = staging / "DEBIAN/control"
        control.parent.mkdir()
        control.write_text(f"Package: folio\nVersion: {VERSION.replace('.dev', '~dev')}\nSection: education\nPriority: optional\nArchitecture: amd64\nMaintainer: Folio <234798021+antoniorasulo89@users.noreply.github.com>\nDepends: libc6 (>= 2.39), libx11-6, libxext6, libxrender1, libxft2, fontconfig\nHomepage: https://github.com/antoniorasulo89/folio\nDescription: Folio - Biblioteca offline\n Applicazione desktop per copie personali dei libri digitali.\n", encoding="utf-8")
        run("dpkg-deb", "--build", "--root-owner-group", staging, artifact)
        run("dpkg-deb", "--info", artifact)
        extracted = Path(tmp) / "extracted"
        run("dpkg-deb", "--extract", artifact, extracted)
        smoke(extracted / "opt/folio/Folio")
else:
    raise ValueError(TARGET)

artifact.with_suffix(artifact.suffix + ".sha256").write_text(
    hashlib.sha256(artifact.read_bytes()).hexdigest() + "  " + artifact.name + "\n", encoding="utf-8")
print("Installer verified:", artifact.name, platform.machine())
