#!/usr/bin/env python3
import json
import os
from dotenv import load_dotenv
load_dotenv()
from datetime import date, timedelta
from src.shared.data_processor import DataProcessor  # Import the new class

class BuildCredits:

    def __init__(self, connector):
        self.__script_dir = os.path.dirname(__file__)
        self.__connector = connector
        self.__credit_days_outstanding = os.getenv('CREDIT_DAYS_OUTSTANDING') if os.getenv('CREDIT_DAYS_OUTSTANDING') else 1

        #******
        #   Setup some variables to store data for processing
        #   Using global functions instead of passing variables back and forth.
        #******
        self.__filter_data = { # Holds the retrieved Fee Fine Data
            "reportedRecordCount": 0,
            "uniquePatronCount": 0,
            "rawRecordCount":0,
         }

        self.__data_processor = DataProcessor(self.__script_dir, self.__connector)  # Initialize DataProcessor

    def get_credits(self):
        error_data = []
        # Get fee fine information
        credits = self.__get_outstanding_credits_all()
        
        #pull the fee fine data
        credits = self.__get_fee_fine_data(credits)

        # Pull the patron ids from the fee fine data and make a unique list
        patron_id = []
        for c in credits:
            patron_id.append(c['patronId'])
        patron_id = list(set(patron_id))

        # pull the material data and include it in the fee fine data
        credits = self.__get_material_data(credits)

        # pull user information
        credits = self.__get_patron_data(credits, patron_id)
        # Merge patron data into the Fee fine data
        self.__filter_data['rawRecordCount'] = len(credits)

        output_JSON = os.path.join(self.__script_dir, 'temp', 'credits.json')
        with open(output_JSON, 'w') as f:
            json.dump(credits, f, indent=4)  # Save with indentation for readability
            

        i = 1
        while f'CREDIT_REFORMAT_{i}' in os.environ:
            settings = json.loads(os.getenv(f'CREDIT_REFORMAT_{i}'))
            print(settings)
            credits = self.__data_processor.update_field_value(credits, settings)
            i += 1
        
        i = 1
        while f'CREDIT_MERGE_{i}' in os.environ:
            settings = json.loads(os.getenv(f'CREDIT_MERGE_{i}'))
            print(settings)
            credits = self.__data_processor.merge_field_data(credits, settings)
            i += 1

        i = 1
        while f'CREDIT_FILTER_{i}' in os.environ:
            settings = json.loads(os.getenv(f'CREDIT_FILTER_{i}'))
            print(settings)
            credits = self.__data_processor.general_filter_function(credits, settings)
            i += 1

        self.__filter_data.update( self.__data_processor.get_filter_data() )
        error_data = self.__data_processor.get_error_data()
        self.__filter_data.update( self.__data_processor.gen_data_summary(credits, 'charge') )
        self.__filter_data.update( self.__data_processor.gen_data_summary(error_data, 'errors') )

        formatted_data = {
            "data": credits,
            "error": error_data,
            "summary": self.__filter_data 
        }
        
        output_JSON = os.path.join(self.__script_dir, 'temp', 'credits.json')
        with open(output_JSON, 'w') as f:
            json.dump(formatted_data, f, indent=4)  # Save with indentation for readability

        return formatted_data
        

    #*************************************************************** 
    # 
    #                   Supporting functions
    #                  --------------------------------
    #   __get_outstanding_credits_all -     Get fee/fines to be transferred to in FOLIO.
    #                                       @returns dict
    #   __get_fee_fine_data -               Get the fee/fine data for the credits
    #                                       @returns dict
    #   __get_patron_data -                 Get all the patrons in the credit data set    
    #                                       @returns dict
    #***************************************************************

    def __get_outstanding_credits_all(self):
        cur_date = date.today()
        min_age = cur_date - timedelta(days=int(self.__credit_days_outstanding))
        max_age = cur_date - timedelta(days=1)
        format = '%Y-%m-%d'
        url = f'/feefine-reports/refund'
        body  = {
            "startDate": min_age.strftime(format),
            "endDate": max_age.strftime(format),
            "feeFineOwners":[]
        }
        data = self.__connector.post_request(url, body)    
        return data['reportData']
    
    def __get_fee_fine_data(self, credits):
        for c in credits:
            url = f'/accounts/{c["feeFineId"]}'
            c['feeFineData'] = self.__connector.get_request(url)
        return credits
    
    def __get_patron_data(self, credits, patron_id):
        new_data = {}
        for p in patron_id:
            self.__filter_data['uniquePatronCount'] += 1
            new_data[p] = self.__connector.get_request(f'/users/{p}')
        for c in credits:
            c['patron'] = new_data[c['patronId']]
        return credits
    
    def __get_material_data(self, credits):
        raw_material_list = self.__connector.get_request('/material-types?limit=1000')
        new_data = {}
        for m in raw_material_list['mtypes']:
            new_data[m['id']] = m
        for c in credits:
            c['material'] = new_data[c['feeFineData']['materialTypeId']]
        return credits