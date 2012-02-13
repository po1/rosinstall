#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import subprocess
import tempfile
import shutil

import rosinstall
import rosinstall.helpers

from scm_test_base import AbstractRosinstallCLITest, AbstractRosinstallBaseDirTest, _create_fake_ros_dir, _create_yaml_file, _create_config_elt_dict


def _create_git_repo(git_path):
    os.makedirs(git_path)
    subprocess.check_call(["git", "init"], cwd=git_path)
    subprocess.check_call(["touch", "gitfixed.txt"], cwd=git_path)
    subprocess.check_call(["git", "add", "*"], cwd=git_path)
    subprocess.check_call(["git", "commit", "-m", "initial"], cwd=git_path)

def _create_hg_repo(hg_path):
    os.makedirs(hg_path)
    subprocess.check_call(["hg", "init"], cwd=hg_path)
    subprocess.check_call(["touch", "hgfixed.txt"], cwd=hg_path)
    subprocess.check_call(["hg", "add", "hgfixed.txt"], cwd=hg_path)
    subprocess.check_call(["hg", "commit", "-m", "initial"], cwd=hg_path)


class RosinstallOptionsTest(AbstractRosinstallBaseDirTest):
    """Test command line option for failure behavior"""
       
    @classmethod
    def setUpClass(self):
        AbstractRosinstallBaseDirTest.setUpClass()
        self.test_root_path = tempfile.mkdtemp()
        _create_fake_ros_dir(self.test_root_path)
        self.ros_path = os.path.join(self.test_root_path, "ros")
        
        # create a repo in git
        self.git_path = os.path.join(self.test_root_path, "gitrepo")
        _create_git_repo(self.git_path)

        self.git_path2 = os.path.join(self.test_root_path, "gitrepo2")
        _create_git_repo(self.git_path2)
        
        # create a repo in hg
        self.hg_path = os.path.join(self.test_root_path, "hgrepo")
        _create_hg_repo(self.hg_path)

        self.simple_rosinstall = os.path.join(self.test_root_path, "simple.rosinstall")
        self.simple_changed_vcs_rosinstall = os.path.join(self.test_root_path, "simple_changed_vcs.rosinstall")
        self.simple_changed_uri_rosinstall = os.path.join(self.test_root_path, "simple_changed_uri.rosinstall")
        self.broken_rosinstall = os.path.join(self.test_root_path, "broken.rosinstall")

        _create_yaml_file([_create_config_elt_dict("other", self.ros_path),
                           _create_config_elt_dict("git", "gitrepo", self.git_path)],
                          self.simple_rosinstall)

        # same local name for gitrepo, different uri
        _create_yaml_file([_create_config_elt_dict("other", self.ros_path),
                           _create_config_elt_dict("git", "gitrepo", self.git_path2)],
                          self.simple_changed_uri_rosinstall)

        _create_yaml_file([_create_config_elt_dict("other", self.ros_path),
                           _create_config_elt_dict("hg", "hgrepo", self.hg_path)],
                          self.simple_changed_vcs_rosinstall)

        _create_yaml_file([_create_config_elt_dict("other", self.ros_path),
                           _create_config_elt_dict("hg", "hgrepo", self.hg_path+"invalid")],
                          self.broken_rosinstall)
        
        
    @classmethod
    def tearDownClass(self):
        shutil.rmtree(self.test_root_path)
        
    def test_Rosinstall_help(self):
        cmd = self.rosinstall_fn
        cmd.append("-h")
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))
        
    def test_rosinstall_delete_changes(self):
        cmd = self.rosinstall_fn
        cmd.extend([self.directory, self.simple_rosinstall])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))
        cmd.extend([self.directory, self.simple_changed_uri_rosinstall, "--delete-changed-uri"])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))


    def test_rosinstall_abort_changes(self):
        cmd = self.rosinstall_fn
        cmd.extend([self.directory, self.simple_rosinstall])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))
        cmd.extend([self.directory, self.simple_changed_uri_rosinstall, "--abort-changed-uri", "-n"])
        self.assertEqual(1, subprocess.call(cmd, env=self.new_environ))


    def test_rosinstall_backup_changes(self):
        cmd = self.rosinstall_fn
        cmd.extend([self.directory, self.simple_rosinstall])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))
        directory1 = tempfile.mkdtemp()
        self.directories["backup1"] = directory1
        cmd.extend([self.directory, self.simple_changed_uri_rosinstall, "--backup-changed-uri=%s"%directory1])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))
        self.assertEqual(len(os.listdir(directory1)), 1)

    def test_rosinstall_change_vcs_type(self):
        cmd = self.rosinstall_fn
        cmd.extend([self.directory, self.simple_rosinstall])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))
        cmd.extend([self.directory, self.simple_changed_vcs_rosinstall, "--delete-changed-uri", "-n"])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))

    def test_rosinstall_invalid_fail(self):
        cmd = self.rosinstall_fn
        cmd.extend([self.directory, self.broken_rosinstall])
        self.assertEqual(1, subprocess.call(cmd, env=self.new_environ))

    def test_rosinstall_invalid_continue(self):
        cmd = self.rosinstall_fn
        cmd.extend([self.directory, self.broken_rosinstall, "--continue-on-error"])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))


