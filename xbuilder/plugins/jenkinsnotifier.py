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
from __future__ import absolute_import

import re
import hashlib

import requests

from simplejson import loads, dumps

from xutils import output, XUtilsError

from xbuilder.plugin import XBuilderPlugin


def create_sha1(pattern):
    hasher = hashlib.sha1()
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
        self.crumb = self.__crumb()

    def __crumb(self):
        uri = '%s/crumbIssuer/api/json' % self.server
        try:
            response = requests.get(uri, auth=self.credentials)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            output.warn('jenkinsnotifier: Unable to get crumb issuer.')
            return None
        data = loads(response.text)
        return {data['crumbRequestField']: data['crumb']}

    @staticmethod
    def is_token(token):
        if len(token) != 34:
            return False
        try:
            int(token, 16)
        except ValueError:
            return False
        return True

    def listjobs(self):
        uri = '%s/api/json' % self.server
        params = {'pretty': 'true'}
        try:
            response = requests.get(uri, auth=self.credentials, data=params)
            response.raise_for_status()
        except requests.exceptions.RequestException, e:
            output.error('jenkinsnotifier: Unable to get uri %s.' % uri)
            output.error('jenkinsnotifier: Error %s.' % (e, ))
            return None
        return loads(response.text)['jobs']

    def getjobinfo(self, job):
        uri = '%s/job/%s/api/json' % (self.server, job)
        try:
            response = requests.get(uri, auth=self.credentials)
            response.raise_for_status()
        except requests.exceptions.RequestException, e:
            output.error('jenkinsnotifier: Unable to get uri %s.' % uri)
            output.error('jenkinsnotifier: Error %s.' % (e, ))
            return None
        return loads(response.text)

    def build(self, job, uri=str(), jobparams=None):
        if not uri:
            uri = '%s/job/%s/build' % (self.server, job)
        if not self.crumb:
            output.error('jenkinsnotifier: Unable to build %s with uri %s.' % (job, uri))
            output.error('crumb is none')
            return False
        params = self.crumb
        params['delay'] = 60  #set a 60s delay to ensure release phase from build plugin is done
        params['token'] = create_sha1(job)
        params['cause'] = 'xbuilder released a prebuilt.'
        if jobparams:
            params['json'] = dumps({
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
        try:
            response = requests.post(uri, auth=self.credentials, data=params)
            response.raise_for_status()
        except requests.exceptions.RequestException, e:
            output.error('jenkinsnotifier: Unable to build %s with uri %s.' % (job, uri))
            output.error('jenkinsnotifier: Error %s.' % (e, ))
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

    def release(self, build_info):
        if not build_info['success']:
            return

        if not self.params['jobname']:
            output.warn('jenkinsnotifier: no jobname defined in configuration file.')
            return

        my_match = {
            'category': build_info['category'],
            'package': build_info['pkg_name'],
            'version': build_info['version'],
            'arch': build_info['arch']
        }
        jobname = ''
        for substring in re.split(r'\${([a-z]+)}', self.params['jobname']):
            jobname += my_match[substring] if substring in my_match.keys() else substring
        jobs = self.jenkins.listjobs()
        if jobs is None:
            output.warn('no jobs could be retrieved')
            return

        for job in jobs:
            if job['name'] == jobname:
                jinfo = self.jenkins.getjobinfo(job['name'])
                if jinfo is None:
                    output.warn('no jobinfo could be retrieved')
                    continue
                actions = jinfo['actions'][0]
                withparams = 'with' if 'parameterDefinitions' in actions else 'without'
                output.info(
                    'jenkinsnotifier: will trigger job %s %s parameters (%s).' % (jobname, withparams, job['url'])
                )
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
                return

        output.warn('jenkinsnotifier: job not found on server %s', self.params['uri'])


def register(builder):
    builder.add_plugin(XBuilderJenkinsNotifierPlugin)
