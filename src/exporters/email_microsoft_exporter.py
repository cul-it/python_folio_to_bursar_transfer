"""Python script to send emails using Microsoft Graph API with OAuth2 authentication."""
# pylint: disable=R0801
import re
import logging
from io import BytesIO
from src.shared.common_helpers import generate_file_name
from src.shared.microsoft_connector import MicrosoftConnector

logger = logging.getLogger(__name__)


class EmailMicrosoftExporter:
    """
    A class to handle sending emails using Microsoft Graph API.
    """

    def __init__(self, conf, template_processor):
        """
        Initializes the MSEmail class with client ID, client secret, and tenant ID.
        """
        connection_name = conf['connection_name']
        self.__conf = conf
        self.__template_processor = template_processor

        logger.info("Initializing MSEmail with connection_name: %s", connection_name)
        ms_connector = MicrosoftConnector(connection_name)
        self.__message = ms_connector.get_new_message()
        logger.info("MSEmail initialized.")

    def build_message(self, to, subject, body):
        """
        Creates a new message object.
        """
        # pylint: disable=R0801
        if isinstance(to, str):
            to = re.split(r'[;, ]+', to)

        new_body = f"""<html><body>
                     {body.replace('\n', '<br>')}
                </body></html>"""
        self.__message.to.add(to)
        self.__message.subject = subject
        self.__message.body = new_body
        logger.info("Email message built successfully.")
        return True

    def send_message(self):
        """
        Authenticates the account using the provided credentials.
        """
        logger.info("Sending email message.")
        try:
            self.__message.send()
            logger.info("Email sent successfully.")
        except Exception as e:
            logger.error("Failed to send email: %s", e, exc_info=True)
            raise
        return True

    def add_attachment(self, file_data, filename):
        """
        Adds an attachment to the email message.
        :param file_data: The attachment body to add.
        :param filename: The name of the file to attach.
        """
        logger.info("Adding attachment to email: %s", filename)
        try:
            data = BytesIO()
            data.write(file_data.encode("utf-8"))
            data.seek(0)
            attachment = (data, filename)
            self.__message.attachments.add([attachment])
            logger.info("Attachment added successfully: %s", filename)
        except Exception as e:
            logger.error("Failed to add attachment: %s", e, exc_info=True)
            raise
        return True

    def ship_it(self):
        """
        Processes the export configuration and sends the email.
        """
        logger.info("Processing export configuration: %s", self.__conf)
        processed_data = self.__template_processor.process_template(
            self.__conf)
        file_name = generate_file_name(self.__conf)
        logger.debug("Processed file name: %s", file_name)

        self.build_message(
            to=self.__conf['export_to'],
            subject=file_name,
            body=processed_data
        )

        if 'attachment' in self.__conf and self.__conf['attachment']:
            logger.debug("Processing email attachments.")
            for attach in self.__conf['attachment']:
                logger.debug("Processing email attachment: %s", attach)
                attachment_data = self.__template_processor.process_template(
                    attach)
                attachment_name = generate_file_name(attach)
                self.add_attachment(attachment_data, attachment_name)

        self.send_message()

# End of the class MSEmail
