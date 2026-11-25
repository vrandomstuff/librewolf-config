# AGENTS.md

Tokyo Night Storm CSS theme targeted at LibreWolf; regular Firefox is untested
and may not work. Targets Nova UI 157+; the chrome CSS includes legacy token
fallbacks.

## Repo shape

- `chrome/` is the shipped product. `userChrome.css` and `userContent.css` are
  entry points that import `tokyo-night-storm.css` and
  `tokyo-night-storm-content.css`; `userChrome.css` also hides the tab strip and
  sidebar header and moves window controls, so it is not just an import shim.
- `sideberry.css` is applied through Sidebery's managed `storage` manifest
  (per-user, not per-profile), not by editing Sidebery IndexedDB or settings.
- `install.py` is the only executable installer and the source of truth for
  install behavior.
- The static add-on/XPI route is gone from the current tree. Do not reintroduce
  `theme/`, `build.ps1`, `dist/`, or `preview.html` references into docs or
  commands.

## Installer behavior and constraints

- `python3 install.py` copies all four `chrome/*.css` files into
  `<profile>/chrome/`, including both entry points. It overwrites existing
  `userChrome.css`/`userContent.css` after timestamped `.bak-*` backups; it does
  not prepend imports to an existing file. The manual README path is different:
  keep your own entry files and add `@import` as the first line (only `@charset`
  may precede it).
- The installer writes `sideberry.css` into a `Mozilla/ManagedStorage`
  `{sideberyId}.json` manifest, appends missing prefs to `<profile>/user.js`,
  and downloads the latest Sidebery and Dark Reader XPIs from AMO into
  `<profile>/extensions/` (they are not vendored). `--dry-run` skips all writes
  and downloads.
- On Windows, managed storage is registered in HKCU
  (`Software\Mozilla\ManagedStorage\...`) and the same XPIs are also added to
  the HKCU extension-install policy. Elsewhere the manifest lives in
  `~/Library/Application Support/Mozilla/ManagedStorage` (macOS) or
  `~/.mozilla/managed-storage` (Linux).
- Write scope is strictly the selected profile, HKCU, and
  `Mozilla/ManagedStorage`. Never touch the LibreWolf install directory, its
  shipped `policies.json`, or the system policy folder.
- `xpinstall.signatures.required = false` only works in LibreWolf; regular
  Firefox releases ignore it, so do not rely on it for Firefox.
- Profile auto-detection reads `Default` from `installs.ini`/`profiles.ini`, then
  falls back to the newest directory under `Profiles`; the chosen folder must
  contain `prefs.js`. Pass `--profile-path` when detection is wrong. Sidebery-
  only runs (`--skip-chrome --skip-extensions --skip-prefs`) need no profile.
- `--remove-sidebery` deletes the managed manifest and Windows registry key; it
  does not restore a backed-up manifest. Existing `user*.css`, `user.js`, and
  Sidebery manifests are backed up as `.bak-*`, which `.gitignore` ignores.

## Commands

```sh
python3 install.py --dry-run    # safe preview; use `python` on Windows
python3 install.py              # mutates the real profile
python3 install.py --remove-sidebery
python3 install.py --help
```

Other flags: `--profile-path`, `--managed-storage-path`, `--skip-chrome`,
`--skip-sidebery`, `--skip-extensions`, `--skip-prefs`.

## Style, palette, verification

- Python 3 standard library only; use tabs and camelCase in `install.py`.
  Keep CLI flags kebab-case; do not rename `user_pref()` names, CSS selectors,
  Firefox design tokens, or Sidebery DOM classes — they are external APIs.
- The palette is duplicated in `chrome/tokyo-night-storm.css` (`--tn-*`),
  `chrome/tokyo-night-storm-content.css` (hard-coded hex), and `sideberry.css`
  (`--tn-*` subset). There is no generator or preview file; update all three for
  a palette change.
- No package manager, tests, linter, or CI. Verify with `--dry-run` and
  `--help`; functional checks require restarting LibreWolf and inspecting
  chrome, `about:` pages, and Sidebery.
