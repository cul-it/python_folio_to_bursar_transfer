# -*- coding: utf-8 -*-
import os
import logging
from src.shared.common_helpers import generate_file_name

logger = logging.getLogger(__name__)

class LocalExporter:
    """
    A class to handle file exports to an AWS S3 bucket.
    """

    def __init__(self, conf, template_processor):
        """
        Initialize the AwsBucketExporter with the bucket name and AWS credentials.
        :param env_key: The environment key used in the .env file to retrieve S3 bucket and credentials.
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
        processed_data = self.__template_processor.process_template(self.__conf)
        file_name = generate_file_name(self.__conf)
        logger.debug("Processed file name: %s", file_name)

        logger.info("Saving to local file system.")
        output_location = os.path.join(
            self.__script_dir, '../..',
            self.__conf['export_to'],
            file_name)
        with open(output_location, 'w') as file: #pylint: disable=unspecified-encoding
            file.write(processed_data)
        logger.debug("File saved locally at: %s", output_location)

# End of class LocalExporter
