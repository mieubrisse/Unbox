import os
import shutil
import json
import uuid
import unbox_filesystem

"""
Module for the Unbox filesystem to handle Dropbox-related commands
"""
class DropboxModule:

    # Constants
    _INDEX_FILENAME = "index.json"
    _RSRC_INFO_KEY_PARENT_DIRNAME = "parent_dirname"
    _RSRC_INFO_KEY_VERSIONS_INFO = "versions_info"
    _RSRC_INFO_KEY_CURRENT_VERSION = "current_version"
    _VERSION_INFO_KEY_DEPENDENCIES = "dependencies"
    _CURRENT_RSRC_VERSION_LINKNAME = "current"



    """
    Instantiates a new Dropbox filesystem module at the given location
    - dropbox_dirpath: path to the user's Dropbox directory
    - unbox_dirname: name of Unbox directory in Dropbox folder
    """
    def __init__(self, dropbox_dirpath, unbox_dirname):
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
            self._dropbox_index = json.load(dropbox_index_fp)
            dropbox_index_fp.close()
        else:
            self._dropbox_index = dict()
        # _dropbox_index maps resource names in Dropbox -> info dict{
        #   versions_info : version name -> info dict{
        #       dependencies : list of dependencies version needs[]
        #   current_version : version that will be used by default
        #   directory : name of directory where resource is stored




    """ ======= Helper Methods ======= """
    """
    Writes the in-memory Dropbox index to the Dropbox index file
    """
    def _write_index(self):
        INDEX_FILEPATH = os.path.join(self._unbox_dirpath, self._INDEX_FILENAME)
        dropbox_index_fp = open(INDEX_FILEPATH, "w")
        json.dump(self._dropbox_index, dropbox_index_fp, indent=4)
        dropbox_index_fp.close()

    """
    Checks if a resource is in the Dropbox Unbox system
    - resource: name of resource to check for
    - RETURN: true if the resource exists, false otherwise
    """
    def resource_exists(self, resource):
        return resource in self._dropbox_index

    """
    Sanity check function to ensure a version exists for a resource
    - resource: resource to check for version
    - version: version to check for
    - RETURN: true if the version exists, false otherwise
    """
    def resource_version_exists(self, resource_name, version):
        # Ensure validity
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot check if resource version exists; cannot find resource")
        resource_info = self._dropbox_index[resource_name]
        resource_versions_info = resource_info[self._RSRC_INFO_KEY_VERSIONS_INFO]
        return version in resource_versions_info




    """ ======= Resource Methods ======= """
    """
    Gets resources stored in Dropbox
    - RETURN: set of names of resources in Dropbox
    """
    def resource_set(self):
        return self._dropbox_index.keys()

    """
    Gets the dictionary entry for the given resource
    - resource_name: name of resource in Dropbox
    - RETURN: tuple of (resource dirname, current version number, set of version names)
    NOTE: To get version info, use resource_version_info
    """
    def resource_info(self, resource_name):
        # Sanity check
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot get resource info; resource does not exist")

        resource_info = self._dropbox_index[resource_name]
        return (
                resource_info[self._RSRC_INFO_KEY_PARENT_DIRNAME],
                resource_info[self._RSRC_INFO_KEY_CURRENT_VERSION], 
                resource_info[self._RSRC_INFO_KEY_VERSIONS_INFO].keys()
            )

    """
    Gets the absolute path to a resource in the Dropbox Unbox system
    - resource: name of resource
    """
    def resource_path(self, resource):
        # Check validity
        if not self.resource_exists(resource):
            raise ValueError("Could not get path to resource in Dropbox; resource does not exist")

        # Find resource and get absolute path
        resource_info = self._dropbox_index[resource]
        resource_parent_dirname = resource_info[self._RSRC_INFO_KEY_PARENT_DIRNAME]
        current_version = resource_info[self._RSRC_INFO_KEY_CURRENT_VERSION]

        resource_path = os.path.join(self._unbox_dirpath, resource_parent_dirname, current_version, resource)
        return resource_path

    """
    Adds the given resource to the Dropbox system
    - path: path to resource to add
    - RETURN: true if the resource exists, false otherwise
    """
    def add_resource(self, local_path, version="1.0", dependencies=None):
        if dependencies == None:
            dependencies = list()

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
        veresion = version.strip()

        # Creates directory structure to place resource in
        upstream, resource_filename = os.path.split(local_path)
        parent_dirname = str(uuid.uuid4())
        parent_dirpath = os.path.join(self._unbox_dirpath, parent_dirname)
        os.mkdir(parent_dirpath)
        version_dirpath = os.path.join(parent_dirpath, str(version))
        os.mkdir(version_dirpath)

        # Creates symlink to current version
        current_version_linkpath = os.path.join(parent_dirpath, self._CURRENT_RSRC_VERSION_LINKNAME) 
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

#       THIS MIGHT COME IN HANDY LATER
# 
#         shutil.move(path, dest_dirpath)
# 
#         # Creates a link at the local path to the Dropbox resource
#         resource_filepath = os.path.join(dest_dirpath, resource_filename)
#         os.symlink(resource_filepath, path)
# 
# 
#         # Register the addition in the local index
#         unboxed_resource_info = {
#             self._UNBXD_RSRC_INFO_KEY_LINKPATH : path,
#             self._UNBXD_RSRC_INFO_KEY_LINKTARGET : resource_filepath,
#             self._UNBXD_RSRC_INFO_KEY_VERSION : version
#         }
#         unboxed_resources_dict = self._local_index[self._UNBOXED_RESOURCES_DICT_KEY]
#         unboxed_resources_dict[resource_filename] = unboxed_resource_info
#         self._write_local_index()

    """
    Deletes a resource and all its versions from the Dropbox Unbox filesystem
    - resource: name of resource to delete
    """
    def delete_resource(self, resource_name):
        # Sanity check
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot delete resource; cannot find resource")

        # Perform delete and write to file
        resource_dirname = self._dropbox_index[resource_name][self._RSRC_INFO_KEY_PARENT_DIRNAME]
        resource_dirpath = os.path.join(self._unbox_dirpath, resource_dirname)
        del(self._dropbox_index[resource_name])
        shutil.rmtree(resource_dirpath)
        self._write_index



    """ ======= Version Methods ======= """
    """
    Gets information about a resource version
    - resource_name: name of resource to get info about
    - version: version to get info about
    - RETURN: version dependencies
    """
    def resource_version_info(self, resource_name, version):
        # Sanity check
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot get resource version info; cannot find resource")
        if not self.resource_version_exists(resource_name, version):
            raise ValueError("Cannot get resource version info; cannot find version")

        # Extract version info
        resource_info = self._dropbox_index[resource_name]
        versions_info = resource_info[self._RSRC_INFO_KEY_VERSIONS_INFO]
        version_info = versions_info[version]
        return version_info[self._VERSION_INFO_KEY_DEPENDENCIES]

    """
    Copies the given resource file ONLY into a new version
    - resource_name: name of resource to create version for
    - new_version: name of new version
    - source_version: version to copy resource from; defaults to current version
    - move_current: whether to move the 'current' pointer to the newly-created version
    """
    def copy_version(self, resource_name, source_version, new_version, copy_dependencies=True):
        # Sanity checks
        if new_version == None or len(new_version.strip() == 0):
            raise ValueError("Cannot add resource version; cannot add empty version name")
        new_version = new_version.strip()
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot add resource version; cannot find resource")
        if not self.resource_version_exists(resource_name, source_version):
            raise ValueError("Cannot add resource version; cannot find source version")

        # Create files for new version
        resource_info = self._dropbox_index[resource_name]
        resource_dirname = resource_info[self._RSRC_INFO_KEY_PARENT_DIRNAME]
        new_version_filepath = os.path.join(self._unbox_dirpath, new_version, resource_name)
        os.mkdir(new_version_dirpath)
        if source_version == self._CURRENT_RSRC_VERSION_LINKNAME:
            source_version_filepath = os.path.join(self._unbox_dirpath, resource_dirname, self._CURRENT_RSRC_VERSION_LINKNAME)
        else:
            source_version_filepath = os.path.join(self._unbox_dirpath, resource_dirname, source_version, resource_name)
        shutil.copytree(source_version_filepath, new_version_filepath)

        # Update in-memory copy
        resource_versions_info = resource_info[self._RSRC_INFO_KEY_VERSIONS_INFO]
        source_version_info = resource_versions_info[source_version]
        new_version_info = dict()
        if copy_dependencies == True:
            new_version_info[self._VERSION_INFO_KEY_DEPENDENCIES] = list(source_version_info[self._VERSION_INFO_KEY_DEPENDENCIES])
        else:
            new_version_info[self._VERSION_INFO_KEY_DEPENDENCIES] = list()
        resource_versions_info[new_version] = new_version_info

        self._write_index()

    """
    Adds the given dependency to the given resource version
    - resource_name: name of resource to modify version for
    - version_name: name of version to add dependency to
    - dependency: dependency to add
    """
    def add_version_dependency(self, resource_name, version_name, dependency_name):
        # Sanity check
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot add version dependency; cannot find resource")
        if not self.resource_version_exists(resource_name, version_name):
            raise ValueError("Cannot add version dependency; cannot find resource version")
        if dependency_name == None or len(dependency_name.strip()) == 0:
            raise ValueError("Cannot add version dependency; dependency name must be non-empty string")

        # Add version dependency to in-memory list and write to file
        versions_info = self._dropbox_index[resource_name][self._RSRC_INFO_KEY_VERSIONS_INFO]
        version_dependencies = versions_info[version_name][self._VERSION_INFO_KEY_DEPENDENCIES]
        if dependency_name not in version_dependencies:
            version_dependencies.append(dependency_name)
            self._write_index()

    """
    Deletes the given dependency for the given resource version
    - resource_name: name of resource to modify version for
    - version_name: name of version to delete dependency from
    - dependency: dependency to delete
    - RETURN: true if the dependency existed, false otherwise
    """
    def delete_version_dependency(self, resource_name, version_name, dependency_name):
        # Sanity check
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot add version dependency; cannot find resource")
        if not self.resource_version_exists(resource_name, version_name):
            raise ValueError("Cannot add version dependency; cannot find resource version")
        if dependency_name == None or len(dependency_name.strip()) == 0:
            raise ValueError("Cannot add version dependency; dependency name must be non-empty string")

        # Add version dependency to in-memory list and write to file
        versions_info = self._dropbox_index[resource_name][self._RSRC_INFO_KEY_VERSIONS_INFO]
        version_dependencies = set(versions_info[version_name][self._VERSION_INFO_KEY_DEPENDENCIES])
        if dependency_name in version_dependencies:
            version_dependencies.remove(dependency_name)
            self._write_index()
            return True
        return False

    """
    Changes the current version of a Dropbox resource
    - resource_name: name of resource to change version for
    - version: version to point resource to
    """
    def change_current_version(self, resource_name, version):
        # Sanity check
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot change resource version; cannot find resource")
        if not self.resource_version_exists(resource_name, version):
            raise ValueError("Cannot change resource version; cannot find version")

        # Perform version change and write changes to file
        resource_dirpath = os.path.join(self._unbox_dirpath, self._dropbox_index[self._RSRC_INFO_KEY_PARENT_DIRNAME])
        current_rsrc_version_linkpath = os.path.join(
                resource_dirpath,
                self._CURRENT_RSRC_VERSION_LINKNAME)
        target_rsrc_version_filepath = os.path.join(
                resource_dirpath,
                version,
                resource_name)
        os.unlink(current_rsrc_version_linkpath)
        os.symlink(target_rsrc_version_filepath, current_rsrc_version_linkpath)
        self._dropbox_index[resource_name][self._RSRC_INFO_KEY_CURRENT_VERSION] = version
        self._write_index()

    """
    Deletes the given version of a Dropbox resource
    - resource_name: name of resource to change version for
    - version: version to point resource to
    """
    def delete_resource_version(self, resource_name, version):
        # Sanity check
        if not self.resource_exists(resource_name):
            raise ValueError("Cannot delete resource version; cannot find resource")
        if not self.resource_version_exists(resource_name, version):
            raise ValueError("Cannot delete resource version; cannot find version")
        resource_info = self._dropbox_index[resource_name]
        resource_versions = resource_info[self._RSRC_INFO_KEY_VERSIONS_INFO]
        if version == resource_info[self._RSRC_INFO_KEY_CURRENT_VERSION]:
            raise ValueError("Cannot delete resource version; version is current version -- delete version first")
        if len(resource_versions) <= 1:
            raise ValueError("Cannot delete resource version; no other versions exist")

        # Delete data associated with version and write changes to file
        version_dirpath = os.path.join(
                self._unbox_dirpath,
                self._dropbox_index[self._RSRC_INFO_KEY_PARENT_DIRNAME],
                version)
        shutil.rmtree(version_dirpath)
        del(resource_versions[version])
        self._write_index()


