# -*- coding: utf-8 -*-
"""
Local Exporter Module
This module provides functionality to export data to the local file system.
"""
# pylint: disable=R0801,too-few-public-methods
import os
import logging

from src.shared.template_processor import TemplateProcessor

logger = logging.getLogger(__name__)


class LocalExporter:
    """
    A class to handle file exports to an AWS S3 bucket.
    """

    def __init__(self, conf, template_processor):
        """
        Initialize the LocalExporter class.
        :param conf: Configuration dictionary for the export.
        :param template_processor: Template processor for processing templates.
        """
        self.__script_dir = os.path.dirname(__file__)
        self.__conf = conf
        self.__template_processor = template_processor

    def ship_it(self):
        """
        Saves the processed data to the local file system.
        :return: True if the upload was successful, False otherwise.
        """
        logger.info("Processing export configuration: %s", self.__conf)
        processed_data = self.__template_processor.process_template(
            self.__conf)
        
        processor = TemplateProcessor()
        file_name = processor.process_string_no_template(
            self.__conf.get('file_name', None)
            )
        logger.debug("Processed file name: %s", file_name)

        logger.info("Saving to local file system.")
        output_location = os.path.join(
            self.__script_dir, '../..',
            self.__conf['export_to'],
            file_name)
        with open(output_location, 'w') as file:  # pylint: disable=unspecified-encoding
            file.write(processed_data)
        logger.debug("File saved locally at: %s", output_location)

# End of class LocalExporter
