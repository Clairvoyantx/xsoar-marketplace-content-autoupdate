# Author: Steven Yang, Latest Version Demisto tested: 6.0 beta 76251
import requests
import json
import sys
import re
requests.packages.urllib3.disable_warnings()

SERVER_URL = "SERVERURL"
API_KEY = "APIKEY"

headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': API_KEY
}

# Global var for storing info of all installed packages
PACKAGE_LIST = []


def major_minor_micro(version):
    '''
    Max function key method
    '''
    major, minor, micro = re.search('(\d+)\.(\d+)\.(\d+)', version).groups()
    return int(major), int(minor), int(micro)


def packages_to_update():
    '''
    Returns a list of packages that needs to be updated on the Marketplace
    '''
    global PACKAGE_LIST
    response = requests.get(f'{SERVER_URL}/contentpacks/installed-expired', headers=headers,verify=False)
    res = json.loads(response.content)
    # Store packages in global var
    PACKAGE_LIST = res
    # Get list of packages to update, checking the updateAvailable field == True
    packages_to_update = [i for i in res if i['updateAvailable']]
    return packages_to_update


def checkDependencies(dep):
    '''
    Returns True if all depenencies exist and version is > min version, False otherwise
    '''
    for depname,values in dep.items():
        # Min Version needed: ver
        ver = values['minVersion']
        for pack in PACKAGE_LIST:
            if depname == pack['id']:
                # Name of dependency: depname
                # Currently installed version: pack['currentVersion'])
                # IS Current version newest?
                if pack['currentVersion'] != max([pack['currentVersion'],ver], key=major_minor_micro):
                    return False
    return True


def update_package(single_item):
    '''
    Updates a single package on the marketplace
    Added dependency management, do not update if dependency is not installed
    '''
    change_log_keys = list(single_item['changelog'].keys())
    # Grab the latest version
    latest_ver = max(change_log_keys, key=major_minor_micro)
    # Grab Name of package
    id_item = single_item['id']
    # Grab dependencies of package
    dependencies = single_item['dependencies']
    # True for good to update, False for dependency missing
    boolres = checkDependencies(dependencies)
    if not boolres:
        print(f"Dependency missing from {id_item}, skipping.. Please update {id_item} manually")
        return boolres
    data = {
        "packs":[{
            "id":id_item,
            "version":latest_ver,
            "transition":None,
            "skipInstall":False
            }],
        "ignoreWarnings":False,
        "transitionPrice":0
    }
    response = requests.post(f'{SERVER_URL}/contentpacks/marketplace/install', data=json.dumps(data), headers=headers, verify=False)
    if response.status_code == 200:
        print(f"Upgraded {id_item} to {latest_ver}")
    return boolres

# Get the packages to update
packs_to_update = packages_to_update()
if packs_to_update == []:
    print("Nothing to update")
else:
    # Loop for updating all packages
    for i in packs_to_update:
        update_package(i)

print("Done with Content Update")