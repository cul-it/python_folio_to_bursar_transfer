# Start of TemplateProcessor class
"""
Class to process templates using Handlebars and generate output files.
"""
import json
import logging
from pybars import Compiler
from src.shared.handlebars_helpers import left_pad, right_pad, format_date, format_money

logger = logging.getLogger(__name__)

class TemplateProcessor:
    """
    A class to process templates using Handlebars and generate output files.
    public methods:
        - process_template: Processes the template based on the configuration and 
            data provided.
        - process_data: Processes the data based on the specified level and 
            return a formatted dictionary.
    private methods:
        - __init__: Initializes the TemplateProcessor class.
    """
    def __init__(self, working_data, file_loader):
        """
        Initialize the TemplateProcessor class.
        :param working_data: The data to be used for template processing.
        :param file_loader: An instance of FileLoader for loading templates.
        """
        logger.info("Initializing TemplateProcessor.")
        self.__working_data = working_data
        self.__file_loader = file_loader
        logger.info("TemplateProcessor initialized successfully.")

    def process_template(self, conf):
        """
        Process the template based on the configuration.
        :param conf: The configuration dictionary for the export.
        :return: The processed data as a string.
        """
        logger.info("Processing template with configuration: %s", conf)
        try:
            compiler = Compiler()
            helpers = {
                'left_pad': left_pad,
                'right_pad': right_pad,
                'format_date': format_date,
                'format_money': format_money
            }
            logger.debug("Processing data for template: %s", conf['template_data'])
            template_data = self.process_data(conf['template_data'])

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
        except Exception as e:
            logger.error("Error processing template: %s", e)
            raise

    def process_data(self, level):
        """
        Process the data based on the specified level.
        :param level: The level of data to process.
        :return: The processed data as a string.
        """
        logger.info("Processing data for level: %s", level)
        try:
            match level.upper():
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
                    logger.error("Invalid export type: %s", level)
                    raise ValueError("Invalid export type")
            logger.debug("Processed data for level %s: %s", level, template_data)
            return template_data
        except Exception as e:
            logger.error("Error processing data for level %s: %s", level, e)
            raise
# End of TemplateProcessor class
