# Copyright (C) 2018 Wyplay, All Rights Reserved.
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

import errno
import os
import shutil
import time

from xutils import warn

from xbuilder.plugin import XBuilderPlugin


class XBuilderSymlinkPlugin(XBuilderPlugin):
    """ target are puts in arch_dir/category/name/arch/version with ACL set at 'arch' level
        legacy path were arch_dir/category/name/versin/arch with ACL set at 'name' level

        here we create compatibility symlinks in the legacy folders (to avoid breaking all tools)
    """

    def release(self, build_info):
        archive = self._archive_dir(
            build_info['category'], build_info['pkg_name'], build_info['version'], build_info['arch']
        )
        if not os.path.exists(archive):
            return
        legacy = os.path.join(
            self.cfg['release']['archive_dir'], build_info['category'], build_info['pkg_name'], build_info['version'],
            build_info['arch']
        )
        compat = os.path.dirname(legacy)
        self._makedirs(compat, exist_ok=True)
        retry = True
        while True:
            try:
                os.symlink(os.path.relpath(archive, compat), legacy)
                break
            except OSError as e:
                if retry and e.errno == errno.EEXIST:
                    if os.path.islink(legacy) and os.path.realpath(legacy) == os.path.realpath(archive):
                        break
                    bak = '%s.bak%s' % (legacy, int(time.time()))
                    warn('Unexpected folder found at %s: it will be renamed %s' % (legacy, bak), output=self.log_fd)
                    shutil.move(legacy, bak)
                    retry = False
                else:
                    raise


def register(builder):  # pragma: no cover
    builder.add_plugin(XBuilderSymlinkPlugin)
