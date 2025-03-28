"""
This module is used to process data from the data sets.
It is used to filter, update, and merge data from the data sets.
"""
import json
import os


class DataProcessor:
    """
    This class processes the data from the data sets.
    It is used to filter, update, and merge data from the data sets.
    init:
        script_dir : str - The directory of the script that is calling the data processor.
    exposed methods:
        general_filter_function(fines : list, settings : dict) -> list: Runs the filters 
            based on the YAML configuration files
        update_field_value(fines : list, settings : dict) -> list: Runs the update function 
            based on the YAML configuration files
        merge_field_data(fines : list, settings : dict) -> list: Runs the merge function 
            based on the YAML configuration files
        gen_data_summary(fine : list, name : str) -> dict: Generates a summary of the data set.
    Internal methods:
        __filter_error(data : dict, settings : dict) -> dict: Collects and formats the error data
            for later use.
        __filter_get_field_value(data : dict, settings : dict) -> any : Gets the field 
            value from the data set.
        __flatten_array(ary : list) -> list: Flattens an array of dictionaries.
    """

    def __init__(self, script_dir):
        self.__script_dir = script_dir
        self.__filter_data = {}
        self.__error_data = []

    def get_filter_data(self):
        """
        This function returns the filter data that has been processed.
        """
        if self.__filter_data:
            return self.__filter_data
        return None

    def get_error_data(self):
        """
        This function returns the error data that has been processed.
        """
        return self.__error_data

    #pylint: disable-next=inconsistent-return-statements
    def general_filter_function(self, fines, settings):
        """
        This function is used to filter the data based on the settings passed in.
        :param fines : list - The data set to be filtered.
        :param settings : dict - The settings to be used to filter the data.
        :returns: list - The filtered data set.
        """
        # Set the passed and failed values in the filter data array
        if f'passed{settings["name"]}' not in self.__filter_data:
            self.__filter_data[f'passed{settings["name"]}'] = 0
            self.__filter_data[f'failed{settings["name"]}'] = 0

        # check to see if there are any items in the data set to process
        if fines:
            # If load is not False then a JSON file is loaded and processed as
            # the filter.
            if settings['load']:
                path = os.path.join(
                    self.__script_dir, '..', 'dataSets', f"{
                        settings['load']}.json")
                if path:  # Check if the file exists
                    with open(path, 'r', encoding='utf-8') as f:
                        test_data = json.load(f)
                else:
                    return

                if settings['flatten']:
                    test_data = self.__flatten_array(test_data)

            new_data = []
            # Filter the row data.
            for f in fines:
                tmp_val = self.__filter_get_field_value(f, settings)
                val_check = False
                filter_value = ''
                if isinstance(
                        settings['filter_value'],
                        str) and settings['filter_value'].startswith('ENV'):
                    tmp = settings['filter_value'].split('|')
                    filter_value = os.getenv(tmp[1])
                else:
                    filter_value = settings['filter_value']
                match  settings['filter_operator'].upper():
                    case "IN_FILE":
                        val_check = tmp_val is False or tmp_val in test_data
                    case "EQUALS":
                        val_check = tmp_val == filter_value
                    case "NOT_EQUAL":
                        val_check = tmp_val != filter_value
                    case "ONE_OF":
                        val_check = tmp_val in filter_value
                    case "NULL_OR_ONE_OF":
                        val_check = tmp_val is False or tmp_val in filter_value
                    case "LONGER_THAN":
                        val_check = tmp_val and int(
                            tmp_val) > int(filter_value)
                    case "SHORTER_THAN":
                        val_check = tmp_val and int(
                            tmp_val) < int(filter_value)

                if val_check:
                    self.__filter_data[f'passed{settings["name"]}'] += 1
                    new_data.append(f)
                else:
                    f = self.__filter_error(f, settings)
            return new_data
        return []

    def update_field_value(self, fines, settings):
        """
        This function is used to update the data based on the settings passed in.
        :param fines : list - The data set to be updated.
        :param settings : dict - The settings to be used to update the data.
        :returns: list - The updated data set.
        """
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
            if final_old_key in current_dict:
                match settings['type'].upper():
                    case 'REPLACE':
                        new_dict[final_new_key] = current_dict[final_old_key].replace(
                            search_for, replace_with)
                    case 'LEFT_STRIP':
                        new_dict[final_new_key] = current_dict[final_old_key].lstrip(
                            search_for)
                    case 'RIGHT_STRIP':
                        new_dict[final_new_key] = current_dict[final_old_key].rstrip(
                            search_for)
                    case 'MOVE':
                        new_dict[final_new_key] = current_dict[final_old_key]
        return fines

    #pylint: disable-next=inconsistent-return-statements, too-many-locals
    def merge_field_data(self, fines, settings):
        """
        This function is used to merge the data based on the settings passed in.
        :param fines : list - The data set to be merged.
        :param settings : dict - The settings to be used to merge the data.
        :returns: list - The updated data set.
        """
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
                new_dict[final_new_key] = f'{
                    current_dict_1[final_old_key_1]}{
                    settings["field_deliminator"]}{
                    current_dict_2[final_old_key_2]}'
        elif settings['merge_type'].upper() == "FILE":
            path = os.path.join(
                self.__script_dir, '..', 'dataSets',
                    f"{settings['load']}.json")
            if path:  # Check if the file exists
                with open(path, 'r', encoding='utf-8') as f:
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

    def gen_data_summary(self, fine, name):
        """
        This function is used to generate a summary of the data set.
        :param fine : list - The data set to be summarized.
        :param name : str - The name of the data set.
        :returns: list - The updated data set.
        """
        total = 0
        remaining = 0
        record_count = 0
        owner_stats = {}
        for f in fine:
            total += float(f['amount'])
            remaining += float(f['remaining']) if 'remaining' in f else 0
            record_count += 1
            if f['owner_data']['FeeFineOwner'] not in owner_stats:
                owner_stats[f['owner_data']['FeeFineOwner']] = {
                    "name": f['owner_data']['FeeFineOwner'],
                    "total": 0,
                    "remaining": 0,
                    "record_count": 0
                }
            owner_stats[f['owner_data']['FeeFineOwner']
                        ]['total'] += float(f['amount'])
            owner_stats[f['owner_data']['FeeFineOwner']
                        ]['remaining'] += float(f['remaining']) if 'remaining' in f else 0
            owner_stats[f['owner_data']['FeeFineOwner']]['record_count'] += 1
        return {
            f'{name}_total': total,
            f'{name}_remaining': remaining,
            f'{name}_record_count': record_count,
            f'{name}_owner_stats': owner_stats
        }

    def __filter_error(self, data, settings):
        """
        This function is used to handle errors in the data set and save them fro later export.
        :param data : dict - The data set to be processed.
        :param settings : dict - The settings to be used to process the data.
        :returns: dict - The processed data set.
        """
        self.__filter_data[f'failed{settings["name"]}'] += 1
        if settings["log_error"]:
            data['errorCode'] = settings['error_message']
            self.__error_data.append(data)
        return data

    def __filter_get_field_value(self, data, settings):
        """
        This function is used to get the field value from the data set.
        :param data : dict - The data set to be processed.
        :param settings : dict - The settings to be used to process the data.
        :returns: dict - The processed data set.
        """
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
        """
        This function is used to flatten an array of dictionaries.
        :param ary : list - The array to be flattened.
        :returns: list - The flattened array.
            { <<UUID>>, <<UUID>> }
        """
        new_data = []
        for x in ary:
            new_data.append(x['uuid'])
        return new_data

# End class DataProcessor
