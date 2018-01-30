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

from subprocess import Popen

from xbuilder.plugin import XBuilderPlugin
from xbuilder.consts import XBUILDER_REPORT_FILE

from xintegtools.xreport import XReport, XReportXMLOutput

from xutils import XUtilsError

import bz2


class XBuilderXreportPlugin(XBuilderPlugin):
    def postbuild(self, build_info):
        self.info('Generating report with xreport')
        workdir = self.cfg['build']['workdir']
        xr = XReport(root=workdir + '/root', portage_configroot=workdir + '/root')
        xr.vdb_create()
        self.report_file = '/'.join([workdir, XBUILDER_REPORT_FILE])
        fd = bz2.BZ2File(self.report_file, 'w')
        XReportXMLOutput(errors_only=False).process(xr, fd)
        fd.close()

        hostxr = XReport()
        hostxr.vdb_create()
        self.report_host_file = '/'.join([workdir, 'host-' + XBUILDER_REPORT_FILE])
        hostfd = bz2.BZ2File(self.report_host_file, 'w')
        XReportXMLOutput(errors_only=False).process(hostxr, hostfd)
        hostfd.close()
        return self.report_file, self.report_host_file

    def release(self, build_info):
        archive = self.cfg['release']['archive_dir']

        dest_dir = '/'.join([
            archive, build_info['category'], build_info['pkg_name'], build_info['version'], build_info['arch']
        ])

        if not exists(dest_dir):
            os.makedirs(dest_dir)

        self.info('Releasing report file')
        self.log_fd.flush()
        ret = Popen(['cp', self.report_file, '/'.join([dest_dir, XBUILDER_REPORT_FILE])],
                    bufsize=-1,
                    stdout=self.log_fd,
                    stderr=self.log_fd,
                    shell=False,
                    cwd=None).wait()
        Popen(['cp', self.report_host_file, '/'.join([dest_dir, 'host-' + XBUILDER_REPORT_FILE])],
              bufsize=-1,
              stdout=self.log_fd,
              stderr=self.log_fd,
              shell=False,
              cwd=None).wait()
        if ret != 0:
            raise XUtilsError('Failed to release the report file')


def register(builder):
    builder.add_plugin(XBuilderXreportPlugin)
