# -*- coding: utf-8 -*-
"""
# AWS S3 Exporter"""
# pylint: disable=R0801,too-few-public-methods
import logging
from src.shared.template_processor import TemplateProcessor
from src.uploaders.aws_bucket import S3Uploader

logger = logging.getLogger(__name__)


class AwsBucketExporter:
    """
    A class to handle file exports to an AWS S3 bucket.
    """

    def __init__(self, conf, template_processor):
        """
        Initialize the AwsBucketExporter with the bucket name and AWS credentials.
        :param connection_name: The environment key used in the .env file to retrieve S3 
            bucket and credentials.
        """
        self.__s3_uploader = S3Uploader(connection_name=conf['connection_name'])
        self.__conf = conf
        self.__template_processor = template_processor

    def ship_it(self):
        """
        Uploads the processed data to the S3 bucket.
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

        logger.info("Uploading to S3 bucket.")
        self.__s3_uploader.upload_file_from_string(processed_data, file_name)
        return True

# End of class AwsBucketExporter
