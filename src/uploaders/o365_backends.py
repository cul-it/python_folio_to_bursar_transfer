import os
from O365.utils import BaseTokenBackend
from dotenv import load_dotenv


class CustomAwsS3Backend(BaseTokenBackend):
    """ An AWS S3 backend to store tokens """

    def __init__(self, env_key, filename):
        """
        Init Backend
        :param str filename: Name of the S3 bucket
        """
        # Load environment variables from the .env file
        load_dotenv()
        try:
            import boto3
        except ModuleNotFoundError as e:
            raise Exception('Please install the boto3 package to use this token backend.') from e
        super().__init__()
        self._bucket_name = os.getenv(f"{env_key}_BUCKET")
        self.filename = filename
        self._client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv(f"{env_key}_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv(f"{env_key}_SECRET_ACCESS_KEY"),
            region_name=os.getenv(f"{env_key}_REGION", "us-east-1")
        )

    def __repr__(self):
        return "AWSS3Backend('{}', '{}')".format(self._bucket_name, self.filename)

    def load_token(self) -> bool:
        """
        Retrieves the token from the store
         :return bool: Success / Failure
        """
        try:
            token_object = self._client.get_object(Bucket=self._bucket_name, Key=self.filename)
            self._cache = self.deserialize(token_object['Body'].read())
        except Exception as e:
            log.error("Token ({}) could not be retrieved from the backend: {}".format(self.filename, e))
            return False
        return True

    def save_token(self, force=False) -> bool:
        """
        Saves the token dict in the store
        :param bool force: Force save even when state has not changed
        :return bool: Success / Failure
        """
        if not self._cache:
            return False

        if force is False and self._has_state_changed is False:
            return True

        token_str = str.encode(self.serialize())
        if self.check_token():  # file already exists
            try:
                _ = self._client.put_object(
                    Bucket=self._bucket_name,
                    Key=self.filename,
                    Body=token_str
                )
            except Exception as e:
                log.error("Token file could not be saved: {}".format(e))
                return False
        else:  # create a new token file
            try:
                r = self._client.put_object(
                    ACL='private',
                    Bucket=self._bucket_name,
                    Key=self.filename,
                    Body=token_str,
                    ContentType='text/plain'
                )
            except Exception as e:
                log.error("Token file could not be created: {}".format(e))
                return False

        return True

    def delete_token(self) -> bool:
        """
        Deletes the token from the store
        :return bool: Success / Failure
        """
        try:
            r = self._client.delete_object(Bucket=self._bucket_name, Key=self.filename)
        except Exception as e:
            log.error("Token file could not be deleted: {}".format(e))
            return False
        else:
            log.warning("Deleted token file {} in bucket {}.".format(self.filename, self._bucket_name))
            return True

    def check_token(self) -> bool:
        """
        Checks if the token exists
        :return bool: True if it exists on the store
        """
        try:
            _ = self._client.head_object(Bucket=self._bucket_name, Key=self.filename)
        except:
            return False
        else:
            return True
