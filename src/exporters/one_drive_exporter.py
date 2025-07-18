"""OneDrive Exporter Module
This module provides functionality to upload files to OneDrive using the O365 library.
"""
import io
import logging
from io import BytesIO
from src.shared.microsoft_connector import MicrosoftConnector
from src.shared.template_processor import TemplateProcessor

logger = logging.getLogger(__name__)

class OneDriveExporter:
    """
    A class to handle uploading files to OneDrive using the O365 library.
    """

    def __init__(self, conf, template_processor):
        """
        Initialize the OneDriveUploader class.
        :param client_id: The client ID of your Azure application.
        :param client_secret: The client secret of your Azure application.
        :param token_path: The path to store the token file.
        :param token_filename: The name of the token file.
        """
        logger.info("Initializing OneDriveUploader.")
        connection_name = conf['connection_name']
        self.__conf = conf
        self.__template_processor = template_processor

        logger.info("Initializing OneDriveUploader with connection_name: %s", connection_name)
        ms_connector = MicrosoftConnector(connection_name)
        self.__storage = ms_connector.get_new_storage()
        self.__processor = TemplateProcessor()

        folder_name = self.__processor.process_string_no_template(
            self.__conf.get('export_to', None)
            )
        logger.info("Processing export_to folder name: %s", folder_name)
        self.__storage = ms_connector.walk_the_tree(folder_name, self.__storage, 'onedrive')
        logger.info("OneDriveUploader initialized successfully.")

    def ship_it(self):
        """
        Upload a file-like object to OneDrive.
        :param file_stream: The file-like object to upload.
        :param file_name: The name of the file to upload.
        :param folder_name: The name of the folder to upload the file to. 
        If None, uploads to the root folder.
        :return: The uploaded file object.
        """
        logger.info("Processing export configuration: %s", self.__conf)
        processed_data = self.__template_processor.process_template(
            self.__conf)
        
        processor = TemplateProcessor()
        file_name = processor.process_string_no_template(
            self.__conf.get('file_name', None)
        )
        logger.debug("Processed file name: %s", file_name)


        logger.info("Uploading file '%s' to OneDrive.", file_name)

        # Ensure processed_data is a string and upload as a BytesIO stream
        data_stream = io.StringIO(processed_data)
        uploaded_file = self.__storage.upload_file(item='na', stream=data_stream, stream_size=len(processed_data), item_name=file_name)
        logger.info("File '%s' uploaded successfully to OneDrive.", file_name)
        return uploaded_file
    
# end of class OneDriveExporter
