# -*- coding: utf-8 -*-
"""
Mattermost notification:
Format the notification to send on the mattermost server
Contains a summary of the different steps of the service ans its status

@author: Kim-Céline FRANOT
"""
import datetime
import requests


class Mattermost:
    """
    Class to send notification to the mattermost server

    Attributes:
        webhook: string
        mattermost_content: dict
        log: Log
    Methods:
        set_info(string)
        set_error(string)
        set_warning(string)
        format_notification()
        send_notification()

    """

    def __init__(self, log_, webhook_=None):
        self.mattermost_content = {
            "tasks": ["Tasks", ":-----------------------------"],
            "status": ["Status", ":-------------:"]
        }
        self.log = log_
        if webhook_ is None:
            self.webhook = "https://chat.telecomste.fr/hooks/13ta3nw3e787tnxxqkyxfh5xnr"
        else:
            self.webhook = webhook_

    def set_info(self, task):
        """
        method to add status symbol to the task
        :param task: string of task name
        :return: None
        """
        self.mattermost_content["tasks"].append(task)
        self.mattermost_content["status"].append(" :white_check_mark: ")

    def set_warning(self, task):
        """
        method to add status symbol to the task
        :param task: string of task name
        :return: None
        """
        self.mattermost_content["tasks"].append(task)
        self.mattermost_content["status"].append(" :warning: ")

    def set_error(self, task):
        """
        method to add status symbol to the task
        :param task: string of task name
        :return: None
        """
        self.mattermost_content["tasks"].append(task)
        self.mattermost_content["status"].append(" :x: ")

    def format_notification(self):
        """
        method to format the body of the notification
        :return: content, String
        """

        # get date to add to header of the notification
        actual_date = datetime.date.today().strftime("%B %d, %Y")
        content = "#### Archiving report for " + actual_date + "\n"

        # we add a line for each tasks
        for i in range(len(self.mattermost_content["tasks"])):
            content += (
                    "|"
                    + self.mattermost_content["tasks"][i]
                    + "|"
                    + self.mattermost_content["status"][i]
                    + "|\n"
            )
        return content

    def send_notification(self):
        """
        method to send the notification on the mattermost server

        :return: None
        """
        # get data to be sent
        content = self.format_notification()

        payload = {
            "icon_url": "https://mattermost.org/wp-content/uploads/2016/04/icon.png",
            "text": content
        }

        try:
            # request to post on the server with webhook
            response = requests.post(self.webhook, json=payload)
            response.raise_for_status()

        except requests.exceptions.ConnectionError:
            self.log.warning("Mattermost notification",
                             "Connection error to the mattermost server. Notification not sent.")
        except requests.exceptions.HTTPError as err:
            self.log.warning("Mattermost notification",
                             "HTTP error encountered: " + err.args[0] + ". Notification not sent.")
        except requests.exceptions.Timeout:
            self.log.warning("Mattermost notification", "Timeout. Notification not sent.")
        except requests.exceptions.RequestException:
            self.log.warning("Mattermost notification", "Unknown Error. Notification not sent.")
