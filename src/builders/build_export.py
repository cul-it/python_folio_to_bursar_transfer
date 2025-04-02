#!/usr/bin/env python3
import os
import json
from io import BytesIO
from datetime import date
from src.shared.handlebars_helpers import left_pad, right_pad, format_date, format_money
from pybars import Compiler
from src.uploaders.aws_bucket import S3Uploader
from src.uploaders.sfpt import SftpUploader
from src.uploaders.ms_email import MSEmail
from src.uploaders.smtp_email import SMTPEmailSender


class ExportData:

    def __init__(self, working_data, settings):
        """
        Initialize the ExportData class.
        :param working_data: the three data files combined into a 
            single package for processing.
        :param settings: The configuration settings for the job.
        """
        self.__script_dir = os.path.dirname(__file__)
        self.__working_data = working_data

        if 'export' in settings and settings['export'] is not None:
            for conf in settings['export']:
                processed_data = self.__process_template(conf)

                file_name = self.__process_file_name(conf)
                self.__ship_package(conf, file_name, processed_data)

                # TODO: REMOVE THIS ----------------
                # output_file = os.path.join(
                #     self.__script_dir, '..', 'temp', file_name)
                # with open(output_file, 'w') as file:
                #     file.write(processed_data)
                # ---------------------------------

    def __process_file_name(self, conf):
        """
        This function processes the file name based on the configuration.
        It replaces the placeholders in the file name with actual values.
        :param conf: The configuration dictionary for the export.
        :return: The processed file name.
        """
        file_name = conf['file_name']
        if conf['file_append_date']:
            date_string = f'_{
                date.today().strftime(
                    conf['date_format'])}'
            file_name = file_name.replace('{date}', date_string)
        return file_name
    def __process_template(self, conf):
        """
        This function processes the template based on the configuration.
        It uses the handlebars template engine to compile the template
        and process the data.
        :param conf: The configuration dictionary for the export.
        :return: The processed data as a string.
        """
        compiler = Compiler()
        helpers = {
            'left_pad': left_pad,
            'right_pad': right_pad,
            'format_date': format_date,
            'format_money': format_money
        }

        match conf['template_data'].upper():
            case 'CHARGE_DATA':
                template_data = self.__working_data["charge_data"]
            case 'REFUND_DATA':
                template_data = self.__working_data["refund_data"]
            case 'BOTH':
                template_data = {
                    "charge": self.__working_data["charge_data"],
                    "credit": self.__working_data["refund_data"]
                }
            case 'PROCESS_DATA':
                template_data = self.__working_data["process_data"]
            case 'ALL_DATA':
                template_data = {
                    "charge": self.__working_data["charge_data"],
                    "credit": self.__working_data["refund_data"],
                    "process": self.__working_data["process_data"]
                }
            case _:
                raise ValueError("Invalid export type")
        
        if conf['template_name'].upper() == 'DUMP_JSON':
            # Serialize the dump dictionary to a JSON string
            processed_data = json.dumps(template_data, indent=4)
        else:
            # Load the template file from the YAML file
            template_path = os.path.join(
                self.__script_dir, '..',
                'templates', 
                f'{conf['template_name']}.handlebars'
                )
            with open(template_path, 'r', encoding='utf-8') as file:
                template = file.read()
            # Compile the template with handlebars for processing
            compiled_template = compiler.compile(template)
            # Process the template with the data
            # and the helpers
            processed_data = compiled_template(
                template_data, helpers=helpers)
        return processed_data

    def __ship_package(self, conf, file_name, data):
        """
        This function is responsible for shipping the package.
        The location is based on the configuration file.
        """
        match conf['export_type'].upper():
            case 'S3':
                # Upload to S3 bucket
                s3_uploader = S3Uploader(env_key=conf['env_key'])
                s3_uploader.upload_file_from_string(data, file_name)
            case 'S3_SECURE':
                # Upload to S3 bucket using a secure connection
                s3_uploader = S3Uploader(env_key=conf['env_key'], secure=True)
                s3_uploader.upload_file_from_string(data, file_name)
            case 'FTP':
                # Upload to FTP server
                sftp = SftpUploader(env_key=conf['env_key'])
                sftp.upload_file(data, file_name)
            case 'LOCAL':
                # Save to local file system
                output_location = os.path.join(
                    self.__script_dir, '../..',
                    conf['export_to'],
                    file_name)
                with open(output_location, 'w') as file:
                    file.write(data)
            case 'MS_EMAIL' | 'EMAIL':
                # Send via Microsoft email
                if conf['export_type'].upper() == 'MS_EMAIL':
                    msg = MSEmail(conf['env_key'])
                else:
                    msg = SMTPEmailSender(conf['env_key'])
                msg.build_message(
                        to=conf['export_to'],
                        subject=file_name,
                        body=data
                    )
                if 'attachment' in conf and conf['attachment']:
                    for attach in conf['attachment']:
                        attachment_data = self.__process_template(attach)
                        attachment_name = self.__process_file_name(attach)
                        msg.add_attachment(attachment_data, attachment_name)
                msg.send_message()
                
            case _:
                raise ValueError("Invalid export type for shipping package")
        return


# End of class ExportData
