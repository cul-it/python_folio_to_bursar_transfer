"""
This module provides a class to load environment variables from different sources.
"""
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class EnvLoader:  # pylint: disable=too-few-public-methods
    """
    A class to load environment variables from the following sources in order:
    1. .env file (if it exists)
    2. AWS environment variables (system environment variables)
    3. Docker environment variables (if running in a Docker container)
    """

    def __init__(self, env_file_path=".env"):
        """
        Initialize the EnvLoader class.
        :param env_file_path: Path to the .env file (default is ".env").
        """
        self.env_file_path = env_file_path

        # Load the .env file if it exists
        if os.path.exists(self.env_file_path):
            logger.info("Loading .env file from path: %s",
                        self.env_file_path)
            load_dotenv(self.env_file_path)
        else:
            logger.warning(".env file not found at path: %s",
                           self.env_file_path)
        logger.info("EnvLoader initialized successfully.")
        logger.debug("EnvLoader initialized with env_file_path: %s",
                     self.env_file_path)

    def get(self, name, default=None):
        """
        Get the value of an environment variable.
        The method checks for the variable in the following order:
        1. .env file
        2. AWS/system environment variables
        3. Docker environment variables
        :param name: The name of the environment variable.
        :param default: The default value to return if the variable is not found (default is None).
        :return: The value of the environment variable or the default value.
        """
        logger.debug("Attempting to retrieve environment variable: %s", name)

        # Check in .env file or system environment variables
        value = os.getenv(name)
        if value is not None:
            logger.info(
                "Environment variable '%s' found in .env or system variables.",
                name)
            return value

        # Check in Docker environment variables
        docker_value = self._get_docker_env(name)
        if docker_value is not None:
            logger.info(
                "Environment variable '%s' found in Docker environment variables.",
                name)
            return docker_value

        # Return the default value if not found
        logger.warning(
            "Environment variable '%s' not found. Returning default value: %s",
            name,
            default)
        return default

    def _get_docker_env(self, name):
        """
        Get the value of a Docker environment variable from /proc/1/environ.
        :param name: The name of the environment variable.
        :return: The value of the environment variable or None if not found.
        """
        logger.debug("Attempting to retrieve Docker environment variable: %s",
                     name)
        try:
            # Check if running in a Docker container by looking for
            # Docker-specific environment variables
            if not os.path.exists("/proc/1/environ"):
                logger.debug(
                    "Not running in a Docker container. /proc/1/environ not found.")
                return None

            with open("/proc/1/environ", "r", encoding="utf-8") as f:
                env_data = f.read()
                env_vars = dict(line.split("=", 1)
                                for line in env_data.split("\0") if "=" in line)
                logger.info(
                    "Docker environment variable '%s' retrieved successfully.", name)
                return env_vars.get(name)
        except FileNotFoundError:
            logger.debug(
                "Not running in a Docker container. /proc/1/environ not found.")
            return None
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error reading Docker environment variables: %s",
                         e, exc_info=True)
            return None
