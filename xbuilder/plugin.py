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
import errno
import os
import subprocess


class XBuilderPlugin(object):
    def __init__(self, cfg, info, log_fd, log_file):
        self.cfg = cfg
        self.info = info
        self.log_fd = log_fd
        self.log_file = log_file

    def prebuild(self, target_ebuild, arch=None):
        pass

    def build(self, target_ebuild, target_builder, arch=None):
        pass

    def postbuild_success(self, build_info):
        pass

    def postbuild_failure(self, build_info):
        pass

    def postbuild(self, build_info):
        if build_info['success']:
            fun = self.postbuild_success
        else:
            fun = self.postbuild_failure
        return fun(build_info)

    def release_success(self, build_info):
        pass

    def release_failure(self, build_info):
        pass

    def release(self, build_info):
        if build_info['success']:
            fun = self.release_success
        else:
            fun = self.release_failure
        return fun(build_info)

    def _popen(self, cmd, **kwargs):
        """ Popen piped to logfile
        """
        return subprocess.Popen(cmd, stdout=self.log_fd, stderr=self.log_fd, **kwargs)

    @staticmethod
    def _makedirs(name, exist_ok=False):
        """ like makedirs from py3
        """
        try:
            os.makedirs(name)
        except OSError as e:
            if not exist_ok or e.errno != errno.EEXIST:
                raise

    def _archive_dir(self, category, pkg_name, version, arch):
        return os.path.join(self.cfg['release']['archive_dir'], category, pkg_name, arch, version)
