"""
common_helpers.py
This module contains utility functions
methods:
    pascal_to_camel_case: Converts a PascalCase string to camelCase.
    generate_file_name: Processes the file name based on the configuration passed.
"""
import re
import logging
from datetime import date

logger = logging.getLogger(__name__)


def pascal_to_camel_case(pascal_string):
    """Converts a PascalCase string to camelCase.

    Args:
        pascal_string: The PascalCase string to convert.

    Returns:
        The camelCase version of the string.
    """
    snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', pascal_string).lower()
    return snake_case


def generate_file_name(conf):
    """
    This function processes the file name based on the configuration.
    It replaces the placeholders in the file name with actual values.
    :param conf: The configuration dictionary for the export.
    :return: The processed file name.
    """
    logger.info("Generating file name with configuration: %s", conf)
    file_name = conf['file_name']
    if conf['file_append_date']:
        date_string = f'{date.today().strftime(conf["date_format"])}'
        file_name = file_name.replace('{date}', date_string)
    logger.debug("Generated file name: %s", file_name)
    return file_name

def get_nested_value(data, *keys):
    """
    This function retrieves a nested value from a dictionary or a list using keys or indices.
    If the data is a dictionary, it calls get_nested_value.
    If the data is a list, it calls get_nested_list_value.
    :param data: The dictionary or list to search.
    :param keys: A list of keys/indices, a dot-separated string (for dict), or multiple key arguments.
    :return: The value found at the specified path, or None if not found.
    """
    print(f"get_nested_value called with data: {data} and keys: {keys}")
    logger.debug("data (type): %s", type(keys))
    if isinstance(keys, str):
        logger.debug("keys (string): %s", keys)
        keys = keys.split('.')
    elif isinstance(keys, tuple):
        keys = [subkey for key in keys for subkey in (key.split('.') if isinstance(key, str) else [key])]
    elif not isinstance(keys, list):
        keys = list(keys)

    if isinstance(data, dict):
        return __get_nested_dict_value(data, keys)
    elif isinstance(data, list):
        return __get_nested_list_value(data, keys)
    else:
        raise TypeError("Data must be either a dictionary or a list.")

def set_nested_value(data, value, *keys):
    """
    This function retrieves a nested value from a dictionary or a list using keys or indices.
    If the data is a dictionary, it calls get_nested_value.
    If the data is a list, it calls get_nested_list_value.
    :param data: The dictionary or list to search.
    :param keys: A list of keys/indices, a dot-separated string (for dict), or multiple key arguments.
    :return: The value found at the specified path, or None if not found.
    """
    logger.debug("data (type): %s", type(keys))
    if isinstance(keys, str):
        logger.debug("keys (string): %s", keys)
        keys = keys.split('.')
    elif isinstance(keys, tuple):
        keys = [subkey for key in keys for subkey in (key.split('.') if isinstance(key, str) else [key])]
    elif not isinstance(keys, list):
        keys = list(keys)

    if isinstance(data, dict):
        print("this is a dict")
        return __set_nested_dict_value(data, keys, value)
    elif isinstance(data, list):
        print("this is a list")
        return __set_nested_list_value(data, keys, value)
    else:
        raise TypeError("Data must be either a dictionary or a list.")

def __get_nested_dict_value(data, keys):
    """
    This function retrieves a nested value from a dictionary using a list of keys, 
    a dot-separated string, or multiple key arguments.    
    :param data: The dictionary to search.
    :param keys: A list of keys, a dot-separated string, or multiple key arguments 
                 representing the path to the desired value.
    :return: The value found at the specified path, or None if not found.
    """
    for key in keys:
        data = data.get(key, None)
        if data is None:
            return None
    return data

def __set_nested_dict_value(data, keys, value):
    """
    This function sets a value in a nested dictionary using a list of keys, 
    a dot-separated string, or multiple key arguments.
    :param data: The dictionary to modify.
    :param keys: A list of keys, a dot-separated string, or multiple key arguments 
                 representing the path to the desired value.
    :param value: The value to set at the specified path.
    :return: The full updated dictionary after modification.
    """
    current = data
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value
    return data  # Ensure the original dictionary is returned

def __get_nested_list_value(data, indices):
    """
    This function retrieves a nested value from a list using a list of indices.
    :param data: The list to search.
    :param indices: A list of indices representing the path to the desired value.
    :return: The value found at the specified path, or None if not found.
    """
    try:
        for index in indices:
            data = data[index]
        return data
    except (IndexError, TypeError):
        return None


def __set_nested_list_value(data, indices, value):
    """
    This function sets a value in a nested list using a list of indices.
    :param data: The list to modify.
    :param indices: A list of indices representing the path to the desired value.
    :param value: The value to set at the specified path.
    :return: The full updated list after modification.
    """
    print(f"data: {data}, indices: {indices}, value: {value}")
    wk_data = data
    if not isinstance(indices, (list, tuple)):
        indices = [indices]

    for index in indices[:-1]:
        while len(wk_data) <= index:
            wk_data.append([])
        if not isinstance(wk_data[index], list):
            wk_data[index] = []
        wk_data = wk_data[index]

    while len(wk_data) <= indices[-1]:
        wk_data.append(None)
    wk_data[indices[-1]] = value
    print(f"wk_data: {wk_data}")
    return data

# End of file common_helpers.py
