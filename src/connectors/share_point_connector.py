"""Python script to send emails using Microsoft Graph API with OAuth2 authentication."""
# pylint: disable=R0801
import logging
from O365 import Account, FileSystemTokenBackend
from O365.utils import AWSS3Backend
from src.uploaders.o365_backends import CustomAwsS3Backend
from src.shared.env_loader import EnvLoader

logger = logging.getLogger(__name__)


class SharePointConnection:
    """
    A class to handle sending emails using Microsoft Graph API.
    """

    def __init__(self, env_key):
        """
        Initializes the MSEmail class with client ID, client secret, and tenant ID.
        """
        connection_id = EnvLoader().get(name=f"{env_key}_CONNECTION")
        logger.info("Initializing MSEmail with env_key: %s", env_key)
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

        acct = Account(
            credentials,
            token_backend=token_backend,
            raise_http_errors=False)

        sp_site = acct.sharepoint().get_site(
            EnvLoader().get(name=f"{env_key}_SITE")
        )
        self.__sp_list = sp_site.get_list_by_name(
            EnvLoader().get(name=f"{env_key}_LIST")
        )

    def write_rows(self, data):
        """
        Write rows to the SharePoint List.
        :param data: The data to be written.
        :return: The results of the write operation.
        """
        logger.info("Writing rows to SharePoint. Data: %s", data)
        results = []
        try:
            for item in data:
                result = self.__sp_list.create_list_item(item)
                results.append(result)
                logger.debug("Updated row: %s", result)
            logger.info("Rows written successfully. Results: %s", results)
            return results
        except Exception as e:
            logger.error("Error writing rows to SharePoint: %s", e)
            raise

    def update_rows(self, data, filter_string):
        """
        Update rows in the SharePoint List based on the filter string.
        :param data: The data to be updated.
        :param filter_string: The field to filter the rows.
        :return: The results of the update.
        """
        logger.info(
            "Updating rows in SharePoint. Filter: %s, Data: %s",
            filter_string,
            data)
        results = []
        try:
            for item in data:
                formula = f"fields/{filter_string} eq '{item[filter_string]}'"
                logger.debug("Generated formula for update: %s", formula)
                list_items = self.__sp_list.get_items(query=formula)
                if list_items:
                    for list_item in list_items:
                        list_item.update_fields(item)
                        result = list_item.save_updates()
                        results.append(result)
                        logger.debug("Updated row: %s", result)
            logger.info("Rows updated successfully. Results: %s", results)
            return results
        except Exception as e:
            logger.error("Error updating rows in SharePoint: %s", e)
            raise

    def delete_rows(self, data, filter_string):
        """
        Delete rows from the SharePoint based on the filter string.
        :param data: The data to be deleted.
        :param filter_string: The field name to filter by.
        :return: The results of the deletion.
        """
        logger.info(
            "Deleting rows from SharePoint. Filter: %s, Data: %s",
            filter_string,
            data)
        results = []
        try:
            for item in data:
                formula = f"fields/{filter_string} eq '{item[filter_string]}'"
                logger.debug("Generated formula for deletion: %s", formula)
                list_items = self.__sp_list.get_items(query=formula)
                if list_items:
                    for list_item in list_items:
                        result = list_item.delete()
                        results.append(result)
                        logger.debug("Delete row: %s", result)
            logger.info("Rows deleted successfully. Results: %s", results)
            return results
        except Exception as e:
            logger.error("Error deleting rows from SharePoint: %s", e)
            raise

# End of class SharePointImporter
