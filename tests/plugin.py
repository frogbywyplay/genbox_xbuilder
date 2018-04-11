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

import unittest

from xbuilder.plugin import XBuilderPlugin


class TestXBuilderRootfsPlugin(unittest.TestCase):
    def test_archive(self):
        plugin = XBuilderPlugin(dict(release=dict(archive_dir='/toto')), None, None, None)
        self.assertEqual(plugin._archive_dir('cat', 'pkg', '1.2.3', 'arch'), '/toto/cat/pkg/arch/1.2.3')  # pylint: disable=protected-access
