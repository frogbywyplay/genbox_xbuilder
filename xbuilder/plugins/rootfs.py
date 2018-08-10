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

import os
import shutil

from xutils import XUtilsError

from xbuilder.plugin import XBuilderPlugin

BUILD_LOG_BUFSIZE = 1024 * 1024 * 2  # 2Mo should be enough


class XBuilderRootfsPlugin(XBuilderPlugin):
    def tar_cf(self, kind, build_info, workdir, path, compression, tar_extra_opts):  # pylint: disable=too-many-arguments
        self.info('Creating %s archive' % (kind, ))
        akind = 'root' if kind == 'rootfs' else kind
        out_file = os.path.join(
            workdir, '%s-%s_%s.tar.%s' % (build_info['pkg_name'], build_info['version'], akind, compression)
        )
        # Special case: for xz we want to use parallel compression with pixz
        tar_comp_opts = '-Ipixz' if compression == "xz" else '-a'
        if '--xattrs' in tar_extra_opts:
            tar_extra_opts = tar_extra_opts.replace('--xattrs', '')
        cmd = ['tar', 'cfp', out_file, '-C', workdir, path, tar_comp_opts] + tar_extra_opts.split()
        self.log_fd.flush()
        if self._popen(cmd, bufsize=-1).wait() != 0:
            raise XUtilsError('Something went wrong while creating the %s archive' % (kind, ))

    def postbuild_failure(self, build_info):
        workdir = os.path.realpath(self.cfg['build']['workdir'])
        # TODO ???
        # TODO use libmount
        with open('/proc/mounts', 'r') as mounts:
            for line in mounts:
                if workdir not in line:
                    continue
                for word in line.split():
                    if not word.startswith(workdir):
                        continue
                    self.info('Cleaning builddir (%s)' % word)
                    if self._popen(['umount', word], bufsize=-1).wait() != 0:
                        raise XUtilsError('Something went wrong while trying to clean the builddir')

    def postbuild_success(self, build_info):
        """ Generating rootfs """
        workdir = self.cfg['build']['workdir']

        compression = self.cfg['release']['compression']
        tar_extra_opts = self.cfg['release']['tar_extra_opts']

        debugdir = os.path.join(workdir, 'root/usr/lib/debug')
        if os.path.isdir(debugdir):
            try:
                self.tar_cf('debuginfo', build_info, workdir, 'root/usr/lib/debug', compression, tar_extra_opts)
            finally:
                shutil.rmtree(debugdir)

        self.tar_cf('rootfs', build_info, workdir, 'root', compression, tar_extra_opts)


def register(builder):  # pragma: no cover
    builder.add_plugin(XBuilderRootfsPlugin)
