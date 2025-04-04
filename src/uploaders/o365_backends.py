""" AWS S3 backend to store tokens """
#pylint: skip-file
# Skipping lint as this file is based on the O365 library
import os
import boto3
import logging
import sys
from O365.utils import BaseTokenBackend
from src.shared.env_loader import EnvLoader

log = logging.getLogger(__name__)

class CustomAwsS3Backend(BaseTokenBackend):
    """ An AWS S3 backend to store tokens """

    def __init__(self, env_key, filename):
        """
        Init Backend
        :param str filename: Name of the S3 bucket
        """
        log.info("Initializing CustomAwsS3Backend with env_key: %s and filename: %s", env_key, filename)
        super().__init__()
        self._bucket_name = EnvLoader().get(name=f"{env_key}_BUCKET")
        self.filename = filename
        self._client = boto3.client(
            "s3",
            aws_access_key_id=EnvLoader().get(name=f"{env_key}_ACCESS_KEY_ID"),
            aws_secret_access_key=EnvLoader().get(name=f"{env_key}_SECRET_ACCESS_KEY"),
            region_name=EnvLoader().get(name=f"{env_key}_REGION", default="us-east-1")
        )
        log.info("CustomAwsS3Backend initialized for bucket: %s", self._bucket_name)

    def __repr__(self):
        return f"AWSS3Backend({self._bucket_name}, {self.filename})"

    def load_token(self) -> bool:
        """
        Retrieves the token from the store
         :return bool: Success / Failure
        """
        log.info("Loading token from S3 bucket: %s, filename: %s", self._bucket_name, self.filename)
        try:
            token_object = self._client.get_object(
                Bucket=self._bucket_name, Key=self.filename)
            self._cache = self.deserialize(token_object['Body'].read())
            log.info("Token loaded successfully.")
        except Exception as e:
            log.error("Token (%s) could not be retrieved from the backend: %s", self.filename, e, exc_info=True)
            return False
        return True

    def save_token(self, force=False) -> bool:
        """
        Saves the token dict in the store
        :param bool force: Force save even when state has not changed
        :return bool: Success / Failure
        """
        log.info("Saving token to S3 bucket: %s, filename: %s", self._bucket_name, self.filename)
        if not self._cache:
            log.warning("No token cache available to save.")
            return False

        if force is False and self._has_state_changed is False:
            log.info("Token state has not changed. Skipping save.")
            return True

        token_str = str.encode(self.serialize())
        if self.check_token():  # file already exists
            try:
                _ = self._client.put_object(
                    Bucket=self._bucket_name,
                    Key=self.filename,
                    Body=token_str
                )
                log.info("Token file updated successfully.")
            except Exception as e:
                log.error("Token file could not be saved: %s", e, exc_info=True)
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
                log.info("Token file created successfully.")
            except Exception as e:
                log.error("Token file could not be created: %s", e, exc_info=True)
                return False

        return True

    def delete_token(self) -> bool:
        """
        Deletes the token from the store
        :return bool: Success / Failure
        """
        log.info("Deleting token from S3 bucket: %s, filename: %s", self._bucket_name, self.filename)
        try:
            self._client.delete_object(
                Bucket=self._bucket_name, Key=self.filename)
            log.warning("Deleted token file %s in bucket %s.", self.filename, self._bucket_name)
            return True
        except Exception as e:
            log.error("Token file could not be deleted: %s", e, exc_info=True)
            return False

    def check_token(self) -> bool:
        """
        Checks if the token exists
        :return bool: True if it exists on the store
        """
        log.info("Checking if token exists in S3 bucket: %s, filename: %s", self._bucket_name, self.filename)
        try:
            _ = self._client.head_object(
                Bucket=self._bucket_name, Key=self.filename)
            log.info("Token exists in the store.")
            return True
        except Exception as e:
            log.warning("Token does not exist: %s", e, exc_info=True)
            return False

# End of Class CustomAwsS3Backend
