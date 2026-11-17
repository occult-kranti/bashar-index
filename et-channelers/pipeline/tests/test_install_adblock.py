"""Offline archive safety checks; no browser, download or extension is installed."""
import io
import stat
import unittest
import zipfile

from pipeline import install_adblock as subject


class ArchiveTests(unittest.TestCase):
    def archive(self, names):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as bundle:
            for name in names:
                bundle.writestr(name, b'{}')
        data.seek(0)
        return zipfile.ZipFile(data)

    def test_normal_extension_tree_is_accepted(self):
        with self.archive(['manifest.json', 'js/background.js']) as bundle:
            self.assertEqual(len(subject.checked_entries(bundle)), 2)

    def test_windows_and_posix_escape_and_device_entries_are_rejected(self):
        for name in ('../outside', '/outside', 'C:/outside', 'js\\..\\..\\outside', 'file:stream', 'CON.txt', 'tail. '):
            with self.subTest(name=name), self.archive(['manifest.json', name]) as bundle:
                with self.assertRaisesRegex(ValueError, 'unsafe_extension_entry'):
                    subject.checked_entries(bundle)

    def test_case_collision_is_rejected(self):
        with self.archive(['manifest.json', 'MANIFEST.JSON']) as bundle:
            with self.assertRaisesRegex(ValueError, 'duplicate_extension_entry'):
                subject.checked_entries(bundle)

    def test_symlink_is_rejected(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as bundle:
            bundle.writestr('manifest.json', b'{}')
            link = zipfile.ZipInfo('escape')
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            bundle.writestr(link, b'../outside')
        data.seek(0)
        with zipfile.ZipFile(data) as bundle:
            with self.assertRaisesRegex(ValueError, 'unsafe_extension_entry'):
                subject.checked_entries(bundle)


if __name__ == '__main__':
    unittest.main()
