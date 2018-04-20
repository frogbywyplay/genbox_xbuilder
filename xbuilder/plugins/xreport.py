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


import bz2
import contextlib
import os
import shutil

import portage

from xintegtools.xreport import XReport, XReportXMLOutput

from xutils import XUtilsError

from xbuilder.plugin import XBuilderPlugin
from xbuilder.consts import XBUILDER_REPORT_FILE


@contextlib.contextmanager
def env_override(**kwargs):
    def saveenv():
        for k in kwargs:
            try:
                yield k, os.environ[k]
            except KeyError:
                pass

    savedenv = dict(saveenv())
    os.environ.update(kwargs)
    yield
    os.environ.update(savedenv)


class XBuilderXreportPlugin(XBuilderPlugin):
    def __init__(self, *args, **kwargs):
        super(XBuilderXreportPlugin, self).__init__(*args, **kwargs)
        self.report_file = None
        self.report_host_file = None

    def postbuild(self, build_info):
        self.info('Generating report with xreport')

        workdir = self.cfg['build']['workdir']
        wroot = os.path.join(workdir, 'root/')
        xr = XReport(root=wroot, portage_configroot=wroot)
        xr.vdb_create()

        self.report_file = os.path.join(workdir, XBUILDER_REPORT_FILE)
        with bz2.BZ2File(self.report_file, 'w') as fd:
            with env_override(ROOT=wroot, PORTAGE_CONFIGROOT=wroot):
                reload(portage)
                XReportXMLOutput(errors_only=False).process(xr, fd, with_deps=True)

        reload(portage)
        hostxr = XReport()
        hostxr.vdb_create()

        self.report_host_file = os.path.join(workdir, 'host-' + XBUILDER_REPORT_FILE)
        with bz2.BZ2File(self.report_host_file, 'w') as hostfd:
            XReportXMLOutput(errors_only=False).process(hostxr, hostfd)

        return self.report_file, self.report_host_file

    def release(self, build_info):
        dest_dir = self._archive_dir(
            build_info['category'], build_info['pkg_name'], build_info['version'], build_info['arch']
        )
        self._makedirs(dest_dir, exist_ok=True)

        self.info('Releasing report file')
        self.log_fd.flush()
        try:
            shutil.copy(self.report_file, os.path.join(dest_dir, XBUILDER_REPORT_FILE))
            failed = False
        except (IOError, OSError):
            failed = True
        try:
            shutil.copy(self.report_host_file, os.path.join(dest_dir, 'host-' + XBUILDER_REPORT_FILE))
        except (IOError, OSError):
            pass
        if failed:
            raise XUtilsError('Failed to release the report file')


def register(builder):  # pragma: no cover
    builder.add_plugin(XBuilderXreportPlugin)
