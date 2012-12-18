import os
import shutil
import json
import uuid
import dropbox_module
import local_module

"""
Gets the user-expanded, normalized, absolute path to a file object
- path: path to find absolute path for
- RETURN: absolute path to object
"""
def abs_path(path):
    # Ensure validity
    if path == None or len(path.strip()) == 0:
        raise ValueError("Cannot find absolute path; string is empty")
    return os.path.abspath(os.path.expanduser(os.path.normpath(path)))

"""
Class to manage all resources in the Unbox filesystem
"""
class Filesystem:
    # Module to manage the Dropbox Unbox directory
    _dropbox_module = None

    # Module to manage the local Unbox directory
    _local_module = None




    """
    Instantiates a Filesystem object to handle Unbox's file operations
    - RETURNS: 
    """
    def __init__(self, local_unbox_dirpath, dropbox_dirpath, dropbox_unbox_dirname):
        self._dropbox_module = dropbox_module.DropboxModule(dropbox_dirpath, unbox_dirname)
        self._local_module = local_module.LocalModule(local_unbox_dirpath)










        

