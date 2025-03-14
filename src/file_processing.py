#!/usr/bin/env python3
import json
import os
from dotenv import load_dotenv
load_dotenv()
import csv
import requests

class FileProcessing:

    def __init__(self, fileName, fileStream, fileType = False):
        self.__fileName = fileName
        self.__fileStream = fileStream
        fileFormat = os.getenv('DELIVERY_METHOD') if  fileType == False else fileType