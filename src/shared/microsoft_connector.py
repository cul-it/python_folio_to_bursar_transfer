"""
Microsoft Connector
This module provides a class to connect to Microsoft services using the O365 library.
It handles authentication and provides methods to interact with Microsoft services.
"""
import logging
from O365 import Account, FileSystemTokenBackend
from O365.utils import AWSS3Backend
from src.uploaders.o365_backends import CustomAwsS3Backend
from src.shared.env_loader import EnvLoader

logger = logging.getLogger(__name__)

class MicrosoftConnector:

    def __init__(self, env_key):
        """
        Initializes the MSEmail class with client ID, client secret, and tenant ID.
        """
        self.__env_key = env_key
        connection_id = EnvLoader().get(name=f"{self.__env_key}_CONNECTION")
        logger.info("Initializing MSEmail with env_key: %s", self.__env_key)
        credentials = (
            EnvLoader().get(name=f"{connection_id}_CLIENT_ID"),
            EnvLoader().get(name=f"{connection_id}_CERTIFICATE_VALUE")
        )

        match EnvLoader().get(name=f"{connection_id}_AUTH_LOCATION").upper():
            case 'LOCAL':
                logger.info("Loading local credentials...")
                token_backend = FileSystemTokenBackend(
                    token_path=EnvLoader().get(
                        name=f"{connection_id}_AUTH_PATH"),
                    token_filename=f"{connection_id}_TOKEN.json")
            case 'S3':
                if EnvLoader().get(name=f"{connection_id}_SECURE"):
                    logger.info("Loading AWS credentials from S3 bucket.")
                    token_backend = CustomAwsS3Backend(
                        env_key=EnvLoader().get(
                            name=f"{connection_id}_AUTH_PATH"),
                        filename=f"{connection_id}_TOKEN.json")
                else:
                    logger.info(
                        "Loading AWS credentials from Lambda function.")
                    token_backend = AWSS3Backend(
                        bucket_name=EnvLoader().get(
                            name=f"{connection_id}_AUTH_PATH"),
                        filename=f"{connection_id}_TOKEN.json")
            case _:
                logger.error(
                    "Invalid AUTH_LOCATION. Must be 'LOCAL' or 'AWS'.")
                raise ValueError(
                    "Invalid AUTH_LOCATION. Must be 'LOCAL' or 'AWS'.")

        self.__acct = Account(
            credentials,
            token_backend=token_backend,
            raise_http_errors=False)

        if self.__acct.is_authenticated:
            logger.info("Authenticated successfully.")
        else:
            logger.warning("Authentication failed.")

    def get_new_message(self):
        """
        Returns a new message object.
        """
        return self.__acct.new_message()

    def get_sharepoint_list(self):
        """
        Returns a SharePoint site object.
        """

        sp_site = self.__acct.sharepoint().get_site(
            EnvLoader().get(name=f"{self.__env_key}_SITE")
        )
        return sp_site.get_list_by_name(
            EnvLoader().get(name=f"{self.__env_key}_LIST")
        )

    def get_new_storage(self):
        """
        Returns the storage object for OneDrive.
        """
        return self.__acct.storage()

# End of class MicrosoftConnector
