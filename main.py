
import logging
import time
from src.job_processor import JobProcessor

# Set the root logger to propagate logs to all modules
logging.basicConfig(
    level=logging.WARNING,  # Set to DEBUG for more detailed logs
)
logger = logging.getLogger(__name__)
# Sleep 20 seconds to allow the logger to initialize
time.sleep(20)
logger.info('Starting to run the job scripts')

jobs = JobProcessor()
jobs.process_active_jobs()
