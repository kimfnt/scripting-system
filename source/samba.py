# -*- coding: utf-8 -*-
"""
SMB Share Management
Connects to the SMB share in order to transfer file
Checks validity of other files stored on the share

@author: Kim-Céline FRANOT
"""
import datetime
import json

import smb.base
from smb.SMBConnection import SMBConnection


class SMBServer:
    """
    Class to manage SMB share

    Attributes:
        log: Log
        file: String
        ip: String
        hostname: String
        username: String
        password: String
        save_days: String
        sharename: String
        path: String
        samba: SMBConnection

    Methods:
        connect(): None
        disconnect(): None
        send_file(): None
        check_server(): None
        check_file(): boolean
    """

    def __init__(self, config_, logging_, file_):

        # self.port = 445
        self.log = logging_
        self.file = file_

        try:
            with open(config_, "r") as json_file:
                data = json.load(json_file)
                ip_ = data["smb"]["ip"]
                hostname_ = data["smb"]["hostname"]
                user_ = data["smb"]["user"]
                pswd_ = data["smb"]["password"]
                sharename_ = data["smb"]["sharename"]
                path_ = data["smb"]["path"]
                try:
                    save_days_ = int(data["save_days"])
                except ValueError:
                    save_days_ = 7
                    self.log.info("JSON read", "Time format not supported.")

        except json.JSONDecodeError:
            self.log.error("JSON file read")
            return
        except KeyError as err:
            self.log.error("JSON file read", err.args[0])
            return
        except EnvironmentError:
            self.log.error("JSON file read")

        # Check all entries and log infos.
        if ip_ == "" or ip_ is None:
            self.log.error(
                "JSON read", "SMB server IP must not be blank in 'config.json'."
            )

        if hostname_ == "" or hostname_ is None:
            self.log.error(
                "JSON read", "Host name must not be blank in 'config.json'."
            )

        if user_ == "" or user_ is None:
            self.log.error(
                "JSON read", "SMB server user must not be blank in 'config.json'."
            )

        if pswd_ == "" or pswd_ is None:
            self.log.error(
                "JSON read", "SMB server password must not be blank in 'config.json'."
            )

        if sharename_ == "" or sharename_ is None:
            self.log.error(
                "JSON read", "SMB shared folder name must not be blank in 'config.json'."
            )

        if path_ == "" or path_ is None:
            self.log.error(
                "JSON read", "SMB path must not be blank in 'config.json'."
            )

        if not path_.endswith('/'):
            path_ += '/'

        # Affect all values.
        self.ip = ip_
        self.hostname = hostname_
        self.username = user_
        self.password = pswd_
        self.save_days = save_days_
        self.sharename = sharename_
        self.path = path_
        self.samba = None

    def connect(self):
        """
        Method to connect to the SMB share
        :return: None
        """
        try:
            # instantiate a SMBConnection object
            self.samba = SMBConnection(self.username, self.password, '', self.hostname, '', use_ntlm_v2=True)
            # connect to the SMB share with ip address
            auth_ = self.samba.connect(self.ip)
        except smb.base.SMBTimeout:
            self.log.error("SMB Connection", "Unable to connect to SMB share")
            self.samba.close()

    def disconnect(self):
        """
        Method to close connection with SMB share
        :return: None
        """
        self.samba.close()

    def send_file(self):
        """
        Method to transfer file to the SMB share
        :return: None
        """
        if self.samba is not None:
            # send file to smb server
            file_obj = open(self.file, 'rb')
            self.samba.storeFile(self.sharename, self.path + self.file, file_obj)
            self.log.info("Send File to SMB", "File sent to the SMB Share.")

    def check_server(self):
        """
        Method to check if files stored on the SMB share are still valid.
        Deletes files if they're considered old
        :return: None
        """
        try:
            nb_delete = 0
            if self.samba is not None:
                # get the list of all elements on the smb share
                file_list = self.samba.listPath(self.sharename, self.path)

                # calculate the maximum date according to the number of days it should stay on the server
                max_date = (datetime.datetime.today() - datetime.timedelta(days=self.save_days)).date()

                # iterate each elements
                for f in file_list:
                    # if element is not a directory => therefore element is a file
                    if not f.isDirectory:
                        # get date of file with its name
                        date = datetime.datetime.strptime(f.filename.replace(".tgz", ""), "%Y%d%m").date()
                        # if file date is older than the maximum date calculated
                        if date < max_date:
                            # remove file from share and increment value of nb_delete
                            self.samba.deleteFiles(self.sharename, self.path + f.filename)
                            nb_delete += 1

                self.log.info("Server File Check",
                              str(nb_delete) + " file(s) removed from remote server.")
            else:
                self.log.error("Server File Check", "Unable to connect to the server, file check not done.")
        except Exception as err_:
            self.log.error("Server File Check", f'Error encountered: {err_}')

    def check_file(self):
        """
        Method to check if file was uploaded to the SMB share
        :return: boolean
        """
        try:
            if self.samba is not None:
                present = False
                # get the list of elements in share directory
                file_list = self.samba.listPath(self.sharename, self.path)
                # iterate over elements and compare name to the name of the file that was uploaded
                for i in range(len(file_list)):
                    if self.file == file_list[i].filename:
                        present = True
                # if file is present, log success
                if present:
                    self.log.info("File Uploaded", "Tar file exists on the remote server. Upload successful.")
                    return True
                else:
                    #otherwise log error
                    self.log.error("File Uploaded", "Tar file is not on the remote server. Upload failed.")
                    return False
            else:
                self.log.error("File Uploaded", "Unable to connect to the SMB server and check if file was uploaded.")
                return False
        except Exception as e:
            self.log.error("File Uploaded", f'Error encountered: {e}')
