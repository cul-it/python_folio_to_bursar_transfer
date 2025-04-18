#!/usr/bin/env python3
"""
    This script is used to call the FOLIO API. It is used to get
    the auth token and to make requests to the FOLIO API.
"""
import logging
import requests
from src.shared.env_loader import EnvLoader

logger = logging.getLogger(__name__)


class FolioConnector:
    """
    This class is used to get the auth token and to make requests to the FOLIO API.

    init:
        job: The job object that is passed to the script. This is used to get the run_env.
    exposed methods:
        get_requests(url_part: str) -> dict: This function is used to perform a get
            action against the FOLIO API.
        post_requests(url_part: str, body: dict) -> dict: This function is used to
            perform a post action against the FOLIO API.
    Internal methods:
        __login() -> dict: This function is used to get the auth token.
        __renew_token() -> None: This function is used to renew the auth token.
    """

    def __init__(self, job):
        self.run_env = job['run_env'].upper()
        logger.info("Initializing CallFunctions for environment: %s",
                    self.run_env)
        self.__baseurl = EnvLoader().get(name=f'{self.run_env}_BASE_URL')
        self.__headers = {
            "x-okapi-tenant": EnvLoader().get(name=f'{self.run_env}_FOLIO_TENANT'),
            "Content-Type": "application/json"
        }
        logger.info("Base URL: %s", self.__baseurl)
        logger.info("Headers: %s", self.__headers)
        try:
            cookies = self.__login()
            self.__auth_cookie = {
                'folioAccessToken': cookies['folioAccessToken']}
            self.__renew_cookie = {
                'folioAccessToken': cookies['folioAccessToken']}
            logger.info("Auth cookie: %s", self.__auth_cookie)
            logger.info("Renew cookie: %s", self.__renew_cookie)
        except Exception as e:
            logger.error("Raising exception: %s", e)
            raise
        logger.info("CallFunctions initialized successfully.")

    def __login(self):
        """
        This function is used to get the auth token.
        """
        logger.info("Attempting to log in to FOLIO API.")
        url = f"{self.__baseurl}/authn/login-with-expiry"
        data = {
            "username": EnvLoader().get(name=f'{self.run_env}_USER_NAME'),
            "password": EnvLoader().get(name=f'{self.run_env}_USER_PASSWORD'),
        }
        try:
            r = requests.post(
                url,
                json=data,
                headers=self.__headers,
                timeout=30)
            r.raise_for_status()
            if r.status_code == 201:
                cookie_data = {}
                for cookie in r.cookies:
                    cookie_data[cookie.name] = cookie.value
                logger.info("Login successful. Auth token retrieved.")
                return cookie_data
            logger.warning("Unexpected status code during login: %s",
                           r.status_code)
        except requests.exceptions.RequestException as e:
            logger.error("Raising exception in Login: %s", e)
            raise
        return None

    def __renew_token(self):  # pylint: disable=unused-private-member
        """
        This function is used to renew the auth token.
        """
        logger.info("Renewing auth token.")
        try:
            self.__auth_cookie = self.__login()
            logger.info("Auth token successfully renewed.")
        except Exception as e:
            logger.error("Raising exception in Renewing Token: %s", e)
            raise

    def get_request(self, url_part):
        """
        This function is used perform a get action against the FOLIO API.
        :param url_part: The part of the URL that is specific to the API being called.
        :return: The data returned from the API.
        """
        url = f'{self.__baseurl}{url_part}'
        logger.info("Performing GET request to URL: %s", url)
        try:
            r = requests.get(url, cookies=self.__auth_cookie, timeout=30)
            r.raise_for_status()
            data = r.json()
            logger.info("GET request successful. Data retrieved: %s", data)
            if 'errors' in data:
                logger.warning("Errors found in response: %s", data['errors'])
            if 'totalRecords' in data:
                logger.info("Total records found: %s", data['totalRecords'])
            if 'totalRecords' in data and data['totalRecords'] == 0:
                logger.warning("No records found in response.")
            if 'totalRecords' in data and data['totalRecords'] > 0:
                logger.info(
                    "Records found in response: %s",
                    data['totalRecords'])
            return data
        except requests.exceptions.RequestException as e:
            logger.error("Error during GET request to %s: %s",
                         url, e, exc_info=True)
            raise

    def post_request(self, url_part, body):
        """
        This function is used perform a post action against the FOLIO API.
        :param url_part: The part of the URL that is specific to the API being called.
        :param body: The body of the request.
        :return: The data returned from the API.
        """
        url = f'{self.__baseurl}{url_part}'
        logger.info("Performing POST request to URL: %s with body: %s",
                    url, body)
        try:
            r = requests.post(
                url,
                json=body,
                cookies=self.__auth_cookie,
                timeout=30)
            r.raise_for_status()
            data = r.json()
            logger.info("POST request successful. Data retrieved: %s", data)
            if 'errors' in data:
                logger.warning("Errors found in response: %s", data['errors'])

            return data
        except requests.exceptions.RequestException as e:
            logger.error("Error during GET request to %s: %s",
                         url, e, exc_info=True)
            raise
