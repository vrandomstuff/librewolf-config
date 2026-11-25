# Tokyo Night Storm for LibreWolf / Firefox

A Tokyo Night Storm theme for the browser chrome: storm-blue surfaces, lavender
text, neon-blue accents, and a dark treatment for Firefox/LibreWolf's internal
pages.

![Tokyo Night Storm UI preview](preview.png)

Targets **LibreWolf 160 / Firefox 160** with the Nova UI (157+). The CSS
includes pre-Nova fallbacks for the main surfaces, so it still works if Nova is
switched off.

## What it styles

- Window frame, tab strip, toolbars, bookmarks bar
- Tabs (selected, hover, vertical, tab groups) and close buttons
- Address bar, focused/open state, results dropdown, identity/page actions
- Menus, panels, downloads, extension popups, tooltips
- Sidebar (Nova and classic), find bar, notification bars, status panel
- Window controls (Windows/Linux titlebar buttons)
- Private windows get a Tokyo Night magenta accent
- `about:` pages: new tab, Settings, Add-ons, `about:config`, Downloads,
  private browsing

## Palette

| Token | Hex | Used for |
| --- | --- | --- |
| `--tn-bg` | `#24283b` | toolbars, page background |
| `--tn-bg-dark` | `#1f2335` | frame, sidebar, panels |
| `--tn-bg-darker` | `#1b1e2d` | address bar, inputs |
| `--tn-bg-highlight` | `#292e42` | hover / selected surfaces |
| `--tn-border` | `#3b4261` | borders and separators |
| `--tn-fg` | `#c0caf5` | primary text |
| `--tn-fg-dark` | `#a9b1d6` | secondary text, inactive tabs |
| `--tn-comment` | `#565f89` | placeholders, disabled text |
| `--tn-blue` | `#7aa2f7` | accent, focus, selected tab rail |
| `--tn-blue0` | `#3d59a1` | selection / active background |
| `--tn-cyan` | `#7dcfff` | URLs, links, hover accent |
| `--tn-magenta` | `#bb9af7` | private browsing accent |
| `--tn-yellow` | `#e0af68` | bookmarked star |
| `--tn-red` | `#f7768e` | close-button hover |

## Install

### Requirements

1. LibreWolf 157+ (Nova UI on, which is the default).
2. In `about:config`, make sure this is `true`:

   ```
   toolkit.legacyUserProfileCustomizations.stylesheets
   ```

3. Know where your profile is. Easiest: open `about:profiles`, find the profile
   marked **Default**, and click **Open Folder** under **Root Directory**.
   Common locations:

   ```
   Windows: %APPDATA%\librewolf\Profiles\<random>.default-release
   macOS:   ~/Library/Application Support/librewolf/Profiles/<random>.default-release
   Linux:   ~/.librewolf
   ```

### Option A — installer script (recommended)

`install.py` copies the theme files into your profile's `chrome` folder and
adds the `@import` lines to the top of your existing `userChrome.css` and
`userContent.css`. It backs up any file it modifies. It also installs
`sideberry.css` through Sidebery's managed storage (see below).

```sh
python3 install.py --dry-run    # preview
python3 install.py              # install
```

On Windows use `python` instead of `python3`. The profile is auto-detected from
`installs.ini` / `profiles.ini`; pass one explicitly if needed:

```sh
python3 install.py --profile-path "/path/to/profile"
```

Useful flags:

```sh
python3 install.py --skip-sidebery          # chrome CSS only
python3 install.py --skip-chrome            # Sidebery CSS only
python3 install.py --remove-sidebery        # undo the Sidebery CSS
python3 install.py --managed-storage-path <dir>  # override manifest location
```

Then restart LibreWolf.

### Option B — manual, keeping your existing customisations

Your current `userChrome.css` is **not** replaced. Put the two theme files next
to it:

```
<profile>\
  chrome\
    userChrome.css                 <- your existing file
    userContent.css                <- optional, your existing file
    tokyo-night-storm.css          <- copy from this repo's chrome\
    tokyo-night-storm-content.css  <- copy from this repo's chrome\
```

Then add these as the **first line** of `userChrome.css`:

```css
@import url("tokyo-night-storm.css");
```

and, if you use `userContent.css`, the first line of that file:

```css
@import url("tokyo-night-storm-content.css");
```

Only `@charset` may appear before an `@import`. Restart the browser afterward.

### Option C — fresh profile

Copy this repo's `chrome` folder into your profile root, replacing the `chrome`
folder only if you do not already have customisations there. The included
`chrome/userChrome.css` and `chrome/userContent.css` are just the import lines.

### Optional — installable theme add-on

The `theme` folder is a standard static theme. It paints the frame, toolbar,
sidebar, URL bar, menus and new-tab page with the same palette. It is optional:
`userChrome.css` already covers the chrome, and `userContent.css` covers the new
tab page.

```powershell
.\build.ps1
# -> dist\tokyo-night-storm.xpi
```

Install it:

1. `about:config` → `xpinstall.signatures.required` → `false`
   (LibreWolf accepts unsigned add-ons; Firefox Release does not).
2. `about:addons` → gear icon → **Install Add-on From File…** → pick the XPI.

Or load `theme/manifest.json` temporarily via `about:debugging` → **This
LibreWolf** → **Load Temporary Add-on**.

Using the add-on and the CSS together is fine; the CSS wins where they overlap.

### Sidebery (managed CSS)

`sideberry.css` is applied through Sidebery's `storage.managed` support, which
Sidebery checks before its own saved CSS. That means the theme is installed as
a plain JSON file, not by editing Sidebery's IndexedDB:

```
Windows: %APPDATA%\Mozilla\ManagedStorage\{3c078156-979c-498b-8990-85f7987dd929}.json
macOS:   ~/Library/Application Support/Mozilla/ManagedStorage/{3c078156-979c-498b-8990-85f7987dd929}.json
Linux:   ~/.mozilla/managed-storage/{3c078156-979c-498b-8990-85f7987dd929}.json
```

On Windows the installer also creates the matching
`HKCU\Software\Mozilla\ManagedStorage\{3c078156-...}` registry key. Managed CSS
is read-only inside Sidebery and overrides anything typed in its settings.
Run `python3 install.py --remove-sidebery` to restore Sidebery's own CSS, then
restart LibreWolf. The manifest is per-user, not per-profile.

## Customising

The whole theme derives from the variables at the top of
`chrome/tokyo-night-storm.css`. Append overrides to the bottom of that file (or
to your own CSS after the import) instead of editing rules throughout.

```css
/* Different accent */
:root {
  --tn-accent: var(--tn-magenta);
  --tn-accent-soft: #4a3a6b;
}

/* Squarer UI */
:root {
  --tn-radius: 4px;
  --tn-tab-radius: 4px;
}

/* Larger address-bar text */
#urlbar-input { font-size: 1.05em !important; }
```

## Notes

- **Existing customisations:** the theme never changes tab-strip visibility or
  toolbar layout. A `userChrome.css` that hides the horizontal tab strip (for
  example to use Sidebery) and moves the window controls keeps working; the
  theme only colours those elements.
- **Nova:** built for the Nova UI. If you turn Nova off in LibreWolf's
  Appearance settings, the legacy tokens included in the theme keep the main
  surfaces and address bar themed, but Nova-only details (sidebar layout, tab
  group styling, some radii) will differ.
- **LibreWolf's own theme:** LibreWolf ships with a dark theme. The theme is
  independent of it; you can keep **Dark** selected in Appearance.
- **Sidebery / other sidebar extensions:** they draw their own content. The
  browser sidebar frame is themed; Sidebery's panel is themed separately through
  `sideberry.css` and managed storage (see above). Other sidebar extensions need
  their own settings with the palette above.
- **Private windows** switch the accent from blue to magenta automatically.
- **`userContent.css`** affects internal `about:` pages only. Website scrollbar
  and selection snippets are included but commented out at the bottom of
  `tokyo-night-storm-content.css`.
- **Reset:** remove the `@import` line(s), or restore the `.bak-*` files created
  by the installer.

## Files

```
chrome/
  userChrome.css                  entry point (@import)
  userContent.css                 entry point (@import)
  tokyo-night-storm.css           browser chrome theme
  tokyo-night-storm-content.css   about: pages / new tab
theme/
  manifest.json                   optional static theme add-on
  icon.svg
sideberry.css                     Sidebery custom CSS (managed storage)
install.py                        safe installer for LibreWolf profiles
build.ps1                         builds dist/tokyo-night-storm.xpi
preview.html                      hand-built UI mockup
preview.png                       screenshot of the mockup
```

## Credits

- Palette: [Tokyo Night](https://github.com/enkia/tokyo-night-vscode-theme) by
  enkia (MIT).
- Built against Firefox/LibreWolf's Nova UI and the theme/token names documented
  by Mozilla.

## License

MIT — see [LICENSE](LICENSE).
