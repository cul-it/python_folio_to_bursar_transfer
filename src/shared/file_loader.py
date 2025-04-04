"""File loader module for loading files from a given directory 
or from an S3 Bucket depending on the conf settings.
"""
import os
import json
import logging
import yaml
from src.uploaders.aws_bucket import S3Uploader

logger = logging.getLogger(__name__)


class FileLoader:  # pylint: disable=too-few-public-methods
    """
    This class is responsible for loading files from a given directory or from an S3 Bucket
    depending on the conf settings.
    """

    def __init__(self, conf):
        """
        Initialize the FileLoader class.
        :param conf: The configuration settings for the job.
        """
        self.__conf = conf
        self.__script_dir = os.path.dirname(__file__)
        self.__is_json = False
        self.__is_yaml = False
        logger.info("FileLoader initialized with configuration: %s", conf)

    def load_file(self, file_name, is_yaml=False, is_json=False):
        """
        Load a file based on the configuration settings.
        :param file_name: The name of the file to load.
        :return: The loaded file.
        """
        self.__is_json = is_json
        self.__is_yaml = is_yaml
        logger.info("Loading file: %s (YAML: %s, JSON: %s)",
                    file_name, is_yaml, is_json)
        try:
            logger.debug("File type specified in configuration: %s",
                         self.__conf['type'])
            match self.__conf['type'].upper():
                case 'LOCAL':
                    logger.debug("Loading file from local directory.")
                    return self.__load_local_file(file_name)
                case 'S3':
                    logger.debug("Loading file from S3 bucket.")
                    return self.__load_s3_file(file_name)
                case _:
                    logger.error("Unsupported file type specified in configuration: %s",
                                 self.__conf['type'])
                    raise ValueError("Unsupported file type specified in configuration.")
        except Exception as e:
            logger.error("Error loading file '%s': %s",
                         file_name, e, exc_info=True)
            raise

    def __load_local_file(self, file_name):
        """
        Load a file from the local directory.
        :return: The loaded file.
        """
        file_path = os.path.join(self.__script_dir, self.__conf['location'], file_name)
        logger.debug("Resolved local file path: %s",
                     file_path)
        if not os.path.exists(file_path):
            logger.error("File not found: %s", file_path)
            raise FileNotFoundError(f"The file '{file_path}' does not exist.")
        try:
            with open(file_path, 'r') as file:  # pylint: disable=unspecified-encoding
                logger.info("Successfully opened local file: %s",
                            file_path)
                if self.__is_yaml:
                    logger.debug("Parsing file as YAML.")
                    return yaml.safe_load(file)
                if self.__is_json:
                    logger.debug("Parsing file as JSON.")
                    return json.load(file)
                return file.read()
        except Exception as e:
            logger.error("Error reading local file '%s': %s",
                         file_path, e, exc_info=True)
            raise

    def __load_s3_file(self, file_name):
        """
        Load a file from an S3 bucket.
        :return: The loaded file.
        """
        logger.debug("Initializing S3Uploader with location: %s",
                     self.__conf['location'])
        s3_uploader = S3Uploader(env_key=self.__conf['location'])
        try:
            file_content = s3_uploader.download_file_as_variable(file_name)
            logger.info("Successfully downloaded file from S3: %s",
                        file_name)
            if self.__is_yaml:
                logger.debug("Parsing S3 file as YAML.")
                return yaml.safe_load(file_content)
            if self.__is_json:
                logger.debug("Parsing S3 file as JSON.")
                return json.loads(file_content)
            return file_content
        except Exception as e:
            logger.error("Error loading file from S3 '%s': %s",
                         file_name, e, exc_info=True)
            raise

# END of file_loader.py
