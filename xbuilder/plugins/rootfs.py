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

from os.path import exists, realpath

from subprocess import Popen

from xutils import XUtilsError
from xutils.ebuild import ebuild_factory

from xtarget import XTargetError

from xbuilder.plugin import XBuilderPlugin

BUILD_LOG_BUFSIZE = 1024 * 1024 * 2 # 2Mo should be enough

class XBuilderRootfsPlugin(XBuilderPlugin):

    def postbuild(self, build_info):
        """ Generating rootfs """
        workdir = self.cfg['build']['workdir']
        compression = self.cfg['release']['compression']

        if build_info['success'] != True:
            workdir = realpath(workdir)
            mounts = open('/proc/mounts', 'r')
            for line in mounts.readlines():
                if not workdir in line:
                    continue
                for word in line.split():
                    if not word.startswith(workdir):
                        continue
                    self.info('Cleaning builddir (%s)' % word)
                    ret = Popen(['umount', word], bufsize=-1,
                                    stdout=self.log_fd, stderr=self.log_fd,
                                    shell=False, cwd=None).wait()
                    if ret != 0:
                        raise XUtilsError("Something went wrong while trying to clean the builddir")
            mounts.close()
        else:
            """ Special case: for xz we want to use parallel compression with pixz """
            tar_comp_opts = '-Ipixz' if compression == "xz" else '-a'
            tar_extra_opts = self.cfg['release']['tar_extra_opts']
            if '--xattrs' in tar_extra_opts: tar_extra_opts = tar_extra_opts.replace('--xattrs', '')

            if os.path.isdir ( workdir + '/root/usr/lib/debug' ):
                self.info('Creating debuginfo archive')
                debugfs_file = '%s-%s_debuginfo.tar.%s' % (build_info['pkg_name'], build_info['version'], compression)
                self.log_fd.flush()
                tar_cmd = ['tar', 'cfp', workdir + '/' + debugfs_file, '--xattrs', tar_comp_opts, '-C', workdir, 'root/usr/lib/debug'] + tar_extra_opts.split()
                ret = Popen(tar_cmd, bufsize=-1,
                            stdout=self.log_fd,
                            stderr=self.log_fd,
                            shell=False, cwd=None).wait()
                shutil.rmtree(workdir + '/root/usr/lib/debug')
                if ret != 0:
                    raise XUtilsError("Something went wrong while creating the debuginfo archive")

            self.info('Creating rootfs archive')
            rootfs_file = '%s-%s_root.tar.%s' % (build_info['pkg_name'], build_info['version'], compression)
            self.log_fd.flush()
            tar_cmd = ['tar', 'cfp', workdir + '/' + rootfs_file, '--xattrs', tar_comp_opts, '-C', workdir, 'root'] + tar_extra_opts.split()
            ret = Popen(tar_cmd, bufsize=-1,
                        stdout=self.log_fd,
                        stderr=self.log_fd,
                        shell=False, cwd=None).wait()
            if ret != 0:
                raise XUtilsError("Something went wrong while creating the rootfs archive")

def register(builder):
    builder.add_plugin(XBuilderRootfsPlugin)

