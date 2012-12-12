import os
import shutil
import json
import uuid

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

    # Mapping resources in backup -> directory in backup directory containing resource
    _backup_index = dict()


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

        self._local_unbox_dirpath = local_unbox_dirpath
        self._dropbox_unbox_dirpath = dropbox_unbox_dirpath

        # Read backup index file
        backup_index_filepath = os.path.join(local_unbox_dirpath, self._BACKUP_DIRNAME, self._BACKUP_INDEX_FILENAME)
        if os.path.isfile(backup_index_filepath):
            backup_index_fp = open(backup_index_filepath, "r")
            self._backup_index = json.load(backup_index_fp)
            backup_index_fp.close()

    """
    Gets the user-expanded, normalized, absolute path to a file object
    - path: path to find absolute path for
    - RETURN: absolute path to object
    """
    @staticmethod
    def abs_path(path):
        return os.path.abspath(os.path.expanduser(os.path.normpath(path)))


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
    def has_backup(self, path):
        return path in self._backup_index.keys()

    """
    Gets the list of backed-up files
    """
    def get_backup_list(self):
        return self._backup_index.keys()

    """
    Moves the given file/directory tree into the backup system
    - path: local path to the file 
    """
    def save_backup(self, path):
        # Check validity
        path = Filesystem.abs_path(path)
        if not os.path.exists(path):
            raise ValueError("Cannot add file to backup; file does not exist")

        # Hashes the resource's full path, creates a directory with the hash name, and places the resource inside
        BACKUP_DIRPATH = os.path.join(self._local_unbox_dirpath, self._BACKUP_DIRNAME)
        upstream, basename = os.path.split(path)
        dest_dir = str(uuid.uuid4())
        dest_path = os.path.join(BACKUP_DIRPATH, dest_dir)
        os.mkdir(dest_path)
        shutil.move(path, dest_path)

        # Tracks the file with the backup index
        self._backup_index[path] = dest_dir
        BACKUP_INDEX_FILEPATH = os.path.join(BACKUP_DIRPATH, self._BACKUP_INDEX_FILENAME)
        backup_index_fp = open(BACKUP_INDEX_FILEPATH, "w")
        json.dump(self._backup_index, backup_index_fp)
        backup_index_fp.close()

    """
    Retrieves the file/diretory tree from the backup system
    """
    def restore_backup(self, path):
        print "Nothing here yet!"
