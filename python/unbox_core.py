# Import python libraries
import json
import sys
import os
import shutil

"""
Main processing engine for the script
"""
class Core:

    """ ====== Constants ======== """
    # Names of files detailing reosurce link behaviors
    LINK_FILENAME = ".unbox_link"
    IGNORED_FILENAME = ".unbox_ignore"

    # Suffix attached to backup files
    BACKUP_SUFFIX = ".unbox_bak"

    


    """ ====== Variables ======== """
    # Path to config files in Dropbox
    remote_resource_dir_path = ""

    # Dropconfig file on local machine
    unbox_dir_path = ""
    
    # List of remote resource paths
    remote_resources = None

    # Information about items in Dropbox

    dropbox_info

    # Mapping of installed resources (resource path : {)
    resource_link_dict = None
    
    # List of ignored resource paths
    ignored_resources = None

    # Mapping of 
    terminal_text_color_codes = None
    




    """ ====== Functions ======== """
    """
    Constructor method
     - config_fp: filepointer to the Unbox config file
     - script_args: arguments passed to the script
    """
    def __init__(self, config_fp):
        config_obj = json.load(config_fp)

        # Ensure valid resource directory was specified
        self.remote_resource_dir_path = os.path.expanduser(os.path.normpath(config_obj["resources directory"]))

        # Ensure valid unbox directory was specified
        self.unbox_dir_path = os.path.expanduser(os.path.normpath(config_obj["unbox directory"]))
        if not os.path.exists(self.unbox_dir_path):
            os.makedirs(self.unbox_dir_path)
        if os.path.exists(self.unbox_dir_path) and not os.path.isdir(self.unbox_dir_path):
            raise Exception(self.unbox_dir_path + " exists but isn't a directory")

        # Load rules from files detailing what links should be made
        resource_link_dict_filepath = os.path.join(self.unbox_dir_path, self.LINK_FILENAME)
        if os.path.exists(resource_link_dict_filepath):
            resource_link_dict_file = open(resource_link_dict_filepath, 'r+')
            self.resource_link_dict = json.load(resource_link_dict_file)
            resource_link_dict_file.close()
        else:
            self.resource_link_dict = dict()
        
        # Load which resources should be ignored
        ignored_resources_filepath = os.path.join(self.unbox_dir_path, self.IGNORED_FILENAME)
        if os.path.exists(ignored_resources_filepath):
            ignored_resources_file = open(ignored_resources_filepath, 'r+')
            self.ignored_resources = json.load(ignored_resources_file)
            ignored_resources_file.close()
        else:
            self.ignored_resources = dict()

        # Gather resources
        self.remote_resources = []
        for dirpath, dirnames, filenames in os.walk(self.remote_resource_dir_path):
            for filename in filenames:
                self.remote_resources.append(os.path.join(dirpath, filename))

        self.terminal_text_color_codes = config_obj["terminal text color codes"]


    """
    If possible, creates the desired links
     - links_to_create: mapping of (resource path : link path) that user wants to create
    """
    def forge_links(self, links_to_create):
        for resource_path in links_to_create.keys():
            resource_path = resource_path.strip()

            # Check resource path validity
            if len(resource_path.strip()) == 0:
                print "-- Skipping empty resource path"
                continue
            full_resource_path = os.path.expanduser(os.path.normpath(resource_path))
            if not os.path.exists(full_resource_path):
                print "!! No resource at path " + resource_path + " exists"
                continue

            # Check link path validity
            link_path = links_to_create[full_resource_path].strip()
            full_link_path = os.path.expanduser(os.path.normpath(link_path))
            if len(link_path.strip()) == 0:
                print "-- Skipping empty link path"
                continue

            # If a link exists at the link path, remove it
            if os.path.islink(full_link_path):
                os.remove(full_link_path)

            # If a file exists at the link path, back it up
            if os.path.exists(full_link_path):
                print "-- " + full_link_path + " already exists; appending " + self.BACKUP_SUFFIX
                os.rename(full_link_path, full_link_path + self.BACKUP_SUFFIX)
            os.symlink(full_resource_path, full_link_path)
            print "++ Link from " + link_path + " to " + full_resource_path + " created successfully!"
            self.resource_link_dict[full_resource_path] = link_path


    """
    Cleans the in-memory lists to remove references to resources that no longer exist
    """
    def clean_lists(self):
        # Remove dead resources and restore from backup if possible
        dead_link_resources = [resource for resource in self.resource_link_dict.keys() if resource not in self.remote_resources]
        self.remove_links(dead_link_resources)

        dead_ignored_resources = [resource for resource in self.ignored_resources if resource not in self.remote_resources]
        self.ignored_resources = list(set(self.ignored_resources) - set(dead_ignored_resources))
        # for dead_ignored_resource in dead_ignored_resources:
        #     self.ignored_resources.remove(dead_ignored_resource)

    """
    Removes links for the given resources and attempts to restore the backup saved when the link was created
     - resources: list of paths to resources to remove
    """
    def remove_links(self, resources):
        for resource_to_remove in resources:
            link_path = self.resource_link_dict[resource_to_remove]
            if not os.path.exists(link_path):
                continue
            print "Removing dead link " + link_path + " pointing to nonexistent resource " + resource_to_remove
            backup_path = link_path + self.BACKUP_SUFFIX
            if os.path.exists(backup_path):
                try:
                    shutil.copyfile(backup_path, link_path)
                    os.remove(backup_path)
                    print "-- Found and successfully restored backup"
                except IOError:
                    print "!! Found backup at " + backup_path + " but could not restore"
            else:
                try:
                    os.remove(link_path)
                    print "-- No backup found; link successfully removed"
                except IOError:
                    print "!! No backup found; could not remove link"
                
            del self.resource_link_dict[resource_to_remove]



    """
    Helper function to write the in-memory lists to file
    """
    def write_lists(self):

        # Write list of resources
        resource_link_dict_filepath = os.path.join(self.unbox_dir_path, self.LINK_FILENAME)
        resource_link_dict_file = open(resource_link_dict_filepath, 'w')
        json.dump(self.resource_link_dict, resource_link_dict_file)
        resource_link_dict_file.close()

        ignored_resources_filepath = os.path.join(self.unbox_dir_path, self.IGNORED_FILENAME)
        ignored_resources_file = open (ignored_resources_filepath, 'w')
        json.dump(self.ignored_resources, ignored_resources_file)
        ignored_resources_file.close()

        
