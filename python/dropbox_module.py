import os
import shutil
import pickle
import uuid
import unbox_filesystem

class DropboxModule:
    """Module for the Unbox filesystem to expose Dropbox-managing functionality
    
    Keeps track of all resources in the Unbox folder in Dropbox
    All modifications to said folder should be through this module
    """


    """ ========== CONSTANTS =========== """
    # Name of file to store Dropbox data in
    _INDEX_FILENAME = "index"

    # Name of directory containing all versions of a resource
    _RSRC_INFO_KEY_PARENT_DIRNAME = "parent_dirname"

    # Key to dict of resource versions mapped to info about the version
    _RSRC_INFO_KEY_VERSIONS_INFO = "versions_info"

    # Version that the "current" symlink in the resource directory is pointing to
    _RSRC_INFO_KEY_CURRENT_VERSION = "current_version"

    # Key to version dependencies
    _VERSION_INFO_KEY_DEPENDENCIES = "dependencies"

    # Pseudo version name to represent the current version
    _CURRENT_RSRC_VERSION_KEYWORD = "current"



    def __init__(self, dropbox_dirpath, unbox_dirname):
        """Instantiates a new Dropbox filesystem module at the given location

        Keyword Args:
        dropbox_dirpath -- path to the user's Dropbox directory
        unbox_dirname -- name of Unbox directory in the Dropbox folder
        """
        # Ensure argument validity
        if dropbox_dirpath == None or unbox_dirname == None:
            raise TypeError("Cannot use 'None' type")
        if len(dropbox_dirpath.strip()) == 0 or len(unbox_dirname.strip()) == 0:
            raise ValueError("Cannot have empty arguments")
        dropbox_dirpath = unbox_filesystem.abs_path(dropbox_dirpath)

        # Ensure valid Dropbox path
        if not os.path.isdir(dropbox_dirpath):
            raise ValueError("Invalid Dropbox path")

        # Test if Dropbox Unbox directory exists and create if not
        unbox_dirpath = os.path.join(dropbox_dirpath, unbox_dirname)
        if not os.path.isdir(unbox_dirpath):
            try:
                os.mkdir(unbox_dirpath)
            except OSError as e:
                raise ValueError("Could not create Dropbox Unbox directory: " + str(e))
        self._unbox_dirpath = unbox_dirpath # Path to Dropbox Unbox directory

        # Read Dropbox index file
        dropbox_index_filepath = os.path.join(self._unbox_dirpath, self._INDEX_FILENAME)
        if os.path.isfile(dropbox_index_filepath):
            dropbox_index_fp = open(dropbox_index_filepath, "r")
            self._dropbox_index = pickle.load(dropbox_index_fp)
            dropbox_index_fp.close()
        else:
            self._dropbox_index = dict()
        # _dropbox_index maps resource names in Dropbox -> info dict{
        #   versions_info : version name -> info dict{
        #       dependencies : list of dependencies version needs[]
        #   current_version : version that will be used by default
        #   directory : name of directory where resource is stored




    """ ======= Helper Methods ======= """
    def _write_index(self):
        """Writes the in-memory index to the index file in Dropbox"""
        INDEX_FILEPATH = os.path.join(self._unbox_dirpath, self._INDEX_FILENAME)
        dropbox_index_fp = open(INDEX_FILEPATH, "w")
        pickle.dump(self._dropbox_index, dropbox_index_fp)
        dropbox_index_fp.close()

    def resource_exists(self, resource):
        """Checks if a resource is in the Dropbox Unbox system

        Keyword Args:
        resource -- name of resource to check for

        Return: 
        True if the resource exists, false otherwise
        """
        return resource in self._dropbox_index

    def version_exists(self, resource_name, version):
        """Sanity check function to ensure a version exists for a resource

        Keyword Args:
        resource -- resource to check for version
        version -- version to check for

        Return: 
        True if the version exists, false otherwise
        """
        # Ensure validity
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot check if resource version exists; cannot find resource")
        resource_info = self._dropbox_index[resource_name]
        resource_versions_info = resource_info[self._RSRC_INFO_KEY_VERSIONS_INFO]
        return version in resource_versions_info




    """ ======= RESOURCE METHODS ======= """
    def resources_set(self):
        """Gets resources stored in Dropbox

        Return: 
        Set of names of resources in Dropbox
        """
        return self._dropbox_index.keys()

    def resource_info(self, resource_name):
        """Gets the dictionary entry for the given resource

        Keyword Args:
        resource_name: name of resource in Dropbox

        Return: 
        Tuple of (resource dirname, current version number, set of version names)
        """
        # Sanity check
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot get resource info; resource does not exist")

        resource_info = self._dropbox_index[resource_name]
        return (
                resource_info[self._RSRC_INFO_KEY_PARENT_DIRNAME],
                resource_info[self._RSRC_INFO_KEY_CURRENT_VERSION], 
                resource_info[self._RSRC_INFO_KEY_VERSIONS_INFO].keys()
            )

    def resource_path(self, resource, version=None):
        """Gets the full path to a resource with the given version in the Dropbox Unbox system
        NOTE: If no version is supplied, function will return a path to version currently in use, which is dynamic and may change

        Keyword Args:
        resource -- name of resource
        version -- name of resoure's version to look up (default: current)

        Return:
        Absolute path to the resource
        """
        # Check validity
        if not self.resource_exists(resource):
            raise ValueError("Could not get path to resource in Dropbox; resource does not exist")
        if version is not None and not self.version_exists(resource, version):
            raise ValueError("Could not find version for resource; version does not exist")

        # Find resource and get absolute path
        resource_info = self._dropbox_index[resource]
        resource_parent_dirname = resource_info[self._RSRC_INFO_KEY_PARENT_DIRNAME]
        if version is None:
            version = self._CURRENT_RSRC_VERSION_KEYWORD
        else:
            version = resource_info[self._RSRC_INFO_KEY_CURRENT_VERSION]

        resource_path = os.path.join(self._unbox_dirpath, resource_parent_dirname, version, resource)
        return resource_path

    def add_resource(self, local_path, version="1.0", dependencies=None):
        """Copies the given resource into the Dropbox system
        NOTE: The resource must not already be in the system

        Keyword Args:
        path -- path to resource to add
        version -- version to give the resource (default: 1.0)
        dependencies -- dependencies the resource depends on (default: None)

        Return:
        Path to the resource in Dropbox
        """
        if dependencies == None:
            dependencies = set()

        # Sanity checks
        if local_path == None:
            raise ValueError("Cannot add resource to Dropbox directory; cannot use null resource")
        local_path = unbox_filesystem.abs_path(local_path)
        upstream, resource_filename = os.path.split(local_path)
        if not os.path.exists(local_path):
            raise ValueError("Cannot add resource to Dropbox; resource does not exist")
        if not (os.path.isdir(local_path) or os.path.isfile(local_path)):
            raise ValueError("Cannot add resource to Dropbox; resource is not a file or directory")
        if resource_filename in self._dropbox_index:
            raise ValueError("Cannot add resource to Dropbox; resource with same name already exists")
        if version == None or len(version.strip()) == 0:
            raise ValueError("Cannot have empty version name")
        version = version.strip()
        if version == self._CURRENT_RSRC_VERSION_KEYWORD:
            raise ValueError("Version name '" + self._CURRENT_RSRC_VERSION_KEYWORD + "' is a reserved name")

        # Creates directory structure to copy resource to
        upstream, resource_filename = os.path.split(local_path)
        parent_dirname = str(uuid.uuid4())
        parent_dirpath = os.path.join(self._unbox_dirpath, parent_dirname)
        os.mkdir(parent_dirpath)
        version_dirpath = os.path.join(parent_dirpath, str(version))
        os.mkdir(version_dirpath)

        # Creates symlink to current version
        current_version_linkpath = os.path.join(parent_dirpath, self._CURRENT_RSRC_VERSION_KEYWORD)
        os.symlink(version_dirpath, current_version_linkpath)

        # Copies resource to proper spot
        dest_dirpath = os.path.join(parent_dirpath, str(version))
        if os.path.isdir(local_path):
            shutil.copytree(local_path, dest_dirpath)
        else:
            shutil.copy(local_path, dest_dirpath)

        # Register the addition in the Dropbox index
        version_info = {
            self._VERSION_INFO_KEY_DEPENDENCIES : dependencies
        }
        resource_info = {
            self._RSRC_INFO_KEY_PARENT_DIRNAME : parent_dirname, 
            self._RSRC_INFO_KEY_VERSIONS_INFO : { str(version) : version_info },
            self._RSRC_INFO_KEY_CURRENT_VERSION : version
        }
        self._dropbox_index[resource_filename] = resource_info
        self._write_index()

        return dest_dirpath

    def delete_resource(self, resource_name):
        """Deletes a resource and all its versions from the Dropbox Unbox filesystem

        Keyword Args:
        resource -- name of resource to delete
        """
        # Sanity check
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot delete resource; cannot find resource")

        # Perform delete and write to file
        resource_dirname = self._dropbox_index[resource_name][self._RSRC_INFO_KEY_PARENT_DIRNAME]
        resource_dirpath = os.path.join(self._unbox_dirpath, resource_dirname)
        del(self._dropbox_index[resource_name])
        shutil.rmtree(resource_dirpath)
        self._write_index()



    """ ======= Version Methods ======= """
    def version_info(self, resource_name, version):
        """Gets information about a resource version

        Keyword Args:
        resource_name -- name of resource to get info about
        version -- version to get info about

        Return: 
        Set of version dependencies
        """
        # Sanity check
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot get resource version info; cannot find resource")
        if not self.version_exists(resource_name, version):
            raise ValueError("Cannot get resource version info; cannot find version")

        # Extract version info
        resource_info = self._dropbox_index[resource_name]
        versions_info = resource_info[self._RSRC_INFO_KEY_VERSIONS_INFO]
        version_info = versions_info[version]
        return version_info[self._VERSION_INFO_KEY_DEPENDENCIES]

    def copy_version(self, resource_name, source_version, new_version, copy_dependencies=True):
        """Copies the given resource file ONLY into a new version

        Keyword Args:
        resource_name -- name of resource to create version for
        new_version -- name of new version
        source_version -- version to copy resource from; defaults to current version
        move_current -- whether to move the 'current' pointer to the newly-created version
        """
        # Sanity checks
        if new_version == None or len(new_version.strip()) == 0:
            raise ValueError("Cannot add resource version; cannot add empty version name")
        new_version = new_version.strip()
        if new_version == self._CURRENT_RSRC_VERSION_KEYWORD:
            raise ValueError("Resource name '" + self._CURRENT_RSRC_VERSION_KEYWORD + "' is a reserved name")
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot add resource version; cannot find resource")
        if not self.version_exists(resource_name, source_version):
            raise ValueError("Cannot add resource version; cannot find source version")

        # Create files for new version from source version
        resource_info = self._dropbox_index[resource_name]
        resource_dirname = resource_info[self._RSRC_INFO_KEY_PARENT_DIRNAME]
        new_version_dirpath = os.path.join(self._unbox_dirpath, resource_dirname, new_version)
        os.mkdir(new_version_dirpath)
        new_version_filepath = os.path.join(new_version_dirpath, resource_name)
        if source_version == self._CURRENT_RSRC_VERSION_KEYWORD:
            source_version_filepath = os.path.join(self._unbox_dirpath, resource_dirname, self._CURRENT_RSRC_VERSION_KEYWORD)
        else:
            source_version_filepath = os.path.join(self._unbox_dirpath, resource_dirname, source_version, resource_name)
        if os.path.isdir(source_version_filepath):
            shutil.copytree(source_version_filepath, new_version_dirpath)
        else:
            shutil.copy(source_version_filepath, new_version_dirpath)

        # Update in-memory copy
        resource_versions_info = resource_info[self._RSRC_INFO_KEY_VERSIONS_INFO]
        source_version_info = resource_versions_info[source_version]
        new_version_info = dict()
        if copy_dependencies == True:
            new_version_info[self._VERSION_INFO_KEY_DEPENDENCIES] = set(source_version_info[self._VERSION_INFO_KEY_DEPENDENCIES])
        else:
            new_version_info[self._VERSION_INFO_KEY_DEPENDENCIES] = set()
        resource_versions_info[new_version] = new_version_info

        self._write_index()

    def add_version_dependency(self, resource_name, version_name, dependency_name):
        """Adds the given dependency to the given resource version

        Keyword Args:
        resource_name -- name of resource to modify version for
        version_name -- name of version to add dependency to
        dependency -- dependency to add
        """
        # Sanity check
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot add version dependency; cannot find resource")
        if not self.version_exists(resource_name, version_name):
            raise ValueError("Cannot add version dependency; cannot find resource version")
        if dependency_name == None or len(dependency_name.strip()) == 0:
            raise ValueError("Cannot add version dependency; dependency name must be non-empty string")

        # Add version dependency to in-memory list and write to file
        versions_info = self._dropbox_index[resource_name][self._RSRC_INFO_KEY_VERSIONS_INFO]
        version_dependencies = versions_info[version_name][self._VERSION_INFO_KEY_DEPENDENCIES]
        if dependency_name not in version_dependencies:
            version_dependencies.add(dependency_name)
            self._write_index()

    def delete_version_dependency(self, resource_name, version_name, dependency_name):
        """Deletes the given dependency for the given resource version

        Keyword Args:
        resource_name -- name of resource to modify version for
        version_name -- name of version to delete dependency from
        dependency -- dependency to delete
        """
        # Sanity check
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot add version dependency; cannot find resource")
        if not self.version_exists(resource_name, version_name):
            raise ValueError("Cannot add version dependency; cannot find resource version")
        if dependency_name == None or len(dependency_name.strip()) == 0:
            raise ValueError("Cannot add version dependency; dependency name must be non-empty string")

        # Remove version dependency from in-memory list and write to file
        versions_info = self._dropbox_index[resource_name][self._RSRC_INFO_KEY_VERSIONS_INFO]
        version_dependencies = versions_info[version_name][self._VERSION_INFO_KEY_DEPENDENCIES]
        version_dependencies.discard(dependency_name)
        self._write_index()

    def change_current_version(self, resource_name, version):
        """Changes the current version of a Dropbox resource

        Keyword Args:
        resource_name -- name of resource to change version for
        version -- version to point resource to
        """
        # Sanity check
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot change resource version; cannot find resource")
        if not self.version_exists(resource_name, version):
            raise ValueError("Cannot change resource version; cannot find version")

        # Perform version change and write changes to file
        resource_dirname = self._dropbox_index[resource_name][self._RSRC_INFO_KEY_PARENT_DIRNAME]
        resource_dirpath = os.path.join(self._unbox_dirpath, resource_dirname)
        current_rsrc_version_linkpath = os.path.join(
                resource_dirpath,
                self._CURRENT_RSRC_VERSION_KEYWORD)
        target_rsrc_version_filepath = os.path.join(
                resource_dirpath,
                version,
                resource_name)
        os.unlink(current_rsrc_version_linkpath)
        os.symlink(target_rsrc_version_filepath, current_rsrc_version_linkpath)
        self._dropbox_index[resource_name][self._RSRC_INFO_KEY_CURRENT_VERSION] = version
        self._write_index()

    def delete_version(self, resource_name, version):
        """Deletes the given version of a Dropbox resource

        Keyword Args:
        resource_name -- name of resource to change version for
        version -- version to point resource to
        """
        # Sanity check
        if version == self._CURRENT_RSRC_VERSION_KEYWORD:
            raise ValueError("Cannot delete current version")
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot delete resource version; cannot find resource")
        if not self.version_exists(resource_name, version):
            raise ValueError("Cannot delete resource version; cannot find version")
        resource_info = self._dropbox_index[resource_name]
        resource_versions = resource_info[self._RSRC_INFO_KEY_VERSIONS_INFO]
        if version == resource_info[self._RSRC_INFO_KEY_CURRENT_VERSION]:
            raise ValueError("Cannot delete resource version; version is current version -- change current version first")
        if len(resource_versions) <= 1:
            raise ValueError("Cannot delete resource version; no other versions exist")

        # Delete data associated with version and write changes to file
        version_dirpath = os.path.join(
                self._unbox_dirpath,
                self._dropbox_index[resource_name][self._RSRC_INFO_KEY_PARENT_DIRNAME],
                version)
        shutil.rmtree(version_dirpath)
        del(resource_versions[version])
        self._write_index()


