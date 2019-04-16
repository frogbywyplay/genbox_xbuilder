#!/usr/bin/python
#
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
#
#
from __future__ import with_statement

import bz2
import contextlib
from xbuilder.plugin import XBuilderPlugin

class XBuilderLogPlugin(XBuilderPlugin):
    def release(self, build_info):
        self.info('Compressing %s' % self.log_file)

        self.log_fd.flush()
        with open(self.log_file, 'r') as data:
            with contextlib.closing(bz2.BZ2File('%s.bz2' % self.log_file, 'w')) as fobj:
                fobj.write(data.read())


def register(builder):
        builder.add_plugin(XBuilderLogPlugin)

