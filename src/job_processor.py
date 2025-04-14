"""
This module processes the active jobs based on the configuration file.
"""
from datetime import date
import os
import logging
import functools
from calendar import monthrange
from src.builders.build_actions import BuildActions
from src.shared.yaml_loader import YamlLoader
from src.shared.folio_connector import FolioConnector
from src.builders.build_charges import BuildCharges
from src.builders.build_credits import BuildCredits
from src.builders.build_export import ExportData
from src.builders.build_connectors import SendToConnecter

logger = logging.getLogger(__name__)


def catch_exception(method):
    """
    Decorator to catch exceptions in methods.
    This decorator logs the exception and allows the program to continue
    running without crashing.
    :param method: The method to be decorated.
    :return: The wrapped method.
    """
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except Exception as e:  # pylint: disable=broad-except
            print(f"Exception in {method.__name__}: {e}")
            # Handle the exception or re-raise it if necessary
            # raise  # Uncomment to re-raise the exception after logging
            return None  # Or return a default value

    return wrapper


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
    @catch_exception
    def __init__(self):
        self.active_jobs = []

        # Get the jobs configuration file
        logger.info("Initializing JobProcessor and loading jobs configuration.")
        loader = YamlLoader()
        processed_data = loader.load_config('jobs.yaml')
        for j in processed_data['jobs']:
            logger.debug("Processing job: %s",
                         j.get('name', 'Unnamed Job'))
            if self.__check_days(j) and self.__check_month(
                    j) and self.__check_day(j):
                self.active_jobs.append(j)
        logger.info("Loaded %s active jobs.",
                    len(self.active_jobs))
        logger.debug("Active jobs: %s", self.active_jobs)

    @catch_exception
    def process_active_jobs(self):
        """
        This function processes the active jobs based on the configuration file.
        This is the main call function after the class has been instantiated.
        :return: None
        :raises Exception: If an error occurs during job processing.
        """
        logger.info("Starting to process active jobs.")
        for job in self.active_jobs:
            try:
                logger.info("Processing job: %s",
                            job.get('name', 'Unnamed Job'))
                # Get the job configuration file
                settings = YamlLoader().load_config(job['job_config'])
                logger.debug("Job configuration: %s",
                             settings)

                # set up the connector to FOLIO -- this is used by all
                # functions to
                connector = FolioConnector(job)
                logger.info("Connector initialized.")

                # Build the charge data
                logger.info("Building charge data.")
                charge_data = BuildCharges(connector, settings).get_charges()
                logger.debug("Charge data %s",
                             charge_data)

                # Build the credit data
                logger.info("Building credit data.")
                refund_data = BuildCredits(connector, settings).get_credits()
                logger.debug("Refund data %s",
                             refund_data)

                # Process the Fine data
                logger.info("Processing fine data.")
                trans_active = job["trans_active"] if 'trans_active' in job else False
                logger.debug("Transaction active: %s",
                             trans_active)
                process_data = BuildActions(
                    connector,
                    charge_data["data"],
                    settings,
                    trans_active).get_process_data()
                logger.debug("Process data %s",
                             process_data)

                # Build the export data
                working_data = {
                    "charge_data": charge_data,
                    "refund_data": refund_data,
                    "process_data": process_data
                }
                ExportData(working_data, settings)
                logger.info("Job %s processed successfully.",
                            job.get('name', 'Unnamed Test Job'))

                SendToConnecter(working_data, settings)
                logger.info("Data sent to connector successfully.")
            except Exception as e:  # pylint: disable=broad-except
                logger.error("Error processing job '%s': %s",
                             job.get('name', 'Unnamed Job'), e,
                             exc_info=True)
                raise e

    @catch_exception
    def run_test_job(self, job):
        """
        This function runs a test job based on the provided job configuration.
        It is used
        for testing purposes and is not intended for production use.
        :param job: The job configuration dictionary.
        :return: None
        :raises Exception: If an error occurs during job processing.
        """
        logger.info("Running test job: %s",
                    job.get('name', 'Unnamed Test Job'))
        try:
            job_config = os.path.join('config', job['job_config'])

            # Get the job configuration file
            settings = YamlLoader().load_config(job_config)

            # set up the connector to FOLIO -- this is used by all functions to
            connector = FolioConnector(job)

            # Build the charge data
            charge_data = BuildCharges(connector, settings).get_charges()
            logger.debug("Charge data: %s", charge_data)

            # Build the credit data
            refund_data = BuildCredits(connector, settings).get_credits()
            logger.debug("Refund data: %s", refund_data)

            # Process the Fine data
            process_data = BuildActions(
                connector,
                charge_data["data"],
                settings,
                False).get_process_data()
            logger.debug("Process data: %s", process_data)

            # Build the export data
            working_data = {
                "charge_data": charge_data,
                "refund_data": refund_data,
                "process_data": process_data
            }
            ExportData(working_data, settings)
            logger.info("Job %s processed successfully.",
                        job.get('name', 'Unnamed Test Job'))
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error processing job '%s': %s",
                         job.get('name', 'Unnamed Job'), e,
                         exc_info=True)
            raise e

    def __check_days(self, job):
        """
        This function checks if the job should run on the current day of the week.
        It checks the 'run_days' field in the job configuration.

        :param job: The job configuration dictionary.
        :return: True if the job should run today, False otherwise.

        Available options are:
        - A list of integers representing the days (0-6) when the job should run.
        """
        logger.debug("Checking run days for job: %s",
                     job.get('name', 'Unnamed Job'))
        rtn_check = False
        logger.debug("Job run days: %s",
                     job.get('run_days', 'No run days specified'))
        if 'run_days' in job and job['run_days'] is not None and job['run_days'] != '':
            today = date.today()
            check_days = int(today.strftime("%w"))
            if check_days in job['run_days']:
                rtn_check = True
        else:
            rtn_check = True
        logger.debug("Job run days check result: %s", rtn_check)
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
        logger.debug("Checking run months for job: %s",
                     job.get('name', 'Unnamed Job'))
        rtn_check = False
        logger.debug("Job run months: %s",
                     job.get('run_on_month', 'No run months specified'))
        if 'run_on_month' in job and job['run_on_month'] is not None and job['run_on_month'] != '':
            today = date.today()
            check_month = int(today.strftime("%m"))
            if not isinstance(job['run_on_month'], (list, str)):
                raise ValueError(
                    "Invalid type for 'run_on_month'. Expected list or string.")
            if isinstance(job['run_on_month'], str):
                logger.debug("Job run month string: %s",
                             job['run_on_month'])
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
        logger.debug("Job run months check result: %s", rtn_check)
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
        logger.debug("Checking run days of the month for job: %s",
                     job.get('name', 'Unnamed Job'))
        rtn_check = False
        logger.debug("Job run days of the month: %s",
                     job.get('run_on_day', 'No run days specified'))
        if 'run_on_day' in job and job['run_on_day'] is not None and job['run_on_day'] != '':
            today = date.today()
            check_day = int(today.strftime("%d"))
            if not isinstance(job['run_on_day'], (list, str)):
                logger.error(
                    "Invalid type for 'run_on_day'. Expected list or string.")
                logger.debug("Job run days of the month: %s",
                             job.get('run_on_day', 'No run days specified'))
                raise ValueError(
                    "Invalid type for 'run_on_day'. Expected list or string.")
            if isinstance(job['run_on_day'], str):
                logger.debug("Job run day string: %s",
                             job['run_on_day'])
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
        logger.debug("Job run days of the month check result: %s",
                     rtn_check)
        return rtn_check
# End of src/job_processor.py
