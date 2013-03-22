import os
import shutil
import json
import uuid
import unbox_filesystem

class LocalModule:
    """Module for the Unbox filesystem to handle local Unbox directory-related commands"""

    """ ========== Constants =========== """
    # Constants for the local Unbox directory
    _INDEX_FILENAME = "index.json"
    _UNBOXED_RESOURCES_DICT_KEY = "unboxed_resources"
    _IGNORED_RESOURCES_LIST_KEY = "ignored_resources"
    _UNBXD_RSRC_INFO_KEY_LINKPATH = "link_path"
    _UNBXD_RSRC_INFO_KEY_LINKTARGET = "link_target"
    _UNBXD_RSRC_INFO_KEY_NAME = "name"
    _UNBXD_RSRC_INFO_KEY_VERSION = "version"

    # Constants for dealing with the backup system
    _BACKUP_DIRNAME = "backups"
    _BACKUP_INDEX_FILENAME = "index.json"



    """ ========== Variables =========== """
    # Path to local Unbox directory
    _local_unbox_dirpath = ""

    # Mapping resources on local machine -> resource types on the machine {
    _local_index = {
        _UNBOXED_RESOURCES_DICT_KEY : dict(),
        _IGNORED_RESOURCES_LIST_KEY : list()
    }

    # Mapping resources in backup -> directory in backup directory containing resource
    _backup_index = dict()



    """ ========== Functions =========== """
    def __init__(self, local_unbox_dirpath):
        """Instantiates a new module to manage the local Unbox directory

        Keyword Args:
        local_unbox_dirpath -- path to the local Unbox directory

        Returns: a new manager for the local unbox filesystem
        """
        local_unbox_dirpath = unbox_filesystem.abs_path(local_unbox_dirpath)

        # Test if local Unbox directory exists and create if not
        if not self._is_valid_local_dir(local_unbox_dirpath):
            try:
                self._make_local_dir(local_unbox_dirpath)
            except OSError as e:
                raise ValueError("Could not create local Unbox directory: " + str(e))

        # Register input variables
        self._local_unbox_dirpath = local_unbox_dirpath

        # Read backup index file
        backup_index_filepath = os.path.join(local_unbox_dirpath, self._BACKUP_DIRNAME, self._BACKUP_INDEX_FILENAME)
        if os.path.isfile(backup_index_filepath):
            backup_index_fp = open(backup_index_filepath, "r")
            self._backup_index = json.load(backup_index_fp)
            backup_index_fp.close()

        # Read local index file
        local_index_filepath = os.path.join(self._local_unbox_dirpath, self._INDEX_FILENAME)
        if os.path.isfile(local_index_filepath):
            dropbox_index_fp = open(dropbox_index_filepath, "r")
            self._dropbox_index = json.load(dropbox_index_fp)
            dropbox_index_fp.close()



    """ ========== Validation Functions =========== """
    def _is_valid_local_dir(self, path):
        """Ensures the given local Unbox directory has all the necessary directories

        Keyword Args:
        path -- path to local Unbox directory
        """
        backup_dir = os.path.join(path, self._BACKUP_DIRNAME)
        return os.path.isdir(path) and os.path.isdir(backup_dir)

    def _make_local_dir(self, path):
        """Creates the elements of a local Unbox directory

        Keyword Args:
        path -- path to Unbox directory
        """
        if not os.path.isdir(path):
            os.mkdir(path)
        backup_dir = os.path.join(path, self._BACKUP_DIRNAME)
        if not os.path.isdir(backup_dir):
            os.mkdir(backup_dir)

    """ ========== Non-Backup Functions =========== """
    def _write_local_index(self):
        """Writes the in-memory local index to the local index file"""
        INDEX_FILEPATH = os.path.join(self._local_unbox_dirpath, self._INDEX_FILENAME)
        local_index_fp = open(INDEX_FILEPATH, "w")
        json.dump(self._local_index, local_index_fp, indent=4)
        local_index_fp.close()

    def local_add(self, local_path, dropbox_path):
        """Adds the given Dropbox resource to the local filesystem at the given location

        Keyword Args:
        local_path -- local path to place the resource at
        dropbox_path -- path to resource in Dropbox
        """
        # Validate input
        if not os.path.exists(local_path):
            ValueError("Local_path must exist")
        if not os.path.exists(dropbox_path):
            ValueError("Dropbox_path must exist")

        # TODO Add resource to local index




    """ ========== Backup Functions =========== """
    def backup_exists(self, path):
        """Checks if the given resource is stored in the backup system

        Keyword Args:
        path -- local path to resource

        Return: true if the resource is already saved, false otherwise
        """
        return (path in self._backup_index.keys())

    def backup_list(self):
        """Gets the list of backed-up files

        Return: set of backed-up files
        """
        return self._backup_index.keys()

    def backup_add(self, path):
        """Moves the given file/directory tree into the backup system

        Keyword Args:
        path -- local path to the file 
        """
        # Check validity
        path = unbox_filesystem.abs_path(path)
        if not os.path.exists(path):
            raise ValueError("Cannot add file to backup; file does not exist")
        if self.backup_exists(path):
            raise ValueError("Cannot add file to backup; file already exists in backup")

        # Hashes the resource's full path, creates a directory with the hash name, and places the resource inside
        BACKUP_DIRPATH = os.path.join(self._local_unbox_dirpath, self._BACKUP_DIRNAME)
        upstream, basename = os.path.split(path)
        dest_dir = str(uuid.uuid4())
        dest_path = os.path.join(BACKUP_DIRPATH, dest_dir)
        os.mkdir(dest_path)
        shutil.move(path, dest_path)

        # Register the addition in the backup index
        self._backup_index[path] = dest_dir
        self._write_backup_index()

    def backup_restore(self, path):
        """Retrieves the resource from the backup system to its prior spot

        Keyword Args:
        path -- local path to retrieve
        """
        # Check validity
        path = unbox_filesystem.abs_path(path)
        if not self.backup_exists(path):
            raise ValueError("Cannot restore file from backup; file does not exist")

        # Restore backed-up resource into original location
        resource_filename = os.path.basename(path)
        BACKUP_DIRPATH = os.path.join(self._local_unbox_dirpath, self._BACKUP_DIRNAME)
        resource_parent_dirpath = os.path.join(BACKUP_DIRPATH, self._backup_index[path]) 
        resource_parent_filepath = os.path.join(resource_parent_dirpath, resource_filename)
        shutil.move(resource_parent_filepath, path)
        os.rmdir(resource_parent_dirpath)

        # Register the removal in the backup index 
        del(self._backup_index[path])
        self._write_backup_index()

    def backup_delete(self, path):
        """Deletes a resource in the backup system

        Keyword Args:
        path -- local path to resource
        """
        # Check validity
        path = unbox_filesystem.abs_path(path)
        if not self.backup_exists(path):
            raise ValueError("Cannot delete file from backup; file does not exist")


        # Remove the resource and the directory holding it
        resource_filename = os.path.basename(path)
        BACKUP_DIRPATH = os.path.join(self._local_unbox_dirpath, self._BACKUP_DIRNAME)
        resource_parent_dirpath = os.path.join(BACKUP_DIRPATH, self._backup_index[path]) 
        resource_parent_filepath = os.path.join(resource_parent_dirpath, resource_filename)
        if os.path.isdir(resource_parent_filepath):
            shutil.rmtree(saved_local_filepath)
        else:
            os.remove(path)
        os.rmdir(resource_parent_dirpath)

        # Register the removal in the backup index 
        del(self._backup_index[path])
        self._write_backup_index()

    def _write_backup_index(self):
        """Writes the in-memory backup index to the backup index file"""
        BACKUP_DIRPATH = os.path.join(self._local_unbox_dirpath, self._BACKUP_DIRNAME)
        BACKUP_INDEX_FILEPATH = os.path.join(BACKUP_DIRPATH, self._BACKUP_INDEX_FILENAME)
        backup_index_fp = open(BACKUP_INDEX_FILEPATH, "w")
        json.dump(self._backup_index, backup_index_fp, indent=4)
        backup_index_fp.close()
