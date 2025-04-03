#!/usr/bin/env python3
import json
import os
from src.shared.data_processor import DataProcessor  # Import the new class
from src.shared.env_loader import EnvLoader


class ProcessFines:
    """
    This class is responsible for processing fines based on the configuration file.
    exposed methods:
        get_process_data() -> dict: This function retrieves the processed fine data.
    Internal methods:   
        __process_fines( fines: dict, settings: dict, trans_active: boolean) -> list: This function processes the fines based on the configuration file.

    """
    def __init__(self, connector, fines, settings, trans_active):
        """
        Initialize the ProcessFines class.
        :param connector: The connector to the FOLIO system.
        :param fines: The list of fines to be processed.
        :param settings: The configuration settings for the job.
        :param trans_active: Is the transfer active form the jobs.yaml setting profile.
        """
        self.__script_dir = os.path.dirname(__file__)
        self.__connector = connector
        self.__data_processor = DataProcessor()  # Initialize DataProcessor

        self.return_data = {}
        if 'processors' in settings and settings["processors"] and len(
                settings["processors"]) > 0:
            for config in settings['processors']:
                working_fines = fines
                if 'filters' in config and config["filters"] and len(
                        config["filters"]) > 0:
                    for f in config["filters"]:
                        filter = json.loads(EnvLoader().get(name=f))
                        working_fines = self.__data_processor.general_filter_function(
                            working_fines, filter)
                working_fines = self.__process_fine(
                    working_fines, config, trans_active)
                self.return_data[config["name"]] = working_fines
                if 'stop_processing' in config and config['stop_processing']:
                    fines = [
                        item for item in fines if item not in working_fines]
        return

    def get_process_data(self):
        """
        This function retrieves the processed fine data.
        :return: A dictionary containing the processed fine data.
        """
        return self.return_data

    def __process_fine(self, fines, settings, trans_active):
        """
        This function processes the fines based on the configuration file.
        :param fines: The list of fines to be processed.
        :param settings: The configuration settings for the job.
        :param trans_active: Is the transfer active form the jobs.yaml setting profile.        
        :return: A list of processed fines.
        """
        process_active = settings["process_active"] if trans_active in settings else True
        do_transfer = not (str(process_active).lower() ==
                           "false" or str(trans_active).lower() == "false")
        for fine in fines:
            accountId = fine["id"]
            amount = fine["amount"]
            fine["transfer"] = {}
            action = settings["action_type"].lower()
            if amount > 0:
                body = {"amount": amount}
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
                        "paymentMethod": settings["payment_method"]
                    }
                    url_2 = f"/accounts/{accountId}/{action}"
                    if do_transfer:
                        # fine["transfer"]["process"] = self.__connector.post_request(url_2, body_2)
                        fine["transfer"]["process"] = {"message": "UGGGG"}
                    else:
                        fine["transfer"]["process"] = {
                            "status": "NOT PROCESSED",
                            "message": "TRANSFER NOT PROCESSED",
                            "url": url_2,
                            "body": body_2
                        }
                else:
                    fine["transfer"]["process"] = {}
                    fine["transfer"]["errors"] = "Not Allowed"

            else:
                fine["transfer"]["errors"] = "Zero Balance"
        return fines
# End of ProcessFines class