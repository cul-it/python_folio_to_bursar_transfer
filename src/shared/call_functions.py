#!/usr/bin/env python3
"""
    This script is used to call the FOLIO API. It is used to get
    the auth token and to make requests to the FOLIO API.
"""
import requests
from src.utilities.env_loader import EnvLoader



class CallFunctions:
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
        self.__baseurl = EnvLoader().get(name=f'{self.run_env}_BASE_URL')
        self.__headers = {
            "x-okapi-tenant": EnvLoader().get(name=f'{self.run_env}_FOLIO_TENANT'),
            "Content-Type": "application/json"
        }
        cookies = self.__login()
        self.__auth_cookie = {'folioAccessToken': cookies['folioAccessToken']}
        #pylint: disable-next=unused-private-member
        self.__renew_cookie = {'folioAccessToken': cookies['folioAccessToken']}
    # Logon function.
    # Gets the auth cookie and saves it to a private variable to be used later.

    def __login(self):
        """
        This function is used to get the auth token"
        """
        url = f"{self.__baseurl}/authn/login-with-expiry"
        data = {
            "username": EnvLoader().get(name=f'{self.run_env}_USER_NAME'),
            "password": EnvLoader().get(name=f'{self.run_env}_USER_PASSWORD'),
        }

        # Send the request for a new token and send the request token back for future requests.
        # Since this is a short lived script the refresh token is dropped.
        r = requests.post(url, json=data, headers=self.__headers, timeout=30)
        r.raise_for_status()
        if r.status_code == 201:
            cookie_data = {}
            for cookie in r.cookies:
                cookie_data[cookie.name] = cookie.value
            return cookie_data
        return None

    #pylint: disable-next=unused-private-member
    def __renew_token(self):
        """
        This function is used to renew the auth token.
        """
        self.__auth_cookie = self.__login()

    def get_request(self, url_part):
        """
        This function is used perform a get action against the FOLIO API.
        :param url_part: The part of the URL that is specific to the API being called.
        :return: The data returned from the API.
        """
        url = f'{self.__baseurl}{url_part}'
        print(url)
        r = requests.get(url, cookies=self.__auth_cookie, timeout=30)
        data = r.json()
        return data

    def post_request(self, url_part, body):
        """
        This function is used perform a post action against the FOLIO API.
        :param url_part: The part of the URL that is specific to the API being called.
        :param body: The body of the request.
        :return: The data returned from the API.
        """
        url = f'{self.__baseurl}{url_part}'
        print(url)
        r = requests.post(url, json=body, cookies=self.__auth_cookie, timeout=30)
        data = r.json()
        return data
