#!/usr/bin/env python3
"""
BuildCredits class
This class is responsible for building the credit data for FOLIO.
It retrieves the data from the FOLIO system and processes it according to the
configuration file."""
# pylint: disable=R0801,too-few-public-methods
import logging
import json
from datetime import date, timedelta
from src.shared.data_processor import DataProcessor  # Import the new class

logger = logging.getLogger(__name__)


class BuildCredits:
    """
    This class is responsible for building the credit data for FOLIO.
    It retrieves the data from the FOLIO system and processes it according to the
    configuration file.
    exposed methods:
        get_credits() -> dict: This function retrieves the credit data from the FOLIO system
    Internal methods:
        __get_outstanding_credits_all() -> list: This function retrieves
            the outstanding credits from the FOLIO system.
        __get_fee_fine_data(credits: list) -> list: This function retrieves
            the fee fine data from the FOLIO system and includes it in the credit data.
    """

    PATRON_MERGE_SETTINGS = {
        "merge_type": "API",
        "api_call": "{{FOLIO}}/users/{{ID}}",
        "filter_field": "userId",
        "new_field": "patron",
        "api_action": "BATCH",
        "api_root": False,
    }
    MATERIAL_MERGE_SETTINGS = {
        "merge_type": "API",
        "api_call": "{{FOLIO}}/material-types?limit=1000",
        "filter_field": "materialTypeId",
        "new_field": "material",
        "api_action": "FLATTEN",
        "api_root": "mtypes",
    }

    def __init__(self, connector, settings):
        """
        Initialize the BuildCredits class.
        :param connector: The connector to the FOLIO system.
        :param settings: The configuration settings for the job.
        """
        logger.info("Initializing BuildCredits.")
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

        self.__data_processor = DataProcessor(connector)  # Initialize DataProcessor
        logger.info("BuildCredits initialized with settings: %s", settings)

    def get_credits(self):
        """
        This function retrieves the credit data from the FOLIO system and processes it
        according to the configuration file.
        :return: A dictionary containing the processed credit data, error data, and summary.
        """
        logger.info("Retrieving credit data.")
        error_data = []
        # Get fee fine information
        credit_data = {}
        # pull the outstanding credits
        credit_data = self.__get_outstanding_credits_all()
        logger.debug("Retrieved outstanding credits: %d records",
                     len(credit_data))

        # pull the fee fine data
        credit_data = self.__get_fee_fine_data(credit_data)
        logger.debug("Fee fine data merged into credit_data.")

        # pull the material data and include it in the fee fine data
        credit_data = self.__data_processor.merge_field_data(fines=credit_data, settings=self.MATERIAL_MERGE_SETTINGS)
        logger.debug("Material data merged into credit_data.")

        # pull user information
        credit_data = self.__data_processor.merge_field_data(fines=credit_data, settings=self.PATRON_MERGE_SETTINGS)
        logger.debug("Patron data merged into credit_data.")

        # Merge patron data into the Fee fine data
        self.__filter_data['rawRecordCount'] = len(credit_data)
        logger.info(
            "Raw record count: %d",
            self.__filter_data['rawRecordCount'])
        logger.debug("Credit data: %s", json.dumps(credit_data, indent=4))
        logger.info("Credit data retrieval complete.")

        if 'formatters' in self.__settings and 'credit_formatters' in self.__settings[
                'formatters']:
            for config in self.__settings['formatters']['credit_formatters']:
                credit_data = self.__data_processor.update_field_value(
                    credit_data, config)
                logger.debug("Applied formatter: %s", config)

        if 'mergers' in self.__settings and 'credit_mergers' in self.__settings['mergers']:
            for config in self.__settings['mergers']['credit_mergers']:
                credit_data = self.__data_processor.merge_field_data(
                    credit_data, config)
                logger.debug("Applied merger: %s", config)

        logger.debug("Credit data after formatters and merges: %s",
                     json.dumps(credit_data, indent=4))

        if 'filters' in self.__settings and 'credit_filters' in self.__settings['filters']:
            for config in self.__settings['filters']['credit_filters']:
                credit_data = self.__data_processor.general_filter_function(
                    credit_data, config)
                logger.debug("Credit data after filter %s: %s",
                             config["name"], json.dumps(credit_data, indent=4))
                logger.debug("Applied filter: %s", config)

        self.__filter_data.update(self.__data_processor.get_filter_data())
        error_data = self.__data_processor.get_error_data()
        logger.info("Filter data and error data updated.")

        self.__filter_data.update(
            self.__data_processor.gen_data_summary(
                credit_data, 'charge'))
        self.__filter_data.update(
            self.__data_processor.gen_data_summary(
                error_data, 'errors'))
        logger.info("Data summary generated.")

        formatted_data = {
            "data": credit_data,
            "error": error_data,
            "summary": self.__filter_data
        }
        logger.info("Credit data retrieval and processing complete.")
        return formatted_data

    def __get_outstanding_credits_all(self):
        """
        This function retrieves the outstanding credits from the FOLIO system.
        This pulls the "Refunds to process manually" report.
        :return: A list of outstanding credits.
        """
        logger.info("Retrieving outstanding credits.")
        credit_days_outstanding = self.__settings[
            "credit_days_outstanding"] if self.__settings["credit_days_outstanding"] else 1
        cur_date = date.today()
        start_age = cur_date - timedelta(days=int(credit_days_outstanding))
        end_age = cur_date - timedelta(days=1)
        date_format = '%Y-%m-%d'
        url = '/feefine-reports/refund'
        body = {
            "startDate": start_age.strftime(date_format),
            "endDate": end_age.strftime(date_format),
            "feeFineOwners": []
        }
        logger.debug(
            "Generated URL and body for outstanding credits: %s, %s",
            url,
            body)
        data = self.__connector.post_request(url, body)
        logger.info(
            "Retrieved outstanding credits: %d records", len(
                data['reportData']))
        return data['reportData']

    def __get_fee_fine_data(self, credit_data):
        """
        This function retrieves the fee fine data from the FOLIO system and
        includes it in the credit data.
        :param credit_data: The list of credits to process.
        :return: The list of credits with the fee fine data included.
        """
        logger.info("Retrieving fee fine data for credits.")
        new_data = []
        for c in credit_data:
            url = f'/accounts/{c["feeFineId"]}'
            fine_data = self.__connector.get_request(url)
            fine_data['report_data'] = c
            new_data.append(fine_data)
            logger.debug(
                "Retrieved fee fine data for credit: %s",
                c["feeFineId"])
            logger.debug(
                "Fee fine data: %s",
                json.dumps(fine_data, indent=4))
        logger.info("Fee fine data merged into credit_data.")
        return new_data
    
# End of BuildCredits class
