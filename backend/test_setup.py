import unittest
from unittest.mock import patch
import setup


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.paths = patch.object(setup.Path, 'exists', return_value=False)
        self.paths.start()
        self.addCleanup(self.paths.stop)

    def test_non_linux_stops(self):
        with patch.object(setup.platform, 'system', return_value='Windows'):
            self.assertTrue(setup.preflight())

    def test_non_root_stops(self):
        with patch.object(setup.platform, 'system', return_value='Linux'), patch.object(setup.os, 'geteuid', return_value=1000, create=True):
            self.assertIn('root', setup.preflight()[0])

    def test_preflight_failure_never_runs_installer(self):
        with patch.object(setup.sys, 'argv', ['setup.py']), patch.object(setup, 'preflight', return_value=['collision']), patch.object(setup.subprocess, 'run') as run:
            self.assertEqual(setup.main(), 1)
            run.assert_not_called()

    def test_check_only_does_not_install(self):
        with patch.object(setup.sys, 'argv', ['setup.py', '--check']), patch.object(setup, 'preflight', return_value=[]), patch.object(setup.subprocess, 'run') as run:
            self.assertEqual(setup.main(), 0)
            run.assert_not_called()

    def test_cancel_does_not_install(self):
        with patch.object(setup.sys, 'argv', ['setup.py']), patch.object(setup, 'preflight', return_value=[]), patch('builtins.input', return_value=''), patch.object(setup.subprocess, 'run') as run:
            self.assertEqual(setup.main(), 0)
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
