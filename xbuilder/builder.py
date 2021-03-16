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

import os
import sys

from os.path import realpath, dirname, isfile, exists, expanduser
from subprocess import Popen

from portage import config
from portage_const import INCREMENTALS

from xtarget import XTargetBuilder, XTargetError, XTargetReleaseParser

from xutils import XUtilsError, XUtilsConfig, info, vinfo, error
from xutils.ebuild import ebuild_factory

from xintegtools.xbump import Xbump, XbumpWarn, XbumpError
from xintegtools.xbump.consts import XBUMP_DEF_NAMING
from consts import *

class XBuilder(object):
        def __init__(self,
                     config=None,
                     type=XBUILDER_DEFTYPE):
                self.log_fd = None
                self.build_info = {}
                self.plugin_list = []

                if config and not isfile(config):
                        raise XUtilsError("Can't find config file %s" % config)

                self.type = type
                if type not in XBUILDER_TYPES:
                        raise XUtilsError("Unkown build type %s" % type)

                self.config(config)

                workdir = self.cfg['build']['workdir']

                if self.cfg['build']['clean_workdir'] and exists(workdir):
                        info('Cleaning workdir')
                        ret = Popen(["rm", "-rf", workdir], bufsize=-1,
                                    stdout=None, stderr=None, shell=False,
                                    cwd=None).wait()

                if not exists(workdir):
                        os.makedirs(workdir)

                self.log_file = '%s/%s' % (workdir, XBUILDER_LOGFILE)
                self.log_fd = open(self.log_file, 'a')
                self.stderr = sys.stderr
                sys.stderr = self.log_fd

                self.target_builder = XTargetBuilder(arch=r'*', stdout=self.log_fd, stderr=self.log_fd)

                self.info('Loading plugins:', eol=False)
                for plugin in self.cfg['build']['plugins']:
                        self.out('%s' % plugin, eol=False)
                        p = __import__('xbuilder.plugins.%s' % plugin, fromlist=['register'])
                        p.register(self)
                self.out('')

        def add_plugin(self, plugin):
                self.plugin_list.append(plugin(self.cfg, self.info, self.log_fd, self.log_file))

        def __del__(self):
                if (self.log_fd):
                        sys.stderr = self.stderr
                        self.log_fd.close()

        def config(self, config_files):
                if config_files is None:
                        config_files = [
                                        XBUILDER_SYS_CFG,
                                        expanduser('~') + '/' + XBUILDER_USER_CFG
                                       ]

                cfg = XUtilsConfig(config_files)
                self.cfg = {
                            'target' : {},
                            'build' : {},
                            'jenkinsnotifier': {},
                            'mail' : {},
                            'notifier': {},
                            'release' : {},
                            'gpg' : {},
                            'xreport' : {}
                           }
                self.cfg['target']['max_beta'] = int(cfg.get('target', 'max_beta', XBUILDER_MAX_BETA_TARGETS))
                self.cfg['target']['commit'] = cfg.get('target', 'commit', XBUILDER_TARGET_COMMIT)

                self.cfg['build']['clean_workdir'] = cfg.get('build', 'clean_workdir', XBUILDER_CLEAN_WORKDIR) == 'True'
                self.cfg['build']['workdir'] = cfg.get('build', 'workdir', XBUILDER_WORKDIR)
                self.cfg['build']['plugins'] = cfg.get('build', 'plugins', '').split()
                self.cfg['build']['features'] = cfg.get('build', 'features', XBUILDER_FEATURES)
                self.cfg['build']['binpkgs'] = cfg.get('build', 'binpkgs', str()).split()

                self.cfg['release']['server'] = cfg.get('release', 'server', XBUILDER_ARTIFACT_SERVER)
                self.cfg['release']['basedir'] = cfg.get('release', 'basedir', XBUILDER_PREBUILT_BASEDIR)
                self.cfg['release']['compression'] = cfg.get('release', 'compression', XBUILDER_COMPRESSION)
                self.cfg['release']['tar_extra_opts'] = cfg.get('release', 'tar_extra_opts', str())
                self.cfg['release']['flat_profile'] = cfg.get('release', 'flat_profile', False)
                self.cfg['release']['tag_overlays'] = cfg.get('release', 'tag_overlays', False)
                self.cfg['release']['tag_ebuilds'] = cfg.get('release', 'tag_ebuilds', False)

                self.cfg['jenkinsnotifier']['uri'] = cfg.get('jenkinsnotifier', 'uri', str())
                self.cfg['jenkinsnotifier']['username'] = cfg.get('jenkinsnotifier', 'username', str())
                self.cfg['jenkinsnotifier']['usertoken'] = cfg.get('jenkinsnotifier', 'usertoken', str())
                self.cfg['jenkinsnotifier']['jobname'] = cfg.get('jenkinsnotifier', 'jobname', str())
                self.cfg['mail']['smtp'] = cfg.get('mail', 'smtp', XBUILDER_MAIL_SMTP)
                self.cfg['mail']['from'] = cfg.get('mail', 'from', XBUILDER_MAIL_FROM)
                self.cfg['mail']['to'] = cfg.get('mail', 'to', XBUILDER_MAIL_TO)
                self.cfg['mail']['log_size'] = int(cfg.get('mail', 'log_size', XBUILDER_MAIL_LOG_SIZE))
                self.cfg['mail']['uri'] = cfg.get('mail', 'uri', XBUILDER_MAIL_URI)

                self.cfg['notifier']['uri'] = cfg.get('notifier', 'uri', XBUILDER_NOTIFIER_URI)
                self.cfg['gpg']['logfile'] = cfg.get('gpg', 'logfile', os.path.join(self.cfg['build']['workdir'], XBUILDER_GPG_LOGFILE))
                self.cfg['gpg']['loglevel'] = int(cfg.get('gpg', 'loglevel', XBUILDER_GPG_LOGLEVEL))
                self.cfg['xreport']['server'] = cfg.get('xreport', 'server', XBUILDER_XREPORT_SERVER)
                del cfg

        def info(self, msg, eol=True):
                info(msg, eol)
                if eol:
                        print >>self.log_fd, msg
                else:
                        print >>self.log_fd, msg,

        def out(self, msg, eol=True):
                if eol:
                        print msg
                        print >>self.log_fd, msg
                else:
                        print msg,
                        print >>self.log_fd, msg,

        def vinfo(self, msg, eol=True):
                vinfo(msg, eol)
                if eol:
                        print >>self.log_fd, msg
                else:
                        print >>self.log_fd, msg,

        def __load_target_db(self, force=False):
                if not self.target_builder.xportage.portdb or force:
                        self.target_builder.xportage.create_trees()

        def __find_templates(self, pkg_atom):
                self.__load_target_db()
                template = None
                for tgt, visible in self.target_builder.list_profiles_ng(pkg_atom, version=True, multi=False):
                        if not visible:
                                continue
                        eb_file = self.target_builder.xportage.portdb.findname(tgt)
                        if eb_file is None:
                                raise XUtilsError('Error in xportage.portdb.findname')
                        ebuild = ebuild_factory(eb_file)
                        if ebuild is None:
                                continue
                        if ebuild.get_type() == 'target' and ebuild.is_template():
                                if not template:
                                        template = [ eb_file ]
                                else:
                                        template.append(eb_file)

                return template

        def run(self, pkg_atom, version=None, arch=None, name=None):
                if not name:
                        name = XBUMP_DEF_NAMING
                ebuild = self.create_desc(pkg_atom, version, name)
                if not ebuild:
                        ebuild = pkg_atom
                self.prebuild(ebuild, arch)
                self.build(ebuild, arch)
                self.postbuild()
                self.release()
                return self.build_info['success']

        def create_desc(self, template, version=None, name=XBUMP_DEF_NAMING):
                """Create a new target description with xbump
                """
                if template.endswith('.ebuild'):
                        if not isfile(template):
                                raise XUtilsError('Can\'t find ebuild file %s' % template)
                        ebuild = ebuild_factory(template)
                        if not ebuild:
                                raise XUtilsError('Unkown ebuild type')
                        elif not ebuild.is_template():
                                # Don't create any desc, the ebuild doesn't seem to be a template
                                return None
                else:
                        tpls = self.__find_templates(template)
                        if not tpls:
                                # Don't create any desc, let's try to build the best_match
                                return None
                        if len(tpls) > 1:
                                raise XUtilsError('Too many templates found for %s: %s' % (template, ' '.join(tpls)))
                        template = tpls[0]
                # FIXME: need to define which variables from portage environment we want to provide to xbump
                if self.target_builder.xportage.config.has_key('EHG_BASE_URI'):
                        os.environ['EHG_BASE_URI'] = self.target_builder.xportage.config.get('EHG_BASE_URI')

                eb_dir = dirname(realpath(template))
                xb = Xbump()
                try:
                        eb_name = xb.update(template, version, force=True, name=name)
                except XbumpWarn, e:
                        raise XUtilsError(error=str(e), error_log=e.get_log())
                except XbumpError, e:
                        raise XUtilsError(error=str(e), error_log=e.get_log())


                self.info('Target description created: %s' % eb_name)
                if self.type == 'beta' and self.cfg['target']['max_beta'] > 0:
                        self.info('Cleaning old targets')
                        # TODO delete old targets from repo

                # Rebuild the target db (new ebuilds and some might have been deleted)
                self.__load_target_db(force=True)
                return eb_dir + '/' + eb_name + '.ebuild'

        def prebuild(self, target_ebuild, arch=None):
                self.info('Running prebuild step')
                for p in self.plugin_list:
                        p.prebuild(target_ebuild, arch)

        def build(self, target_ebuild, arch=None):
                self.info('Running build step')
                self.__load_target_db()

                self.build_info['success'] = True

                for p in self.plugin_list:
                        try:
                                p.build(target_ebuild, self.target_builder, arch)
                        except XUtilsError, e:
                                error(str(e))
                                self.build_info['success'] = False
                                return

        def __extract_info(self):
                workdir = self.cfg['build']['workdir']

                release = XTargetReleaseParser().get(workdir, self.target_builder.cfg['release_file'])

                if not release:
                        raise XUtilsError('Can\'t find release file')

                for k in [ 'name', 'version', 'arch' ]:
                        if not release.has_key(k):
                                raise XUtilsError('Missing key in release file (%s)' % k)

                cat, pn = release['name'].split('/')
                self.build_info['pkg_name'] = pn
                self.build_info['category'] = cat
		if not self.build_info.has_key('version'):
                	self.build_info['version'] = release['version']
                self.build_info['arch'] = release['arch']
                if self.cfg['release']['flat_profile']:
                    self.build_info['profile'] = self.build_info['arch']
                else:
                    # profile_directory is: myroot + /etc/portage + pkg_name + profile
                    # we just want to keep profile part.
                    myroot = '%s/%s' % (workdir, 'root')
                    profile_directory = config(config_root=myroot, target_root=myroot, config_incrementals=INCREMENTALS).profiles[-1]
                    base = realpath('%s/%s/%s' % (myroot, '/etc/portage', pn))
                    if not os.path.isdir(base):
			base = realpath('%s/%s' % (myroot, 'etc/portage/profiles'))
                    self.build_info['profile'] = profile_directory[len(base) + 1:]

        def postbuild(self):
                self.info('Running postbuild step')
                if not 'pkg_name' in self.build_info:
                        self.__extract_info()

                for p in self.plugin_list:
                        p.postbuild(self.build_info)

        def release(self):
                self.info('Running release step')
                if not 'pkg_name' in self.build_info:
                        self.__extract_info()

                for p in self.plugin_list:
                        p.release(self.build_info)

        def cleanup(self):
                pass
