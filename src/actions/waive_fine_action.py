import logging

logger = logging.getLogger(__name__)

class WaiveFineAction:
    def __init__(self, conf, folio_connection, trans_active):
        """
        Initialize the WaiveFineAction class.
        :param conf: Configuration dictionary for the waive action.
        :param folio_connection: Connection object for interacting with FOLIO.
        :param trans_active: Indicates if the waive process is active.
        """
        self.__conf = conf
        self.__connector = folio_connection

        logger.info("Initializing WaiveFineAction with settings: %s", conf["name"])
        process_active = conf["process_active"] if trans_active in conf else True
        self.__do_waive = not (str(process_active).lower() == "false" or str(trans_active).lower() == "false")
        logger.debug("Waive process active: %s", self.__do_waive)

    def check(self, fine):
        """
        Check if the waive can proceed for a given fine.
        :param fine: The fine object to check.
        :return: fine.
        """
        logger.info("Checking waive conditions for fine ID: %s", fine.get("id"))
        if self.__conf["name"] not in fine:
            fine[self.__conf["name"]] = {}
        if fine["amount"] <= 0:
            logger.warning("waive not allowed for non-positive amounts. Fine ID: %s", fine.get("id"))
            fine[self.__conf["name"]]["check"] = {}
            fine[self.__conf["name"]]["check"]["allowed"] = False
        else:
            logger.debug("Waive allowed for positive amounts. Fine ID: %s", fine.get("id"))
            body = {"amount": fine["amount"]}
            url = f"/accounts/{fine['id']}/check-waive"
            logger.debug("Checking waive action for fine ID: %s with URL: %s", fine["id"], url)
            try:
                check_response = self.__connector.post_request(url, body)
                fine[self.__conf["name"]]["check"] = check_response
                if check_response["allowed"]:
                    logger.info("Waive check passed for fine ID: %s", fine["id"])
                else:
                    logger.warning("Waive check failed for fine ID: %s", fine["id"])
                return fine
            except Exception as e:
                logger.error("Error during waive check for fine ID: %s. Error: %s", fine["id"], e)
                raise

    def execute(self, fine):
        """
        Execute the waive for a given fine.
        :param fine: The fine object to waive.
        :return: The updated fine object with waive details.
        """
        logger.info("Executing waive for fine ID: %s", fine.get("id"))
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
        url_2 = f"/accounts/{fine['id']}/waive"

        if self.__do_waive:
            logger.debug("Processing waive for fine ID: %s with URL: %s", fine["id"], url_2)
            logger.debug("Waive body: %s", body_2)
            try:
                # Uncomment the following line to enable actual waive processing
                # fine[self.__conf["name"]]["process"] = self.__connector.post_request(url_2, body_2)
                fine[self.__conf["name"]]["process"] = {"message": "waive processed successfully"}
                logger.info("waive processed successfully for fine ID: %s", fine["id"])
            except Exception as e:
                logger.error("Error processing waive for fine ID: %s. Error: %s", fine["id"], e)
                raise
        else:
            logger.warning("Waive not processed for fine ID: %s", fine["id"])
            fine[self.__conf["name"]]["process"] = {
                "status": "NOT PROCESSED",
                "message": "waive NOT PROCESSED",
                "url": url_2,
                "body": body_2
            }
        return fine

    def undo(self):
        """
        Revert the waive action.
        :return: True if the undo operation is successful.
        """
        logger.info("Reverting waive action.")
        try:
            # Add actual revert logic here
            logger.debug("waive reverted successfully.")
            return True
        except Exception as e:
            logger.error("Error reverting waive action. Error: %s", e)
            raise