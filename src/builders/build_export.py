#!/usr/bin/env python3
import json
import os
from dotenv import load_dotenv
load_dotenv()
from datetime import date, timedelta
from src.shared.handlebars_helpers import left_pad, right_pad, format_date, format_money
from pybars import Compiler


class ExportData:

    def __init__(self, charge_data, refund_data, settings):
        self.__script_dir = os.path.dirname(__file__)

        compiler = Compiler()
        helpers = {
            'left_pad': left_pad,
            'right_pad': right_pad,
            'format_date': format_date,
            'format_money': format_money
            }
        
        if 'export' in settings and settings['export'] is not None:
            for conf in settings['export']:
                template_path = os.path.join(self.__script_dir, '..', 'templates', f'{conf['template_name']}.handlebars')
                with open(template_path, 'r') as file:
                    template = file.read()
                compiled_template = compiler.compile(template)

                if conf['template_data'].upper() == 'CHARGE_DATA':
                    working_data = charge_data
                elif conf['template_data'].upper() == 'REFUND_DATA':
                    working_data = refund_data
                elif conf['template_data'].upper() == 'BOTH':
                    working_data = { 
                        "charge": charge_data,
                        "credit": refund_data
                    }
                else:
                    raise ValueError("Invalid template data")
                processed_data = compiled_template(working_data, helpers=helpers)

                file_name = conf['file_name']
                if conf['file_append_date']:
                    date_string = f'_{date.today().strftime(conf['date_format'])}'
                    file_name = file_name.replace('{date}', date_string)

                output_file = os.path.join(self.__script_dir, 'temp', file_name)
                with open(output_file, 'w') as file:
                    file.write(processed_data) 
            
                i += 1