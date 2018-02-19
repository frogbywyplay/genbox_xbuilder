from __future__ import print_function

import unittest

from xbuilder.plugin import XBuilderPlugin


class TestXBuilderRootfsPlugin(unittest.TestCase):
    def test_archive(self):
        plugin = XBuilderPlugin(dict(release=dict(archive_dir='/toto')), None, None, None)
        self.assertEqual(plugin._archive_dir('cat', 'pkg', '1.2.3', 'arch'), '/toto/cat/pkg/arch/1.2.3')  # pylint: disable=protected-access
