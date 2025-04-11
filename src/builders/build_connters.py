#!/usr/bin/env python3
import os
import json
import logging
from datetime import date
# Utilities
from src.shared.env_loader import EnvLoader
from src.shared.file_loader import FileLoader
from src.shared.template_processor import TemplateProcessor
#Uploaders / Connectors
from src.uploaders.air_table import AirTableImporter

logger = logging.getLogger(__name__)

class SendToConnecter:

    def __init__(self, working_data, settings):
        """
        Initialize the SendToConnecter class.
        :param env_key: The environment key for the connector.
        """
        self.__script_dir = os.path.dirname(__file__)
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
        self.__template_processor = TemplateProcessor(working_data, file_loader)
        logger.info("ExportData initialized with configuration: %s", template_conf)

        if 'connectors' in settings and settings['connectors'] is not None:
            for conf in settings['connectors']:
                logger.info("Processing connectors configuration: %s", conf)

                if conf['mapping_type'].upper() == "TEMPLATE":
                    processed_data = self.__template_processor.process_template(conf)
                elif conf['mapping_type'].upper() == "INLINE":
                    processed_data = self.__process_inline(conf)
                else:
                    logger.error("Invalid mapping type: %s", conf['mapping_type'])
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
        template_date = self.__template_processor.process_data(conf['field_data'])
        data_array = []
        for data in template_date["data"]:
            temp_array = {}
            for pattern in conf["field_mapping"]:
                match pattern["field_type"].upper():
                    case "DYNAMIC":
                        temp_array[pattern["field_name"]] = self.__extract_data(
                                pattern["field_source"], data
                            )
                    case "STATIC":
                        temp_array[pattern["field_name"]] = pattern["field_format"]
                    case "DATE":
                        temp_array[pattern["field_name"]] = date.today().strftime(
                                pattern["field_format"]
                            )
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
        The location is based on the configuration file.
        """
        logger.info("Shipping package with configuration: %s", conf)
        match conf['connector_type'].upper():
            case 'AIRTABLE':
                air = AirTableImporter(env_key=conf['env_key'])
                logger.info("Uploading to AirTable.")
                if conf['connector_action'].upper() == "CREATE":
                    results = air.write_rows(data=data)
                elif conf['connector_action'].upper() == "UPDATE":
                    results = air.update_rows(data=data, filter_string=conf["filter_filed"])
                elif conf['connector_action'].upper() == "DELETE":
                    results = air.delete_rows(data=data, filter_string=conf["filter_filed"])
                else:
                    logger.error("Invalid connector action for AirTable: %s", conf['connector_action'])
                    raise ValueError("Invalid connector action for AirTable")

            case _:
                logger.error("Invalid export type for shipping package: %s", conf['export_type'])
                raise ValueError("Invalid export type for shipping package")