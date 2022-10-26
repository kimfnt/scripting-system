# -*- coding: utf-8 -*-
"""
Log management:
Adds logging to file everytime a task is realised
Logs can be of three levels: INFO, WARNING, ERROR
Adds information to the content fro email and notification if needed
Sends email and/or notification

@author: Kim-Céline FRANOT
"""

import logging
import os
from source.mattermost import Mattermost
from source.e_mail import Email


class Log:
    """
    Class to manage logging

    Attributes:
        nb_error: int
        nb_warning: int
        mattermost: Mattermost
        send_notification: string
        email: Email
        send_emails: string

    Methods:
        info(string, string): None
        error(string, string): None
        warning(string, string): None
        get_file(): string
        send_notification_email(): None
    """

    def __init__(self, notification_=None, emails_=None, webhook_=None):
        self.nb_error = 0
        self.nb_warning = 0
        logging.basicConfig(
            filename="./logfile.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%d/%m/%Y %I:%M:%S %p",
        )
        self.mattermost = None
        self.email = None

        # delete initial content of file
        with open('logfile.log', 'w'):
            pass

        # instantiate Mattermost object
        if notification_ is not None:
            self.send_notification = notification_
            self.mattermost = Mattermost(self, webhook_)
            if notification_ not in ("always", "error", "never"):
                self.send_notification = "always"
                self.warning("Config File", "Notification value not supported. Default value 'always' applied")

        # instantiate Email Object
        if emails_ is not None:
            self.send_emails = emails_["send-mail"].lower()
            self.email = Email(emails_, self)

            if self.send_emails not in ("yes", "y", "no", "n"):
                self.send_emails = "yes"
                self.warning("Config File", "Email value not supported. Default value 'yes' applied")

    def info(self, action_name, message=None):
        """
        Add info message to log file, notification and email body
        :param action_name: string
        :param message: string
        :return: None
        """
        if message is not None:
            logging.info("%s: %s", action_name, message)
        else:
            logging.info('Task: "%s" went smoothly.', action_name)

        # add content to mattermost notification is needed
        if self.mattermost is not None:
            self.mattermost.set_info(action_name)

        # add content to email body is needed
        if self.email is not None:
            if message is not None:
                self.email.add_content("INFO", action_name + ": " + message)
            else:
                self.email.add_content("INFO", action_name + ": task successful")

    def error(self, action_name, message=None):
        """
        Add error message to log file, notification and email body
        :param action_name: string
        :param message: string
        :return: None
        """
        self.nb_error += 1
        if message is not None:
            logging.error("%s: %s", action_name, message)
        else:
            logging.error('Task: "%s" failed.', action_name)

        # add content to mattermost notification is needed
        if self.mattermost is not None:
            self.mattermost.set_error(action_name)

        # add content to email body is needed
        if self.email is not None:
            if message is not None:
                self.email.add_content("ERROR", action_name + ": " + message)
            else:
                self.email.add_content("ERROR", action_name + ": task failed")

    def warning(self, action_name, message=None):
        """
        Add warning message to log file, notification and email body
        :param action_name: string
        :param message: string
        :return: None
        """
        self.nb_warning += 1
        if message is not None:
            logging.warning("%s: %s", action_name, message)
        else:
            logging.warning('Task: "%s" raised a warning.', action_name)

        # add content to mattermost notification is needed
        if self.mattermost is not None:
            self.mattermost.set_warning(action_name)

        # add content to email body is needed
        if self.email is not None:
            if message is not None:
                self.email.add_content("WARNING", action_name + ": " + message)
            else:
                self.email.add_content("WARNING", action_name + ": task raised a warning")

    def get_file(self):
        """
        method that returns the path to the log file
        :return: string
        """
        return str(os.path.abspath("logfile.log"))

    def send_notification_email(self):
        """
        method to send email and/or notification
        :return: None
        """
        # notification to be sent if not None
        if self.mattermost is not None and self.send_notification is not None:
            # send notification if value is always or if value is error and errors have been encountered
            if self.send_notification == "always" or (self.send_notification == "error" and self.nb_error > 0):
                self.mattermost.send_notification()

        # email to be sent if not None
        if self.email is not None and self.send_emails in ("yes", "y"):
            # add a title according to number of errors or warnings found
            if self.nb_error > 0:
                self.email.err_warning = "Service disrupted due to " + str(self.nb_error) + " error(s)"
            else:
                self.email.err_warning = "Service completed with " + str(self.nb_warning) + " warning(s)"
            # send email
            self.email.send_email()
