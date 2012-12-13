import os
import shutil
import json
import uuid

"""
Class to manage all resources in the Unbox filesystem
"""
class Filesystem:
    # Constants for the local Unbox directory
    _local_unbox_dirpath = ""
    _LOCAL_INDEX_FILENAME = "index.json"

    # Constants for dealing with the backup system
    _BACKUP_DIRNAME = "backups"
    _BACKUP_INDEX_FILENAME = "index.json"

    # Constants for the Dropbox Unbox directory
    _dropbox_unbox_dirpath = ""
    _DROPBOX_INDEX_FILENAME = "index.json"
    _RESOURCE_INFO_KEY_PARENT_DIRNAME = "parent_directory"

    # Mapping resources in backup -> directory in backup directory containing resource
    _backup_index = dict()

    # Mapping resources in Dropbox -> information about resource{
    #   versions : list of version numbers
    #   directory : name of directory where resource is stored
    _dropbox_index = dict()


    """
    Instantiates a Filesystem object to handle Unbox's file operations
    - RETURNS: 
    """
    def __init__(self, local_unbox_dirpath, dropbox_dirpath, dropbox_unbox_dirname):
        local_unbox_dirpath = Filesystem.abs_path(local_unbox_dirpath)
        dropbox_dirpath = Filesystem.abs_path(dropbox_dirpath)

        # Ensure valid Dropbox path
        if not os.path.isdir(dropbox_dirpath):
            raise ValueError("Invalid Dropbox path")

        # Test if Dropbox Unbox directory exists and create if not
        dropbox_unbox_dirpath = os.path.join(dropbox_dirpath, dropbox_unbox_dirname)
        if not os.path.isdir(dropbox_unbox_dirpath):
            try:
                os.mkdir(dropbox_unbox_dirpath)
                os.mkdir(os.path.join(dropbox_unbox_dirpath, self._BACKUP_DIRNAME))
            except OSError as e:
                raise ValueError("Could not create Dropbox Unbox directory: " + str(e))

        # Test if local Unbox directory exists and create if not
        if not self._is_valid_local_dir(local_unbox_dirpath):
            try:
                self._make_local_dir(local_unbox_dirpath)
            except OSError as e:
                raise ValueError("Could not create local Unbox directory: " + str(e))

        # Register input variables
        self._local_unbox_dirpath = local_unbox_dirpath
        self._dropbox_unbox_dirpath = dropbox_unbox_dirpath

        # Read backup index file
        backup_index_filepath = os.path.join(local_unbox_dirpath, self._BACKUP_DIRNAME, self._BACKUP_INDEX_FILENAME)
        if os.path.isfile(backup_index_filepath):
            backup_index_fp = open(backup_index_filepath, "r")
            self._backup_index = json.load(backup_index_fp)
            backup_index_fp.close()

        # Read Dropbox index file
        dropbox_index_filepath = os.path.join(self._dropbox_unbox_dirpath, self._DROPBOX_INDEX_FILENAME)
        if os.path.isfile(dropbox_index_filepath):
            dropbox_index_fp = open(dropbox_index_filepath, "r")
            self._dropbox_index = json.load(dropbox_index_fp)
            dropbox_index_fp.close()


    """
    Gets the user-expanded, normalized, absolute path to a file object
    - path: path to find absolute path for
    - RETURN: absolute path to object
    """
    @staticmethod
    def abs_path(path):
        return os.path.abspath(os.path.expanduser(os.path.normpath(path)))


    """ ==========  Dropbox Functions =========== """
    """
    Checks if a resource is in the Dropbox Unbox system
    - resource: name of resource to check for
    - RETURN: true if the resource exists, false otherwise
    """
    def _dropbox_exists(self, resource, version):
        return (resource in self._dropbox_index.key())

    """
    Gets the absolute path to a resource in the Dropbox Unbox system
    - resource: name of resource
    """
    def _dropbox_get_resource_path(self, resource):
        # Check validity
        if not self._dropbox_exists(resource):
            raise ValueError("Could not get path to resource in Dropbox; resource does not exist")

        # Find resource and get absolute path
        resource_info = self._dropbox_index[resource]
        stored_loc_dirname = resource_info[
        

        os.path.join(self._dropbox_unbox_dirpath, 


    """
    Adds the given resource to the Dropbox system
    - path: path to resource to add
    - RETURN: true if the resource exists, false otherwise
    """
    def _dropbox_add(self, path):
        # Check validity
        path = Filesystem.abs_path(path)
        if not os.path.exists(path):
            raise ValueError("Cannot add file to dropbox; file does not exist")

        # Hashes the resource's full path, creates a directory with the hash name, and places the resource inside
        BACKUP_DIRPATH = os.path.join(self._local_unbox_dirpath, self._BACKUP_DIRNAME)
        upstream, basename = os.path.split(path)
        dest_dir = str(uuid.uuid4())
        dest_path = os.path.join(BACKUP_DIRPATH, dest_dir)
        os.mkdir(dest_path)
        shutil.move(path, dest_path)

        # Register the addition in the dropbox index
        self._dropbox_index[path] = dest_dir
        self._write_dropbox_index()

    """ ========== Validation Functions =========== """
    """
    Ensures the given local Unbox directory has all the necessary directories
    - path: path to local Unbox directory
    """
    def _is_valid_local_dir(self, path):
        backup_dir = os.path.join(path, self._BACKUP_DIRNAME)
        return os.path.isdir(path) and os.path.isdir(backup_dir)

    """
    Creates the elements of a local Unbox directory
    - path: path to Unbox directory
    """
    def _make_local_dir(self, path):
        if not os.path.isdir(path):
            os.mkdir(path)
        backup_dir = os.path.join(path, self._BACKUP_DIRNAME)
        if not os.path.isdir(backup_dir):
            os.mkdir(backup_dir)




    """ ========== Backup Functions =========== """
    """
    Checks if the given resource is stored in the backup system
    - path: local path to resource
    - RETURN: true if the resource is already saved, false otherwise
    """
    def backup_exists(self, path):
        return (path in self._backup_index.keys())

    """
    Gets the list of backed-up files
    """
    def backup_list(self):
        return self._backup_index.keys()

    """
    Moves the given file/directory tree into the backup system
    - path: local path to the file 
    """
    def backup_add(self, path):
        # Check validity
        path = Filesystem.abs_path(path)
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

    """
    Retrieves the file/diretory tree from the backup system
    - path: local path to retrieve
    """
    def backup_restore(self, path):
        # Check validity
        path = Filesystem.abs_path(path)
        if not self.backup_exists(path):
            raise ValueError("Cannot restore file from backup; file does not exist")

        # Restore backed-up resource into original location
        resource_filename = os.path.basename(path)
        BACKUP_DIRPATH = os.path.join(self._local_unbox_dirpath, self._BACKUP_DIRNAME)
        saved_loc_dirpath = os.path.join(BACKUP_DIRPATH, self._backup_index[path]) 
        saved_loc_filepath = os.path.join(saved_loc_dirpath, resource_filename)
        shutil.move(saved_loc_filepath, path)
        os.rmdir(saved_loc_dirpath)

        # Register the removal in the backup index 
        del(self._backup_index[path])
        self._write_backup_index()

    """
    Deletes a resource in the backup system
    - path: local path to resource
    """
    def backup_delete(self, path):
        # Check validity
        path = Filesystem.abs_path(path)
        if not self.backup_exists(path):
            raise ValueError("Cannot delete file from backup; file does not exist")


        # Remove the resource and the directory holding it
        resource_filename = os.path.basename(path)
        BACKUP_DIRPATH = os.path.join(self._local_unbox_dirpath, self._BACKUP_DIRNAME)
        saved_loc_dirpath = os.path.join(BACKUP_DIRPATH, self._backup_index[path]) 
        saved_loc_filepath = os.path.join(saved_loc_dirpath, resource_filename)
        if os.path.isdir(saved_loc_filepath):
            shutil.rmtree(saved_local_filepath)
        else:
            os.remove(path)
        os.rmdir(saved_loc_dirpath)

        # Register the removal in the backup index 
        del(self._backup_index[path])
        self._write_backup_index()

    """
    Writes the in-memory backup index to the backup index file
    """
    def _write_backup_index(self):
        BACKUP_DIRPATH = os.path.join(self._local_unbox_dirpath, self._BACKUP_DIRNAME)
        BACKUP_INDEX_FILEPATH = os.path.join(BACKUP_DIRPATH, self._BACKUP_INDEX_FILENAME)
        backup_index_fp = open(BACKUP_INDEX_FILEPATH, "w")
        json.dump(self._backup_index, backup_index_fp)
        backup_index_fp.close()


        

