"""
Model to send messages and files to a Slack channel.
This module uses the Slack SDK to send messages and upload files to a specified 
Slack channel.
It is initialized with the environment key to retrieve the necessary credentials 
and channel information.
"""
import logging
from slack_sdk import WebClient
from src.shared.env_loader import EnvLoader

logger = logging.getLogger(__name__)


class SlackMessenger:
    """
    This class is responsible for sending messages to a Slack channel.
    """
    def __init__(self, env_key):
        """
        Initialize the SlackMessenger class.
        :param conf: The configuration settings for the job.
        """
        logger.info("Initializing SlackMessenger with env_key: %s", env_key)
        env = EnvLoader()

        # Retrieve environment variables
        self.__channel = env.get(name=f"{env_key}_CHANNEL")
        self.__client = WebClient(token=env.get(name=f"{env_key}_TOKEN"))
        logger.info("SlackMessenger initialized for channel: %s", self.__channel)

    def send_message(self, message=None, header=None):
        """
        Send a message to the Slack channel.
        :param message: The message to send.
        :param header: The header of the message.
        """
        logger.info("Sending message to Slack channel: %s", self.__channel)
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": header
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]
        try:
            response = self.__client.chat_postMessage(
                channel=self.__channel,
                text=message,
                blocks=blocks
            )
            logger.info("Message sent successfully: %s", response["message"]["text"])
        except Exception as e:
            logger.error("Failed to send message to Slack: %s", e, exc_info=True)
            raise

    def upload_file(self, file_stream, title, comment=None):
        """
        Upload a file to the Slack channel.
        :param file_stream: The file stream to upload.
        :param title: The title of the file.
        """
        logger.info("Uploading file to Slack channel: %s with title: %s", self.__channel, title)
        try:
            response = self.__client.files_upload_v2(
                filename=title,
                content=file_stream,
                title=f"File uploaded {title}",
                channel=self.__channel,
                initial_comment=comment,
            )
            logger.info("File uploaded successfully: %s", response["file"]["name"])
        except Exception as e:
            logger.error("Failed to upload file to Slack: %s", e, exc_info=True)
            raise
# End of class
