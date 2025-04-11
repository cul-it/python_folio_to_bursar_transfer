"""
This script provides a function to upload files to an SFTP server using either
a private key or username and password authentication. It handles errors
and provides feedback on the upload process.
"""
import io
import logging
from base64 import decodebytes
import paramiko.hostkeys
import paramiko
# pylint: disable-next=unused-import
from paramiko import RSAKey, Ed25519Key
from src.uploaders.aws_bucket import S3Uploader
from src.shared.env_loader import EnvLoader

logger = logging.getLogger(__name__)


class SftpUploader:
    """
    A class to handle SFTP file uploads.
    """

    # pylint: disable-next=too-many-branches, too-many-statements
    def __init__(self, env_key):
        """
        Transfer a file to an SFTP server using either a certificate (private key) or
        username and password.
        :param env_key: The environment key used in the .env file to retrieve S3 bucket and FTP.
        :return: None
        """
        logger.info("Initializing SftpUploader with env_key: %s", env_key)
        self.__ftp_remote_path = EnvLoader().get(name=f"{env_key}_REMOTE_PATH")

        # Create an SSH client
        self.__ssh_client = paramiko.SSHClient()

        # See if the user wants to use a private key or password
        if EnvLoader().get(
                name=f"{env_key}_PASSWORD").upper() == 'CERTIFICATE':
            logger.info("Using certificate for authentication.")
            if EnvLoader().get(
                    name=f"{env_key}_CERTIFICATE_LOCATION").upper() == 'LOCAL':
                logger.info("Loading certificate from local file system.")
                with open(
                    EnvLoader().get(name=f"{env_key}_CERTIFICATE_PATH"),
                    'r', encoding='utf-8'
                ) as file:
                    certificate = file.read()
            elif 'AWS' in EnvLoader().get(name=f"{env_key}_CERTIFICATE_LOCATION").upper():
                logger.info("Loading certificate from AWS S3.")
                s3_uploader = S3Uploader(f"{env_key}_CERTIFICATE_LOCATION")
                certificate = s3_uploader.download_file_as_variable(
                    f"{env_key}_CERTIFICATE_PATH")
            if EnvLoader().get(name=f"{env_key}_KEY_TYPE").upper() == 'RSA':
                certificate = paramiko.RSAKey.from_private_key(
                    io.StringIO(certificate))
            else:
                certificate = paramiko.Ed25519Key.from_private_key(
                    io.StringIO(certificate))
        else:
            logger.info("Using password for authentication.")

        # See if a known_hosts file is provided
        # If not, we will use the AutoAddPolicy
        # If the known_hosts file is provided, we will use the RejectPolicy
        # to reject any unknown hosts
        if not EnvLoader().get(name=f"{env_key}_KNOW_HOSTS_LOCATION"):
            logger.info("No known_hosts file provided. Using AutoAddPolicy.")
            self.__ssh_client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())
        else:
            logger.info("Loading known_hosts file.")
            known_hosts = None
            if EnvLoader().get(
                    name=f"{env_key}_KNOW_HOSTS_LOCATION").upper() == 'LOCAL':
                logger.info("Loading known_hosts from local file system.")
                with open(EnvLoader().get(
                    name=f"{env_key}_KNOW_HOSTS_PATH"),
                    'r', encoding='utf-8'
                ) as file:
                    known_hosts = file.read()
            elif 'AWS' in EnvLoader().get(name=f"{env_key}_KNOW_HOSTS_LOCATION").upper():
                logger.info("Loading known_hosts from AWS S3.")
                s3_uploader = S3Uploader(EnvLoader().get(
                    name=f"{env_key}_KNOW_HOSTS_LOCATION").upper())
                known_hosts = s3_uploader.download_file_as_variable(
                    EnvLoader().get(name=f"{env_key}_KNOW_HOSTS_PATH")
                )

            if not known_hosts:
                logger.error("The known_hosts file could not be loaded.")
                raise ValueError("The known_hosts file could not be loaded.")

            # Load the known_hosts file into the reject policy
            # and set the policy to reject any unknown hosts
            # known host key
            hosts_lines = known_hosts.splitlines()
            for line in hosts_lines:
                line_values = line.split()
                know_host_key = line_values[2]
                key_obj = RSAKey(data=decodebytes(know_host_key.encode()))
                self.__ssh_client.get_host_keys().add(
                    hostname=line_values[0],
                    keytype=line_values[1],
                    key=key_obj
                )
            self.__ssh_client.set_missing_host_key_policy(
                paramiko.RejectPolicy())

        # Create a connection to the SFTP server
        if EnvLoader().get(
                name=f"{env_key}_PASSWORD").upper() == 'CERTIFICATE':
            logger.info("Connecting to SFTP server using certificate.")
            self.__ssh_client.connect(
                hostname=EnvLoader().get(name=f"{env_key}_HOST"),
                port=EnvLoader().get(name=f"{env_key}_PORT"),
                username=EnvLoader().get(name=f"{env_key}_USER"),
                pkey=certificate
            )
        else:
            logger.info("Connecting to SFTP server using password.")
            self.__ssh_client.connect(
                hostname=EnvLoader().get(name=f"{env_key}_HOST"),
                port=EnvLoader().get(name=f"{env_key}_PORT"),
                username=EnvLoader().get(name=f"{env_key}_USER"),
                password=EnvLoader().get(name=f"{env_key}_PASSWORD")
            )
        self.__sftp = self.__ssh_client.open_sftp()
        logger.info("SftpUploader initialized successfully.")

    def upload_file(self, file_contents, file_name):
        """
        Upload a file to the SFTP server.
        :param file_contents: The content of the file as a string.
        :param file_name: The name of the file to be uploaded.
        :return: None
        """
        logger.info("Uploading file to SFTP server: %s", file_name)
        try:
            file_obj = io.BytesIO(file_contents.encode('utf-8'))
            remote_path = f"{self.__ftp_remote_path}/{file_name}"
            self.__sftp.putfo(file_obj, remote_path)
            logger.info("File uploaded successfully to: %s", remote_path)
        except Exception as e:
            logger.error("Failed to upload file: %s", e, exc_info=True)
            raise

    def close(self):
        """
        Close the SFTP session and SSH client.
        """
        logger.info("Closing SFTP session and SSH client.")
        try:
            self.__sftp.close()
            self.__ssh_client.close()
            logger.info("SFTP session and SSH client closed successfully.")
        except Exception as e:
            logger.error(
                "Failed to close SFTP session or SSH client: %s",
                e,
                exc_info=True)
            raise
        return True
# End of the SftpUploader class
