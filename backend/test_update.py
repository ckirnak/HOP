import tempfile
import unittest
from pathlib import Path
from update import Updater, FILES


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'system'
        self.source = Path(self.tmp.name) / 'package' / 'backend'
        self.source.mkdir(parents=True)
        self.calls = []
        self.up = Updater(self.source, self.root, run=self.calls.append, health=lambda: True)
        for name, dest in FILES.items():
            target = self.up.target(dest)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('old')
            (self.source / name).write_text('# new\n')
        self.up.target('/opt/hop/VERSION').write_text('0.24.0')
        (self.source.parent / 'VERSION').write_text('0.25.0')
        (self.source / 'live.html').write_text('HOP v0.25.0')
        for dest in ['/etc/hop/ami.env', '/etc/systemd/system/hop.service', '/etc/asterisk/manager_custom.conf']:
            target = self.up.target(dest)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('preserve-existing-config')

    def tearDown(self):
        self.tmp.cleanup()

    def test_update_and_rollback_preserve_configuration(self):
        version, backup = self.up.apply()
        self.assertEqual(version, '0.25.0')
        self.assertEqual(self.up.current(), version)
        for dest in ['/etc/hop/ami.env', '/etc/asterisk/manager_custom.conf']:
            self.assertEqual(self.up.target(dest).read_text(), 'preserve-existing-config')
        self.assertEqual(self.up.restore(backup), '0.24.0')
        self.assertEqual(self.up.target('/opt/hop/server.py').read_text(), 'old')

    def test_failed_health_restores_old_files(self):
        results = iter([True, False, True])
        self.up.health = lambda: next(results)
        with self.assertRaises(RuntimeError):
            self.up.apply()
        self.assertEqual(self.up.current(), '0.24.0')
        self.assertEqual(self.up.target('/var/www/html/hop/live.js').read_text(), 'old')

    def test_unhealthy_initial_state_changes_nothing(self):
        self.up.health = lambda: False
        with self.assertRaises(RuntimeError):
            self.up.apply()
        self.assertEqual(self.calls, [])
        self.assertFalse(self.up.backups.exists())

    def test_downgrade_rejected(self):
        (self.source.parent / 'VERSION').write_text('0.23.0')
        with self.assertRaises(ValueError):
            self.up.check()

    def test_legacy_install_without_version_marker(self):
        self.up.target('/opt/hop/VERSION').unlink()
        self.up.target('/opt/hop/live.html').write_text('HOP v0.23.0')
        self.assertEqual(self.up.check(), ('0.23.0', '0.25.0'))
        _, backup = self.up.apply()
        self.up.restore(backup)
        self.assertFalse(self.up.target('/opt/hop/VERSION').exists())

    def test_symlink_target_rejected(self):
        target = self.up.target('/opt/hop/server.py')
        target.unlink()
        target.symlink_to(self.source / 'server.py')
        with self.assertRaises(ValueError):
            self.up.check()

    def test_incomplete_backup_does_not_stop_service(self):
        _, backup = self.up.apply()
        self.calls.clear()
        (backup / 'opt/hop/server.py').unlink()
        with self.assertRaises(ValueError):
            self.up.restore(backup)
        self.assertEqual(self.calls, [])


if __name__ == '__main__':
    unittest.main()
