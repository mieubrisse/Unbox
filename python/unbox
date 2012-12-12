#!/usr/bin/python

# Import python libraries
import sys
import os.path
import tempfile
import json
import subprocess
import time
import optparse

# Import custom libraries
import unbox_core



""" ======== MAIN ======== """

# Ensure config exists
try:
    config_file = open("config.json")
except IOError:
    print("Unable to find 'config.json'")
    sys.exit()

# Load state of application
config_file = open("config.json")
core = unbox_core.Core(config_file)
core.clean_lists()

# Parse user arguments
#parser = OptionParser()
#parser.add_option("-f", "--fresh", help="configure Unbox from scratch"
command_arg = sys.argv[1]


# Perform fresh install
if command_arg == "fresh":
    
    resource_link_dict = core.resource_link_dict
    core.remove_links(resource_link_dict.keys())
    core.ignored_resources = []
    remote_resources = core.remote_resources
    
    # Write out resources in Dropbox folder in temp file
    json_obj = dict.fromkeys(remote_resources, " ")
    tempfile = tempfile.NamedTemporaryFile(delete=False)
    json.dump(json_obj, tempfile, indent=4, separators=(",", "\t:\t"))
    tempfile.flush()

    # Open editor to let user set what should be installed
    editor = os.environ.get("EDITOR", "vim")
    return_code = subprocess.call([editor, tempfile.name]) 
    tempfile.seek(0)
    desired_links = json.load(tempfile)
    tempfile.close()

    # Process user's decisions
    resources_to_ignore = [resource for resource in desired_links.keys() if resource not in remote_resources]
    core.ignored_resources.append(resources_to_ignore)
    core.forge_links(desired_links)
# Print help
elif command_arg == "help":
    printHelp()
else:
    usage()

    

core.write_lists()
    # remove any existing links
    # clear the ignore list
    # gather all resources
    # display list of resources to user
    # add list of resources user did not map to ignore list

    

