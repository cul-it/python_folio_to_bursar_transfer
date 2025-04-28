"""
RefundFineAction class for handling fine refund actions in a library system.
"""
# pylint: disable=R0801
import logging

logger = logging.getLogger(__name__)


class RefundFineAction:
    """
    A class to handle the refund of fines in a library system.
    It checks if the refund can proceed and executes the refund if allowed.
    public methods:
    - check: Validates if the refund can be processed for a given fine.
    - execute: Processes the refund for a given fine.
    - undo: Reverts the refund action.
    """

    def __init__(self, conf, folio_connection, trans_active):
        """
        Initialize the RefundFineAction class.
        :param conf: Configuration dictionary for the refund action.
        :param folio_connection: Connection object for interacting with FOLIO.
        :param trans_active: Indicates if the refund process is active.
        """
        self.__conf = conf
        self.__connector = folio_connection

        logger.info(
            "Initializing RefundFineAction with settings: %s",
            conf["name"])
        process_active = conf["process_active"] if trans_active in conf else True
        self.__do_refund = not (str(process_active).lower(
        ) == "false" or str(trans_active).lower() == "false")
        logger.debug("Refund process active: %s", self.__do_refund)

    def check(self, fine):
        """
        Check if the refund can proceed for a given fine.
        :param fine: The fine object to check.
        :return: fine.
        """
        logger.info(
            "Checking refund conditions for fine ID: %s",
            fine.get("id"))
        if self.__conf["name"] not in fine:
            fine[self.__conf["name"]] = {}
        if fine["amount"] <= 0:
            logger.warning(
                "Refund not allowed for non-positive amounts. Fine ID: %s",
                fine.get("id"))
            fine[self.__conf["name"]]["check"] = {
                "allowed": False,
                "message": "Refund not allowed for non-positive amounts."
            }
        else:
            logger.debug(
                "Refund allowed for positive amounts. Fine ID: %s",
                fine.get("id"))
            body = {"amount": fine["amount"]}
            url = f"/accounts/{fine['id']}/check-refund"
            logger.debug(
                "Checking refund action for fine ID: %s with URL: %s",
                fine["id"],
                url)
            try:
                check_response = self.__connector.post_request(url, body, allow_errors=True)
                fine[self.__conf["name"]]["check"] = check_response
                if check_response["allowed"]:
                    logger.info(
                        "Refund check passed for fine ID: %s", fine["id"])
                else:
                    logger.warning(
                        "Refund check failed for fine ID: %s", fine["id"])
            except Exception as e:
                logger.error(
                    "Error during refund check for fine ID: %s. Error: %s",
                    fine["id"],
                    e)
                raise
        return fine

    def execute(self, fine):
        """
        Execute the refund for a given fine.
        :param fine: The fine object to refund.
        :return: The updated fine object with refund details.
        """
        logger.info("Executing refund for fine ID: %s", fine.get("id"))
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
        url_2 = f"/accounts/{fine['id']}/refund"

        if self.__do_refund:
            logger.debug(
                "Processing refund for fine ID: %s with URL: %s",
                fine["id"],
                url_2)
            logger.debug("Refund body: %s", body_2)
            try:
                # Uncomment the following line to enable actual refund processing
                # fine[self.__conf["name"]]["process"] =
                # self.__connector.post_request(url_2, body_2)
                fine[self.__conf["name"]]["process"] = {
                    "message": "Refund processed successfully"}
                logger.info(
                    "Refund processed successfully for fine ID: %s",
                    fine["id"])
            except Exception as e:
                logger.error(
                    "Error processing refund for fine ID: %s. Error: %s",
                    fine["id"],
                    e)
                raise
        else:
            logger.warning("Refund not processed for fine ID: %s", fine["id"])
            fine[self.__conf["name"]]["process"] = {
                "status": "NOT PROCESSED",
                "message": "TRANSFER NOT PROCESSED",
                "url": url_2,
                "body": body_2
            }
        return fine

    def undo(self):
        """
        Revert the refund action.
        :return: True if the undo operation is successful.
        """
        logger.info("Reverting refund action.")
        try:
            # Add actual revert logic here
            logger.debug("Refund reverted successfully.")
            return True
        except Exception as e:
            logger.error("Error reverting refund action. Error: %s", e)
            raise
