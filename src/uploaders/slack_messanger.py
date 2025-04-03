import os
from io import BytesIO
from slack_sdk import WebClient
from src.shared.env_loader import EnvLoader

class SlackMessenger:
    """
    This class is responsible for sending messages to a Slack channel.
    """
    def __init__(self, env_key):
        """
        Initialize the SlackMessenger class.
        :param conf: The configuration settings for the job.
        """
        env = EnvLoader()

        # Retrieve environment variables
        self.__channel = env.get(name=f"{env_key}_CHANNEL")
        self.__client = WebClient(token=env.get(name=f"{env_key}_TOKEN"))

    def send_message(self, message=None, header=None):
        """
        Send a message to the Slack channel.
        :param message: The message to send.
        :param header: The header of the message.
        """


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
        # Initialize Slack client
        response = self.__client.chat_postMessage(
            channel=self.__channel,
            text=message,
            blocks=blocks
        )
        print("Message sent successfully:", response["message"]["text"])

    def upload_file(self, file_stream, title, comment=None):
        """
        Upload a file to the Slack channel.
        :param file_stream: The file stream to upload.
        :param title: The title of the file.
        """
        response = self.__client.files_upload_v2(
            filename=title,
            content=file_stream,
            title=f"File uploaded {title}",
            channel=self.__channel,
            initial_comment=comment,
        )
        print("File uploaded successfully:", response["file"]["name"])