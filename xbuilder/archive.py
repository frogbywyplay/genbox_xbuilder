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
from __future__ import with_statement

from os import stat
from os.path import exists, realpath, basename
from functools import partial
import sys

try:
    # filter warning from pycrypto (imported by paramiko)
    # "PowmInsecureWarning: Not using mpz_powm_sec."
    import warnings as _warnings
    from Crypto.pct_warnings import PowmInsecureWarning
    _warnings.simplefilter('ignore', category=PowmInsecureWarning, append=1)
except ImportError:
    pass

from paramiko import AutoAddPolicy, SFTPClient, SSHClient
from paramiko.config import SSHConfig
from paramiko.ssh_exception import AuthenticationException, BadHostKeyException, SSHException

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

    def check_connection(self, basedir):
        # Test SSH connection
        ssh = SSHClient()
        try:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            ssh.connect(self.server, username = self.user, allow_agent = True)
        except BadHostKeyException, e:
            output.error('BadHostKeyException: %s' % str(e))
            raise XUtilsError('Server host key verification failed.')
        except AuthenticationException, e:
            output.error('AuthenticationException: %s' % str(e))
            raise XUtilsError('Authentication to %s failed.' % self.server)
        except SSHException, e:
            output.error('SSHException: %s' % str(e))
            raise XUtilsError('Unable to establish a SSH connection to %s' % self.server)
        finally:
            stdin, stdout, stderr = ssh.exec_command(  # pylint: disable=unused-variable
                'touch %(base)s/foo && rm %(base)s/foo' % {'base': basedir}
            )
            if stderr.read():
                raise XUtilsError(
                    'User does not have sufficient permission on server %s to create/delete files.' %
                     self.server
                )
            ssh.close()

    def upload(self, filenames = [], destination = '/'):
        def progress(filename, transferred, total):
            sys.stdout.write(' * %s transfer in progress: %02d%%.\r' % (filename, transferred * 100 / total))
            sys.stdout.flush()

        ssh = SSHClient()
        try:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            ssh.connect(self.server, username = self.user, allow_agent = True)
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
        for dir in path.split('/'):
            try:
                sftp.chdir(dir)
            except IOError, e:
                if e.errno == 2:
                    try:
                        sftp.mkdir(dir)
                    except IOError, ex:
                        output.error('Exception: %s' % str(ex))
                        raise XUtilsError('%s is unable to create %s directory on server %s' % (self.user, dir, self.server))
                    sftp.chdir(dir)
                elif e.errno == 13:
                    raise XUtilsError('%s is unable to enter directory %s on server %s' % (self.user, dir, self.server))
                else:
                    output.error('Exception: %s' % str(e))
                    raise XUtilsError('Undefined error when entering %s' % dir)

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
