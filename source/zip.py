# -*- coding: utf-8 -*-
"""
Zip file management
Downloads the zip file from server, extract the sql file,
compares version, compress to tar archive

@author: Kim-Céline FRANOT
"""

import os
import tarfile
from io import BytesIO
import hashlib
import datetime
import json
import zipfile
import requests
from requests import HTTPError
from source.log import Log


class Zip:
    """
    Class to manage the zip file downloaded

    Attributes:
        config: String
        name_tgz: String
        prev_sql_file: String
        url_zip: String
        name_zip: String
        name_sql_file: String
        log: Log

    Methods:
        get_config(): None
        download_unzip(): None
        check_file_version(): boolean
        compress_targz(): None
        clean_directory(): None
    """

    def __init__(self, config_):
        # name of the config file
        self.config = config_
        # name of the tar.gz archive
        self.name_tgz = datetime.datetime.today().strftime('%Y%d%m') + ".tgz"

        # name of the previous dump file
        self.prev_sql_file = "./prev_dump.sql"
        self.url_zip = None
        self.name_zip = None
        self.name_sql_file = None
        self.log = None

    def get_config(self):
        """
        method to get information from the configuration file
        :return: None
        """
        user_zip = None
        user_dump = None

        self.log = Log()

        try:
            with open(self.config, "r") as json_file:
                data = json.load(json_file)
                user_zip = data["url-zip"]
                user_dump = data["file"]

                self.log = Log(data["notification"], data["email"], data["mattermost_webhook"])

        except json.JSONDecodeError:
            self.log.error("JSON file read")
            return
        except KeyError as err:
            self.log.error("JSON file read", err.args[0])
            return
        except EnvironmentError:
            self.log.error("JSON file read")

        # check entries format
        if user_zip == "" or user_zip is None:
            self.log.error("JSON file read")

        if user_dump == "" or user_dump is None:
            self.log.error("JSON file read")

        # add extension if none
        if user_zip is not None and user_zip.find(".zip") == -1:
            user_zip = user_zip + ".zip"
        if user_dump is not None and user_dump.find(".sql") == -1:
            user_dump = user_dump + ".sql"

        # affect values
        self.url_zip = user_zip
        self.name_zip = user_zip.split("/")[-1]
        self.name_sql_file = user_dump

    def download_unzip(self):
        """
        method to download the zip file from url if the sql dump is in it
        :return: None
        """
        try:
            url = self.url_zip
            req = requests.get(url)
            zfile = zipfile.ZipFile(BytesIO(req.content))
            req.raise_for_status()

            # check if zip contains dump
            if self.name_sql_file in zfile.namelist():
                self.log.info("SQL File in Zip", "Zip file contains dump file.")
                # proceed with extraction
                try:
                    zfile.extract(self.name_sql_file, os.getcwd())
                    self.log.info("SQL File Downloaded", "Zip file extraction successful")
                except zipfile.BadZipfile:
                    self.log.error("SQL File Downloaded", "Bad zip file: extraction interrupted.")
                finally:
                    zfile.close()
            else:
                self.log.error("SQL File in Zip"
                               , "Zip file does not contain dump file: extraction not done")

        except HTTPError as http_err:
            self.log.error("Request ZIP", f'HTTP error encountered: {http_err}')
        except Exception as err:
            self.log.error("Request ZIP", f'Error encountered: {err}')

    def check_file_version(self):
        """
        method to compare if sql file is different from the previous one
        :return: boolean
        """
        # if there's a previous file in the directory
        if os.path.isfile(self.prev_sql_file):
            sha1_prev = hashlib.sha1()
            sha1_current = hashlib.sha1()

            with open(self.prev_sql_file, "rb") as prev_file:
                while True:
                    prev_data = prev_file.read(65536)
                    if not prev_data:
                        break
                    sha1_prev.update(prev_data)

            with open(self.name_sql_file, "rb") as file_to_check:
                while True:
                    data = file_to_check.read(65536)
                    if not data:
                        break
                    sha1_current.update(data)

            # compare hash with the one of the last file on distant server
            if sha1_prev.hexdigest() == sha1_current.hexdigest():
                # same file -> we do not compress it
                self.log.warning("SQL File Comparison", "The actual file is the same as the previous version.")
                self.log.warning("Compress File into TAR", "Compression not done (same version).")

                # delete the dump file that was downloaded
                if os.path.exists(os.getcwd() + "/" + self.name_sql_file):
                    os.remove(os.getcwd() + "/" + self.name_sql_file)
                return False

            else:
                # file is different
                self.log.info("SQL File Comparison"
                              , "The actual file is different from the previous version.")
                return True

        else:
            # there is no file to compare
            self.log.info("SQL File Comparison", "There is no previous file to compare.")
            return True

    def compress_targz(self):
        """
        method to compress the sql file into tar archive
        :return: None
        """
        try:
            # open a tar file and add the sql file in it
            with tarfile.open(self.name_tgz, "w:gz") as tar:
                tar.add(self.name_sql_file, arcname=self.name_sql_file)
                self.log.info("Compress File into TAR", "Compression into archive successful.")

        except tarfile.CompressionError:
            self.log.error("Compress File into TAR", "Error while compressing SQL dump.")
        except FileNotFoundError:
            self.log.error("Compress File into TAR", "Couldn't find the SQL dump.")
        except tarfile.ReadError:
            self.log.error("Compress File into TAR", "Error while reading SQL dump.")
        except tarfile.TarError as error:
            self.log.error("Compress File into TAR", "Error while compressing file: " + str(error))
        except Exception as err_:
            self.log.error("Compress File into TAR", "Error while compressing SQL dump: " + str(err_))

        # delete prev dump (if exists)
        if os.path.isfile(self.prev_sql_file):
            os.remove(os.getcwd() + "/" + self.prev_sql_file)

        # rename actual dump file
        if os.path.isfile(self.name_sql_file):
            os.rename(os.getcwd() + "/" + self.name_sql_file, os.getcwd() + "/" + self.prev_sql_file)


    def clean_directory(self):
        """
        Method to delete files once the service is done
        :return: None
        """

        # remove tar file from working directory
        if os.path.exists(os.getcwd() + "/" + self.name_tgz):
            os.remove(os.getcwd() + "/" + self.name_tgz)
