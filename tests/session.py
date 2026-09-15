#!/usr/bin/env python3
"""Headless tests: staged files, fake WM/audio/bus; no live session changes."""
import os
from pathlib import Path
import signal
import shutil
import sys
import socket
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Session(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.prefix = self.base / 'local'
        subprocess.run(['make', '-s', 'install-launcher', 'install-lightdm-session',
                        f'PREFIX={self.prefix}', f'SESSIONDIR={self.base}/sessions'],
                       cwd=ROOT, check=True)
        self.bin = self.prefix / 'bin'
        self.launcher = self.bin / 'dwm-session'
        self.lib = self.prefix / 'libexec/dwm-session'
        self.env = dict(os.environ, HOME=str(self.base), XDG_CONFIG_HOME=str(self.base / 'config'),
                        PATH=str(self.bin), DISPLAY=':fake', DBUS_SESSION_BUS_ADDRESS='fake',
                        XDG_RUNTIME_DIR=str(self.base), DWM_SESSION_AUDIO='none',
                        DWM_SESSION_POLKIT='none', DWM_SESSION_BLOCKS='none',
                        DWM_SESSION_WM='dwm', OUT=str(self.base))
        (self.bin / 'awk').symlink_to(shutil.which('awk'))
        (self.base / '.Xresources').write_text(
            'Xft.dpi: 144\ndwm.font: DroidSansM Nerd Font Mono:size=11\n')
        self.mock('dwm', 'printf "%s\\n" "$#" "$1" "$2" > "$OUT/args"; exit 7')
        self.mock('xrandr', 'printf "%s\\n" "$@" > "$OUT/dpi"')
        xrdb = self.bin / 'xrdb'
        xrdb.write_text(f'#!{sys.executable}\n'
                        'import json, os, pathlib, sys\n'
                        'db = pathlib.Path(os.environ["OUT"]) / "resources"\n'
                        'data = json.loads(db.read_text()) if db.exists() else {}\n'
                        'if sys.argv[1] == "-query":\n'
                        '    print("\\n".join(k+": "+v for k,v in data.items()))\n'
                        'else:\n'
                        '    for line in pathlib.Path(sys.argv[2]).read_text().splitlines():\n'
                        '        if ":" in line:\n'
                        '            k,v=line.split(":",1); data[k.strip()]=v.strip()\n'
                        '    db.write_text(json.dumps(data))\n')
        xrdb.chmod(0o755)

    def mock(self, name, body):
        path = self.bin / name
        path.write_text('#!/bin/sh\n' + body + '\n')
        path.chmod(0o755)

    def run_session(self, **env):
        return subprocess.run([str(self.launcher)], env=dict(self.env, **env),
                              capture_output=True, text=True, timeout=5)

    def test_font_dpi_and_exit_status(self):
        result = self.run_session()
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertEqual((self.base / 'args').read_text().splitlines(),
                         ['2', '-fn', 'DroidSansM Nerd Font Mono:size=11'])
        self.assertEqual((self.base / 'dpi').read_text(), '--dpi\n144\n')
        desktop = (self.base / 'sessions/dwm.desktop').read_text()
        self.assertIn(f'Exec={self.launcher}\n', desktop)
        self.assertNotIn('-fn', desktop)

    def test_missing_optionals_nonfatal(self):
        result = self.run_session(DWM_SESSION_BLOCKS='auto', DWM_SESSION_POLKIT='/missing/agent')
        self.assertEqual(result.returncode, 7)
        self.assertIn('dwmblocks not installed', result.stderr)
        self.assertIn('polkit agent not found', result.stderr)

    def test_missing_wm_or_display(self):
        self.assertEqual(self.run_session(DWM_SESSION_WM='/missing/wm').returncode, 127)
        self.assertEqual(self.run_session(DISPLAY='').returncode, 1)

    def test_bus_only_when_missing(self):
        self.mock('dbus-run-session', 'echo bus > "$OUT/bus"; shift; '
                  'export DBUS_SESSION_BUS_ADDRESS=mock; exec "$@"')
        self.assertEqual(self.run_session().returncode, 7)
        self.assertFalse((self.base / 'bus').exists())
        self.assertEqual(self.run_session(DBUS_SESSION_BUS_ADDRESS='').returncode, 7)
        self.assertTrue((self.base / 'bus').exists())

    def test_activation_environment(self):
        self.mock('dbus-update-activation-environment',
                  'printf "%s\\n" "$@" > "$OUT/activation"; '
                  'printf "%s" "$XDG_CURRENT_DESKTOP" > "$OUT/desktop"')
        self.assertEqual(self.run_session().returncode, 7)
        self.assertEqual((self.base / 'desktop').read_text(), 'dwm')
        args = (self.base / 'activation').read_text().splitlines()
        self.assertIn('XDG_CURRENT_DESKTOP', args)
        self.assertNotIn('--all', args)

    def test_machine_override(self):
        config = self.base / 'config/X11'
        config.mkdir(parents=True)
        (config / 'machine.resources').write_text('dwm.font: Local Font:size=11\nXft.dpi: 96\n')
        self.assertEqual(self.run_session(DWM_SESSION_FONT='ignored:size=7').returncode, 7)
        self.assertIn('Local Font:size=11', (self.base / 'args').read_text())
        self.assertEqual((self.base / 'dpi').read_text(), '--dpi\n96\n')

    def test_without_resources(self):
        (self.bin / 'xrdb').unlink()
        self.assertEqual(self.run_session().returncode, 7)
        self.assertIn('monospace:size=11', (self.base / 'args').read_text())
        self.assertFalse((self.base / 'dpi').exists())

    def test_audio_policy(self):
        # A fake helper records selection, synchronizing via the mock WM.
        (self.lib / 'void-audio').write_text('#!/bin/sh\necho audio > "$OUT/audio"\n')
        self.mock('dwm', 'i=0; while [ ! -f "$OUT/audio" ] && [ "$i" -lt 100000 ]; do i=$((i+1)); done; exit 7')
        for distro in ('linuxmint', 'unknown', 'void'):
            (self.lib / 'distro-id').write_text(f'#!/bin/sh\necho {distro}\n')
            self.assertEqual(self.run_session(DWM_SESSION_AUDIO='auto').returncode, 7)
            self.assertEqual((self.base / 'audio').exists(), distro == 'void')

    def test_void_audio_existing_socket(self):
        self.mock('pipewire', 'echo started > "$OUT/audio"')
        helper = self.lib / 'void-audio'
        sock = socket.socket(socket.AF_UNIX)
        self.addCleanup(sock.close)
        sock.bind(str(self.base / 'pipewire-0'))
        subprocess.run([str(helper)], env=self.env, check=True, timeout=5)
        self.assertFalse((self.base / 'audio').exists())
        sock.close()
        (self.base / 'pipewire-0').unlink()
        subprocess.run([str(helper)], env=self.env, check=True, timeout=5)
        self.assertTrue((self.base / 'audio').exists())

    def test_normal_exit_cleans_companion(self):
        import sys
        self.mock('dwm', f'exec {sys.executable} -c \'import os, time; '
                  'p=os.environ["OUT"]+"/companion.pid"; '
                  'exec("while not os.path.exists(p): time.sleep(.01)"); '
                  'raise SystemExit(7)\'')
        path = self.bin / 'dwmblocks'
        path.write_text(f'#!{sys.executable}\nimport os, time\n'
                        'open(os.environ["OUT"]+"/companion.pid", "w").write(str(os.getpid()))\n'
                        'while True: time.sleep(1)\n')
        path.chmod(0o755)
        self.assertEqual(self.run_session(DWM_SESSION_BLOCKS='auto').returncode, 7)
        with self.assertRaises(ProcessLookupError):
            os.kill(int((self.base / 'companion.pid').read_text()), 0)

    def test_signal_cleans_owned_children(self):
        # Python mocks have reliable signal handling and do not spawn grandchildren.
        import sys
        for name in ('dwm', 'dwmblocks'):
            path = self.bin / name
            path.write_text(f'#!{sys.executable}\nimport os, signal, time\n'
                            f'open(os.environ["OUT"] + "/{name}.pid", "w").write(str(os.getpid()))\n'
                            'while True: time.sleep(1)\n')
            path.chmod(0o755)
        proc = subprocess.Popen([str(self.launcher)], env=dict(self.env, DWM_SESSION_BLOCKS='auto'),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(100):
                if all((self.base / f'{name}.pid').exists() for name in ('dwm', 'dwmblocks')):
                    break
                time.sleep(.02)
            else:
                self.fail('children did not start')
            pids = [int((self.base / f'{name}.pid').read_text()) for name in ('dwm', 'dwmblocks')]
            proc.send_signal(signal.SIGTERM)
            self.assertEqual(proc.wait(timeout=5), 143)
            for pid in pids:
                with self.assertRaises(ProcessLookupError):
                    os.kill(pid, 0)
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            for name in ('dwm', 'dwmblocks'):
                pidfile = self.base / f'{name}.pid'
                if pidfile.exists():
                    try:
                        os.kill(int(pidfile.read_text()), signal.SIGTERM)
                    except ProcessLookupError:
                        pass


if __name__ == '__main__':
    unittest.main()
