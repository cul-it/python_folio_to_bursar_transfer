"""Python script to send emails using Microsoft Graph API with OAuth2 authentication."""
import re
import logging
from io import BytesIO
from O365 import Account, FileSystemTokenBackend
from O365.utils import AWSS3Backend
from src.uploaders.o365_backends import CustomAwsS3Backend
from src.shared.env_loader import EnvLoader

logger = logging.getLogger(__name__)


class MSEmail:
    """
    A class to handle sending emails using Microsoft Graph API.
    """

    def __init__(self, env_key):
        """
        Initializes the MSEmail class with client ID, client secret, and tenant ID.
        """
        logger.info("Initializing MSEmail with env_key: %s", env_key)
        credentials = (
            EnvLoader().get(name=f"{env_key}_CLIENT_ID"),
            EnvLoader().get(name=f"{env_key}_CERTIFICATE_VALUE")
        )

        match EnvLoader().get(name=f"{env_key}_AUTH_LOCATION").upper():
            case 'LOCAL':
                logger.info("Loading local credentials...")
                token_backend = FileSystemTokenBackend(
                    token_path=EnvLoader().get(name=f"{env_key}_AUTH_PATH"),
                    token_filename=f"{env_key}_TOKEN.json"
                )
            case 'S3':
                if EnvLoader().get(name=f"{env_key}_SECURE"):
                    logger.info("Loading AWS credentials from S3 bucket.")
                    token_backend = CustomAwsS3Backend(
                        env_key=EnvLoader().get(name=f"{env_key}_AUTH_PATH"),
                        filename=f"{env_key}_TOKEN.json"
                    )
                else:
                    logger.info("Loading AWS credentials from Lambda function.")
                    token_backend = AWSS3Backend(
                        bucket_name=EnvLoader().get(name=f"{env_key}_AUTH_PATH"),
                        filename=f"{env_key}_TOKEN.json"
                    )
            case _:
                logger.error("Invalid AUTH_LOCATION. Must be 'LOCAL' or 'AWS'.")
                raise ValueError("Invalid AUTH_LOCATION. Must be 'LOCAL' or 'AWS'.")

# Initialize the account with the credentials and token backend
        # the default protocol will be Microsoft Graph
        # the default authentication method will be "on behalf of a user"
        self.__account = Account(credentials, token_backend=token_backend)
        if self.__account.is_authenticated:
            logger.info("Authenticated successfully.")
        else:
            logger.warning("Authentication failed.")

        self.__message = self.__account.new_message()
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

# End of the class MSEmail
