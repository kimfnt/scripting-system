# -*- coding: utf-8 -*-
"""
Email management:
Mail can be send through the internal service or smtp.
Format an email to send to several recipients.
Contains a summary of the different steps.
Log file can be attached to the email.

@author: Kim-Céline FRANOT
"""

from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
import json
import smtplib
import ssl
import datetime
from email_validator import validate_email


class Email:
    """
    Class to send email

    Attributes:
        server: smtplib object
        content: Array
        log: Log
        err_warning: string
        host = String
        port = string
        auth = dict
        include_log = string
        title = string
        dest = Array
    Methods:
        login(): None
        login_and_send(): None
        send_smtp(): None
        add_content(String, String): None
        attach_file(MIMEMultipart): MIMEMultipart()
        format_mail(): String
        send_email(): None

    """

    def __init__(self, config_, log_):
        self.server = None
        self.log = log_
        self.content = []
        self.err_warning = None
        try:
            data = config_
            auth_ = data["auth"]
            include_log_ = data["include_log"].lower()
            title_ = data["title"]
            dest_ = data["dest"]
            host_ = data["server"]["host"]
            try:
                port_ = int(data["server"]["port"])
            except ValueError:
                port_ = 465
                self.log.info("JSON read", "Email Server port format not supported. Default value is 465.")

        except json.JSONDecodeError:
            self.log.error("JSON file read")
            return
        except KeyError as err:
            self.log.error("JSON file read", err.args[0])
            return
        except EnvironmentError:
            self.log.error("JSON file read")

        if auth_["email"] == "":
            self.log.warning("Email config", "No email entered: email sending canceled.")

        if auth_["password"] == "":
            self.log.warning("Email config", "No password entered: email sending canceled.")

        if include_log_ not in ("yes", "no", "y", "n"):
            include_log_ = "yes"
            self.log.warning("Email config", "Value entered for include_log field incorrect. Default value is yes.")

        if title_ == "":
            title_ = "Scripting System Summary"
            self.log.warning("Email config", "Title of email empty, default title added.")

        if len(dest_) == 0:
            self.log.warning("Email config", "No recipients for the email entered.")
        else:
            for _e_ in dest_:
                if not validate_email(_e_):
                    self.log.warning("Email config", _e_ + " is not valid.")
                    dest_.remove(_e_)

        # Affect values
        self.host = host_
        self.port = port_
        self.auth = auth_
        self.include_log = include_log_
        self.title = title_
        self.dest = dest_

    def login(self):
        """
        method to login to personal email account
        :return: None
        """
        try:
            self.server.login(self.auth["email"], self.auth["password"])
        except smtplib.SMTPAuthenticationError as err:
            self.log.warning("Email authentication", "Credentials not accepted on server. Email not sent." + err)
        except smtplib.SMTPNotSupportedError:
            self.log.warning("Email authentication", "AUTH command not supported on the server. Email not sent.")
        except smtplib.SMTPException:
            self.log.warning("Email authentication", "Unknown error occurred. Email not sent.")

    def login_and_send(self):
        """
        method to send email
        :return: None
        """
        try:
            self.login()
            msg = MIMEMultipart()
            msg["Subject"] = self.title + ": " + self.err_warning
            msg.attach(MIMEText(self.format_mail(), 'plain'))
            msg = self.attach_file(msg)
            self.server.sendmail(self.auth["email"], self.dest, msg.as_string())
            self.log.info("Email sent")
            self.server.quit()
        except smtplib.SMTPRecipientsRefused:
            self.log.warning("Sending email", "Recipients refused, email was not sent.")

        except smtplib.SMTPSenderRefused:
            self.log.warning("Sending email", "Sender address not accepted by server. Email not sent.")

        except smtplib.SMTPDataError:
            self.log.warning("Sending email", "Error occurred. Email not sent.")

        except smtplib.SMTPServerDisconnected as err:
            self.log.warning("Sending email", "Server disconnected. Email not sent." + err)

        except smtplib.SMTPException:
            self.log.warning("Sending email", "Unknown error occurred. Email not sent.")

        except Exception as err:
            self.log.warning("Sending mail", err)

    def send_stmp(self):
        """
        method to send mail through personal mail service
        :return: None
        """
        context = ssl.create_default_context()
        try:
            self.server = smtplib.SMTP_SSL(self.host, self.port, context=context)
        except TimeoutError:
            self.log.warning("Email server connection", "Timeout error, email not sent.")
        except smtplib.SMTPServerDisconnected:
            self.log.warning("Email server connection", "Server disconnected, email not sent.")

        if self.server is not None:
            self.login_and_send()

    def send_internal_server(self):
        """
        method to send through internal server of machine
        :return: None
        """
        try:
            server = smtplib.SMTP('192.168.56.1', port=1025)
            msg = MIMEMultipart()
            msg['Subject'] = self.title
            msg.attach(MIMEText(self.format_mail(), 'plain'))
            msg = self.attach_file(msg)
            server.sendmail(self.auth["email"], self.dest, msg.as_string())
        except Exception as err:
            self.log.warning("Sending email", err)

    def add_content(self, message_type, msg):
        """
        Method to add task log into mail content
        :param message_type: String that indicates the type of log status
        :param msg: String with content of the task information
        :return: None
        """
        self.content.append(message_type + ": " + msg)

    def attach_file(self, msg):
        """
        method to add log file as attachment to email if requested
        :param msg:
        :return: msg
        """
        if self.include_log in ("yes", "y"):
            try:
                log_file = self.log.get_file()
                actual_date = datetime.date.today().strftime("%d_%m_%Y")
                part = MIMEBase('application', 'octet-stream')
                with open(log_file, 'rb') as attachment:
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment; filename= log_file_' + actual_date + '.txt')
                    msg.attach(part)
                    self.log.info('Attachment', "Log file added to mail")
            except EnvironmentError:
                self.log.warning("Attachment", "Error while loading attachment into email body. No file attached.")

        return msg

    def format_mail(self):
        """
        method to break line of body
        :return: format_data, string
        """
        format_data = ""

        for line in self.content:
            format_data += line + "\n"

        return format_data

    def send_email(self):
        """
        method to send email
        :return: None
        """
        if self.host != "":
            self.send_stmp()
        else:
            self.send_internal_server()
