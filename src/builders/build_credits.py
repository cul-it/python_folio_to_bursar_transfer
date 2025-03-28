#!/usr/bin/env python3
import os
from datetime import date, timedelta
from src.shared.data_processor import DataProcessor  # Import the new class


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
    """

    def __init__(self, connector, settings):
        """
        Initialize the BuildCredits class.
        :param connector: The connector to the FOLIO system.
        :param settings: The configuration settings for the job.
        """
        self.__settings = settings
        script_dir = os.path.dirname(__file__)
        self.__connector = connector
        credit_days_outstanding = settings["credit_days_outstanding"] if settings["credit_days_outstanding"] else 1

        # ******
        #   Setup some variables to store data for processing
        #   Using global functions instead of passing variables back and forth.
        # ******
        self.__filter_data = {  # Holds the retrieved Fee Fine Data
            "reportedRecordCount": 0,
            "uniquePatronCount": 0,
            "rawRecordCount": 0,
        }

        self.__data_processor = DataProcessor(
            script_dir)  # Initialize DataProcessor

    def get_credits(self):
        """
        This function retrieves the credit data from the FOLIO system and processes it
        according to the configuration file.
        :return: A dictionary containing the processed credit data, error data, and summary.
        """
        error_data = []
        # Get fee fine information
        credits = self.__get_outstanding_credits_all()

        # pull the fee fine data
        credits = self.__get_fee_fine_data(credits)

        # pull the material data and include it in the fee fine data
        credits = self.__get_material_data(credits)

        # Pull the patron ids from the fee fine data and make a unique list
        patron_id = []
        for c in credits:
            patron_id.append(c['patronId'])
        patron_id = list(set(patron_id))

        # pull user information
        credits = self.__get_patron_data(credits, patron_id)
        # Merge patron data into the Fee fine data
        self.__filter_data['rawRecordCount'] = len(credits)

        if 'formatters' in self.__settings and 'credit_formatters' in self.__settings[
                'formatters']:
            for config in self.__settings['formatters']['credit_formatters']:
                credits = self.__data_processor.update_field_value(
                    credits, config)

        if 'mergers' in self.__settings and 'credit_mergers' in self.__settings['mergers']:
            for config in self.__settings['mergers']['credit_mergers']:
                credits = self.__data_processor.merge_field_data(
                    credits, config)

        if 'filters' in self.__settings and 'credit_filters' in self.__settings['filters']:
            for config in self.__settings['filters']['credit_filters']:
                credits = self.__data_processor.general_filter_function(
                    credits, config)

        self.__filter_data.update(self.__data_processor.get_filter_data())
        error_data = self.__data_processor.get_error_data()
        self.__filter_data.update(
            self.__data_processor.gen_data_summary(
                credits, 'charge'))
        self.__filter_data.update(
            self.__data_processor.gen_data_summary(
                error_data, 'errors'))

        formatted_data = {
            "data": credits,
            "error": error_data,
            "summary": self.__filter_data
        }

        return formatted_data

    def __get_outstanding_credits_all(self):
        """
        This function retrieves the outstanding credits from the FOLIO system.
        This pulls the "Refunds to process manually" report.
        :return: A list of outstanding credits.
        """
        credit_days_outstanding = self.__settings[
            "credit_days_outstanding"] if self.__settings["credit_days_outstanding"] else 1
        cur_date = date.today()
        min_age = cur_date - timedelta(days=int(credit_days_outstanding))
        max_age = cur_date - timedelta(days=1)
        format = '%Y-%m-%d'
        url = f'/feefine-reports/refund'
        body = {
            "startDate": min_age.strftime(format),
            "endDate": max_age.strftime(format),
            "feeFineOwners": []
        }
        data = self.__connector.post_request(url, body)
        return data['reportData']

    def __get_fee_fine_data(self, credits):
        """
        This function retrieves the fee fine data from the FOLIO system and
        includes it in the credit data.
        :param credits: The list of credits to process.
        :return: The list of credits with the fee fine data included.
        """
        for c in credits:
            url = f'/accounts/{c["feeFineId"]}'
            c['feeFineData'] = self.__connector.get_request(url)
        return credits

    def __get_patron_data(self, credits, patron_id):
        """
        This function retrieves the user data from the FOLIO system and
        includes it in the credit data.
        :param credits: The list of credits to process.
        :param patron_id: The list of unique patron IDs.
        :return: The list of credits with the user data included.
        """
        new_data = {}
        for p in patron_id:
            self.__filter_data['uniquePatronCount'] += 1
            new_data[p] = self.__connector.get_request(f'/users/{p}')
        for c in credits:
            c['patron'] = new_data[c['patronId']]
        return credits

    def __get_material_data(self, credits):
        """
        This function retrieves the material data from the FOLIO system and
        includes it in the credit data.
        :param credits: The list of credits to process.
        :return: The list of credits with the material data included.
        """
        raw_material_list = self.__connector.get_request(
            '/material-types?limit=1000')
        new_data = {}
        for m in raw_material_list['mtypes']:
            new_data[m['id']] = m
        for c in credits:
            c['material'] = new_data[c['feeFineData']['materialTypeId']]
        return credits
# End of BuildCredits class