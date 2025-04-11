"""
AWS S3 Uploader Class
This class provides methods to upload files to an AWS S3 bucket.
It supports uploading files from a string or a local file path.
"""
import tempfile
import io
import logging
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from src.shared.env_loader import EnvLoader

logger = logging.getLogger(__name__)


class S3Uploader:
    """
    A class to handle file uploads to an AWS S3 bucket.
    """

    def __init__(self, env_key):
        """
        Initialize the S3Uploader with the bucket name and AWS credentials.
        :param __bucket_name: The name of the S3 bucket.
        """
        logger.info("Initializing S3Uploader with env_key: %s", env_key)
        self.__bucket_name = EnvLoader().get(name=f"{env_key}_BUCKET")
        if EnvLoader().get(name=f"{env_key}_SECURE"):
            self.__s3_client = boto3.client(
                "s3", aws_access_key_id=EnvLoader().get(
                    name=f"{env_key}_ACCESS_KEY_ID"), aws_secret_access_key=EnvLoader().get(
                    name=f"{env_key}_SECRET_ACCESS_KEY"), region_name=EnvLoader().get(
                    name=f"{env_key}_REGION", default="us-east-1"))
        else:
            self.__s3_client = boto3.client("s3")
        logger.info(
            "S3Uploader initialized for bucket: %s",
            self.__bucket_name)

    def upload_file_from_string(self, file_content, s3_key):
        """
        Upload a string as a file to the S3 bucket.
        :param file_content: The content of the file as a string.
        :param s3_key: The key (path) in the S3 bucket where the file will be stored.
        :return: The S3 URL of the uploaded file.
        """
        logger.info("Uploading file from string to S3 with key: %s", s3_key)
        try:
            self.__s3_client.put_object(
                Bucket=self.__bucket_name,
                Key=s3_key,
                Body=file_content)
            s3_url = f"https://{self.__bucket_name}.s3.amazonaws.com/{s3_key}"
            logger.info("File uploaded successfully to S3: %s", s3_url)
            return s3_url
        except NoCredentialsError as exc:
            logger.error("AWS credentials not found.", exc_info=True)
            # pylint: disable-next=too-many-function-args
            raise NoCredentialsError(
                "Error: AWS credentials not found.") from exc
        except PartialCredentialsError as exc:
            logger.error("Incomplete AWS credentials.", exc_info=True)
            # pylint: disable-next=too-many-function-args
            raise PartialCredentialsError(
                "Incomplete AWS credentials.") from exc
        except Exception as e:
            logger.error(
                "An error occurred while uploading the file: %s",
                e,
                exc_info=True)
            # pylint: disable-next=too-many-function-args
            raise RuntimeError(f"An error occurred: {e}") from e

    def upload_file(self, file_path, s3_key):
        """
        Upload a file to the S3 bucket.
        :param file_path: The local path to the file to upload.
        :param s3_key: The key (path) in the S3 bucket where the file will be stored.
        :return: The S3 URL of the uploaded file.
        """
        logger.info(
            "Uploading file to S3 from path: %s with key: %s",
            file_path,
            s3_key)
        try:
            self.__s3_client.upload_file(file_path, self.__bucket_name, s3_key)
            s3_url = f"https://{self.__bucket_name}.s3.amazonaws.com/{s3_key}"
            logger.info("File uploaded successfully to S3: %s", s3_url)
            return s3_url
        except FileNotFoundError as exc:
            logger.error("File not found: %s", file_path, exc_info=True)
            raise FileNotFoundError(
                f"Error: The file {file_path} was not found.") from exc
        except NoCredentialsError as exc:
            logger.error("AWS credentials not found.", exc_info=True)
            # pylint: disable-next=too-many-function-args
            raise NoCredentialsError(
                "Error: AWS credentials not found.") from exc
        except PartialCredentialsError as exc:
            # pylint: disable-next=too-many-function-args
            raise PartialCredentialsError(
                "Error: Incomplete AWS credentials.") from exc
        except Exception as e:
            logger.error(
                "An error occurred while uploading the file: %s",
                e,
                exc_info=True)
            raise RuntimeError(f"An error occurred: {e}") from e

    def list_files(self):
        """
        List all files in the S3 bucket.
        :return: A list of file keys in the bucket.
        """
        logger.info("Listing files in S3 bucket: %s", self.__bucket_name)
        try:
            response = self.__s3_client.list_objects_v2(
                Bucket=self.__bucket_name)
            if "Contents" in response:
                files = [item["Key"] for item in response["Contents"]]
                logger.info("Files listed successfully: %s", files)
                return files
            logger.info("No files found in the bucket.")
            return []
        except Exception as e:
            logger.error(
                "An error occurred while listing files: %s",
                e,
                exc_info=True)
            raise RuntimeError(
                f"An error occurred while listing files: {e}") from e

    def delete_file(self, s3_key):
        """
        Delete a file from the S3 bucket.
        :param s3_key: The key (path) of the file to delete in the S3 bucket.
        """
        logger.info("Deleting file from S3 with key: %s", s3_key)
        try:
            self.__s3_client.delete_object(
                Bucket=self.__bucket_name, Key=s3_key)
            logger.info("File deleted successfully: %s", s3_key)
            return {"message": f"File {s3_key} deleted successfully."}
        except Exception as e:
            logger.error(
                "An error occurred while deleting the file: %s",
                e,
                exc_info=True)
            raise RuntimeError(
                f"An error occurred while deleting the file: {e}") from e

    def download_file_to_temp(self, s3_key):
        """
        Download a file from the S3 bucket to a temporary location.
        :param s3_key: The key (path) of the file in the S3 bucket.
        :return: The path to the temporary file.
        """
        logger.info(
            "Downloading file from S3 to temporary location with key: %s",
            s3_key)
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(b"")
            temp_file_path = temp_file.name
            temp_file.close()
            self.__s3_client.download_file(
                self.__bucket_name, s3_key, temp_file_path)
            logger.info(
                "File downloaded successfully to temporary location: %s",
                temp_file_path)
            return temp_file_path
        except Exception as e:
            logger.error(
                "An error occurred while downloading the file: %s",
                e,
                exc_info=True)
            raise RuntimeError(
                f"An error occurred while downloading the file: {e}") from e

    def download_file_as_variable(self, s3_key):
        """
        Download a file from the S3 bucket and return its content as a variable.
        :param s3_key: The key (path) of the file in the S3 bucket.
        :return: The content of the file as a string.
        """
        logger.info(
            "Downloading file from S3 as variable with key: %s",
            s3_key)
        try:
            file_obj = io.BytesIO()
            self.__s3_client.download_fileobj(
                self.__bucket_name, s3_key, file_obj)
            file_obj.seek(0)
            file_content = file_obj.read().decode('utf-8')
            logger.info("File downloaded successfully as variable.")
            return file_content
        except Exception as e:
            logger.error(
                "An error occurred while downloading the file: %s",
                e,
                exc_info=True)
            raise RuntimeError(
                f"An error occurred while downloading the file: {e}") from e

# End of class S3Uploader
