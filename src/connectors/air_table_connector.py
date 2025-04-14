"""
 This class provides methods to write, update, and delete rows in an AirTable table.
"""
import logging
from pyairtable import Api
from pyairtable.formulas import match
from src.shared.env_loader import EnvLoader

logger = logging.getLogger(__name__)


class AirTableConnector:
    """
    A class to handle importing data into AirTable.
    public methods:
    - write_rows: Write rows to the AirTable table.
    - update_rows: Update rows in the AirTable table based on the filter string.
    - delete_rows: Delete rows from the AirTable based on the filter string.
    """
    def __init__(self, env_key: str):
        logger.info("Initializing AirTableConnector with env_key: %s", env_key)
        api = Api(EnvLoader().get(name=f"{env_key}_API_KEY"))
        app_id = EnvLoader().get(name=f"{env_key}_APP_ID")
        table_id = EnvLoader().get(name=f"{env_key}_TABLE_ID")
        self.__table = api.table(app_id, table_id)
        logger.info("AirTableConnector initialized successfully.")

    def write_rows(self, data):
        """
        Write rows to the AirTable table.
        :param data: The data to be written.
        :return: The results of the write operation.
        """
        logger.info("Writing rows to AirTable. Data: %s", data)
        try:
            results = self.__table.batch_create(data)
            logger.info("Rows written successfully. Results: %s", results)
            return results
        except Exception as e:
            logger.error("Error writing rows to AirTable: %s", e)
            raise

    def update_rows(self, data, filter_string):
        """
        Update rows in the AirTable table based on the filter string.
        :param data: The data to be updated.
        :param filter_string: The field to filter the rows.
        :return: The results of the update.
        """
        logger.info("Updating rows in AirTable. Filter: %s, Data: %s", filter_string, data)
        results = []
        try:
            for item in data:
                formula = match({filter_string: item[filter_string]})
                logger.debug("Generated formula for update: %s", formula)
                air_items = self.__table.all(formula=formula)
                if air_items:
                    for air_item in air_items:
                        result = self.__table.update(air_item['id'], item)
                        results.append(result)
                        logger.debug("Updated row: %s", result)
            logger.info("Rows updated successfully. Results: %s", results)
            return results
        except Exception as e:
            logger.error("Error updating rows in AirTable: %s", e)
            raise

    def delete_rows(self, data, filter_string):
        """
        Delete rows from the AirTable based on the filter string.
        :param data: The data to be deleted.
        :param filter_string: The field name to filter by.
        :return: The results of the deletion.
        """
        logger.info("Deleting rows from AirTable. Filter: %s, Data: %s", filter_string, data)
        results = []
        try:
            for item in data:
                formula = match({filter_string: item[filter_string]})
                logger.debug("Generated formula for deletion: %s", formula)
                air_items = self.__table.all(formula=formula)
                if air_items:
                    for air_item in air_items:
                        result = self.__table.delete(air_item['id'])
                        results.append(result)
                        logger.debug("Deleted row: %s", result)
            logger.info("Rows deleted successfully. Results: %s", results)
            return results
        except Exception as e:
            logger.error("Error deleting rows from AirTable: %s", e)
            raise

# End of class AirTableConnector
