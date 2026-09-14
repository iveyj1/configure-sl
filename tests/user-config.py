#!/usr/bin/env python3
"""Test explicit user setup in temporary homes; never touch real dotfiles."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MAKE = shutil.which('make')


class UserConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.home = self.base / 'home'
        self.home.mkdir()
        self.bin = self.base / 'bin'
        self.bin.mkdir()
        # Model a normal user's UID even when a CI runner itself is root.
        (self.bin / 'id').write_text('#!/bin/sh\necho "${TEST_UID:-1000}"\n')
        (self.bin / 'id').chmod(0o755)
        for name in ('mkdir', 'cat'):
            (self.bin / name).symlink_to(shutil.which(name))
        self.env = dict(os.environ, HOME=str(self.home), PATH=str(self.bin),
                        XDG_CONFIG_HOME='', SUDO_USER='', TEST_UID='1000')

    def run_target(self, *args, **env):
        return subprocess.run([MAKE, '-s', 'install-user-config', *args], cwd=ROOT,
                              env=dict(self.env, **env), capture_output=True,
                              text=True, timeout=5)

    def test_create_then_preserve(self):
        result = self.run_target()
        self.assertEqual(result.returncode, 0, result.stderr)
        config = self.home / '.config'
        resources = config / 'X11/machine.resources'
        session = config / 'dwm/session.conf'
        self.assertEqual(resources.read_bytes(), (ROOT / 'machine.resources.example').read_bytes())
        self.assertEqual(session.read_bytes(), (ROOT / 'session.conf.example').read_bytes())
        resources.write_text('local font settings\n')
        session.write_text('local audio policy\n')
        resources.chmod(0o600)
        self.assertEqual(self.run_target().returncode, 0)
        self.assertEqual(resources.read_text(), 'local font settings\n')
        self.assertEqual(session.read_text(), 'local audio policy\n')
        self.assertEqual(resources.stat().st_mode & 0o777, 0o600)
        self.assertFalse((self.home / '.Xresources').exists())
        self.assertFalse((self.home / '.xinitrc').exists())

    def test_xdg_and_symlinks(self):
        config = self.base / 'custom config'
        (config / 'X11').mkdir(parents=True)
        (config / 'dwm').mkdir()
        target = self.base / 'shared'
        target.write_text('keep shared data\n')
        (config / 'X11/machine.resources').symlink_to(target)
        dangling = config / 'dwm/session.conf'
        dangling.symlink_to(self.base / 'missing')
        result = self.run_target(XDG_CONFIG_HOME=str(config))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(target.read_text(), 'keep shared data\n')
        self.assertTrue(dangling.is_symlink())
        self.assertFalse((self.base / 'missing').exists())
        self.assertFalse((self.home / '.config').exists())

    def test_reject_root_sudo_relative_path_and_staging(self):
        for env in ({'TEST_UID': '0'}, {'SUDO_USER': 'someone'}, {'XDG_CONFIG_HOME': 'relative'}):
            self.assertNotEqual(self.run_target(**env).returncode, 0)
        self.assertNotEqual(self.run_target(f'DESTDIR={self.base}/stage').returncode, 0)
        self.assertFalse((self.home / '.config').exists())

    def test_system_install_does_not_create_user_config(self):
        result = subprocess.run([MAKE, '-s', 'install', f'DESTDIR={self.base}/stage'],
                                cwd=ROOT, env=dict(os.environ, HOME=str(self.home)),
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.home / '.config').exists())


if __name__ == '__main__':
    unittest.main()
