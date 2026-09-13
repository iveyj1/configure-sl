# Small dwm session integration for Mint and Void

This repository installs a session launcher and a LightDM desktop entry. It does
not build or install dmenu, dwm, dwmblocks, or st-reflow.

Session paths:

- LightDM: `LightDM -> stock Xsession wrapper -> /usr/local/bin/dwm-session`
- Console: `startx -> ~/.xinitrc -> /usr/local/bin/dwm-session`

## Mint instructions

- Install the build packages:
  `build-essential pkg-config libx11-dev libxft-dev libxinerama-dev libx11-xcb-dev libxcb-res0-dev libfontconfig-dev libfreetype-dev ncurses-bin`.
- Install the session/helper packages:
  `xinit x11-xserver-utils dbus-daemon xdg-utils policykit-1-gnome iw brightnessctl playerctl scrot xclip xsel`.
-  *** Or run `installmintpkgs`
- Install the applications (`dmenu`, `dwm`, optional `dwmblocks`, and
  `st-reflow`) from their own checkouts.
- Install `DroidSansM Nerd Font Mono`, or set another installed font in
  `~/.config/dwm/session.conf`.
- Test and install the launcher from this checkout:
  ```sh
  make check
  sudo make install
  sudo make install-session
  ```
- Log out, select **dwm** in LightDM, and log in.
- For console startup, copy or merge the supplied `xinitrc` into `~/.xinitrc`,
  make it executable, and run `startx`.
- Verify the DPI/font, terminal launch, dwmblocks, polkit prompts, audio,
  brightness controls, and logout.
- If using `~/.config/scripts/install-mint-apps`, set `DWM_SESSION_DIR` to this
  checkout to install the launcher. The script does not register the LightDM
  entry or replace `~/.xinitrc`.

Mint uses its existing PipeWire/WirePlumber user services; the launcher does not
start another audio server.

## Void instructions

- Use `../void-app-installer` for the XBPS, runit, network, and PipeWire setup.
  Its core package list includes `brightnessctl` and `libxcb-devel`.
- Prepare the application checkouts and this checkout. To let the installer
  install the launcher, set `DWM_SESSION_DIR` to this directory; its default is
  `$SUCKLESS_DIR/mint-void-suckless`.
- Install `lightdm` and a greeter such as `lightdm-gtk3-greeter`.
- Verify the greeter name in the LightDM configuration and keep the packaged
  D-Bus service plus D-Bus-activated elogind setup.
- Enable the packaged LightDM runit service when ready. Its usual link is
  `/var/service/lightdm -> /etc/sv/lightdm`.
- Test and install the launcher and session entry:
  ```sh
  make check
  sudo make install
  sudo make install-session
  ```
- Log out, select **dwm** in LightDM, and log in.
- For console startup, use the installer-managed selector or copy/merge the
  supplied `xinitrc` into `~/.xinitrc`, make it executable, and run `startx`.
- Verify the DPI/font, terminal launch, dwmblocks, polkit prompts, audio,
  brightness controls, and logout.

On Void, the launcher starts its private `void-audio` helper when
`DWM_SESSION_AUDIO=auto`. The helper starts PipeWire only when the default
PipeWire socket is absent. It requires the installer's WirePlumber and
pipewire-pulse drop-ins and a PAM/elogind-provided `XDG_RUNTIME_DIR`.

## Session configuration

Optional configuration lives at `~/.config/dwm/session.conf`. Start with
`session.conf.example`. The file is sourced as trusted shell code; executable
settings accept one command name or path, not a shell command string.

Defaults:

- `DWM_SESSION_DPI=144`; use `none` to leave DPI and Qt settings unchanged.
- `DWM_SESSION_FONT='DroidSansM Nerd Font Mono:size=10'`.
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

## Contingencies

### Existing files or nonstandard paths

- Back up an existing `/usr/share/xsessions/dwm.desktop` before
  `make install-session`; store the backup outside `xsessions` to avoid a second
  menu entry.
- Review and merge an existing `~/.xinitrc` instead of overwriting it.
- `PREFIX` defaults to `/usr/local`; `SESSIONDIR` defaults independently to
  `/usr/share/xsessions`. If either differs locally, pass it to `make` and update
  `~/.xinitrc` and `PATH` as needed.
- To inspect an installation without changing the live system:
  ```sh
  stage=$(mktemp -d)
  make DESTDIR="$stage" install install-session
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
- Run `sudo make uninstall-session` to remove the dwm desktop entry and
  `sudo make uninstall` to remove the launcher/helpers. These targets do not
  remove applications, packages, fonts, user configuration, or services.
- Suspend does not lock the screen. Configure and test a locker with
  lock-before-suspend integration before depending on suspend for security.
