"""File loader module for loading files from a given directory 
or from a S3 Bucket depending on the conf settings.
"""
import os
import yaml
from src.uploaders.aws_bucket import S3Uploader

class FileLoader: #pylint: disable=too-few-public-methods
    """
    This class is responsible for loading files from a given directory or from a S3 Bucket
    depending on the conf settings.
    """

    def __init__(self, conf):
        """
        Initialize the FileLoader class.
        :param conf: The configuration settings for the job.
        """
        self.__conf = conf
        self.__script_dir = os.path.dirname(__file__)

    def load_file(self, file_name, is_yaml=False):
        """
        Load a file based on the configuration settings.
        :param file_name: The name of the file to load.
        :return: The loaded file.
        """
        match self.__conf['type'].upper():
            case 'LOCAL':
                return self.__load_local_file(file_name, is_yaml)
            case 'S3':
                return self.__load_s3_file(file_name, is_yaml)
            case _:
                raise ValueError("Unsupported file type specified in configuration.")

    def __load_local_file(self, file_name, is_yaml):
        """
        Load a file from the local directory.
        :return: The loaded file.
        """
        file_path = os.path.join(self.__script_dir, self.__conf['location'], file_name)
        with open(file_path, 'r') as file: #pylint: disable=unspecified-encoding
            if is_yaml:
                return yaml.safe_load(file)
            return file.read()

    def __load_s3_file(self, file_name, is_yaml):
        """
        Load a file from an S3 bucket.
        :return: The loaded file.
        """
        # Implement S3 file loading logic here
        s3_uploader = S3Uploader(env_key=self.__conf['location'])
        if is_yaml:
            return yaml.safe_load(s3_uploader.download_file_as_variable(file_name))
        return s3_uploader.download_file_as_variable(file_name)

# END of file_loader.py
