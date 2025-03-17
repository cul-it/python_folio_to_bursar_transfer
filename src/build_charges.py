#!/usr/bin/env python3
import json
import os
from dotenv import load_dotenv
load_dotenv()
from datetime import date, timedelta

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
        self.__error_data = [] # Hold fee fines that can not be processed for one reason or another

    def get_charges(self):
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
        while f'REFORMAT_{i}' in os.environ:
            settings = json.loads(os.getenv(f'REFORMAT_{i}'))
            fines = self.__update_field_value(fines, settings)
            i += 1
        
        i = 1
        while f'MERGE_{i}' in os.environ:
            settings = json.loads(os.getenv(f'MERGE_{i}'))
            fines = self.__merge_field_data(fines, settings)
            i += 1

        i = 1
        while f'FILTER_{i}' in os.environ:
            settings = json.loads(os.getenv(f'FILTER_{i}'))
            fines = self.__general_filter_function(fines, settings)
            i += 1

        self.__filter_data.update( self.__gen_data_summary(fines, 'charge') )
        self.__filter_data.update( self.__gen_data_summary(self.__error_data, 'errors') )

        formatted_data = {
            "charge_data": fines,
            "error_data": self.__error_data,
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
    
    def __general_filter_function(self, fines, settings):
        # Set the passed and failed values in the filter data array
        if f'passed{settings['name']}' not in self.__filter_data:
            self.__filter_data[f'passed{settings['name']}'] = 0
            self.__filter_data[f'failed{settings['name']}'] = 0

        # check to see if there are any items in the data set to process    
        if fines:
            # If load is not False then a JSON file is loaded and processed as the filter.
            if settings['load'] != False:
                path = os.path.join(self.__script_dir, 'dataSets', settings['load'])
                if path:  # Check if the file exists
                    with open(path, 'r') as f:
                        test_data = json.load(f)
                else:
                    return
                
                if settings['flatten'] == True:
                    test_data = self.__flatten_array(test_data)
            
            new_data = []
            # Filter the row data.
            for f in fines:
                tmpVal = self.__filter_get_field_value(f, settings)
                valCheck = False
                match  settings['filter_operator'].upper():
                    case "IN_FILE":
                        valCheck = True if tmpVal == False or tmpVal in test_data else False
                    case "EQUALS":
                        valCheck = True if tmpVal == settings['filter_value'] else False
                    case "NOT_EQUAL": 
                        valCheck = True if tmpVal != settings['filter_value'] else False
                    case "ONE_OF":
                        valCheck = True if tmpVal in settings['filter_value'] else False
                    case "NULL_OR_ONE_OF":
                        valCheck = True if tmpVal == False or tmpVal in settings['filter_value'] else False
                    case "LONGER_THAN":
                        valCheck = True if int(tmpVal) > int(settings['filter_value']) else False
                    case "SHORTER_THAN":
                        valCheck = True if int(tmpVal) < int(settings['filter_value']) else False

                if valCheck == True:
                    self.__filter_data[f'passed{settings['name']}'] += 1
                    new_data.append(f)
                else:
                    f = self.__filter_error(f, settings)
            return new_data
        else:
            print('Fine data is empty')
            return []
        
    def __update_field_value(self, fines, settings): 
        # Split the filter_field to navigate through the dictionary
        old_keys = settings['filter_field'].split('.')
        new_keys = settings['new_field'].split('.')
        search_for = settings['search_for']
        replace_with = settings['replace_with']

        for f in fines:
            current_dict = f
            new_dict = f

            # Navigate through the dictionary to get to the final key
            for key in old_keys[:-1]:
                current_dict = current_dict[key]
            for key in new_keys[:-1]:
                new_dict = new_dict[key]

            # Apply the replacement
            final_old_key = old_keys[-1]
            final_new_key = new_keys[-1]
            match settings['type'].upper():
                case 'REPLACE':
                    new_dict[final_new_key] = current_dict[final_old_key].replace(search_for, replace_with)
                case 'LEFT_STRIP':
                    new_dict[final_new_key] = current_dict[final_old_key].lstrip(search_for)
                case 'RIGHT_STRIP':
                    new_dict[final_new_key] = current_dict[final_old_key].rstrip(search_for)

        return fines

    def __merge_field_data(self, fines, settings):
        if settings['merge_type'].upper() == "FIELD":
            old_keys_1 = settings['field_1'].split('.')
            old_keys_2 = settings['field_2'].split('.')
            new_keys = settings['new_field'].split('.')
            for f in fines:
                current_dict_1 = f
                current_dict_2 = f
                new_dict = f
                for key in old_keys_1[:-1]:
                    current_dict_1 = current_dict_1[key]
                for key in old_keys_2[:-1]:
                    current_dict_2 = current_dict_2[key]
                for key in new_keys[:-1]:
                    new_dict = new_dict[key]
                final_old_key_1 = old_keys_1[-1]
                final_old_key_2 = old_keys_2[-1]
                final_new_key = new_keys[-1]
                new_dict[final_new_key] = f'{current_dict_1[final_old_key_1]}{settings['field_deliminator']}{current_dict_2[final_old_key_2]}'
        elif settings['merge_type'].upper() == "FILE":
            path = os.path.join(self.__script_dir, 'dataSets', settings['load'])
            if path:  # Check if the file exists
                with open(path, 'r') as f:
                    merge_data = json.load(f)
            else:
                return
            for f in fines:
                key_value = self.__filter_get_field_value(f, settings)            
                new_keys = settings['new_field'].split('.')
                new_dict = f

                # Navigate through the dictionary to get to the final key
                for key in new_keys[:-1]:
                    new_dict = new_dict[key]

                # Apply the replacement
                final_new_key = new_keys[-1]
                new_dict[final_new_key] = merge_data[key_value]
            

        return fines



    def __filter_error(self, data, settings):
        self.__filter_data[f'failed{settings['name']}'] += 1
        data['errorCode'] = settings['error_message']
        self.__error_data.append(data)
        return data


    def __filter_get_field_value(self, data, settings):
        keys = settings['filter_field'].split('.')
        for key in keys:
            if key in data:
                data = data[key]
            else:
                return False
        match settings['field_transform'].upper():
            case 'NONE':
                return data
            case 'COUNT':
                return len(data)
        return data
    
    def __flatten_array(self, ary):
        new_data = []
        for x in ary:
            new_data.append( x['uuid'] )
        return new_data
    
    def __gen_data_summary(self, fine, name):
        total = 0
        remaining = 0
        record_count = 0
        owner_stats = {}
        for f in fine:
            total += int(f['amount'])
            remaining += int(f['remaining'])
            record_count += 1
            if f['owner_data']['FeeFineOwner'] not in owner_stats:
                owner_stats[f['owner_data']['FeeFineOwner']] = {
                    "name": f['owner_data']['FeeFineOwner'],
                    "total": 0,
                    "remaining": 0,
                    "record_count": 0
                }
            owner_stats[f['owner_data']['FeeFineOwner']]['total'] += int(f['amount'])
            owner_stats[f['owner_data']['FeeFineOwner']]['remaining'] += int(f['remaining'])
            owner_stats[f['owner_data']['FeeFineOwner']]['record_count'] += 1
        return {
            f'{name}_total': total,
            f'{name}_remaining': remaining,
            f'{name}_record_count': record_count,
            f'{name}_owner_stats': owner_stats
        }