#!/usr/bin/python3.6
# Author: Kaan Arslan kaan(dot)arslan(at)deltics(dot)nl
# Date: 07 Jun 2022
# Description: Script to backup MM Config.
# Dependencies: requests, datetime
#
# License: This nagios plugin comes with ABSOLUTELY NO WARRANTY. You may redistribute copies of
# the plugins under the terms of the GNU General Public License. For more information about these
# matters, see the GNU General Public License.

import requests, argparse, sys, os
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from datetime import date
import datetime

today = date.today()
maxdate = today - datetime.timedelta(days=30)


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
parser = argparse.ArgumentParser(description='Script to backup MM Config')
parser.add_argument('-U', help='SCP User', required=True)
parser.add_argument('-P', help='SCP Password', required=True)
parser.add_argument('-S', help='SCP Address', required=True)
parser.add_argument('-H', help='Hostaddress', required=True)
parser.add_argument('-x', help='MM Username', required=True)
parser.add_argument('-y', help='MM Password', required=True)
args = parser.parse_args()
#
scp_host = args.S
scp_user = args.U
scp_pass = args.P
aosip = args.H
username = args.x
password = args.y

# Handle logout
def logout(uidaruba, aosip, aoscookie):
    url_logout = "https://" + aosip + ":4343/v1/api/logout"
    headers = {'uidaruba': uidaruba}
    r = query.get(url_logout, cookies=aoscookie, headers=headers, verify=False)
    return r.status_code

# Create backup file
def make_backup(aosip, uidaruba):

    url_create_backup = "https://" + aosip + ":4343/v1/configuration/object/flash_backup?config_path=%2Fmd&UIDARUBA=" + uidaruba
    aoscookie = dict(SESSION = uidaruba)

    try:
        payload = {"backup_flash": "flash", "filename": "configbackup" }
        r = requests.post(url_create_backup, cookies=aoscookie, verify=False, json=payload)
        # showdata = json.loads(r.text)['mac_table_entry_element']
        if r.status_code != 200:
            #print(vars(r))
            print('Status:', r.status_code, 'Headers:', r.headers,
                  'Error Response:', r.reason)

        return r.json(), aoscookie
    except requests.exceptions.RequestException as error:
        #print("Error")
        return "Error:\n" + str(error) + " get_showcommand: An Error has occured"


def copy_backup(aosip, uidaruba, payload):

    url_copy_backup = "https://" + aosip + ":4343/v1/configuration/object/copy_flash_scp?config_path=%2Fmd&UIDARUBA=" + uidaruba
    aoscookie = dict(SESSION = uidaruba)

    try:
        r = requests.post(url_copy_backup, cookies=aoscookie, verify=False, json=payload)

        if r.status_code != 200:
            #print(vars(r))
            print('Status:', r.status_code, 'Headers:', r.headers,
                  'Error Response:', r.reason)

        return r.json()
    except requests.exceptions.RequestException as error:
        #print("Error")
        return "Error:\n" + str(error) + " get_showcommand: An Error has occured"



with requests.Session() as query:
    url_login = "https://" + aosip + ":4343/v1/api/login"
    version = "v1"
    payload_login = 'username=' + username + '&password=' + password
    headers = {'Content-Type': 'application/json'}
    get_uidaruba = query.post(url_login, data=payload_login, headers=headers, verify=False)
    if get_uidaruba.status_code != 200:
        #print(vars(get_uidaruba))
        print('Status:', get_uidaruba.status_code, 'Headers:', get_uidaruba.headers,
              'Error Response:', get_uidaruba.reason)
        exit(2)
    uidaruba = get_uidaruba.json()["_global_result"]['UIDARUBA']
    status = []
    critical = []
    output = make_backup(aosip, uidaruba)
    filename = output[0]['flash_backup']['filename']
    status = output[0]['_global_result']['status_str']

    if status == "Success":
        date = today.strftime("%Y-%m-%d")
        payload = {"srcfilename": f"{filename}.tar.gz", "scphost": scp_host, "username": scp_user,
                   "destfilename": f"Mobility/{date}_{aosip}_{filename}.tar.gz", "passwd": scp_pass}
        # Copy generated backup to scp_host
        output = copy_backup(aosip, uidaruba, payload)
        status = output['_global_result']['status_str']
        if "File uploaded successfully" in status:
            print("Backup completed successfully")
            try:
                max_file = f"/home/backup/Mobility/{maxdate.strftime('%Y-%m-%d')}_{aosip}_{filename}.tar.gz"
                os.remove(max_file)
                print("Successfully removed oldest backup")
            except:
                print("Cannot remove oldest backup. File does not exist")
                pass
        else:
            print(f"Backup scp copy failed. Error: {status}")
    else:
        print(f"Backup creation failed. Error: {status}")


