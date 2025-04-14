# -*- coding: utf-8 -*-
import logging
from src.uploaders.aws_bucket import S3Uploader
from src.shared.common_helpers import generate_file_name

logger = logging.getLogger(__name__)

class AwsBucketExporter:
    """
    A class to handle file exports to an AWS S3 bucket.
    """

    def __init__(self, conf, template_processor):
        """
        Initialize the AwsBucketExporter with the bucket name and AWS credentials.
        :param env_key: The environment key used in the .env file to retrieve S3 bucket and credentials.
        """
        self.__s3_uploader = S3Uploader(env_key=conf['env_key'])
        self.__conf = conf
        self.__template_processor = template_processor

    def ship_it(self):
        """
        Uploads the processed data to the S3 bucket.
        :return: True if the upload was successful, False otherwise.
        """
        logger.info("Processing export configuration: %s", self.__conf)
        processed_data = self.__template_processor.process_template(self.__conf)
        file_name = generate_file_name(self.__conf)
        logger.debug("Processed file name: %s", file_name)

        logger.info("Uploading to S3 bucket.")
        self.__s3_uploader.upload_file_from_string(processed_data, file_name)
        return True

# End of class AwsBucketExporter
