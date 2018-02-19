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
import errno
import subprocess

from xutils import XUtilsError

from xbuilder.plugin import XBuilderPlugin


class XBuilderLogPlugin(XBuilderPlugin):
    def release_success(self, build_info):
        def hook(_):
            pass

        return self.release_log(build_info, hook)

    def release_failure(self, build_info):
        def hook(destdir):
            with open(os.path.join(destdir, 'failed'), 'w'):
                pass

        return self.release_log(build_info, hook)

    def release_log(self, build_info, hook):
        dest_dir = self._archive_dir(
            build_info['category'], build_info['pkg_name'], build_info['version'], build_info['arch']
        )
        self._makedirs(dest_dir, exist_ok=True)

        hook(dest_dir)

        if os.path.exists(self.log_file):
            self.info('Releasing log file')
            self.log_fd.flush()
            dest_log = os.path.join(dest_dir, os.path.basename(self.log_file))
            try:
                shutil.copy(self.log_file, dest_log)
            except:
                raise XUtilsError('Failed to release the log file')

            # compress in bzip2
            # 22455: Reusing version number of a failed target is not possible
            dest_log_bz2 = '%s.bz2' % dest_log
            try:
                os.remove(dest_log_bz2)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
            ret = subprocess.Popen(['bzip2', dest_log], bufsize=-1).wait()
            if ret != 0:
                raise XUtilsError('Failed to compress log file')


def register(builder):  # pragma: no cover
    builder.add_plugin(XBuilderLogPlugin)
