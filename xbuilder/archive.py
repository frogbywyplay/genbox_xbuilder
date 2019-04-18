#!/usr/bin/python
#
# Copyright (C) 2006-2019 Wyplay, All Rights Reserved.
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
from os import stat
from os.path import exists, realpath, basename
from functools import partial
import sys

from paramiko import AutoAddPolicy, SFTPClient, SSHClient
from paramiko.config import SSHConfig
from paramiko.ssh_exception import SSHException

from xutils import output, XUtilsError

class Archive(object):
    def __init__(self, server):
        self.server = server
        config = SSHConfig()
        with open('/etc/ssh/ssh_config', 'r') as f:
            config.parse(f)
        if 'user' in config.lookup(server):
            self.user = config.lookup(server)['user']
        else:
            output.error('No config for "Host %s" in /etc/ssh/ssh_config' % server)
            raise XUtilsError('SSH config is incomplete.')

    def upload(self, filenames=list(), destination='/'):
        def progress(filename, transferred, total):
            sys.stdout.write(' * %s transfer in progress: %02d%%.\r' % (filename, transferred * 100 / total))
            sys.stdout.flush()

        ssh = SSHClient()
        try:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            ssh.connect(self.server, username=self.user, allow_agent=True)
        except SSHException, e:
            output.error('SSHException: %s' % str(e))
            raise XUtilsError('Unable to establish a SSH connection to %s' % self.server)

        try:
            sftp = SFTPClient.from_transport(ssh.get_transport())
            sftp.chdir('/')
        except SSHException:
            raise XUtilsError('Unable to negotiate a SFTP session for %s' % self.server)

        # create destination directory if it does not exist
        path = realpath(destination)
        for directory in path.split('/'):
            try:
                sftp.chdir(directory)
            except IOError, e:
                if e.errno == 2:
                    try:
                        sftp.mkdir(directory)
                    except IOError, ex:
                        output.error('Exception: %s' % str(ex))
                        raise XUtilsError('%s is unable to create %s directory on server %s' %
                                          (self.user, directory, self.server))
                    sftp.chdir(directory)
                elif e.errno == 13:
                    raise XUtilsError('%s is unable to enter directory %s on server %s' %
                                      (self.user, directory, self.server))
                else:
                    output.error('Exception: %s' % str(e))
                    raise XUtilsError('Undefined error when entering %s' % directory)

        for f in filenames:
            filepath = realpath(f)
            f = basename(filepath)
            if not exists(filepath):
                output.warn('%s not found => skip it.' % f)
                continue
            my_callback = partial(progress, f)
            remote_attr = sftp.put(filepath, f, callback=my_callback)
            if stat(filepath).st_size == remote_attr.st_size:
                output.info('%s successfully copied on server %s.' % (f, self.server))
            else:
                raise XUtilsError('Copy of %s on server %s is corrupted.' % (f, self.server))

        sftp.close()
        ssh.close()
