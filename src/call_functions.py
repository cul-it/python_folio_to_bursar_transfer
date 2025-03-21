#!/usr/bin/env python3
import json
import os
from dotenv import load_dotenv
load_dotenv()
import csv
import requests

class CallFunctions:
    # Logon function.
    # Gets the auth cookie and saves it to a private variable to be used later.
    def __login(self):
        # Set the request parameters
        #  -- Request URl
        #  -- Headers, pulling the tenant ID
        #  -- Data; User name and password based on the current environment
        url = f"{self.__baseurl}/authn/login-with-expiry"
        data = {
            "username": os.getenv(f'{self.run_env}_USER_NAME'),
            "password": os.getenv(f'{self.run_env}_USER_PASSWORD'),
        }

        # Send the request for a new token and send the request token back for future requests.
        # Since this is a short lived script the refresh token is dropped.
        r = requests.post(url, json=data, headers=self.__headers)
        r.raise_for_status()
        if r.status_code == 201:
            cookieData = {}
            for cookie in r.cookies:
                cookieData[cookie.name] = cookie.value
            return cookieData
        return None
    
    #  init function that is ran when this class is called. 
    #  this function sets up the token and base urls used for other requests.
    def __init__(self):
        self.run_env = os.getenv('RUN_ENV')
        self.__baseurl = os.getenv(f'{self.run_env}_BASE_URL')
        self.__headers = {
                "x-okapi-tenant": os.getenv('FOLIO_TENANT'),
                "Content-Type":"application/json"
        }

        cookies = self.__login()
        self.__auth_cookie = {'folioAccessToken': cookies['folioAccessToken']}
        self.__renew_cookie = {'folioAccessToken': cookies['folioAccessToken']}

    def __renew_token(self):
        self.__auth_cookie = self.__login()

    def get_request(self, url_part):
        url = f'{self.__baseurl}{url_part}'
        print(url)
        r = requests.get(url, cookies=self.__auth_cookie)
        data = r.json()
        return data

    def post_request(self, url_part, body):
        url = f'{self.__baseurl}{url_part}'
        print(url)
        print(body)
        r = requests.post(url, json=body, cookies=self.__auth_cookie)
        print(r.status_code)
        print(r.json())
        data = r.json()
        return data