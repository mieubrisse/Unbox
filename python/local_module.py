import os
import shutil
import json
import uuid
import unbox_filesystem

class LocalModule:
    """Module for the Unbox filesystem to handle local Unbox directory-related commands

    Handles backups and tracking of symlinks in the non-Dropbox filesystem
    """

    """ ========== Consants =========== """
    # Filename to store local data under
    _INDEX_FILENAME = "index.json"

    # Listing of local symlinks to resources
    _UNBOXED_RESOURCES_DICT_KEY = "unboxed_resources"

    # Key 
    _IGNORED_RESOURCES_LIST_KEY = "ignored_resources"

    # Path symlink points to
    _UNBXD_RSRC_INFO_KEY_LINKTARGET = "link_target"

    # Name of resource
    _UNBXD_RSRC_INFO_KEY_NAME = "resource_name"

    # Version of resource 
    _UNBXD_RSRC_INFO_KEY_VERSION = "resource_version"

    # Ignore new versions of resource
    _UNBXD_RSRC_INFO_KEY_IGNORENEW = "ignore_new_versions"

    # Constants for dealing with the backup system
    _BACKUP_DIRNAME = "backups"
    _BACKUP_INDEX_FILENAME = "index.json"



    """ ========== VARIABLES =========== """
    # Path to local Unbox directory
    _local_unbox_dirpath = ""

    # Mapping resources on local machine -> resource types on the machine {
    _local_index = {
        # Maps symlink's paths ->
            # resource path
            # resource name
            # resource version
            # whether link should ignore new resource versions
        _UNBOXED_RESOURCES_DICT_KEY : dict(),
        _IGNORED_RESOURCES_LIST_KEY : list()
    }

    # Mapping resources in backup -> directory in backup directory containing resource
    _backup_index = dict()



    def __init__(self, local_unbox_dirpath):
        """Instantiates a new module to manage the local Unbox directory

        Keyword Args:
        local_unbox_dirpath -- path to the local Unbox directory
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



    """ ========== LOCAL MANAGER FUNCTIONS =========== """
    def link_exists(self, link_path):
        """Checks if a link is being tracked by the system

        Keyword Args:
        link_path -- path of link to check for

        Returns:
        True if the link is being tracked, false otherwise
        """
        return link_path in self._local_index[_UNBOXED_RESOURCES_DICT_KEY]

    def link_info(self, link_path):
        """Gets the info dict for the link

        Keyword Args:
        link_path -- path to the link

        Returns:
        Tuple of (link target path, 
            target resource name, 
            target resource version, 
            flag indicating if link ignores new resource versions
        )
        """
        if not self.link_exists(link_path):
            raise ValueError("Could not get link info; link is not being tracked")

        link_info = self._local_index[_UNBOXED_RESOURCES_DICT_KEY][link_path]
        return (
                link_info[_UNBXD_RSRC_INFO_KEY_LINKTARGET],
                link_info[_UNBXD_RSRC_INFO_KEY_NAME],
                link_info[_UNBXD_RSRC_INFO_KEY_VERSION],
                link_info[_UNBXD_RSRC_INFO_KEY_IGNORENEW]
        )


    def add_link(self, link_path, resource_path, resource_name, resource_version, ignore_new=False):
        """Tracks a resource locally

        Keyword Args:
        link_path -- path to place the symlink in
        resource_path -- path of resource to link to
        resource_version -- version of target resource being used
        ignore_new -- whether the link shouldn't care about new resource versions
        """
        # Sanity checks
        link_path = os.path.abspath(link_path)
        resource_path = os.path.abspath(resource_path)
        if not os.path.exists(resource_path):
            raise ValueError("Cannot add link; resource at given path does not exist")
        if os.path.exists(link_path):
            raise ValueError("Cannot add link; file already exists at link path")
        if resource_name == None or len(resource_name.strip()) == 0:
            raise ValueError("Cannot add link; resource name is empty")
        if resource_version == None or len(resource_version.strip()) == 0:
            raise ValueError("Cannot add link; resource version is empty")
        if ignore_new != True and ignore_new != False:
            raise ValueError("Cannod add link; non-boolean value for ignore_new")
        resource_name = resource_name.strip()
        resource_version = resource_version.strip()

        # Add symlink to the filesystem
        os.symlink(link_path, resource_path)

        # Register addition in local index
        link_info = {
            _UNBXD_RSRC_INFO_KEY_LINKTARGET : resource_path,
            _UNBXD_RSRC_INFO_KEY_NAME : resource_name,
            _UNBXD_RSRC_INFO_KEY_VERSION : resource_version,
            _UNBXD_RSRC_INFO_KEY_IGNORENEW : ignore_new
        }
        self._local_index[_UNBOXED_RESOURCES_DICT_KEY][link_path] = link_info
        self._write_local_index()

    def delete_link(self, link_path):
        """Deletes a resource being tracked locally

        Keyword Args:
        link_path -- path to link to delete
        """
        if not self.link_exists(link_path):
            raise ValueError("Could not delete link; link does not exist")

        os.remove(link_path)
        del self._local_index[_UNBOXED_RESOURCES_DICT_KEY][link_path]
        self._write_index()


    def set_ignore_new(self, link_path, ignore_new):
        """Sets a link's flag for ignoring new resource versions

        Keyword Args:
        link_path -- path of link
        ignore_new -- boolean value to set
        """
        # Sanity check
        if not self.link_exists(link_path):
            raise ValueError("Could not set 'ignore new' field; link does not exist")
        if ignore_new != True and ignore_new != False:
            raise ValueError("Could not set 'ignore new' field; new value is not boolean")

        self._local_index[_UNBOXED_RESOURCES_DICT_KEY][link_path][_UNBXD_RSRC_INFO_KEY_IGNORENEW] = ignore_new
        self._write_local_index()

    def check_integrity(self):
        """Checks the integrity of the local store

        Returns:
        Tuple of (
            set of link paths whose links no longer exist,
            set of link paths whose link target is broken,
        )
        """
        nonexistent_links = set()
        broken_links = set()
        for link_path, link_info in self._local_index[_UNBOXED_RESOURCES_DICT_KEY]:
            if not os.path.lexists(link_path):
                nonexistent_links.add(link_path)
            if os.path.lexists(link_path) and not os.path.exists(link_path):
                broken_links.add(link_path)
        return (nonexistent_links, broken_links)




    """ ========== BACKUP FUNCTIONS =========== """
    def backup_exists(self, path):
        """Checks if the given resource is stored in the backup system

        Keyword Args:
        path -- local path to resource

        Returns True if the resource is already saved, or False otherwise"""
        return (path in self._backup_index.keys())

    """
    Gets the list of backed-up files
    """
    def backup_list(self):
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
        """Retrieves the file/diretory tree from the backup system

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
