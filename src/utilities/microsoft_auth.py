"""
This script is used to authenticate a 360 account using the O365 library.
It will prompt the user for their client ID, client secret, and the location to save the token file.
It will then authenticate the account and save the token file to the specified location.
"""
from O365 import Account, FileSystemTokenBackend


class Auth360Account: #pylint: disable=too-few-public-methods
    """This class is used to authenticate a 360 account using the O365 library."""

    def authenticate_account(): #pylint: disable=no-method-argument
        """
        This function is used to authenticate a 360 account using the O365 library.
        It will prompt the user for their client ID, client secret, and the 
            location to save the token file.
        It will then authenticate the account and save the token file to the specified location.
        """
        print("----------------------------------------\n"
              "Welcome to the 360 Authentication Script\n"
              "----------------------------------------\n"
              "This script will authenticate your 360 account.\n"
              "Please enter your credentials when prompted.\n"
              "\n\n"
              "---------------------------------------->>>>>>>\n")
        client_id = input(
            "Enter your `Application (client) ID`. Found on the 'Overview' page: ")
        print("\n\n"
              "---------------------------------------->>>>>>>\n")
        client_secret = input(
            "Enter your prom `Value`. Found on the "
            "'Certificates & secrets' page for your app certificate: ")
        print("\n\n"
              "----------------------------------------\n"
              "you will be asked where to save the token file\n"
              "This is the file that will be used to authenticate your\n "
              "account later and must be accessible to the server.\n")
        token_location = input(
            "Enter the path to the folder where you want to save the token file: ")
        print("\n\n"
              "----------------------------------------\n"
              "You will be asked to authenticate your account.\n"
              "----------------------------------------\n"
              "\n\n")

        credentials = (client_id, client_secret)
        token_backend = FileSystemTokenBackend(
            token_path=token_location, token_filename='my_token.txt')
        account = Account(credentials, token_backend=token_backend)
        if account.authenticate(scopes=['basic', 'message_all']):
            print('Authenticated!')

        print("----------------------------------------\n"
              "You have successfully authenticated your account.\n"
              f" The token file has been saved to {token_location}/my_token.txt.\n"
              "----------------------------------------\n"
              "\n\n"
              "----------------------------------------\n"
              "You can now use this script to authenticate your account.\n"
              "----------------------------------------\n"
              "\n\n")
