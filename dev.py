"""
This script is used to run the job processor in a development environment.
It initializes the logger and processes active jobs.
"""
import logging
import sys
import time
from src.job_processor import JobProcessor


# Set the root logger to propagate logs to all modules
logging.basicConfig(
    level=logging.NOTSET,  # Set to DEBUG for more detailed logs
    format="%(levelname)s | %(asctime)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Log to the console
    ]
)
logger = logging.getLogger(__name__)
# Sleep 20 seconds to allow the logger to initialize
time.sleep(20)

logger.info('Hello world!')
logger.info('Starting to run the job scripts')


jobs = JobProcessor()
jobs.process_active_jobs()

# End of script
