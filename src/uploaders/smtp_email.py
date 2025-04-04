"""
This module provides a class to send emails via SMTP with support for 
secure and insecure connections,
"""
import re
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List
from src.shared.env_loader import EnvLoader

logger = logging.getLogger(__name__)


class SMTPEmailSender:
    """
    A class to send emails via SMTP with support for secure and insecure connections,
    and the ability to add multiple attachments.
    """

    def __init__(self, env_key):
        """
        Initialize the SMTPEmailSender class.
        :param env_key: The environment key for loading SMTP configuration 
            from environment variables.
        :return: None
        """
        logger.info("Initializing SMTPEmailSender with env_key: %s", env_key)
        self.__smtp_server = EnvLoader().get(name=f"{env_key}_HOST")
        self.__port = EnvLoader().get(name=f"{env_key}_PORT")
        self.__username = EnvLoader().get(name=f"{env_key}_USERNAME")
        self.__password = EnvLoader().get(name=f"{env_key}_PASSWORD")
        self.__use_tls = EnvLoader().get(name=f"{env_key}_TLS")
        self.__message = MIMEMultipart()
        self.__message["From"] = EnvLoader().get(name=f"{env_key}_DEFAULT_FROM")
        logger.info("SMTPEmailSender initialized with server: %s, port: %s",
                    self.__smtp_server, self.__port)

    def build_message(self, to: List[str], subject: str, body: str):
        """
        Creates a new message object.
        :param to: The recipient email addresses.
        :param subject: The subject of the email.
        :param body: The body of the email.
        """
        logger.info("Building email message with subject: %s", subject)
        if isinstance(to, str):
            to = re.split(r'[;, ]+', to)

        new_body = f"""<html><body>
                     {body.replace('\n', '<br>')}
                </body></html>"""
        self.__message["To"] = ", ".join(to)
        self.__message["Subject"] = subject
        self.__message.attach(MIMEText(new_body, "html"))
        logger.info("Email message built successfully.")
        return True

    def add_attachment(self, file_data: str, filename: str):
        """
        Adds an attachment to the email message.
        :param file_data: The attachment body to add.
        :param filename: The name of the file to attach.
        """
        logger.info("Adding attachment to email: %s", filename)
        try:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(file_data.encode("utf-8"))
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={filename}",
            )
            self.__message.attach(part)
            logger.info("Attachment added successfully: %s", filename)
        except Exception as e:
            logger.error("Failed to add attachment: %s", e, exc_info=True)
            raise

    def send_message(self):
        """
        Authenticates the account using the provided credentials and sends the email.
        """
        logger.info("Sending email message.")
        try:
            # Connect to the SMTP server
            with smtplib.SMTP(self.__smtp_server, self.__port) as server:
                if self.__use_tls:
                    logger.info("Starting TLS for SMTP connection.")
                    server.starttls()
                logger.info("Logging in to SMTP server.")
                server.login(self.__username, self.__password)
                server.send_message(self.__message)
                logger.info("Email sent successfully.")
        except Exception as e:
            logger.error("Failed to send email: %s", e, exc_info=True)
            raise RuntimeError(f"An error occurred: {e}") from e
# End of class SMTPEmailSender
