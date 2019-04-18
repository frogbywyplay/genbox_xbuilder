#!/usr/bin/python
#
# Copyright (C) 2006-2019 Wyplay, All Rights Reserved.
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

from bz2 import BZ2File
from contextlib import closing
from os import remove

from xbuilder.archive import Archive
from xbuilder.plugin import XBuilderPlugin


class XBuilderLogPlugin(XBuilderPlugin):
    def release(self, build_info):
        bz2file = '%s.bz2' % self.log_file
        destination = '/'.join([self.cfg['release']['basedir'], build_info['category'],
                                build_info['pkg_name'], build_info['version'], build_info['arch']])

        self.info('Compressing %s' % self.log_file)
        self.log_fd.flush()
        with open(self.log_file, 'r') as data:
            with closing(BZ2File('%s.bz2' % self.log_file, 'w')) as fobj:
                fobj.write(data.read())

        self.info('Uploading %s to %s' % (bz2file, self.cfg['release']['server']))
        archive = Archive(self.cfg['release']['server'])
        archive.upload([bz2file], destination)
        remove(bz2file)


def register(builder):  # pragma: no cover
    builder.add_plugin(XBuilderLogPlugin)
