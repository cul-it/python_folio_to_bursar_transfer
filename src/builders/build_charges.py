#!/usr/bin/env python3
import json
import os
from datetime import date, timedelta
from src.shared.data_processor import DataProcessor  # Import the new class


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
        self.__settings = settings
        self.__script_dir = os.path.dirname(__file__)
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

        self.__data_processor = DataProcessor(
            self.__script_dir)  # Initialize DataProcessor

    def get_charges(self):
        """
        This function retrieves the charge data from the FOLIO system and processes it
        according to the configuration file.
        :return: A dictionary containing the processed charge data, error data, and summary.
        """
        error_data = []
        # Get fee fine information
        fines = self.__get_outstanding_fines_all()

        # Pull the patron ids from the fee fine data and make a unique list
        patron_id = []
        for f in fines:
            patron_id.append(f['userId'])
        patron_id = list(set(patron_id))

        # pull user information
        fines = self.__get_patron_data(fines, patron_id)
        # pull the material data and include it in the fee fine data
        fines = self.__get_material_data(fines)

        # Merge patron data into the Fee fine data
        self.__filter_data['rawRecordCount'] = len(fines)

        if 'formatters' in self.__settings and 'charge_formatters' in self.__settings[
                'formatters']:
            for config in self.__settings['formatters']['charge_formatters']:
                fines = self.__data_processor.update_field_value(fines, config)

        if 'mergers' in self.__settings and 'charge_mergers' in self.__settings['mergers']:
            for config in self.__settings['mergers']['charge_mergers']:
                fines = self.__data_processor.merge_field_data(fines, config)

        if 'filters' in self.__settings and 'charge_filters' in self.__settings['filters']:
            for config in self.__settings['filters']['charge_filters']:
                fines = self.__data_processor.general_filter_function(
                    fines, config)

        self.__filter_data.update(self.__data_processor.get_filter_data())
        error_data = self.__data_processor.get_error_data()
        self.__filter_data.update(
            self.__data_processor.gen_data_summary(
                fines, 'charge'))
        self.__filter_data.update(
            self.__data_processor.gen_data_summary(
                error_data, 'errors'))

        formatted_data = {
            "data": fines,
            "error": error_data,
            "summary": self.__filter_data
        }

        return formatted_data

    def __get_outstanding_fines_all(self):
        """
        This function retrieves the outstanding fines from the FOLIO system.
        :return: A list of outstanding fines.
        """
        charges_max_age = self.__settings["charges_max_age"] if self.__settings["charges_max_age"] else 365
        charge_days_outstanding = self.__settings[
            "charge_days_outstanding"] if self.__settings["charge_days_outstanding"] else 0
        limit = self.__settings["max_fines_to_be_pulled"] if self.__settings["max_fines_to_be_pulled"] else 10000000

        cur_date = date.today()
        file_name_date = cur_date - \
            timedelta(days=int(charge_days_outstanding))
        max_age = cur_date - timedelta(days=int(charges_max_age))

        url = f'/accounts?query=(status.name=="Open" and metadata.createdDate < {
            file_name_date.strftime("%Y-%m-%d")} and metadata.createdDate > {
            max_age.strftime("%Y-%m-%d")})&limit={limit}'
        data = self.__connector.get_request(url)
        self.__filter_data['reportedRecordCount'] = data['resultInfo']['totalRecords']
        return data['accounts']

    def __get_patron_data(self, fines, patron_id):
        new_data = {}
        for p in patron_id:
            self.__filter_data['uniquePatronCount'] += 1
            new_data[p] = self.__connector.get_request(f'/users/{p}')
        for f in fines:
            f['patron'] = new_data[f['userId']]
        return fines

    def __get_material_data(self, fines):
        """
        This function retrieves the material data from the FOLIO system and
        includes it in the fee fine data.
        :param fines: The list of fines to be processed.
        :return: The list of fines with the material data included.
        """
        raw_material_list = self.__connector.get_request(
            '/material-types?limit=1000')
        new_data = {}
        for m in raw_material_list['mtypes']:
            new_data[m['id']] = m
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
            else:
                f['material'] = new_data[f['materialTypeId']]
        return fines
# End of class BuildCharges