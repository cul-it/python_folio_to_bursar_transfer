#!/usr/bin/env python3
import os
import logging
import sys
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
        __get_patron_data(credits: list, patron_id: list) -> list: This
            function retrieves the user data from the FOLIO system and
            includes it in the credit data.
        __get_material_data(credits: list) -> list: This function retrieves
            the material data from the FOLIO system and includes it in the credit data.
exposed methods:
        get_credits() -> dict: This function retrieves the credit data from the FOLIO system
    Internal methods:
        __get_outstanding_credits_all() -> list: This function retrieves
            the outstanding credits from the FOLIO system.
        __get_fee_fine_data(credits: list) -> list: This function retrieves
            the fee fine data from the FOLIO system and includes it in the credit data.
        __get_patron_data(credits: list, patron_id: list) -> list: This
            function retrieves the user data from the FOLIO system and
            includes it in the credit data.
        __get_material_data(credits: list) -> list: This function retrieves
            the material data from the FOLIO system and includes it in the credit data.
    """

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

        self.__data_processor = DataProcessor()  # Initialize DataProcessor
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
        credit_data = self.__get_outstanding_credits_all()
        logger.debug("Retrieved outstanding credits: %d records",
                     len(credit_data))

        # pull the fee fine data
        credit_data = self.__get_fee_fine_data(credit_data)
        logger.debug("Fee fine data merged into credit_data.")

        # pull the material data and include it in the fee fine data
        credit_data = self.__get_material_data(credit_data)
        logger.debug("Material data merged into credit_data.")

        # Pull the patron ids from the fee fine data and make a unique list
        patron_id = []
        for c in credit_data:
            patron_id.append(c['patronId'])
        patron_id = list(set(patron_id))
        logger.debug("Unique patron IDs extracted: %d", len(patron_id))

        # pull user information
        credit_data = self.__get_patron_data(credit_data, patron_id)
        logger.debug("Patron data merged into credit_data.")

        # Merge patron data into the Fee fine data
        self.__filter_data['rawRecordCount'] = len(credit_data)
        logger.info("Raw record count: %d", self.__filter_data['rawRecordCount'])

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

        if 'filters' in self.__settings and 'credit_filters' in self.__settings['filters']:
            for config in self.__settings['filters']['credit_filters']:
                credit_data = self.__data_processor.general_filter_function(
                    credit_data, config)
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
        min_age = cur_date - timedelta(days=int(credit_days_outstanding))
        max_age = cur_date - timedelta(days=1)
        date_format = '%Y-%m-%d'
        url = '/feefine-reports/refund'
        body = {
            "startDate": min_age.strftime(date_format),
            "endDate": max_age.strftime(date_format),
            "feeFineOwners": []
        }
        logger.debug("Generated URL and body for outstanding credits: %s, %s", url, body)
        data = self.__connector.post_request(url, body)
        logger.info("Retrieved outstanding credits: %d records", len(data['reportData']))
        return data['reportData']

    def __get_fee_fine_data(self, credit_data):
        """
        This function retrieves the fee fine data from the FOLIO system and
        includes it in the credit data.
        :param credit_data: The list of credits to process.
        :return: The list of credits with the fee fine data included.
        """
        logger.info("Retrieving fee fine data for credits.")
        for c in credit_data:
            url = f'/accounts/{c["feeFineId"]}'
            c['feeFineData'] = self.__connector.get_request(url)
            logger.debug("Retrieved fee fine data for credit: %s", c["feeFineId"])
        logger.info("Fee fine data merged into credit_data.")
        return credit_data

    def __get_patron_data(self, credit_data, patron_id):
        """
        This function retrieves the user data from the FOLIO system and
        includes it in the credit data.
        :param credit_data: The list of credits to process.
        :param patron_id: The list of unique patron IDs.
        :return: The list of credits with the user data included.
        """
        logger.info("Retrieving patron data for %d patrons.", len(patron_id))
        new_data = {}
        for p in patron_id:
            self.__filter_data['uniquePatronCount'] += 1
            new_data[p] = self.__connector.get_request(f'/users/{p}')
            logger.debug("Retrieved data for patron ID: %s", p)
        for c in credit_data:
            c['patron'] = new_data[c['patronId']]
        logger.info("Patron data merged into credit_data.")
        return credit_data

    def __get_material_data(self, credit_data):
        """
        This function retrieves the material data from the FOLIO system and
        includes it in the credit data.
        :param credit_data: The list of credits to process.
        :return: The list of credits with the material data included.
        """
        logger.info("Retrieving material data.")
        raw_material_list = self.__connector.get_request(
            '/material-types?limit=1000')
        new_data = {}
        for m in raw_material_list['mtypes']:
            new_data[m['id']] = m
            logger.debug("Material type added: %s", m['id'])
        for c in credit_data:
            c['material'] = new_data[c['feeFineData']['materialTypeId']]
            logger.debug("Material data added for credit: %s", c['feeFineData']['materialTypeId'])
        logger.info("Material data merged into credit_data.")
        return credit_data
# End of BuildCredits class