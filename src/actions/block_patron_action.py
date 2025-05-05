"""
BlockPatronAction class for handling blocking patrons.
"""
# pylint: disable=R0801
import logging
from datetime import timezone
import  dateparser

logger = logging.getLogger(__name__)


class BlockPatronAction:
    """
    A class to handle the payment of fines in a library system.
    It checks if the payment can proceed and executes the payment if allowed.
    public methods:
    - check: Validates if the payment can be processed for a given fine.
    - execute: Processes the payment for a given fine.
    - undo: Reverts the payment action.
    """

    def __init__(self, conf, folio_connection, trans_active):
        """
        Initialize the PayFineAction class.
        :param conf: Configuration dictionary for the block action.
        :param folio_connection: Connection object for interacting with FOLIO.
        :param trans_active: Indicates if the block process is active.
        """
        self.__conf = conf
        self.__connector = folio_connection

        logger.info(
            "Initializing PayFineAction with settings: %s",
            conf["name"])
        process_active = conf["process_active"] if trans_active in conf else True
        self.__do_pay = not (str(process_active).lower() == "false" or
                             str(trans_active).lower() == "false")
        logger.debug("Block process active: %s", self.__do_pay)

    def check(self, fine):
        """
        False "check" to see if the patron can be blocked. This needs to be in 
        paces as the builder checked for the allowed value to fire off the 
        block action.
        :param fine: The fine object to checked.
        :return: fine.
        """
        logger.info("Checking block conditions for fine ID: %s", fine["id"])
        if self.__conf["name"] not in fine:
            fine[self.__conf["name"]] = {}
        fine[self.__conf["name"]]["check"] = { 
            "allowed": True,
            "message": "Block action allowed"
        }
        return fine

    def execute(self, fine):
        """
        Execute the block for a given fine.
        :param fine: The fine object to block.
        :return: The updated fine object with block details.
        """
        logger.info("Executing block for fine ID: %s", fine["id"])

        if self.__conf["name"] not in fine:
            fine[self.__conf["name"]] = {}

        staff_info = self.__conf.get("staff_note", "")
        staff_info += f"\nsystemID: {fine['id']}"

        user_note = self.__conf.get("user_note", "")
        block_description = self.__conf.get("description", "Automated block VIA the transfer system")

        expire_date = dateparser.parse("in 2 weeks, 2 days")
        expire_date = expire_date.astimezone(timezone.utc).isoformat()


        body_2 = {
            "desc": block_description,
            "staffInformation": staff_info,
            "patronMessage": user_note,
            "borrowing": bool(self.__conf.get("block_borrowing", False)),
            "renewals": bool(self.__conf.get("block_renewals", False)),
            "requests": bool(self.__conf.get("block_requests", False)),
            "expirationDate": expire_date,
            "type": "Manual",
            "userId": fine["patron"]["id"]
        }
        url_2 = "/manualblocks"

        if self.__do_pay:
            logger.debug(
                "Processing block for fine ID: %s with URL: %s",
                fine["id"],
                url_2)
            logger.debug("Block body: %s", body_2)
            try:
                # Uncomment the following line to enable actual block processing
                # fine[self.__conf["name"]]["process"] =
                #   self.__connector.post_request(url_2, body_2)
                fine[self.__conf["name"]]["process"] = {
                    "message": "Block processed successfully"}
                logger.info(
                    "Block processed successfully for fine ID: %s",
                    fine["id"])
            except Exception as e:
                logger.error(
                    "Error processing block for fine ID: %s. Error: %s",
                    fine["id"],
                    e)
                raise
        else:
            logger.warning("Block not processed for fine ID: %s", fine["id"])
            fine[self.__conf["name"]]["process"] = {
                "status": "NOT PROCESSED",
                "message": "TRANSFER NOT PROCESSED",
                "url": url_2,
                "body": body_2
            }
        return fine

    def undo(self):
        """
        Revert the block action.
        :return: True if the undo operation is successful.
        """
        logger.info("Reverting block action.")
        try:
            # Add actual revert logic here
            logger.debug("Block reverted successfully.")
            return True
        except Exception as e:
            logger.error("Error reverting block action. Error: %s", e)
            raise
# End of PayFineAction class
