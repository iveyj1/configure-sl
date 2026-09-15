# Small dwm session integration for Mint and Void

This repository installs a session launcher and a LightDM desktop entry. It does
not build or install dmenu, dwm, dwmblocks, or st-reflow.

Session paths:

- LightDM: `LightDM -> stock Xsession wrapper -> /usr/local/bin/dwm-session`
- Console: `startx -> ~/.xinitrc -> /usr/local/bin/dwm-session`

## Mint instructions

- Install build/session dependencies with
  `../mint-app-installer/installmintdeps` (moved out of this repository).
  That repo owns Mint APT provisioning; see its README for the package list and
  the optional full personal `install-mint-apps` bootstrap.
- Install the applications (`dmenu`, `dwm`, optional `dwmblocks`, and
  `st-reflow`) from their own checkouts.
- Install the desired fonts (optionally using
  `../mint-app-installer/install-debian-nerd-fonts`). Run
  `make install-user-config` **without sudo** to create missing local defaults.
  Edit `~/.config/X11/machine.resources` per machine; supplied font sizes are
  all 11 points, at 144 DPI. Existing files/symlinks are never overwritten.
- Test and install the launcher from this checkout:
  ```sh
  make check
  sudo make install-launcher
  sudo make install-lightdm-session  # optional; only for LightDM
  ```
- Log out, select **dwm** in LightDM, and log in.
- For console startup, copy or merge the supplied `xinitrc` into `~/.xinitrc`,
  make it executable, and run `startx`. Do not run `dwm-session` directly from
  a console: `startx` must create the X display first.
- Verify the DPI/font, terminal launch, dwmblocks, polkit prompts, audio,
  brightness controls, and logout.
- If using `../mint-app-installer/install-mint-apps`, `DWM_SESSION_DIR` defaults
  to `~/.local/src/configure-sl`; override it for a different checkout.
  The script optionally installs the launcher but does not create user defaults,
  register the LightDM entry, or replace `~/.xinitrc`.

Mint uses its existing PipeWire/WirePlumber user services; the launcher does not
start another audio server.

## Void instructions

- Use `../void-app-installer` for the XBPS, runit, network, and PipeWire setup.
  Its core package list includes `brightnessctl` and `libxcb-devel`.
- Prepare the application checkouts and this checkout. Install this launcher's
  `install-launcher` target before using the installer-managed `~/.xinitrc`;
  its dwm branch delegates to `/usr/local/bin/dwm-session`.
- Run `make install-user-config` here as your normal user to create any missing
  machine/session defaults; review the font/DPI values before logging in.
- Install `lightdm` and a greeter such as `lightdm-gtk3-greeter`.
- Verify the greeter name in the LightDM configuration and keep the packaged
  D-Bus service plus D-Bus-activated elogind setup.
- Enable the packaged LightDM runit service when ready. Its usual link is
  `/var/service/lightdm -> /etc/sv/lightdm`.
- Test and install the launcher and, if used, the LightDM session entry:
  ```sh
  make check
  sudo make install-launcher
  sudo make install-lightdm-session  # optional; only for LightDM
  ```
- Log out, select **dwm** in LightDM, and log in.
- For console startup, use the installer-managed selector or copy/merge the
  supplied `xinitrc` into `~/.xinitrc`, make it executable, and run `startx`.
  The selector delegates its dwm branch to `dwm-session`; do not run the launcher
  directly from a console because it requires the display created by `startx`.
- Verify the DPI/font, terminal launch, dwmblocks, polkit prompts, audio,
  brightness controls, and logout.

On Void, the launcher starts its private `void-audio` helper when
`DWM_SESSION_AUDIO=auto`. The helper starts PipeWire only when the default
PipeWire socket is absent. It requires the installer's WirePlumber and
pipewire-pulse drop-ins and a PAM/elogind-provided `XDG_RUNTIME_DIR`.

## Configuration ownership

- `mint-app-installer` and `void-app-installer`: distro packages, provisioning
  and service policy. No runtime compatibility framework.
- Each application repository: its own build, install and helper scripts.
- `configure-sl` (this repo): shared session launcher, desktop entry and examples.
- `dotrepo`: shared preferences such as the symlinked `~/.Xresources`.
- Local `~/.config/X11/machine.resources`: per-machine fonts/DPI, not automatically
  distributed through dotrepo.

The target names describe their scope: `install-launcher` installs the launcher
used by both startup paths; `install-lightdm-session` installs only the optional
LightDM menu entry; and `install-user-config` creates local defaults. The older
`install` and `install-session` names remain compatibility aliases.

`make install-user-config` explicitly creates missing `X11/machine.resources`
and `dwm/session.conf` under `${XDG_CONFIG_HOME:-$HOME/.config}`. It refuses
sudo/root and DESTDIR, preserves existing files (including dangling symlinks),
and never edits .Xresources, .xinitrc or dotrepo. System `make install` and the
distro provisioning scripts do not invoke this target. Tests use temporary
homes; no live user configuration is created by `make check`.

## Session configuration

Optional configuration lives at `~/.config/dwm/session.conf`. Start with
`session.conf.example`. The file is sourced as trusted shell code; executable
settings accept one command name or path, not a shell command string.

Defaults:

- `DWM_SESSION_WM=dwm`; use `/usr/local/bin/dwm` to pin that installation.
- `DWM_SESSION_BLOCKS=auto`; use `none` to disable dwmblocks.
- `DWM_SESSION_POLKIT=auto`; use `none` or an executable path to override it.
- `DWM_SESSION_AUDIO=auto`; use `none` when audio is managed elsewhere, or
  `void` to opt into the Void policy on another distribution.

The launcher:

- reuses the login D-Bus session, or uses `dbus-run-session` when no bus exists;
- updates the standard D-Bus activation environment when the utility exists;
- starts at most one detected polkit agent and optional dwmblocks;
- waits for dwm, preserves its exit status, and terminates only tracked child
  processes at logout;
- does not start a wallpaper, compositor, notification daemon, locker, or
  desktop settings daemon.

## Per-machine fonts (no rebuild after initial installation)

The launcher merges `~/.Xresources` first, then
`${XDG_CONFIG_HOME:-~/.config}/X11/machine.resources`. Keep shared colors in the
first file and local font/DPI settings in the second. Example:

```text
Xft.dpi: 144
dwm.font: DroidSansM Nerd Font Mono:size=11
dmenu.font: DroidSansM Nerd Font Mono:size=11
st.font: JetBrainsMono Nerd Font Mono:size=11
```

`DWM_SESSION_FONT` and `DWM_SESSION_DPI` are retired and ignored. Remove them
from old session.conf files. The launcher passes `dwm.font` as one quoted `-fn`
argument; dwm itself does not parse resources. Without it, the bar uses
`monospace:size=11`. If Xft.dpi is absent, the launcher leaves DPI/Qt settings
alone. The sample keeps this machine's existing 144 DPI.

The independently installed dmenu repository now supplies `dmenu-font`, a small
wrapper that queries `dmenu.font` on each invocation (fallback monospace size 11).
Explicit `-fn` arguments still win. `dmenu_run`, the dwm keymap/tag rename, and
st's menu helpers use this wrapper when available, otherwise plain dmenu.
Raw `dmenu` remains unchanged: use `dmenu-font` in other personal scripts if you
want this policy. No script depends on this session repository for menu fonts.

st already reads `st.font` at startup; `st -f` overrides it and per-window zoom
is still available. Its compiled fallback is now size 11 too.

After editing the machine file, merge it for this X display:

```sh
xrdb -merge ~/.config/X11/machine.resources
```

New menus and terminals then use the new size. Existing st windows retain their
font/zoom; the bar requires a fresh dwm session. Editing the file alone takes
effect on the next dwm-session login. Other desktop sessions can merge the same
file explicitly; the launcher does not change their startup files.

Initial migration: build/install updated dwm and dmenu from their own repos,
install updated st-reflow (including its helpers), and `sudo make install-launcher` here
for the updated launcher. No new desktop entry or LightDM restart is needed.
After that, font changes require only resource edits, not recompilation.

## Contingencies

### Existing files or nonstandard paths

- Back up an existing `/usr/share/xsessions/dwm.desktop` before
  `make install-lightdm-session`; store the backup outside `xsessions` to avoid a second
  menu entry.
- Review and merge an existing `~/.xinitrc` instead of overwriting it.
- `PREFIX` defaults to `/usr/local`; `SESSIONDIR` defaults independently to
  `/usr/share/xsessions`. If either differs locally, pass it to `make` and update
  `~/.xinitrc` and `PATH` as needed.
- To inspect an installation without changing the live system:
  ```sh
  stage=$(mktemp -d)
  make DESTDIR="$stage" install-launcher install-lightdm-session
  find "$stage" -type f
  ```
  Generated paths still refer to the final `PREFIX`.

### Session or service conflicts

- Do not start dwmblocks, an audio server, or a polkit agent again from
  `.profile` or `.xprofile`.
- Do not launch a second window manager inside an existing Cinnamon or Xfce
  display. Use another permitted VT/display or end the active session first.
- Do not enable LightDM alongside another display manager. Creating Void's
  `/var/service/lightdm` link can start LightDM immediately, so perform that step
  from a text console when graphical work is closed.
- Concurrent graphical logins that share one user D-Bus use one activation
  environment; the most recently started session supplies its display values.
- Void's console `xfce` selection delegates to `startxfce4`. If an older
  generated `.xinitrc` started audio for Xfce, move that startup to Xfce
  autostart or an existing user-service mechanism.
- The Void installer writes `dwm-portals.conf`, not a global `portals.conf`;
  review any older global file manually.

### Startup failures

- LightDM diagnostics normally go to its session log; on Mint this is commonly
  `~/.xsession-errors`.
- Capture console diagnostics with
  `startx > "$HOME/dwm-startx.log" 2>&1`.
- A missing optional dwmblocks or polkit agent produces a warning. A polkit
  agent cannot correct broken PAM, seat, or elogind registration.
- On Void, verify `XDG_RUNTIME_DIR`, the PipeWire socket, installer drop-ins,
  and elogind/PAM setup. Use `DWM_SESSION_AUDIO=none` if another mechanism owns
  audio.
- On Mint, inspect audio/session state with `wpctl status`,
  `systemctl --user status pipewire wireplumber`, and `loginctl session-status`.
  Packaged `has_option` Xsession warnings are outside this project.
- If LightDM uses a nonstandard session search directory, set `SESSIONDIR` when
  installing the desktop entry.

### Recovery and removal

- Keep a working stock desktop entry and a verified getty on a spare VT.
- Restore backed-up `dwm.desktop` or `~/.xinitrc` files to roll back.
- Run `sudo make uninstall-lightdm-session` to remove the dwm desktop entry and
  `sudo make uninstall-launcher` to remove the launcher/helpers. These targets do not
  remove applications, packages, fonts, user configuration, or services.
- Suspend does not lock the screen. Configure and test a locker with
  lock-before-suspend integration before depending on suspend for security.
