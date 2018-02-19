#!/usr/bin/python
#
# Copyright (C) 2006-2014 Wyplay, All Rights Reserved.
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

import os
import shutil

from xutils import XUtilsError

from xbuilder.plugin import XBuilderPlugin


class XBuilderUbifsPlugin(XBuilderPlugin):
    def postbuild_success(self, build_info):
        """ Generating ubifs """
        workdir = self.cfg['build']['workdir']

        self.info('Creating UBIfs archive')

        ubifs_file = '%s-%s.img' % (build_info['pkg_name'], build_info['version'])
        self.log_fd.flush()
        ret = self._popen([
            'mkfs.ubifs', '-m', '2048', '-e', '129024', '-c', '2047', '-o',
            os.path.join(workdir, ubifs_file), '-r',
            os.path.join(workdir, 'root/redist')
        ],
                          bufsize=-1).wait()
        if ret != 0:
            raise XUtilsError('Something went wrong while creating the UBIfs archive')

    def release_success(self, build_info):
        """ Releasing ubifs.tgz """

        workdir = self.cfg['build']['workdir']

        ubifs_file = '%s-%s.img' % (build_info['pkg_name'], build_info['version'])

        dest_dir = self._archive_dir(
            build_info['category'], build_info['pkg_name'], build_info['version'], build_info['arch']
        )
        self._makedirs(dest_dir, exist_ok=True)

        self.info('Releasing UBIFs archive')
        self.log_fd.flush()
        try:
            shutil.move(os.path.join(workdir, ubifs_file), os.path.join(dest_dir, ubifs_file))
        except:
            raise XUtilsError('failed to move the ubifs archive')


def register(builder):  # pragma: no cover
    builder.add_plugin(XBuilderUbifsPlugin)
