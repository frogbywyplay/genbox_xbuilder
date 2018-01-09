from __future__ import with_statement

import contextlib
import os
import shutil
import subprocess
import tarfile
import tempfile
import unittest
import types

from xutils import XUtilsError
from xbuilder.plugins.rootfs import XBuilderRootfsPlugin


@contextlib.contextmanager
def chdir(dir_):
    cur = os.getcwd()
    os.chdir(dir_)
    yield
    os.chdir(cur)


class TestXBuilderRootfsPlugin(unittest.TestCase):
    def setUp(self):
        self.tmpfl = tempfile.NamedTemporaryFile(delete=(os.getenv('KEEP_TMP') is None))
        self.tmpd = tempfile.mkdtemp()
        self.tmpwd = os.path.join(tempfile.mkdtemp(), 'wd')

    def tearDown(self):
        if os.getenv('KEEP_TMP') is None:
            self.tmpfl.close()
            shutil.rmtree(self.tmpd, True)
            shutil.rmtree(os.path.dirname(self.tmpwd), True)
        else:
            print(self.tmpfl.name, self.tmpd, self.tmpwd)

    def _log(self):
        self.tmpfl.flush()
        with open(self.tmpfl.name) as fl:
            return fl.read()

    def test_check_call_stdout_ok(self):
        plugin = XBuilderRootfsPlugin(None, None, self.tmpfl, self.tmpfl.name)
        plugin.log_fd = self.tmpfl
        plugin.check_call(['echo', 'hello, world!'], 'test err msg')
        self.assertEqual(self._log(), 'hello, world!\n')

    def test_check_call_stderr_ok(self):
        plugin = XBuilderRootfsPlugin(None, None, self.tmpfl, self.tmpfl.name)
        plugin.log_fd = self.tmpfl
        plugin.check_call(['bash', '-c', 'echo 1>&2 "hello, world!"'], 'test err msg')
        self.assertEqual(self._log(), 'hello, world!\n')

    def test_check_call_ko(self):
        plugin = XBuilderRootfsPlugin(None, None, self.tmpfl, self.tmpfl.name)
        plugin.log_fd = self.tmpfl
        self.assertRaises(XUtilsError, lambda: plugin.check_call(['cat', '/tmp/not/exist'], 'test err msg'))

    def test_tar_cf_root(self):
        plugin = XBuilderRootfsPlugin(None, self.tmpfl.write, self.tmpfl, self.tmpfl.name)
        plugin.log_fd = self.tmpfl
        shutil.copytree(os.path.join(os.path.dirname(__file__), 'workdir'), self.tmpwd)
        with chdir(self.tmpd):
            plugin.tar_cf('rootfs', dict(pkg_name='toto', version='2.3.88'), self.tmpwd, 'root', 'gz', '')
            with tarfile.open(os.path.join(self.tmpwd, 'toto-2.3.88_root.tar.gz')) as tfl:
                self.assertEqual(len(tfl.getmembers()), 6)
        self.assertIn('Creating rootfs archive', self._log())

    def test_tar_cf_debuginfo(self):
        plugin = XBuilderRootfsPlugin(None, self.tmpfl.write, self.tmpfl, self.tmpfl.name)
        plugin.log_fd = self.tmpfl
        shutil.copytree(os.path.join(os.path.dirname(__file__), 'workdir'), self.tmpwd)
        with chdir(self.tmpd):
            plugin.tar_cf(
                'debuginfo', dict(pkg_name='toto', version='2.3.88'), self.tmpwd, 'root/usr/lib/debug', 'gz', ''
            )
            with tarfile.open(os.path.join(self.tmpwd, 'toto-2.3.88_debuginfo.tar.gz')) as tfl:
                self.assertEqual(len(tfl.getmembers()), 2)
        self.assertIn('Creating debuginfo archive', self._log())

    def test_tar_cf_debuginfo_xz(self):
        plugin = XBuilderRootfsPlugin(None, self.tmpfl.write, self.tmpfl, self.tmpfl.name)
        plugin.log_fd = self.tmpfl
        use_pixz = dict(use_pixz=False)
        org_check_call = plugin.check_call

        def new_check_call(self, cmd, errmsg):
            use_pixz['use_pixz'] = '-Ipixz' in cmd
            org_check_call(cmd, errmsg)

        plugin.check_call = types.MethodType(new_check_call, plugin)
        shutil.copytree(os.path.join(os.path.dirname(__file__), 'workdir'), self.tmpwd)
        with chdir(self.tmpd):
            plugin.tar_cf(
                'debuginfo', dict(pkg_name='toto', version='2.3.88'), self.tmpwd, 'root/usr/lib/debug', 'xz', ''
            )
            self.assertTrue(use_pixz['use_pixz'])
            # python tar does not know xz
            out = subprocess.check_output(['file', os.path.join(self.tmpwd, 'toto-2.3.88_debuginfo.tar.xz')])
            self.assertIn('XZ compressed data', out)
        self.assertIn('Creating debuginfo archive', self._log())

    def test_postbuild(self):
        plugin = XBuilderRootfsPlugin(
            dict(build=dict(workdir=self.tmpwd), release=dict(compression='bz2', tar_extra_opts='')), self.tmpfl.write,
            self.tmpfl, self.tmpfl.name
        )
        plugin.log_fd = self.tmpfl
        shutil.copytree(os.path.join(os.path.dirname(__file__), 'workdir'), self.tmpwd)
        with chdir(self.tmpd):
            plugin.postbuild(dict(success=True, pkg_name='toto', version='2.3.88'))
            self.assertFalse(os.path.exists(os.path.join(self.tmpwd, 'root/usr/lib/debug')))
            with tarfile.open(os.path.join(self.tmpwd, 'toto-2.3.88_root.tar.bz2')) as tfl:
                self.assertEqual(len(tfl.getmembers()), 4)
            with tarfile.open(os.path.join(self.tmpwd, 'toto-2.3.88_debuginfo.tar.bz2')) as tfl:
                self.assertEqual(len(tfl.getmembers()), 2)
        log = self._log()
        self.assertIn('Creating rootfs archive', log)
        self.assertIn('Creating debuginfo archive', log)
