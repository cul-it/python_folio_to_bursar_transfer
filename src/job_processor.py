"""
This module processes the active jobs based on the configuration file.
"""
from datetime import date
import os
import json
from calendar import monthrange
from src.builders.process_fines import ProcessFines
from src.shared.yaml_loader import YamlLoader
from src.shared.call_functions import CallFunctions
from src.builders.build_charges import BuildCharges
from src.builders.build_credits import BuildCredits
from src.builders.build_export import ExportData


class JobProcessor:
    """
    This class processes the active jobs based on the configuration file.
    exposed methods:
        process_active_jobs() -> None
    Internal methods:
        __check_days(job : dict) -> bool
        __check_month(job : dict) -> bool
        __check_day(job : dict) -> bool
    """

    def __init__(self):
        self.active_jobs = []

        # Get the jobs configuration file
        loader = YamlLoader()
        job_file = os.path.join('config', 'jobs.yaml')
        processed_data = loader.load_config(job_file)
        for j in processed_data['jobs']:
            if self.__check_days(j) and self.__check_month(
                    j) and self.__check_day(j):
                self.active_jobs.append(j)

    def process_active_jobs(self):
        """
        This function processes the active jobs based on the configuration file.
        This is the main call function after the class has been instantiated.
        """
        for job in self.active_jobs:
            job_config = os.path.join('config', job['job_config'])

            # Get the job configuration file
            # loader = YamlLoader()
            settings = YamlLoader().load_config(job_config)

            # set up the connector to FOLIO -- this is used by all functions to
            # call the FOLIO system
            connector = CallFunctions(job)

            # # build the charge data
            # build_charges = BuildCharges(connector, settings)
            charge_data = BuildCharges(connector, settings).get_charges()

            # build the credit data
            # build_credits = BuildCredits(connector, settings)
            refund_data = BuildCredits(connector, settings).get_credits()

            # Process the Fine data
            trans_active = job["trans_active"] if 'trans_active' in job else False
            process_data = ProcessFines(
                connector,
                charge_data["data"],
                settings,
                trans_active).get_process_data()

            #TODO: REMOVE THIS ----------------
            dump = {
                "charges": charge_data,
                "credits": refund_data,
                "process": process_data}
            output_json = os.path.join(
                os.path.dirname(__file__), 'temp', 'dump.json')
            with open(output_json, 'w', encoding='utf-8') as f:
                # Save with indentation for readability
                json.dump(dump, f, indent=4)
            # ---------------------------------

            # build the export data
            ExportData(charge_data, refund_data, process_data, settings)
        return
    
    def __check_days(self, job):
        """
        This function checks if the job should run on the current day of the week.
        It checks the 'run_days' field in the job configuration.

        :param job: The job configuration dictionary.
        :return: True if the job should run today, False otherwise.

        Available options are:
        - A list of integers representing the days (0-6) when the job should run.
        """
        rtn_check = False
        if 'run_days' in job and job['run_days'] is not None and job['run_days'] != '':
            today = date.today()
            check_days = int(today.strftime("%w"))
            if check_days in job['run_days']:
                rtn_check = True
        else:
            rtn_check = True
        return rtn_check

    def __check_month(self, job):
        """ 
        This function checks if the job should run on the current month.
        It checks the 'run_on_month' field in the job configuration.

        :param job: The job configuration dictionary.
        :return: True if the job should run this month, False otherwise.
        :raises ValueError: If the 'run_on_month' field is not a list or string.

        Available options are:
        - 'EVERY': The job runs every month.
        - 'ODD': The job runs on odd months (1, 3, 5, 7, 9, 11).
        - 'EVEN': The job runs on even months (2, 4, 6, 8, 10, 12).
        - A list of integers representing the months (1-12) when the job should run.
        """
        rtn_check = False
        if 'run_on_month' in job and job['run_on_month'] is not None and job['run_on_month'] != '':
            today = date.today()
            check_month = int(today.strftime("%m"))
            if not isinstance(job['run_on_month'], (list, str)):
                raise ValueError(
                    "Invalid type for 'run_on_month'. Expected list or string.")
            if isinstance(job['run_on_month'], str):
                match job['run_on_month'].upper():
                    case 'EVERY':
                        rtn_check = True
                    case 'ODD':
                        if check_month % 2 != 0:
                            rtn_check = True
                    case 'EVEN':
                        if check_month % 2 == 0:
                            rtn_check = True
                    case _:
                        rtn_check = False
            elif isinstance(job['run_on_month'], list):
                if check_month in job['run_on_month']:
                    rtn_check = True
        else:
            rtn_check = True
        return rtn_check

    def __check_day(self, job):
        """
        This function checks if the job should run on the current day of the month.
        It checks the 'run_on_day' field in the job configuration.
        :param job: The job configuration dictionary.
        :return: True if the job should run today, False otherwise.
        :raises ValueError: If the 'run_on_day' field is not a list or string.

        Available options are:
        - 'EVERY': The job runs every day.
        - 'ODD': The job runs on odd days (1, 3, 5, ...).
        - 'EVEN': The job runs on even days (2, 4, 6, ...).
        - 'LAST': The job runs on the last day of the month.
        - 'FIRST': The job runs on the first day of the month.
        - 'WEEKDAY': The job runs on weekdays (Monday to Friday).
        - 'WEEKEND': The job runs on weekends (Saturday and Sunday).
        - A list of integers representing the days (1-31) when the job should run.
        """
        rtn_check = False
        if 'run_on_day' in job and job['run_on_day'] is not None and job['run_on_day'] != '':
            today = date.today()
            check_day = int(today.strftime("%d"))
            if not isinstance(job['run_on_day'], (list, str)):
                raise ValueError(
                    "Invalid type for 'run_on_day'. Expected list or string.")
            if isinstance(job['run_on_day'], str):
                match job['run_on_day'].upper():
                    case 'EVERY':
                        rtn_check = True
                    case 'ODD':
                        if check_day % 2 != 0:
                            rtn_check = False
                    case 'EVEN':
                        if check_day % 2 == 0:
                            rtn_check = True
                    case 'LAST':
                        last_day = monthrange(today.year, today.month)[1]
                        if check_day == int(last_day):
                            rtn_check = True
                    case 'FIRST':
                        if check_day == 1:
                            rtn_check = True
                    case 'WEEKDAY':
                        if 1 <= int(today.strftime("%w")) <= 5:
                            rtn_check = True
                    case 'WEEKEND':
                        if today.strftime("%w") in ['0', '6']:
                            rtn_check = True
                    case _:
                        rtn_check = False
            elif isinstance(job['run_on_day'], list):
                if check_day in job['run_on_day']:
                    rtn_check = True
        else:
            rtn_check = True
        return rtn_check
# End of src/job_processor.py
