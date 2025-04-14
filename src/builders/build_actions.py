#!/usr/bin/env python3
import json
import os
import logging
import importlib
import sys
from src.shared.data_processor import DataProcessor  # Import the new class
from src.shared.env_loader import EnvLoader
from src.shared.common_helpers import pascal_to_camel_case

logger = logging.getLogger(__name__)


class BuildActions:
    """
    This class is responsible for processing fines based on the configuration file.
    exposed methods:
        get_process_data() -> dict: This function retrieves the processed fine data.
    Internal methods:   
        __process_fines( fines: dict, settings: dict, trans_active: boolean) -> list: This function processes the fines based on the configuration file.

    """
    def __init__(self, connector, fines, settings, trans_active):
        """
        Initialize the BuildActions class.
        :param connector: The connector to the FOLIO system.
        :param fines: The list of fines to be processed.
        :param settings: The configuration settings for the job.
        :param trans_active: Is the transfer active form the jobs.yaml setting profile.
        """
        logger.info("Initializing BuildActions.")
        self.__connector = connector
        self.__data_processor = DataProcessor()  # Initialize DataProcessor

        self.return_data = {}
        logger.info("Checking for actions in settings.")
        if 'actions' in settings and settings["actions"] and len(
                settings["actions"]) > 0:
            for config in settings['actions']:
                logger.info("Processing configuration: %s", config["name"])
                working_fines = fines
                if 'filters' in config and config["filters"] and len(
                        config["filters"]) > 0:
                    for f in config["filters"]:
                        logger.debug("Applying filter: %s", f)
                        filter = json.loads(EnvLoader().get(name=f))
                        working_fines = self.__data_processor.general_filter_function(
                            working_fines, filter)
                working_fines = self.__process_fine(
                    working_fines, config, trans_active)
                self.return_data[config["name"]] = working_fines
                logger.info("Processed fines for configuration: %s", config["name"])
                if 'stop_processing' in config and config['stop_processing']:
                    fines = [
                        item for item in fines if item not in working_fines]
                    logger.debug("Stopped processing remaining fines for configuration: %s", config["name"])
        logger.info("BuildActions initialization complete.")

    def get_process_data(self):
        """
        This function retrieves the processed fine data.
        :return: A dictionary containing the processed fine data.
        """
        logger.info("Retrieving processed fine data.")
        return self.return_data

    def __process_fine(self, fines, conf, trans_active):
        """
        This function processes the fines based on the configuration file.
        :param fines: The list of fines to be processed.
        :param settings: The configuration settings for the job.
        :param trans_active: Is the transfer active form the jobs.yaml setting profile.        
        :return: A list of processed fines.
        """
        logger.info("Processing fines with settings: %s", conf["name"])

        try:
            # Dynamically import the connector class
            module_name = f"src.actions.{pascal_to_camel_case(conf['action_type'])}"
            class_name = conf['action_type']
            module = importlib.import_module(module_name)
            connector_class = getattr(module, class_name)
        except (ModuleNotFoundError, AttributeError) as e:
            logger.error("Failed to load connector class for type: %s. Error: %s",
                         conf['action_type'], e)
            raise ValueError(f"Invalid connector type: {conf['action_type']}")

        # Initialize the connector instance
        connector_instance = connector_class(conf, self.__connector, trans_active)
        logger.info("sending to %s.", conf['action_type'])

        for fine in fines:
            logger.debug("Processing fine ID: %s", fine["id"])
            fine = connector_instance.check(fine)
            if fine[conf["name"]]["check"]["allowed"]:
                fine = connector_instance.execute(fine)
        return fines
# End of BuildActions class
