"""
yaml_loader.py - used to load yaml files with support for includes and variable substitution.
"""
import re
import logging
from src.shared.env_loader import EnvLoader
from src.shared.file_loader import FileLoader

logger = logging.getLogger(__name__)

# pylint: disable-next=too-few-public-methods
class YamlLoader:
    """
    This class is used to load YAML files with support for includes and variable substitution.
    It allows for the inclusion of other YAML files and the replacement of variables in the
    YAML data using a dictionary of variables.
    exposed methods:
        load_config(file_path: str) -> dict: Loads the YAML file and processes it.
    private methods:
        __load_yaml_with_variables(data: dict, variables: dict) -> dict: Replaces variables 
            in the YAML data.
    """
    def __init__(self):
        logger.info("Initializing YamlLoader.")
        env = EnvLoader()
        conf = {
            "type": env.get(name="CONFIG_FILE_STORAGE_TYPE", default="local").upper(),
            "connector": env.get(name="CONFIG_FILE_STORAGE_CONNECTOR", default="local").upper(),
            "location": env.get(name="CONFIG_FILE_LOCATION", default="local")
        }
        self.__file_loader = FileLoader(conf)
        logger.info("YamlLoader initialized with configuration: %s", conf)

    def __load_yaml_with_variables(self, data, variables):
        """
        Replace variables in the given YAML data using the provided variables dictionary.
        :param data: The YAML data to process.
        :param variables: A dictionary of variables to use for substitution.
        :return: The processed YAML data with variables replaced.
        """
        logger.debug("Replacing variables in YAML data with variables: %s",
                     variables)

        def replace_variables(obj):
            if isinstance(obj, str):
                return re.sub(
                    r"\$\{(\w+)\}",
                    lambda match: str(
                        variables.get(
                            match.group(1),
                            match.group(0))),
                    obj)
            if isinstance(obj, list):
                return [replace_variables(item) for item in obj]
            if isinstance(obj, dict):
                return {key: replace_variables(value)
                        for key, value in obj.items()}
            return obj

        processed_data = replace_variables(data)
        logger.debug("Variable replacement complete.")
        return processed_data

    def load_config(self, file_path):
        """
        Load a YAML file with support for includes and variable substitution.
        :param file_path: The path to the YAML file to load.
        :return: The processed YAML data as a dictionary.
        """
        logger.info("Loading YAML configuration from file: %s", file_path)
        main_data = self.__file_loader.load_file(file_path, is_yaml=True)

        # Extract variables from the main file
        global_variables = main_data.get("vars", [])
        logger.debug("Extracted global variables: %s", global_variables)
        main_data = self.__load_yaml_with_variables(
            main_data, global_variables)

        # Process included files
        if "include" in main_data and isinstance(main_data["include"], list):
            logger.info("Processing included files: %s", main_data["include"])
            for include_sub_file in main_data["include"]:
                included_data = self.__file_loader.load_file(include_sub_file, is_yaml=True)
                logger.debug("Loaded included file: %s", include_sub_file)

                # Extract variables from the included file
                local_variables = included_data.get("vars", [])
                logger.debug("Extracted local variables from included file: %s", local_variables)
                all_variables = {
                    key: value for d in global_variables + local_variables for key,
                    value in d.items()
                }

                # Replace variables in the included file
                included_data = self.__load_yaml_with_variables(
                    included_data, all_variables)

                # Remove the "vars" section from the included data after processing
                included_data.pop("vars", None)

                # Merge the included data into the main data
                if isinstance(included_data, dict):
                    main_data.update(included_data)
                    logger.debug("Merged included file data into main data.")
                else:
                    logger.error("Included file %s must contain a dictionary at the top level.",
                                 include_sub_file)
                    raise ValueError(
                        "Included file {include_sub_file} must contain a " \
                        "dictionary at the top level."
                        )
            logger.info("All included files processed successfully.")
        # Remove the "include" key from the main data after processing
        main_data.pop("include", None)
        logger.info("YAML configuration loaded successfully.")
        return main_data
