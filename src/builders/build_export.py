#!/usr/bin/env python3
import logging
import importlib
from pybars import Compiler
# Utilities
from src.shared.env_loader import EnvLoader
from src.shared.file_loader import FileLoader
from src.shared.template_processor import TemplateProcessor
from src.shared.common_helpers import pascal_to_camel_case

logger = logging.getLogger(__name__)


class ExportData:

    def __init__(self, working_data, settings):
        """
        Initialize the ExportData class.
        :param working_data: the three data files combined into a 
            single package for processing.
        :param settings: The configuration settings for the job.
        """
        logger.info("Initializing ExportData.")
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

        if 'export' in settings and settings['export'] is not None:
            for conf in settings['export']:
                self.__ship_package(conf)
                logger.info("Shipping package with configuration: %s", conf)
                
    def __ship_package(self, conf):
        """
        This function is responsible for shipping the package.
        Dynamically loads the exporter class based on the export_type.
        """
        logger.info("Shipping package with configuration: %s", conf)

        try:
            # Dynamically import the connector class
            module_name = f"src.exporters.{pascal_to_camel_case(conf['export_type'])}"
            class_name = conf['export_type']
            module = importlib.import_module(module_name)
            connector_class = getattr(module, class_name)
        except (ModuleNotFoundError, AttributeError) as e:
            logger.error("Failed to load connector class for type: %s. Error: %s",
                         conf['export_type'], e)
            raise ValueError(f"Invalid connector type: {conf['export_type']}")

        # Initialize the connector instance
        connector_instance = connector_class(conf=conf, template_processor=self.__template_processor)
        logger.info("Uploading to %s.", conf['export_type'])
        # Execute the action

        results = connector_instance.ship_it()
        logger.debug("%s results: %s", conf['export_type'],
                     results)


# End of class ExportData
