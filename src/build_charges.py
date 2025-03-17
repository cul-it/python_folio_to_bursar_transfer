#!/usr/bin/env python3
import json
import os
from dotenv import load_dotenv
load_dotenv()
from datetime import date, timedelta
from src.data_processor import DataProcessor  # Import the new class

class BuildCharges:

    def __init__(self, baseFunctions):
        self.__script_dir = os.path.dirname(__file__)
        self.__base_functions = baseFunctions
        self.__charge_days_outstanding = os.getenv('CHARGES_DAYS_OUTSTANDING') if os.getenv('CHARGES_DAYS_OUTSTANDING') else 0
        self.__max_fine_age = os.getenv('CHARGES_MAX_AGE') if os.getenv('CHARGES_MAX_AGE') else 365

        #******
        #   Setup some variables to store data for processing
        #   Using global functions instead of passing variables back and forth.
        #******
        self.__filter_data = { # Holds the retrieved Fee Fine Data
            "reportedRecordCount": 0,
            "uniquePatronCount": 0,
            "rawRecordCount":0,
         }

        self.__data_processor = DataProcessor(self.__script_dir, self.__base_functions)  # Initialize DataProcessor

    def get_charges(self):
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


        output_JSON = os.path.join(self.__script_dir, 'temp', 'fine.json')
        with open(output_JSON, 'w') as f:
            json.dump(fines, f, indent=4)  # Save with indentation for readability
            

        i = 1
        while f'CHARGE_REFORMAT_{i}' in os.environ:
            settings = json.loads(os.getenv(f'CHARGE_REFORMAT_{i}'))
            fines = self.__data_processor.update_field_value(fines, settings)
            i += 1
        
        i = 1
        while f'CHARGE_MERGE_{i}' in os.environ:
            settings = json.loads(os.getenv(f'CHARGE_MERGE_{i}'))
            fines = self.__data_processor.merge_field_data(fines, settings)
            i += 1

        i = 1
        while f'CHARGE_FILTER_{i}' in os.environ:
            settings = json.loads(os.getenv(f'CHARGE_FILTER_{i}'))
            fines = self.__data_processor.general_filter_function(fines, settings)
            i += 1

        self.__filter_data.update( self.__data_processor.get_filter_data() )
        error_data = self.__data_processor.get_error_data()
        self.__filter_data.update( self.__data_processor.gen_data_summary(fines, 'charge') )
        self.__filter_data.update( self.__data_processor.gen_data_summary(error_data, 'errors') )

        formatted_data = {
            "data": credits,
            "error": error_data,
            "summary": self.__filter_data 
        }
        

        output_JSON = os.path.join(self.__script_dir, 'temp', 'fine.json')
        with open(output_JSON, 'w') as f:
            json.dump(formatted_data, f, indent=4)  # Save with indentation for readability

        return formatted_data
        
        

        
    
    #*************************************************************** 
    # 
    #                   Supporting functions
    #                  --------------------
    #   __get_outstanding_fines_all -   Get fee/fines to be transferred to in FOLIO.
    #                                   @returns dict
    #    __get_patron_data -            Get all the patrons in the fee fine data set    
    #                                   @returns true if successful
    #   __merge_data -                  Merge patron and other data into the Fee Fine Data
    #                                   @returns new fee fine object
    #   __general_filter_function -     Filters out fee fines based on parameters stored in the ENV file.
    #                                   @returns new fee fine object
    #   __update_field_value -          replaces a fields value with another value based on a regex expression
    #   __filter_error -                Logs errors during the filter process
    #   __filter_get_field_value -      Gets the value of a field for filtering. Also checks to see if the field is in the dataset. If not it returns False
    #   __flatten_array -               Flattens a data set so it can be access more efficiently
    #   __gen_data_summary -            Generates a summary of the fine data set
    # 
    #***************************************************************/

    def __get_outstanding_fines_all(self):
        cur_date = date.today()
        file_name_date = cur_date - timedelta(days=int(self.__charge_days_outstanding))
        max_age = cur_date - timedelta(days=int(self.__max_fine_age))
        limit = os.getenv('MAX_FINES_TO_BE_PULLED')
        url = f'/accounts?query=(status.name=="Open" and metadata.createdDate < {file_name_date.strftime("%Y-%m-%d")} and metadata.createdDate > {max_age.strftime("%Y-%m-%d")})&limit={limit}'
        data = self.__base_functions.get_request(url)    
        self.__filter_data['reportedRecordCount'] = data['resultInfo']['totalRecords']
        return data['accounts']
    
    def __get_patron_data(self, fines, patron_id):
        new_data = {}
        for p in patron_id:
            self.__filter_data['uniquePatronCount'] += 1
            new_data[p] = self.__base_functions.get_request(f'/users/{p}')
        for f in fines:
            f['patron'] = new_data[f['userId']]
        return fines
    
    def __get_material_data(self, fines):
        raw_material_list = self.__base_functions.get_request('/material-types?limit=1000')
        new_data = {}
        for m in raw_material_list['mtypes']:
            new_data[m['id']] = m
        for f in fines:
            f['material'] = new_data[f['materialTypeId']]
        return fines
    
    