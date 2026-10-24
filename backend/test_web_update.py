import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from web_update import release_asset, unpack


class WebUpdateTests(unittest.TestCase):
    def release(self):
        return {'tag_name': 'v0.27.0', 'assets': [{'name': 'HOP-0.27.0-source.zip',
                'browser_download_url': 'https://github.com/ckirnak/HOP/releases/download/v0.27.0/HOP-0.27.0-source.zip',
                'digest': 'sha256:' + 'a' * 64}]}

    def test_current_release_needs_no_download(self):
        self.assertIsNone(release_asset(self.release(), '0.27.0'))

    def test_only_fixed_repository_asset_is_accepted(self):
        release = self.release()
        self.assertEqual(release_asset(release, '0.26.0')[0], '0.27.0')
        release['assets'][0]['browser_download_url'] = 'https://example.org/package.zip'
        with self.assertRaises(ValueError):
            release_asset(release, '0.26.0')

    def test_missing_digest_and_prerelease_rejected(self):
        for field, value in [('digest', None), ('digest', 'md5:abc')]:
            release = self.release()
            release['assets'][0][field] = value
            with self.assertRaises(ValueError):
                release_asset(release, '0.26.0')
        release = self.release(); release['prerelease'] = True
        with self.assertRaises(ValueError):
            release_asset(release, '0.26.0')

    def test_archive_path_traversal_rejected_before_extraction(self):
        for name in ['hop-0.27.0/../../escape', '/absolute', 'other/file']:
            data = io.BytesIO()
            with zipfile.ZipFile(data, 'w') as zipped:
                zipped.writestr(name, 'bad')
            with tempfile.TemporaryDirectory() as folder:
                with self.assertRaises(ValueError):
                    unpack(data.getvalue(), Path(folder), '0.27.0')
                self.assertFalse((Path(folder) / 'hop-0.27.0').exists())


if __name__ == '__main__':
    unittest.main()
