#!/usr/bin/env python3
"""
    This script is used to call the FOLIO API. It is used to get
    the auth token and to make requests to the FOLIO API.
"""
import logging
import time
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
                'folioRefreshToken': cookies['folioRefreshToken']}
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

    def __renew_token(self):
        """
        This function is used to renew the auth token using the folioRefreshToken.
        """
        logger.info("Attempting to renew auth token using refresh token.")
        url = f"{self.__baseurl}/authn/refresh"
        try:
            r = requests.post(
                url,
                cookies=self.__renew_cookie,
                headers=self.__headers,
                timeout=30
            )
            r.raise_for_status()
            if r.status_code == 200:
                cookie_data = {}
                for cookie in r.cookies:
                    cookie_data[cookie.name] = cookie.value
                self.__auth_cookie = {'folioAccessToken': cookie_data['folioAccessToken']}
                self.__renew_cookie = {'folioRefreshToken': cookie_data['folioRefreshToken']}
                logger.info("Auth token successfully renewed.")
            else:
                logger.warning("Unexpected status code during token renewal: %s", r.status_code)
                raise RuntimeError("Failed to renew auth token.")
        except requests.exceptions.RequestException as e:
            logger.error("Error during token renewal: %s", e, exc_info=True)
            raise

    def get_request(self, url_part):
        """
        This function is used to perform a GET action against the FOLIO API.
        Retries up to 4 times if a timeout occurs.
        :param url_part: The part of the URL that is specific to the API being called.
        :return: The data returned from the API.
        """
        url = f'{self.__baseurl}{url_part}'
        logger.info("Performing GET request to URL: %s", url)
        retries = 5
        for attempt in range(retries):
            try:
                r = requests.get(url, cookies=self.__auth_cookie, timeout=30)
                r.raise_for_status()
                data = r.json()
                logger.info("GET request successful. Data retrieved: %s", data)
                return data
            except requests.exceptions.Timeout as e:
                logger.warning("GET request timed out. Attempt %d of %d.", attempt + 1, retries)
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                logger.error("GET request failed after %d attempts. Error: %s", retries, e, exc_info=True)
                raise
            except requests.exceptions.HTTPError as e:
                if r.status_code == 401:  # Unauthorized, likely due to token expiration
                    logger.warning("Auth token expired. Attempting to renew token.")
                    self.__renew_token()
                    return self.get_request(url_part)  # Retry the request after renewing the token
                logger.error("Error during GET request to %s: %s", url, e, exc_info=True)
                raise
            except requests.exceptions.RequestException as e:
                logger.error("Error during GET request to %s: %s", url, e, exc_info=True)
                raise

    def post_request(self, url_part, body, allow_errors=False):
        """
        This function is used to perform a POST action against the FOLIO API.
        Retries up to 4 times if a timeout occurs.
        :param url_part: The part of the URL that is specific to the API being called.
        :param body: The body of the request.
        :return: The data returned from the API.
        """
        url = f'{self.__baseurl}{url_part}'
        logger.info("Performing POST request to URL: %s with body: %s", url, body)
        retries = 5
        for attempt in range(retries):
            try:
                r = requests.post(
                    url,
                    json=body,
                    cookies=self.__auth_cookie,
                    timeout=30
                )
                if not allow_errors or r.status_code not in [422, 404]:
                    r.raise_for_status()
                else:
                    logger.warning("Ignoring error with status code: %s", r.status_code)
                data = r.json()
                logger.info("POST request successful. Data retrieved: %s", data)
                return data
            except requests.exceptions.Timeout as e:
                logger.warning("POST request timed out. Attempt %d of %d.", attempt + 1, retries)
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                logger.error("POST request failed after %d attempts. Error: %s", retries, e, exc_info=True)
                raise
            except requests.exceptions.HTTPError as e:
                if r.status_code == 401:  # Unauthorized, likely due to token expiration
                    logger.warning("Auth token expired. Attempting to renew token.")
                    self.__renew_token()
                    return self.post_request(url_part, body, allow_errors)  # Retry the request after renewing the token
                logger.error("Error during POST request to %s: %s", url, e, exc_info=True)
                raise
            except requests.exceptions.RequestException as e:
                logger.error("Error during POST request to %s: %s", url, e, exc_info=True)
                raise

    def delete_request(self, url_part):
        """
        This function is used to perform a DELETE action against the FOLIO API.
        Retries up to 4 times if a timeout occurs.
        :param url_part: The part of the URL that is specific to the API being called.
        :return: The data returned from the API.
        """
        url = f'{self.__baseurl}{url_part}'
        logger.info("Performing DELETE request to URL: %s", url)
        retries = 5
        for attempt in range(retries):
            try:
                r = requests.delete(
                    url,
                    cookies=self.__auth_cookie,
                    timeout=30
                )
                r.raise_for_status()
                data = r.json()
                logger.info("DELETE request successful. Data retrieved: %s", data)
                return data
            except requests.exceptions.Timeout as e:
                logger.warning("DELETE request timed out. Attempt %d of %d.", attempt + 1, retries)
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                logger.error("DELETE request failed after %d attempts. Error: %s", retries, e, exc_info=True)
                raise
            except requests.exceptions.HTTPError as e:
                if r.status_code == 401:
                    logger.warning("Auth token expired. Attempting to renew token.")
                    self.__renew_token()
                    return self.delete_request(url_part)
                logger.error("Error during DELETE request to %s: %s", url, e, exc_info=True)
                raise
            except requests.exceptions.RequestException as e:
                logger.error("Error during DELETE request to %s: %s", url, e, exc_info=True)
                raise

# End of the FolioConnector class
