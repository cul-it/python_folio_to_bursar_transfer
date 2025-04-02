"""
AWS S3 Uploader Class
This class provides methods to upload files to an AWS S3 bucket.
It supports uploading files from a string or a local file path.
"""
import os
import tempfile
import io
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from dotenv import load_dotenv


class S3Uploader:
    """
    A class to handle file uploads to an AWS S3 bucket.
    """

    def __init__(self, env_key, secure=False):
        """
        Initialize the S3Uploader with the bucket name and AWS credentials.
        :param __bucket_name: The name of the S3 bucket.
        """
        # Load environment variables from the .env file
        load_dotenv()

        self.__bucket_name = os.getenv(f"{env_key}_BUCKET")
        if secure:
            self.__s3_client = boto3.client(
                "s3",
                aws_access_key_id=os.getenv(f"{env_key}_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv(f"{env_key}_SECRET_ACCESS_KEY"),
                region_name=os.getenv(f"{env_key}_REGION", "us-east-1")
            )
        else:
            self.__s3_client = boto3.client("s3")

    def upload_file_from_string(self, file_content, s3_key):
        """
        Upload a string as a file to the S3 bucket.
        :param file_content: The content of the file as a string.
        :param s3_key: The key (path) in the S3 bucket where the file will be stored.
        :return: The S3 URL of the uploaded file.
        """
        try:
            self.__s3_client.put_object(
                Bucket=self.__bucket_name,
                Key=s3_key,
                Body=file_content)
            s3_url = f"https://{self.__bucket_name}.s3.amazonaws.com/{s3_key}"
            return s3_url
        except NoCredentialsError as exc:
            # pylint: disable-next=too-many-function-args
            raise NoCredentialsError(
                "Error: AWS credentials not found.") from exc
        except PartialCredentialsError as exc:
            # pylint: disable-next=too-many-function-args
            raise PartialCredentialsError(
                "Incomplete AWS credentials.") from exc
        except Exception as e:
            raise RuntimeError(f"An error occurred: {e}") from e

    def upload_file(self, file_path, s3_key):
        """
        Upload a file to the S3 bucket.
        :param file_path: The local path to the file to upload.
        :param s3_key: The key (path) in the S3 bucket where the file will be stored.
        :return: The S3 URL of the uploaded file.
        """
        try:
            self.__s3_client.upload_file(file_path, self.__bucket_name, s3_key)
            s3_url = f"https://{self.__bucket_name}.s3.amazonaws.com/{s3_key}"
            return s3_url
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Error: The file {file_path} was not found.") from exc
        except NoCredentialsError as exc:
            # pylint: disable-next=too-many-function-args
            raise NoCredentialsError(
                "Error: AWS credentials not found.") from exc
        except PartialCredentialsError as exc:
            # pylint: disable-next=too-many-function-args
            raise PartialCredentialsError(
                "Error: Incomplete AWS credentials.") from exc
        except Exception as e:
            raise RuntimeError(f"An error occurred: {e}") from e

    def list_files(self):
        """
        List all files in the S3 bucket.
        :return: A list of file keys in the bucket.
        """
        try:
            response = self.__s3_client.list_objects_v2(
                Bucket=self.__bucket_name)
            if "Contents" in response:
                files = [item["Key"] for item in response["Contents"]]
                return files
            return []
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while listing files: {e}") from e

    def delete_file(self, s3_key):
        """
        Delete a file from the S3 bucket.
        :param s3_key: The key (path) of the file to delete in the S3 bucket.
        """
        try:
            self.__s3_client.delete_object(
                Bucket=self.__bucket_name, Key=s3_key)
            return {"message": f"File {s3_key} deleted successfully."}
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while deleting the file: {e}") from e

    def download_file_to_temp(self, s3_key):
        """
        Download a file from the S3 bucket to a temporary location.
        :param s3_key: The key (path) of the file in the S3 bucket.
        :return: The path to the temporary file.
        """
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                # Write the file to the temporary file
                temp_file.write(b"")
            temp_file_path = temp_file.name
            temp_file.close()

            # Download the file from S3 to the temporary file
            self.__s3_client.download_file(
                self.__bucket_name, s3_key, temp_file_path)
            return temp_file_path
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while downloading the file: {e}") from e

    def download_file_as_variable(self, s3_key):
        """
        Download a file from the S3 bucket and return its content as a variable.
        :param s3_key: The key (path) of the file in the S3 bucket.
        :return: The content of the file as a string.
        """
        try:
            # Create an in-memory file-like object
            file_obj = io.BytesIO()

            # Download the file from S3 into the in-memory object
            self.__s3_client.download_fileobj(
                self.__bucket_name, s3_key, file_obj)

            # Move the pointer to the beginning of the file
            file_obj.seek(0)

            # Read the content as a string (or bytes if needed)
            file_content = file_obj.read().decode('utf-8')  # Decode as UTF-8 string
            return file_content
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while downloading the file: {e}") from e

# End of class S3Uploader
