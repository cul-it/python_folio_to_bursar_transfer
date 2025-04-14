#!/usr/bin/env python3
"""
SendToConnecter class
This class is responsible for sending data to various connectors.
It dynamically loads the appropriate connector class based on the configuration."""
# pylint: disable=R0801,too-few-public-methods
import logging
import importlib
from datetime import date
# Utilities
from src.shared.env_loader import EnvLoader
from src.shared.file_loader import FileLoader
from src.shared.template_processor import TemplateProcessor
from src.shared.common_helpers import pascal_to_camel_case

logger = logging.getLogger(__name__)


class SendToConnecter:
    """
    This class is responsible for sending data to various connectors.
    It dynamically loads the appropriate connector class based on the configuration.
    Private methods:
        - __init__: Initializes the SendToConnecter class.
        - __process_inline: Processes inline configuration.
        - __extract_data: Recursively searches for a key in a nested JSON object.
        - __ship_package: Ships the package to the specified connector.
    accepts:
        :param working_data: The data to be processed and sent to the connector.
        :param settings: The configuration settings for the connector.
    returns: None
    """

    def __init__(self, working_data, settings):
        """
        Initialize the SendToConnecter class.
        :param env_key: The environment key for the connector.
        """
        env = EnvLoader()
        template_conf = {
            "type": env.get(
                name="TEMPLATE_FILE_STORAGE_TYPE",
                default="local").upper(),
            "connector": env.get(
                name="TEMPLATE_FILE_STORAGE_CONNECTOR",
                default="local").upper(),
            "location": env.get(
                name="TEMPLATE_FILE_LOCATION",
                default="local")
        }
        file_loader = FileLoader(template_conf)
        self.__template_processor = TemplateProcessor(
            working_data, file_loader)
        logger.info(
            "ExportData initialized with configuration: %s",
            template_conf)

        if 'connectors' in settings and settings['connectors'] is not None:
            for conf in settings['connectors']:
                logger.info("Processing connectors configuration: %s", conf)

                if conf['mapping_type'].upper() == "TEMPLATE":
                    processed_data = self.__template_processor.process_template(
                        conf)
                elif conf['mapping_type'].upper() == "INLINE":
                    processed_data = self.__process_inline(conf)
                else:
                    logger.error(
                        "Invalid mapping type: %s",
                        conf['mapping_type'])
                    continue
                logger.debug("Processed data: %s", processed_data)

                self.__ship_package(conf, processed_data)

    def __process_inline(self, conf):
        """
        Process the inline configuration.
        :param conf: The configuration dictionary for the export.
        :return: The processed data as a string.
        """
        logger.info("Processing inline configuration: %s", conf)
        template_date = self.__template_processor.process_data(
            conf['field_data'])
        data_array = []
        for data in template_date["data"]:
            temp_array = {}
            for pattern in conf["field_mapping"]:
                match pattern["field_type"].upper():
                    case "DYNAMIC":
                        temp_array[pattern["field_name"]] = self.__extract_data(
                            pattern["field_source"], data)
                    case "STATIC":
                        temp_array[pattern["field_name"]
                                   ] = pattern["field_format"]
                    case "DATE":
                        temp_array[pattern["field_name"]] = date.today().strftime(
                            pattern["field_format"])
            data_array.append(temp_array)
        logger.debug("Processed inline data: %s", data_array)
        return data_array

    def __extract_data(self, key_path, data):
        """
        Recursively search for a key in a nested JSON object.
        :param data: The JSON object (dict or list).
        :param key_path: The dot-separated key path (e.g., "patron.externalSystemId").
        :return: The value of the key if found, otherwise None.
        """
        keys = key_path.split('.')
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return None
        return data

    def __ship_package(self, conf, data):
        """
        This function is responsible for shipping the package.
        Dynamically loads the connector class based on the connector_type.
        """
        logger.info("Shipping package with configuration: %s", conf)

        try:
            # Dynamically import the connector class
            module_name = f"src.connectors.{
                pascal_to_camel_case(
                    conf['connector_type'])}"
            class_name = conf['connector_type']
            module = importlib.import_module(module_name)
            connector_class = getattr(module, class_name)
        except (ModuleNotFoundError, AttributeError) as e:
            logger.error(
                "Failed to load connector class for type: %s. Error: %s",
                conf['connector_type'],
                e)
            raise ValueError(
                f"Invalid connector type: {
                    conf['connector_type']}"
                    ) from e

        # Initialize the connector instance
        connector_instance = connector_class(env_key=conf['env_key'])
        logger.info("Uploading to %s.", conf['connector_type'])

        # Define actions
        actions = {
            "CREATE": connector_instance.write_rows,
            "UPDATE": lambda data: connector_instance.update_rows(
                data=data, filter_string=conf["filter_filed"]),
            "DELETE": lambda data: connector_instance.delete_rows(
                data=data, filter_string=conf["filter_filed"])
        }

        # Get the action
        action = actions.get(conf['connector_action'].upper())
        if not action:
            logger.error("Invalid connector action for %s: %s",
                         conf['connector_type'], conf['connector_action'])
            raise ValueError("Invalid connector action")

        # Execute the action
        results = action(data)
        logger.debug("%s %s results: %s", conf['connector_type'],
                     conf['connector_action'], results)

# End of SendToConnecter class
