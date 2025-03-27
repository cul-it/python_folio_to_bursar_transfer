#!/usr/bin/env python3
import json
import os
from dotenv import load_dotenv
load_dotenv()
from datetime import date, timedelta
from src.shared.data_processor import DataProcessor  # Import the new class

class ProcessFines:

    def __init__(self, connector, fines, settings):
        self.__script_dir = os.path.dirname(__file__)
        self.__connector = connector
        self.__data_processor = DataProcessor(self.__script_dir, self.__connector)  # Initialize DataProcessor
        
        i = 1
        while f'PROCESS_{i}' in os.environ:
            working_fines = fines
            settings = json.loads(os.getenv(f'PROCESS_{i}'))
            if settings["filters"]:
                filters = settings["filters"].split(',')
                for f in filters:
                    filter = json.loads(os.getenv(f))
                    working_fines = self.__data_processor.general_filter_function(working_fines, filter)
            self.__process_fine(working_fines, settings)
            fines = [item for item in fines if item not in working_fines]
            
    
    def __process_fine(self, fines, settings):
        for fine in fines:
            accountId = fine["id"]
            amount = fine["amount"]
            fine["transfer"] = []
            action = settings["action_type"].lower()
            if amount > 0:
                body = { "amount": amount }
                url = f"/accounts/{accountId}/check-{action}"
                check_response = self.__connector.post_request(url, body)
                fine["transfer"]["check"] = check_response
                if check_response["allowed"]:
                    body_2 = { 
                            "amount": amount,
                            "notifyPatron": False,
                            "comments": settings["comments"],
                            "userName": settings["user_name"],
                            "servicePointId": settings["service_point_id"],
                            "paymentMethod":settings["payment_method"]
                        }
                    url_2 = f"/accounts/{accountId}/{action}"
                    # transfer_response = self.__connector.post_request(url_2, body_2)
                    transfer_response = {
                        "status": "success",
                        "message": "Transfer Successful",
                        "url": url_2,
                        "body": body_2
                    }
                    fine["transfer"]["process"] = transfer_response
                else:
                    fine["transfer"]["process"] = {}
                    fine["transfer"]["errors"] = "Not Allowed"

            else:
                fine["transfer"]["errors"] = "Zero Balance"
        return fines

    

