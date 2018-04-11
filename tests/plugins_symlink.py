# Copyright (C) 2006-2018 Wyplay, All Rights Reserved.
# This file is part of xbuilder.
#
# xbuilder is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# xbuilder is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; see file COPYING.
# If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import os
import shutil
import tempfile
import unittest

from xbuilder.plugins.symlink import XBuilderSymlinkPlugin


class TestXBuilderRootfsPlugin(unittest.TestCase):
    def setUp(self):
        self.tmpfl = tempfile.NamedTemporaryFile(delete=(os.getenv('KEEP_TMP') is None))
        self.tmpd = tempfile.mkdtemp()
        self.tmpwd = os.path.join(tempfile.mkdtemp(), 'wd')

    def tearDown(self):
        if os.getenv('KEEP_TMP') is None:
            self.tmpfl.close()
            shutil.rmtree(self.tmpd, True)
            shutil.rmtree(os.path.dirname(self.tmpwd), True)
        else:
            print(self.tmpfl.name, self.tmpd, self.tmpwd)

    def _log(self):
        self.tmpfl.flush()
        with open(self.tmpfl.name) as fl:
            return fl.read()

    def test_release(self):
        os.makedirs(os.path.join(self.tmpd, 'cat/name/arch1/1.2.3'))
        plugin = XBuilderSymlinkPlugin(
            dict(release=dict(archive_dir=self.tmpd)), self.tmpfl.write, self.tmpfl, self.tmpfl.name
        )
        plugin.release(dict(success=True, category='cat', pkg_name='name', version='1.2.3', arch='arch1'))
        self.assertTrue(os.path.isdir(os.path.join(self.tmpd, 'cat/name/1.2.3')))
        self.assertTrue(os.path.islink(os.path.join(self.tmpd, 'cat/name/1.2.3/arch1')))
        self.assertEqual(
            os.path.realpath(os.path.join(self.tmpd, 'cat/name/1.2.3/arch1')),
            os.path.realpath(os.path.join(self.tmpd, 'cat/name/arch1/1.2.3'))
        )

    def test_release_dflt_arch(self):
        os.makedirs(os.path.join(self.tmpd, 'cat/name/default/arch1/1.2.3'))
        plugin = XBuilderSymlinkPlugin(
            dict(release=dict(archive_dir=self.tmpd)), self.tmpfl.write, self.tmpfl, self.tmpfl.name
        )
        plugin.release(dict(success=True, category='cat', pkg_name='name', version='1.2.3', arch='default/arch1'))
        self.assertTrue(os.path.isdir(os.path.join(self.tmpd, 'cat/name/1.2.3')))
        self.assertTrue(os.path.islink(os.path.join(self.tmpd, 'cat/name/1.2.3/default/arch1')))
        self.assertEqual(
            os.path.realpath(os.path.join(self.tmpd, 'cat/name/1.2.3/default/arch1')),
            os.path.realpath(os.path.join(self.tmpd, 'cat/name/default/arch1/1.2.3'))
        )

    def test_release_retry(self):
        os.makedirs(os.path.join(self.tmpd, 'cat/name/arch1/1.2.3'))
        os.makedirs(os.path.join(self.tmpd, 'cat/name/1.2.3/arch1'))
        plugin = XBuilderSymlinkPlugin(
            dict(release=dict(archive_dir=self.tmpd)), self.tmpfl.write, self.tmpfl, self.tmpfl.name
        )
        plugin.release(dict(success=True, category='cat', pkg_name='name', version='1.2.3', arch='arch1'))
        self.assertTrue(os.path.isdir(os.path.join(self.tmpd, 'cat/name/1.2.3')))
        self.assertTrue(os.path.islink(os.path.join(self.tmpd, 'cat/name/1.2.3/arch1')))
        self.assertEqual(
            os.path.realpath(os.path.join(self.tmpd, 'cat/name/1.2.3/arch1')),
            os.path.realpath(os.path.join(self.tmpd, 'cat/name/arch1/1.2.3'))
        )

    def test_release_not_arch(self):
        os.makedirs(os.path.join(self.tmpd, 'cat/name/arch2/1.2.3'))
        plugin = XBuilderSymlinkPlugin(
            dict(release=dict(archive_dir=self.tmpd)), self.tmpfl.write, self.tmpfl, self.tmpfl.name
        )
        plugin.release(dict(success=True, category='cat', pkg_name='name', version='1.2.3', arch='arch1'))
        self.assertFalse(os.path.isdir(os.path.join(self.tmpd, 'cat/name/1.2.3')))
        self.assertFalse(os.path.islink(os.path.join(self.tmpd, 'cat/name/1.2.3/arch1')))
