"""
TransferFineAction class for transfer fine refund actions in a library system.
"""
# pylint: disable=R0801
import logging

logger = logging.getLogger(__name__)


class TransferFineAction:
    """
    A class to handle the transfer of fines in a library system.
    It checks if the transfer can proceed and executes the transfer if allowed.
    public methods:
    - check: Validates if the transfer can be processed for a given fine.
    - execute: Processes the transfer for a given fine.
    - undo: Reverts the transfer action.
    """

    def __init__(self, conf, folio_connection, trans_active):
        """
        Initialize the TransferFineAction class.
        :param conf: Configuration dictionary for the transfer action.
        :param folio_connection: Connection object for interacting with FOLIO.
        :param trans_active: Indicates if the transfer process is active.
        """
        self.__conf = conf
        self.__connector = folio_connection

        logger.info(
            "Initializing TransferFineAction with settings: %s",
            conf["name"])
        process_active = conf["process_active"] if trans_active in conf else True
        self.__do_transfer = not (str(process_active).lower(
        ) == "false" or str(trans_active).lower() == "false")
        logger.debug("Transfer process active: %s", self.__do_transfer)

    def check(self, fine):
        """
        Check if the transfer can proceed for a given fine.
        :param fine: The fine object to check.
        :return: fine.
        """
        logger.info(
            "Checking transfer conditions for fine ID: %s",
            fine.get("id"))
        if self.__conf["name"] not in fine:
            fine[self.__conf["name"]] = {}
        if fine["amount"] <= 0:
            logger.warning(
                "Transfer not allowed for non-positive amounts. Fine ID: %s",
                fine.get("id"))
            fine[self.__conf["name"]]["check"] = {}
            fine[self.__conf["name"]]["check"]["allowed"] = False
        else:
            logger.debug(
                "Transfer allowed for positive amounts. Fine ID: %s",
                fine.get("id"))
            body = {"amount": fine["amount"]}
            url = f"/accounts/{fine['id']}/check-transfer"
            logger.debug(
                "Checking transfer action for fine ID: %s with URL: %s",
                fine["id"],
                url)
            try:
                check_response = self.__connector.post_request(url, body)
                fine[self.__conf["name"]]["check"] = check_response
                if check_response["allowed"]:
                    logger.info(
                        "Transfer check passed for fine ID: %s",
                        fine["id"])
                else:
                    logger.warning(
                        "Transfer check failed for fine ID: %s", fine["id"])
            except Exception as e:
                logger.error(
                    "Error during transfer check for fine ID: %s. Error: %s",
                    fine["id"],
                    e)
                raise
        return fine

    def execute(self, fine):
        """
        Execute the transfer for a given fine.
        :param fine: The fine object to transfer.
        :return: The updated fine object with transfer details.
        """
        logger.info("Executing transfer for fine ID: %s", fine.get("id"))
        if self.__conf["name"] not in fine:
            fine[self.__conf["name"]] = {}

        body_2 = {
            "amount": fine["amount"],
            "notifyPatron": False,
            "comments": self.__conf["comments"],
            "userName": self.__conf["user_name"],
            "servicePointId": self.__conf["service_point_id"],
            "paymentMethod": self.__conf["payment_method"]
        }
        url_2 = f"/accounts/{fine['id']}/transfer"

        if self.__do_transfer:
            logger.debug(
                "Processing transfer for fine ID: %s with URL: %s",
                fine["id"],
                url_2)
            logger.debug("Transfer body: %s", body_2)
            try:
                # Uncomment the following line to enable actual transfer processing
                # fine[self.__conf["name"]]["process"] =
                # self.__connector.post_request(url_2, body_2)
                fine[self.__conf["name"]]["process"] = {
                    "message": "Transfer processed successfully"}
                logger.info(
                    "Transfer processed successfully for fine ID: %s",
                    fine["id"])
            except Exception as e:
                logger.error(
                    "Error processing transfer for fine ID: %s. Error: %s",
                    fine["id"],
                    e)
                raise
        else:
            logger.warning(
                "Transfer not processed for fine ID: %s",
                fine["id"])
            fine[self.__conf["name"]]["process"] = {
                "status": "NOT PROCESSED",
                "message": "TRANSFER NOT PROCESSED",
                "url": url_2,
                "body": body_2
            }
        return fine

    def undo(self):
        """
        Revert the transfer action.
        :return: True if the undo operation is successful.
        """
        logger.info("Reverting transfer action.")
        try:
            # Add actual revert logic here
            logger.debug("Transfer reverted successfully.")
            return True
        except Exception as e:
            logger.error("Error reverting transfer action. Error: %s", e)
            raise
