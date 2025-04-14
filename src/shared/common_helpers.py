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

# End of file common_helpers.py
