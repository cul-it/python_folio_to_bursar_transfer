from datetime import date
import os
import json
from calendar import monthrange
from src.builders.process_fines import ProcessFines
from src.shared.yaml_loader import yamlLoader
from src.shared.call_functions import CallFunctions
from src.builders.build_charges import BuildCharges
from src.builders.build_credits import BuildCredits
from src.builders.build_export import ExportData


class JobProcessor:

    def __init__(self):
        self.active_jobs = []

        # Get the jobs configuration file
        loader = yamlLoader()
        job_file = os.path.join( 'config', 'jobs.yaml')
        processed_data = loader.load_config(job_file)
        for j in processed_data['jobs']:
            if self.__check_days(j) and self.__check_month(j) and self._check_day(j):
                self.active_jobs.append(j)

    def process_active_jobs(self):
        for job in self.active_jobs:
            print(f"Processing job: {job['name']}")
            job_config = os.path.join('config', job['job_config'])

            # Get the job configuration file
            loader = yamlLoader()
            settings = loader.load_config(job_config)

            #set up the connector to FOLIO -- this is used by all functions to call the FOLIO system
            connector = CallFunctions(job)

            # # build the charge data
            build_charges = BuildCharges(connector, settings)
            charge_data = build_charges.get_charges()

            # build the credit data
            build_credits = BuildCredits(connector, settings)
            refund_data = build_credits.get_credits()

            # Process the Fine data
            trans_active = job["trans_active"] if 'trans_active' in job else False
            process = ProcessFines(connector, charge_data["data"], settings, trans_active)
            process_data = process.get_process_data()
            
            # TODO: REMOVE THIS ----------------
            dump = { "charges": charge_data, "credits": refund_data, "process": process_data }
            output_JSON = os.path.join(os.path.dirname(__file__), 'temp', 'dump.json')
            with open(output_JSON, 'w') as f:
                json.dump(dump, f, indent=4)  # Save with indentation for readability
            # ---------------------------------

            #build the export data
            ExportData(charge_data, refund_data, process_data, settings)


    def __check_days(self, job):
        if 'run_days' in job and job['run_days'] is not None and job['run_days'] != '':
            today = date.today()
            check_days = int(today.strftime("%w"))
            if check_days in job['run_days']:
                return True
            return False
        return True
    
    def __check_month(self, job):
        if 'run_on_month' in job and job['run_on_month'] is not None and job['run_on_month'] != '':
            today = date.today()
            check_month = int(today.strftime("%m"))
            if not isinstance(job['run_on_month'], (list, str)):
                raise ValueError("Invalid type for 'run_on_month'. Expected list or string.")
            elif isinstance(job['run_on_month'], str):
                match job['run_on_month'].upper():
                    case 'EVERY':
                        return True
                    case 'ODD':
                        if check_month % 2 != 0:
                            return True
                        return False
                    case 'EVEN':
                        if check_month % 2 == 0:
                            return True
                        return False
                    case _:
                        return False
            elif isinstance(job['run_on_month'], list):
                if check_month not in job['run_on_month']:
                    return False
                return True
        return True
    
    def _check_day(self, job):
        if 'run_on_day' in job and job['run_on_day'] is not None and job['run_on_day'] != '':
            today = date.today()
            check_day = int(today.strftime("%d"))
            if not isinstance(job['run_on_day'], (list, str)):
                raise ValueError("Invalid type for 'run_on_day'. Expected list or string.")
            elif isinstance(job['run_on_day'], str):
                match job['run_on_day'].upper():
                    case 'EVERY':
                        return True
                    case 'ODD':
                        if check_day % 2 != 0:
                            return True
                        return False
                    case 'EVEN':
                        if check_day % 2 == 0:
                            return True
                        return False
                    case 'LAST':
                        last_day = monthrange(today.year, today.month)[1]
                        if check_day == int(last_day):
                            return True
                        return False
                    case 'FIRST':
                        if check_day == 1:
                            return True
                        return False
                    case 'WEEKDAY':
                        if 1 <= int(today.strftime("%w")) <= 5:
                            return True
                        return False
                    case 'WEEKEND':
                        if today.strftime("%w") in ['0', '6']:
                            return True
                        return False
                    case _:
                        return False
            elif isinstance(job['run_on_day'], list):
                if check_day in job['run_on_day']:
                    return True
                return False
        return True