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

from xbuilder.plugins.version import XBuilderXversionPlugin


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

    def test_postbuild_success_no_file(self):
        make_profile_lnk = os.path.join(self.tmpwd, 'root/etc/portage/frog-dev/default/bcm973625sff2l')
        os.makedirs(make_profile_lnk)
        make_profile = os.path.join(self.tmpwd, 'root/etc/make.profile')
        os.symlink('portage/frog-dev/default/bcm973625sff2l', make_profile)
        os.symlink('frog-dev/default/bcm973625sff2l', os.path.join(self.tmpwd, 'root/etc/portage/make.profile'))
        redist = os.path.join(self.tmpwd, 'root/redist/etc')
        os.makedirs(redist)

        plugin = XBuilderXversionPlugin(
            dict(build=dict(workdir=self.tmpwd)), self.tmpfl.write, self.tmpfl, self.tmpfl.name
        )
        plugin.postbuild(dict(success=True, version='1.2.3'))
        with open(os.path.join(self.tmpwd, 'root/etc/version')) as fl:
            self.assertIn('1.2.3', fl.read())
        with open(os.path.join(self.tmpwd, 'root/redist/etc/version')) as fl:
            self.assertIn('1.2.3', fl.read())
