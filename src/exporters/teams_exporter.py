"""
Model to send messages and files to a Teams channel.
This module uses the Teams SDK to send messages and upload files to a specified
Teams channel.
It is initialized with the environment key to retrieve the necessary credentials
and channel information.
"""
# pylint: disable=R0801
import logging
from src.shared.env_loader import EnvLoader
from src.shared.microsoft_connector import MicrosoftConnector

logger = logging.getLogger(__name__)


class TeamsExporter:
    """
    This class is responsible for sending messages to a Teams channel.
    """

    def __init__(self, conf, template_processor):
        """
        Initialize the TeamsMessenger class.
        :param conf: The configuration settings for the job.
        """

        
        connection_name = conf['connection_name']
        logger.info("Initializing SftpUploader with connection_name: %s", connection_name)
        self.__conf = conf
        self.__template_processor = template_processor

        logger.info("Initializing TeamsMessenger with connection_name: %s", connection_name)
        env = EnvLoader()


        logger.info("Initializing OneDriveUploader with connection_name: %s", connection_name)
        ms_connector = MicrosoftConnector(connection_name)
        self.__channel = ms_connector.get_teams_channel()
        logger.info(
            "TeamsMessenger initialized for channel: %s",
            self.__channel)
        
    def ship_it(self):
        """
        Send the processed message to the Teams channel.
        """
        logger.info("Processing export configuration: %s", self.__conf)
        message = self.__template_processor.process_template(
            self.__conf)
        self.__channel.send_message(message)

# End of class