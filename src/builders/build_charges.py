#!/usr/bin/env python3
"""
BuildCharges class
This class is responsible for building the charge data for FOLIO.
It retrieves the data from the FOLIO system and processes it according to the
configuration file.
"""
# pylint: disable=R0801,too-few-public-methods
import logging
from datetime import date, timedelta
from src.shared.data_processor import DataProcessor  # Import the new class

logger = logging.getLogger(__name__)


class BuildCharges:
    """
    This class is responsible for building the charge data for FOLIO.
    It retrieves the data from the FOLIO system and processes it according to the
    configuration file.
    exposed methods:
        get_charges() -> dict: This function retrieves the charge data from the FOLIO system
    Internal methods:
        __get_outstanding_fines_all() -> list: This function retrieves
            the outstanding fines from the FOLIO system.
        __get_patron_data(fines: list, patron_id: list) -> list: This
            function retrieves the patron data from the FOLIO system
            and adds it to the fine data.
        __get_material_data(fines: list) -> list: This function retrieves
            the material data from the FOLIO system and includes it in the fee fine data.
    """

    def __init__(self, connector, settings):
        """
        Initialize the BuildCharges class.
        :param connector: The connector to the FOLIO system.
        :param settings: The configuration settings for the job.
        """
        logger.info("Initializing BuildCharges.")
        self.__settings = settings
        self.__connector = connector

        # ******
        #   Setup some variables to store data for processing
        #   Using global functions instead of passing variables back and forth.
        # ******
        self.__filter_data = {  # Holds the retrieved Fee Fine Data
            "reportedRecordCount": 0,
            "uniquePatronCount": 0,
            "rawRecordCount": 0,
        }
        self.__data_processor = DataProcessor()
        logger.info("BuildCharges initialized with settings: %s", settings)

    def get_charges(self):
        """
        This function retrieves the charge data from the FOLIO system and processes it
        according to the configuration file.
        :return: A dictionary containing the processed charge data, error data, and summary.
        """
        logger.info("Retrieving charge data.")
        error_data = []
        fines = self.__get_outstanding_fines_all()
        logger.debug("Retrieved outstanding fines: %d records",
                     len(fines))

        patron_id = list(set(f['userId'] for f in fines))
        logger.debug("Unique patron IDs extracted: %d",
                     len(patron_id))

        fines = self.__get_patron_data(fines, patron_id)
        logger.debug("Patron data merged into fines.")

        fines = self.__get_material_data(fines)
        logger.debug("Material data merged into fines.")

        self.__filter_data['rawRecordCount'] = len(fines)
        logger.info("Raw record count: %d",
                    self.__filter_data['rawRecordCount'])

        if 'formatters' in self.__settings and 'charge_formatters' in self.__settings[
                'formatters']:
            for config in self.__settings['formatters']['charge_formatters']:
                fines = self.__data_processor.update_field_value(fines, config)
                logger.debug("Applied formatter: %s", config)

        if 'mergers' in self.__settings and 'charge_mergers' in self.__settings['mergers']:
            for config in self.__settings['mergers']['charge_mergers']:
                fines = self.__data_processor.merge_field_data(fines, config)
                logger.debug("Applied merger: %s", config)

        if 'filters' in self.__settings and 'charge_filters' in self.__settings['filters']:
            for config in self.__settings['filters']['charge_filters']:
                fines = self.__data_processor.general_filter_function(
                    fines, config)
                logger.debug("Applied filter: %s", config)

        self.__filter_data.update(self.__data_processor.get_filter_data())
        error_data = self.__data_processor.get_error_data()
        logger.info("Filter data and error data updated.")

        self.__filter_data.update(
            self.__data_processor.gen_data_summary(
                fines, 'charge'))
        self.__filter_data.update(
            self.__data_processor.gen_data_summary(
                error_data, 'errors'))
        logger.info("Data summary generated.")

        formatted_data = {
            "data": fines,
            "error": error_data,
            "summary": self.__filter_data
        }
        logger.info("Charge data retrieval and processing complete.")
        return formatted_data

    def __get_outstanding_fines_all(self):
        """
        This function retrieves the outstanding fines from the FOLIO system.
        :return: A list of outstanding fines.
        """
        logger.info("Retrieving outstanding fines.")
        charges_max_age = self.__settings.get("charges_max_age", 365)
        charge_days_outstanding = self.__settings.get(
            "charge_days_outstanding", 0)
        limit = self.__settings.get("max_fines_to_be_pulled", 10000000)

        cur_date = date.today()
        file_name_date = cur_date - \
            timedelta(days=int(charge_days_outstanding))
        max_age = cur_date - timedelta(days=int(charges_max_age))

        url = f'/accounts?query=(status.name=="Open" and metadata.createdDate < {
            file_name_date.strftime("%Y-%m-%d")} and metadata.createdDate > {
            max_age.strftime("%Y-%m-%d")})&limit={limit}'
        logger.debug("Generated URL for outstanding fines: %s", url)

        data = self.__connector.get_request(url)
        self.__filter_data['reportedRecordCount'] = data['resultInfo']['totalRecords']
        logger.info("Reported record count: %d",
                    self.__filter_data['reportedRecordCount'])
        return data['accounts']

    def __get_patron_data(self, fines, patron_id):
        """
        This function retrieves the patron data from the FOLIO system
        and adds it to the fine data.
        :param fines: The list of fines to be processed.
        :param patron_id: The list of unique patron IDs.
        :return: The list of fines with the patron data included.
        """
        logger.info("Retrieving patron data for %d patrons.", len(patron_id))
        new_data = {}
        for p in patron_id:
            self.__filter_data['uniquePatronCount'] += 1
            new_data[p] = self.__connector.get_request(f'/users/{p}')
            logger.debug("Retrieved data for patron ID: %s", p)

        for f in fines:
            f['patron'] = new_data[f['userId']]
        logger.info("Patron data merged into fines.")
        return fines

    def __get_material_data(self, fines):
        """
        This function retrieves the material data from the FOLIO system and
        includes it in the fee fine data.
        :param fines: The list of fines to be processed.
        :return: The list of fines with the material data included.
        """
        logger.info("Retrieving material data.")
        raw_material_list = self.__connector.get_request(
            '/material-types?limit=1000')
        new_data = {}
        for m in raw_material_list['mtypes']:
            new_data[m['id']] = m
            logger.debug("Material type added: %s", m['id'])

        for f in fines:
            if 'materialTypeId' not in f:
                f['material'] = {
                    "id": "",
                    "name": "",
                    "source": "",
                    "metadata": {
                        "createdDate": "",
                        "createdByUserId": "",
                        "updatedDate": "",
                        "updatedByUserId": ""
                    }
                }
                logger.debug("Default material data added for fine: %s", f)
            else:
                f['material'] = new_data[f['materialTypeId']]
                logger.debug(
                    "Material data added for fine: %s",
                    f['materialTypeId'])
        logger.info("Material data merged into fines.")
        return fines
# End of class BuildCharges
