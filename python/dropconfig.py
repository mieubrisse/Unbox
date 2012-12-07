#!/usr/bin/python

# Import python libraries
import sys
import os.path
import tempfile
import json
import subprocess




import time

# Import custom libraries
import dropconfig_core

if not len(sys.argv) > 1:
    print "Enter 'dropconfig help' for usage help"
    sys.exit()

# Ensure config exists
try:
    config_file = open("config.json")
except IOError:
    print("Unable to find 'config.json'")
    sys.exit()

config_file = open("config.json")
core = dropconfig_core.Core(config_file)
core.cleanLists()
if sys.argv[1] == "fresh":
    resource_link_dict = core.resource_link_dict
    core.removeLinks(resource_link_dict.keys())
    core.ignored_resources = []
    remote_resources = core.remote_resources
    
    # Get user input on where to map which resources
    json_obj = dict.fromkeys(remote_resources, " ")
    tempfile = tempfile.NamedTemporaryFile(delete=False)
    json.dump(json_obj, tempfile, indent=4, separators=(",", "\t:\t"))
    tempfile.flush()
    editor = os.environ.get("EDITOR", "vim")
    return_code = subprocess.call([editor, tempfile.name]) 
    tempfile.seek(0)
    desired_links = json.load(tempfile)
    tempfile.close()
    resources_to_ignore = [resource for resource in desired_links.keys() if resource not in remote_resources]
    core.ignored_resources.append(resources_to_ignore)
    core.forgeLinks(desired_links)
    

core.writeLists()
    # remove any existing links
    # clear the ignore list
    # gather all resources
    # display list of resources to user
    # add list of resources user did not map to ignore list

    

