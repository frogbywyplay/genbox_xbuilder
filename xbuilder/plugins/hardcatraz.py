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
from os.path import exists

from shutil import copy

from xbuilder.plugin import XBuilderPlugin

#XXX WIP, do not use yet
class XBuilderHardcatrazPlugin(XBuilderPlugin):

        def postbuild(self, build_info):
                self.info('Running hardcatraz postbuild script')
                rootdir = self.cfg['build']['workdir'] + '/root'
                redistdir = rootdir + '/redist'
                hardcatraz_file = rootdir + '/etc/portage/hardcatraz-config/hardcatraz.json'
                check_rootfs = '/opt/alcatraz-tools/hardcatraz_check_rootfs.py'

                self.info("config %s"%hardcatraz_file)
                if exists(hardcatraz_file) and exists(check_rootfs):
                        self.info('Running xexec %s'%check_rootfs)
                        self.log_fd.flush()
                        ret = Popen(['xexec', check_rootfs],
                                    bufsize=-1, stdout=self.log_fd, stderr=self.log_fd, shell=False, cwd=None).wait()
                        if ret != 0:
                                raise XUtilsError("failed to run hardcataz postbuild script")

def register(builder):
        builder.add_plugin(XBuilderHardcatrazPlugin)

