#!/usr/bin/env python3
import os
import json
import logging
import sys
from io import BytesIO
from datetime import date
from src.shared.handlebars_helpers import left_pad, right_pad, format_date, format_money
from pybars import Compiler
from src.uploaders.aws_bucket import S3Uploader
from src.uploaders.sfpt import SftpUploader
from src.uploaders.ms_email import MSEmail
from src.uploaders.smtp_email import SMTPEmailSender
from src.shared.env_loader import EnvLoader
from src.shared.file_loader import FileLoader
from src.uploaders.slack_messanger import SlackMessenger

logger = logging.getLogger(__name__)


class ExportData:

    def __init__(self, working_data, settings):
        """
        Initialize the ExportData class.
        :param working_data: the three data files combined into a 
            single package for processing.
        :param settings: The configuration settings for the job.
        """
        logger.info("Initializing ExportData.")
        self.__script_dir = os.path.dirname(__file__)
        self.__working_data = working_data
        env = EnvLoader()
        conf = {
            "type": env.get(
                name="TEMPLATE_FILE_STORAGE_TYPE",
                default="local").upper(),
            "connector": env.get(
                name="TEMPLATE_FILE_STORAGE_CONNECTOR",
                default="local").upper(),
            "location": env.get(
                name="TEMPLATE_FILE_LOCATION",
                default="local")
        }
        self.__file_loader = FileLoader(conf)
        logger.info("ExportData initialized with configuration: %s", conf)

        if 'export' in settings and settings['export'] is not None:
            for conf in settings['export']:
                logger.info("Processing export configuration: %s", conf)
                processed_data = self.__process_template(conf)

                file_name = self.__process_file_name(conf)
                logger.debug("Processed file name: %s", file_name)
                self.__ship_package(conf, file_name, processed_data)

    def __process_file_name(self, conf):
        """
        This function processes the file name based on the configuration.
        It replaces the placeholders in the file name with actual values.
        :param conf: The configuration dictionary for the export.
        :return: The processed file name.
        """
        logger.info("Processing file name with configuration: %s", conf)
        file_name = conf['file_name']
        if conf['file_append_date']:
            date_string = f'{date.today().strftime(conf["date_format"])}'
            file_name = file_name.replace('{date}', date_string)
        logger.debug("Processed file name: %s", file_name)
        return file_name

    def __process_template(self, conf):
        """
        This function processes the template based on the configuration.
        It uses the handlebars template engine to compile the template
        and process the data.
        :param conf: The configuration dictionary for the export.
        :return: The processed data as a string.
        """
        logger.info("Processing template with configuration: %s", conf)
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
                logger.error("Invalid export type: %s", conf['template_data'])
                raise ValueError("Invalid export type")
        
        if conf['template_name'].upper() == 'DUMP_JSON':
            logger.debug("Serializing data to JSON format.")
            processed_data = json.dumps(template_data, indent=4)
        else:
            logger.debug("Loading template file: %s.handlebars", conf['template_name'])
            template = self.__file_loader.load_file(
                    f'{conf["template_name"]}.handlebars',
                    is_yaml=False
                )
            logger.debug("Compiling template with handlebars.")
            compiled_template = compiler.compile(template)
            processed_data = compiled_template(
                template_data, helpers=helpers)
        logger.info("Template processing complete.")
        return processed_data

    def __ship_package(self, conf, file_name, data):
        """
        This function is responsible for shipping the package.
        The location is based on the configuration file.
        """
        logger.info("Shipping package with configuration: %s", conf)
        match conf['export_type'].upper():
            case 'S3':
                logger.info("Uploading to S3 bucket.")
                s3_uploader = S3Uploader(env_key=conf['env_key'])
                s3_uploader.upload_file_from_string(data, file_name)
            case 'FTP':
                logger.info("Uploading to FTP server.")
                sftp = SftpUploader(env_key=conf['env_key'])
                sftp.upload_file(data, file_name)
            case 'LOCAL':
                logger.info("Saving to local file system.")
                output_location = os.path.join(
                    self.__script_dir, '../..',
                    conf['export_to'],
                    file_name)
                with open(output_location, 'w') as file: #pylint: disable=unspecified-encoding
                    file.write(data)
                logger.debug("File saved locally at: %s", output_location)
            case 'EMAIL':
                logger.info("Sending via email.")
                if EnvLoader().get(name=f"{conf['env_key']}_EMAIL_TYPE").upper() == 'MICROSOFT':
                    msg = MSEmail(conf['env_key'])
                else:
                    msg = SMTPEmailSender(conf['env_key'])
                msg.build_message(
                        to=conf['export_to'],
                        subject=file_name,
                        body=data
                    )
                if 'attachment' in conf and conf['attachment']:
                    logger.debug("Processing email attachments.")
                    for attach in conf['attachment']:
                        logger.debug("Processing email attachment: %s", attach)
                        attachment_data = self.__process_template(attach)
                        attachment_name = self.__process_file_name(attach)
                        msg.add_attachment(attachment_data, attachment_name)
                msg.send_message()
            case 'SLACK':
                logger.info("Sending via Slack.")
                slack = SlackMessenger(env_key=conf['env_key'])        
                slack.send_message(message=data, header=file_name)
                if 'attachment' in conf and conf['attachment']:
                    logger.debug("Processing Slack attachments.")
                    for attach in conf['attachment']:
                        logger.debug("Processing Slack attachment: %s", attach)
                        attachment_data = self.__process_template(attach)
                        attachment_name = self.__process_file_name(attach)
                        slack.upload_file(
                            file_stream=attachment_data,
                            title=attachment_name,
                            comment=attach["comment"] if "comment" in attach else None
                        )
            case _:
                logger.error("Invalid export type for shipping package: %s", conf['export_type'])
                raise ValueError("Invalid export type for shipping package")
        logger.info("Package shipped successfully.")
        return


# End of class ExportData
