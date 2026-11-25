#!/usr/bin/env python3
# Installs the Tokyo Night Storm chrome CSS, Sidebery CSS (through managed
# storage), profile-local Sidebery/Dark Reader XPIs (plus HKCU policy on
# Windows), and the user.js prefs needed by the theme.

import argparse
import json
import os
import re
import shutil
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

sideberyId = "{3c078156-979c-498b-8990-85f7987dd929}"
darkReaderId = "addon@darkreader.org"
# Copy the entry points too: userChrome.css carries the tab/sidebar hiding rules.
cssFiles = (
	"tokyo-night-storm.css",
	"tokyo-night-storm-content.css",
	"userChrome.css",
	"userContent.css",
)
extensions = {
	sideberyId: "https://addons.mozilla.org/firefox/downloads/latest/sidebery/latest.xpi",
	darkReaderId: "https://addons.mozilla.org/firefox/downloads/latest/darkreader/latest.xpi",
}
userPrefs = {
	"xpinstall.signatures.required": False,
	"svg.context-properties.content.enabled": True,
	"toolkit.legacyUserProfileCustomizations.stylesheets": True,
	# Sideloaded XPIs in the profile otherwise install disabled.
	"extensions.autoDisableScopes": 0,
	"extensions.enabledScopes": 15,
	# Scan profile XPIs before WebExtensions start, not after the browser is up.
	# Otherwise they show as enabled but do not run until toggled once.
	"extensions.startupScanScopes": 1,
}


def stamp():
	return datetime.now().strftime("%Y%m%d-%H%M%S")


def uniqueBackup(path):
	candidate = path.with_name(f"{path.name}.bak-{stamp()}")
	counter = 1
	while candidate.exists():
		candidate = path.with_name(f"{path.name}.bak-{stamp()}-{counter}")
		counter += 1
	return candidate


def writeText(path, text, dryRun):
	if dryRun:
		return
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="utf-8", newline="") as handle:
		handle.write(text)


def copyFile(source, target, dryRun):
	if dryRun:
		return
	target.parent.mkdir(parents=True, exist_ok=True)
	shutil.copy2(source, target)


def backup(path, dryRun):
	if not path.exists() or dryRun:
		return None
	target = uniqueBackup(path)
	if not dryRun:
		shutil.copy2(path, target)
	return target


def librewolfBase():
	if sys.platform == "win32":
		appdata = os.environ.get("APPDATA")
		return Path(appdata) / "librewolf" if appdata else None
	if sys.platform == "darwin":
		return Path.home() / "Library/Application Support/librewolf"
	return Path.home() / ".librewolf"


def findDefaultProfile(explicit):
	if explicit:
		return Path(explicit).expanduser()

	base = librewolfBase()
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

	profilesDir = base / "Profiles"
	if profilesDir.is_dir():
		candidates = [p for p in profilesDir.iterdir() if p.is_dir()]
		if candidates:
			return max(candidates, key=lambda p: p.stat().st_mtime)

	return None


def managedStorageDir(explicit):
	if explicit:
		return Path(explicit).expanduser()
	if sys.platform == "win32":
		appdata = os.environ.get("APPDATA")
		return Path(appdata) / "Mozilla/ManagedStorage" if appdata else None
	if sys.platform == "darwin":
		return Path.home() / "Library/Application Support/Mozilla/ManagedStorage"
	return Path.home() / ".mozilla/managed-storage"


def setWindowsRegistry(manifest, dryRun, remove=False):
	# Windows resolves managed manifests through the registry, not a fixed dir.
	import winreg

	keyPath = rf"Software\Mozilla\ManagedStorage\{sideberyId}"
	if dryRun:
		return
	if remove:
		try:
			winreg.DeleteKey(winreg.HKEY_CURRENT_USER, keyPath)
		except FileNotFoundError:
			pass
		return
	with winreg.CreateKey(winreg.HKEY_CURRENT_USER, keyPath) as key:
		winreg.SetValue(key, None, winreg.REG_SZ, str(manifest))


def installChrome(root, profile, dryRun):
	chromeDir = profile / "chrome"
	print(f"Chrome  : {chromeDir}")

	if not chromeDir.exists() and not dryRun:
		chromeDir.mkdir(parents=True)

	for name in cssFiles:
		source = root / "chrome" / name
		if not source.is_file():
			raise FileNotFoundError(f"Missing theme file: {source}")
		target = chromeDir / name
		saved = backup(target, dryRun) if name.startswith("user") else None
		copyFile(source, target, dryRun)
		status = f"updated (backup: {saved.name})" if saved else "installed"
		print(f"  + {name}: {status}")


def installSidebery(root, directory, dryRun):
	cssPath = root / "sideberry.css"
	if not cssPath.is_file():
		raise FileNotFoundError(f"Missing Sidebery CSS: {cssPath}")
	if directory is None:
		raise RuntimeError("Could not determine the managed storage directory.")

	manifest = directory / f"{sideberyId}.json"
	payload = {
		"name": sideberyId,
		"description": "Tokyo Night Storm — Sidebery",
		"type": "storage",
		"data": {"sidebarCSS": cssPath.read_text(encoding="utf-8")},
	}

	print(f"Sidebery: {manifest}")
	saved = backup(manifest, dryRun)
	if saved:
		print(f"  + backup: {saved.name}")
	writeText(manifest, json.dumps(payload, indent=2, ensure_ascii=False) + "\n", dryRun)
	print("  + sidebarCSS from sideberry.css")

	if sys.platform == "win32":
		setWindowsRegistry(manifest, dryRun)


def removeSidebery(directory, dryRun):
	if directory is None:
		raise RuntimeError("Could not determine the managed storage directory.")

	manifest = directory / f"{sideberyId}.json"
	print(f"Sidebery: remove {manifest}")
	if manifest.exists():
		saved = backup(manifest, dryRun)
		if not dryRun:
			manifest.unlink()
		if saved:
			print(f"  + renamed to: {saved.name}")
	else:
		print("  - nothing to remove")

	if sys.platform == "win32":
		setWindowsRegistry(manifest, dryRun, remove=True)


def downloadXpi(url, target, dryRun):
	if dryRun:
		return
	target.parent.mkdir(parents=True, exist_ok=True)
	with urllib.request.urlopen(url, timeout=60) as response:
		target.write_bytes(response.read())


def setWindowsExtensionPolicy(dryRun):
	# HKCU policy installs the same XPIs without touching the LibreWolf install.
	import winreg

	keyPath = r"Software\Policies\Mozilla\Firefox\Extensions\Install"
	if dryRun:
		return

	with winreg.CreateKey(winreg.HKEY_CURRENT_USER, keyPath) as key:
		values = []
		index = 1
		while True:
			try:
				values.append(winreg.QueryValue(key, str(index)))
			except FileNotFoundError:
				break
			index += 1

		for url in extensions.values():
			if url not in values:
				values.append(url)

		for index, value in enumerate(values, start=1):
			winreg.SetValueEx(key, str(index), 0, winreg.REG_SZ, value)

		index = len(values) + 1
		while True:
			try:
				winreg.DeleteValue(key, str(index))
			except FileNotFoundError:
				break
			index += 1


def installExtensions(profile, dryRun):
	extensionsDir = profile / "extensions"
	print(f"Add-ons : {extensionsDir}")

	for extensionId, url in extensions.items():
		target = extensionsDir / f"{extensionId}.xpi"
		downloadXpi(url, target, dryRun)
		print(f"  + {extensionId}.xpi")

	if sys.platform == "win32":
		setWindowsExtensionPolicy(dryRun)
		print("  + HKCU Extensions\\Install policy")


def addUserPrefs(profile, dryRun):
	path = profile / "user.js"
	text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
	lines = []

	for name, value in userPrefs.items():
		if isinstance(value, bool):
			rendered = "true" if value else "false"
		else:
			rendered = str(value)
		line = f'user_pref("{name}", {rendered});'
		if not re.search(rf'^\s*{re.escape(line)}\s*$', text, re.MULTILINE):
			lines.append(line)

	if not lines:
		print(f"User.js : {path} (already set)")
		return

	saved = backup(path, dryRun)
	addition = ""
	if not text:
		addition = "// Added by install.py\n"
	elif not text.endswith("\n"):
		addition = "\n"
	addition += "\n".join(lines) + "\n"

	writeText(path, text + addition, dryRun)
	print(f"User.js : {path}")
	print(f"  + {len(lines)} pref(s)")
	if saved:
		print(f"  + backup: {saved.name}")


def parseArgs():
	parser = argparse.ArgumentParser(
		description="Install the Tokyo Night Storm theme, Sidebery CSS, add-ons, and prefs."
	)
	parser.add_argument("--profile-path", dest="profilePath", help="LibreWolf profile folder")
	parser.add_argument("--managed-storage-path", dest="managedStoragePath", help="Override the managed storage folder")
	parser.add_argument("--skip-chrome", dest="skipChrome", action="store_true", help="Do not install userChrome/userContent CSS")
	parser.add_argument("--skip-sidebery", dest="skipSidebery", action="store_true", help="Do not install Sidebery CSS")
	parser.add_argument("--skip-extensions", dest="skipExtensions", action="store_true", help="Do not install Sidebery/Dark Reader XPIs")
	parser.add_argument("--skip-prefs", dest="skipPrefs", action="store_true", help="Do not write user.js prefs")
	parser.add_argument("--remove-sidebery", dest="removeSidebery", action="store_true", help="Remove Sidebery managed CSS")
	parser.add_argument("--dry-run", dest="dryRun", action="store_true", help="Show actions without writing files")
	return parser.parse_args()


def main():
	args = parseArgs()
	root = Path(__file__).resolve().parent

	print()
	print("Tokyo Night Storm — installer")
	if args.dryRun:
		print("Mode    : DRY RUN (no files will be written)")
	print()

	profile = None
	if not args.skipChrome or not args.skipPrefs or not args.skipExtensions:
		profile = findDefaultProfile(args.profilePath)
		if profile is None:
			raise RuntimeError("Could not find a LibreWolf profile. Pass --profile-path.")
		profile = profile.resolve()
		if not (profile / "prefs.js").exists():
			raise RuntimeError(f"That does not look like a profile folder (no prefs.js): {profile}")
		print(f"Profile : {profile}")

	if not args.skipChrome:
		installChrome(root, profile, args.dryRun)
		print()

	if args.removeSidebery:
		removeSidebery(managedStorageDir(args.managedStoragePath), args.dryRun)
	elif not args.skipSidebery:
		installSidebery(root, managedStorageDir(args.managedStoragePath), args.dryRun)

	if not args.skipExtensions:
		print()
		installExtensions(profile, args.dryRun)

	if not args.skipPrefs:
		print()
		addUserPrefs(profile, args.dryRun)

	print()
	print("Done. Restart LibreWolf to apply everything.")
	print("Extensions are profile-local XPIs; Sidebery CSS is managed and read-only.")
	print()


if __name__ == "__main__":
	main()
