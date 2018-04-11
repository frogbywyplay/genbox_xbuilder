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

from xbuilder.plugins.xreport import XBuilderXreportPlugin


class TestXBuilderRootfsPlugin(unittest.TestCase):
    def setUp(self):
        self.tmpfl = tempfile.NamedTemporaryFile(delete=(os.getenv('KEEP_TMP') is None))
        self.tmpd = tempfile.mkdtemp()
        self.tmpwd = os.path.join(tempfile.mkdtemp(), 'wd')
        os.makedirs(self.tmpwd)

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
        plugin = XBuilderXreportPlugin(
            dict(build=dict(workdir=self.tmpwd), release=dict(archive_dir=self.tmpd)), self.tmpfl.write, self.tmpfl,
            self.tmpfl.name
        )
        plugin.report_file = os.path.join(self.tmpwd, 'report_file')
        with open(plugin.report_file, 'w') as fl:
            fl.write('this is report file')
        plugin.report_host_file = os.path.join(self.tmpwd, 'report_host_file')
        with open(plugin.report_host_file, 'w') as fl:
            fl.write('this is host report file')
        plugin.release(dict(success=True, category='cat', pkg_name='pkg', version='1.2.3', arch='arch'))
        archdir = plugin._archive_dir('cat', 'pkg', '1.2.3', 'arch')  # pylint: disable=protected-access
        self.assertTrue(os.path.isdir(archdir))
        with open(os.path.join(archdir, 'report.xml.bz2')) as fl:
            self.assertTrue('is report' in fl.read())
        with open(os.path.join(archdir, 'host-report.xml.bz2')) as fl:
            self.assertTrue('is host report' in fl.read())
