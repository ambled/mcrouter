# Copyright (c) 2015, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import re
import signal
import socket
import subprocess
import sys
import time
import unittest

from mcrouter.test.config import McrouterGlobals

class OutputCheckerTestCase(unittest.TestCase):
    def setUp(self):
        self.proc = None

    def tearDown(self):
        if self.proc:
            try:
                self.proc.terminate()
            except OSError:
                pass
            self.proc.wait()
        signal.alarm(0)

    def spawn(self, cmd):
        self.proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)

    def check_for_message(self, good, bad, timeout):
        stderr = ""

        def timeout_handler(signum, frame):
            self.fail("Timed out")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        for line in self.proc.stderr:
            stderr += line
            if re.search(bad, line):
                self.fail("bad regex matched '%s'" % line.strip())

            if re.search(good, line):
                signal.alarm(0)
                return

        self.fail("no good or bad matches in output: " + stderr)

class TestBadParams(OutputCheckerTestCase):
    def test_bad_config(self):
        listen_sock = socket.socket()
        listen_sock.listen(100)
        args = McrouterGlobals.preprocessArgs([
            McrouterGlobals.InstallDir + '/mcrouter/mcrouter', '-d',
            '-f', "/dev/null/doesnotexist",
            '--listen-sock-fd', str(listen_sock.fileno())
        ])

        self.spawn(args)
        self.check_for_message(
                good='Can not read config file',
                bad='reconfigured with',
                timeout=10)

        listen_sock.close()

    def test_bad_tko_param(self):
        listen_sock = socket.socket()
        listen_sock.listen(100)
        args = McrouterGlobals.preprocessArgs([
            McrouterGlobals.InstallDir + '/mcrouter/mcrouter', '-d',
            '-f', 'mcrouter/test/test_ascii.json',
            '--listen-sock-fd', str(listen_sock.fileno()),
            '--fibers-max-pool-size', 'uu'
        ])

        self.spawn(args)
        self.check_for_message(
                good="Option parse error: fibers_max_pool_size=uu,"
                " Couldn't convert value to integer",
                bad='mcrouter .* startup',
                timeout=10)

        listen_sock.close()
