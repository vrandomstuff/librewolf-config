#!/usr/bin/env python3
# Installs the Tokyo Night Storm chrome CSS and, optionally, the Sidebery CSS
# through Sidebery's managed storage so no profile IndexedDB editing is needed.

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

SIDEBERY_ID = "{3c078156-979c-498b-8990-85f7987dd929}"
THEME_FILES = ("tokyo-night-storm.css", "tokyo-night-storm-content.css")
IMPORTS = {
    "userChrome.css": '@import url("tokyo-night-storm.css");',
    "userContent.css": '@import url("tokyo-night-storm-content.css");',
}
PREF_NAME = "toolkit.legacyUserProfileCustomizations.stylesheets"


def stamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def unique_backup(path):
    candidate = path.with_name(f"{path.name}.bak-{stamp()}")
    counter = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.name}.bak-{stamp()}-{counter}")
        counter += 1
    return candidate


def write_text(path, text, dry_run):
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def copy_file(source, target, dry_run):
    if dry_run:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def backup(path, dry_run):
    if not path.exists() or dry_run:
        return None
    target = unique_backup(path)
    if not dry_run:
        shutil.copy2(path, target)
    return target


def librewolf_base():
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        return Path(appdata) / "librewolf" if appdata else None
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/librewolf"
    return Path.home() / ".librewolf"


def find_default_profile(explicit):
    if explicit:
        return Path(explicit).expanduser()

    base = librewolf_base()
    if base is None:
        return None

    for name in ("installs.ini", "profiles.ini"):
        ini = base / name
        if not ini.exists():
            continue
        text = ini.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"^\s*Default\s*=\s*(.+?)\s*$", text, re.MULTILINE)
        if match:
            candidate = (base / match.group(1)).expanduser()
            if candidate.is_dir():
                return candidate

    profiles_dir = base / "Profiles"
    if profiles_dir.is_dir():
        candidates = [p for p in profiles_dir.iterdir() if p.is_dir()]
        if candidates:
            return max(candidates, key=lambda p: p.stat().st_mtime)

    return None


def pref_enabled(profile):
    for name in ("prefs.js", "user.js"):
        path = profile / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        pattern = rf'user_pref\(\s*"{re.escape(PREF_NAME)}"\s*,\s*true\s*\)'
        if re.search(pattern, text):
            return True
    return False


def add_import(path, line, dry_run):
    if not path.exists():
        write_text(path, line + "\n", dry_run)
        return "created"

    # The repo's userChrome/userContent are import-only stubs, so never copy
    # them over an existing profile file; prepend instead.
    text = path.read_text(encoding="utf-8", errors="replace")
    if line in text:
        return "already imported"

    saved = backup(path, dry_run)
    write_text(path, line + "\n" + text, dry_run)
    return f"updated (backup: {saved.name})" if saved else "updated"


def managed_storage_dir(explicit):
    if explicit:
        return Path(explicit).expanduser()
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        return Path(appdata) / "Mozilla/ManagedStorage" if appdata else None
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/Mozilla/ManagedStorage"
    return Path.home() / ".mozilla/managed-storage"


def set_windows_registry(manifest, dry_run, remove=False):
    # Windows resolves managed manifests through the registry, not a fixed dir.
    import winreg

    key_path = rf"Software\Mozilla\ManagedStorage\{SIDEBERY_ID}"
    if dry_run:
        return
    if remove:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except FileNotFoundError:
            pass
        return
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        winreg.SetValue(key, None, winreg.REG_SZ, str(manifest))


def install_chrome(root, profile, dry_run):
    chrome_dir = profile / "chrome"
    print(f"Chrome  : {chrome_dir}")

    if not chrome_dir.exists() and not dry_run:
        chrome_dir.mkdir(parents=True)

    for name in THEME_FILES:
        source = root / "chrome" / name
        if not source.is_file():
            raise FileNotFoundError(f"Missing theme file: {source}")
        copy_file(source, chrome_dir / name, dry_run)
        print(f"  + {name}")

    for name, line in IMPORTS.items():
        status = add_import(chrome_dir / name, line, dry_run)
        print(f"  + {name}: {status}")

    if not pref_enabled(profile):
        print("Action needed:")
        print(f"  Set {PREF_NAME} = true in about:config.")


def install_sidebery(root, directory, dry_run):
    css_path = root / "sideberry.css"
    if not css_path.is_file():
        raise FileNotFoundError(f"Missing Sidebery CSS: {css_path}")
    if directory is None:
        raise RuntimeError("Could not determine the managed storage directory.")

    manifest = directory / f"{SIDEBERY_ID}.json"
    payload = {
        "name": SIDEBERY_ID,
        "description": "Tokyo Night Storm — Sidebery",
        "type": "storage",
        "data": {"sidebarCSS": css_path.read_text(encoding="utf-8")},
    }

    print(f"Sidebery: {manifest}")
    saved = backup(manifest, dry_run)
    if saved:
        print(f"  + backup: {saved.name}")
    write_text(manifest, json.dumps(payload, indent=2, ensure_ascii=False) + "\n", dry_run)
    print("  + sidebarCSS from sideberry.css")

    if sys.platform == "win32":
        set_windows_registry(manifest, dry_run)


def remove_sidebery(directory, dry_run):
    if directory is None:
        raise RuntimeError("Could not determine the managed storage directory.")

    manifest = directory / f"{SIDEBERY_ID}.json"
    print(f"Sidebery: remove {manifest}")
    if manifest.exists():
        saved = backup(manifest, dry_run)
        if not dry_run:
            manifest.unlink()
        if saved:
            print(f"  + renamed to: {saved.name}")
    else:
        print("  - nothing to remove")

    if sys.platform == "win32":
        set_windows_registry(manifest, dry_run, remove=True)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Install the Tokyo Night Storm chrome CSS and Sidebery CSS."
    )
    parser.add_argument("--profile-path", help="LibreWolf profile folder")
    parser.add_argument("--managed-storage-path", help="Override the managed storage folder")
    parser.add_argument("--skip-chrome", action="store_true", help="Do not install userChrome/userContent CSS")
    parser.add_argument("--skip-sidebery", action="store_true", help="Do not install Sidebery CSS")
    parser.add_argument("--remove-sidebery", action="store_true", help="Remove Sidebery managed CSS")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without writing files")
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(__file__).resolve().parent

    print()
    print("Tokyo Night Storm — installer")
    if args.dry_run:
        print("Mode    : DRY RUN (no files will be written)")
    print()

    if not args.skip_chrome:
        profile = find_default_profile(args.profile_path)
        if profile is None:
            raise RuntimeError("Could not find a LibreWolf profile. Pass --profile-path.")
        profile = profile.resolve()
        if not (profile / "prefs.js").exists():
            raise RuntimeError(f"That does not look like a profile folder (no prefs.js): {profile}")
        print(f"Profile : {profile}")
        install_chrome(root, profile, args.dry_run)
        print()

    if args.remove_sidebery:
        remove_sidebery(managed_storage_dir(args.managed_storage_path), args.dry_run)
    elif not args.skip_sidebery:
        install_sidebery(root, managed_storage_dir(args.managed_storage_path), args.dry_run)

    print()
    print("Done. Restart LibreWolf to apply the theme.")
    print("Sidebery CSS is managed and read-only; remove the manifest to use its UI again.")
    print()


if __name__ == "__main__":
    main()
