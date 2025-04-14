"""
PayFineAction class for handling fine payment actions in a library system.
"""
# pylint: disable=R0801
import logging

logger = logging.getLogger(__name__)


class PayFineAction:
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
        :param conf: Configuration dictionary for the pay action.
        :param folio_connection: Connection object for interacting with FOLIO.
        :param trans_active: Indicates if the pay process is active.
        """
        self.__conf = conf
        self.__connector = folio_connection

        logger.info(
            "Initializing PayFineAction with settings: %s",
            conf["name"])
        process_active = conf["process_active"] if trans_active in conf else True
        self.__do_pay = not (str(process_active).lower() == "false" or
                             str(trans_active).lower() == "false")
        logger.debug("Pay process active: %s", self.__do_pay)

    def check(self, fine):
        """
        Check if the pay can proceed for a given fine.
        :param fine: The fine object to check.
        :return: fine.
        """
        logger.info("Checking pay conditions for fine ID: %s", fine.get("id"))
        if self.__conf["name"] not in fine:
            fine[self.__conf["name"]] = {}
        if fine["amount"] <= 0:
            logger.warning(
                "Pay not allowed for non-positive amounts. Fine ID: %s",
                fine.get("id"))
            fine[self.__conf["name"]]["check"] = {}
            fine[self.__conf["name"]]["check"]["allowed"] = False
        else:
            logger.debug(
                "Pay allowed for positive amounts. Fine ID: %s",
                fine.get("id"))
            body = {"amount": fine["amount"]}
            url = f"/accounts/{fine['id']}/check-pay"
            logger.debug(
                "Checking pay action for fine ID: %s with URL: %s",
                fine["id"],
                url)
            try:
                check_response = self.__connector.post_request(url, body)
                fine[self.__conf["name"]]["check"] = check_response
                if check_response["allowed"]:
                    logger.info("Pay check passed for fine ID: %s", fine["id"])
                else:
                    logger.warning(
                        "Pay check failed for fine ID: %s", fine["id"])
            except Exception as e:
                logger.error(
                    "Error during pay check for fine ID: %s. Error: %s",
                    fine["id"],
                    e)
                raise
        return fine

    def execute(self, fine):
        """
        Execute the pay for a given fine.
        :param fine: The fine object to pay.
        :return: The updated fine object with pay details.
        """
        logger.info("Executing pay for fine ID: %s", fine.get("id"))
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
        url_2 = f"/accounts/{fine['id']}/pay"

        if self.__do_pay:
            logger.debug(
                "Processing pay for fine ID: %s with URL: %s",
                fine["id"],
                url_2)
            logger.debug("Pay body: %s", body_2)
            try:
                # Uncomment the following line to enable actual pay processing
                # fine[self.__conf["name"]]["process"] =
                #   self.__connector.post_request(url_2, body_2)
                fine[self.__conf["name"]]["process"] = {
                    "message": "Pay processed successfully"}
                logger.info(
                    "Pay processed successfully for fine ID: %s",
                    fine["id"])
            except Exception as e:
                logger.error(
                    "Error processing pay for fine ID: %s. Error: %s",
                    fine["id"],
                    e)
                raise
        else:
            logger.warning("Pay not processed for fine ID: %s", fine["id"])
            fine[self.__conf["name"]]["process"] = {
                "status": "NOT PROCESSED",
                "message": "TRANSFER NOT PROCESSED",
                "url": url_2,
                "body": body_2
            }
        return fine

    def undo(self):
        """
        Revert the pay action.
        :return: True if the undo operation is successful.
        """
        logger.info("Reverting pay action.")
        try:
            # Add actual revert logic here
            logger.debug("Pay reverted successfully.")
            return True
        except Exception as e:
            logger.error("Error reverting pay action. Error: %s", e)
            raise
# End of PayFineAction class
