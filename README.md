# Aruba-Mobility-Master-Backup
Script to backup the Aruba Mobility Master Flash to a SCP host


Create a cronjob to run every night `./MMbackup_config.py -S scp_host -U scp_user -P scp_password -H MM_host -x MM_user -y MM_password`  
It will create a backup file every night `2022-06-07_1.1.1.1_configbackup.tar.gz`, it will keep the last 30 backups.
