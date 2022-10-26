# -*- coding: utf-8 -*-
"""
Main

@author: Kim-Céline FRANOT
"""

import os
from source.zip import Zip
from source.samba import SMBServer


def main():
    """
    Main to launch program
    :return: None
    """
    script = Zip(os.getcwd() + "/config_file.json")

    script.get_config()

    script.download_unzip()

    smb = SMBServer("config_file.json", script.log, script.name_tgz)

    # if the sql file is new, we proceed with compression and
    # transfer to the SMB share
    if script.check_file_version():
        script.compress_targz()

        try:
            smb.connect()
            smb.send_file()
            smb.check_file()
            smb.check_server()
            smb.disconnect()
        except TimeoutError as err_:
            script.log.error("SMB Server Error", f'Error encountered: {err_}')
    else:
        # otherwise we just check the server for files to delete
        try:
            smb.connect()
            smb.check_server()
            smb.disconnect()
        except TimeoutError as err_:
            script.log.error("SMB Server Error", f'Error encountered: {err_}')

    script.log.send_notification_email()
    script.clean_directory()


if __name__ == "__main__":
    main()
