# AGENTS.md

LibreWolf/Firefox **static theme add-on** (WebExtension `theme`, MV2) using the
Tokyo Night Storm palette.

## What is actually in this repo

**The XPI is the focus.** `theme/` is the primary deliverable and the shipped
artifact: make theme changes there first, then mirror the palette into the CSS
files. The `chrome/` route is a supported secondary path that must be kept in
sync — it is not a separate design, just the same theme applied via
`userChrome.css`.

- `theme/` — installable static theme add-on: `manifest.json` + `icon.svg`.
  `build.ps1` zips the *contents* of `theme/` into `dist/tokyo-night-storm.xpi`
  (ZIP with `manifest.json` at the root). Anything placed in `theme/` ships in
  the add-on, so do not drop stray files there.
- `chrome/` — `userChrome.css` / `userContent.css` entry points that `@import`
  `tokyo-night-storm.css` (browser chrome) and
  `tokyo-night-storm-content.css` (`about:` pages / new tab). This path can
  style surfaces the static theme API cannot, but its colours must stay in sync
  with `theme/manifest.json`.
- `install.py` — copies `chrome/*.css` into a LibreWolf profile and prepends the
  imports, backing up any file it touches. Also writes `sideberry.css` into
  Sidebery's managed storage so its IndexedDB is never edited. Supports
  `--dry-run`, `--profile-path`, `--managed-storage-path`, `--skip-chrome`,
  `--skip-sidebery`, and `--remove-sidebery`.
- No package manager, tests, linter, CI, or git repo here. Do not look for npm
  scripts or lockfiles. Python 3 standard library only; do not add dependencies.

## Docs

`README.md` and the footer of `preview.html` document the CSS route (Options
A/B/C), the Sidebery managed-storage route, and the optional XPI. Keep them in
sync when the palette or install steps change.

Note: README targets Firefox/LibreWolf 160 + Nova, but
`theme/manifest.json` has `strict_min_version: "128.0"`.

## Commands

```sh
python3 install.py --dry-run         # preview chrome + Sidebery install
python3 install.py                   # install both
python3 install.py --remove-sidebery  # restore Sidebery's own CSS
```

```powershell
.\build.ps1                          # -> dist\tokyo-night-storm.xpi (overwrites)
.\build.ps1 -OutputDirectory <dir>   # custom output
```

There is no test or lint step. Verify a change by:

- loading `theme/manifest.json` via `about:debugging` → **Load Temporary Add-on**
  (fastest iteration, no build), or
- rebuilding and installing `dist\tokyo-night-storm.xpi` with
  `xpinstall.signatures.required = false` in LibreWolf (`about:config`).

`dist/` is build output and gitignored; never edit it by hand.

## Palette / version edits

- `theme/manifest.json` → `theme.colors` is the source of truth for the add-on.
  Keep `properties.color_scheme` and `content_color_scheme` set to `dark`.
- **Keep `chrome/` and `sideberry.css` in sync with the XPI.** The same hex
  values are duplicated in `chrome/tokyo-night-storm.css` (as `--tn-*`),
  `chrome/tokyo-night-storm-content.css` (hard-coded), `sideberry.css` (as
  `--tn-*`), `preview.html`'s `:root` (as `--bg`, `--blue`, `--magenta`, …) and
  the README table. A palette change must touch all of them; `preview.html` is
  hand-written, not generated.
- Bump `version` in `theme/manifest.json` for any release, then rebuild the XPI.
