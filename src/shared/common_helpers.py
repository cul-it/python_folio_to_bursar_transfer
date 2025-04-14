"""
common_helpers.py
This module contains utility functions
methods:
  pascal_to_camel_case: Converts a PascalCase string to camelCase.
"""

def pascal_to_camel_case(pascal_string):
    """Converts a PascalCase string to camelCase.
    
    Args:
        pascal_string: The PascalCase string to convert.
    
    Returns:
        The camelCase version of the string.
    """
    return pascal_string[0].lower() + pascal_string[1:]

# End of file common_helpers.py
