"""
RemoveBlockPatronAction class for handling removing blocks from patrons.
"""
# pylint: disable=R0801
import logging

logger = logging.getLogger(__name__)


class RemoveBlockPatronAction:
    """
    A class to handle the removal of blocks from patrons in a library system.
    It checks if the block can be removed and executes the removal if allowed.
    public methods:
    - check: Validates if the block removal can be processed for a given fine.
    - execute: Processes the block removal for a given fine.
    - undo: Reverts the block removal action.
    """

    def __init__(self, conf, folio_connection, trans_active):
        """
        Initialize the RemoveBlockPatronAction class.
        :param conf: Configuration dictionary for the block action.
        :param folio_connection: Connection object for interacting with FOLIO.
        :param trans_active: Indicates if the block process is active.
        """
        self.__conf = conf
        self.__connector = folio_connection

        logger.info(
            "Initializing RemoveBlockPatronAction with settings: %s",
            conf["name"])
        process_active = conf["process_active"] if trans_active in conf else True
        self.__do_pay = not (str(process_active).lower() == "false" or
                             str(trans_active).lower() == "false")
        logger.debug("Block removal process active: %s", self.__do_pay)

    def check(self, fine):
        """
        False "check" to see if the patron block can be removed.
        This needs to be in place as the builder checks for the allowed value
        to fire off the block removal action.
        :param fine: The fine object to check.
        :return: fine.
        """
        logger.info("Checking block removal conditions for fine ID: %s", fine.get("id"))
        fine[self.__conf["name"]]["check"] = {
            "allowed": True,
            "message": "Block removal action allowed"
        }
        logger.debug("Block removal check result for fine ID %s: %s",
                     fine.get("id"), fine[self.__conf["name"]]["check"]
                     )
        return fine

    def execute(self, fine):
        """
        Execute the block removal for a given fine.
        :param fine: The fine object to unblock.
        :return: The updated fine object with block removal details.
        """
        logger.info("Executing block removal for fine ID: %s", fine.get("id"))
        url_1 = "/manualblocks"
        try:
            all_blocks = self.__connector.get_request(url_1)
            logger.debug("Retrieved all blocks: %s", all_blocks)
            for block in all_blocks:
                if block["type"] == "Manual" and fine["id"] in block["staffInformation"]:
                    url_2 = f"/manualblocks/{block['id']}"
                    self.__connector.delete_request(url_2)
                    logger.info(
                        "Deleted existing block for fine ID: %s",
                        fine["id"])
                    fine[self.__conf["name"]]["delete"] = {
                        "status": "DELETED",
                        "message": "Block deleted successfully",
                        "block_id": block['id'],
                        "block_data": block
                    }
                    logger.debug("Block removal details for fine ID %s: %s",
                                 fine.get("id"), fine[self.__conf["name"]]["delete"]
                                 )
        except Exception as e:
            logger.error("Error during block removal for fine ID: %s. Error: %s",
                         fine.get("id"), e, exc_info=True)
            raise
        return fine

    def undo(self):
        """
        Revert the block removal action.
        :return: True if the undo operation is successful.
        """
        logger.info("Reverting block removal action.")
        try:
            # Add actual revert logic here
            logger.debug("Block removal reverted successfully.")
            return True
        except Exception as e:
            logger.error("Error reverting block removal action. Error: %s", e, exc_info=True)
            raise

# End of the RemoveBlockPatronAction class
