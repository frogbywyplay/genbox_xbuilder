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

import os
import logging

import gnupg

from portage import config  # pylint: disable=no-name-in-module

from xutils import XUtilsError

from xbuilder.plugin import XBuilderPlugin


class XBuilderGnuPGPlugin(XBuilderPlugin):
    def __init__(self, *args, **kwargs):
        super(XBuilderGnuPGPlugin, self).__init__(*args, **kwargs)
        self.gpg_allkeyids = None
        self.log_handler = None
        self.gpg = None

    def postbuild_success(self, build_info):
        """ Encryption of rootfs.tgz """
        workdir = self.cfg['build']['workdir']
        paths = [os.path.join(workdir, 'root/etc/portage/gpg')]
        target_root = os.path.join(workdir, 'root')
        profile_paths = config(config_root=target_root, target_root=target_root).profiles
        paths.extend(profile_paths)

        def find_pubring():
            for path in reversed(paths):
                path = os.path.join(path, 'pubring.gpg')
                if os.path.isfile(path):
                    yield path

        try:
            keysfile = next(find_pubring())
        except StopIteration:
            self.info('No encryption on this target')
            return
        self.redirect_logging()
        self.gpg = gnupg.GPG(keyring=keysfile)
        self.gpg_allkeyids = [i['keyid'] for i in self.gpg.list_keys()]
        if not self.gpg_allkeyids:
            self.clean_up()
            raise XUtilsError(
                'No gpg keys, externalkeyring=%r, see GnuPG log %r.' % (keysfile, self.cfg['gpg']['logfile'])
            )
        self.process_file('debuginfo', build_info)
        self.process_file('root', build_info)
        self.clean_up()

    def redirect_logging(self):
        logfile = self.cfg['gpg']['logfile']
        self.info('Redirecting GnuPG log to %r.' % logfile)
        logger = logging.getLogger('gnupg')
        logger.setLevel(self.cfg['gpg']['loglevel'])
        self.log_handler = logging.FileHandler(logfile)
        self.log_handler.setFormatter(logging.Formatter('%(levelname)s - %(name)s - %(message)s'))
        logger.addHandler(self.log_handler)

    def clean_up(self):
        del self.gpg_allkeyids
        del self.gpg
        logging.getLogger('gnupg').removeHandler(self.log_handler)
        self.log_handler.close()

    def process_file(self, type_, build_info):
        fn = os.path.join(
            self.cfg['build']['workdir'], '%s-%s_%s.tar.%s' %
            (build_info['pkg_name'], build_info['version'], type_, self.cfg['release']['compression'])
        )
        if type_ == 'debuginfo' and not os.path.isfile(fn):
            return
        if not os.path.isfile(fn):
            self.clean_up()
            raise XUtilsError('File %r not found for encrypt.' % fn)
        with open(fn, 'rb') as tarball:
            self.info('Encrypting %s archive' % type_)
            encrypted = self.gpg.encrypt_file(
                tarball, self.gpg_allkeyids, always_trust=True, output=fn + '.gpg', armor=False
            )
            if not encrypted:
                self.clean_up()
                raise XUtilsError(
                    'encrypt_file() for %s failed, file name is %r, see GnuPG log %r.' %
                    (type_, fn, self.cfg['gpg']['logfile'])
                )
        os.remove(fn)


def register(builder):  # pragma: no cover
    builder.add_plugin(XBuilderGnuPGPlugin)
