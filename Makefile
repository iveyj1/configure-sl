PREFIX ?= /usr/local
LIBEXECDIR ?= $(PREFIX)/libexec/dwm-session
# LightDM's standard system session directory, independent of binary PREFIX.
SESSIONDIR ?= /usr/share/xsessions

all:
	@echo 'No binaries to build. Use make check, install, or install-session.'

install:
	install -d "$(DESTDIR)$(PREFIX)/bin" "$(DESTDIR)$(LIBEXECDIR)"
	sed 's|@LIBEXECDIR@|$(LIBEXECDIR)|g' dwm-session > "$(DESTDIR)$(PREFIX)/bin/dwm-session"
	chmod 755 "$(DESTDIR)$(PREFIX)/bin/dwm-session"
	install -m 755 libexec/distro-id libexec/void-audio "$(DESTDIR)$(LIBEXECDIR)/"

# Explicit opt-in: ordinary installation never changes display-manager sessions.
install-session:
	install -d "$(DESTDIR)$(SESSIONDIR)"
	sed 's|@PREFIX@|$(PREFIX)|g' dwm.desktop > "$(DESTDIR)$(SESSIONDIR)/dwm.desktop"
	chmod 644 "$(DESTDIR)$(SESSIONDIR)/dwm.desktop"

uninstall:
	rm -f "$(DESTDIR)$(PREFIX)/bin/dwm-session"
	rm -f "$(DESTDIR)$(LIBEXECDIR)/distro-id" "$(DESTDIR)$(LIBEXECDIR)/void-audio"

uninstall-session:
	rm -f "$(DESTDIR)$(SESSIONDIR)/dwm.desktop"

check:
	@for script in dwm-session libexec/distro-id libexec/void-audio xinitrc; do sh -n "$$script" || exit; done
	python3 tests/session.py

.PHONY: all install install-session uninstall uninstall-session check
