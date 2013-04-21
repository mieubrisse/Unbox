#!/usr/bin/python

import unittest
import os
import shutil
import logging
import sys
import dropbox_module
import local_module

class TestDropboxModule(unittest.TestCase):
    """Tests the Dropbox filesystem module"""

    # Test environment folder structure
    _TEST_DIRNAME = "dropbox_module_test"
    _TEST_DROPBOX_DIRPATH = os.path.join(_TEST_DIRNAME, "test_dropbox")
    _TEST_DROPBOX_UNBOX_DIRNAME = "test_unbox"

    _log = logging.getLogger("TestDropboxModule")

    def setUp(self):
        """Creates a test directory and a test Dropbox directory within that"""
        os.mkdir(self._TEST_DIRNAME)
        os.mkdir(self._TEST_DROPBOX_DIRPATH)

    def test_clean_init(self):
        """Tests a clean initialization"""
        dropbox_module.DropboxModule(self._TEST_DROPBOX_DIRPATH, self._TEST_DROPBOX_UNBOX_DIRNAME)

    def test_preexisting_unbox_init(self):
        """Tests an initialization with the Unbox directory already existing"""
        os.mkdir(os.path.join(self._TEST_DROPBOX_DIRPATH, self._TEST_DROPBOX_UNBOX_DIRNAME))
        dropbox_module.DropboxModule(self._TEST_DROPBOX_DIRPATH, self._TEST_DROPBOX_UNBOX_DIRNAME)

    def test_bad_unbox_dirname_init(self):
        """Test init with an empty Unbox dirname"""
        self.assertRaises(ValueError, dropbox_module.DropboxModule, self._TEST_DROPBOX_DIRPATH, "")
        self.assertRaises(TypeError, dropbox_module.DropboxModule, self._TEST_DROPBOX_DIRPATH, None)

    def test_bad_dropbox_dirpath_init(self):
        """Test init with a bogus and empty Dropbox dirpath"""
        self.assertRaises(ValueError, dropbox_module.DropboxModule, "$@%@#!%", self._TEST_DROPBOX_UNBOX_DIRNAME)
        self.assertRaises(ValueError, dropbox_module.DropboxModule, "", self._TEST_DROPBOX_UNBOX_DIRNAME)
        self.assertRaises(TypeError, dropbox_module.DropboxModule, None, self._TEST_DROPBOX_UNBOX_DIRNAME)

    def test_add_resources(self):
        """Adds two files normally, then adds a collision"""
        # Set up first file
        TEST_FILENAME = "test.txt"
        test_filepath = os.path.join(self._TEST_DIRNAME, TEST_FILENAME)
        test_fp = open(test_filepath, "w")
        test_fp.write("This is test text!")
        test_fp.close()

        # Set up second file
        TEST2_FILENAME = "test.txt2"
        test2_filepath = os.path.join(self._TEST_DIRNAME, TEST2_FILENAME)
        test2_fp = open(test2_filepath, "w")
        test2_fp.write("This is a different test text!")
        test2_fp.close()

        # Set up module
        test_module = dropbox_module.DropboxModule(self._TEST_DROPBOX_DIRPATH, self._TEST_DROPBOX_UNBOX_DIRNAME)
        test_module.add_resource(test_filepath)
        test_module.add_resource(test2_filepath)

        # Test files exist in memory
        resources_set = test_module.resources_set()
        self.assertTrue(TEST_FILENAME in resources_set)
        self.assertTrue(TEST2_FILENAME in resources_set)

        # Test files exist in OS
        resource1_dirname, _, _ = test_module.resource_info(TEST_FILENAME)
        resource2_dirname, _, _ = test_module.resource_info(TEST2_FILENAME)
        resource1_dirpath = os.path.join(self._TEST_DROPBOX_DIRPATH, self._TEST_DROPBOX_UNBOX_DIRNAME, resource1_dirname)
        resource2_dirpath = os.path.join(self._TEST_DROPBOX_DIRPATH, self._TEST_DROPBOX_UNBOX_DIRNAME, resource2_dirname)

        self.assertTrue(os.path.isdir(resource1_dirpath))
        self.assertTrue(os.path.isdir(resource2_dirpath))
        self.assertTrue(os.path.exists(test_module.resource_path(TEST_FILENAME)))
        self.assertTrue(os.path.exists(test_module.resource_path(TEST2_FILENAME)))

        # Test a collision
        self.assertRaises(ValueError, test_module.add_resource, TEST_FILENAME)

    def test_delete_resources(self):
        """Tests deletion of resources"""
        # Set up environment
        TEST_FILENAME = "test.txt"
        test_filepath = os.path.join(self._TEST_DIRNAME, TEST_FILENAME)
        test_fp = open(test_filepath, "w")
        test_fp.write("This is test text!")
        test_fp.close()

        test_module = dropbox_module.DropboxModule(self._TEST_DROPBOX_DIRPATH, self._TEST_DROPBOX_UNBOX_DIRNAME)
        test_module.add_resource(test_filepath)
        resource_dirname, _, _ = test_module.resource_info(TEST_FILENAME)
        resource_dirpath = os.path.join(self._TEST_DROPBOX_DIRPATH, self._TEST_DROPBOX_UNBOX_DIRNAME, resource_dirname)

        # Test valid deletion
        test_module.delete_resource(TEST_FILENAME)
        self.assertFalse(TEST_FILENAME in test_module.resources_set())
        self.assertFalse(os.path.exists(resource_dirpath))

        # Test deleting the same file again without re-adding it
        self.assertRaises(ValueError, test_module.delete_resource, TEST_FILENAME)

    def test_add_invalid_resource(self):
        """Attempts to add a nonexistent file and an empty path to Dropbox"""
        # Set up environment
        TEST_FILENAME = "test.txt"
        test_filepath = os.path.join(self._TEST_DIRNAME, TEST_FILENAME)
        test_module = dropbox_module.DropboxModule(self._TEST_DROPBOX_DIRPATH, self._TEST_DROPBOX_UNBOX_DIRNAME)

        self.assertRaises(ValueError, test_module.add_resource, test_filepath)
        self.assertRaises(ValueError, test_module.add_resource, "")

    def test_normal_versioning(self):
        """Tests that the resource versioning code works as expected"""
        # Set up environment
        TEST_FILENAME = "test.txt"
        TEST_FILEPATH = os.path.join(self._TEST_DIRNAME, TEST_FILENAME)
        test_fp = open(TEST_FILEPATH, "w")
        test_fp.write("This is test text!")
        test_fp.close()

        test_module = dropbox_module.DropboxModule(self._TEST_DROPBOX_DIRPATH, self._TEST_DROPBOX_UNBOX_DIRNAME)

        # Add regular versioned file
        TEST_VERSION = "2.3"
        TEST_DEPENDENCIES = set(["dep1", "dep2"])
        test_module.add_resource(TEST_FILEPATH, version=TEST_VERSION, dependencies=TEST_DEPENDENCIES)
        _, current_version, _ = test_module.resource_info(TEST_FILENAME)
        dependencies = set(test_module.version_info(TEST_FILENAME, TEST_VERSION))
        self.assertTrue(dependencies == TEST_DEPENDENCIES)
        self.assertEqual(TEST_VERSION, current_version)

        # Test copying of versions
        COPY_VERSION = "2.5"
        test_module.copy_version(TEST_FILENAME, TEST_VERSION, COPY_VERSION, copy_dependencies=True)
        old_version_info = test_module.version_info(TEST_FILENAME, TEST_VERSION)
        new_version_info = test_module.version_info(TEST_FILENAME, COPY_VERSION)
        self.assertEquals(len(old_version_info - new_version_info), 0)

        # Test changing 'current' pointer and deleting objects
        test_module.change_current_version(TEST_FILENAME, TEST_VERSION)
        self.assertRaises(ValueError, test_module.delete_version, TEST_FILENAME, TEST_VERSION)
        test_module.delete_version(TEST_FILENAME, COPY_VERSION)
        self.assertRaises(ValueError, test_module.change_current_version, TEST_FILENAME, COPY_VERSION)

    def test_version_dependencies(self):
        """Adds and removes depedencies from a version"""
        # Set up environment
        TEST_FILENAME = "test.txt"
        TEST_FILEPATH = os.path.join(self._TEST_DIRNAME, TEST_FILENAME)
        test_fp = open(TEST_FILEPATH, "w")
        test_fp.write("This is test text!")
        test_fp.close()

        test_module = dropbox_module.DropboxModule(self._TEST_DROPBOX_DIRPATH, self._TEST_DROPBOX_UNBOX_DIRNAME)
        TEST_VERSION = "2.3"
        test_module.add_resource(TEST_FILEPATH, version=TEST_VERSION)

        # Test adding and removing dependencies
        TEST_DEPENDENCY = "foo"
        test_module.add_version_dependency(TEST_FILENAME, TEST_VERSION, TEST_DEPENDENCY)
        dependencies = test_module.version_info(TEST_FILENAME, TEST_VERSION)
        self.assertTrue(TEST_DEPENDENCY in dependencies)
        self.assertRaises(ValueError, test_module.add_version_dependency, TEST_FILENAME, TEST_VERSION, "")
        test_module.delete_version_dependency(TEST_FILENAME, TEST_VERSION, TEST_DEPENDENCY)
        dependencies = test_module.version_info(TEST_FILENAME, TEST_VERSION)
        self.assertTrue(TEST_DEPENDENCY not in dependencies)
        self.assertRaises(ValueError, test_module.delete_version_dependency, TEST_FILENAME, TEST_VERSION, "")

    def tearDown(self):
        """Removes the test directories that were created"""
        shutil.rmtree(self._TEST_DIRNAME)

class TestLocalModule(unittest.TestCase):
    """Tests the local filesystem module"""

    # Test environment folder structure
    _TEST_DIRNAME = "local_module_test"
    _TEST_DROPBOX_DIRPATH = os.path.join(_TEST_DIRNAME, "test_dropbox")
    _TEST_LOCAL_UNBOX_DIRPATH = os.path.join(_TEST_DIRNAME, "test_unbox")

    # Fake resources in environment
    _TEST_RESOURCE1_FILEPATH = os.path.join(_TEST_DROPBOX_DIRPATH, "test_resource1")
    _TEST_RESOURCE2_FILEPATH = os.path.join(_TEST_DROPBOX_DIRPATH, "test_resource2")

    _log = logging.getLogger("TestLocalModule")

    def setUp(self):
        """Creates:
        - A directory to simulate the home directory, contining...
        - A directory with fake files to simulate the Dropbox directory inside of that
        """
        os.mkdir(self._TEST_DIRNAME)
        os.mkdir(self._TEST_DROPBOX_DIRPATH)

        resource1_fp = open(self._TEST_RESOURCE1_FILEPATH, 'w')
        resource1_fp.write("Resource 1's text is here!")
        resource1_fp.close()

        resource2_fp = open(self._TEST_RESOURCE2_FILEPATH, 'w')
        resource2_fp.write("This is resource 2's test text")
        resource2_fp.close()

    def test_clean_init(self):
        """Tests an initialization with a nonexistent local Unbox folder"""
        local_module.LocalModule(self._TEST_LOCAL_UNBOX_DIRPATH)

    def test_preexisting_unbox_folder(self):
        """Tests initialization with preexisting local Unbox folder"""
        os.mkdir(self._TEST_LOCAL_UNBOX_DIRPATH)
        local_module.LocalModule(self._TEST_LOCAL_UNBOX_DIRPATH)

    def test_add_link(self):
        """Tests adding a link to a resource"""
        test_module = local_module.LocalModule(self._TEST_LOCAL_UNBOX_DIRPATH)

        link_filename = "resource_link"
        resource_version = "1.0"
        link_filepath = os.path.join(self._TEST_DIRNAME, link_filename)
        test_module.add_link(self._TEST_RESOURCE1_FILEPATH, resource_version, "test_resource", resource_version)

        # Test for existence
        self.assertTrue(test_module.link_exists(link_filepath))

    def tearDown(self):
        """Cleans up the test environment"""
        shutil.rmtree(self._TEST_DIRNAME)


if __name__ == "__main__":
    logging.basicConfig(stream = sys.stderr)
    logging.getLogger("TestDropboxModule").setLevel(logging.DEBUG)
    logging.getLogger("TestLocalModule").setLevel(logging.DEBUG)
    unittest.main(verbosity=2)
