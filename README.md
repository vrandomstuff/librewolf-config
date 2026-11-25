# Tokyo Night Storm for LibreWolf
__IMPORTANT:__ Regular firefox is not tested and may not work with this. Example: xpinstall.signatures.required does not do anything in a regular release but does work in LibreWolf.

A Tokyo Night Storm theme for the browser chrome and internal pages.

## Install with the installer (recommended)

Copies the CSS files into your profile, sets up Sidebery CSS, installs the
Sidebery/Dark Reader XPIs, and writes a `user.js` with all required prefs — no
`about:config` changes needed. Existing `user*.css` files are backed up. Nothing
in the LibreWolf install directory is modified.

```sh
python3 install.py --dry-run    # preview
python3 install.py              # install
```

On Windows use `python` instead of `python3`. The profile is auto-detected; to
set it explicitly:

```sh
python3 install.py --profile-path "/path/to/profile"
```

Other flags: `--skip-sidebery`, `--skip-extensions`, `--skip-prefs`,
`--skip-chrome`, `--remove-sidebery`, `--managed-storage-path <dir>`.

Restart LibreWolf.

## Manual install

1. `about:config` → `toolkit.legacyUserProfileCustomizations.stylesheets` → `true`.
2. Find your profile: `about:support` → **Profile Folder** → **Show in Finder**
   (macOS) / **Show in Explorer** (Windows) / **Show in File Manager** (Linux).

Copy these files from this repo's `chrome/` folder into `<profile>/chrome/`:

```
<profile>/chrome/
  tokyo-night-storm.css
  tokyo-night-storm-content.css
```

Keep your existing `userChrome.css`/`userContent.css` and add as their **first
line** (only `@charset` may come before `@import`):

```css
@import url("tokyo-night-storm.css");
```

```css
@import url("tokyo-night-storm-content.css");
```

The second import goes in `userContent.css` and is optional. For a fresh
profile, you can instead copy the whole `chrome/` folder over, which includes
entry-point `userChrome.css`/`userContent.css`.

Restart LibreWolf.
