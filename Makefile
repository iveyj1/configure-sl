PREFIX ?= /usr/local
LIBEXECDIR ?= $(PREFIX)/libexec/dwm-session
# LightDM's standard system session directory, independent of binary PREFIX.
SESSIONDIR ?= /usr/share/xsessions

all: help

help:
	@printf '%s\n' \
		'make check                         test scripts' \
		'make install-user-config           create missing user defaults (no sudo)' \
		'sudo make install-launcher         install dwm-session for startx/LightDM' \
		'sudo make install-lightdm-session  install optional LightDM desktop entry' \
		'sudo make uninstall-launcher       remove dwm-session and helpers' \
		'sudo make uninstall-lightdm-session  remove optional LightDM entry' \
		'' \
		'Compatibility aliases: install, install-session, uninstall, uninstall-session.'

# There are no generated files; support the common clean/build/install workflow.
clean:
	@:

install: install-launcher

install-launcher:
	install -d "$(DESTDIR)$(PREFIX)/bin" "$(DESTDIR)$(LIBEXECDIR)"
	sed 's|@LIBEXECDIR@|$(LIBEXECDIR)|g' dwm-session > "$(DESTDIR)$(PREFIX)/bin/dwm-session"
	chmod 755 "$(DESTDIR)$(PREFIX)/bin/dwm-session"
	install -m 755 libexec/distro-id libexec/void-audio "$(DESTDIR)$(LIBEXECDIR)/"

# Explicit user step: never called by install or distro provisioning scripts.
# Refuse sudo/root and staging to avoid writing into the wrong home directory.
install-user-config:
	@set -eu; \
	if [ "$$(id -u)" = 0 ] || [ -n "$${SUDO_USER:-}" ]; then \
		echo 'Run make install-user-config as your normal user, without sudo.' >&2; exit 1; \
	fi; \
	if [ -n "$(DESTDIR)" ]; then echo 'Use a temporary HOME/XDG_CONFIG_HOME, not DESTDIR, for user config.' >&2; exit 1; fi; \
	config="$${XDG_CONFIG_HOME:-$$HOME/.config}"; \
	case "$$config" in /*) ;; *) echo 'Config directory must be an absolute path.' >&2; exit 1;; esac; \
	mkdir -p "$$config/X11" "$$config/dwm"; \
	for pair in machine.resources.example:X11/machine.resources session.conf.example:dwm/session.conf; do \
		source=$${pair%%:*}; dest="$$config/$${pair#*:}"; \
		if [ -e "$$dest" ] || [ -L "$$dest" ]; then \
			printf 'Keeping %s\n' "$$dest"; \
		else \
			(umask 022; set -C; cat "$$source" > "$$dest"); \
			printf 'Created %s\n' "$$dest"; \
		fi; \
	done

# Explicit opt-in: ordinary installation never changes display-manager sessions.
install-session: install-lightdm-session

install-lightdm-session:
	install -d "$(DESTDIR)$(SESSIONDIR)"
	sed 's|@PREFIX@|$(PREFIX)|g' dwm.desktop > "$(DESTDIR)$(SESSIONDIR)/dwm.desktop"
	chmod 644 "$(DESTDIR)$(SESSIONDIR)/dwm.desktop"

uninstall: uninstall-launcher

uninstall-launcher:
	rm -f "$(DESTDIR)$(PREFIX)/bin/dwm-session"
	rm -f "$(DESTDIR)$(LIBEXECDIR)/distro-id" "$(DESTDIR)$(LIBEXECDIR)/void-audio"

uninstall-session: uninstall-lightdm-session

uninstall-lightdm-session:
	rm -f "$(DESTDIR)$(SESSIONDIR)/dwm.desktop"

check:
	@for script in dwm-session libexec/distro-id libexec/void-audio xinitrc; do sh -n "$$script" || exit; done
	python3 tests/session.py
	python3 tests/user-config.py

.PHONY: all help clean install install-launcher install-user-config install-session \
	install-lightdm-session uninstall uninstall-launcher uninstall-session \
	uninstall-lightdm-session check
