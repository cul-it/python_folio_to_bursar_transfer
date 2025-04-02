# Start of the EnvLoader class
"""
This module provides a class to load environment variables from different sources.
"""
import os
from dotenv import load_dotenv


class EnvLoader: #pylint: disable=too-few-public-methods
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
            load_dotenv(self.env_file_path)

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
        # Check in .env file or system environment variables
        value = os.getenv(name)
        if value is not None:
            return value

        # Check in Docker environment variables
        docker_value = self._get_docker_env(name)
        if docker_value is not None:
            return docker_value

        # Return the default value if not found
        return default

    def _get_docker_env(self, name):
        """
        Get the value of a Docker environment variable from /proc/1/environ.
        :param name: The name of the environment variable.
        :return: The value of the environment variable or None if not found.
        """
        try:
            # Check if running in a Docker container by looking for
            # Docker-specific environment variables
            if not os.path.exists("/proc/1/environ"):
                return None

            with open("/proc/1/environ", "r", encoding="utf-8") as f:
                env_data = f.read()
                env_vars = dict(
                    line.split("=", 1) for line in env_data.split("\0") if "=" in line
                )
                return env_vars.get(name)
        except FileNotFoundError:
            # Not running in a Docker container
            return None
        except Exception as e: #pylint: disable=broad-except
            print(f"Error reading Docker environment variables: {e}")
            return None

#  End of the EnvLoader class
