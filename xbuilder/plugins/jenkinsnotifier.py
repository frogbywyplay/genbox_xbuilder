#!/usr/bin/python
#
# Copyright (C) 2006-2016 Wyplay, All Rights Reserved.
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

from __future__ import absolute_import

import json
import re
from hashlib import sha1

from requests import codes, get, post

from xutils import output, XUtilsError

from xbuilder.plugin import XBuilderPlugin


def create_sha1(pattern):
    hasher = sha1()
    hasher.update(pattern)
    return hasher.hexdigest()


class Jenkins(object):
    def __init__(self, server, credentials=None):
        if not server:
            raise XUtilsError('Empty uri as Jenkins server to notify.')
        self.server = server
        if credentials and not self.is_token(credentials['apitoken']):
            raise XUtilsError('Invalid Jenkins token for user %s.' % credentials['user'])
        self.credentials = (credentials['user'], credentials['apitoken'])
        self.jobs = list()
        self.crumb = self.__crumb()

    def __crumb(self):
        uri = '%s/crumbIssuer/api/json' % self.server
        request = get(uri, auth=self.credentials)
        if request.status_code != codes.ok:
            output.warn('jenkinsnotifier: Unable to get crumb issuer.')
            return dict()
        return {request.json()['crumbRequestField']: request.json()['crumb']}

    @staticmethod
    def is_token(token):
        if len(token) != 32:
            return False
        try:
            int(token, 16)
        except ValueError:
            return False
        return True

    def listjobs(self):
        uri = '%s/api/json' % self.server
        params = {'pretty': 'true'}
        request = get(uri, auth=self.credentials, data=params)
        if request.status_code != codes.ok:
            output.error('jenkinsnotifier: Unable to get uri %s.' % uri)
            output.error('jenkinsnotifier: Error %d: %s.' % (request.status_code, request.reason))
            return self.jobs
        self.jobs = request.json()['jobs']
        return self.jobs

    def getjobinfo(self, job):
        uri = '%s/job/%s/api/json' % (self.server, job)
        request = get(uri, auth=self.credentials)
        if request.status_code != codes.ok:
            output.error('jenkinsnotifier: Unable to get uri %s.' % uri)
            output.error('jenkinsnotifier: Error %d: %s.' % (request.status_code, request.reason))
            return self.jobs
        return request.json()

    def build(self, job, uri=None, jobparams=None):
        if not uri:
            uri = '%s/job/%s/build' % (self.server, job)
        params = self.crumb
        params['delay'] = 60  #set a 60s delay to ensure release phase from build plugin is done
        params['token'] = create_sha1(job)
        params['cause'] = 'xbuilder released a prebuilt.'
        if jobparams:
            params['json'] = json.dumps({
                'parameter': [{
                    'name': 'TARGET_NAME',
                    'value': jobparams['name']
                }, {
                    'name': 'TARGET_ARCH',
                    'value': jobparams['arch']
                }, {
                    'name': 'VERSION',
                    'value': jobparams['version']
                }]
            })
        request = post(uri, auth=self.credentials, data=params)
        if request.status_code != 201:
            output.error('jenkinsnotifier: Unable to build %s with uri %s.' % (job, uri))
            output.error('jenkinsnotifier: Error %d: %s.' % (request.status_code, request.reason))
            return False
        return True


class XBuilderJenkinsNotifierPlugin(XBuilderPlugin):
    def __init__(self, cfg, info, log_fd, log_file):
        super(XBuilderJenkinsNotifierPlugin, self).__init__(cfg, info, log_fd, log_file)
        self.params = self.cfg['jenkinsnotifier'].copy()
        self.jenkins = Jenkins(
            self.params['uri'], {
                'user': self.params['username'],
                'apitoken': self.params['usertoken']
            }
        )

    def release_success(self, build_info):
        if not self.params['jobname']:
            output.warn('jenkinsnotifier: no jobname defined in configuration file.')
            return

        my_match = {
            'category': build_info['category'],
            'package': build_info['pkg_name'],
            'version': build_info['version'],
            'arch': build_info['arch']
        }
        # interpolate ${xxx} in self.params['jobname]
        jobname = ''.join(
            my_match.get(substring, substring) for substring in re.split(r'\${([a-z]+)}', self.params['jobname'])
        )
        try:
            job = next(j for j in self.jenkins.listjobs() if j['name'] == jobname)
        except StopIteration:
            output.warn('jenkinsnotifier: job not found on server %s', self.params['uri'])
            return

        actions = self.jenkins.getjobinfo(job['name'])['actions'][0]
        withparams = 'with' if 'parameterDefinitions' in actions else 'without'
        output.info('jenkinsnotifier: will trigger job %s %s parameters (%s).' % (jobname, withparams, job['url']))
        if 'parameterDefinitions' in actions:
            targetname = build_info['category'] + '/' + build_info['pkg_name']
            self.jenkins.build(
                job['name'], job['url'] + '/build', {
                    'name': targetname,
                    'arch': build_info['arch'],
                    'version': build_info['version']
                }
            )
        else:
            self.jenkins.build(job['name'], job['url'] + '/build')


def register(builder):  # pragma: no cover
    builder.add_plugin(XBuilderJenkinsNotifierPlugin)
