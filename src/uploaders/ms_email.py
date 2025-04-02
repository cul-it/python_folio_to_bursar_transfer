"""Python script to send emails using Microsoft Graph API with OAuth2 authentication."""
import os
from io import BytesIO
from dotenv import load_dotenv
from O365 import Account, FileSystemTokenBackend
from O365.utils import AWSS3Backend
from src.uploaders.o365_backends import CustomAwsS3Backend



class MSEmail:
    """
    A class to handle sending emails using Microsoft Graph API.
    """

    def __init__(self, env_key):
        """
        Initializes the MSEmail class with client ID, client secret, and tenant ID.
        """
        # Load environment variables from the .env file
        load_dotenv()

        credentials = (
            os.getenv(
                f"{env_key}_CLIENT_ID"), os.getenv(
                f"{env_key}_CERTIFICATE_VALUE"))

        match os.getenv(f"{env_key}_AUTH_LOCATION").upper():
            case 'LOCAL':
                print('Loading local credentials...')
                # Local certificate from the local file system
                token_backend = FileSystemTokenBackend(
                    token_path=os.getenv(f"{env_key}_AUTH_PATH"),
                    token_filename=f"{env_key}_TOKEN.json"
                )
            case 'S3_SECURE':
                # AWS certificate from S3
                token_backend = CustomAwsS3Backend(
                    env_key=os.getenv(f"{env_key}_AUTH_PATH"),
                    filename='f"{env_key}_TOKEN.json'
                )
            case 'S3':
                token_backend = AWSS3Backend(
                    bucket_name=os.getenv(f"{env_key}_AUTH_PATH"),
                    filename=f"{env_key}_TOKEN.json"
                )
            case _:
                raise ValueError(
                    "Invalid AUTH_LOCATION. Must be 'LOCAL' or 'AWS'.")

        # Initialize the account with the credentials and token backend
        # the default protocol will be Microsoft Graph
        # the default authentication method will be "on behalf of a user"
        self.__account = Account(credentials, token_backend=token_backend)
        if self.__account.is_authenticated:
            print('Authenticated!')

        self.__message = self.__account.new_message()

    def build_message(self, to, subject, body):
        """
        Creates a new message object.
        """
        if ';' in to:
            to = to.split(';')
        elif ',' in to:
            to = to.split(',')
        elif ' ' in to:
            to = to.split(' ')
        else:
            to = [to]

        new_body = f"""<html><body>
                     {body.replace('\n', '<br>')}
                </body></html>"""
        self.__message.to.add(to)
        self.__message.subject = subject
        self.__message.body = new_body

        return True

    def send_message(self):
        """
        Authenticates the account using the provided credentials.
        """
        self.__message.send()
        return True

    def add_attachment(self, file_data, filename):
        """
        Adds an attachment to the email message.
        :param file_data: The attachment body to add.
        :param filename: The name of the file to attach.
        """
        data = BytesIO()
        data.write(file_data.encode("utf-8"))
        data.seek(0)
        attachment = (data, filename)
        self.__message.attachments.add([attachment])

        return True

# End of the class MSEmail
