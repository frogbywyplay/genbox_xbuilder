#!/usr/bin/python
#
# Copyright (C) 2006-2020 Wyplay, All Rights Reserved.
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
from __future__ import absolute_import, with_statement

import bz2
import contextlib
import os
import smtplib

from email.mime.text import MIMEText

from xbuilder.archive import Archive
from xbuilder.consts import XBUILDER_REPORT_FILE
from xbuilder.plugin import XBuilderPlugin

from xintegtools.xreport import XReport, XReportXMLOutput


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


def reload_portage_and_gentoolkit():
    import portage
    reload(portage)
    import gentoolkit
    reload(gentoolkit)
    from threading import Lock
    settingslock = Lock()  # pylint: disable=unused-variable
    gentoolkit.settings = portage.config(clone=portage.settings)
    gentoolkit.porttree = portage.db[portage.root]['porttree']
    gentoolkit.vartree = portage.db[portage.root]['vartree']
    gentoolkit.virtuals = portage.db[portage.root]['virtuals']
    import gentoolkit.package
    reload(gentoolkit.package)


def notify_by_mail(cfg, data):
    body  = 'An error occured while submitting XML reports to the bumpmanager service:\n%s\n' % data
    body += 'Do not forget to add the target once the issue is fixed.'
    msg = MIMEText(body)
    msg['From'] = os.getenv('MAIL_FROM', cfg['mail']['from'])
    msg['To'] = 'pmo@wyplay.com'
    msg['Subject'] = 'Issue with %s' % cfg['xreport']['server']

    s = smtplib.SMTP(cfg['mail']['smtp'])
    s.sendmail(msg['From'], msg['To'], msg.as_string())
    s.quit()

class XBuilderXreportPlugin(XBuilderPlugin):
    def postbuild(self, build_info):
        if not build_info['success']:
            return None

        self.info('Generating report with xreport')
        workdir = self.cfg['build']['workdir']
        rootdir = os.path.join(workdir, 'root/')
        xr = XReport(root=rootdir, portage_configroot=rootdir)
        xr.vdb_create()
        self.report_file = os.path.join(workdir, XBUILDER_REPORT_FILE)
        with contextlib.closing(bz2.BZ2File(self.report_file, 'w')) as fd:
            with env_override(ROOT=rootdir, PORTAGE_CONFIGROOT=rootdir):
                reload_portage_and_gentoolkit()
                XReportXMLOutput(errors_only=False).process(xr, fd, True)

        reload_portage_and_gentoolkit()
        self.info('Generating host-report with xreport')
        hostxr = XReport()
        hostxr.vdb_create()
        self.report_host_file = os.path.join(workdir, 'host-' + XBUILDER_REPORT_FILE)
        with contextlib.closing(bz2.BZ2File(self.report_host_file, 'w')) as hostfd:
            XReportXMLOutput(errors_only=False).process(hostxr, hostfd)
        return self.report_file, self.report_host_file

    def release(self, build_info):
        if not build_info['success']:
            return None

        sources = [ '%s/%s' % (self.cfg['build']['workdir'], XBUILDER_REPORT_FILE),
                    '%s/host-%s' % (self.cfg['build']['workdir'], XBUILDER_REPORT_FILE)]
        destination = '/'.join([self.cfg['release']['basedir'], build_info['category'],
                build_info['pkg_name'], build_info['version'], build_info['arch']])

        self.info('Submit XML reports to %s' % self.cfg['xreport']['server'])
        url = '%s/%s/%s/%s/%s/%s' % (self.cfg['xreport']['server'], '/api/prebuilt/', build_info['category'], build_info['pkg_name'], build_info['version'], build_info['arch'])
        r = requests.post(url, files={'target': sources[0], 'host': sources[1]})
        if not r.ok:
            self.error('An unexpected error occured while submitting XML reports: %d' % r.status_code)
            self.error(r.text)
            notify_by_mail(self.cfg, r.text)
        self.info('Uploading XML reports to %s' % self.cfg['release']['server'])
        archive = Archive(self.cfg['release']['server'])
        archive.upload(sources, destination)


def register(builder):
    builder.add_plugin(XBuilderXreportPlugin)
