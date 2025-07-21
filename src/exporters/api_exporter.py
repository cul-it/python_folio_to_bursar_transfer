"""
Class to send data via an API endpoint. Data is formatted via 
a handlebars template, and sent to the specified API URL.
"""
# pylint: disable=R0801
import json
import logging
from unittest import case
import requests

from src.shared.env_loader import EnvLoader
from src.shared.microsoft_connector import MicrosoftConnector

logger = logging.getLogger(__name__)

class ApiExporter:
    """
    Exporter for sending data to an API endpoint.
    """
    def __init__(self, conf, template_processor):
        """
        Initialize the ApiExporter with a connection name and configuration.
        """

        env = EnvLoader()

        logger.info("Initializing ApiExporter with connection_name: %s", conf['connection_name'])
        self.__template_processor = template_processor

        self.__conf = conf
        self.__connection_name = conf['connection_name']
        self.__api_url = env.get(name=f"{conf['connection_name']}_URL")
        self.__api_method = env.get(name=f"{conf['connection_name']}_METHOD", default="POST")
        self.__api_headers = json.loads(
            env.get(name=f"{conf['connection_name']}_HEADERS", default='{"Content-Type": "application/json"}')
            )
        self.__api_token = env.get(name=f"{conf['connection_name']}_TOKEN")
        
        if not self.__api_url:
            raise ValueError(f"API URL for {conf['connection_name']} is not set in environment variables.")
        
        logger.info("ApiExporter initialized with URL: %s", self.__api_url)
    
    def ship_it(self):
        """
        Send the data to the API endpoint.
        :param data: The data to be sent to the API.
        """
        logger.info("Sending data to API: %s", self.__api_url)

        message = self.__template_processor.process_template(
            self.__conf)

        match self.__api_method.upper():
            case "POST":
                response = requests.post(
                    self.__api_url,
                    headers=self.__api_headers,
                    json=json.loads(message),
                    timeout=10
                )
                print(f"Response: {response.status_code} - {response.text}")
            case "GET":
                response = requests.get(
                    self.__api_url,
                    headers=self.__api_headers,
                    json=json.loads(message),
                    timeout=10
                    )
            case _:
                logger.error("Unsupported HTTP method: %s", self.__api_method)
                raise ValueError(f"Unsupported HTTP method: {self.__api_method}")

        if response.status_code not in (200, 201, 202):
            logger.error("Failed to send data to API: %s", response.text)


# End of class