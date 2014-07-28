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
from os.path import exists, basename
from subprocess import Popen

from xutils import XUtilsError

from xbuilder.plugin import XBuilderPlugin

class XBuilderLogPlugin(XBuilderPlugin):
        def release(self, build_info):
                archive = self.cfg['release']['archive_dir']

                dest_dir = "/".join([archive, build_info['category'],
                        build_info['pkg_name'], build_info['version'],
                        build_info['arch']])

                if not exists(dest_dir):
                        os.makedirs(dest_dir)

                if build_info['success'] != True:
                        failed = open(dest_dir + '/failed', 'w')
                        failed.close()

                if exists(self.log_file):
                        self.info('Releasing log file')
                        self.log_fd.flush()
                        dest_log = '/'.join([dest_dir, basename(self.log_file)])
                        dest_log_bz2 = '%s.bz2' % dest_log
                        ret = Popen(['cp', self.log_file, dest_log],
                                    bufsize=-1, stdout=None, stderr=None, shell=False, cwd=None).wait()
                        if ret != 0:
                                raise XUtilsError("Failed to release the log file")
			# compress in bzip2
                        # 22455: Reusing version number of a failed target is not possible
                        if exists(dest_log_bz2):
                                os.remove(dest_log_bz2)
			ret = Popen(['bzip2', dest_log],
				bufsize=-1, stdout=None, stderr=None, shell=False, cwd=None).wait()
			if ret != 0:
				raise XUtilsError("Failed to compress log file")

def register(builder):
        builder.add_plugin(XBuilderLogPlugin)

