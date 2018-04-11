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

import contextlib
import errno
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import time

from xbuilder.plugin import XBuilderPlugin

MAIL_BODY = 'This message was sent automatically by a builder, please do not reply.'
MAIL_BODY_FAILED = """See log file at %(uri)s/%(category)s/%(pkg_name)s/%(version)s/%(arch)s/build.log.bz2
This message was sent automatically by a builder, please do not reply."""

MAIL_MSG_OK = '[Build] OK on %s for %s at %s'
MAIL_MSG_NOK = '[Build] FAILED on %s for %s at %s'


class XBuilderMailPlugin(XBuilderPlugin):
    @staticmethod
    def __attach_text(fd, msg):
        pj = MIMEText(fd.read())
        pj.add_header('Content-Disposition', 'attachment', filename=os.path.basename(fd.name))
        msg.attach(pj)

    def release_success(self, build_info):
        subject = MAIL_MSG_OK
        if 'analyzer' in build_info:
            body = MIMEText(MAIL_BODY + '\n\n' + build_info['analyzer'] + '\n\n' + os.getenv('MAIL_BODY', ''))
        else:
            body = MIMEText(MAIL_BODY + '\n\n' + os.getenv('MAIL_BODY', ''))
        with self.release_mail(build_info, subject, body):
            pass

    def release_failure(self, build_info):
        subject = MAIL_MSG_NOK
        body = MIMEText(
            MAIL_BODY_FAILED % {
                'uri': self.cfg['mail']['uri'],
                'category': build_info['category'],
                'pkg_name': build_info['pkg_name'],
                'version': build_info['version'],
                'arch': build_info['arch']
            }
        )
        with self.release_mail(build_info, subject, body) as msg:
            try:
                with open(self.log_file, 'r') as fd:
                    self.log_fd.flush()
                    try:
                        fd.seek(-self.cfg['mail']['log_size'], os.SEEK_END)
                        fd.readline()
                    except IOError:
                        # The file might be less than MAIL_LOG_SIZE
                        fd.seek(0, os.SEEK_SET)
                    self.__attach_text(fd, msg)
            except IOError as e:  # no logfile
                if e.errno != errno.ENOENT:
                    raise

    @contextlib.contextmanager
    def release_mail(self, build_info, subject, body):
        self.info('Sending mails')
        build_time = time.strftime('%Y-%m-%d %H:%M:%S')
        build_name = '%s/%s-%s' % (build_info['category'], build_info['pkg_name'], build_info['version'])

        msg = MIMEMultipart()

        msg['From'] = os.getenv('MAIL_FROM', self.cfg['mail']['from'])
        msg['To'] = os.getenv('MAIL_TO', self.cfg['mail']['to'])

        yield msg
        body.add_header('Content-Disposition', 'inline')
        msg.attach(body)
        msg['Subject'] = subject % (build_name, build_info['arch'], build_time)

        s = smtplib.SMTP(self.cfg['mail']['smtp'])
        s.sendmail(msg['From'], msg['To'], msg.as_string())
        s.quit()


def register(builder):  # pragma: no cover
    builder.add_plugin(XBuilderMailPlugin)
