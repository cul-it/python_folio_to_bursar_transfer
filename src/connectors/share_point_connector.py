"""Python script to send emails using Microsoft Graph API with OAuth2 authentication."""
# pylint: disable=R0801
import logging
from src.shared.microsoft_connector import MicrosoftConnector

logger = logging.getLogger(__name__)


class SharePointConnection:
    """
    A class to handle sending emails using Microsoft Graph API.
    """

    def __init__(self, conf):
        """
        Initializes the MSEmail class with client ID, client secret, and tenant ID.
        """
        ms_connector = MicrosoftConnector(conf['connection_name'])
        self.__sp_list = ms_connector.get_sharepoint_list()

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
