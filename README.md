# Small dwm session integration: Mint and Void

This checkout owns session assembly, **not** the four applications or a distro
compatibility framework. dmenu, dwm, dwmblocks and st-reflow retain their own
build/install targets and work independently. No C executable changes are needed.

```
LightDM -> stock Xsession wrapper -> /usr/local/bin/dwm-session
TTY -> startx -> ~/.xinitrc       -> /usr/local/bin/dwm-session
```

The desktop entry has no arguments. This avoids the font-name splitting seen
with `Exec=dwm -fn "DroidSansM Nerd Font Mono:size=10"` through wrappers that
expand command strings without preserving argument boundaries. Do not modify
Mint's global Xsession wrapper to fix this, or call startx from LightDM.

## Session policy

- 144 DPI, dwm bar font `DroidSansM Nerd Font Mono:size=10`.
- Optional dwmblocks and one available polkit agent; missing companions warn.
- Reuse the login's D-Bus session; use dbus-run-session only when absent.
  Update activation variables for dwm when the standard D-Bus utility is present.
  Concurrent graphical logins sharing one user bus also share its activation
  environment; the most recently started session wins.
- Mint/unknown systems: leave user audio services alone.
- Void: private `void-audio` helper starts PipeWire unless its default socket
  already exists. Requires the Void installer's WirePlumber/pipewire-pulse
  drop-ins and a valid PAM/elogind `XDG_RUNTIME_DIR`. It does not invent one.
- Small shell supervisor: wait for dwm, preserve its status, terminate/reap only
  tracked children on logout/signals. No restart loop, killall or pkill.
- No wallpaper, compositor, notification daemon, automatic locker, or desktop
  settings daemon. **Suspend does not lock the screen.** Add a proper locker
  and verified lock-before-suspend integration before relying on that security.

The private `distro-id` reads os-release. It is used only for audio policy,
never by the applications. Unknown distros use the conservative generic policy.
Hardware helpers should continue to select capabilities, not distro names.

Optional configuration is `~/.config/dwm/session.conf`; see
`session.conf.example`. This is trusted shell code, not a generated file.
Executable settings take a single name/path, not shell command strings.
Set `DWM_SESSION_AUDIO=none` if Void audio is managed elsewhere; `void` explicitly
opts into that policy on another system. DPI is a machine preference, not a
distro property; use `DWM_SESSION_DPI=none` to leave it untouched.

The launcher uses the inherited PATH (normally including /usr/local/bin from
login setup). Set `DWM_SESSION_WM=/usr/local/bin/dwm` to pin the intended build.
Keep session startup out of .profile/.xprofile so stock desktops are unaffected.
Do not start a second dwmblocks, audio server or polkit agent in those files.

## Prepare and test (no live installation)

```
make check
stage=$(mktemp -d)
make DESTDIR="$stage" install install-session
find "$stage" -type f
```

Tests use temporary installations and mock X/audio/window-manager programs.
`DESTDIR` is for staging: generated paths refer to the final destination.
`PREFIX` defaults to /usr/local; `SESSIONDIR` independently defaults to
/usr/share/xsessions, where standard LightDM installations look. Use installation
paths without whitespace or shell/sed metacharacters. For a nondefault prefix,
also adjust the example .xinitrc and login PATH.

## Install later, deliberately

First build/install the desired applications separately in their own checkouts.
Do not rerun a whole workstation provisioning script merely to fix a session.

```
sudo make install
# Inspect/back up an existing entry BEFORE replacing it:
# sudo cp -a /usr/share/xsessions/dwm.desktop /root/dwm.desktop.before-session
sudo make install-session
```

`make install` installs only the launcher and its private helpers.
`install-session` explicitly installs/replaces only `dwm.desktop`; it leaves
stock entries and the default session untouched. It neither installs nor restarts
LightDM. Keep the backup outside xsessions to avoid a duplicate menu entry.

For console startup, review/back up an existing ~/.xinitrc, then use the supplied
`xinitrc` (and make it executable). Its only action is `exec dwm-session` by
absolute path. This is opt-in: this project's Makefile never edits home files.

Log out normally and select dwm in LightDM. Do not restart LightDM while a
session contains unsaved work. A failure should return to the greeter, not loop.
The supervisor's diagnostics go to the display manager's session log (on this
Mint installation, ~/.xsession-errors). For console testing:

```
startx > "$HOME/dwm-startx.log" 2>&1
```

If another graphical session is active, use a free VT/display with appropriate
X-server permissions, or test after ending that session. Do not run a second WM
inside Cinnamon's existing display. Keep a working stock session for recovery.

## Distribution setup

### Mint

Preserve stock LightDM, slick-greeter, Cinnamon entries and systemd/PAM services.
The amended `~/.config/scripts/install-mint-apps` lists the missing dependencies
and optionally installs this launcher from `DWM_SESSION_DIR`. It does not
register LightDM sessions or change .xinitrc. That broad provisioning script
still has unrelated downloads and system changes; it is not a repair tool.

Relevant build packages:

```
build-essential pkg-config libx11-dev libxft-dev libxinerama-dev
libx11-xcb-dev libxcb-res0-dev libfontconfig-dev libfreetype-dev ncurses-bin
```

Session/helper packages (in addition to the existing X/LightDM/PipeWire stack):

```
xinit x11-xserver-utils dbus-daemon xdg-utils policykit-1-gnome
iw brightnessctl playerctl scrot xclip xsel
```

Install the chosen Nerd Fonts separately or select installed fonts. Do not
start PipeWire/WirePlumber manually on a normal Mint 22 user-service setup.
`wpctl status`, `systemctl --user status pipewire wireplumber`, and `loginctl
session-status` help diagnose services; a polkit agent cannot repair a broken
login/seat registration. Existing `has_option` Xsession warnings are a separate
packaged-wrapper issue: this project does not patch system files to hide them.

### Void

`../void-app-installer` retains XBPS/runit/network/PipeWire setup. Its core list
now explicitly includes brightnessctl and libxcb-devel. It installs this
launcher only if `DWM_SESSION_DIR` points at a prepared checkout (default:
`$SUCKLESS_DIR/mint-void-suckless`), otherwise leaves .xinitrc unchanged with a
message. It never fetches this integration implicitly. App clones use HTTPS,
so a fresh machine does not need GitHub SSH authentication to build them.

For LightDM, install the Void packages `lightdm` and a greeter such as
`lightdm-gtk3-greeter`, verify its greeter session name/configuration, then enable
the packaged LightDM runit service when ready. Keep the existing D-Bus service
and D-Bus-activated elogind arrangement. The usual service link is
`/var/service/lightdm -> /etc/sv/lightdm`; creating it may immediately start the
manager, so do this deliberately from a recovery console, not in an installer
run during graphical work. Register dwm with `make install-session` separately.
Check the installed LightDM session search path if it differs from the default.
Do not enable a second display manager alongside it.

Stock Xfce LightDM entries use their stock launcher. The managed console selector
still accepts `xfce`, now delegating to startxfce4 rather than imposing dwm's
session services. **Migration:** if Xfce previously relied on the generated
.xinitrc to start audio, configure PipeWire once through Xfce's session autostart
(or your existing user-service mechanism). The dwm Void helper is not a general
Xfce session manager. This deliberate separation keeps desktops independent.

The installer now writes a dwm-specific `dwm-portals.conf` instead of a global
`portals.conf`. Review any old global file yourself: it is not silently removed.

## Console and recovery

A real console is a getty on a spare VT (Ctrl+Alt+F-key), not a LightDM X session
named "console". Keep at least one enabled and verify login before changing
session files. Mint normally provides systemd gettys; Void uses runit agetty
services. No display-manager stop/chvt privilege wrapper is installed.

After installation, verify both LightDM and startx: font/DPI, terminal launch,
optional status, polkit authorization, audio, brightness and logout cleanup.
Test suspend only after saving work; test locking separately once configured.
The code has headless tests, not a claim of live dual-distro certification.

Rollback: restore the backed-up dwm.desktop and .xinitrc; select a stock session
or use a TTY. `make uninstall-session` removes only the dwm entry and `make
uninstall` removes the launcher/helpers. Neither removes applications, fonts,
packages, user configuration, or changes services. Restore a previous dwm entry
from backup rather than expecting uninstall to reconstruct it.
