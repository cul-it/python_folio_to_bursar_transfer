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

    def __init__(self, connection_name):
        """
        Initializes the MSEmail class with client ID, client secret, and tenant ID.
        """
        self.__connection_name = connection_name
        self.__ms_connection = EnvLoader().get(name=f"{connection_name}_CONNECTION")
        logger.info("Initializing MSConnector with connection_name: %s", self.__connection_name)
        credentials = (
            EnvLoader().get(name=f"{self.__ms_connection}_CLIENT_ID"),
            EnvLoader().get(name=f"{self.__ms_connection}_CERTIFICATE_VALUE")
        )

        match EnvLoader().get(name=f"{self.__ms_connection}_AUTH_LOCATION").upper():
            case 'LOCAL':
                logger.info("Loading local credentials...")
                token_backend = FileSystemTokenBackend(
                    token_path=EnvLoader().get(
                        name=f"{self.__ms_connection}_AUTH_PATH"),
                    token_filename=f"{self.__ms_connection}_TOKEN.json")
            case 'S3':
                if EnvLoader().get(name=f"{self.__ms_connection}_SECURE"):
                    logger.info("Loading AWS credentials from S3 bucket.")
                    token_backend = CustomAwsS3Backend(
                        env_key=EnvLoader().get(
                            name=f"{self.__ms_connection}_AUTH_PATH"),
                        filename=f"{self.__ms_connection}_TOKEN.json")
                else:
                    logger.info(
                        "Loading AWS credentials from Lambda function.")
                    token_backend = AWSS3Backend(
                        bucket_name=EnvLoader().get(
                            name=f"{self.__ms_connection}_AUTH_PATH"),
                        filename=f"{self.__ms_connection}_TOKEN.json")
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
            EnvLoader().get(name=f"{self.__connection_name}_SITE")
        )
        return sp_site.get_list_by_name(
            EnvLoader().get(name=f"{self.__connection_name}_LIST")
        )
    
    def get_teams_channel(self):
        """
        Returns a Teams channel object.
        """
        channel_id = EnvLoader().get(name=f"{self.__connection_name}_CHANNEL_ID")
        team_id = EnvLoader().get(name=f"{self.__connection_name}_TEAM_ID")
        team = self.__acct.teams()
        team = team.get_channel(channel_id=channel_id, team_id=team_id)
        return team
    
    def get_sharepoint_site(self):
        """
        Returns a SharePoint folder object.
        """
        sp_site = self.__acct.sharepoint().get_site(
            EnvLoader().get(name=f"{self.__connection_name}_SITE")
        )
        return sp_site
        # folder = EnvLoader().get(name=f"{self.__connection_name}_FOLDER")
        # sp_site = sp_site.get_default_document_library()
        # return sp_site.get_item_by_path(folder)

    def get_new_storage(self):
        """
        Returns the storage object for OneDrive.
        """
        return self.__acct.storage()
    
    def walk_the_tree(self, folder, ms_site, type):
        """
        Walks through the folder tree and returns a list of items.
        """
        cur_folder = EnvLoader().get(name=f"{self.__connection_name}_FOLDER")
        folders = folder.split('/')
        for item in folders:
            logger.info("Current item: %s", item)
            if not item:
                continue
            if type == 'onedrive':
                logger.info("Walking through OneDrive: %s", item)
                ms_site_copy = ms_site.get_default_drive()
            else:
                logger.info("Walking through SharePoint site: %s", item)
                ms_site_copy = ms_site.get_default_document_library()
            ms_site_copy = ms_site_copy.get_item_by_path(f"{cur_folder}/{item}")
            if not ms_site_copy:
                logger.info("Creating new folder: %s", item)
                if type == 'onedrive':
                    logger.info("Walking through OneDrive: %s", item)
                    ms_site_copy = ms_site.get_default_drive()
                else:
                    logger.info("Walking through SharePoint site: %s", item)
                    ms_site_copy = ms_site.get_default_document_library()
                ms_site_copy = ms_site_copy.get_item_by_path(cur_folder)
                ms_site_copy = ms_site_copy.create_child_folder(item)
            cur_folder = f"{cur_folder}/{item}"
        logger.info("Final folder path: %s", cur_folder)
        ms_site = ms_site.get_default_document_library()
        return ms_site.get_item_by_path(cur_folder)

# End of class MicrosoftConnector
